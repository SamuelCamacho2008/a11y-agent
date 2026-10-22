"""Web page fetcher and dynamic renderer using Playwright."""

import uuid
import time
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from a11y_agent.core.config import settings
from a11y_agent.core.security import validate_url_security, check_robots_txt_allowed
from a11y_agent.core.exceptions import CrawlError, SSRFSecurityError
from a11y_agent.crawler.browser import get_browser_page
from a11y_agent.crawler.detector import detect_technologies

class CrawlResult(BaseModel):
    url: str
    report_id: str
    raw_html: str
    rendered_dom: str
    status_code: int = 200
    technologies: List[str]
    screenshot_path: Optional[str] = None
    crawl_time_seconds: float = 0.0

async def fetch_and_render_page(
    url: str,
    report_id: Optional[str] = None,
    allow_private_ips: bool = False,
    page_instance: Optional[Page] = None
) -> CrawlResult:
    """
    Validate, fetch and render a web page using Playwright.
    If page_instance is provided, it reuses it; otherwise, creates a new one.
    """
    report_id = report_id or f"rep_{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    # 1. SSRF Validation
    sanitized_url = validate_url_security(url, allow_private_ips=allow_private_ips)

    # 2. Robots.txt check
    is_allowed = await check_robots_txt_allowed(sanitized_url)
    if not is_allowed:
        raise CrawlError(f"El rastreo de la URL '{sanitized_url}' está bloqueado por el archivo robots.txt del sitio.")

    screenshot_filename = f"{report_id}.png"
    screenshot_file = settings.screenshots_dir / screenshot_filename

    async def _do_crawl(page: Page) -> CrawlResult:
        try:
            response = await page.goto(
                sanitized_url,
                wait_until="load",
                timeout=settings.request_timeout * 1000
            )
            # Give a brief moment for dynamic hydration/scripts
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # Networkidle timeout is non-fatal for streaming pages

            status_code = response.status if response else 200

            # Rendered DOM
            rendered_dom = await page.content()

            # Take screenshot
            try:
                await page.screenshot(path=str(screenshot_file), full_page=False)
                screenshot_path = str(screenshot_file)
            except Exception:
                screenshot_path = None

            # Detect technologies
            technologies = detect_technologies(rendered_dom)

            elapsed = round(time.time() - start_time, 2)
            return CrawlResult(
                url=sanitized_url,
                report_id=report_id,
                raw_html=rendered_dom,  # Base HTML
                rendered_dom=rendered_dom,
                status_code=status_code,
                technologies=technologies,
                screenshot_path=screenshot_path,
                crawl_time_seconds=elapsed
            )
        except PlaywrightTimeoutError as e:
            raise CrawlError(f"Tiempo de espera agotado ({settings.request_timeout}s) al cargar '{sanitized_url}': {e}")
        except Exception as e:
            raise CrawlError(f"Error al renderizar la página '{sanitized_url}': {e}")

    if page_instance:
        return await _do_crawl(page_instance)
    else:
        async with get_browser_page() as page:
            return await _do_crawl(page)
