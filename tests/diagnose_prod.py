import asyncio
from playwright.async_api import async_playwright

async def diagnose_production():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        console_logs = []
        network_failures = []
        all_requests = []

        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))

        page.on("requestfailed", lambda req: network_failures.append({
            "url": req.url,
            "failure": req.failure,
            "method": req.method
        }))

        page.on("response", lambda res: all_requests.append({
            "url": res.url,
            "status": res.status,
            "content_type": res.headers.get("content-type", "")
        }))

        print("Navigating to https://samuelcamacho2008.github.io/a11y-agent/ ...")
        try:
            response = await page.goto("https://samuelcamacho2008.github.io/a11y-agent/", wait_until="load", timeout=20000)
            status = response.status if response else 0
            print(f"Page load status: {status}")
        except Exception as e:
            print(f"Navigation error: {e}")

        # Wait a moment for dynamic scripts
        await page.wait_for_timeout(2000)

        # Print all requests with 4xx or 5xx
        bad_responses = [r for r in all_requests if r["status"] >= 400]
        print(f"\nTotal HTTP requests: {len(all_requests)}")
        print(f"Failed HTTP responses (4xx/5xx): {len(bad_responses)}")
        for b in bad_responses:
            print(f"  [HTTP {b['status']}]: {b['url']}")

        print(f"\nNetwork failures (aborted/blocked): {len(network_failures)}")
        for nf in network_failures:
            print(f"  [FAILED]: {nf['url']} -> {nf['failure']}")

        print(f"\nConsole errors / warnings: {len(console_logs)}")
        for log in console_logs:
            if log["type"] in ("error", "warning"):
                print(f"  [{log['type'].upper()}]: {log['text']} (at {log['location']})")

        # Test tabs presence & accessibility
        tabs = await page.query_selector_all('[role="tab"]')
        print(f"\nTabs found in production: {len(tabs)}")
        for t in tabs:
            txt = await t.inner_text()
            selected = await t.get_attribute("aria-selected")
            print(f"  Tab '{txt.strip()}' -> aria-selected={selected}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose_production())
