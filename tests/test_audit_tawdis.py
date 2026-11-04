import asyncio
import http.server
import socketserver
import threading
from pathlib import Path
from playwright.async_api import async_playwright

PORT = 8999
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

def start_server():
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

async def test_audit_tawdis():
    start_server()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"[UNHANDLED_EXCEPTION] {err}"))

        url = f"http://127.0.0.1:{PORT}/index.html"
        print(f"Loading {url} ...")
        await page.goto(url, wait_until="load")

        # Fill URL input with tawdis.net
        print("Entering 'tawdis.net'...")
        await page.fill("#url-input", "tawdis.net")

        # Click audit button
        print("Clicking submit button...")
        await page.click("#form-url button[type='submit']")

        # Wait for either report dashboard or error banner
        for i in range(25):
            await page.wait_for_timeout(1000)

            error_card = await page.query_selector("#actionable-error")
            error_style = await error_card.get_attribute("style") if error_card else ""
            error_visible = "display: block" in (error_style or "")

            results_box = await page.query_selector("#results-container")
            results_style = await results_box.get_attribute("style") if results_box else ""
            results_visible = "display: block" in (results_style or "")

            loader = await page.query_selector("#loading-overlay")
            loader_text = await page.inner_text("#loading-text") if loader else ""

            print(f"[{i}s] Loader='{loader_text}', Error visible={error_visible}, Results visible={results_visible}", flush=True)

            if error_visible:
                error_title = await page.inner_text("#error-title")
                error_msg = await page.inner_text("#error-description")
                safe_title = error_title.encode("ascii", "replace").decode("ascii")
                safe_msg = error_msg.encode("ascii", "replace").decode("ascii")
                print(f"ERROR DISPLAYED TO USER: {safe_title} -> {safe_msg}", flush=True)
                break

            if results_visible:
                score = await page.inner_text("#score-circle")
                problems = await page.inner_text("#kpi-problems")
                warnings = await page.inner_text("#kpi-warnings")
                unverified = await page.inner_text("#kpi-unverified")
                print(f"SUCCESS! Report rendered for tawdis.net! Score={score}, Problems={problems}, Warnings={warnings}, Unverified={unverified}", flush=True)
                break

        print("\n--- CONSOLE LOGS ---")
        for log in console_logs:
            safe_log = log.encode("ascii", "replace").decode("ascii")
            print(safe_log)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_audit_tawdis())
