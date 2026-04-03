#!/usr/bin/env python3
"""
fetch_images.py
---------------
Downloads game images from wiki.warframe.com using Playwright.

Reads manifest files from data/ and downloads PNGs into web/static/images/<category>/.

Categories:
  abilities    → web/static/images/abilities/
  arcanes      → web/static/images/arcanes/
  enemies      → web/static/images/enemies/
  damage_types → web/static/images/damage_types/
  relics       → web/static/images/relics/
  resources    → web/static/images/resources/

Requirements:
  pip install playwright
  python -m playwright install chromium

Run (on Windows — sandbox has no internet):
  python scripts/fetch_images.py                        # all categories
  python scripts/fetch_images.py --category arcanes     # single category
  python scripts/fetch_images.py --resume               # skip existing
  python scripts/fetch_images.py --limit 50             # cap per category
  python scripts/fetch_images.py --category enemies --resume  # resume enemies only
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
IMAGES_DIR = Path(__file__).parent.parent / "web" / "static" / "images"

WIKI_FILE_URL = "https://wiki.warframe.com/w/Special:Redirect/file/{filename}"

CATEGORIES = {
    "abilities":    {"manifest": "manifest_abilities.json",    "out_dir": "abilities"},
    "arcanes":      {"manifest": "manifest_arcanes.json",      "out_dir": "arcanes"},
    "enemies":      {"manifest": "manifest_enemies.json",      "out_dir": "enemies"},
    "damage_types": {"manifest": "manifest_damage_types.json", "out_dir": "damage_types"},
    "relics":       {"manifest": "manifest_relics.json",       "out_dir": "relics"},
    "resources":    {"manifest": "manifest_resources.json",    "out_dir": "resources"},
}

DELAY_BETWEEN = 0.4
DELAY_BATCH = 3.0
BATCH_SIZE = 50


async def download_category(
    page,
    name: str,
    manifest: dict[str, str],
    out_dir: Path,
    resume: bool,
    limit: int,
) -> tuple[int, list[dict]]:
    """Download images for one category. Returns (downloaded_count, failures)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Deduplicate filenames (multiple entries may share the same image)
    seen_files: set[str] = set()
    to_download: list[tuple[str, str]] = []
    for entry_name, filename in manifest.items():
        if filename in seen_files:
            continue
        seen_files.add(filename)
        out_path = out_dir / filename
        if resume and out_path.exists() and out_path.stat().st_size > 0:
            continue
        to_download.append((entry_name, filename))

    if limit > 0:
        to_download = to_download[:limit]

    if not to_download:
        print(f"  [{name}] Nothing to download (all {len(manifest)} exist)")
        return 0, []

    print(f"  [{name}] Downloading {len(to_download)} images → {out_dir}")

    downloaded = 0
    failed: list[dict] = []

    for i, (entry_name, filename) in enumerate(to_download):
        url = WIKI_FILE_URL.format(filename=filename)
        out_path = out_dir / filename

        try:
            resp = await page.goto(url, wait_until="load", timeout=15000)
            if resp and resp.ok:
                body = await resp.body()
                if body and len(body) > 100:
                    out_path.write_bytes(body)
                    downloaded += 1
                else:
                    failed.append({"name": entry_name, "file": filename, "error": "empty response"})
            else:
                status = resp.status if resp else "no response"
                failed.append({"name": entry_name, "file": filename, "error": f"HTTP {status}"})
        except Exception as e:
            failed.append({"name": entry_name, "file": filename, "error": str(e)[:80]})

        if (i + 1) % 25 == 0 or i == len(to_download) - 1:
            print(f"    [{name}] {i+1}/{len(to_download)} — ok={downloaded} fail={len(failed)}")

        if (i + 1) % BATCH_SIZE == 0:
            await asyncio.sleep(DELAY_BATCH)
        else:
            await asyncio.sleep(DELAY_BETWEEN)

    return downloaded, failed


async def main() -> None:
    parser = argparse.ArgumentParser(description="Download game images from wiki")
    parser.add_argument("--category", "-c", choices=list(CATEGORIES.keys()),
                        help="Download only this category (default: all)")
    parser.add_argument("--resume", action="store_true", help="Skip already-downloaded images")
    parser.add_argument("--limit", type=int, default=0, help="Max images per category (0 = all)")
    args = parser.parse_args()

    cats = {args.category: CATEGORIES[args.category]} if args.category else CATEGORIES

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Install playwright: pip install playwright && python -m playwright install chromium")
        return

    total_downloaded = 0
    all_failed: list[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                       " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for cat_name, cat_info in cats.items():
            manifest_path = DATA_DIR / cat_info["manifest"]
            if not manifest_path.exists():
                print(f"  [{cat_name}] Manifest not found: {manifest_path}")
                continue

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            out_dir = IMAGES_DIR / cat_info["out_dir"]

            downloaded, failed = await download_category(
                page, cat_name, manifest, out_dir, args.resume, args.limit
            )
            total_downloaded += downloaded
            for f in failed:
                f["category"] = cat_name
            all_failed.extend(failed)

        await browser.close()

    print(f"\nDone: {total_downloaded} downloaded, {len(all_failed)} failed")

    if all_failed:
        fail_path = DATA_DIR / "images_failed.json"
        fail_path.write_text(json.dumps(all_failed, indent=2))
        print(f"Failed list saved to {fail_path}")


if __name__ == "__main__":
    asyncio.run(main())
