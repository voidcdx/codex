#!/usr/bin/env python3
"""
Download weapon images from wiki.warframe.com.

Images are fetched via Special:FilePath which redirects to the CDN URL.
Wiki filenames use spaces/underscores; local files use hyphens.

Run from repo root:
  pip install requests
  python scripts/fetch_weapon_images.py

Output: web/static/images/weapons/<Weapon-Name>.png
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

WEAPONS_JSON = Path(__file__).parent.parent / "data" / "weapons.json"
OUT_DIR = Path(__file__).parent.parent / "web" / "static" / "images" / "weapons"
WIKI_FILE_URL = "https://wiki.warframe.com/w/Special:FilePath/{filename}"

HEADERS = {"User-Agent": "warframe-damage-calc/1.0 (image fetch; github)"}


def wiki_filename(weapon_name: str) -> str:
    """Convert weapon name to wiki image filename (spaces → underscores)."""
    return weapon_name.replace(" ", "_") + ".png"


def local_filename(weapon_name: str) -> str:
    """Convert weapon name to local image filename (spaces → hyphens)."""
    return weapon_name.replace(" ", "-") + ".png"


def fetch_image(session: requests.Session, weapon_name: str, dest: Path) -> bool:
    if dest.exists():
        return True  # already downloaded

    url = WIKI_FILE_URL.format(filename=wiki_filename(weapon_name))
    try:
        r = session.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"):
            dest.write_bytes(r.content)
            return True
        print(f"  SKIP {weapon_name!r}: HTTP {r.status_code}")
        return False
    except requests.RequestException as e:
        print(f"  ERR  {weapon_name!r}: {e}")
        return False


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(WEAPONS_JSON) as f:
        weapons = json.load(f)

    names = sorted(weapons.keys())
    print(f"Fetching {len(names)} weapon images → {OUT_DIR}")

    session = requests.Session()
    ok = skip = fail = 0

    for i, name in enumerate(names, 1):
        dest = OUT_DIR / local_filename(name)
        if dest.exists():
            skip += 1
            continue
        success = fetch_image(session, name, dest)
        if success:
            ok += 1
            print(f"[{i}/{len(names)}] {name}")
        else:
            fail += 1
        time.sleep(0.3)  # be polite

    print(f"\nDone: {ok} downloaded, {skip} already present, {fail} failed")


if __name__ == "__main__":
    main()
