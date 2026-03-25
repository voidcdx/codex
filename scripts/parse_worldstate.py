#!/usr/bin/env python3
"""
Parse raw Warframe worldstate JSON → clean, human-readable worldstate.json.

Input:  data/worldstate_raw.json   (from fetch_worldstate.py or browser download)
Input:  data/solnode_map.json      (from fetch_solnodes.py, optional but improves node names)
Output: data/worldstate.json

Can also be imported and called from web/api.py for live parsing.

Run:
  python scripts/parse_worldstate.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Node / mission type lookup tables
# ---------------------------------------------------------------------------

# Tier name from the internal fissure modifier key
FISSURE_TIERS: dict[str, str] = {
    "VoidT1": "Lith",
    "VoidT2": "Meso",
    "VoidT3": "Neo",
    "VoidT4": "Axi",
    "VoidT5": "Requiem",
    "VoidT6": "Omnia",
}

# Mission type path suffix → display name
MISSION_TYPES: dict[str, str] = {
    "Assassination":       "Assassination",
    "Assault":             "Assault",
    "Capture":             "Capture",
    "Defense":             "Defense",
    "Disruption":          "Disruption",
    "Excavation":          "Excavation",
    "Exterminate":         "Exterminate",
    "Hive":                "Hive",
    "Hijack":              "Hijack",
    "Infested":            "Infested Salvage",
    "InfestedSalvage":     "Infested Salvage",
    "Interception":        "Interception",
    "Junction":            "Junction",
    "MobileDefense":       "Mobile Defense",
    "Pursuit":             "Pursuit",
    "Rescue":              "Rescue",
    "Sabotage":            "Sabotage",
    "Spy":                 "Spy",
    "Survival":            "Survival",
    "Excavation":          "Excavation",
    "LongSurvival":        "Endurance",
    "RailjackAerial":      "Skirmish",
    "RailjackMission":     "Railjack",
    "VoidCascade":         "Void Cascade",
    "VoidFlood":           "Void Flood",
    "VoidArmageddon":      "Void Armageddon",
    "Assassination":       "Assassination",
    "GasCity":             "Gas City",
    "ArchwingAssassination": "Archwing Assassination",
}

FACTION_NAMES: dict[str, str] = {
    "FC_GRINEER":   "Grineer",
    "FC_CORPUS":    "Corpus",
    "FC_INFESTATION": "Infested",
    "FC_OROKIN":    "Orokin",
    "FC_TENNO":     "Tenno",
    "FC_MURMUR":    "Murmur",
    "FC_NARMER":    "Narmer",
    "FC_CORRUPTED": "Corrupted",
    "FC_SCALDRA":   "Scaldra",
    "FC_TECHROT":   "Techrot",
}

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _parse_date(val: Any) -> datetime | None:
    """
    Parse Warframe's BSON-style date:
      {"$date": {"$numberLong": "1234567890000"}}   — milliseconds
      {"$date": 1234567890000}                      — milliseconds int
      1234567890                                    — seconds int
    Returns UTC datetime or None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        # Assume seconds if < 1e11, else milliseconds
        ts = val / 1000 if val > 1e11 else val
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(val, dict):
        inner = val.get("$date")
        if isinstance(inner, dict):
            ms = int(inner.get("$numberLong", 0))
        elif isinstance(inner, (int, float)):
            ms = int(inner)
        else:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return None


def _eta(expiry: datetime | None) -> str:
    """Human-readable time-until from now (UTC)."""
    if expiry is None:
        return "?"
    now = datetime.now(tz=timezone.utc)
    delta = expiry - now
    total = int(delta.total_seconds())
    if total <= 0:
        return "Expired"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


# ---------------------------------------------------------------------------
# Node name lookup
# ---------------------------------------------------------------------------

def _load_solnode_map() -> dict[str, dict]:
    p = DATA_DIR / "solnode_map.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _node_display(node_key: str, solnode_map: dict[str, dict]) -> str:
    """
    Convert a node key to human-readable 'Name (Planet)'.
    node_key may be:
      - 'SolNode1' → look up in solnode_map
      - '/Lotus/Levels/.../MercuryCapture' → strip path, look up last segment
      - 'MercuryCapture' → look up directly
    """
    key = node_key.rstrip("/").rsplit("/", 1)[-1] if "/" in node_key else node_key

    info = solnode_map.get(key) or solnode_map.get(node_key) or {}
    name = info.get("name", "")
    planet = info.get("planet", "")

    if name and planet:
        return f"{name} ({planet})"
    if name:
        return name

    # Fallback: humanise the key itself (e.g. 'SolNode1' stays as-is; 'MercuryCapture' → 'Capture (Mercury)')
    # Try to split CamelCase planet prefix
    match = re.match(r"([A-Z][a-z]+)(.+)", key)
    if match:
        planet_hint, rest = match.groups()
        # un-camel the mission
        mission = re.sub(r"([A-Z])", r" \1", rest).strip()
        return f"{mission} ({planet_hint})"
    return key


def _mission_type(type_key: str) -> str:
    """Strip Lotus path and look up human name."""
    suffix = type_key.rstrip("/").rsplit("/", 1)[-1] if "/" in type_key else type_key
    return MISSION_TYPES.get(suffix, suffix)


def _faction(faction_key: str) -> str:
    return FACTION_NAMES.get(faction_key, faction_key)


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------

def _parse_fissures(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for f in raw:
        expiry = _parse_date(f.get("Expiry"))
        if expiry and expiry < datetime.now(tz=timezone.utc):
            continue  # skip expired

        modifier = f.get("Modifier", "")
        tier = FISSURE_TIERS.get(modifier, modifier)

        mission_key = f.get("MissionType", "")
        is_storm = "VoidStorm" in mission_key or "VoidArmageddon" in mission_key or "VoidCascade" in mission_key or "VoidFlood" in mission_key
        is_hard = f.get("Hard", False)

        out.append({
            "node":         _node_display(f.get("Node", ""), solnode_map),
            "mission_type": _mission_type(mission_key),
            "enemy":        _faction(f.get("Faction", "")),
            "tier":         tier,
            "eta":          _eta(expiry),
            "is_storm":     is_storm,
            "is_steel_path": is_hard,
        })

    # Sort: Lith → Meso → Neo → Axi → others
    tier_order = {"Lith": 0, "Meso": 1, "Neo": 2, "Axi": 3, "Requiem": 4, "Omnia": 5}
    out.sort(key=lambda x: tier_order.get(x["tier"], 99))
    return out


def _parse_alerts(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for a in raw:
        expiry = _parse_date(a.get("Expiry"))
        if expiry and expiry < datetime.now(tz=timezone.utc):
            continue

        mission = a.get("MissionInfo", {})
        reward = mission.get("missionReward", {})
        items = reward.get("items", []) or []
        counted = reward.get("countedItems", []) or []
        credits = reward.get("credits", 0)

        reward_parts = []
        for ci in counted:
            ct = ci.get("ItemCount", 1)
            nm = ci.get("ItemType", "").rstrip("/").rsplit("/", 1)[-1]
            reward_parts.append(f"{ct}× {nm}" if ct > 1 else nm)
        for it in items:
            reward_parts.append(it.rstrip("/").rsplit("/", 1)[-1])
        if credits:
            reward_parts.append(f"{credits:,} Credits")

        out.append({
            "node":         _node_display(mission.get("location", ""), solnode_map),
            "mission_type": _mission_type(mission.get("missionType", "")),
            "faction":      _faction(mission.get("faction", "")),
            "reward":       ", ".join(reward_parts) or "Unknown",
            "eta":          _eta(expiry),
        })
    return out


def _parse_sortie(raw: list, solnode_map: dict) -> dict | None:
    if not raw:
        return None
    s = raw[0]
    expiry = _parse_date(s.get("Expiry"))
    variants = s.get("Variants", [])
    missions = []
    for v in variants:
        missions.append({
            "node":         _node_display(v.get("node", ""), solnode_map),
            "mission_type": _mission_type(v.get("missionType", "")),
            "modifier":     v.get("modifierType", ""),
        })
    boss_path = s.get("Boss", "")
    boss = boss_path.rstrip("/").rsplit("/", 1)[-1].replace("Boss", "").strip()
    faction_key = s.get("Faction", "")
    return {
        "boss":     boss or "Unknown",
        "faction":  _faction(faction_key),
        "eta":      _eta(expiry),
        "missions": missions,
    }


def _parse_archon_hunt(raw: list, solnode_map: dict) -> dict | None:
    # Archon Hunt is often in Goals[] filtered by tag, or its own key
    if not raw:
        return None
    # Take the first entry that looks like an archon hunt (has Boss field)
    for entry in raw:
        if not entry.get("Boss"):
            continue
        expiry = _parse_date(entry.get("Expiry"))
        variants = entry.get("Variants", [])
        missions = []
        for v in variants:
            missions.append({
                "node":         _node_display(v.get("node", ""), solnode_map),
                "mission_type": _mission_type(v.get("missionType", "")),
                "modifier":     v.get("modifierType", ""),
            })
        boss_path = entry.get("Boss", "")
        boss = boss_path.rstrip("/").rsplit("/", 1)[-1]
        return {
            "boss":     boss,
            "faction":  _faction(entry.get("Faction", "")),
            "eta":      _eta(expiry),
            "missions": missions,
        }
    return None


def _parse_void_trader(raw: list, solnode_map: dict) -> dict:
    if not raw:
        return {"active": False, "eta": "Unknown", "node": "", "inventory": []}

    trader = raw[0]
    activation = _parse_date(trader.get("Activation"))
    expiry = _parse_date(trader.get("Expiry"))
    now = datetime.now(tz=timezone.utc)

    active = activation is not None and activation <= now and (expiry is None or expiry > now)

    inventory = []
    for item in trader.get("Manifest", []):
        item_path = item.get("ItemType", "")
        item_name = item_path.rstrip("/").rsplit("/", 1)[-1]
        inventory.append({
            "item":    item_name,
            "ducats":  item.get("PrimePrice", 0),
            "credits": item.get("RegularPrice", 0),
        })

    return {
        "active":    active,
        "node":      _node_display(trader.get("Node", ""), solnode_map),
        "eta":       _eta(expiry if active else activation),
        "arrives":   activation.isoformat() if activation else None,
        "departs":   expiry.isoformat() if expiry else None,
        "inventory": inventory,
    }


def _parse_nightwave(raw: list) -> dict | None:
    # Nightwave is a syndicate; look for the RadioLegion tag
    nw = next((s for s in raw if "RadioLegion" in s.get("Tag", "")), None)
    if not nw:
        return None

    expiry = _parse_date(nw.get("Expiry"))
    challenges = []
    for ch in nw.get("ActiveChallenges", []):
        ch_expiry = _parse_date(ch.get("Expiry"))
        info = ch.get("Challenge", "")
        # Challenge path like /Lotus/Types/Challenges/...
        title = info.rstrip("/").rsplit("/", 1)[-1] if "/" in info else info
        challenges.append({
            "title":      title,
            "reputation": ch.get("xpAmount", 0),
            "is_daily":   ch.get("isDaily", False),
            "is_elite":   ch.get("isElite", False),
            "eta":        _eta(ch_expiry),
        })

    return {
        "season": nw.get("Season", 0),
        "phase":  nw.get("Phase", 0),
        "eta":    _eta(expiry),
        "active_challenges": challenges,
    }


def _parse_cycles(raw: dict) -> list[dict]:
    """Parse open-world day/night and warm/cold cycle states."""
    cycles: list[dict] = []
    now = datetime.now(tz=timezone.utc)

    # ── Cetus / Plains of Eidolon (computed from known cycle constants) ──────
    # Community-derived: total 9000 s cycle, 6000 s day, 3000 s night.
    # Reference epoch ≈ Nov 4 2017 (Plains of Eidolon launch).
    try:
        from datetime import timedelta
        day_s, night_s = 6000, 3000
        cycle_s = day_s + night_s
        epoch_s = 1509785490
        elapsed = int(now.timestamp() - epoch_s) % cycle_s
        is_day   = elapsed < day_s
        secs_left = (day_s - elapsed) if is_day else (cycle_s - elapsed)
        cycles.append({
            "location": "Cetus",
            "state":    "Day"   if is_day else "Night",
            "eta":      _eta(now + timedelta(seconds=secs_left)),
        })
    except Exception:
        pass

    # ── Orb Vallis warm / cold ────────────────────────────────────────────────
    vallis = raw.get("VallisCycle")
    if isinstance(vallis, dict):
        expiry_dt = _parse_date(vallis.get("expiry") or vallis.get("Expiry"))
        raw_state = vallis.get("state", vallis.get("isDay", "cold"))
        is_warm   = (raw_state is True) or str(raw_state).lower() in ("warm", "true", "day")
        cycles.append({
            "location": "Orb Vallis",
            "state":    "Warm" if is_warm else "Cold",
            "eta":      _eta(expiry_dt),
        })

    # ── Cambion Drift fass / vome ─────────────────────────────────────────────
    cambion = raw.get("CambionCycle")
    if isinstance(cambion, dict):
        expiry_dt = _parse_date(cambion.get("expiry") or cambion.get("Expiry"))
        active    = str(cambion.get("active", cambion.get("state", ""))).lower()
        is_fass   = active == "fass" or cambion.get("isDay", False) is True
        cycles.append({
            "location": "Cambion Drift",
            "state":    "Fass" if is_fass else "Vome",
            "eta":      _eta(expiry_dt),
        })

    # ── Zariman Ten Zero corpus / grineer ─────────────────────────────────────
    zariman = raw.get("ZarimanCycle")
    if isinstance(zariman, dict):
        expiry_dt = _parse_date(zariman.get("expiry") or zariman.get("Expiry"))
        raw_state = zariman.get("state", zariman.get("isDay", "grineer"))
        is_corpus = (raw_state is True) or str(raw_state).lower() in ("corpus", "true", "day")
        cycles.append({
            "location": "Zariman Ten Zero",
            "state":    "Corpus" if is_corpus else "Grineer",
            "eta":      _eta(expiry_dt),
        })

    return cycles


def _parse_events(raw: dict) -> list[dict]:
    """Parse active, non-expired game events."""
    out: list[dict] = []
    now = datetime.now(tz=timezone.utc)
    for ev in raw.get("Events", []):
        try:
            expiry = _parse_date(ev.get("Expiry"))
            if expiry and expiry < now:
                continue

            # Name: try Description → Messages → Tag
            desc = ev.get("Description", {})
            name = (desc.get("value", "") if isinstance(desc, dict) else str(desc)) if desc else ""
            if not name:
                msgs = ev.get("Messages", [])
                if msgs and isinstance(msgs[0], dict):
                    name = msgs[0].get("message", "")
            if not name:
                name = ev.get("Tag", "")
            if not name:
                continue

            # Reward hint
            rewards = ev.get("Rewards", [])
            reward = ""
            if rewards and isinstance(rewards[0], dict):
                r = rewards[0]
                items = r.get("items") or r.get("Items") or []
                credits = r.get("credits", r.get("Credits", 0))
                if items:
                    first = items[0]
                    reward = first if isinstance(first, str) else first.get("ItemType", "").rsplit("/", 1)[-1]
                elif credits:
                    reward = f"{int(credits):,} Credits"

            out.append({
                "name":   name[:60],
                "eta":    _eta(expiry),
                "reward": reward[:50],
            })
        except Exception:
            continue
    return out[:10]


def _parse_invasions(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for inv in raw:
        # Skip completed invasions
        if inv.get("Completed", False):
            continue
        expiry = _parse_date(inv.get("Expiry"))

        def _reward(side: dict) -> str:
            reward = side.get("MissionInfo", {}).get("missionReward", {})
            counted = reward.get("countedItems", [])
            items = reward.get("items", [])
            parts = []
            for ci in counted:
                ct = ci.get("ItemCount", 1)
                nm = ci.get("ItemType", "").rstrip("/").rsplit("/", 1)[-1]
                parts.append(f"{ct}× {nm}" if ct > 1 else nm)
            for it in items:
                parts.append(it.rstrip("/").rsplit("/", 1)[-1])
            cr = reward.get("credits", 0)
            if cr:
                parts.append(f"{cr:,} cr")
            return ", ".join(parts) or "Unknown"

        attacker = inv.get("AttackerInfo", {})
        defender = inv.get("DefenderInfo", {})

        # Progress: positive = attacker winning, negative = defender winning
        # Count field: number of runs completed; goal varies
        count = inv.get("Count", 0)
        required = inv.get("Goal", 1)
        # Invaders start at Goal (negative) and go to 0; or 0 to Goal for normal
        progress = min(100.0, max(0.0, abs(count) / max(required, 1) * 100))

        out.append({
            "node":              _node_display(inv.get("Node", ""), solnode_map),
            "attacker":          _faction(attacker.get("faction", "")),
            "defender":          _faction(defender.get("faction", "")),
            "attacker_reward":   _reward(attacker),
            "defender_reward":   _reward(defender),
            "progress":          round(progress, 1),
            "eta":               _eta(expiry),
            "vs_infestation":    attacker.get("faction", "") == "FC_INFESTATION" or defender.get("faction", "") == "FC_INFESTATION",
        })
    return out


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse(raw: dict) -> dict:
    """Parse a raw worldstate dict → clean structured dict."""
    solnode_map = _load_solnode_map()

    return {
        "fissures":    _parse_fissures(raw.get("ActiveMissions", []), solnode_map),
        "alerts":      _parse_alerts(raw.get("Alerts", []), solnode_map),
        "sortie":      _parse_sortie(raw.get("Sorties", []), solnode_map),
        "archon_hunt": _parse_archon_hunt(raw.get("LevelOverrides", []) or raw.get("Goals", []), solnode_map),
        "void_trader": _parse_void_trader(raw.get("VoidTraders", []), solnode_map),
        "nightwave":   _parse_nightwave(raw.get("SyndicateMissions", [])),
        "invasions":   _parse_invasions(raw.get("Invasions", []), solnode_map),
        "cycles":      _parse_cycles(raw),
        "events":      _parse_events(raw),
    }


def main() -> None:
    raw_path = DATA_DIR / "worldstate_raw.json"
    if not raw_path.exists():
        print(f"✗ {raw_path} not found.")
        print("  Run:  python scripts/fetch_worldstate.py")
        print("  Or download manually and save as data/worldstate_raw.json")
        return

    print(f"Parsing {raw_path} …")
    raw = json.loads(raw_path.read_text())
    result = parse(raw)

    out = DATA_DIR / "worldstate.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✓ Saved → {out}")

    # Summary
    print(f"  Fissures:   {len(result['fissures'])}")
    print(f"  Alerts:     {len(result['alerts'])}")
    print(f"  Sortie:     {'yes' if result['sortie'] else 'no'}")
    print(f"  Archon Hunt:{'yes' if result['archon_hunt'] else 'no'}")
    print(f"  Void Trader: {'active' if result.get('void_trader', {}).get('active') else 'inactive'}")
    nw = result.get("nightwave")
    print(f"  Nightwave:  {len(nw['active_challenges']) if nw else 0} challenges")
    print(f"  Invasions:  {len(result['invasions'])}")


if __name__ == "__main__":
    main()
