"""
One-shot patch: add fire_rate_pct to mods in data/mods.json that have a Fire Rate
or Attack Speed value in effect_raw but are missing the field.

Skips conditional / contextual effects (e.g. "Fire Rate for Secondary Weapons",
"Fire Rate while Aiming", "Attack Speed for 10s").
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "mods.json"

# Matches a bare "+/-N% Fire Rate" or "+/-N% Attack Speed" segment.
# The look-ahead (?!\s+\w) rejects qualifiers like "for ...", "while ...", etc.
PATTERN = re.compile(
    r'([+-]?\d+(?:\.\d+)?)%\s+(Fire Rate|Attack Speed)'
    r'(?!\s+(?:for|while|on|per|when|during|after)\b)',
    re.IGNORECASE,
)

# Additional explicit skip substrings (contextual multi-weapon or timed effects)
SKIP_PHRASES = [
    "fire rate for secondary",
    "fire rate for primary",
    "fire rate while",
    "attack speed for",
    "attack speed while",
    "attack speed on",
    "when aiming",
    "while aiming",
]


def is_conditional(effect_raw: str, match_start: int) -> bool:
    """Return True if the matched segment is preceded or followed by a qualifier."""
    # Check for skip phrases anywhere in the raw effect
    lower = effect_raw.lower()
    return any(phrase in lower for phrase in SKIP_PHRASES)


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))

    patched = []
    for name, entry in data.items():
        if "fire_rate_pct" in entry:
            continue  # already set

        effect_raw = entry.get("effect_raw", "")
        if not effect_raw:
            continue

        m = PATTERN.search(effect_raw)
        if not m:
            continue

        if is_conditional(effect_raw, m.start()):
            print(f"  SKIP (conditional): {name!r}  →  {effect_raw!r}")
            continue

        pct = float(m.group(1)) / 100.0
        entry["fire_rate_pct"] = round(pct, 4)
        patched.append((name, pct, effect_raw))

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nPatched {len(patched)} mods:")
    for name, pct, raw in sorted(patched):
        sign = "+" if pct > 0 else ""
        snippet = repr(raw[:60])
        print(f"  {name:<40}  fire_rate_pct = {sign}{pct:.4f}  ({snippet})")


if __name__ == "__main__":
    main()
