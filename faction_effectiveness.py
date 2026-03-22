# Faction damage effectiveness table
# Source: https://wiki.warframe.com/w/Damage/Overview
# Extracted: 2026-03-21
#
# Vulnerable (+) = 1.5   Resistant (−) = 0.5   Neutral = omitted
#
# NOTE: FactionType.ANARCHS does not exist in enums.py yet.
# Add it before using the ANARCHS entries below.

from src.enums import FactionType, DamageType

FACTION_EFFECTIVENESS: dict[tuple[FactionType, DamageType], float] = {

    # ── Impact ──────────────────────────────────────────────────────────────
    (FactionType.GRINEER,        DamageType.IMPACT): 1.5,
    (FactionType.KUVA_GRINEER,   DamageType.IMPACT): 1.5,
    (FactionType.SCALDRA,        DamageType.IMPACT): 1.5,
    # (FactionType.ANARCHS,      DamageType.IMPACT): 1.5,   # add ANARCHS to enum

    # ── Puncture ─────────────────────────────────────────────────────────────
    (FactionType.CORPUS,         DamageType.PUNCTURE): 1.5,
    (FactionType.CORRUPTED,      DamageType.PUNCTURE): 1.5,   # Orokin / Void

    # ── Slash ────────────────────────────────────────────────────────────────
    (FactionType.INFESTED,       DamageType.SLASH): 1.5,
    (FactionType.NARMER,         DamageType.SLASH): 1.5,

    # ── Cold ─────────────────────────────────────────────────────────────────
    (FactionType.SENTIENT,       DamageType.COLD): 1.5,
    (FactionType.TECHROT,        DamageType.COLD): 0.5,

    # ── Electricity ──────────────────────────────────────────────────────────
    (FactionType.CORPUS_AMALGAM, DamageType.ELECTRICITY): 1.5,
    (FactionType.MURMUR,         DamageType.ELECTRICITY): 1.5,
    # (FactionType.ANARCHS,      DamageType.ELECTRICITY): 1.5,

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
    # (FactionType.ANARCHS,      DamageType.RADIATION): 0.5,

    # ── Viral ────────────────────────────────────────────────────────────────
    (FactionType.DEIMOS_INFESTED,DamageType.VIRAL): 0.5,
    (FactionType.CORRUPTED,      DamageType.VIRAL): 1.5,
    (FactionType.MURMUR,         DamageType.VIRAL): 0.5,
}
