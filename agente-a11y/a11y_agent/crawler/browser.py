"""Playwright browser lifecycle and execution manager."""

import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from a11y_agent.core.config import settings

@asynccontextmanager
async def get_browser_page() -> AsyncGenerator[Page, None]:
    """
    Context manager that launches a headless Chromium instance, creates an isolated context,
    and yields a configured page with security constraints.
    """
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--mute-audio"
            ]
        )
        try:
            context: BrowserContext = await browser.new_context(
                user_agent=settings.user_agent,
                viewport={"width": 1280, "height": 800},
                device_scale_factor=1.0,
                ignore_https_errors=False,
                bypass_csp=True  # allows injecting axe-core script safely
            )
            context.set_default_timeout(settings.request_timeout * 1000)
            page: Page = await context.new_page()
            try:
                yield page
            finally:
                await page.close()
                await context.close()
        finally:
            await browser.close()
