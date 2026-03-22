#!/usr/bin/env python3
"""
update_enemy_base_levels.py
---------------------------
Reads all data/enemies_*.lua files (except enemies_data.lua) and updates
the base_level field in data/enemies.json from Stats.BaseLevel per enemy.

Run:
  python scripts/update_enemy_base_levels.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.parse_lua import lua_to_py

DATA_DIR = Path(__file__).parent.parent / "data"


def build_base_level_map() -> dict[str, int]:
    """Parse all faction Lua files and return {enemy_name: base_level}."""
    mapping: dict[str, int] = {}
    lua_files = sorted(DATA_DIR.glob("enemies_*.lua"))
    for path in lua_files:
        if path.name == "enemies_data.lua":
            continue  # router module, no enemy stats
        print(f"  Parsing {path.name} …", end=" ", flush=True)
        try:
            data = lua_to_py(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ERROR: {e}")
            continue
        if not isinstance(data, dict):
            print("skipped (unexpected format)")
            continue
        count = 0
        for name, entry in data.items():
            if not isinstance(entry, dict):
                continue
            stats = entry.get("Stats", {})
            if not isinstance(stats, dict):
                continue
            bl = stats.get("BaseLevel")
            if bl is not None:
                mapping[str(name)] = int(bl)
                count += 1
        print(f"{count} entries")
    return mapping


def main() -> None:
    print("Building base_level map from Lua files…")
    lua_map = build_base_level_map()
    print(f"Total: {len(lua_map)} enemies with BaseLevel data\n")

    enemies_path = DATA_DIR / "enemies.json"
    enemies: dict[str, dict] = json.loads(enemies_path.read_text(encoding="utf-8"))

    # Build case-insensitive lookup
    lua_lower: dict[str, int] = {k.lower(): v for k, v in lua_map.items()}

    updated = 0
    unchanged = 0
    not_found: list[str] = []

    for name, enemy in enemies.items():
        bl = lua_lower.get(name.lower())
        if bl is None:
            not_found.append(name)
            unchanged += 1
            continue
        if enemy.get("base_level") != bl:
            enemy["base_level"] = bl
            updated += 1
        else:
            unchanged += 1

    print(f"Updated:   {updated}")
    print(f"Unchanged: {unchanged}")
    if not_found:
        print(f"Not found in Lua ({len(not_found)}): {not_found[:10]}{'…' if len(not_found) > 10 else ''}")

    enemies_path.write_text(
        json.dumps(enemies, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {enemies_path}")


if __name__ == "__main__":
    main()
