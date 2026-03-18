--[[
  extract_data.lua
  ----------------
  Extracts weapon and mod data from the Warframe Wiki Lua modules.

  TWO WAYS TO USE THIS:

  ── Option A: Wiki's Scribunto console (easiest) ─────────────────────────
  Open https://wiki.warframe.com/w/Special:ApiSandbox
  Set action=scribunto-console, then paste into the "question" field:

    Weapons:
      =require('Module:LuaSerializer')._serialize('Weapons/data')

    Mods:
      =require('Module:LuaSerializer')._serialize('Mods/data')

  Copy the JSON output and save as data/weapons_raw.json and data/mods_raw.json.

  ── Option B: Local Lua 5.1+ with downloaded module files ────────────────
  1. Download the raw Lua modules (fetch_wiki_data.py does this automatically):
       curl -A "Mozilla/5.0" "https://wiki.warframe.com/w/Module:Weapons/data?action=raw" > data/weapons_data.lua
       curl -A "Mozilla/5.0" "https://wiki.warframe.com/w/Module:Mods/data?action=raw"    > data/mods_data.lua

  2. Install dkjson:  luarocks install dkjson
  3. Run:  lua scripts/extract_data.lua

  Output: data/weapons_raw.json, data/mods_raw.json
--]]

local json = require('dkjson')  -- luarocks install dkjson

-- Load the raw module files (local execution mode)
local function load_module(path)
    local chunk, err = loadfile(path)
    if not chunk then
        error("Cannot load " .. path .. ": " .. tostring(err))
    end
    return chunk()
end

-- ── Weapons ──────────────────────────────────────────────────────────────
io.write("Loading weapons data... ")
local weapons = load_module("data/weapons_data.lua")
io.write(tostring(type(weapons) == "table" and "OK" or "FAILED") .. "\n")

local f = io.open("data/weapons_raw.json", "w")
f:write(json.encode(weapons, { indent = true }))
f:close()
print("Saved → data/weapons_raw.json")

-- ── Mods ─────────────────────────────────────────────────────────────────
io.write("Loading mods data... ")
local mods_module = load_module("data/mods_data.lua")
-- Module:Mods/data returns { Mods = { ... } }
local mods = mods_module.Mods or mods_module
io.write(tostring(type(mods) == "table" and "OK" or "FAILED") .. "\n")

local g = io.open("data/mods_raw.json", "w")
g:write(json.encode(mods, { indent = true }))
g:close()
print("Saved → data/mods_raw.json")

print("\nNext: python scripts/parse_wiki_data.py")
