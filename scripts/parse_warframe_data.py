#!/usr/bin/env python3
"""
parse_warframe_data.py
----------------------
Parses data/warframes_data.lua + data/companions_data.lua → data/warframes.json

Extracts Prime entries from:
  - Warframes section (Type == "Warframe")
  - Archwings section (Type == "Archwing")
  - Companions (Category == "Sentinels" or any Prime companion)

Stats: Name, Health, Shield, Armor, Energy, Sprint, Type, Image

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


def _extract_prime(section: dict, result: dict) -> int:
    """Extract Prime entries from a Lua section dict. Returns count added."""
    count = 0
    for name, info in section.items():
        if not isinstance(info, dict):
            continue
        if "Prime" not in name:
            continue

        entry: dict = {"name": name}
        for key in STAT_KEYS:
            val = info.get(key)
            if val is not None:
                entry[key.lower()] = val
        img = info.get("Image")
        if img:
            entry["image"] = img

        result[name] = entry
        count += 1
    return count


def main() -> None:
    result: dict[str, dict] = {}

    # ── Warframes + Archwings ────────────────────────────────────────────
    wf_path = DATA_DIR / "warframes_data.lua"
    if not wf_path.exists():
        print("Missing data/warframes_data.lua — download from:")
        print("  https://wiki.warframe.com/w/Module:Warframes/data?action=raw")
    else:
        print(f"Parsing {wf_path.name} …", end=" ", flush=True)
        data = lua_to_py(wf_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            wf_count = _extract_prime(data.get("Warframes", {}), result)
            aw_count = _extract_prime(data.get("Archwings", {}), result)
            print(f"{wf_count} warframes + {aw_count} archwings")

    # ── Companions ───────────────────────────────────────────────────────
    comp_path = DATA_DIR / "companions_data.lua"
    if not comp_path.exists():
        print("Missing data/companions_data.lua — download from:")
        print("  https://wiki.warframe.com/w/Module:Companions/data?action=raw")
    else:
        print(f"Parsing {comp_path.name} …", end=" ", flush=True)
        data = lua_to_py(comp_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            comp_count = _extract_prime(data.get("Companions", {}), result)
            print(f"{comp_count} companions")

    if result:
        out = DATA_DIR / "warframes.json"
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"\nTotal: {len(result)} Prime entries → {out.name}")
    else:
        print("\nNo entries found.")


if __name__ == "__main__":
    main()
