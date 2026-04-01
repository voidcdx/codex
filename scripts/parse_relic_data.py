#!/usr/bin/env python3
"""
parse_relic_data.py
-------------------
Parses data/void_data.lua (from wiki.warframe.com Module:Void/data) and
produces data/relics.json.

Run:
  python scripts/parse_relic_data.py

Output format (one entry per relic):
  {
    "name": "Axi A1",
    "tier": "Axi",
    "vaulted": true,
    "is_baro": false,
    "introduced": "Specters of the Rail",
    "rewards": [
      {"item": "Trinity Prime", "part": "Systems Blueprint", "rarity": "Common"},
      ...
    ]
  }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Reuse _LuaParser from parse_lua.py
sys.path.insert(0, str(Path(__file__).parent))
from parse_lua import _LuaParser  # type: ignore

DATA_DIR = Path(__file__).parent.parent / "data"


def _extract_block(src: str, varname: str) -> str:
    """
    Extract the { ... } table literal from 'varname = { ... }' in src.
    Handles nested braces correctly, ignores braces inside strings.
    """
    marker = f"{varname} = {{"
    idx = 0
    while True:
        idx = src.find(marker, idx)
        if idx == -1:
            raise ValueError(f"Could not find non-empty '{marker}' in source")
        # Skip declarations like "local RelicData = {}" — look for the block
        # that isn't immediately followed by } on the same line (i.e. non-empty)
        brace_pos = idx + len(marker) - 1
        # Check if this is just an empty table {} by peeking ahead past whitespace
        rest = src[brace_pos + 1:].lstrip(" \t")
        if not rest.startswith("}"):
            break  # found the real data block
        idx += len(marker)  # skip this empty one and keep searching

    brace_start = idx + len(marker) - 1  # position of opening {
    depth = 0
    i = brace_start
    in_string = False
    string_char = ""

    while i < len(src):
        c = src[i]
        if in_string:
            if c == "\\" and string_char != "":
                i += 2  # skip escaped char
                continue
            if c == string_char:
                in_string = False
        else:
            if c in ('"', "'"):
                in_string = True
                string_char = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return src[brace_start : i + 1]
        i += 1

    raise ValueError(f"Unmatched braces for '{varname}'")


def parse_relics(src: str) -> list[dict]:
    block = _extract_block(src, "RelicData")
    parser = _LuaParser(block)
    raw = parser._value()  # returns dict keyed by relic name

    if not isinstance(raw, dict):
        raise ValueError(f"Expected dict from RelicData, got {type(raw)}")

    relics: list[dict] = []
    for relic_key, entry in raw.items():
        if not isinstance(entry, dict):
            continue

        drops_raw = entry.get("Drops") or []
        rewards = []
        for drop in drops_raw:
            if not isinstance(drop, dict):
                continue
            item = drop.get("Item", "")
            part = drop.get("Part", "")
            rarity = drop.get("Rarity", "")
            if item:
                rewards.append({
                    "item": item,
                    "part": part,
                    "rarity": rarity,
                })

        relics.append({
            "name":        entry.get("Name") or relic_key,
            "tier":        entry.get("Tier") or "",
            "vaulted":     entry.get("Vaulted") is not None,
            "is_baro":     bool(entry.get("IsBaro")),
            "introduced":  entry.get("Introduced") or "",
            "rewards":     rewards,
        })

    # Sort: tier order, then name
    tier_order = {"Lith": 0, "Meso": 1, "Neo": 2, "Axi": 3, "Requiem": 4}
    relics.sort(key=lambda r: (tier_order.get(r["tier"], 9), r["name"]))
    return relics


def main() -> None:
    src_path = DATA_DIR / "void_data.lua"
    if not src_path.exists():
        sys.exit(f"Missing {src_path}\nRun: python scripts/fetch_wiki_playwright.py")

    print(f"Reading {src_path} …")
    src = src_path.read_text(encoding="utf-8")

    relics = parse_relics(src)
    print(f"Parsed {len(relics)} relics")

    out = DATA_DIR / "relics.json"
    out.write_text(json.dumps(relics, indent=2, ensure_ascii=False))
    print(f"Saved → {out}")

    # Summary
    vaulted = sum(1 for r in relics if r["vaulted"])
    baro = sum(1 for r in relics if r["is_baro"])
    tiers: dict[str, int] = {}
    for r in relics:
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print(f"  Vaulted: {vaulted}  Baro-only: {baro}")
    for tier, count in sorted(tiers.items(), key=lambda x: x[0]):
        print(f"  {tier}: {count}")


if __name__ == "__main__":
    main()
