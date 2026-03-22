"""
One-shot patch: add missing secondary weapon-stat fields to data/mods.json.

For each mod that already has a primary stat but is missing a secondary weapon stat
(e.g. Chilling Reload has +40% Reload as secondary, Burdened Magazine has -18% Reload
as a penalty), extract the value from effect_raw and write the correct JSON field.

Handles: crit_chance_pct, crit_damage_pct, status_chance_pct, status_damage_pct,
         multishot_pct, reload_speed_pct, magazine_pct, ammo_max_pct, damage_bonus_pct
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "mods.json"

# ---------------------------------------------------------------------------
# Skip-list: mod-level substrings that indicate the effect is NOT a flat
# global weapon-stat bonus (augment, ability, companion, or conditional).
# ---------------------------------------------------------------------------
GLOBAL_SKIP = [
    "augment",
    "sentinel",
    "kavat",
    "kubrow",
    "companion",
    "cast ",          # ability cast
    "ability",
    " allies",
    "warframe",       # warframe ability mods
    "melee kills",    # on-kill trigger
    "whipclaw",       # augment
    "arcsphere",
    "decoy ",
    "vial rush",
    "artemis bow",
    "frost gains",
    "healing return", # on proc trigger
]

# Mod type values that indicate companion or hound mods (never weapon stats)
COMPANION_TYPES = {"kavat", "kubrow", "hound", "moa", "predasite", "vulpaphyla"}

# Conditional qualifiers that follow the stat name — make it contextual
STAT_SKIP = [
    "while aim",
    "while aiming",
    "when aim",
    "when aiming",
    "aim gliding",
    "on kill",
    "on headshot",
    "on weak point",
    "on mercy",
    "for \\d+s",     # timed buff (handled as regex below)
    "based on",
    "per stack",
    "per status",
    "per combo",     # combo-conditional (e.g. Weeping Wounds)
    " stacks",
    "up to ",
    "increased by",
    "gained from",
    "refills ",
    "per shot landed",
    "cannot be modified",
    "on reload:",
    "on shotguns",   # type-conditional (e.g. Amalgam Ripkas True Steel)
    "on rifles",
    "on pistols",
    "on primaries",
    "on secondaries",
    "for each ",     # per-mod conditional (e.g. Sil-Tabol)
    "critical chance and damage",  # combined — skip, too ambiguous
]

TIMED_RE = re.compile(r"for \d+s", re.IGNORECASE)


def is_global_skip(effect_raw: str, mod_type: str = "") -> bool:
    lower = effect_raw.lower()
    if any(phrase in lower for phrase in GLOBAL_SKIP):
        return True
    if mod_type.lower() in COMPANION_TYPES:
        return True
    return False


def has_stat_skip(effect_raw: str) -> bool:
    lower = effect_raw.lower()
    if any(phrase in lower for phrase in STAT_SKIP):
        return True
    if TIMED_RE.search(lower):
        return True
    return False


# ---------------------------------------------------------------------------
# Per-field extraction rules
# ---------------------------------------------------------------------------
# Each rule: (json_key, list_of_trigger_patterns, extra_skip_substrings)
# Trigger patterns are searched in effect_raw with re.search (IGNORECASE).
# Extra skip substrings are checked in addition to STAT_SKIP.
# ---------------------------------------------------------------------------
FIELD_RULES = [
    (
        "crit_chance_pct",
        [r"([+-]?\d+(?:\.\d+)?)%\s+Critical Chance(?!\s+and\b)"],
        ["per cent", "allies within"],
    ),
    (
        "crit_damage_pct",
        [r"([+-]?\d+(?:\.\d+)?)%\s+Critical Damage(?!\s+and\b)"],
        [],
    ),
    (
        "status_chance_pct",
        [r"([+-]?\d+(?:\.\d+)?)%\s+Status Chance"],
        ["guaranteed", "with a \d+%"],  # ability-triggered status
    ),
    (
        "status_damage_pct",
        [r"([+-]?\d+(?:\.\d+)?)%\s+Status Damage"],
        ["vulnerable to", "more status"],
    ),
    (
        "multishot_pct",
        [r"([+-]?\d+(?:\.\d+)?)%\s+Multishot"],
        ["amp multishot"],  # operator amp — not weapon
    ),
    (
        "reload_speed_pct",
        [
            r"([+-]?\d+(?:\.\d+)?)%\s+Reload Speed",
            r"([+-]?\d+(?:\.\d+)?)%\s+Reload Time",
        ],
        [],
    ),
    (
        "magazine_pct",
        [
            r"([+-]?\d+(?:\.\d+)?)%\s+Magazine Capacity",
            r"([+-]?\d+(?:\.\d+)?)%\s+Clip Size",
        ],
        ["charged chamber", "first shot"],  # per-shot conditional
    ),
    (
        "ammo_max_pct",
        [
            r"([+-]?\d+(?:\.\d+)?)%\s+Ammo Maximum",
            r"([+-]?\d+(?:\.\d+)?)%\s+Max(?:imum)? Ammo",
        ],
        [],
    ),
    (
        "damage_bonus_pct",
        [
            # Plain "+X% Damage" only — NOT melee/weak-point/status/ability/elemental/DoT
            r"([+-]?\d+(?:\.\d+)?)%\s+Damage(?!\s*(?:Type|Multiplier|per|on|to|against|while|for|when|bonus|over|block))",
        ],
        [
            "melee damage",
            "ability damage",
            "weak point damage",
            "status damage",
            "elemental damage",
            "armor damage",
            "shield damage",
            "health damage",
            "additional damage",
            "damage to ",
            "damage against",
            "+30% damage",   # Measured Burst is conditional "+30% Damage when aiming"
        ],
    ),
]


def extract_field(effect_raw: str, patterns: list[str]) -> float | None:
    """Return the first matching float value from effect_raw, or None."""
    for pat in patterns:
        m = re.search(pat, effect_raw, re.IGNORECASE)
        if m:
            return float(m.group(1)) / 100.0
    return None


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    total_patched = 0
    per_field: dict[str, list[str]] = {key: [] for key, _, _ in FIELD_RULES}

    for name, entry in data.items():
        effect_raw = entry.get("effect_raw", "")
        if not effect_raw:
            continue

        mod_type = entry.get("type", "")
        if is_global_skip(effect_raw, mod_type):
            continue

        if has_stat_skip(effect_raw):
            continue

        for json_key, patterns, extra_skips in FIELD_RULES:
            if json_key in entry:
                continue  # already set

            lower = effect_raw.lower()
            if any(s in lower for s in extra_skips):
                continue

            val = extract_field(effect_raw, patterns)
            if val is None:
                continue

            entry[json_key] = round(val, 4)
            per_field[json_key].append(name)
            total_patched += 1

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Patched {total_patched} field assignments across mods:\n")
    for json_key, names in per_field.items():
        if not names:
            continue
        print(f"  {json_key} ({len(names)}):")
        for n in sorted(names):
            val = data[n][json_key]
            sign = "+" if val > 0 else ""
            print(f"    {n:<45}  {sign}{val:.4f}")
        print()


if __name__ == "__main__":
    main()
