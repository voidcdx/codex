#!/usr/bin/env python3
"""
Fetch Warframe wiki Lua modules using Playwright (real Chromium browser).
Bypasses 403s that block the requests-based fetch_wiki_data.py.

Run on Windows (where Playwright + Chromium are installed):
  python scripts/fetch_wiki_playwright.py

Outputs:
  data/weapons_data.lua
  data/mods_data.lua
  data/enemies_data.lua   (optional — only if MODULE_ENEMIES is reachable)

Then run the normal parse pipeline:
  python scripts/parse_lua.py
  python scripts/parse_wiki_data.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

MODULES = [
    ("weapons_data.lua", "https://wiki.warframe.com/w/Module:Weapons/data?action=raw"),
    ("mods_data.lua",    "https://wiki.warframe.com/w/Module:Mods/data?action=raw"),
    ("enemies_data.lua", "https://wiki.warframe.com/w/Module:Enemies/data?action=raw"),
]


async def fetch_all() -> None:
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import stealth_async
    except ImportError as exc:
        sys.exit(f"Missing dependency: {exc}\n  pip install playwright playwright-stealth")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await stealth_async(page)

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


if __name__ == "__main__":
    asyncio.run(fetch_all())
