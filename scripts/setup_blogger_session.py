#!/usr/bin/env python3
"""
One-time setup: captures your Google/Blogger session cookies.
Run in Terminal, log in when Chrome opens, then save the output as
GitHub secret BLOGGER_SESSION_STATE.

Usage:
    pip3 install playwright
    python3 -m playwright install chromium
    python3 scripts/setup_blogger_session.py
"""

import base64, pathlib, asyncio, sys
from playwright.async_api import async_playwright

STATE_FILE = pathlib.Path("blogger_session.json")

async def main():
    async with async_playwright() as p:
        # Use real installed Chrome (not Playwright's Chromium) to avoid Google blocking
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",   # use real Chrome
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        print("Opening Blogger in Chrome...")
        await page.goto("https://accounts.google.com/signin/v2/identifier?continue=https://www.blogger.com/")
        print("\nPlease log in as a.n.k.nandu2133@gmail.com in the browser window.")
        print("Once you see the Blogger dashboard (Smart Study Tips), come back here.")

        sys.stdin = open("/dev/tty")
        input("\nPress Enter once you're on the Blogger dashboard: ")

        await context.storage_state(path=str(STATE_FILE))
        await browser.close()

    raw = STATE_FILE.read_bytes()
    encoded = base64.b64encode(raw).decode()

    print(f"\n✅ Session saved!")
    print("\n" + "="*60)
    print("COPY EVERYTHING BELOW AS GITHUB SECRET: BLOGGER_SESSION_STATE")
    print("="*60)
    print(encoded)
    print("="*60)

asyncio.run(main())
