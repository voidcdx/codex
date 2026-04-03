#!/usr/bin/env python3
"""
fetch_mod_images.py
-------------------
Downloads mod card images from wiki.warframe.com using Playwright.

Reads data/mod_images_manifest.json (mod name → image filename),
downloads each PNG to web/static/images/mods/.

Uses real Chromium to bypass wiki 403 blocks.
Batches requests with delays to be respectful.

Requirements:
  pip install playwright
  playwright install chromium

Run (on Windows — sandbox has no internet):
  python scripts/fetch_mod_images.py
  python scripts/fetch_mod_images.py --resume   # skip already-downloaded
  python scripts/fetch_mod_images.py --limit 50  # download only 50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT_DIR = Path(__file__).parent.parent / "web" / "static" / "images" / "mods"

# Wiki file redirect URL pattern
WIKI_FILE_URL = "https://wiki.warframe.com/w/Special:Redirect/file/{filename}"

# Delays (seconds)
DELAY_BETWEEN = 0.5   # between individual requests
DELAY_BATCH = 3.0     # pause every N requests
BATCH_SIZE = 50


async def main() -> None:
    parser = argparse.ArgumentParser(description="Download mod images from wiki")
    parser.add_argument("--resume", action="store_true", help="Skip already-downloaded images")
    parser.add_argument("--limit", type=int, default=0, help="Max images to download (0 = all)")
    args = parser.parse_args()

    manifest_path = DATA_DIR / "mod_images_manifest.json"
    if not manifest_path.exists():
        print("Missing data/mod_images_manifest.json — run parse first")
        return

    manifest: dict[str, str] = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"Manifest: {len(manifest)} mods")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Filter already downloaded if resuming
    to_download: list[tuple[str, str]] = []
    for mod_name, filename in manifest.items():
        out_path = OUT_DIR / filename
        if args.resume and out_path.exists() and out_path.stat().st_size > 0:
            continue
        to_download.append((mod_name, filename))

    if args.limit > 0:
        to_download = to_download[:args.limit]

    if not to_download:
        print("Nothing to download.")
        return

    print(f"Downloading {len(to_download)} images to {OUT_DIR}")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Install playwright: pip install playwright && playwright install chromium")
        return

    failed: list[tuple[str, str, str]] = []
    downloaded = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for i, (mod_name, filename) in enumerate(to_download):
            url = WIKI_FILE_URL.format(filename=filename)
            out_path = OUT_DIR / filename

            try:
                resp = await page.goto(url, wait_until="load", timeout=15000)
                if resp and resp.ok:
                    body = await resp.body()
                    if body and len(body) > 100:  # sanity check — not an error page
                        out_path.write_bytes(body)
                        downloaded += 1
                    else:
                        failed.append((mod_name, filename, "empty response"))
                else:
                    status = resp.status if resp else "no response"
                    failed.append((mod_name, filename, f"HTTP {status}"))
            except Exception as e:
                failed.append((mod_name, filename, str(e)[:80]))

            # Progress
            if (i + 1) % 10 == 0 or i == len(to_download) - 1:
                print(f"  [{i+1}/{len(to_download)}] downloaded={downloaded} failed={len(failed)}")

            # Rate limiting
            if (i + 1) % BATCH_SIZE == 0:
                print(f"  — batch pause ({DELAY_BATCH}s) —")
                await asyncio.sleep(DELAY_BATCH)
            else:
                await asyncio.sleep(DELAY_BETWEEN)

        await browser.close()

    print(f"\nDone: {downloaded} downloaded, {len(failed)} failed")

    if failed:
        fail_path = DATA_DIR / "mod_images_failed.json"
        fail_data = [{"mod": m, "file": f, "error": e} for m, f, e in failed]
        fail_path.write_text(json.dumps(fail_data, indent=2))
        print(f"Failed list saved to {fail_path}")


if __name__ == "__main__":
    asyncio.run(main())
