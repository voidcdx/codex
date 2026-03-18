#!/usr/bin/env python3
"""
parse_lua.py
------------
Reads data/weapons_data.lua and data/mods_data.lua (downloaded manually from
wiki.warframe.com) and produces data/weapons_raw.json and data/mods_raw.json.

Run:
  python scripts/parse_lua.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Minimal Lua table → Python parser
# Handles the subset used in Warframe wiki data modules:
#   { ["key"] = value, ... }  and  { value, ... }
# Values: strings, numbers, booleans, nil, nested tables.
# ---------------------------------------------------------------------------

class _LuaParser:
    def __init__(self, src: str) -> None:
        self.src = src
        self.pos = 0

    def _skip(self) -> None:
        """Skip whitespace and -- comments."""
        while self.pos < len(self.src):
            if self.src[self.pos] in " \t\r\n":
                self.pos += 1
            elif self.src[self.pos:self.pos+2] == "--":
                # long comment --[[ ... ]]
                if self.src[self.pos+2:self.pos+4] == "[[":
                    self.pos += 4
                    while self.pos < len(self.src):
                        if self.src[self.pos:self.pos+2] == "]]":
                            self.pos += 2
                            break
                        self.pos += 1
                else:
                    while self.pos < len(self.src) and self.src[self.pos] != "\n":
                        self.pos += 1
            else:
                break

    def _peek(self) -> str:
        self._skip()
        return self.src[self.pos] if self.pos < len(self.src) else ""

    def _consume(self, s: str) -> None:
        self._skip()
        if self.src[self.pos:self.pos+len(s)] != s:
            ctx = self.src[max(0, self.pos-20):self.pos+30]
            raise SyntaxError(f"Expected {s!r} near: {ctx!r}")
        self.pos += len(s)

    def parse(self) -> Any:
        """
        Parse a Lua module file. Handles two forms:
          1. Plain table literal:   return { ... }
          2. Statement sequence:    local t = {}
                                    t["k"] = { ... }
                                    return t
        """
        self._skip()
        # Form 1: starts directly with "return { ... }"
        if self.src[self.pos:self.pos+7] == "return ":
            self.pos += 7
            return self._value()

        # Form 2: sequence of statements — execute them into a namespace
        namespace: dict[str, Any] = {}
        return_val: Any = None

        while self.pos < len(self.src):
            self._skip()
            if self.pos >= len(self.src):
                break

            # return <expr>
            if self.src[self.pos:self.pos+7] == "return ":
                self.pos += 7
                self._skip()
                # return a variable name
                m = re.match(r"([A-Za-z_]\w*)", self.src[self.pos:])
                if m:
                    return_val = namespace.get(m.group(1))
                    self.pos += len(m.group(0))
                else:
                    return_val = self._value()
                break

            # local varname = value
            if self.src[self.pos:self.pos+6] == "local ":
                self.pos += 6
                self._skip()
                m = re.match(r"([A-Za-z_]\w*)", self.src[self.pos:])
                if not m:
                    self._skip_statement(); continue
                varname = m.group(1)
                self.pos += len(varname)
                self._skip()
                if self._peek() == "=":
                    self.pos += 1
                    saved = self.pos
                    try:
                        namespace[varname] = self._value()
                    except SyntaxError:
                        # e.g. mw.site.namespaces[828].name — skip
                        self.pos = saved
                        self._skip_statement()
                        namespace[varname] = None
                else:
                    namespace[varname] = None
                self._skip_semi()
                continue

            # varname["key"] = value  OR  varname.key = value
            m = re.match(r"([A-Za-z_]\w*)", self.src[self.pos:])
            if m:
                varname = m.group(1)
                self.pos += len(varname)
                self._skip()

                if self._peek() == "[":
                    # varname[key] = value
                    self.pos += 1
                    try:
                        key = self._value()
                        self._consume("]")
                        self._skip()
                        if self._peek() == "=":
                            self.pos += 1
                            val = self._value()
                            if varname in namespace and isinstance(namespace[varname], dict):
                                namespace[varname][key] = val
                    except SyntaxError:
                        self._skip_statement()
                    self._skip_semi()
                    continue

                if self._peek() == ".":
                    # varname.key = value
                    self.pos += 1
                    km = re.match(r"([A-Za-z_]\w*)", self.src[self.pos:])
                    if km:
                        key = km.group(1)
                        self.pos += len(key)
                        self._skip()
                        if self._peek() == "=":
                            self.pos += 1
                            val = self._value()
                            if varname in namespace and isinstance(namespace[varname], dict):
                                namespace[varname][key] = val
                    self._skip_semi()
                    continue

            # unrecognised statement — skip to next line
            self._skip_statement()

        return return_val

    def _skip_semi(self) -> None:
        self._skip()
        if self._peek() in (",", ";"):
            self.pos += 1

    def _skip_statement(self) -> None:
        """Skip to the next newline (give up on this statement)."""
        while self.pos < len(self.src) and self.src[self.pos] != "\n":
            self.pos += 1

    def _value(self) -> Any:
        self._skip()
        if self.pos >= len(self.src):
            return None
        c = self.src[self.pos]

        if c == "{":
            return self._table()
        if c == '"':
            return self._string('"')
        if c == "'":
            return self._string("'")
        if self.src[self.pos:self.pos+2] == "[[":
            return self._long_string()
        if self.src[self.pos:self.pos+4] == "true":
            self.pos += 4; return True
        if self.src[self.pos:self.pos+5] == "false":
            self.pos += 5; return False
        if self.src[self.pos:self.pos+3] == "nil":
            self.pos += 3; return None

        # number (int or float, optionally negative)
        m = re.match(r"-?(?:0x[\da-fA-F]+|\d+\.?\d*(?:[eE][+-]?\d+)?)",
                     self.src[self.pos:])
        if m:
            s = m.group(0)
            self.pos += len(s)
            try:
                return int(s, 0)
            except ValueError:
                return float(s)

        # Anything else (identifier, function call, concatenation, mw.* API, …)
        # We can't evaluate it locally — consume the expression and return None.
        # An "expression" ends at a structural delimiter: , ; } ) \n
        depth = 0
        while self.pos < len(self.src):
            ch = self.src[self.pos]
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                if depth == 0:
                    break
                depth -= 1
            elif ch in (",", ";", "\n") and depth == 0:
                break
            self.pos += 1
        return None

    def _string(self, q: str) -> str:
        self.pos += 1
        parts: list[str] = []
        while self.pos < len(self.src):
            c = self.src[self.pos]
            if c == "\\":
                self.pos += 1
                esc = self.src[self.pos]
                parts.append({"n":"\n","t":"\t","r":"\r",
                              '"':'"',"'":"'","\\":"\\",
                              "a":"\a","b":"\b","f":"\f","v":"\v"
                              }.get(esc, esc))
                self.pos += 1
            elif c == q:
                self.pos += 1
                break
            else:
                parts.append(c)
                self.pos += 1
        return "".join(parts)

    def _long_string(self) -> str:
        self.pos += 2  # skip [[
        # count optional = signs: [==[...]==]
        eq = 0
        while self.pos < len(self.src) and self.src[self.pos] == "=":
            eq += 1; self.pos += 1
        if self.src[self.pos] != "[":
            raise SyntaxError("Invalid long string")
        self.pos += 1
        close = "]" + "=" * eq + "]"
        parts: list[str] = []
        while self.pos < len(self.src):
            if self.src[self.pos:self.pos+len(close)] == close:
                self.pos += len(close)
                break
            parts.append(self.src[self.pos])
            self.pos += 1
        result = "".join(parts)
        return result.lstrip("\n")

    def _table(self) -> dict | list:
        self._consume("{")
        obj: dict = {}
        arr: list = []
        is_arr = True
        idx = 1

        while True:
            self._skip()
            if self._peek() == "}":
                self._consume("}")
                break

            # ["key"] = value
            if self._peek() == "[" and self.src[self.pos+1:self.pos+2] != "[":
                self.pos += 1
                key = self._value()
                self._consume("]")
                self._consume("=")
                val = self._value()
                obj[key] = val
                is_arr = False

            # ident = value  (bare key)
            elif re.match(r"[A-Za-z_]\w*\s*=(?!=)", self.src[self.pos:]):
                m = re.match(r"([A-Za-z_]\w*)\s*=", self.src[self.pos:])
                key = m.group(1)
                self.pos += m.end()
                val = self._value()
                obj[key] = val
                is_arr = False

            # positional value
            else:
                val = self._value()
                obj[idx] = val
                arr.append(val)
                idx += 1

            self._skip()
            if self._peek() in (",", ";"):
                self.pos += 1

        return arr if (is_arr and arr) else obj


def lua_to_py(src: str) -> Any:
    return _LuaParser(src).parse()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

WEAPON_SLOTS = ["primary", "secondary", "melee", "archwing", "companion", "railjack"]


def main() -> None:
    # ── Weapons (sub-pages) ──────────────────────────────────────────────
    weapon_files = sorted(DATA_DIR.glob("weapons_*.lua"))
    if not weapon_files:
        print("No weapons_*.lua files found in data/. Download these and save them:")
        for slot in ["primary", "secondary", "melee"]:
            print(f"  https://wiki.warframe.com/w/Module:Weapons/data/{slot}?action=raw"
                  f"  →  data/weapons_{slot}.lua")
    else:
        all_weapons: dict = {}
        for lua_path in weapon_files:
            print(f"Parsing {lua_path.name} …", end=" ", flush=True)
            src = lua_path.read_text(encoding="utf-8")
            data = lua_to_py(src)
            if isinstance(data, dict):
                data = {k: v for k, v in data.items() if k is not None}
                all_weapons.update(data)
                print(f"{len(data)} entries")
            else:
                print("skipped (unexpected format)")

        out = DATA_DIR / "weapons_raw.json"
        out.write_text(json.dumps(all_weapons, indent=2, ensure_ascii=False))
        print(f"Total: {len(all_weapons)} weapons → {out.name}\n")

    # ── Mods ─────────────────────────────────────────────────────────────
    mods_path = DATA_DIR / "mods_data.lua"
    if not mods_path.exists():
        print("Missing data/mods_data.lua — download from:")
        print("  https://wiki.warframe.com/w/Module:Mods/data?action=raw")
    else:
        print(f"Parsing {mods_path.name} …", end=" ", flush=True)
        src = mods_path.read_text(encoding="utf-8")
        data = lua_to_py(src)
        if isinstance(data, dict) and "Mods" in data:
            data = data["Mods"]
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if k is not None}
        out = DATA_DIR / "mods_raw.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        n = len(data) if isinstance(data, (dict, list)) else "?"
        print(f"{n} entries → {out.name}")

    print("\nNext: python scripts/parse_wiki_data.py")


if __name__ == "__main__":
    main()
