#!/usr/bin/env python3
"""
Fetch weapon and mod data from wiki.warframe.com by running Lua code
on the wiki's Scribunto console endpoint.

The wiki stores all data in Lua modules (Module:Weapons/data, Module:Mods/data).
We send Lua snippets to the wiki's API and get JSON back — no local Lua parser needed.

Run:
  pip install requests
  python scripts/fetch_wiki_data.py

NOTE: Must be run locally (not inside the Claude sandbox) — the sandbox
blocks outbound connections. The wiki API works fine with a real internet connection.

Strategies tried in order:
  1. Scribunto console + LuaSerializer  → richest JSON, runs Lua on wiki server
  2. Scribunto console + mw.text.jsonEncode → fallback JSON serializer
  3. Raw module download (?action=raw)  → raw Lua text saved for local execution
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

API = "https://wiki.warframe.com/w/api.php"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://wiki.warframe.com/",
}

# ---------------------------------------------------------------------------
# Lua snippets executed on the wiki's Scribunto console
# ---------------------------------------------------------------------------

# Serialize all weapons to JSON using the wiki's own Module:LuaSerializer
LUA_WEAPONS = """\
local data = require('Module:Weapons/data')
return require('Module:LuaSerializer')._serialize('Weapons/data')
"""

# Mods/data contains { Mods = { ... } } — serialize the Mods table
LUA_MODS = """\
return require('Module:LuaSerializer')._serialize('Mods/data')
"""

# Fallback: use mw.text.jsonEncode (available in MediaWiki Lua environment)
LUA_WEAPONS_JSON = """\
local data = require('Module:Weapons/data')
return mw.text.jsonEncode(data)
"""

LUA_MODS_JSON = """\
local raw = require('Module:Mods/data')
return mw.text.jsonEncode(raw.Mods or raw)
"""


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _get(s: requests.Session, url: str, params: dict,
         retries: int = 4) -> requests.Response:
    delay = 2
    for attempt in range(retries):
        try:
            r = s.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except requests.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else 0
            if code == 403:
                raise
            print(f"  [{attempt+1}/{retries}] HTTP {code} — retrying in {delay}s")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed after {retries} attempts")


# ---------------------------------------------------------------------------
# Scribunto console: run a Lua snippet on the wiki server
# ---------------------------------------------------------------------------

def scribunto(s: requests.Session, lua_code: str, title: str = "Scratch") -> str | None:
    """
    POST Lua code to the Scribunto console endpoint.
    Returns the string result, or None on failure.
    """
    params = {
        "action":   "scribunto-console",
        "format":   "json",
        "title":    title,
        "content":  "",          # module body (empty — we use question=)
        "question": f"={lua_code.strip()}",
        "clear":    "1",
        "utf8":     "1",
    }
    try:
        r = _get(s, API, params)
        payload = r.json()
        # result lives in "return", errors in "error"
        if "error" in payload:
            print(f"  Lua error: {payload['error']}")
            return None
        return payload.get("return") or payload.get("print")
    except Exception as exc:
        print(f"  scribunto() failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_weapons(s: requests.Session) -> dict:
    print("=== Weapons ===")

    # Try LuaSerializer first
    print("  Running LuaSerializer via Scribunto …")
    raw = scribunto(s, LUA_WEAPONS, title="Weapons fetch")
    if raw:
        data = json.loads(raw)
        print(f"  ✓ {len(data)} weapons via LuaSerializer")
        return data

    # Fallback: mw.text.jsonEncode
    print("  Trying mw.text.jsonEncode …")
    raw = scribunto(s, LUA_WEAPONS_JSON, title="Weapons fetch json")
    if raw:
        data = json.loads(raw)
        print(f"  ✓ {len(data)} weapons via jsonEncode")
        return data

    # Fallback: download raw Lua source and save it (user runs locally with Lua)
    print("  Downloading raw Lua source for Weapons/data …")
    try:
        r = _get(s, "https://wiki.warframe.com/w/Module:Weapons/data", {"action": "raw"})
        raw_path = DATA_DIR / "weapons_data.lua"
        raw_path.write_text(r.text)
        print(f"  ✓ Saved raw Lua → {raw_path}")
        print("  Run: lua scripts/extract_data.lua to produce weapons_raw.json locally")
        return {}  # empty — caller should check
    except Exception as exc:
        print(f"  Raw Lua download failed: {exc}")

    raise RuntimeError("All weapon strategies failed")


def fetch_mods(s: requests.Session) -> dict:
    print("=== Mods ===")

    print("  Running LuaSerializer via Scribunto …")
    raw = scribunto(s, LUA_MODS, title="Mods fetch")
    if raw:
        data = json.loads(raw)
        # unwrap { Mods = {...} } if present
        if isinstance(data, dict) and "Mods" in data and len(data) == 1:
            data = data["Mods"]
        print(f"  ✓ {len(data)} mods via LuaSerializer")
        return data

    print("  Trying mw.text.jsonEncode …")
    raw = scribunto(s, LUA_MODS_JSON, title="Mods fetch json")
    if raw:
        data = json.loads(raw)
        print(f"  ✓ {len(data)} mods via jsonEncode")
        return data

    # Fallback: download raw Lua source
    print("  Downloading raw Lua source for Mods/data …")
    try:
        r = _get(s, "https://wiki.warframe.com/w/Module:Mods/data", {"action": "raw"})
        raw_path = DATA_DIR / "mods_data.lua"
        raw_path.write_text(r.text)
        print(f"  ✓ Saved raw Lua → {raw_path}")
        return {}
    except Exception as exc:
        print(f"  Raw Lua download failed: {exc}")

    raise RuntimeError("All mod strategies failed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    s = _session()

    weapons = fetch_weapons(s)
    out_w = DATA_DIR / "weapons_raw.json"
    out_w.write_text(json.dumps(weapons, indent=2, ensure_ascii=False))
    print(f"Saved → {out_w}\n")

    mods = fetch_mods(s)
    out_m = DATA_DIR / "mods_raw.json"
    out_m.write_text(json.dumps(mods, indent=2, ensure_ascii=False))
    print(f"Saved → {out_m}\n")

    print("Done. Run scripts/parse_wiki_data.py to extract damage-relevant fields.")


if __name__ == "__main__":
    main()
