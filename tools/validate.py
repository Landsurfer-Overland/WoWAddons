#!/usr/bin/env python3
"""Check addon packaging and isolated core behavior; does not emulate the WoW UI."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from lupa.lua51 import LuaRuntime

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "LegacyAchievementsReforged").resolve()
lua = LuaRuntime(unpack_returned_tuples=True)
compile_lua = lua.eval("function(source, name) local fn, err = loadstring(source, name); return fn ~= nil, err end")
files = sorted(root.rglob("*.lua"))
if not files:
    raise SystemExit(f"No Lua files found in {root}")
for path in files:
    ok, error = compile_lua(path.read_text(), "@" + str(path))
    if not ok:
        raise SystemExit(error)
print(f"Lua 5.1 syntax: {len(files)} files passed")

toc_files = []
for line in (root / "LegacyAchievementsReforged.toc").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        path = root / line.replace("\\", "/")
        if not path.is_file():
            raise SystemExit(f"Missing TOC reference: {line}")
        toc_files.append(path)
xml_files = sorted(root.rglob("*.xml"))
for path in xml_files:
    for element in ET.parse(path).iter():
        if element.tag.rsplit("}", 1)[-1] in ("Script", "Include") and "file" in element.attrib:
            target = path.parent / element.attrib["file"].replace("\\", "/")
            if not target.is_file():
                raise SystemExit(f"Missing XML reference: {target}")
print(f"Packaging: {len(toc_files)} TOC references and {len(xml_files)} XML files passed")

# Explicit mocks support core initialization only. Timers and frame callbacks
# are recorded/deferred, not executed. No renderer or native Legacy API is claimed.
lua.execute('''
frames = {}
function CreateFrame(kind, name, parent)
    local f = { scripts = {}, events = {} }
    function f:SetScript(key, fn) self.scripts[key] = fn end
    function f:RegisterEvent(event) self.events[event] = true end
    function f:RegisterUnitEvent(event) self.events[event] = true end
    function f:Hide() end
    frames[#frames + 1] = f
    return f
end
C_Timer = { After = function() end, NewTicker = function() return {} end }
SlashCmdList = {}
UISpecialFrames = {}
tinsert = table.insert
time = function() return 100 end
GetTime = function() return 0 end
UnitLevel = function() return TEST_LEVEL or 1 end
UnitFactionGroup = function() return "Alliance" end
UnitName = function() return "Fixture", "Character" end
GetRealmName = function() return "Fixture Realm" end
UnitGUID = function() return "Player-FIXTURE" end
ns = {}
''')
for name in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua", "DataExtra.lua", "MoneyTracking.lua", "LegacyAchievementsReforged.lua"):
    chunk = lua.execute("return assert(loadstring(...))", (root / name).read_text(), "@" + name)
    chunk("LegacyAchievementsReforged", lua.globals().ns)
print(f"Core initialized: {len(lua.globals().ns.LAR.ALL)} achievement definitions")

checks = lua.execute('''
local checks = 0
local function check(ok, message)
    assert(ok, message)
    checks = checks + 1
end
local a = ns.LAR.BY_KEY.lvl10
TEST_LEVEL = 9
local cur, need = a.progress()
check(cur == 9 and need == 10, "Level 9 should not meet Level 10")
TEST_LEVEL = 10
cur, need = a.progress()
check(cur == need, "Level 10 should meet Level 10")
local z
for _, candidate in ipairs(ns.EXPLORE) do if candidate.id == 802 then z = candidate; break end end
assert(z and #z.areas > 1, "Westfall's multi-area production definition is required")
local key = z.key or ("explore" .. z.id)
local zone = ns.LAR.BY_KEY[key]
local d = ns.LAR.DB()
d.explored = { [key] = {} }
local complete = zone.progress()
check(complete == nil, "Unavailable map evidence must remain unknown")
C_Map = { GetBestMapForUnit = function(unit) assert(unit == "player"); return z.map end,
GetMapInfo = function(mapID)
    if mapID == z.map then return {mapID = mapID, name = z.zone} end
end }
local currentArea = z.areas[1][1]
GetRealZoneText = function() return z.zone end
GetSubZoneText = function() return currentArea end
local textures = {}
C_MapExplorationInfo = { GetExploredMapTextures = function(mapID)
    assert(mapID == z.map)
    return textures
end }
local function mapUpdated()
    for _, frame in ipairs(frames) do
        if frame.events.MAP_EXPLORATION_UPDATED then
            frame.scripts.OnEvent(frame, "MAP_EXPLORATION_UPDATED")
        end
    end
end
mapUpdated()
complete = zone.progress()
check(complete == nil and zone.has(currentArea) == false,
    "A locally checked unrevealed area is false; unobserved areas remain unknown")
for _, area in ipairs(z.areas) do d.explored[key][area[1]] = true end
complete = zone.progress()
check(complete == nil and zone.has(currentArea) == false,
    "Historical subzone visits must not establish revealed-map completion")
local function texture(area)
    return { offsetX = area[2], offsetY = area[3], textureWidth = 256,
             textureHeight = 256, isShownByMouseOver = false }
end
textures = { texture(z.areas[1]) }
mapUpdated()
complete = zone.progress()
check(complete == nil and zone.has(currentArea) == true,
    "One locally observed overlay proves its area without inventing other discoveries")
for i, area in ipairs(z.areas) do textures[i] = texture(area) end
for _, area in ipairs(z.areas) do
    currentArea = area[1]
    mapUpdated()
    assert(zone.has(currentArea) == true, "Every required area needs positive local proof")
end
complete, need = zone.progress()
check(complete == need, "All character-attributed local discoveries should complete the zone")
d.done.exploreEK = 100
d.done.exploreKal = nil
local world = ns.LAR.BY_KEY.worldexplorer
complete, need = world.progress()
check(complete == 1 and need == 2, "One continent should not complete world exploration")
d.done.exploreKal = 101
d.done.explore855 = 102
complete, need = world.progress()
check(complete == nil and need == 2,
    "Historical Moonglade without character evidence must not validate its continent")
local moon
for _, candidate in ipairs(ns.EXPLORE) do if candidate.id == 855 then moon = candidate; break end end
assert(moon and #moon.areas == 1, "Moonglade's production criterion is required")
GetRealZoneText = function() return moon.zone end
GetSubZoneText = function() return "Nighthaven" end
C_Map.GetBestMapForUnit = function(unit) assert(unit == "player"); return moon.map end
C_Map.GetMapInfo = function(mapID)
    if mapID == moon.map then return {mapID = mapID, name = moon.zone} end
end
C_MapExplorationInfo.GetExploredMapTextures = function(mapID)
    assert(mapID == moon.map)
    return {texture(moon.areas[1])}
end
local moonCurrent, moonNeeded = ns.LAR.BY_KEY.explore855.progress()
check(moonCurrent == moonNeeded and d.done.explore855 == 102,
    "Local Moonglade proof must preserve the original completion timestamp")
complete, need = world.progress()
check(complete == 2 and need == 2, "Both continents should complete world exploration")
local native
for _, candidate in ipairs(ns.LAR.ALL) do
    if candidate.native then native = candidate; break end
end
check(native ~= nil, "Native achievement imports missing")
complete, need = native.progress()
check(complete == 0 and need == 1, "Missing native API must not grant completion")
GetAchievementInfo = function(id) return id, "Native", 0, true end
complete, need = native.progress()
check(complete == 1 and need == 1, "Native completion must come from the client API")
return checks
''')
print(f"Isolated behavior: {checks} assertions passed")
print("In-client UI, event delivery, persistence, and actual Legacy APIs remain untested.")
