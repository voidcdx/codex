"""
python -m dc — Warframe Damage Calculator CLI

Usage:
  python -m dc "Soma Prime" "Serration" "Split Chamber" vs "Heavy Gunner"
  python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" --crit average
  python -m dc --list-weapons
  python -m dc --list-mods
  python -m dc --list-enemies
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as  python -m dc  from parent dir
_project_root = Path(__file__).parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.calculator import DamageCalculator, calculate_crit_multiplier
from src.loader import load_enemy, load_mod, load_weapon, list_enemies, list_mods, list_weapons


def _print_results(
    weapon_name: str,
    mod_names: list[str],
    enemy_name: str,
    crit_mode: str,
    headshot: bool,
) -> None:
    weapon = load_weapon(weapon_name)
    mods   = [load_mod(m) for m in mod_names]
    enemy  = load_enemy(enemy_name, headshot=headshot)

    # Compute total crit stats from weapon + mods
    crit_chance_base = 0.0  # weapons.json doesn't store crit_chance on the Weapon dataclass
    # Read directly from raw JSON for display stats
    from src.loader import _raw_weapons
    raw_w = _raw_weapons().get(weapon.name, {})
    base_cc = float(raw_w.get("crit_chance") or 0.0)
    base_cm = float(raw_w.get("crit_multiplier") or 1.0)

    from src.enums import DamageType
    cc_bonus = sum(
        float(getattr(m, "_crit_chance_bonus", 0))
        for m in mods
    )
    # For now: no crit mods parsed yet — use base values
    total_cc = base_cc
    total_cm = base_cm
    crit_mult = calculate_crit_multiplier(total_cc, total_cm, mode=crit_mode)

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=headshot,
    )

    total = sum(result.values())

    print(f"\nWeapon : {weapon.name}")
    print(f"Mods   : {', '.join(mod_names) if mod_names else '(none)'}")
    print(f"Enemy  : {enemy.name}  [{enemy.faction.name}, {enemy.armor_type.name} armor,"
          f" {enemy.base_armor:.0f} base armor]")
    print(f"Crit   : {crit_mode}  CC={total_cc*100:.1f}%  CM={total_cm:.1f}x"
          f"  eff={crit_mult:.3f}x")
    if headshot:
        print(f"         (headshot — crit multiplier doubled)")
    print()
    print(f"{'Damage type':<18} {'Final damage':>14}")
    print("-" * 34)
    for dtype, val in sorted(result.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {dtype.name:<16} {val:>14.4f}")
    print("-" * 34)
    print(f"  {'TOTAL':<16} {total:>14.4f}")
    print()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m dc",
        description="Warframe 100% Accurate Damage Calculator",
    )
    parser.add_argument("--list-weapons",  action="store_true", help="List all weapon names")
    parser.add_argument("--list-mods",     action="store_true", help="List all mod names")
    parser.add_argument("--list-enemies",  action="store_true", help="List all enemy names")
    parser.add_argument("--crit", choices=["average", "guaranteed", "max"],
                        default="average", help="Crit mode (default: average)")
    parser.add_argument("--headshot", action="store_true",
                        help="Apply headshot (doubles crit mult)")
    parser.add_argument("args", nargs="*",
                        help='"WeaponName" [ModName ...] [vs EnemyName]')

    ns = parser.parse_args(argv)

    if ns.list_weapons:
        for name in list_weapons():
            print(name)
        return

    if ns.list_mods:
        for name in list_mods():
            print(name)
        return

    if ns.list_enemies:
        for name in list_enemies():
            print(name)
        return

    args: list[str] = ns.args
    if not args:
        parser.print_help()
        sys.exit(0)

    # Split: weapon  [mods...]  [vs enemy]
    weapon_name = args[0]
    rest = args[1:]

    enemy_name: str | None = None
    if "vs" in rest:
        idx = rest.index("vs")
        mod_names = rest[:idx]
        after_vs = rest[idx + 1:]
        enemy_name = " ".join(after_vs) if after_vs else None
    else:
        mod_names = rest

    if enemy_name is None:
        print("Error: specify an enemy with  vs <EnemyName>")
        sys.exit(1)

    try:
        _print_results(weapon_name, mod_names, enemy_name, ns.crit, ns.headshot)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
