"""
parse_drops.py — Extract relic drop locations from data/drops.html

Reads the #missionRewards section and outputs data/drops.json keyed by
relic name (e.g. "Lith D7") → list of drop location entries.

Usage:
    python scripts/parse_drops.py
"""

import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("BeautifulSoup4 required. Run: pip install beautifulsoup4")

DATA_DIR = Path(__file__).parent.parent / "data"

RELIC_RE = re.compile(
    r"^(Lith|Meso|Neo|Axi|Requiem)\s+(\S+)\s+Relic$", re.IGNORECASE
)
RARITY_RE = re.compile(r"^(.+?)\s+\((\d+(?:\.\d+)?)%\)$")
HEADER_RE = re.compile(r"^(?:Event:\s+)?(.+?)\s+\(([^)]+)\)(\s+Extra)?$")
ROTATION_RE = re.compile(r"^Rotation ([A-Z])$")

ROTATION_ORDER = {None: 0, "A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


def parse_header(text: str) -> tuple[str, str]:
    """
    "Void/Taranis (Defense)"          → ("Void/Taranis", "Defense")
    "Event: Mercury/Neruda (Caches)"  → ("Mercury/Neruda", "Caches")
    "Venus/Bifrost Echo (Skirmish) Extra" → ("Venus/Bifrost Echo", "Skirmish Extra")
    """
    m = HEADER_RE.match(text.strip())
    if not m:
        return (text.strip(), "")
    location = m.group(1).strip()
    mission_type = m.group(2).strip()
    if m.group(3):
        mission_type += " Extra"
    return location, mission_type


def parse_rarity_chance(text: str) -> tuple[str, float]:
    """
    "Rare (6.67%)" → ("Rare", 6.67)
    """
    m = RARITY_RE.match(text.strip())
    if not m:
        raise ValueError(f"Cannot parse rarity/chance: {text!r}")
    return m.group(1).strip(), float(m.group(2))


def normalize_relic_name(item_text: str) -> str | None:
    """
    "Lith D7 Relic" → "Lith D7"
    Non-relics → None
    """
    m = RELIC_RE.match(item_text.strip())
    if not m:
        return None
    return f"{m.group(1).capitalize()} {m.group(2)}"


def parse_mission_rewards(source: "Path | str") -> dict[str, list[dict]]:
    """
    Parse the #missionRewards <table> and return a dict keyed by relic name.
    Stops at the #relicRewards section.

    *source* can be a ``Path`` to an HTML file **or** an HTML string.
    """
    if isinstance(source, Path):
        html = source.read_text(encoding="utf-8")
    else:
        html = source
    soup = BeautifulSoup(html, "html.parser")

    # Find the missionRewards h3 and its immediately following table
    h3 = soup.find("h3", id="missionRewards")
    if not h3:
        raise ValueError("Could not find <h3 id='missionRewards'> in drops HTML")

    table = h3.find_next_sibling("table")
    if not table:
        raise ValueError("No <table> found after missionRewards heading")

    results: dict[str, list[dict]] = {}
    seen: dict[str, set[tuple]] = {}  # for deduplication

    current_location: str | None = None
    current_mission_type: str | None = None
    current_rotation: str | None = None

    for tr in table.find_all("tr"):
        # Blank-row separator — reset rotation context
        if "blank-row" in (tr.get("class") or []):
            current_rotation = None
            continue

        th_list = tr.find_all("th")
        td_list = tr.find_all("td")

        # Header row (mission or rotation)
        if th_list:
            text = th_list[0].get_text(strip=True)
            rot_match = ROTATION_RE.match(text)
            if rot_match:
                current_rotation = rot_match.group(1)
            else:
                # Mission header — check it's not the relicRewards section
                if text.startswith("Relic ") or text == "Relics":
                    break
                current_location, current_mission_type = parse_header(text)
                current_rotation = None
            continue

        # Item row
        if len(td_list) >= 2:
            item_text = td_list[0].get_text(strip=True)
            rarity_text = td_list[1].get_text(strip=True)

            relic_name = normalize_relic_name(item_text)
            if relic_name is None:
                continue

            try:
                rarity, chance = parse_rarity_chance(rarity_text)
            except ValueError:
                continue

            entry = {
                "location": current_location,
                "mission_type": current_mission_type,
                "rotation": current_rotation,
                "rarity": rarity,
                "chance": chance,
            }

            # Deduplicate
            key = (current_location, current_mission_type, current_rotation, rarity, chance)
            if relic_name not in seen:
                seen[relic_name] = set()
            if key in seen[relic_name]:
                continue
            seen[relic_name].add(key)

            if relic_name not in results:
                results[relic_name] = []
            results[relic_name].append(entry)

    # Sort each relic's drop list: rotation order, then chance descending
    for drops in results.values():
        drops.sort(
            key=lambda d: (ROTATION_ORDER.get(d["rotation"], 99), -d["chance"])
        )

    return results


def main() -> None:
    html_path = DATA_DIR / "drops.html"
    if not html_path.exists():
        sys.exit(f"ERROR: {html_path} not found")

    print(f"Parsing {html_path} ...")
    try:
        drops = parse_mission_rewards(html_path)
    except ValueError as exc:
        sys.exit(f"ERROR: {exc}")

    total_entries = sum(len(v) for v in drops.values())
    print(f"Found {len(drops)} relics, {total_entries} total drop entries")

    out_path = DATA_DIR / "drops.json"
    out_path.write_text(json.dumps(drops, indent=2), encoding="utf-8")
    print(f"Written → {out_path}")

    # Quick sanity check
    sample_key = next(iter(drops))
    print(f"\nSample ({sample_key}):")
    for entry in drops[sample_key][:3]:
        print(f"  {entry}")


if __name__ == "__main__":
    main()
