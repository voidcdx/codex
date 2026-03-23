#!/usr/bin/env python3
"""
Fetch Warframe solar node map from the official MobileExport manifest.

One-time setup — run this before parse_worldstate.py.
Saves → data/solnode_map.json  (SolNode key → {name, planet, faction})

Run:
  pip install requests
  python scripts/fetch_solnodes.py

NOTE: Must be run locally — the sandbox blocks outbound connections.
"""

from __future__ import annotations

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
}

MANIFEST_URL = "https://content.warframe.com/MobileExport/Manifest/SolarMapManifest.json"


def _get(url: str, retries: int = 4) -> requests.Response:
    delay = 2
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            if code in (403, 404):
                raise
            print(f"  [{attempt+1}/{retries}] HTTP {code} — retrying in {delay}s")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed after {retries} attempts: {url}")


def _extract_solnode_key(unique_name: str) -> str | None:
    """
    Extract SolNode key from a uniqueName path like:
      /Lotus/Levels/Proc/SolNodes/MercuryCapture
    Returns e.g. 'MercuryCapture', or None if not a SolNode path.
    """
    if "SolNode" not in unique_name and "/SolNodes/" not in unique_name:
        return None
    return unique_name.rstrip("/").rsplit("/", 1)[-1]


def main() -> None:
    print("Fetching SolarMapManifest …")
    try:
        r = _get(MANIFEST_URL)
    except Exception as exc:
        print(f"  ✗ Failed: {exc}")
        print()
        print("  Manual fallback:")
        print("  1. Open in browser: " + MANIFEST_URL)
        print("  2. Save as data/SolarMapManifest.json")
        print("  3. Re-run this script — it will parse the local file.")
        _try_local_fallback()
        return

    data = r.json()
    _build_map(data)


def _try_local_fallback() -> None:
    local = DATA_DIR / "SolarMapManifest.json"
    if not local.exists():
        print(f"  No local file at {local} — skipping.")
        return
    print(f"  Found local file {local}, parsing …")
    _build_map(json.loads(local.read_text()))


def _build_map(data: dict | list) -> None:
    """Parse manifest and write solnode_map.json."""
    # Manifest is either a top-level list or {"Manifest": [...]}
    if isinstance(data, dict):
        entries = data.get("Manifest") or data.get("manifest") or []
    else:
        entries = data

    node_map: dict[str, dict] = {}
    for entry in entries:
        unique = entry.get("uniqueName") or entry.get("UniqueName") or ""
        key = _extract_solnode_key(unique)
        if not key:
            continue

        name = entry.get("name") or entry.get("Name") or ""
        planet = entry.get("systemName") or entry.get("SystemName") or ""
        mission_type = entry.get("type") or entry.get("Type") or ""
        faction = entry.get("faction") or entry.get("Faction") or ""

        node_map[key] = {
            "name": name,
            "planet": planet,
            "mission_type": mission_type,
            "faction": faction,
        }

    out = DATA_DIR / "solnode_map.json"
    out.write_text(json.dumps(node_map, indent=2, ensure_ascii=False))
    print(f"  ✓ {len(node_map)} nodes → {out}")


if __name__ == "__main__":
    main()
