#!/usr/bin/env python3
"""
Fetch Warframe wiki Lua modules using Playwright (real Chromium browser).
Bypasses 403s that block the requests-based fetch_wiki_data.py.

Run on Windows (where Playwright + Chromium are installed):
  python scripts/fetch_wiki_playwright.py

Outputs:
  data/weapons_data.lua
  data/mods_data.lua
  data/enemies_data.lua
  data/void_data.lua      ← relic pool data (tiers, rewards, drop locations)

Then run the normal parse pipeline:
  python scripts/parse_lua.py
  python scripts/parse_wiki_data.py
  python scripts/parse_relic_data.py

Environment variables:
  PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH — override Chromium binary path
    e.g. on Linux with system chromium:
      export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

MODULES = [
    ("weapons_data.lua", "https://wiki.warframe.com/w/Module:Weapons/data?action=raw"),
    ("mods_data.lua",    "https://wiki.warframe.com/w/Module:Mods/data?action=raw"),
    ("enemies_data.lua", "https://wiki.warframe.com/w/Module:Enemies/data?action=raw"),
    ("void_data.lua",    "https://wiki.warframe.com/w/Module:Void/data?action=raw"),
]


async def fetch_all() -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        sys.exit("Missing dependency: playwright\n  pip install playwright")

    # playwright-stealth API differs by version — handle both gracefully
    stealth_fn = None
    try:
        from playwright_stealth import stealth_async as stealth_fn  # type: ignore
    except ImportError:
        try:
            from playwright_stealth import Stealth  # type: ignore
            _s = Stealth()
            async def stealth_fn(page):  # type: ignore
                await _s.apply_stealth_async(page)
        except ImportError:
            pass  # no stealth — proceed without it

    chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")

    async with async_playwright() as p:
        launch_kwargs: dict = {"headless": True}
        if chromium_path:
            print(f"Using Chromium at: {chromium_path}")
            launch_kwargs["executable_path"] = chromium_path

        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        if stealth_fn:
            await stealth_fn(page)

        for filename, url in MODULES:
            out = DATA_DIR / filename
            print(f"Fetching {url} …")
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                if response and response.status == 200:
                    # Raw Lua pages are plain text — body contains the full source
                    text = await page.inner_text("body")
                    out.write_text(text, encoding="utf-8")
                    print(f"  ✓ Saved {len(text):,} chars → {out}")
                else:
                    status = response.status if response else "no response"
                    print(f"  ✗ HTTP {status} — skipping {filename}")
            except Exception as exc:
                print(f"  ✗ Error fetching {filename}: {exc}")

        await browser.close()

    print("\nDone. Now run:")
    print("  python scripts/parse_lua.py")
    print("  python scripts/parse_wiki_data.py")
    print("  python scripts/parse_relic_data.py")


if __name__ == "__main__":
    asyncio.run(fetch_all())
