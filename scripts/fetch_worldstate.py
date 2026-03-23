#!/usr/bin/env python3
"""
Fetch the raw Warframe worldstate from Digital Extremes' official endpoint.

Saves → data/worldstate_raw.json

Run:
  python scripts/fetch_worldstate.py [--platform pc|ps4|xb1|swi]

NOTE: Must be run locally — the sandbox blocks outbound connections.
If the endpoint blocks automated requests, download manually:
  PC:    https://content.warframe.com/dynamic/worldState.php
  PS4:   https://ps4.warframe.com/dynamic/worldState.php
  Xbox:  https://xb1.warframe.com/dynamic/worldState.php
  Switch: https://swi.warframe.com/dynamic/worldState.php

Save to data/worldstate_raw.json and run scripts/parse_worldstate.py.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.warframe.com/",
}

PLATFORM_URLS: dict[str, str] = {
    "pc":  "https://content.warframe.com/dynamic/worldState.php",
    "ps4": "https://ps4.warframe.com/dynamic/worldState.php",
    "xb1": "https://xb1.warframe.com/dynamic/worldState.php",
    "swi": "https://swi.warframe.com/dynamic/worldState.php",
}


def _get(url: str, retries: int = 4) -> requests.Response:
    delay = 2
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            if code == 403:
                print(f"  ✗ HTTP 403 — endpoint is blocking automated requests.")
                raise
            print(f"  [{attempt+1}/{retries}] HTTP {code} — retrying in {delay}s")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed after {retries} attempts: {url}")


def fetch(platform: str = "pc") -> dict:
    url = PLATFORM_URLS.get(platform)
    if not url:
        raise ValueError(f"Unknown platform: {platform!r}. Choose from: {list(PLATFORM_URLS)}")

    print(f"Fetching worldstate ({platform}) …")
    print(f"  URL: {url}")

    try:
        r = _get(url)
        data = r.json()
        print(f"  ✓ {len(data)} top-level keys")
        return data
    except requests.HTTPError:
        print()
        print("  Manual fallback — download the worldstate in your browser:")
        print(f"    {url}")
        print(f"  Save it as:  data/worldstate_raw.json")
        print("  Then run:    python scripts/parse_worldstate.py")
        return {}
    except Exception as exc:
        print(f"  ✗ {exc}")
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Warframe worldstate")
    parser.add_argument("--platform", default="pc", choices=list(PLATFORM_URLS),
                        help="Game platform (default: pc)")
    args = parser.parse_args()

    data = fetch(args.platform)
    if not data:
        return

    out = DATA_DIR / "worldstate_raw.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Saved → {out}")
    print()
    print("Run:  python scripts/parse_worldstate.py")


if __name__ == "__main__":
    main()
