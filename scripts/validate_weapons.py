#!/usr/bin/env python3
"""
validate_weapons.py
-------------------
Flags suspicious entries in data/weapons.json.

Checks per weapon / attack:
  - Missing or zero damage
  - CC / SC outside 0–1 range
  - Crit multiplier < 1.0 or suspiciously = 1.0
  - Fire rate = 0 or missing
  - Reload = 0 for non-melee weapons
  - Top-level stats don't match first attack (data sync error)
  - Damage value of exactly 100.0 on a single-element attack (common placeholder)
  - Attack missing required stat fields

Usage:
  python scripts/validate_weapons.py
  python scripts/validate_weapons.py --slot Primary
  python scripts/validate_weapons.py --severity high
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Severity levels
HIGH   = "HIGH"
MEDIUM = "MEDIUM"
LOW    = "LOW"

MELEE_SLOTS = {"Melee"}


@dataclass
class Issue:
    severity: str
    weapon: str
    attack: str | None
    message: str

    def __str__(self) -> str:
        loc = f"{self.weapon}" + (f" [{self.attack}]" if self.attack else "")
        return f"[{self.severity:6}] {loc}: {self.message}"


def _total_damage(attack: dict) -> float:
    total = 0.0
    for v in (attack.get("base_damage") or {}).values():
        total += float(v)
    for v in (attack.get("innate_elements") or {}).values():
        total += float(v)
    return total


def _is_placeholder_damage(attack: dict) -> bool:
    """Single-element attack with exactly 100.0 damage — classic scrape default."""
    base = attack.get("base_damage") or {}
    innate = attack.get("innate_elements") or {}
    combined = {**base, **innate}
    if len(combined) == 1:
        val = next(iter(combined.values()))
        if float(val) == 100.0:
            return True
    return False


def validate(weapons: dict, slot_filter: str | None = None) -> list[Issue]:
    issues: list[Issue] = []

    def flag(sev, name, atk_name, msg):
        issues.append(Issue(sev, name, atk_name, msg))

    for name, wep in weapons.items():
        slot = wep.get("slot", "")
        if slot_filter and slot.lower() != slot_filter.lower():
            continue

        attacks = wep.get("attacks", [])

        # ── Weapon-level checks ──────────────────────────────────────────
        if not attacks:
            flag(HIGH, name, None, "no attacks[] array")
            continue

        top_cc = wep.get("crit_chance")
        top_cm = wep.get("crit_multiplier")
        top_sc = wep.get("status_chance")
        top_fr = wep.get("fire_rate")

        first = attacks[0]
        atk_name = first.get("name", "attack[0]")

        # Top-level vs first-attack mismatch (sync errors from manual edits)
        if top_cc is not None and first.get("crit_chance") is not None:
            if abs(float(top_cc) - float(first["crit_chance"])) > 1e-6:
                flag(HIGH, name, None,
                     f"top-level CC {top_cc} ≠ first attack CC {first['crit_chance']}")

        if top_sc is not None and first.get("status_chance") is not None:
            if abs(float(top_sc) - float(first["status_chance"])) > 1e-6:
                flag(HIGH, name, None,
                     f"top-level SC {top_sc} ≠ first attack SC {first['status_chance']}")

        if top_fr is not None and first.get("fire_rate") is not None:
            if abs(float(top_fr) - float(first["fire_rate"])) > 1e-6:
                flag(MEDIUM, name, None,
                     f"top-level fire_rate {top_fr} ≠ first attack fire_rate {first['fire_rate']}")

        # Top-level stat range checks
        if top_cc is not None:
            if not (0.0 <= float(top_cc) <= 1.0):
                flag(HIGH, name, None, f"CC {top_cc} outside 0–1 range")
        if top_sc is not None:
            if not (0.0 <= float(top_sc) <= 1.0):
                flag(HIGH, name, None, f"SC {top_sc} outside 0–1 range")
        if top_cm is not None and float(top_cm) < 1.0:
            flag(HIGH, name, None, f"crit_multiplier {top_cm} < 1.0 (impossible)")

        # Reload sanity for non-melee
        if slot not in MELEE_SLOTS:
            reload_t = wep.get("reload", 0)
            if float(reload_t) == 0.0:
                flag(MEDIUM, name, None, "reload = 0 for non-melee weapon")

        # ── Per-attack checks ────────────────────────────────────────────
        for atk in attacks:
            aname = atk.get("name", "unnamed")

            # Missing damage entirely
            total = _total_damage(atk)
            if total == 0.0:
                flag(HIGH, name, aname, "total damage = 0")
                continue

            # Placeholder damage
            if _is_placeholder_damage(atk):
                flag(MEDIUM, name, aname,
                     "single-element damage = 100.0 (possible scrape default)")

            # Required stat fields
            for stat in ("crit_chance", "crit_multiplier", "status_chance", "fire_rate"):
                if atk.get(stat) is None:
                    flag(HIGH, name, aname, f"missing field: {stat}")

            # CC / SC range
            atk_cc = atk.get("crit_chance")
            atk_sc = atk.get("status_chance")
            if atk_cc is not None and not (0.0 <= float(atk_cc) <= 1.0):
                flag(HIGH, name, aname, f"CC {atk_cc} outside 0–1 range")
            if atk_sc is not None and not (0.0 <= float(atk_sc) <= 1.0):
                flag(HIGH, name, aname, f"SC {atk_sc} outside 0–1 range")

            # Crit multiplier
            atk_cm = atk.get("crit_multiplier")
            if atk_cm is not None:
                if float(atk_cm) < 1.0:
                    flag(HIGH, name, aname, f"crit_multiplier {atk_cm} < 1.0 (impossible)")
                elif float(atk_cm) == 1.0:
                    flag(LOW, name, aname, "crit_multiplier = 1.0 (no crit bonus — confirm intentional)")

            # Fire rate
            atk_fr = atk.get("fire_rate")
            if atk_fr is not None and float(atk_fr) == 0.0:
                flag(HIGH, name, aname, "fire_rate = 0")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate weapons.json for suspicious data")
    parser.add_argument("--slot", help="Filter by weapon slot (Primary, Secondary, Melee)")
    parser.add_argument("--severity", choices=["high", "medium", "low"],
                        help="Show only issues at this severity or above")
    parser.add_argument("--weapon", help="Check a single weapon by name")
    args = parser.parse_args()

    weapons: dict = json.loads((DATA_DIR / "weapons.json").read_text())

    if args.weapon:
        name = args.weapon
        # Case-insensitive match
        match = next((k for k in weapons if k.lower() == name.lower()), None)
        if not match:
            print(f"Weapon not found: {name!r}")
            return
        weapons = {match: weapons[match]}

    issues = validate(weapons, slot_filter=args.slot)

    # Filter by severity
    sev_order = {HIGH: 0, MEDIUM: 1, LOW: 2}
    min_sev = {"high": 0, "medium": 1, "low": 2}.get(args.severity or "low", 2)
    issues = [i for i in issues if sev_order[i.severity] <= min_sev]

    if not issues:
        print("✓ No issues found.")
        return

    # Group by severity for summary
    by_sev: dict[str, list[Issue]] = {HIGH: [], MEDIUM: [], LOW: []}
    for i in issues:
        by_sev[i.severity].append(i)

    for sev in (HIGH, MEDIUM, LOW):
        grp = by_sev[sev]
        if grp:
            print(f"\n── {sev} ({len(grp)}) ──────────────────────────────")
            for issue in sorted(grp, key=lambda x: x.weapon):
                print(f"  {issue}")

    total = len(issues)
    print(f"\n{total} issue(s): {len(by_sev[HIGH])} high, {len(by_sev[MEDIUM])} medium, {len(by_sev[LOW])} low")


if __name__ == "__main__":
    main()
