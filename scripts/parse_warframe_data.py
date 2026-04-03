#!/usr/bin/env python3
"""
parse_warframe_data.py
----------------------
Parses data/warframes_data.lua → data/warframes.json

Extracts: Name, Health, Shield, Armor, Energy, Sprint, Type, Image
Only includes Type == "Warframe" entries (skips Archwings, Necramechs, Operators).

Run:
  python scripts/parse_warframe_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Reuse the Lua parser from parse_lua.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from parse_lua import lua_to_py

DATA_DIR = Path(__file__).parent.parent / "data"

STAT_KEYS = ["Health", "Shield", "Armor", "Energy", "Sprint"]


def main() -> None:
    lua_path = DATA_DIR / "warframes_data.lua"
    if not lua_path.exists():
        print("Missing data/warframes_data.lua — download from:")
        print("  https://wiki.warframe.com/w/Module:Warframes/data?action=raw")
        return

    print(f"Parsing {lua_path.name} …", end=" ", flush=True)
    src = lua_path.read_text(encoding="utf-8")
    data = lua_to_py(src)

    if not isinstance(data, dict):
        print("unexpected format")
        return

    warframes_section = data.get("Warframes", {})
    if not warframes_section:
        print("no Warframes section found")
        return

    result: dict[str, dict] = {}
    for name, info in warframes_section.items():
        if not isinstance(info, dict):
            continue
        if info.get("Type") != "Warframe":
            continue
        if "Prime" not in name:
            continue

        entry: dict = {"name": name}
        for key in STAT_KEYS:
            val = info.get(key)
            if val is not None:
                entry[key.lower()] = val
        # Image for display
        img = info.get("Image")
        if img:
            entry["image"] = img

        result[name] = entry

    out = DATA_DIR / "warframes.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"{len(result)} warframes → {out.name}")


if __name__ == "__main__":
    main()
