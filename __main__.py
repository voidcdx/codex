"""
python -m dc — Warframe Damage Calculator CLI

Usage:
  python -m dc "Soma Prime" "Serration" "Split Chamber" vs "Heavy Gunner"
  python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" --crit average
  python -m dc "Soma Prime" vs "Heavy Gunner" --viral 5 --procs
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

from src.calculator import DamageCalculator, calculate_crit_multiplier, VIRAL_STACK_MULTIPLIERS
from src.loader import load_enemy, load_mod, load_weapon, list_enemies, list_mods, list_weapons, make_riven_mod, RIVEN_STAT_NAMES


def _parse_riven_arg(riven_str: str) -> list[dict]:
    """Parse '--riven damage:0.658,crit_chance:0.469' into stat dicts."""
    stats = []
    for pair in riven_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        key, _, val = pair.partition(":")
        key = key.strip()
        if key not in RIVEN_STAT_NAMES:
            valid = ", ".join(sorted(RIVEN_STAT_NAMES))
            print(f"Warning: unknown riven stat '{key}' — ignored. Valid: {valid}")
            continue
        stats.append({"stat": key, "value": float(val.strip())})
    return stats


def _print_results(
    weapon_name: str,
    mod_names: list[str],
    enemy_name: str,
    crit_mode: str,
    headshot: bool,
    attack_name: str | None = None,
    riven_str: str | None = None,
    viral_stacks: int = 0,
    corrosive_stacks: int = 0,
    show_procs: bool = False,
) -> None:
    weapon = load_weapon(weapon_name, attack_name=attack_name)
    mods   = [load_mod(m) for m in mod_names]
    if riven_str:
        mods.append(make_riven_mod(_parse_riven_arg(riven_str)))
    enemy  = load_enemy(enemy_name, headshot=headshot)

    # Crit stats come directly from the selected attack on the weapon
    total_cc = weapon.crit_chance + sum(m.cc_bonus for m in mods)
    total_cm = weapon.crit_multiplier + sum(m.cd_bonus for m in mods)
    crit_mult = calculate_crit_multiplier(total_cc, total_cm, mode=crit_mode)

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=headshot,
        viral_stacks=viral_stacks,
        corrosive_stacks=corrosive_stacks,
    )

    total = sum(result.values())

    # Determine which attack was used
    selected_attack_name = attack_name or (weapon.attacks[0].name if weapon.attacks else "")

    print(f"\nWeapon : {weapon.name}")
    if len(weapon.attacks) > 1:
        print(f"Attack : {selected_attack_name}")
    mod_display = ', '.join(mod_names) if mod_names else ''
    if riven_str:
        mod_display = (mod_display + ', Riven').lstrip(', ')
    print(f"Mods   : {mod_display or '(none)'}")
    print(f"Enemy  : {enemy.name}  [{enemy.faction.name}, {enemy.armor_type.name} armor,"
          f" {enemy.base_armor:.0f} base armor]")
    print(f"Crit   : {crit_mode}  CC={total_cc*100:.1f}%  CM={total_cm:.1f}x"
          f"  eff={crit_mult:.3f}x")
    if headshot:
        print(f"         (headshot: body part ×2; crit shots also double crit multiplier)")
    if viral_stacks > 0:
        vmult = VIRAL_STACK_MULTIPLIERS.get(min(viral_stacks, 10), 1.0)
        print(f"Viral  : {viral_stacks} stack{'s' if viral_stacks != 1 else ''}  (×{vmult})")
    if corrosive_stacks > 0:
        print(f"Corros.: {corrosive_stacks} stack{'s' if corrosive_stacks != 1 else ''}")
    print()
    print(f"{'Damage type':<18} {'Final damage':>14}")
    print("-" * 34)
    for dtype, val in sorted(result.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {dtype.name:<16} {val:>14.4f}")
    print("-" * 34)
    print(f"  {'TOTAL':<16} {total:>14.4f}")

    if show_procs:
        procs = calc.calculate_procs(
            weapon=weapon,
            mods=mods,
            enemy=enemy,
            crit_multiplier=crit_mult,
            is_crit_headshot=headshot,
        )
        _PROC_LABELS = {
            "slash":       "Slash (Bleed)",
            "heat":        "Heat  (Burn) ",
            "gas":         "Gas   (Cloud)",
            "toxin":       "Toxin (Poison)",
            "electricity": "Elec. (Arc)  ",
        }
        active = [(k, v) for k, v in procs.items() if v["active"]]
        if active:
            print()
            print(f"{'Status procs':<22} {'per tick':>10} {'total (6t)':>12}")
            print("-" * 46)
            for key, p in active:
                label = _PROC_LABELS.get(key, key)
                print(f"  {label:<20} {p['damage_per_tick']:>10.4f} {p['total_damage']:>12.4f}")
        else:
            print()
            print("  (no active status procs)")

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
                        help="Apply headshot (body part ×2; doubles crit mult on crit shots)")
    parser.add_argument("--attack", default=None,
                        help='Attack mode to use (e.g. "Rocket Explosion"). Defaults to first.')
    parser.add_argument("--riven", default=None,
                        help='Riven stats as "stat:value,..." e.g. "damage:0.658,crit_chance:0.469"')
    parser.add_argument("--viral", type=int, default=0, metavar="N",
                        help="Viral stacks on enemy (0–10, default: 0)")
    parser.add_argument("--corrosive", type=int, default=0, metavar="N",
                        help="Corrosive stacks on enemy (0–10, default: 0)")
    parser.add_argument("--procs", action="store_true",
                        help="Show status proc damage per tick and total")
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
        _print_results(
            weapon_name, mod_names, enemy_name, ns.crit, ns.headshot,
            ns.attack, ns.riven,
            viral_stacks=max(0, min(10, ns.viral)),
            corrosive_stacks=max(0, min(10, ns.corrosive)),
            show_procs=ns.procs,
        )
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
