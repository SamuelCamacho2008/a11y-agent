"""Web page fetcher and dynamic renderer using Playwright."""

import uuid
import time
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse
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
    final_url: Optional[str] = None
    content_type: str = "text/html"
    cookie_banner_detected: bool = False
    cookie_banner_dismissed: bool = False

async def fetch_and_render_page(
    url: str,
    report_id: Optional[str] = None,
    allow_private_ips: bool = False,
    page_instance: Optional[Page] = None,
    dismiss_cookies: bool = False
) -> CrawlResult:
    """
    Validate, fetch and render a web page using Playwright.
    Includes SSRF validation on redirects, lazy-loading auto-scroll,
    Shadow DOM preservation, and cookie banner handling.
    """
    report_id = report_id or f"rep_{uuid.uuid4().hex[:12]}"
    start_time = time.time()

    # 1. Initial SSRF Validation
    sanitized_url = validate_url_security(url, allow_private_ips=allow_private_ips)

    # 2. Robots.txt check
    is_allowed = await check_robots_txt_allowed(sanitized_url)
    if not is_allowed:
        raise CrawlError(f"El rastreo de la URL '{sanitized_url}' está bloqueado por el archivo robots.txt del sitio.")

    screenshot_filename = f"{report_id}.png"
    screenshot_file = settings.screenshots_dir / screenshot_filename

    async def _do_crawl(page: Page) -> CrawlResult:
        cookie_detected = False
        cookie_dismissed = False

        # Intercept and validate every redirect for SSRF safety
        async def on_response(response):
            # Check redirect chain
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if location:
                    # Validate redirected URL immediately
                    try:
                        validate_url_security(location, allow_private_ips=allow_private_ips)
                    except SSRFSecurityError as ssrf_err:
                        raise CrawlError(f"Redirección insegura bloqueada: {ssrf_err}")

        page.on("response", on_response)

        try:
            response = await page.goto(
                sanitized_url,
                wait_until="load",
                timeout=settings.request_timeout * 1000
            )

            # Check final URL after redirects for SSRF
            final_url = page.url
            validate_url_security(final_url, allow_private_ips=allow_private_ips)

            content_type = response.headers.get("content-type", "text/html") if response else "text/html"

            # Check if content is non-HTML (e.g. PDF, binary)
            if "application/pdf" in content_type:
                return CrawlResult(
                    url=sanitized_url,
                    report_id=report_id,
                    raw_html="",
                    rendered_dom="",
                    status_code=response.status if response else 200,
                    technologies=["PDF Document"],
                    final_url=final_url,
                    content_type="application/pdf",
                    crawl_time_seconds=round(time.time() - start_time, 2)
                )

            # Wait for network idle to ensure SPAs (React, Vue, Angular) hydrate
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass

            # Detect & optionally dismiss cookie banner
            cookie_selectors = [
                "#onetrust-accept-btn-handler",
                "button[id*='cookie'][id*='accept']",
                "button[id*='accept']",
                ".cc-btn.cc-allow",
                "[aria-label*='cookie' i] button",
                "[aria-label*='consent' i] button"
            ]
            for sel in cookie_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        cookie_detected = True
                        if dismiss_cookies:
                            await btn.click()
                            cookie_dismissed = True
                            await page.wait_for_timeout(500)
                        break
                except Exception:
                    pass

            # Auto-scroll for lazy-loaded elements in modern SPAs
            try:
                await page.evaluate("""async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 300;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if (totalHeight >= Math.min(scrollHeight, 3500)) {
                                clearInterval(timer);
                                window.scrollTo(0, 0);
                                resolve();
                            }
                        }, 80);
                    });
                }""")
            except Exception:
                pass

            status_code = response.status if response else 200

            # Rendered DOM (including client-side hydrated nodes)
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
                raw_html=rendered_dom,
                rendered_dom=rendered_dom,
                status_code=status_code,
                technologies=technologies,
                screenshot_path=screenshot_path,
                crawl_time_seconds=elapsed,
                final_url=final_url,
                content_type=content_type,
                cookie_banner_detected=cookie_detected,
                cookie_banner_dismissed=cookie_dismissed
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
