import math
from decimal import Decimal
from src.enums import DamageType, FactionType
from src.models import Weapon, Mod, Enemy, DamageComponent
from src.quantizer import quantize, quantize_components
from src.combiner import combine_elements, PRIMARY_ELEMENTS
from src.scaling import scale_enemy_stats

# ---------------------------------------------------------------------------
# Damage type effectiveness table (Update 36.0+)
# Key: (FactionType, DamageType) → multiplier
# Omitted entries = 1.0 (neutral). Vulnerable=×1.5, Resistant=×0.5
# Source: wiki.warframe.com/w/Damage/Overview (extracted 2026-03-21)
# ---------------------------------------------------------------------------
FACTION_EFFECTIVENESS: dict[tuple[FactionType, DamageType], float] = {
    # ── Impact ──────────────────────────────────────────────────────────────
    (FactionType.GRINEER,        DamageType.IMPACT): 1.5,
    (FactionType.KUVA_GRINEER,   DamageType.IMPACT): 1.5,
    (FactionType.SCALDRA,        DamageType.IMPACT): 1.5,
    (FactionType.ANARCHS,        DamageType.IMPACT): 1.5,
    # ── Puncture ─────────────────────────────────────────────────────────────
    (FactionType.CORPUS,         DamageType.PUNCTURE): 1.5,
    (FactionType.CORRUPTED,      DamageType.PUNCTURE): 1.5,
    # ── Slash ────────────────────────────────────────────────────────────────
    (FactionType.INFESTED,       DamageType.SLASH): 1.5,
    (FactionType.NARMER,         DamageType.SLASH): 1.5,
    # ── Cold ─────────────────────────────────────────────────────────────────
    (FactionType.SENTIENT,       DamageType.COLD): 1.5,
    (FactionType.TECHROT,        DamageType.COLD): 0.5,
    # ── Electricity ──────────────────────────────────────────────────────────
    (FactionType.CORPUS_AMALGAM, DamageType.ELECTRICITY): 1.5,
    (FactionType.MURMUR,         DamageType.ELECTRICITY): 1.5,
    (FactionType.ANARCHS,        DamageType.ELECTRICITY): 1.5,
    # ── Heat ─────────────────────────────────────────────────────────────────
    (FactionType.KUVA_GRINEER,   DamageType.HEAT): 0.5,
    (FactionType.INFESTED,       DamageType.HEAT): 1.5,
    # ── Toxin ────────────────────────────────────────────────────────────────
    (FactionType.NARMER,         DamageType.TOXIN): 1.5,
    # ── Blast ────────────────────────────────────────────────────────────────
    (FactionType.CORPUS_AMALGAM, DamageType.BLAST): 0.5,
    (FactionType.DEIMOS_INFESTED,DamageType.BLAST): 1.5,
    # ── Corrosive ────────────────────────────────────────────────────────────
    (FactionType.GRINEER,        DamageType.CORROSIVE): 1.5,
    (FactionType.KUVA_GRINEER,   DamageType.CORROSIVE): 1.5,
    (FactionType.SENTIENT,       DamageType.CORROSIVE): 0.5,
    (FactionType.SCALDRA,        DamageType.CORROSIVE): 1.5,
    # ── Gas ──────────────────────────────────────────────────────────────────
    (FactionType.DEIMOS_INFESTED,DamageType.GAS): 1.5,
    (FactionType.SCALDRA,        DamageType.GAS): 0.5,
    (FactionType.TECHROT,        DamageType.GAS): 1.5,
    # ── Magnetic ─────────────────────────────────────────────────────────────
    (FactionType.CORPUS,         DamageType.MAGNETIC): 1.5,
    (FactionType.CORPUS_AMALGAM, DamageType.MAGNETIC): 1.5,
    (FactionType.NARMER,         DamageType.MAGNETIC): 0.5,
    (FactionType.TECHROT,        DamageType.MAGNETIC): 1.5,
    # ── Radiation ────────────────────────────────────────────────────────────
    (FactionType.CORRUPTED,      DamageType.RADIATION): 0.5,
    (FactionType.SENTIENT,       DamageType.RADIATION): 1.5,
    (FactionType.MURMUR,         DamageType.RADIATION): 1.5,
    (FactionType.ANARCHS,        DamageType.RADIATION): 0.5,
    # ── Viral ────────────────────────────────────────────────────────────────
    (FactionType.DEIMOS_INFESTED,DamageType.VIRAL): 0.5,
    (FactionType.CORRUPTED,      DamageType.VIRAL): 1.5,
    (FactionType.MURMUR,         DamageType.VIRAL): 0.5,
}



# ---------------------------------------------------------------------------
# Bane Mods (faction damage multipliers)
# Standard Bane mods: +30% at max rank
# Primed Bane mods:   +55% at max rank
# Formula (Step 3): Modded Damage × (1 + faction_bonus)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Viral status proc multipliers per stack count (1–10)
# Source: wiki.warframe.com/w/Damage/Viral_Damage
# ---------------------------------------------------------------------------
VIRAL_STACK_MULTIPLIERS: dict[int, float] = {
    0: 1.00,
    1: 1.75,
    2: 2.00,
    3: 2.25,
    4: 2.50,
    5: 2.75,
    6: 3.00,
    7: 3.25,
    8: 3.50,
    9: 3.75,
    10: 4.25,
}


BANE_MODS: dict[str, Mod] = {
    # Standard
    "Bane of Grineer":   Mod("Bane of Grineer",   faction_bonus=0.30, faction_type=FactionType.GRINEER),
    "Bane of Corpus":    Mod("Bane of Corpus",     faction_bonus=0.30, faction_type=FactionType.CORPUS),
    "Bane of Infested":  Mod("Bane of Infested",   faction_bonus=0.30, faction_type=FactionType.INFESTED),
    "Bane of Corrupted": Mod("Bane of Corrupted",  faction_bonus=0.30, faction_type=FactionType.CORRUPTED),
    # Primed
    "Primed Bane of Grineer":   Mod("Primed Bane of Grineer",   faction_bonus=0.55, faction_type=FactionType.GRINEER),
    "Primed Bane of Corpus":    Mod("Primed Bane of Corpus",     faction_bonus=0.55, faction_type=FactionType.CORPUS),
    "Primed Bane of Infested":  Mod("Primed Bane of Infested",   faction_bonus=0.55, faction_type=FactionType.INFESTED),
    "Primed Bane of Corrupted": Mod("Primed Bane of Corrupted",  faction_bonus=0.55, faction_type=FactionType.CORRUPTED),
}


def crit_tier(total_cc: float) -> int:
    """Crit Tier T = floor(total_crit_chance).

    Args:
        total_cc: Crit chance as a decimal (1.65 = 165%). NOT a percentage.
    """
    return math.floor(total_cc)


def calculate_crit_multiplier(
    total_cc: float,
    modded_cm: float,
    mode: str = "average",
) -> float:
    """Critical hit damage multiplier.

    Args:
        total_cc:  Total crit chance as a decimal (e.g. 1.65 for 165%).
        modded_cm: Modded crit multiplier (e.g. 3.5 for 350%).
        mode:      "average"   — weighted average across all possible tiers (DPS use)
                   "guaranteed"— floor tier only, worst case per-hit
                   "max"       — ceiling tier, best case per-hit

    Formula: M_crit = 1 + T × (modded_cm − 1)
    Average is exact for all tiers: 1 + total_cc × (modded_cm − 1)
    """
    d_cc = Decimal(str(total_cc))
    d_cm = Decimal(str(modded_cm))
    if mode == "average":
        return float(Decimal('1') + d_cc * (d_cm - Decimal('1')))
    if mode == "guaranteed":
        T = Decimal(crit_tier(total_cc))
        return float(Decimal('1') + T * (d_cm - Decimal('1')))
    if mode == "max":
        T = Decimal(crit_tier(total_cc) + 1)
        return float(Decimal('1') + T * (d_cm - Decimal('1')))
    raise ValueError(f"Unknown mode {mode!r}. Use 'average', 'guaranteed', or 'max'.")


def calculate_armor_multiplier(armor: float) -> float:
    """Damage fraction passing through armor (Update 36+: flat DR only).

    Post-Update 36 (Jade Shadows): Ferrite/Alloy armor types no longer exist.
    Armor provides flat damage reduction only: DR = armor / (armor + 300),
    capped at 2,700 armor (90% DR). All damage type modifiers are faction-based.
    Returns 1.0 when there is no armor.
    """
    if armor <= 0.0:
        return 1.0
    clamped = min(2700.0, armor)
    return 300.0 / (300.0 + clamped)


class DamageCalculator:
    """Implements the 5-step Warframe damage pipeline.

    Step 1: Base Damage × (1 + ΣDamageMods)      → Modded Base   [math.floor]
    Step 2: Modded Base × Body Part Multiplier    → Part Damage   [warframe_round]
    Step 3: Part Damage × DamageType Multiplier   → Typed Dmg     [math.floor]
    Step 4: Typed Dmg × Armor Mitigation          → Mitigated Dmg [math.floor]
    Step 5: Mitigated Dmg × (1 + FactionMod)      → Final Dmg     [math.floor]

    Crit-on-headshot: if is_crit=True and body_part_multiplier > 1,
    the crit multiplier is doubled before applying to Step 2 output.
    """

    def calculate(
        self,
        weapon: Weapon,
        mods: list[Mod],      # ordered by slot position (slot 0 = top-left)
        enemy: Enemy,
        crit_multiplier: float = 1.0,   # pass calculate_crit_multiplier() result
        is_crit_headshot: bool = False,  # doubles crit multiplier on headshots
        multishot: float = 1.0,         # total projectiles per trigger (1 + Σ multishot mods)
        viral_stacks: int = 0,          # 0–10 Viral status stacks on the enemy
        corrosive_stacks: int = 0,     # 0–10 Corrosive status stacks on the enemy
        enemy_level: int = 1,          # target enemy level (1–9999)
        steel_path: bool = False,      # Steel Path: +100 level, ×2.5 HP/shields
        eximus: bool = False,          # Eximus unit
        combo_counter: int = 0,        # melee combo hit count; mult = 1 + 0.5×floor(count/5)
        unique_statuses: int = 0,      # unique active status types on enemy (for Condition Overload)
        galvanized_stacks: int = 0,    # 0–5 galvanized mod kill-stacks active
    ) -> dict[DamageType, float]:
        """Return final per-trigger damage values after the full pipeline (includes multishot)."""
        base_damage = weapon.total_base_damage

        # --- Collect mod bonuses ---
        total_damage_bonus = sum(m.damage_bonus for m in mods)
        # Condition Overload: additive +N% per unique status type on enemy
        co_total = sum(m.condition_overload_bonus for m in mods) * unique_statuses
        # Galvanized Aptitude/Savvy/Shot: +galv_kill_pct% damage per unique status type per stack
        galv_aptitude_total = sum(
            m.galv_kill_pct * min(galvanized_stacks, m.galv_max_stacks) * unique_statuses
            for m in mods
            if m.galv_kill_stat == "aptitude_damage_bonus"
        )
        # Combo counter: multiplicative melee bonus, 1 + 0.5×floor(hits/5)
        combo_mult = 1.0 + 0.5 * math.floor(combo_counter / 5)
        faction_bonus = sum(
            m.faction_bonus for m in mods
            if m.faction_type == enemy.faction
        )

        # Collect elemental mods in slot order
        mod_elements: list[DamageComponent] = []
        for m in mods:
            mod_elements.extend(m.elemental_bonuses)

        # --- Build elemental components ---
        # Scale elemental mod percentages by base_damage
        scaled_mod_elements = [
            DamageComponent(c.type, c.amount * base_damage)
            for c in mod_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        # Mod-sourced secondary elements (Magnetic, Blast, etc.) pass through directly —
        # they cannot combine further, same treatment as innate secondaries.
        mod_secondary = [
            DamageComponent(c.type, quantize(c.amount * base_damage, base_damage))
            for c in mod_elements
            if c.type not in PRIMARY_ELEMENTS
        ]

        # Split innate elements: primaries go into combiner, secondaries pass through
        # Innate element amounts are flat damage values, not percentages of base_damage
        scaled_innate_primary = [
            DamageComponent(c.type, c.amount)
            for c in weapon.innate_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        innate_secondary = [
            DamageComponent(c.type, quantize(c.amount, base_damage))
            for c in weapon.innate_elements
            if c.type not in PRIMARY_ELEMENTS
        ]

        combined_elements = combine_elements(
            scaled_mod_elements,
            scaled_innate_primary,
            base_damage=base_damage,
            is_kuva_tenet=weapon.is_kuva_tenet,
        )

        elemental_components = (
            combined_elements
            + [c for c in innate_secondary if c.amount != 0.0]
            + [c for c in mod_secondary if c.amount != 0.0]
        )

        # --- Build full component list (IPS + elemental) ---
        ips_components = [
            DamageComponent(dt, amt)
            for dt, amt in weapon.base_damage.items()
        ]

        all_components = ips_components + elemental_components

        # --- Step 1: Apply damage mods → modded base, then quantize ---
        modded: list[DamageComponent] = []
        for comp in all_components:
            raw = math.floor(comp.amount * (1.0 + total_damage_bonus + co_total + galv_aptitude_total) * combo_mult)
            q = quantize(float(raw), base_damage)
            if q != 0.0:
                modded.append(DamageComponent(comp.type, q))

        # --- Step 2: Body part multiplier × crit multiplier [warframe_round] ---
        effective_crit = crit_multiplier
        if is_crit_headshot and enemy.body_part_multiplier > 1.0:
            effective_crit = 1.0 + (crit_multiplier - 1.0) * 2.0
        combined_mult = enemy.body_part_multiplier * effective_crit
        from src.quantizer import warframe_round as _wr
        after_bodypart: list[DamageComponent] = [
            DamageComponent(c.type, _wr(c.amount * combined_mult))
            for c in modded
        ]

        # --- Step 3: Damage type effectiveness [math.floor] ---
        after_type: list[DamageComponent] = [
            DamageComponent(
                c.type,
                math.floor(c.amount * self._type_multiplier(c.type, enemy.faction))
            )
            for c in after_bodypart
        ]

        # --- Step 4: Armor mitigation [math.floor] ---
        # Level scaling is applied first, then Corrosive strip.
        # Corrosive stacks reduce enemy armor: stack 1 = 26%, each additional = +6%, cap 80%.
        # Formula: armor × (1 − min(0.80, 0.20 + 0.06 × stacks))
        # Source: wiki.warframe.com/w/Damage/Corrosive_Damage
        scaled = scale_enemy_stats(
            enemy.base_health, enemy.base_shield, enemy.base_armor,
            enemy.base_level, enemy_level, steel_path, eximus,
        )
        armor = scaled["armor"]
        if corrosive_stacks > 0:
            corrosive_reduction = min(0.80, 0.20 + 0.06 * corrosive_stacks)
            armor = armor * (1.0 - corrosive_reduction)

        after_armor: dict[DamageType, float] = {}
        for c in after_type:
            if c.type in (DamageType.TRUE, DamageType.VOID):
                after_armor[c.type] = float(c.amount)
                continue
            mult = calculate_armor_multiplier(armor)
            value = math.floor(c.amount * mult)
            if value > 0:
                after_armor[c.type] = float(value)

        # --- Step 5: Faction mod — applied last [math.floor] ---
        final: dict[DamageType, float] = {}
        for dtype, value in after_armor.items():
            final[dtype] = float(math.floor(value * (1.0 + faction_bonus)))

        # --- Step 6: Viral status proc multiplier [math.floor] ---
        viral_mult = VIRAL_STACK_MULTIPLIERS.get(min(viral_stacks, 10), 1.0)
        if viral_mult != 1.0:
            final = {dtype: float(math.floor(v * viral_mult)) for dtype, v in final.items()}

        # --- Multishot: multiply all damage by projectile count ---
        if multishot != 1.0:
            final = {dtype: v * multishot for dtype, v in final.items()}

        return final

    # ------------------------------------------------------------------
    def calculate_procs(
        self,
        weapon: Weapon,
        mods: list[Mod],
        enemy: Enemy,
        crit_multiplier: float = 1.0,
        is_crit_headshot: bool = False,
        unique_statuses: int = 0,
        galvanized_stacks: int = 0,
    ) -> dict[str, dict]:
        """Compute Slash (Bleed), Heat (Burn), Gas (Cloud), Toxin (Poison), and Electricity (Arc) proc damage per tick and total.

        Proc damage is based on Step-2 values (after body part + crit, before
        type effectiveness and armor).  Faction bonus double-dips: proc_dmg × (1+f)².
        """
        from src.quantizer import warframe_round as _wr

        base_damage = weapon.total_base_damage

        total_damage_bonus = sum(m.damage_bonus for m in mods)
        galv_aptitude_total = sum(
            m.galv_kill_pct * min(galvanized_stacks, m.galv_max_stacks) * unique_statuses
            for m in mods
            if m.galv_kill_stat == "aptitude_damage_bonus"
        )
        total_damage_bonus += galv_aptitude_total
        faction_bonus = sum(
            m.faction_bonus for m in mods
            if m.faction_type == enemy.faction
        )
        total_status_damage_bonus = sum(m.status_damage_bonus for m in mods)

        mod_elements: list[DamageComponent] = []
        for m in mods:
            mod_elements.extend(m.elemental_bonuses)

        scaled_mod_elements = [
            DamageComponent(c.type, c.amount * base_damage)
            for c in mod_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        mod_secondary = [
            DamageComponent(c.type, quantize(c.amount * base_damage, base_damage))
            for c in mod_elements
            if c.type not in PRIMARY_ELEMENTS
        ]
        scaled_innate_primary = [
            DamageComponent(c.type, c.amount)
            for c in weapon.innate_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        innate_secondary = [
            DamageComponent(c.type, quantize(c.amount, base_damage))
            for c in weapon.innate_elements
            if c.type not in PRIMARY_ELEMENTS
        ]
        combined_elements = combine_elements(
            scaled_mod_elements,
            scaled_innate_primary,
            base_damage=base_damage,
            is_kuva_tenet=weapon.is_kuva_tenet,
        )
        elemental_components = (
            combined_elements
            + [c for c in innate_secondary if c.amount != 0.0]
            + [c for c in mod_secondary if c.amount != 0.0]
        )

        ips_components = [
            DamageComponent(dt, amt) for dt, amt in weapon.base_damage.items()
        ]
        all_components = ips_components + elemental_components

        modded: list[DamageComponent] = []
        for comp in all_components:
            raw = math.floor(comp.amount * (1.0 + total_damage_bonus))
            q = quantize(float(raw), base_damage)
            if q != 0.0:
                modded.append(DamageComponent(comp.type, q))

        effective_crit = crit_multiplier
        if is_crit_headshot and enemy.body_part_multiplier > 1.0:
            effective_crit = 1.0 + (crit_multiplier - 1.0) * 2.0
        combined_mult = enemy.body_part_multiplier * effective_crit
        after_step2: list[DamageComponent] = [
            DamageComponent(c.type, _wr(c.amount * combined_mult))
            for c in modded
        ]

        types_present = {c.type for c in after_step2}
        total_step2 = sum(c.amount for c in after_step2)

        def _proc(active: bool, dpt: float, ticks: int) -> dict:
            return {
                "active": active,
                "damage_per_tick": float(math.floor(dpt)) if active else 0.0,
                "ticks": ticks,
                "total_damage": float(math.floor(dpt) * ticks) if active else 0.0,
            }

        def _cc_proc(active: bool, effect: str) -> dict:
            return {
                "active": active,
                "effect": effect,
                "damage_per_tick": 0.0,
                "ticks": 0,
                "total_damage": 0.0,
            }

        slash_active = DamageType.SLASH in types_present
        slash_dpt = total_step2 * 0.35 * (1.0 + faction_bonus) ** 2 * (1.0 + total_status_damage_bonus)

        heat_active = DamageType.HEAT in types_present
        heat_eff = FACTION_EFFECTIVENESS.get((enemy.faction, DamageType.HEAT), 1.0)
        heat_dpt = total_step2 * 0.50 * heat_eff * (1.0 + faction_bonus) ** 2 * (1.0 + total_status_damage_bonus)

        # Gas Cloud: ignores elemental/physical mods; scales with Gas mods, faction (×2),
        # status damage mods, crit, body part. No type effectiveness (wiki formula has none).
        # Source: wiki.warframe.com/w/Damage/Gas_Damage
        gas_active = DamageType.GAS in types_present
        total_gas_bonus = sum(
            c.amount for m in mods
            for c in m.elemental_bonuses
            if c.type == DamageType.GAS
        )
        gas_dpt = (
            weapon.total_base_damage
            * (1.0 + total_damage_bonus)
            * (1.0 + faction_bonus) ** 2
            * 0.5
            * (1.0 + total_gas_bonus)
            * (1.0 + total_status_damage_bonus)
            * combined_mult
        )

        # Toxin (Poison): 50% of total step-2 damage × Toxin effectiveness vs health.
        # Bypasses shields. Faction double-dips.
        # Source: wiki.warframe.com/w/Damage/Toxin_Damage
        toxin_active = DamageType.TOXIN in types_present
        toxin_eff = FACTION_EFFECTIVENESS.get((enemy.faction, DamageType.TOXIN), 1.0)
        toxin_dpt = total_step2 * 0.50 * toxin_eff * (1.0 + faction_bonus) ** 2 * (1.0 + total_status_damage_bonus)

        # Electricity (Tesla Chain): 50% of total step-2 damage × Electricity effectiveness.
        # Stuns target; AoE ticks enemies within 3m — on single target the proc'd enemy
        # is within its own radius, so the DoT still applies. Starts immediately (no 1s delay).
        # Multi-target chaining to other enemies is out of scope for this single-target calc.
        # Source: wiki.warframe.com/w/Damage/Electricity_Damage
        elec_active = DamageType.ELECTRICITY in types_present
        elec_eff = FACTION_EFFECTIVENESS.get((enemy.faction, DamageType.ELECTRICITY), 1.0)
        elec_dpt = total_step2 * 0.50 * elec_eff * (1.0 + faction_bonus) ** 2 * (1.0 + total_status_damage_bonus)

        return {
            "slash":       _proc(slash_active, slash_dpt, 6),
            "heat":        _proc(heat_active, heat_dpt, 6),
            "gas":         _proc(gas_active, gas_dpt, 6),
            "toxin":       _proc(toxin_active, toxin_dpt, 6),
            "electricity": _proc(elec_active, elec_dpt, 6),
            # CC / debuff procs — no damage ticks
            "viral":     _cc_proc(DamageType.VIRAL in types_present,
                                  "Health Vulnr. \u00d71.75\u2013\u00d74.25"),
            "magnetic":  _cc_proc(DamageType.MAGNETIC in types_present,
                                  "+100% shield/OG dmg; forced Elec proc on shield break"),
            "radiation": _cc_proc(DamageType.RADIATION in types_present,
                                  "Confuses enemy to attack allies for 12s"),
            "blast":     _cc_proc(DamageType.BLAST in types_present,
                                  "\u221230% accuracy (up to \u221275%); detonates at 10 stacks"),
            "cold":      _cc_proc(DamageType.COLD in types_present,
                                  "\u221250% speed (up to \u221290%); +0.1 flat crit damage"),
        }

    # ------------------------------------------------------------------
    def _type_multiplier(self, dtype: DamageType, faction: FactionType) -> float:
        return FACTION_EFFECTIVENESS.get((faction, dtype), 1.0)
