"""
python -m dc — Warframe Damage Calculator CLI

Usage:
  python -m dc "Soma Prime" "Serration" "Split Chamber" vs "Heavy Gunner"
  python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" --crit average
  python -m dc "Soma Prime" vs "Heavy Gunner" --viral 5 --procs
  python -m dc --list-weapons
  python -m dc --list-mods
  python -m dc --list-enemies
  python -m dc --list-body-parts "Heavy Gunner"
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
from src.loader import load_enemy, load_mod, load_weapon, list_enemies, list_mods, list_weapons, list_body_parts, make_riven_mod, RIVEN_STAT_NAMES


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
    body_part: str = "Body",
    attack_name: str | None = None,
    riven_str: str | None = None,
    viral_stacks: int = 0,
    corrosive_stacks: int = 0,
    combo_counter: int = 0,
    unique_statuses: int = 0,
    show_procs: bool = False,
) -> None:
    weapon = load_weapon(weapon_name, attack_name=attack_name)
    mods   = [load_mod(m) for m in mod_names]
    if riven_str:
        mods.append(make_riven_mod(_parse_riven_arg(riven_str)))
    enemy  = load_enemy(enemy_name, body_part=body_part)

    # Crit stats come directly from the selected attack on the weapon
    total_cc = weapon.crit_chance + sum(m.cc_bonus for m in mods)
    total_cm = weapon.crit_multiplier + sum(m.cd_bonus for m in mods)
    crit_mult = calculate_crit_multiplier(total_cc, total_cm, mode=crit_mode)
    modded_ms = 1.0 + sum(m.multishot_bonus for m in mods)

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=(body_part != "Body"),
        multishot=modded_ms,
        viral_stacks=viral_stacks,
        corrosive_stacks=corrosive_stacks,
        combo_counter=combo_counter,
        unique_statuses=unique_statuses,
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
    if body_part != "Body":
        mult = enemy.body_parts.get(body_part, 1.0)
        print(f"         ({body_part}: ×{mult} body part; crit shots also double crit multiplier)")
    if viral_stacks > 0:
        vmult = VIRAL_STACK_MULTIPLIERS.get(min(viral_stacks, 10), 1.0)
        print(f"Viral  : {viral_stacks} stack{'s' if viral_stacks != 1 else ''}  (×{vmult})")
    if corrosive_stacks > 0:
        print(f"Corros.: {corrosive_stacks} stack{'s' if corrosive_stacks != 1 else ''}")
    if combo_counter > 0:
        import math as _math
        cmult = 1.0 + 0.5 * _math.floor(combo_counter / 5)
        print(f"Combo  : {combo_counter} hits  (×{cmult:.2f})")
    if unique_statuses > 0:
        print(f"CO     : {unique_statuses} unique status type{'s' if unique_statuses != 1 else ''} on enemy")
    print()
    trigger_label = "Per-trigger" if modded_ms > 1.0001 else "Per-hit"
    print(f"{'Damage type':<18} {trigger_label + ' damage':>14}")
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
            is_crit_headshot=(body_part != "Body"),
        )
        _DOT_LABELS = {
            "slash":       "Slash (Bleed)",
            "heat":        "Heat  (Burn) ",
            "gas":         "Gas   (Cloud)",
            "toxin":       "Toxin (Poison)",
            "electricity": "Elec. (Arc)  ",
        }
        _CC_LABELS = {
            "viral":     "Viral Health Vulnr.",
            "magnetic":  "Magnetic (Shield) ",
            "radiation": "Radiation (Confuse)",
            "blast":     "Blast (Accuracy)  ",
            "cold":      "Cold  (Freeze)    ",
        }
        dot_active = [(k, v) for k, v in procs.items() if v["active"] and k in _DOT_LABELS]
        cc_active  = [(k, v) for k, v in procs.items() if v["active"] and k in _CC_LABELS]

        if dot_active:
            print()
            print(f"{'Status procs (DoT)':<22} {'per tick':>10} {'total (6t)':>12}")
            print("-" * 46)
            for key, p in dot_active:
                label = _DOT_LABELS[key]
                print(f"  {label:<20} {p['damage_per_tick']:>10.4f} {p['total_damage']:>12.4f}")

        if cc_active:
            print()
            print(f"{'Status CC/Debuffs':<28} {'Effect'}")
            print("-" * 70)
            for key, p in cc_active:
                label = _CC_LABELS[key]
                print(f"  {label:<26} {p['effect']}")

        if not dot_active and not cc_active:
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
    parser.add_argument("--list-body-parts", default=None, metavar="ENEMY",
                        help="List body parts and multipliers for an enemy")
    parser.add_argument("--crit", choices=["average", "guaranteed", "max"],
                        default="average", help="Crit mode (default: average)")
    parser.add_argument("--body-part", default="Body", metavar="PART",
                        help='Body part to target (e.g. "Head", "Body"). Default: Body')
    parser.add_argument("--headshot", action="store_true",
                        help="Alias for --body-part Head")
    parser.add_argument("--attack", default=None,
                        help='Attack mode to use (e.g. "Rocket Explosion"). Defaults to first.')
    parser.add_argument("--riven", default=None,
                        help='Riven stats as "stat:value,..." e.g. "damage:0.658,crit_chance:0.469"')
    parser.add_argument("--viral", type=int, default=0, metavar="N",
                        help="Viral stacks on enemy (0–10, default: 0)")
    parser.add_argument("--corrosive", type=int, default=0, metavar="N",
                        help="Corrosive stacks on enemy (0–10, default: 0)")
    parser.add_argument("--combo", type=int, default=0, metavar="N",
                        help="Melee combo hit count (0–12000, default: 0)")
    parser.add_argument("--statuses", type=int, default=0, metavar="N",
                        help="Unique active status types on enemy (0–10, for Condition Overload)")
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

    if ns.list_body_parts:
        try:
            parts = list_body_parts(ns.list_body_parts)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
        for part, mult in parts.items():
            print(f"{part}: ×{mult}")
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
        effective_part = "Head" if ns.headshot else ns.body_part
        _print_results(
            weapon_name, mod_names, enemy_name, ns.crit, effective_part,
            ns.attack, ns.riven,
            viral_stacks=max(0, min(10, ns.viral)),
            corrosive_stacks=max(0, min(10, ns.corrosive)),
            combo_counter=max(0, ns.combo),
            unique_statuses=max(0, min(10, ns.statuses)),
            show_procs=ns.procs,
        )
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
