"""PDF exporter using Playwright's native Chromium printing."""

from pathlib import Path
from playwright.async_api import async_playwright
from a11y_agent.models.schema import A11yReport
from a11y_agent.reporters.html_reporter import render_html_report

async def export_to_pdf(report: A11yReport, output_path: Path) -> Path:
    """
    Render report to HTML and export as a vector PDF using headless Chromium.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_content = render_html_report(report)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="load")

        await page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "15mm",
                "right": "15mm"
            }
        )
        await browser.close()

    return output_path
