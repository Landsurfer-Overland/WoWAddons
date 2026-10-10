-------------------------------------------------------------------------------
--  Forever Achievements
--
--  The WotLK General achievements that the WoW Forever world still allows,
--  tracked per character. State that the game can report (level, riding,
--  mounts, pets, tabard) is read at any time; everything that happens
--  (money looted, critters loved, pests killed, books read, food and drink,
--  falls, loot rolls) counts from the moment the addon is installed.
-------------------------------------------------------------------------------

local ADDON, ns = ...
local TAG = "|cff0cd29fForever Achievements|r"

ForeverAchievementsCharDB = ForeverAchievementsCharDB or {}
local function DB()
    local d = ForeverAchievementsCharDB
    d.done = d.done or {}          -- [key] = time completed
    d.money = d.money or 0         -- copper looted
    d.critters = d.critters or {}  -- [name] = true
    d.pests = d.pests or {}        -- [name] = true
    d.books = d.books or {}        -- [title] = true
    d.drinks = d.drinks or {}      -- [itemID] = name
    d.foods = d.foods or {}        -- [itemID] = name
    d.skills = d.skills or {}      -- [skill] = best rank
    d.fishedIn = d.fishedIn or {}  -- [zone] = true
    d.rareFish = d.rareFish or {}  -- [itemID] = true
    d.bosses = d.bosses or {}      -- [npcID or name] = time killed
    d.reps = d.reps or {}          -- [factionID] = best standing seen
    d.owned = d.owned or {}        -- [itemID] = true once owned
    d.rares = d.rares or {}        -- [name] = time killed
    d.flags = d.flags or {}        -- [key] = true (one-off feats)
    d.tracked = d.tracked or {}    -- [key] = true
    return d
end

local function Count(t)
    local n = 0
    for _ in pairs(t or {}) do n = n + 1 end
    return n
end

local secret = issecretvalue or function() return false end
local function ProgressKnown(cur, need)
    return type(cur) == "number" and type(need) == "number"
        and not secret(cur) and not secret(need)
        and cur == cur and need == need and cur >= 0 and need >= 0
        and cur < math.huge and need < math.huge
end

-------------------------------------------------------------------------------
--  Lists (WotLK criteria; Northrend and Outland-only entries left out)
-------------------------------------------------------------------------------
local CRITTERS = { "Ram", "Squirrel", "Deer", "Crab", "Fawn", "Frog", "Gazelle", "Hare", "Parrot",
    "Rabbit", "Sheep", "Skunk", "Swine", "Toad", "Prairie Dog", "Cat", "Chicken", "Cow" }

-- Pest Control: creature IDs from the achievement's criteria.
local PESTS = {
    [4076] = "Roach", [15476] = "Scorpion", [2914] = "Snake", [3300] = "Adder", [9699] = "Fire Beetle",
    [16068] = "Larva", [16030] = "Maggot", [4953] = "Moccasin", [6271] = "Mouse", [4075] = "Rat",
    [14881] = "Spider", [1412] = "Squirrel",
}
local PEST_ORDER = {}
for _, name in pairs(PESTS) do PEST_ORDER[#PEST_ORDER + 1] = name end
table.sort(PEST_ORDER)

-------------------------------------------------------------------------------
--  Collections the game can report
-------------------------------------------------------------------------------
local GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant

-- Mount and pet items in the bags (Classic keeps them as items).
local function BagItemsOf(classID, subclassID)
    local seen, n = {}, 0
    for bag = 0, 4 do
        for slot = 1, C_Container.GetContainerNumSlots(bag) do
            local id = C_Container.GetContainerItemID(bag, slot)
            if id and not seen[id] then
                local _, _, _, _, _, c, s = GetItemInfoInstant(id)
                if c == classID and s == subclassID then
                    seen[id] = true
                    n = n + 1
                end
            end
        end
    end
    return n
end

local function MountCount()
    local best = 0
    if C_MountJournal and C_MountJournal.GetMountIDs and C_MountJournal.GetMountInfoByID then
        local n = 0
        for _, id in ipairs(C_MountJournal.GetMountIDs() or {}) do
            local _, _, _, _, _, _, _, _, _, _, collected = C_MountJournal.GetMountInfoByID(id)
            if collected then n = n + 1 end
        end
        best = math.max(best, n)
    end
    if GetNumCompanions then best = math.max(best, GetNumCompanions("MOUNT") or 0) end
    best = math.max(best, BagItemsOf(15, 5)) -- Miscellaneous > Mount
    local d = DB()
    d.mountsBest = math.max(d.mountsBest or 0, best) -- bank or sold mounts still counted once seen
    return d.mountsBest
end

local function PetCount()
    local best = 0
    if C_PetJournal and C_PetJournal.GetNumPets then
        local _, owned = C_PetJournal.GetNumPets()
        best = math.max(best, owned or 0)
    end
    if GetNumCompanions then best = math.max(best, GetNumCompanions("CRITTER") or 0) end
    best = math.max(best, BagItemsOf(15, 2)) -- Miscellaneous > Companion Pets
    local d = DB()
    d.petsBest = math.max(d.petsBest or 0, best)
    return d.petsBest
end

-- Classic riding: the Riding skill (75 apprentice, 150 journeyman), or the
-- riding spells on clients that have them.
local function RidingRank()
    if IsPlayerSpell then
        if IsPlayerSpell(33391) then return 150 end
        if IsPlayerSpell(33388) then return 75 end
    end
    if GetNumSkillLines and GetSkillLineInfo then
        for i = 1, GetNumSkillLines() do
            local name, isHeader, _, rank = GetSkillLineInfo(i)
            if not isHeader and name == "Riding" then return rank or 0 end
        end
    end
    return 0
end

-------------------------------------------------------------------------------
--  Achievements: progress() returns current, needed (and optional text)
-------------------------------------------------------------------------------
local function LevelAch(key, id, lvl)
    return { key = key, id = id, series = "level", name = "Level " .. lvl, desc = "Reach level " .. lvl .. ".", pts = 10,
             progress = function() return math.min(UnitLevel("player"), lvl), lvl end }
end

local SECTIONS = {
    { title = "LEVELS", list = {
        LevelAch("lvl10", 6, 10), LevelAch("lvl20", 7, 20), LevelAch("lvl30", 8, 30),
        LevelAch("lvl40", 9, 40), LevelAch("lvl50", 10, 50), LevelAch("lvl60", 11, 60),
    } },
    { title = "RIDING", list = {
        { key = "riding75", id = 891, series = "riding", name = "Giddy Up!", desc = "Learn the apprentice riding skill.", pts = 10,
          progress = function() return math.min(RidingRank(), 75), 75 end },
        { key = "riding150", id = 889, series = "riding", name = "Fast and Furious", desc = "Learn the journeyman riding skill (epic mounts).", pts = 10,
          progress = function() return math.min(RidingRank(), 150), 150 end },
    } },
    { title = "MONEY", list = {
        { key = "gold100", series = "gold", id = 1176, name = "Got My Mind On My Money", desc = "Loot 100 gold.", pts = 10, money = true,
          progress = function() return math.min(DB().money, 1000000), 1000000 end },
        { key = "gold1000", series = "gold", id = 1177, name = "Got My Mind On My Money", desc = "Loot 1,000 gold.", pts = 10, money = true,
          progress = function() return math.min(DB().money, 10000000), 10000000 end },
        { key = "gold5000", series = "gold", id = 1178, name = "Got My Mind On My Money", desc = "Loot 5,000 gold.", pts = 10, money = true,
          progress = function() return math.min(DB().money, 50000000), 50000000 end },
    } },
    { title = "COLLECTIONS", list = {
        { key = "pet1", id = 1017, series = "pets", name = "Can I Keep Him?", desc = "Obtain a companion pet.", pts = 10,
          progress = function() return math.min(PetCount(), 1), 1 end },
        { key = "pet15", id = 15, series = "pets", name = "Plenty of Pets", desc = "Collect 15 unique companion pets.", pts = 10,
          progress = function() return math.min(PetCount(), 15), 15 end },
        { key = "mount10", id = 2141, name = "Stable Keeper", desc = "Obtain 10 mounts.", pts = 10,
          progress = function() return math.min(MountCount(), 10), 10 end },
        { key = "tabard", id = 621, name = "Represent", desc = "Equip a tabard.", pts = 10,
          progress = function() return GetInventoryItemID("player", 19) and 1 or 0, 1 end },
    } },
    { title = "AROUND AZEROTH", list = {
        { key = "fall", id = 964, name = "Going Down?", desc = "Fall 65 yards without dying.", pts = 10,
          progress = function() return DB().fall and 1 or 0, 1 end },
        { key = "critters", id = 1206, name = "To All The Squirrels I've Loved Before",
          desc = "Show the critters of Azeroth how much you /love them.", pts = 10, list = CRITTERS,
          has = function(n) return DB().critters[n] end,
          progress = function() return Count(DB().critters), #CRITTERS end },
        { key = "pests", id = 2556, name = "Pest Control", desc = "Slay the following pests.", pts = 10,
          list = PEST_ORDER, has = function(n) return DB().pests[n] end,
          progress = function() return Count(DB().pests), #PEST_ORDER end },
        { key = "books", id = 1244, name = "Well Read", desc = "Read the books listed below.", pts = 10,
          list = ns.BOOKS, has = function(n) return DB().books[n] end,
          progress = function() return Count(DB().books), #ns.BOOKS end },
    } },
    { title = "FOOD & DRINK", list = {
        { key = "drinks", id = 1833, name = "It's Happy Hour Somewhere", desc = "Drink 25 different types of beverages.", pts = 10,
          seen = function() return DB().drinks end,
          progress = function() return math.min(Count(DB().drinks), 25), 25 end },
        { key = "foods", id = 1832, name = "Tastes Like Chicken", desc = "Sample 50 different kinds of Azeroth's delectable dishes.", pts = 10,
          seen = function() return DB().foods end,
          progress = function() return math.min(Count(DB().foods), 50), 50 end },
    } },
    { title = "LOOT ROLLS", list = {
        { key = "greedy", id = 558, name = "Greedy", desc = "Win a greed roll on a superior or better item by rolling 100.", pts = 10,
          progress = function() return DB().greedy and 1 or 0, 1 end },
        { key = "needy", id = 559, name = "Needy", desc = "Win a need roll on a superior or better item by rolling 100.", pts = 10,
          progress = function() return DB().needy and 1 or 0, 1 end },
    } },
}

-------------------------------------------------------------------------------
--  Quests and Exploration (WotLK categories, the parts the Forever world has)
-------------------------------------------------------------------------------

-- Character statistics the client keeps (the WotLK Statistics page): a
-- number, or a money string with coin icons.
local function StatText(id)
    if type(GetStatistic) ~= "function" then return nil end
    local ok, text = pcall(GetStatistic, id)
    if not ok or type(text) ~= "string" or secret(text) then return nil end
    return text
end

local function StatNumber(id)
    local text = StatText(id)
    if not text then return nil end
    return tonumber((text:gsub("%D", "")))
end

local function StatCopper(id)
    local text = StatText(id)
    if not text then return nil end
    local total, found = 0, false
    for n, coin in text:gmatch("(%d+)%s*|T[^|]-UI%-(%a+)Icon") do
        local v = tonumber(n) or 0
        coin = coin:lower()
        if coin == "gold" then total = total + v * 10000
        elseif coin == "silver" then total = total + v * 100
        else total = total + v end
        found = true
    end
    if found then return total end
    return tonumber((text:gsub("%D", "")))
end

local STAT_QUESTS, STAT_DAILIES, STAT_QUEST_GOLD = 98, 97, 326

local function CompletedIDs()
    if C_QuestLog and type(C_QuestLog.GetAllCompletedQuestIDs) == "function" then
        local ok, ids = pcall(C_QuestLog.GetAllCompletedQuestIDs)
        if ok and not secret(ids) and type(ids) == "table" then return ids end
    end
    if type(GetQuestsCompleted) ~= "function" then return nil end
    local t, out = {}, {}
    if not pcall(GetQuestsCompleted, t) then return nil end
    for id in pairs(t) do out[#out + 1] = id end
    return out
end

local function QuestCount()
    local n = StatNumber(STAT_QUESTS)
    if n and n > 0 then return n end
    local ids = CompletedIDs()
    if ids then return #ids end
    return n -- a confirmed native zero remains distinct from unavailable
end

local function IsQuestDone(id)
    if C_QuestLog and C_QuestLog.IsQuestFlaggedCompleted then return C_QuestLog.IsQuestFlaggedCompleted(id) end
    return IsQuestFlaggedCompleted and IsQuestFlaggedCompleted(id) or false
end

-- A Simple Re-Quest: days on which the daily counter went up.
local function TrackDailies()
    local n = StatNumber(STAT_DAILIES)
    if not n then return end
    local d = DB()
    d.dailyDays = d.dailyDays or {}
    if d.dailyLast and n > d.dailyLast then d.dailyDays[date("%Y-%m-%d")] = true end
    d.dailyLast = n
end

local function DailyStreak()
    local days = DB().dailyDays or {}
    local best, run = 0, 0
    for i = 0, 60 do
        if days[date("%Y-%m-%d", time() - i * 86400)] then
            run = run + 1
            if run > best then best = run end
        else
            run = 0
        end
    end
    return best
end

-- Loremaster: completed quests whose QuestieDB zone is in the continent's
-- area list. Needs QuestieDB; counted again when quests are turned in.
local loreCount = {}
local function CountLore()
    wipe(loreCount)
    local Q = _G.QuestDB
    if type(Q) ~= "table" or type(Q.Exists) ~= "function" or type(Q.Get) ~= "function" then return end
    local ids = CompletedIDs()
    if not ids then return end
    local ek, kal = {}, {}
    for _, a in ipairs(ns.LORE_EK_A.areas) do ek[a] = true end
    for _, a in ipairs(ns.LORE_KAL_A.areas) do kal[a] = true end
    local nEK, nKal = 0, 0
    for _, id in ipairs(ids) do
        local ok, z = pcall(function() return Q.Exists(id) and Q.Get(id, "zoneOrSort") end)
        if not ok then return end -- partial data cannot prove a complete count
        if z then
            if ek[z] then nEK = nEK + 1 elseif kal[z] then nKal = nKal + 1 end
        end
    end
    loreCount.ek, loreCount.kal = nEK, nKal
end

local function Faction() return UnitFactionGroup("player") == "Horde" and "H" or "A" end

local function LoreNeed(key)
    local t = ns["LORE_" .. key .. "_" .. Faction()]
    return t and t.need or 700
end

-- Exploration: a zone's subzones count when the world map shows them
-- uncovered (matched by the map overlay's position) or when you have
-- stood in them since installing.
local zoneMaps -- [zone name] = uiMapID, built on first use
local function NormZone(s)
    return (s or ""):lower():gsub("^the ", ""):gsub(" desert$", "")
end

local function ZoneMaps()
    if zoneMaps then return zoneMaps end
    zoneMaps = {}
    if not (C_Map and C_Map.GetBestMapForUnit and C_Map.GetMapChildrenInfo) then return zoneMaps end
    local m = C_Map.GetBestMapForUnit("player")
    local top = m
    while m do
        local info = C_Map.GetMapInfo(m)
        if not info then break end
        top = m
        if not info.parentMapID or info.parentMapID == 0 then break end
        m = info.parentMapID
    end
    if not top then zoneMaps = nil return {} end
    for _, child in ipairs(C_Map.GetMapChildrenInfo(top, Enum.UIMapType.Zone, true) or {}) do
        zoneMaps[NormZone(child.name)] = zoneMaps[NormZone(child.name)] or child.mapID
    end
    return zoneMaps
end

local exploredCache, exploredAt = {}, 0
local function ExploredOffsets(mapID)
    if GetTime() - exploredAt > 5 then
        wipe(exploredCache)
        exploredAt = GetTime()
    end
    local c = exploredCache[mapID]
    if c then return c end
    c = {}
    if C_MapExplorationInfo and C_MapExplorationInfo.GetExploredMapTextures then
        for _, tex in ipairs(C_MapExplorationInfo.GetExploredMapTextures(mapID) or {}) do
            c[#c + 1] = { tex.offsetX or 0, tex.offsetY or 0 }
        end
    end
    exploredCache[mapID] = c
    return c
end

local function ZoneKey(z) return z.key or ("explore" .. z.id) end

local function AreaExplored(zone, area)
    local ex = DB().explored
    local seen = ex and (ex[ZoneKey(zone)] or (zone.id and ex[zone.id])) -- older saves used the ID
    if seen and seen[area[1]] then return true end
    local mapID = zone.map or ZoneMaps()[NormZone(zone.zone)]
    if not mapID or not area[2] then return false end
    for _, o in ipairs(ExploredOffsets(mapID)) do
        if math.abs(o[1] - area[2]) <= 2 and math.abs(o[2] - area[3]) <= 2 then return true end
    end
    return false
end

local function NoteSubzone()
    local zoneText = NormZone(GetRealZoneText() or GetZoneText())
    local sub = GetSubZoneText()
    if not sub or sub == "" or secret(sub) then return end
    for _, z in ipairs(ns.EXPLORE) do
        if NormZone(z.zone) == zoneText then
            for _, area in ipairs(z.areas) do
                if area[1] == sub then
                    local d = DB()
                    local zk = ZoneKey(z)
                    d.explored = d.explored or {}
                    d.explored[zk] = d.explored[zk] or {}
                    if not d.explored[zk][sub] then
                        d.explored[zk][sub] = true
                        return true
                    end
                end
            end
        end
    end
end

local function QuestAch(key, id, n, pts)
    return { key = key, id = id, series = "quests", name = n .. " Quests Completed",
             desc = "Complete " .. n .. " quests.", pts = pts or 10,
             progress = function() local count = QuestCount(); return count and math.min(count, n), n end }
end

local function DailyAch(key, id, n)
    return { key = key, id = id, series = "dailies", name = n .. " Daily Quests Complete",
             unsupported = true, unsupportedReason = "Daily quests are unavailable in this Forever project.",
             desc = "Complete " .. n .. " daily quests.", pts = 10,
             progress = function() return math.min(StatNumber(STAT_DAILIES) or 0, n), n end }
end

local GREEN_HILLS_NAMES = { [338] = "The Green Hills of Stranglethorn", [208] = "Big Game Hunter" }
local greenHillsList = {}
for _, q in ipairs(ns.GREEN_HILLS) do greenHillsList[#greenHillsList + 1] = GREEN_HILLS_NAMES[q] or ("Quest " .. q) end

local loreEK = { key = "loreEK", id = 1676, name = "Loremaster of Eastern Kingdoms", pts = 10,
    progress = function() local n = LoreNeed("EK"); return loreCount.ek and math.min(loreCount.ek, n), n end }
local loreKal = { key = "loreKal", id = 1678, name = "Loremaster of Kalimdor", pts = 10,
    progress = function() local n = LoreNeed("KAL"); return loreCount.kal and math.min(loreCount.kal, n), n end }
loreEK.desc = "Complete quests in Eastern Kingdoms (counted with QuestieDB)."
loreKal.desc = "Complete quests in Kalimdor (counted with QuestieDB)."

-- The Bread Winner is quest gold, not a quest line: it joins General > Money.
for _, sec in ipairs(SECTIONS) do
    if sec.title == "MONEY" then
        table.insert(sec.list, {
            key = "breadwinner", id = 1182, name = "The Bread Winner", pts = 10, money = true,
            desc = "Make 10,000 gold from quest rewards.",
            progress = function() return math.min(StatCopper(STAT_QUEST_GOLD) or 0, 100000000), 100000000 end,
        })
    end
end

local QUEST_SECTIONS = {
    { title = "QUESTS COMPLETED", list = {
        QuestAch("q50", 503, 50), QuestAch("q100", 504, 100), QuestAch("q250", 505, 250),
        QuestAch("q500", 506, 500), QuestAch("q1000", 507, 1000), QuestAch("q1500", 508, 1500),
        QuestAch("q2000", 32, 2000), QuestAch("q3000", 978, 3000, 50),
    } },
    { title = "DAILY QUESTS", list = {
        DailyAch("d5", 973, 5), DailyAch("d50", 974, 50), DailyAch("d200", 975, 200),
        DailyAch("d500", 976, 500), DailyAch("d1000", 977, 1000),
        { key = "request", id = 31, name = "A Simple Re-Quest", pts = 10,
          unsupported = true, unsupportedReason = "Daily quests are unavailable in this Forever project.",
          desc = "Complete a daily quest every day for five consecutive days.",
          progress = function() return math.min(DailyStreak(), 5), 5 end },
    } },
    { title = "QUEST LINES", list = {
        { key = "greenhills", id = 940, name = "The Green Hills of Stranglethorn", pts = 10,
          desc = "Complete all of Hemet Nesingwary quests in Stranglethorn Vale.",
          list = greenHillsList,
          has = function(n)
              for q, name in pairs(GREEN_HILLS_NAMES) do if name == n then return IsQuestDone(q) end end
          end,
          progress = function()
              local n = 0
              for _, q in ipairs(ns.GREEN_HILLS) do if IsQuestDone(q) then n = n + 1 end end
              return n, #ns.GREEN_HILLS
          end },
    } },
    { title = "LOREMASTER", list = {
        loreEK, loreKal,
        { key = "loremaster", id = 1681, name = "The Loremaster", pts = 10,
          desc = "Complete Loremaster of Eastern Kingdoms and Loremaster of Kalimdor.",
          list = { "Loremaster of Eastern Kingdoms", "Loremaster of Kalimdor" },
          has = function(n)
              if n:find("Eastern", 1, true) then return DB().done.loreEK end
              return DB().done.loreKal
          end,
          progress = function()
              return (DB().done.loreEK and 1 or 0) + (DB().done.loreKal and 1 or 0), 2
          end },
    } },
}

-- Exploration: one achievement per zone, then the continents and the world.
local function ZoneAch(z)
    local names = {}
    for _, area in ipairs(z.areas) do names[#names + 1] = area[1] end
    return { key = ZoneKey(z), id = z.id, icon = z.icon, name = "Explore " .. z.zone, pts = 10,
             desc = "Explore " .. z.zone .. ", revealing the covered areas of the world map.",
             list = names,
             has = function(n)
                 for _, area in ipairs(z.areas) do if area[1] == n then return AreaExplored(z, area) end end
             end,
             progress = function()
                 local n = 0
                 for _, area in ipairs(z.areas) do if AreaExplored(z, area) then n = n + 1 end end
                 return n, #z.areas
             end }
end

local ekZones, kalZones, otherZones = {}, {}, {}
for _, z in ipairs(ns.EXPLORE) do
    local a = ZoneAch(z)
    if z.cont == "ek" then ekZones[#ekZones + 1] = a
    elseif z.cont == "kal" then kalZones[#kalZones + 1] = a
    else otherZones[#otherZones + 1] = a end
end

local function ContinentAch(key, id, name, zones)
    local names = {}
    for _, a in ipairs(zones) do names[#names + 1] = (a.name:gsub("^Explore ", "")) end
    return { key = key, id = id, name = name, pts = 25,
             desc = "Explore the regions of " .. name:gsub("^Explore ", "") .. ".",
             list = names,
             has = function(n)
                 for _, a in ipairs(zones) do if a.name == "Explore " .. n then return DB().done[a.key] end end
             end,
             progress = function()
                 local n = 0
                 for _, a in ipairs(zones) do if DB().done[a.key] then n = n + 1 end end
                 return n, #zones
             end }
end

local exploreEK = ContinentAch("exploreEK", 42, "Explore Eastern Kingdoms", ekZones)
local exploreKal = ContinentAch("exploreKal", 43, "Explore Kalimdor", kalZones)

local EXPLORE_SECTIONS = {
    { title = "AZEROTH", list = {
        exploreEK, exploreKal,
        { key = "worldexplorer", id = 46, name = "World Explorer", pts = 50,
          desc = "Explore Eastern Kingdoms and Kalimdor.",
          list = { "Eastern Kingdoms", "Kalimdor" },
          has = function(n) return n == "Kalimdor" and DB().done.exploreKal or DB().done.exploreEK end,
          progress = function()
              return (DB().done.exploreEK and 1 or 0) + (DB().done.exploreKal and 1 or 0), 2
          end },
    } },
    { title = "EASTERN KINGDOMS", list = ekZones },
    { title = "KALIMDOR", list = kalZones },
    { title = "ZEPHRAS ISLE", list = otherZones },
}

-------------------------------------------------------------------------------
--  Professions (classic cap 300: Journeyman, Expert and Artisan ranks)
-------------------------------------------------------------------------------
local PRIMARY = { Alchemy = true, Blacksmithing = true, Enchanting = true, Engineering = true, Herbalism = true,
    Leatherworking = true, Mining = true, Skinning = true, Tailoring = true, Jewelcrafting = true, Inscription = true }
local SECONDARY = { "Cooking", "Fishing", "First Aid" }
local SKILL_LINES = { [171] = "Alchemy", [164] = "Blacksmithing", [333] = "Enchanting", [202] = "Engineering",
    [182] = "Herbalism", [165] = "Leatherworking", [186] = "Mining", [393] = "Skinning", [197] = "Tailoring",
    [755] = "Jewelcrafting", [773] = "Inscription", [185] = "Cooking", [356] = "Fishing", [129] = "First Aid" }

-- Best rank ever reached per skill, so dropping a profession keeps the record.
local function Skills()
    local best = DB().skills
    if GetNumSkillLines and GetSkillLineInfo then
        for i = 1, GetNumSkillLines() do
            local name, isHeader, _, rank = GetSkillLineInfo(i)
            if name and not isHeader and rank and not secret(rank) then
                best[name] = math.max(best[name] or 0, rank)
            end
        end
    end
    -- The Forever client has no skill line list: professions come from the
    -- profession slots, named by skill line so the names match any locale.
    if GetProfessions and GetProfessionInfo then
        local slots = { GetProfessions() }
        for i = 1, 6 do
            local index = slots[i]
            if index then
                local name, _, rank, _, _, _, line = GetProfessionInfo(index)
                name = SKILL_LINES[line] or name
                if name and rank and not secret(rank) then
                    best[name] = math.max(best[name] or 0, rank)
                end
            end
        end
    end
    return best
end

local function BestPrimary()
    local top = 0
    for name, rank in pairs(Skills()) do if PRIMARY[name] then top = math.max(top, rank) end end
    return top
end

local function PrimariesAt(n)
    local c = 0
    for name, rank in pairs(Skills()) do if PRIMARY[name] and rank >= n then c = c + 1 end end
    return c
end

local function SkillRank(name) return Skills()[name] or 0 end

local function RankAch(key, id, series, name, desc, skill, n, icon)
    return { key = key, id = id, icon = icon, series = series, skill = skill, name = name, desc = desc, pts = 10,
             progress = function()
                 local r = skill and SkillRank(skill) or BestPrimary()
                 return math.min(r, n), n
             end }
end

local STAT_FISHED, STAT_FISH, STAT_RECIPES = 1456, 1518, 1745
-- The client's catch statistic can lag far behind (it lost catches during the
-- beta), so the skill sets a floor: every point above 1 took at least one catch.
local function FishedCount()
    local floor = math.max(0, SkillRank("Fishing") - 1)
    return math.max(StatNumber(STAT_FISHED) or 0, StatNumber(STAT_FISH) or 0, DB().fished or 0, floor)
end

local function FishAch(key, id, n)
    return { key = key, id = id, series = "fished", name = n .. " Fish", desc = "Fish up " .. n .. " items.", pts = 10,
             progress = function() return math.min(FishedCount(), n), n end }
end

local function RecipeAch(key, id, name, n)
    return { key = key, id = id, series = "recipes", name = name, desc = "Learn " .. n .. " cooking recipes.", pts = 10,
             progress = function() return math.min(StatNumber(STAT_RECIPES) or 0, n), n end }
end

local DIPLOMAT = { "Orgrimmar", "Stormwind City" }
local RARE_NAMES = {}
for _, f in ipairs(ns.RARE_FISH) do RARE_NAMES[#RARE_NAMES + 1] = f[1] end

local function HasRareFish(name)
    for _, f in ipairs(ns.RARE_FISH) do
        if f[1] == name then
            local count = (C_Item and C_Item.GetItemCount) or GetItemCount
            return DB().rareFish[f[2]] or (count and (count(f[2], true) or 0) > 0)
        end
    end
end

-- Quick Fish (optional): its account-wide catch log, QuickFishDB. These
-- achievements show only while Quick Fish is loaded. The totals are summed
-- at most once a second and never in combat (the last numbers stand).
local QF = { stats = { catches = 0, zones = 0, kinds = 0, rares = 0 }, at = -10 }

function QF.DB()
    local db = rawget(_G, "QuickFishDB")
    if type(db) == "table" and type(db.log) == "table" then return db end
end

function QF.Loaded()
    local loaded = (C_AddOns and C_AddOns.IsAddOnLoaded) or IsAddOnLoaded
    if loaded then
        local ok, yes = pcall(loaded, "QuickFish")
        if ok and yes then return true end
    end
    return QF.DB() ~= nil
end

function QF.Stats()
    local now = GetTime()
    if now - QF.at < 1 then return QF.stats end
    local fighting = InCombatLockdown and InCombatLockdown()
    if secret(fighting) or fighting then return QF.stats end
    QF.at = now
    local s = { catches = 0, zones = 0, kinds = 0, rares = 0 }
    local db = QF.DB()
    if db then
        local seen = {}
        for _, z in pairs(db.log) do
            if type(z) == "table" then
                local n = tonumber(z.total) or 0
                s.catches = s.catches + n
                if n > 0 then s.zones = s.zones + 1 end
                if type(z.items) == "table" then
                    for id in pairs(z.items) do
                        if not seen[id] then seen[id] = true; s.kinds = s.kinds + 1 end
                    end
                end
            end
        end
        if type(db.rares) == "table" then s.rares = #db.rares end
    end
    QF.stats = s
    return s
end

function QF.Ach(key, series, stat, name, desc, n, icon)
    return { key = key, series = series, icon = icon, name = name, desc = desc, pts = 10, requires = QF.Loaded,
             progress = function() return math.min(QF.Stats()[stat], n), n end }
end

local PROF_SECTIONS = {
    { title = "PROFESSIONS", list = {
        RankAch("prof75", nil, "prof", "Professional Apprentice", "Reach 75 in a profession.", nil, 75, 134327),
        RankAch("prof150", 116, "prof", "Professional Journeyman", "Reach 150 in a profession.", nil, 150),
        RankAch("prof225", 731, "prof", "Professional Expert", "Reach 225 in a profession.", nil, 225),
        RankAch("prof300", 732, "prof", "Professional Artisan", "Reach 300 in a profession.", nil, 300),
        { key = "dayandnight", id = 735, name = "Working Day and Night", pts = 10,
          desc = "Become an Artisan (300) in two professions.",
          progress = function() return math.min(PrimariesAt(300), 2), 2 end },
        { key = "paythebills", id = 730, name = "Skills to Pay the Bills", pts = 10,
          desc = "Become an Artisan (300) in fishing, first aid and cooking.",
          list = SECONDARY, has = function(n) return SkillRank(n) >= 300 end,
          progress = function()
              local c = 0
              for _, s in ipairs(SECONDARY) do if SkillRank(s) >= 300 then c = c + 1 end end
              return c, #SECONDARY
          end },
    } },
    { title = "COOKING", list = {
        RankAch("cook75", nil, "cook", "Apprentice Cook", "Become an Apprentice Cook.", "Cooking", 75, 133971),
        RankAch("cook150", 121, "cook", "Journeyman Cook", "Become a Journeyman Cook.", "Cooking", 150),
        RankAch("cook225", 122, "cook", "Expert Cook", "Become an Expert Cook.", "Cooking", 225),
        RankAch("cook300", 123, "cook", "Artisan Cook", "Become an Artisan Cook.", "Cooking", 300),
        RecipeAch("recipes25", 1795, "Lunch Lady", 25),
        RecipeAch("recipes50", 1796, "Short Order Cook", 50),
        RecipeAch("recipes75", 1797, "Chef de Partie", 75),
    } },
    { title = "FISHING", list = {
        RankAch("fish75", nil, "fishing", "Apprentice Fisherman", "Become an Apprentice Fisherman.", "Fishing", 75, 136245),
        RankAch("fish150", 126, "fishing", "Journeyman Fisherman", "Become a Journeyman Fisherman.", "Fishing", 150),
        RankAch("fish225", 127, "fishing", "Expert Fisherman", "Become an Expert Fisherman.", "Fishing", 225),
        RankAch("fish300", 128, "fishing", "Artisan Fisherman", "Become an Artisan Fisherman.", "Fishing", 300),
        FishAch("fished25", 1556, 25), FishAch("fished50", 1557, 50), FishAch("fished100", 1558, 100),
        FishAch("fished250", 1559, 250), FishAch("fished500", 1560, 500), FishAch("fished1000", 1561, 1000),
        { key = "oldgnome", id = 153, name = "The Old Gnome and the Sea", desc = "Successfully fish from a school.", pts = 10,
          progress = function() return DB().school and 1 or 0, 1 end },
        { key = "diplomat", id = 150, name = "The Fishing Diplomat", desc = "Fish something up in Orgrimmar and Stormwind.", pts = 10,
          list = DIPLOMAT, has = function(n) return DB().fishedIn[n] end,
          progress = function()
              local c = 0
              for _, z in ipairs(DIPLOMAT) do if DB().fishedIn[z] then c = c + 1 end end
              return c, #DIPLOMAT
          end },
        { key = "masterangler", id = 306, name = "Master Angler of Azeroth", desc = "Win the Booty Bay fishing contest.", pts = 20,
          progress = function() return IsQuestDone(8193) and 1 or 0, 1 end },
        { key = "rarefish", id = 878, name = "One That Didn't Get Away", desc = "Catch one of the rare fish in the list below.", pts = 10,
          list = RARE_NAMES, has = HasRareFish,
          progress = function()
              for _, n in ipairs(RARE_NAMES) do if HasRareFish(n) then return 1, 1 end end
              return 0, 1
          end },
    } },
    { title = "QUICK FISH", list = {
        -- No catch-count series here: the Fishing section's "X Fish" already
        -- counts every catch (game statistic), Quick Fish's log only since install.
        QF.Ach("qfzones5", "qfzones", "zones", "Wandering Angler", "Fish something up in 5 zones (Quick Fish catch log).", 5, 237381),
        QF.Ach("qfzones10", "qfzones", "zones", "Travelling Angler", "Fish something up in 10 zones (Quick Fish catch log).", 10, 237381),
        QF.Ach("qfzones20", "qfzones", "zones", "Angler of Azeroth", "Fish something up in 20 zones (Quick Fish catch log).", 20, 237381),
        QF.Ach("qfrares1", "qfrares", "rares", "Lucky Strike", "Fish up an uncommon or better item (Quick Fish rare finds).", 1, 133921),
        QF.Ach("qfrares10", "qfrares", "rares", "Treasure Angler", "Fish up 10 uncommon or better items (Quick Fish rare finds).", 10, 133921),
        QF.Ach("qfkinds15", "qfkinds", "kinds", "Mixed Bag", "Fish up 15 different items (Quick Fish catch log).", 15, 133892),
        QF.Ach("qfkinds30", "qfkinds", "kinds", "Fish of Every Kind", "Fish up 30 different items (Quick Fish catch log).", 30, 133892),
    } },
    { title = "FIRST AID", list = {
        RankAch("aid75", nil, "firstaid", "Apprentice in First Aid", "Become an Apprentice in first aid.", "First Aid", 75, 135966),
        RankAch("aid150", 131, "firstaid", "Journeyman in First Aid", "Become a Journeyman in first aid.", "First Aid", 150),
        RankAch("aid225", 132, "firstaid", "Expert in First Aid", "Become an Expert in first aid.", "First Aid", 225),
        RankAch("aid300", 133, "firstaid", "Artisan in First Aid", "Become an Artisan in first aid.", "First Aid", 300),
    } },
}

-------------------------------------------------------------------------------
--  Dungeons & Raids (classic instances; a kill counts once per character)
-------------------------------------------------------------------------------
local BOSS_IDS, BOSS_BY_NAME = {}, {}

local function BossKilled(boss) return DB().bosses[boss[2]] or DB().bosses[boss[1]] end

local BOSS_ACH = {} -- [boss name] = achievement name, for the tooltips

local function DungeonAch(d)
    -- Bosses without a known creature ID are tracked by name.
    for _, b in ipairs(d.bosses) do
        if b[2] then BOSS_IDS[b[2]] = b[1] end
        BOSS_BY_NAME[b[1]] = b[2] or b[1]
        BOSS_ACH[b[1]] = d.name
    end
    local names = {}
    for _, b in ipairs(d.bosses) do names[#names + 1] = b[1] end
    local function Killed(b)
        if BossKilled(b) then return true end
        -- The kill statistic names the first boss: it covers kills from before the addon.
        if d.stat and b == d.bosses[1] and (StatNumber(d.stat) or 0) > 0 then return true end
        for _, id in ipairs(ns.BOSS_STATS[b[1]] or {}) do
            if (StatNumber(id) or 0) > 0 then return true end
        end
        return false
    end
    return { key = d.key or ("dungeon" .. d.id), id = d.id, icon = d.icon, name = d.name, desc = d.desc, pts = 10,
             list = (d.all and #names > 1) and names or nil,
             has = function(n)
                 for _, b in ipairs(d.bosses) do if b[1] == n then return Killed(b) end end
             end,
             progress = function()
                 local c = 0
                 for _, b in ipairs(d.bosses) do if Killed(b) then c = c + 1 end end
                 if not d.all then
                     -- The boss's head quests also prove the kill.
                     if c == 0 then
                         for _, q in ipairs(d.quests or {}) do if IsQuestDone(q) then c = 1 break end end
                     end
                     return math.min(c, 1), 1
                 end
                 return c, #d.bosses
             end }
end

local dungeonList, raidList = {}, {}
for _, d in ipairs(ns.DUNGEONS) do dungeonList[#dungeonList + 1] = DungeonAch(d) end
raidList[1] = DungeonAch({ key = "onyxia60", id = 684, icon = 254650, name = "Onyxia's Lair", desc = "Defeat Onyxia.",
    bosses = { { "Onyxia", 10184 } }, stat = 1098 })
for _, d in ipairs(ns.RAIDS) do raidList[#raidList + 1] = DungeonAch(d) end
-- Naxxramas (40): no classic version in WotLK, which only had the level 80 raid.
raidList[#raidList + 1] = DungeonAch({ key = "naxx40", icon = 236493, name = "Naxxramas", desc = "Defeat Kel'Thuzad.",
    bosses = { { "Kel'Thuzad", 15990 } } })

-- Dungeons new in WoW Forever (no WotLK achievement): the final boss, by
-- name, plus the kill statistic the Forever client keeps for it.
local FOREVER_DUNGEONS = {
    -- Final bosses: creature IDs from the Spelunker criteria; a name only where
    -- the client gives none. Kill statistics where the client keeps them.
    { key = "dungeonThanes", icon = ns.ICONS[642], name = "The Hall of Thanes", desc = "Defeat Durgen Dirgehammer.",
      bosses = { { "Durgen Dirgehammer" } }, stat = 63573 },
    { key = "dungeonLordaeron", icon = ns.ICONS[631], name = "Ruins of Lordaeron", desc = "Defeat Rath'mael.",
      bosses = { { "Rath'mael", 250657 } }, stat = 63571 },
    { key = "dungeonExcavation", icon = ns.ICONS[638], name = "Excavation Site: Wetlands", desc = "Defeat the Relic Guardian.",
      bosses = { { "Relic Guardian", 260326 } } },
    { key = "dungeonDalaran", icon = ns.ICONS[645], name = "City of Dalaran", desc = "Defeat the Shade of the Archmage.",
      bosses = { { "Shade of the Archmage", 246020 } }, stat = 63572 },
    { key = "dungeonDrowned", icon = ns.ICONS[632], name = "The Drowned City", desc = "Defeat the master of The Drowned City.",
      bosses = { { "The Drowned City", 260274 } } },
    { key = "dungeonKroldok", icon = ns.ICONS[639], name = "Krol'dok Stronghold", desc = "Defeat the master of Krol'dok Stronghold.",
      bosses = { { "Krol'dok Stronghold", 258968 } } },
    { key = "dungeonAlcaz", icon = ns.ICONS[642], name = "Alcaz Prison", desc = "Defeat Blazeroar.",
      bosses = { { "Blazeroar", 255702 } }, stat = 63575 },
    { key = "dungeonBlackmaw", icon = ns.ICONS[640], name = "Blackmaw Hold", desc = "Defeat the master of Blackmaw Hold.",
      bosses = { { "Blackmaw Hold", 247234 } } },
    { key = "dungeonShaper", icon = ns.ICONS[641], name = "The Shaper's Terrace", desc = "Defeat Nanaya.",
      bosses = { { "Nanaya", 261809 } }, stat = 63574 },
}
local foreverList = {}
for _, d in ipairs(FOREVER_DUNGEONS) do foreverList[#foreverList + 1] = DungeonAch(d) end

local DUNGEON_SECTIONS = {
    { title = "DUNGEONS", list = dungeonList },
    { title = "FOREVER DUNGEONS", list = foreverList },
    { title = "RAIDS", list = raidList },
}

-- Reputation, PvP, Feats and the Forever tab; their helpers stay inside the
-- block (a Lua chunk allows 200 locals at a time).
local REP_SECTIONS, PVP_SECTIONS, FEAT_SECTIONS
do
-------------------------------------------------------------------------------
--  World bosses and rare enemies
-------------------------------------------------------------------------------
local WORLD_BOSSES = {
    { key = "wbAzuregos", name = "Azuregos", desc = "Defeat Azuregos in Azshara.", bosses = { { "Azuregos", 6109 } } },
    { key = "wbKazzak", name = "Lord Kazzak", desc = "Defeat Lord Kazzak.", bosses = { { "Lord Kazzak", 12397 } } },
    { key = "wbYsondre", name = "Ysondre", desc = "Defeat Ysondre, a Dragon of Nightmare.", bosses = { { "Ysondre", 14887 } } },
    { key = "wbLethon", name = "Lethon", desc = "Defeat Lethon, a Dragon of Nightmare.", bosses = { { "Lethon", 14888 } } },
    { key = "wbEmeriss", name = "Emeriss", desc = "Defeat Emeriss, a Dragon of Nightmare.", bosses = { { "Emeriss", 14889 } } },
    { key = "wbTaerar", name = "Taerar", desc = "Defeat Taerar, a Dragon of Nightmare.", bosses = { { "Taerar", 14890 } } },
}
local worldBossList = {}
for _, d in ipairs(WORLD_BOSSES) do
    d.icon = ns.ICONS[686]
    worldBossList[#worldBossList + 1] = DungeonAch(d)
end
worldBossList[#worldBossList + 1] = DungeonAch({ key = "wbNightmare", icon = ns.ICONS[686], name = "Nightmare's End",
    desc = "Defeat the four Dragons of Nightmare.", all = true,
    bosses = { { "Ysondre", 14887 }, { "Lethon", 14888 }, { "Emeriss", 14889 }, { "Taerar", 14890 } } })
for _, a in ipairs(worldBossList) do a.pts = (a.key == "wbNightmare") and 25 or 10 end
table.insert(DUNGEON_SECTIONS, { title = "WORLD BOSSES", list = worldBossList })

-- Rares: any rare or rare elite you kill, counted once per name.
local function RareAch(key, n, name)
    return { key = key, series = "rares", name = name, icon = 136147, pts = 10,
             desc = ("Slay %d different rare enemies."):format(n),
             progress = function() return math.min(Count(DB().rares), n), n end }
end
table.insert(SECTIONS, { title = "RARE ENEMIES", list = {
    RareAch("rare1", 1, "Something Rare"), RareAch("rare10", 10, "Rare Hunter"),
    RareAch("rare25", 25, "Seasoned Rare Hunter"), RareAch("rare50", 50, "Rare Collector"),
    RareAch("rare100", 100, "Rarely Seen, Always Slain"),
} })

-------------------------------------------------------------------------------
--  Reputation
-------------------------------------------------------------------------------
local EXALTED = 42000
local GetFactionDataByID = C_Reputation and C_Reputation.GetFactionDataByID

-- Standing as a number on the classic scale: 0 neutral, 42000 exalted.
local function Standing(id)
    if GetFactionDataByID then
        local data = GetFactionDataByID(id)
        if data and data.currentStanding and not secret(data.currentStanding) then return data.currentStanding end
    end
    if GetFactionInfoByID then
        local _, _, _, _, _, value = GetFactionInfoByID(id)
        if value and not secret(value) then return value end
    end
    return 0
end

-- Best standing ever seen, so a dip after a hostile kill keeps the record.
local function BestStanding(id)
    local d = DB()
    local now = Standing(id)
    if now > (d.reps[id] or -99999) then d.reps[id] = now end
    return d.reps[id]
end

local function IsExalted(id) return BestStanding(id) >= EXALTED end

local function ExaltedCount()
    local n = 0
    for _, f in ipairs(ns.FACTIONS) do if IsExalted(f[1]) then n = n + 1 end end
    return n
end

local FACTION_NAME = {}
for _, f in ipairs(ns.FACTIONS) do FACTION_NAME[f[1]] = f[2] end

local function ExaltedSeries(key, id, n, name)
    return { key = key, id = id, series = "exalted", name = name, pts = 10,
             desc = n == 1 and "Raise a reputation to Exalted." or ("Raise %d reputations to Exalted."):format(n),
             progress = function() return math.min(ExaltedCount(), n), n end }
end

-- Exalted with every faction listed; one faction shows its standing.
local function RepAch(key, id, name, desc, factions, pts, extra)
    local names = {}
    for _, fid in ipairs(factions) do names[#names + 1] = FACTION_NAME[fid] or ("Faction " .. fid) end
    local a = { key = key, id = id, name = name, desc = desc, pts = pts or 10 }
    if #factions == 1 then
        a.progress = function() return math.max(0, math.min(BestStanding(factions[1]), EXALTED)), EXALTED end
    else
        a.list = names
        a.has = function(n)
            for i, fid in ipairs(factions) do if names[i] == n then return IsExalted(fid) end end
        end
        a.progress = function()
            local c = 0
            for _, fid in ipairs(factions) do if IsExalted(fid) then c = c + 1 end end
            return c, #factions
        end
    end
    for k, v in pairs(extra or {}) do a[k] = v end
    return a
end

local INSANE = { 21, 577, 369, 470, 349, 909 }
local insane = RepAch("insane", 2336, "Insane in the Membrane",
    "Honored with the Bloodsail Buccaneers, and Exalted with Booty Bay, Everlook, Gadgetzan, Ratchet, Ravenholdt and the Darkmoon Faire.",
    INSANE, 10, { title = "%s the Insane" })
-- The Bloodsail part is Honored, not Exalted.
local insaneNames = { "Bloodsail Buccaneers (Honored)" }
for _, fid in ipairs(INSANE) do insaneNames[#insaneNames + 1] = FACTION_NAME[fid] end
insane.list = insaneNames
insane.has = function(n)
    if n:find("Bloodsail", 1, true) then return BestStanding(87) >= 9000 end
    for _, fid in ipairs(INSANE) do if FACTION_NAME[fid] == n then return IsExalted(fid) end end
end
insane.progress = function()
    local c = BestStanding(87) >= 9000 and 1 or 0
    for _, fid in ipairs(INSANE) do if IsExalted(fid) then c = c + 1 end end
    return c, #INSANE + 1
end

REP_SECTIONS = {
    { title = "EXALTED", list = {
        ExaltedSeries("ex1", 522, 1, "Somebody Likes Me"), ExaltedSeries("ex5", 523, 5, "5 Exalted Reputations"),
        ExaltedSeries("ex10", 524, 10, "10 Exalted Reputations"), ExaltedSeries("ex15", 521, 15, "15 Exalted Reputations"),
        ExaltedSeries("ex20", 520, 20, "20 Exalted Reputations"), ExaltedSeries("ex25", 519, 25, "25 Exalted Reputations"),
        ExaltedSeries("ex30", 518, 30, "30 Exalted Reputations"),
    } },
    { title = "HOME CITIES", list = {
        RepAch("ambAlliance", 948, "Ambassador of the Alliance", "Earn exalted reputation with the Alliance home cities.",
            { 72, 47, 69, 54 }, 10, { faction = "Alliance", title = "Ambassador %s" }),
        RepAch("ambHorde", 762, "Ambassador of the Horde", "Earn exalted reputation with the Horde home cities.",
            { 76, 81, 68, 530 }, 10, { faction = "Horde", title = "Ambassador %s" }),
    } },
    { title = "CLASSIC FACTIONS", list = {
        RepAch("repTimbermaw", 944, "They Love Me In That Tunnel", "Earn exalted status with Timbermaw Hold.", { 576 }, 15),
        RepAch("repArgent", 946, "The Argent Dawn", "Earn exalted status with the Argent Dawn.", { 529 }, 15),
        RepAch("repCenarius", 953, "Guardian of Cenarius", "Earn exalted status with the Cenarion Circle.", { 609 }, 25,
            { title = "%s, Guardian of Cenarius" }),
        RepAch("repHydraxian", 955, "Hydraxian Waterlords", "Earn exalted status with the Hydraxian Waterlords.", { 749 }),
        RepAch("repBrood", 956, "Brood of Nozdormu", "Earn exalted status with the Brood of Nozdormu.", { 910 }),
        RepAch("repZandalar", 957, "Hero of the Zandalar Tribe", "Earn exalted status with the Zandalar Tribe.", { 270 }),
        RepAch("repThorium", nil, "Thorium Brotherhood", "Earn exalted status with the Thorium Brotherhood.", { 59 }, 10,
            { icon = 236681 }),
        RepAch("repShendralar", nil, "Shen'dralar", "Earn exalted status with the Shen'dralar.", { 809 }, 10, { icon = 236681 }),
        RepAch("repWintersaber", nil, "Wintersaber Trainers", "Earn exalted status with the Wintersaber Trainers.", { 589 }, 10,
            { icon = 132252, faction = "Alliance" }),
        RepAch("repDarkmoon", nil, "Darkmoon Faire", "Earn exalted status with the Darkmoon Faire.", { 909 }, 10, { icon = 236681 }),
        insane,
    } },
}

-- Factions new in WoW Forever: exalted with each.
local foreverReps = {}
for _, f in ipairs(ns.FACTIONS) do
    if f[1] >= 2586 and f[1] ~= 2798 and f[1] ~= 2799 then
        foreverReps[#foreverReps + 1] = RepAch("rep" .. f[1], nil, f[2], "Earn exalted status with " .. f[2] .. ".",
            { f[1] }, 10, { icon = 236681 })
    end
end
table.insert(REP_SECTIONS, { title = "FOREVER FACTIONS", list = foreverReps })

-------------------------------------------------------------------------------
--  Player vs. Player
-------------------------------------------------------------------------------
local STAT_HK = 588
local function HonorKills()
    local life = GetPVPLifetimeStats and GetPVPLifetimeStats()
    if secret(life) then life = nil end
    return math.max(StatNumber(STAT_HK) or 0, tonumber(life) or 0)
end

local function HKAch(key, id, n)
    return { key = key, id = id, series = "hk", pts = 10,
             name = n == 1 and "An Honorable Kill" or (n .. " Honorable Kills"),
             desc = n == 1 and "Achieve an honorable kill." or ("Get %d honorable kills."):format(n),
             progress = function() return math.min(HonorKills(), n), n end }
end

local function StatAch(key, id, name, desc, stat, n, extra)
    local a = { key = key, id = id, name = name, desc = desc, pts = 10,
                progress = function() return math.min(StatNumber(stat) or 0, n), n end }
    for k, v in pairs(extra or {}) do a[k] = v end
    return a
end

local function Flag(key, id, name, desc, extra)
    local a = { key = key, id = id, name = name, desc = desc, pts = 10,
                progress = function() return DB().flags[key] and 1 or 0, 1 end }
    for k, v in pairs(extra or {}) do a[k] = v end
    return a
end

local STAT_WSG, STAT_AB, STAT_AV, STAT_DI = 105, 51, 49, 64176
local DI_ICON = 441150

local battlemaster = { key = "battlemaster", id = 230, name = "Battlemaster", pts = 50, title = "Battlemaster %s",
    desc = "Win Warsong Gulch, Arathi Basin, Alterac Valley and Darkspear Islands.",
    list = { "Warsong Gulch", "Arathi Basin", "Alterac Valley", "Darkspear Islands" } }
local BM_STATS = { ["Warsong Gulch"] = STAT_WSG, ["Arathi Basin"] = STAT_AB, ["Alterac Valley"] = STAT_AV,
    ["Darkspear Islands"] = STAT_DI }
battlemaster.has = function(n) return (StatNumber(BM_STATS[n]) or 0) > 0 end
battlemaster.progress = function()
    local c = 0
    for _, n in ipairs(battlemaster.list) do if battlemaster.has(n) then c = c + 1 end end
    return c, #battlemaster.list
end

-- The other faction's leaders, as the classic capitals have them.
local LEADERS_H = { { "Thrall", 4949 }, { "Cairne Bloodhoof", 3057 }, { "Lady Sylvanas Windrunner", 10181 }, { "Vol'jin", 10540 } }
local LEADERS_A = { { "Highlord Bolvar Fordragon", 1748 }, { "King Magni Bronzebeard", 2784 },
    { "Tyrande Whisperwind", 7999 }, { "High Tinker Mekkatorque", 7937 } }
local forAlliance = DungeonAch({ key = "forAlliance", id = 614, name = "For The Alliance!", all = true,
    desc = "Slay the leaders of the Horde.", bosses = LEADERS_H })
forAlliance.faction, forAlliance.pts = "Alliance", 20
local forHorde = DungeonAch({ key = "forHorde", id = 619, name = "For The Horde!", all = true,
    desc = "Slay the leaders of the Alliance.", bosses = LEADERS_A })
forHorde.faction, forHorde.pts = "Horde", 20

PVP_SECTIONS = {
    { title = "HONORABLE KILLS", list = {
        HKAch("hk1", 238, 1), HKAch("hk100", 513, 100), HKAch("hk500", 515, 500), HKAch("hk1000", 516, 1000),
        HKAch("hk5000", 512, 5000), HKAch("hk10000", 509, 10000), HKAch("hk25000", 239, 25000),
        HKAch("hk50000", 869, 50000), HKAch("hk100000", 870, 100000),
    } },
    { title = "BATTLEGROUNDS", list = {
        StatAch("wsgWin", 166, "Warsong Gulch Victory", "Win Warsong Gulch.", STAT_WSG, 1, { series = "wsg" }),
        StatAch("wsgVet", 167, "Warsong Gulch Veteran", "Complete 100 victories in Warsong Gulch.", STAT_WSG, 100, { series = "wsg" }),
        StatAch("abWin", 154, "Arathi Basin Victory", "Win Arathi Basin.", STAT_AB, 1, { series = "ab" }),
        StatAch("abVet", 155, "Arathi Basin Veteran", "Complete 100 victories in Arathi Basin.", STAT_AB, 100, { series = "ab" }),
        StatAch("avWin", 218, "Alterac Valley Victory", "Win Alterac Valley.", STAT_AV, 1, { series = "av" }),
        StatAch("avVet", 219, "Alterac Valley Veteran", "Complete 100 victories in Alterac Valley.", STAT_AV, 100, { series = "av" }),
        StatAch("diWin", nil, "Darkspear Islands Victory", "Win Darkspear Islands.", STAT_DI, 1, { series = "di", icon = DI_ICON }),
        StatAch("diVet", nil, "Darkspear Islands Veteran", "Complete 100 victories in Darkspear Islands.", STAT_DI, 100,
            { series = "di", icon = DI_ICON }),
        battlemaster,
    } },
    { title = "IN THE BATTLE", list = {
        StatAch("captureFlag", 199, "Capture the Flag", "Personally carry and capture the flag in Warsong Gulch.", 395, 1),
        StatAch("persistent", 200, "Persistent Defender", "Return 50 flags as a defender in Warsong Gulch.", 586, 50),
        StatAch("towerDefense", 222, "Tower Defense", "Defend 50 towers in Alterac Valley.", 393, 50),
        Flag("grimReaper", 229, "The Grim Reaper", "Get 30 honorable kills in a single battle in any battleground."),
        Flag("wreckingBall", 231, "Wrecking Ball", "Get 20 killing blows without dying in a single battle in any battleground."),
        Flag("wsgFast", 201, "Warsong Expedience", "Win Warsong Gulch in under 7 minutes."),
        Flag("abFast", 159, "Let's Get This Done", "Win Arathi Basin in 6 minutes."),
        Flag("avFast", 226, "The Alterac Blitz", "Win Alterac Valley in 6 minutes.", { pts = 20 }),
    } },
    { title = "BATTLEGROUND REPUTATION", list = {
        RepAch("repFrostwolf", 708, "Hero of the Frostwolf Clan", "Gain exalted reputation with the Frostwolf Clan.", { 729 }, 10, { faction = "Horde" }),
        RepAch("repStormpike", 709, "Hero of the Stormpike Guard", "Gain exalted reputation with the Stormpike Guard.", { 730 }, 10, { faction = "Alliance" }),
        RepAch("repDefilers", 710, "The Defiler", "Gain exalted reputation with The Defilers.", { 510 }, 10, { faction = "Horde" }),
        RepAch("repArathor", 711, "Knight of Arathor", "Gain exalted reputation with The League of Arathor.", { 509 }, 10, { faction = "Alliance" }),
        RepAch("repOutriders", 712, "Warsong Outrider", "Gain exalted reputation with the Warsong Outriders.", { 889 }, 10, { faction = "Horde" }),
        RepAch("repSilverwing", 713, "Silverwing Sentinel", "Gain exalted reputation with the Silverwing Sentinels.", { 890 }, 10, { faction = "Alliance" }),
        RepAch("repRaiders", nil, "Darkspear Raider", "Gain exalted reputation with the Darkspear Raiders.", { 2798 }, 10,
            { faction = "Horde", icon = DI_ICON }),
        RepAch("repTheramore", nil, "Theramore Expeditionary", "Gain exalted reputation with the Theramore Expeditionary Force.",
            { 2799 }, 10, { faction = "Alliance", icon = DI_ICON }),
        RepAch("conqueror", 714, "The Conqueror", "Exalted with the Frostwolf Clan, The Defilers and the Warsong Outriders.",
            { 729, 510, 889 }, 20, { faction = "Horde", title = "Conqueror %s" }),
        RepAch("justicar", 907, "The Justicar", "Exalted with the Stormpike Guard, The League of Arathor and the Silverwing Sentinels.",
            { 730, 509, 890 }, 20, { faction = "Alliance", title = "Justicar %s" }),
    } },
    { title = "WORLD PVP", list = {
        StatAch("duel", 1157, "Duel-icious", "Win a duel against another player.", 319, 1),
        Flag("hugDead", 247, "Make Love, Not Warcraft", "Emote /hug on a dead enemy before they release corpse."),
        forAlliance, forHorde,
    } },
}

-------------------------------------------------------------------------------
--  Feats of Strength (no points, as in WotLK)
-------------------------------------------------------------------------------
-- Owned once counts for good: selling or banking the item later keeps it.
local function Owns(items, spells)
    local d = DB()
    local count = (C_Item and C_Item.GetItemCount) or GetItemCount
    for _, id in ipairs(items or {}) do
        if d.owned[id] then return true end
        if (count and (count(id, true) or 0) > 0) or (IsEquippedItem and IsEquippedItem(id)) then
            d.owned[id] = true
            return true
        end
    end
    for _, id in ipairs(spells or {}) do
        if IsPlayerSpell and IsPlayerSpell(id) then return true end
        -- Mounts live in the mount journal on this client.
        if C_MountJournal and C_MountJournal.GetMountFromSpell then
            local mountID = C_MountJournal.GetMountFromSpell(id)
            if mountID and select(11, C_MountJournal.GetMountInfoByID(mountID)) then return true end
        end
    end
    return false
end

local function Feat(key, id, name, desc, items, spells, extra)
    local a = { key = key, id = id, name = name, desc = desc, pts = 0,
                progress = function() return Owns(items, spells) and 1 or 0, 1 end }
    for k, v in pairs(extra or {}) do a[k] = v end
    return a
end


FEAT_SECTIONS = {
    { title = "LEGENDARY", list = {
        Feat("thunderfury", 428, "Thunderfury, Blessed Blade of the Windseeker", "Wielder of Thunderfury, Blessed Blade of the Windseeker.", { 19019 }),
        Feat("sulfuras", 429, "Sulfuras, Hand of Ragnaros", "Wielder of Sulfuras, Hand of Ragnaros.", { 17182 }),
        Feat("atiesh", 425, "Atiesh, Greatstaff of the Guardian", "Wielder of Atiesh, Greatstaff of the Guardian.",
            { 22589, 22630, 22631, 22632 }),
    } },
    { title = "MOUNTS", list = {
        Feat("deathcharger", 729, "Deathcharger's Reins", "Obtain the Deathcharger's Reins from Baron Rivendare in Stratholme.",
            { 13335 }, { 17481 }),
        Feat("zulianTiger", 880, "Swift Zulian Tiger", "Obtain the Swift Zulian Tiger from High Priest Thekal in Zul'Gurub.",
            { 19902 }, { 24252 }),
        Feat("razzashi", 881, "Swift Razzashi Raptor", "Obtain the Swift Razzashi Raptor from Bloodlord Mandokir in Zul'Gurub.",
            { 19872 }, { 24242 }),
        Feat("frostsaber", 3356, "Winterspring Frostsaber", "Obtain a Winterspring Frostsaber.", { 13086 }, { 17229 }),
        Feat("dreadsteed", 2357, "Dreadsteed of Xoroth", "Completed the Dreadsteed of Xoroth warlock quest.", nil, { 23161 }),
        Feat("charger", 2358, "Charger", "Completed the paladin quest to obtain a Charger.", nil, { 23214 }),
        Feat("redQiraji", 424, "Why? Because It's Red", "Obtain a Red Qiraji Resonating Crystal.", { 21321 }, { 26054 }),
    } },
    { title = "TITLES & RARE FINDS", list = {
        Feat("scarabLord", 416, "Scarab Lord", "Opened the gates of Ahn'Qiraj.", { 21176 }, { 26656 },
            { title = "Scarab Lord %s" }),
        Feat("admiral", 871, "Avast Ye, Admiral!", "Obtain the Bloodsail Admiral's Hat.", { 12185 }, nil,
            { title = "Bloodsail Admiral %s" }),
        Feat("fifthElement", 2496, "The Fifth Element", "Obtain an Aqual Quintessence.", { 17333 }),
    } },
}

-------------------------------------------------------------------------------
--  The Forever client's own achievements, read from the game
-------------------------------------------------------------------------------
local function FvInfo(ids)
    if not GetAchievementInfo then return nil end
    local best
    for _, id in ipairs(ids) do
        local ok, aid, _, _, completed = pcall(GetAchievementInfo, id)
        if ok and aid then
            if completed then return id, true end
            best = best or id
        end
    end
    return best, false
end

local function FvCriteria(id)
    local out = {}
    if not (id and GetAchievementNumCriteria and GetAchievementCriteriaInfo) then return out end
    local ok, n = pcall(GetAchievementNumCriteria, id)
    if not ok or not n then return out end
    for i = 1, n do
        local ok2, name, _, done = pcall(GetAchievementCriteriaInfo, id, i)
        if ok2 and name and name ~= "" then out[#out + 1] = { name, done } end
    end
    return out
end

-- The Forever client's own achievements go into the matching categories;
-- the ones that repeat an addon achievement are left out.
local FV_SKIP = { ["Conqueror of the Lair"] = true, -- the addon's Onyxia's Lair
    ["Explore Azeroth"] = true, ["Explore Eastern Kingdoms"] = true, ["Explore Kalimdor"] = true,
    ["Explorer"] = true }
local FV_SKIP_GROUP = { Reputations = true } -- Master of <battleground>: the addon's BG reputations
local function SectionIn(sections, title, atStart)
    for _, sec in ipairs(sections) do if sec.title == title then return sec end end
    local sec = { title = title, list = {} }
    if atStart then table.insert(sections, 1, sec) else sections[#sections + 1] = sec end
    return sec
end
local function FvAch(e)
    -- 10 points like the rest of the addon (the client stores 0 for these).
    local a = { key = "fv" .. e.ids[1], icon = e.icon, name = e.name, desc = e.desc, pts = 10, native = true }
    a.progress = function()
        local id, done = FvInfo(e.ids)
        if done then return 1, 1 end
        local crit = FvCriteria(id)
        if #crit > 1 then
            local c = 0
            for _, it in ipairs(crit) do if it[2] then c = c + 1 end end
            return c, #crit
        end
        return 0, 1
    end
    a.dynamicList = function() return FvCriteria((FvInfo(e.ids))) end
    return a
end
for _, sec in ipairs(ns.FOREVER_ACH) do
    for _, e in ipairs(sec.list) do
        if not FV_SKIP[e.name] and not FV_SKIP_GROUP[e.group] then
            local a = FvAch(e)
            local target
            if sec.title == "CLASSES" then
                a.series = "fvclass" .. e.group
                target = SectionIn(SECTIONS, "CLASSES")
            elseif sec.title == "TRADESKILLS" then
                a.series = "fvprof" .. e.group
                target = SectionIn(PROF_SECTIONS, "PROFESSION RANKS")
                -- Right after the general ranks, not after First Aid.
                if PROF_SECTIONS[#PROF_SECTIONS] == target and #target.list == 0 then
                    table.remove(PROF_SECTIONS)
                    table.insert(PROF_SECTIONS, 2, target)
                end
            elseif sec.title == "DUNGEONS" then
                a.series = "fvspelunker"
                target = SectionIn(DUNGEON_SECTIONS, "SPELUNKER")
                -- With the dungeons, before the raids.
                if #target.list == 0 then
                    for i, sec in ipairs(DUNGEON_SECTIONS) do
                        if sec == target then table.remove(DUNGEON_SECTIONS, i) break end
                    end
                    for i, sec in ipairs(DUNGEON_SECTIONS) do
                        if sec.title == "RAIDS" then table.insert(DUNGEON_SECTIONS, i, target) break end
                    end
                end
            elseif sec.title == "RAIDS" then
                target = SectionIn(DUNGEON_SECTIONS, "RAIDS")
            elseif e.group == "Ranks" then
                a.series = "fvrank"
                target = SectionIn(PVP_SECTIONS, "HONOR RANKS")
            elseif e.group == "Season Journey" then
                a.series = "fvseason"
                target = SectionIn(PVP_SECTIONS, "SEASON JOURNEY")
            elseif sec.title == "PLAYER VS. PLAYER" then
                target = SectionIn(PVP_SECTIONS, "WORLD PVP")
            else
                target = SectionIn(QUEST_SECTIONS, "QUEST LINES")
            end
            target.list[#target.list + 1] = a
        end
    end
end
end

-- Categories, one per tab.
local CATEGORY_SECTIONS = {
    general = SECTIONS,
    quests = QUEST_SECTIONS,
    exploration = EXPLORE_SECTIONS,
    professions = PROF_SECTIONS,
    dungeons = DUNGEON_SECTIONS,
    reputation = REP_SECTIONS,
    pvp = PVP_SECTIONS,
    feats = FEAT_SECTIONS,
}
local CATEGORY_ORDER = { "general", "quests", "exploration", "professions", "dungeons", "reputation", "pvp", "feats" }

local ALL = {}
local SERIES = {} -- [series] = achievements in order
for _, catKey in ipairs(CATEGORY_ORDER) do
    for _, sec in ipairs(CATEGORY_SECTIONS[catKey]) do
        for _, a in ipairs(sec.list) do
            ALL[#ALL + 1] = a
            if a.series then
                SERIES[a.series] = SERIES[a.series] or {}
                table.insert(SERIES[a.series], a)
            end
        end
    end
end

-- Account-wide data (characters, settings), saved for every character.
local function AccountDB()
    ForeverAchievementsDB = ForeverAchievementsDB or {}
    local a = ForeverAchievementsDB
    a.chars = a.chars or {}
    a.settings = a.settings or {}
    return a
end

local function Settings() return AccountDB().settings end

-- Faction-only achievements show for that faction alone; ones that need
-- another addon (requires) only while it is loaded.
local function Available(a)
    if a.unsupported then return false end -- preserve definitions and old saved keys
    if a.requires and not a.requires() then return false end
    return not a.faction or a.faction == UnitFactionGroup("player")
end

-- Earned on this character, or on any character with the account view on.
local function Earned(key)
    local t = DB().done[key]
    if t or not Settings().accountView then return t end
    for _, c in pairs(AccountDB().chars) do
        if c.done and c.done[key] then return c.done[key] end
    end
end

local EARN_HOOKS, CHECK_HOOKS = {}, {} -- filled by the modules
local VIEWS = {}                        -- [tab] = function(child, width) return height
local SLASH = {}                        -- [command] = function(rest)
local COMPARE = {}                      -- name, done: another player's earned keys
local LINK = { fn = function(a) return "|cffffd100[" .. a.name .. "]|r" end }

-------------------------------------------------------------------------------
--  Completion and the toast
-------------------------------------------------------------------------------
local RefreshWindow -- the window, below
local toast

-- The Alpha look (AlphaUI.lua), shared with Quick Fish's /qfa window.
local Kit = ns.Alpha

local function Accent() return Kit.Accent() end

local function Font(parent, size, r, g, b, a) return Kit.MakeFont(parent, size, nil, r, g, b, a) end

local queue, showing = {}, false
local function ShowNextToast()
    local a = table.remove(queue, 1)
    if not a then showing = false return end
    showing = true
    if not toast then
        local r, g, b = Accent()
        toast = CreateFrame("Frame", nil, UIParent)
        -- Size and place on whole pixels (PixelUtil), so the 1 px border is even.
        if PixelUtil then
            PixelUtil.SetSize(toast, 340, 64)
            PixelUtil.SetPoint(toast, "TOP", UIParent, "TOP", 0, -(Settings().toastY or 140))
        else
            toast:SetSize(340, 64)
            toast:SetPoint("TOP", UIParent, "TOP", 0, -(Settings().toastY or 140))
        end
        toast:SetFrameStrata("HIGH")
        local bg = toast:CreateTexture(nil, "BACKGROUND")
        bg:SetAllPoints()
        local cbg = Kit.COLORS.bg
        bg:SetColorTexture(cbg[1], cbg[2], cbg[3], 0.97)
        Kit.MakeBorder(toast, r, g, b, 0.7)
        toast.icon = toast:CreateTexture(nil, "ARTWORK")
        toast.icon:SetSize(44, 44)
        toast.icon:SetPoint("LEFT", 14, 0)
        toast.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
        toast.head = Font(toast, 11, r, g, b, 1)
        toast.head:SetPoint("TOPLEFT", toast.icon, "TOPRIGHT", 10, -4)
        toast.head:SetText("Achievement earned")
        toast.name = Font(toast, 14, 1, 1, 1, 1)
        toast.name:SetPoint("TOPLEFT", toast.head, "BOTTOMLEFT", 0, -4)
        toast.name:SetPoint("RIGHT", -44, 0)
        toast.name:SetJustifyH("LEFT")
        toast.name:SetWordWrap(false)
        toast.pts = Font(toast, 16, r, g, b, 1)
        toast.pts:SetPoint("RIGHT", -14, 0)
        -- Shine: a soft light band that sweeps across once, as in WotLK.
        toast:SetClipsChildren(true)
        toast.shine = CreateFrame("Frame", nil, toast)
        toast.shine:SetSize(90, 64)
        toast.shine:SetFrameLevel(toast:GetFrameLevel() + 5)
        for i, side in ipairs({ { 0, 0.22 }, { 0.22, 0 } }) do
            local t = toast.shine:CreateTexture(nil, "OVERLAY")
            t:SetSize(45, 64)
            t:SetPoint("LEFT", (i - 1) * 45, 0)
            t:SetColorTexture(1, 1, 1, 1)
            local ok = CreateColor and pcall(t.SetGradient, t, "HORIZONTAL",
                CreateColor(1, 1, 1, side[1]), CreateColor(1, 1, 1, side[2]))
            if not ok then t:SetAlpha(0.1) end
        end
        toast.shine:Hide()
    end
    toast.icon:SetTexture((a.icon or ns.ICONS[a.id] or 236376))
    toast.name:SetText(a.name)
    toast.pts:SetText(tostring(a.pts))
    -- In: slides down 18 units while fading in, then the shine sweeps across.
    local baseY = -(Settings().toastY or 140)
    local function Place(y)
        if PixelUtil then PixelUtil.SetPoint(toast, "TOP", UIParent, "TOP", 0, y)
        else toast:SetPoint("TOP", UIParent, "TOP", 0, y) end
    end
    toast:Show()
    Kit.Tween("toastIn", 0.35, function(e)
        toast:SetAlpha(e)
        Place(baseY + 18 * (1 - e))
    end, function()
        Place(baseY)
        Kit.RealignBorders()
        toast.shine:Show()
        Kit.Tween("toastShine", 0.8, function(e)
            toast.shine:SetPoint("LEFT", toast, "LEFT", Kit.Lerp(-90, 340, e), 0)
        end, function() toast.shine:Hide() end)
    end)
    if Settings().sound ~= false and PlaySound and SOUNDKIT then
        local kit = SOUNDKIT[Settings().soundName or "UI_ACHIEVEMENT_AWARDED"]
        PlaySound(kit or SOUNDKIT.UI_ACHIEVEMENT_AWARDED or SOUNDKIT.LEVELUP or 888, "Master")
    end
    -- Out: fades away, then the next one in the queue.
    C_Timer.After(Settings().toastTime or 4, function()
        Kit.Tween("toastOut", 0.4, function(e) toast:SetAlpha(1 - e) end, function()
            toast:Hide()
            C_Timer.After(0.2, ShowNextToast)
        end)
    end)
end

local function Complete(a)
    local d = DB()
    if d.done[a.key] then return end
    d.done[a.key] = time()
    d.tracked[a.key] = nil
    print(TAG .. " earned: " .. LINK.fn(a))
    if Settings().toasts ~= false then
        queue[#queue + 1] = a
        if not showing then ShowNextToast() end
    end
    for _, fn in ipairs(EARN_HOOKS) do pcall(fn, a) end
    if Settings().screenshot and Screenshot then C_Timer.After(1, Screenshot) end
end

-- Until the first quiet pass over the character's history has run, every
-- check is quiet: events fire right after login (entering the world, bags)
-- and would otherwise toast everything the character already had.
local historyReady = false

local function CheckAll(quiet)
    if not historyReady then quiet = true end
    for _, a in ipairs(ALL) do
        if not DB().done[a.key] and Available(a) then
            local cur, need = a.progress()
            if ProgressKnown(cur, need) and cur >= need then
                if quiet then DB().done[a.key] = time() else Complete(a) end
            end
        end
    end
    if RefreshWindow then RefreshWindow() end
    for _, fn in ipairs(CHECK_HOOKS) do pcall(fn) end
end

-------------------------------------------------------------------------------
--  Trackers
-------------------------------------------------------------------------------
local ev = CreateFrame("Frame")
local handlers = {}
-- Registration is guarded: an event this client does not have would stop
-- the whole file from loading.
local function On(event, fn)
    if pcall(ev.RegisterEvent, ev, event) then handlers[event] = fn end
end
ev:SetScript("OnEvent", function(_, event, ...) handlers[event](...) end)

-- Login: anything already true counts quietly (no toast storm), then checks.
On("PLAYER_LOGIN", function()
    CountLore()
    NoteSubzone()
    -- Achievements added in a new version are taken in quietly once (no
    -- toast storm for what was already true); two passes so the continent
    -- and Loremaster metas see the zones and continents earned in the first.
    local DATA_VERSION = 9
    local d = DB()
    if (d.dataVersion or (d.initialised and 1 or 0)) < DATA_VERSION then
        local before = Count(d.done)
        -- The map knows explored areas only once the player is in the world.
        C_Timer.After(3, function()
            CheckAll(true)
            CheckAll(true)
            d.initialised = true
            d.dataVersion = DATA_VERSION
            historyReady = true
            print(TAG .. " ready: " .. Count(d.done) .. " earned (" .. (Count(d.done) - before)
                .. " new from your history). /qa or /fach to open.")
            if ns.FA and ns.FA.OnReady then ns.FA.OnReady(Count(d.done) - before) end
        end)
    else
        historyReady = true
        CheckAll(false)
        -- A character that has not seen the welcome screen yet gets it now.
        if ns.FA and ns.FA.OnReady then ns.FA.OnReady() end
    end
end)
On("PLAYER_LEVEL_UP", function() C_Timer.After(1, function() CheckAll() end) end)
On("QUEST_TURNED_IN", function()
    C_Timer.After(1, function() CountLore(); CheckAll() end)
end)
for _, e in ipairs({ "ZONE_CHANGED", "ZONE_CHANGED_INDOORS", "ZONE_CHANGED_NEW_AREA" }) do
    On(e, function() if NoteSubzone() then CheckAll() end end)
end
On("PLAYER_EQUIPMENT_CHANGED", function() CheckAll() end)
On("BAG_UPDATE_DELAYED", function() CheckAll() end)
On("SKILL_LINES_CHANGED", function() CheckAll() end)
On("LEARNED_SPELL_IN_TAB", function() CheckAll() end)
On("LEARNED_SPELL_IN_SKILL_LINE", function() CheckAll() end)
if C_MountJournal then On("NEW_MOUNT_ADDED", function() CheckAll() end) end
if C_PetJournal then On("NEW_PET_ADDED", function() CheckAll() end) end
On("COMPANION_LEARNED", function() CheckAll() end)

-- Money looted, from the loot money messages (solo loot and party shares).
local function ParseMoney(msg)
    local function amount(word)
        local n = msg:match("(%d+)%s*" .. word)
        return tonumber(n) or 0
    end
    local g = amount(_G.GOLD or "Gold")
    local s = amount(_G.SILVER or "Silver")
    local c = amount(_G.COPPER or "Copper")
    return g * 10000 + s * 100 + c
end
-- The client keeps a "Gold looted" statistic (ID 333) for the whole life of
-- the character, as a money string with coin icons. When it is there it is
-- the better number; our own count covers clients without it.
local STAT_GOLD_LOOTED = 333
local function StatMoney()
    local text = GetStatistic and GetStatistic(STAT_GOLD_LOOTED)
    if type(text) ~= "string" or secret(text) then return nil end
    local total, found = 0, false
    for n, coin in text:gmatch("(%d+)%s*|T[^|]-UI%-(%a+)Icon") do
        local v = tonumber(n) or 0
        coin = coin:lower()
        if coin == "gold" then total = total + v * 10000
        elseif coin == "silver" then total = total + v * 100
        else total = total + v end
        found = true
    end
    if not found then
        local plain = tonumber((text:gsub("%D", "")))
        if plain then return plain end
        return nil
    end
    return total
end

local function SyncMoney()
    local stat = StatMoney()
    if stat and stat > DB().money then DB().money = stat end
end

On("CHAT_MSG_MONEY", function(msg)
    if not msg or secret(msg) then return end
    local copper = ParseMoney(msg)
    if copper > 0 then
        DB().money = DB().money + copper
        SyncMoney()
        CheckAll()
    end
end)
On("PLAYER_ENTERING_WORLD", function()
    bgSeen = false
    C_Timer.After(2, function() SyncMoney(); CheckAll() end)
end)

-- /love on critters: the emote echo names the target.
-- /love on critters. Two ways in: the emote call itself, and the chat echo
-- of it. The target just has to be a creature (not a player) named like a
-- critter on the list; creature types read differently on this client.
local debugOn = false -- /fach debug
local lastLove = 0

local function LoveTarget(source)
    if GetTime() - lastLove < 0.5 then return end
    local target = UnitExists("target") and UnitName("target")
    if debugOn then
        print(TAG .. (" /love seen (%s), target: %s"):format(source, tostring(target)))
    end
    if not target or secret(target) then return end
    local isPlayer = UnitIsPlayer("target")
    if isPlayer and not secret(isPlayer) then return end
    for _, name in ipairs(CRITTERS) do
        if target == name then
            lastLove = GetTime()
            if not DB().critters[name] then
                DB().critters[name] = true
                print(TAG .. " loved a " .. name .. " (" .. Count(DB().critters) .. "/" .. #CRITTERS .. ")")
                CheckAll()
            elseif debugOn then
                print(TAG .. " " .. name .. " already loved")
            end
            return
        end
    end
    if debugOn then print(TAG .. " " .. target .. " is not on the critter list") end
end

if DoEmote then
    hooksecurefunc("DoEmote", function(token)
        if type(token) == "string" and token:upper() == "LOVE" then LoveTarget("emote") end
    end)
end
if C_ChatInfo and C_ChatInfo.PerformEmote then
    hooksecurefunc(C_ChatInfo, "PerformEmote", function(token)
        if type(token) == "string" and token:upper() == "LOVE" then LoveTarget("emote") end
    end)
end

On("CHAT_MSG_TEXT_EMOTE", function(msg, sender)
    if not msg or secret(msg) then return end
    local me = UnitName("player")
    if sender and not secret(sender) and sender ~= me and not sender:find("^" .. me .. "%-") then return end
    local lower = msg:lower()
    if lower:find("love", 1, true) or lower:find("adore", 1, true) then LoveTarget("chat") end
end)

-- Pest Control: your target dying in front of you.
local function NpcID(guid)
    if not guid or secret(guid) then return nil end
    local kind, _, _, _, _, id = strsplit("-", guid)
    if kind ~= "Creature" then return nil end
    return tonumber(id)
end

-- By creature ID, or by name when Forever numbers the creature differently.
local PEST_NAMES = {}
for _, n in pairs(PESTS) do PEST_NAMES[n] = true end

local function NotePest(id, unitName)
    local name = id and PESTS[id]
    if not name and unitName and PEST_NAMES[unitName] then name = unitName end
    if debugOn then
        print(TAG .. (" kill seen: %s, id %s, counted as %s"):format(tostring(unitName), tostring(id), tostring(name)))
    end
    if name and not DB().pests[name] then
        DB().pests[name] = true
        print(TAG .. " pest slain: " .. name .. " (" .. Count(DB().pests) .. "/" .. #PEST_ORDER .. ")")
        CheckAll()
    end
end

-- The combat log is off limits to addons on this client (registering for it
-- is a blocked action), so a pest counts when your target dies.
-- Event driven, so a one-hit kill right after targeting is still seen: the
-- target is remembered the moment it is picked, and checked on every health
-- change. A slow tick backs the events up.
local watchedTarget, watchedAlive, watchedName, watchedID

-- When the target vanishes on its own in combat (dead targets are cleared
-- automatically on many setups), a pest that was alive counts as slain:
-- in combat the client does not say whether it died.
local function NoteBoss(id, unitName)
    local key = (id and BOSS_IDS[id]) and id or (unitName and BOSS_BY_NAME[unitName])
    if not key or DB().bosses[key] then return end
    DB().bosses[key] = time()
    print(TAG .. " boss slain: " .. (BOSS_IDS[key] or unitName))
    CheckAll()
end

local watchedRare

local function NoteRare(unitName)
    if not unitName or DB().rares[unitName] then return end
    DB().rares[unitName] = time()
    print(TAG .. " rare slain: " .. unitName .. " (" .. Count(DB().rares) .. ")")
    CheckAll()
end

local function NoteKill(id, unitName)
    NotePest(id, unitName)
    NoteBoss(id, unitName)
    if watchedRare then NoteRare(unitName) end
end

local function Tracked(id, name)
    return (id and (PESTS[id] or BOSS_IDS[id])) or PEST_NAMES[name or ""] or BOSS_BY_NAME[name or ""] or watchedRare
end

local function TargetGone()
    if watchedTarget and watchedAlive and Tracked(watchedID, watchedName) then
        local fighting = InCombatLockdown() or UnitAffectingCombat("player")
        if secret(fighting) then fighting = true end
        if fighting then
            if debugOn then print(TAG .. " target cleared in combat: counting the kill") end
            NoteKill(watchedID, watchedName)
        end
    end
    watchedTarget, watchedAlive = nil, false
end

local function WatchTarget()
    if not UnitExists("target") then TargetGone() return end
    local guid = UnitGUID("target")
    if guid == nil or secret(guid) then
        if debugOn then print(TAG .. " target GUID is hidden by the client") end
        return
    end
    local dead = UnitIsDead("target")
    -- In combat the client hides whether the target is dead: wait, the
    -- check runs again the moment combat ends.
    if secret(dead) then
        if debugOn then print(TAG .. " target state hidden in combat, checking after combat") end
        return
    end
    if guid ~= watchedTarget then
        local name = UnitName("target")
        watchedTarget, watchedAlive = guid, not dead
        watchedName = (name and not secret(name)) and name or nil
        watchedID = NpcID(guid)
        local class = UnitClassification("target")
        watchedRare = watchedID and not secret(class) and (class == "rare" or class == "rareelite") or nil
        if debugOn then
            print(TAG .. (" target: %s, id %s, %s"):format(tostring(watchedName), tostring(watchedID),
                dead and "dead" or "alive"))
        end
        return
    end
    if watchedAlive and dead then
        watchedAlive = false
        -- Yours if nobody else had tagged it.
        local denied = UnitIsTapDenied and UnitIsTapDenied("target")
        if denied and not (secret(denied)) then
            if debugOn then print(TAG .. " kill not yours (tagged by someone else)") end
            return
        end
        NoteKill(watchedID, watchedName)
    end
end

-- Make Love, Not Warcraft: /hug on a dead enemy player.
local function HugTarget()
    if not UnitExists("target") then return end
    local isPlayer, enemy, dead = UnitIsPlayer("target"), UnitIsEnemy("player", "target"), UnitIsDead("target")
    if secret(isPlayer) or secret(enemy) or secret(dead) then return end
    if isPlayer and enemy and dead and not DB().flags.hugDead then
        DB().flags.hugDead = true
        CheckAll()
    end
end
if DoEmote then
    hooksecurefunc("DoEmote", function(token)
        if type(token) == "string" and token:upper() == "HUG" then HugTarget() end
    end)
end
if C_ChatInfo and C_ChatInfo.PerformEmote then
    hooksecurefunc(C_ChatInfo, "PerformEmote", function(token)
        if type(token) == "string" and token:upper() == "HUG" then HugTarget() end
    end)
end

-- Battlegrounds: the final scoreboard, read once per battle.
local bgSeen = false
local function MyScore()
    local me = UnitName("player")
    local n = GetNumBattlefieldScores and GetNumBattlefieldScores() or 0
    for i = 1, n do
        local name, kb, hk, deaths
        if C_PvP and C_PvP.GetScoreInfo then
            local info = C_PvP.GetScoreInfo(i)
            if info then name, kb, hk, deaths = info.name, info.killingBlows, info.honorableKills, info.deaths end
        else
            name, kb, hk, deaths = GetBattlefieldScore(i)
        end
        if name and not secret(name) and (name == me or name:match("^([^%-]+)") == me) then return kb or 0, hk or 0, deaths or 0 end
    end
end

On("UPDATE_BATTLEFIELD_SCORE", function()
    local winner = GetBattlefieldWinner and GetBattlefieldWinner()
    if winner == nil or bgSeen then return end
    bgSeen = true
    local flags = DB().flags
    local kb, hk, deaths = MyScore()
    if hk and hk >= 30 then flags.grimReaper = true end
    if kb and kb >= 20 and deaths == 0 then flags.wreckingBall = true end
    local team = UnitFactionGroup("player") == "Horde" and 0 or 1
    if winner == team then
        local mins = (GetBattlefieldInstanceRunTime and GetBattlefieldInstanceRunTime() or 0) / 60000
        local zone = GetRealZoneText()
        if mins > 0 then
            if zone == "Warsong Gulch" and mins < 7 then flags.wsgFast = true end
            if zone == "Arathi Basin" and mins <= 6 then flags.abFast = true end
            if zone == "Alterac Valley" and mins <= 6 then flags.avFast = true end
        end
    end
    C_Timer.After(2, function() CheckAll() end)
end)
On("UPDATE_BATTLEFIELD_STATUS", function()
    if GetBattlefieldWinner and GetBattlefieldWinner() ~= nil and RequestBattlefieldScoreData then RequestBattlefieldScoreData() end
end)

for _, e in ipairs({ "UPDATE_FACTION", "PLAYER_PVP_KILLS_CHANGED", "PLAYER_PVP_RANK_CHANGED", "ACHIEVEMENT_EARNED",
    "NEW_MOUNT_ADDED" }) do
    On(e, function() C_Timer.After(0.5, function() CheckAll() end) end)
end

-- Boss fights the client reports (the target may not be the boss at the end).
On("ENCOUNTER_END", function(_, name, _, _, success)
    if success == 1 and name and not secret(name) then NoteBoss(nil, name) end
end)
On("BOSS_KILL", function(_, name)
    if name and not secret(name) then NoteBoss(nil, name) end
end)

-- Fishing: schools, the city diplomat and the rare fish, from the loot window.
local BOBBER = 35591
local SCHOOLSET = {}
for _, id in ipairs(ns.SCHOOLS) do SCHOOLSET[id] = true end
local RARESET = {}
for _, f in ipairs(ns.RARE_FISH) do RARESET[f[2]] = true end

local fishLoot = false -- the open loot window is a catch (Quick Fish logs it)

On("LOOT_OPENED", function()
    if not (IsFishingLoot and IsFishingLoot()) then return end
    fishLoot = true
    local d = DB()
    d.fished = (d.fished or 0) + 1
    local zone = GetRealZoneText and GetRealZoneText() or GetZoneText()
    if zone and not secret(zone) then d.fishedIn[zone] = true end
    for slot = 1, GetNumLootItems() do
        local link = GetLootSlotLink(slot)
        local item = link and tonumber(link:match("item:(%d+)"))
        if item and RARESET[item] then d.rareFish[item] = true end
        if GetLootSourceInfo then
            local guid = GetLootSourceInfo(slot)
            if guid and not secret(guid) then
                local kind, _, _, _, _, id = strsplit("-", guid)
                id = tonumber(id)
                -- Pools are game objects; plain casts loot from the bobber.
                if kind == "GameObject" and id and (SCHOOLSET[id] or id ~= BOBBER) then d.school = true end
            end
        end
    end
    CheckAll()
end)

-- Quick Fish writes its catch log while the loot window is open: once it
-- closes, its totals are summed again for the Quick Fish achievements.
On("LOOT_CLOSED", function()
    if not fishLoot then return end
    fishLoot = false
    if not QF.Loaded() then return end
    QF.at = -10
    C_Timer.After(0.2, function() CheckAll() end)
end)

On("PLAYER_TARGET_CHANGED", WatchTarget)
On("PLAYER_REGEN_ENABLED", function() C_Timer.After(0.2, WatchTarget) end)
local healthWatch = CreateFrame("Frame")
healthWatch:RegisterUnitEvent("UNIT_HEALTH", "target")
healthWatch:SetScript("OnEvent", WatchTarget)
C_Timer.NewTicker(0.5, WatchTarget)

-- Well Read: the title of any book or plaque you open.
local BOOKSET = {}
for _, b in ipairs(ns.BOOKS) do BOOKSET[b:lower()] = b end
On("ITEM_TEXT_BEGIN", function()
    local title = ItemTextGetItem and ItemTextGetItem()
    if not title or secret(title) then return end
    local b = BOOKSET[title:lower()]
    if b and not DB().books[b] then
        DB().books[b] = true
        print(TAG .. " read: " .. b .. " (" .. Count(DB().books) .. "/" .. #ns.BOOKS .. ")")
        CheckAll()
    end
end)

-- Food and drink: a Food & Drink item leaving the bags while you eat or
-- drink. Beverages are told apart by the item's spell or its name.
local DRINK_WORDS = { "water", "juice", "milk", "ale", "wine", "brew", "rum", "grog", "mead", "cider", "tea",
    "coffee", "stout", "beer", "lager", "whiskey", "vodka", "punch", "nectar", "tonic", "beverage", "drink",
    "cocoa", "spirits", "port", "draught", "pilsner", "sherry", "liquor", "moonshine", "bubbly" }
local function IsDrink(id, name)
    local spell = (C_Item and C_Item.GetItemSpell and C_Item.GetItemSpell(id)) or (GetItemSpell and GetItemSpell(id))
    if spell == "Drink" or spell == "Refreshment" then return true end
    if spell == "Food" then return false end
    local lower = (name or ""):lower()
    for _, w in ipairs(DRINK_WORDS) do
        if lower:find(w, 1, true) then return true end
    end
    return false
end

local foodSnap = {}
local function SnapFood()
    local snap = {}
    for bag = 0, 4 do
        for slot = 1, C_Container.GetContainerNumSlots(bag) do
            local info = C_Container.GetContainerItemInfo(bag, slot)
            if info and info.itemID then
                local _, _, _, _, _, c, s = GetItemInfoInstant(info.itemID)
                if c == 0 and s == 5 then
                    snap[info.itemID] = (snap[info.itemID] or 0) + (info.stackCount or 1)
                end
            end
        end
    end
    return snap
end

local busy = false -- vendor, mail, trade or bank open: items leave for other reasons
for _, e in ipairs({ "MERCHANT_SHOW", "MAIL_SHOW", "TRADE_SHOW", "BANKFRAME_OPENED", "AUCTION_HOUSE_SHOW" }) do
    On(e, function() busy = true end)
end
for _, e in ipairs({ "MERCHANT_CLOSED", "MAIL_CLOSED", "TRADE_CLOSED", "BANKFRAME_CLOSED", "AUCTION_HOUSE_CLOSED" }) do
    On(e, function() busy = false; foodSnap = SnapFood() end)
end

local function OnBags()
    local now = SnapFood()
    if not busy and not CursorHasItem() then
        for id, n in pairs(foodSnap) do
            if (now[id] or 0) == n - 1 then
                local name = (C_Item and C_Item.GetItemNameByID and C_Item.GetItemNameByID(id)) or ("item " .. id)
                local d = DB()
                local book = IsDrink(id, name) and d.drinks or d.foods
                if not book[id] then
                    book[id] = name
                    print(TAG .. ((book == d.drinks) and " new drink: " or " new dish: ") .. name
                        .. " (" .. Count(book) .. "/" .. ((book == d.drinks) and 25 or 50) .. ")")
                end
            end
        end
    end
    foodSnap = now
    CheckAll()
end
handlers.BAG_UPDATE_DELAYED = OnBags
C_Timer.After(2, function() foodSnap = SnapFood() end)

-- Going Down?: a fall of about 2.6 seconds (65 yards) that you survive.
local fallStart
local faller = CreateFrame("Frame")
faller:SetScript("OnUpdate", function()
    if IsFalling() then
        fallStart = fallStart or GetTime()
    elseif fallStart then
        local t = GetTime() - fallStart
        fallStart = nil
        if t >= 2.6 then
            C_Timer.After(0.5, function()
                if not UnitIsDeadOrGhost("player") and not DB().fall then
                    DB().fall = true
                    CheckAll()
                end
            end)
        end
    end
end)

-- Greedy / Needy: a 100 on a superior or better item, then winning it.
local function Pattern(fmt)
    if not fmt then return nil end
    fmt = fmt:gsub("([%(%)%.%%%+%-%*%?%[%]%^%$])", "%%%1")
    fmt = fmt:gsub("%%%%s", "(.+)"):gsub("%%%%d", "(%%d+)")
    return "^" .. fmt .. "$"
end
local P_NEED = Pattern(_G.LOOT_ROLL_ROLLED_NEED)
local P_GREED = Pattern(_G.LOOT_ROLL_ROLLED_GREED)
local P_WON = Pattern(_G.LOOT_ROLL_YOU_WON)
local pending = {} -- [link] = "needy" | "greedy"

local function Quality(link)
    local q = link and select(3, ((C_Item and C_Item.GetItemInfo) or GetItemInfo)(link))
    return q or 0
end

On("CHAT_MSG_LOOT", function(msg)
    if not msg or secret(msg) then return end
    local me = UnitName("player")
    for kind, pat in pairs({ needy = P_NEED, greedy = P_GREED }) do
        if pat then
            local roll, link, who = msg:match(pat)
            if roll and tonumber(roll) == 100 and (who == me or who == _G.YOU) and Quality(link) >= 3 then
                pending[link] = kind
            end
        end
    end
    if P_WON then
        local link = msg:match(P_WON)
        if link and pending[link] then
            DB()[pending[link]] = true
            pending[link] = nil
            CheckAll()
        end
    end
end)

-------------------------------------------------------------------------------
--  Window
-------------------------------------------------------------------------------
local WIN_W, WIN_H = 960, 660
-- Categories in a sidebar on the left, as in the WotLK achievement window.
local SIDE_W = 194
local CONTENT_X = 20 + SIDE_W + 14            -- left edge of the cards
local CHILD_W = WIN_W - (CONTENT_X - 20) - 10 -- scroll child (cards sit 20 in)
local CATEGORIES = {
    { key = "summary", label = "Summary" },
    { key = "general", label = "General" },
    { key = "quests", label = "Quests" },
    { key = "exploration", label = "Exploration" },
    { key = "professions", label = "Professions" },
    { key = "dungeons", label = "Dungeons & Raids" },
    { key = "reputation", label = "Reputation" },
    { key = "pvp", label = "PvP" },
    { key = "feats", label = "Feats of Strength" },
    { key = "statistics", label = "Statistics" },
    { key = "settings", label = "Settings" },
}
local ROW_H = 56
local win
local expanded = {}

local function Money(c)
    return (GetCoinTextureString and GetCoinTextureString(c)) or (math.floor(c / 10000) .. "g")
end

local function TotalPoints()
    local done, all = 0, 0
    local n, avail = 0, 0
    for _, a in ipairs(ALL) do
        if Available(a) then
            avail = avail + 1
            all = all + a.pts
            if Earned(a.key) then done, n = done + a.pts, n + 1 end
        end
    end
    return done, all, n, avail
end

-- Search across every tab: achievement name, description, and the entries
-- of its list (critters, pests, books, food and drink seen).
local search = ""

local function ListMatches(a)
    if search == "" then return false end
    if a.list then
        for _, n in ipairs(a.list) do
            if n:lower():find(search, 1, true) then return true end
        end
    elseif a.seen then
        for _, n in pairs(a.seen()) do
            if tostring(n):lower():find(search, 1, true) then return true end
        end
    end
    return false
end

local function Matches(a)
    if search == "" then return true end
    if a.name:lower():find(search, 1, true) or a.desc:lower():find(search, 1, true) then return true end
    return ListMatches(a)
end

-- What the list shows, as in the WotLK achievement window: from a series,
-- the highest earned tier and the next one; the filter keeps all, the
-- completed or the incomplete cards. A search shows every tier that matches.
local function VisibleOf(list)
    local filter = DB().filter or "all"
    local out = {}
    local bySeries = {}
    for _, a in ipairs(list) do
        if a.series then
            local s = bySeries[a.series]
            if not s then
                s = {}
                bySeries[a.series] = s
            end
            if Earned(a.key) then s.top = a elseif not s.next then s.next = a end
        end
    end
    for _, a in ipairs(list) do
        local done = Earned(a.key) and true or false
        local show = Available(a) -- another faction's achievements stay hidden
        if not show then
            show = false
        elseif search ~= "" then
            show = Matches(a)
        elseif a.series then
            local s = bySeries[a.series]
            show = (a == s.top) or (a == s.next)
        else
            show = true
        end
        if show and filter == "completed" then show = done end
        if show and filter == "incomplete" then show = not done end
        if show then out[#out + 1] = a end
    end
    local sort = Settings().sort
    if sort == "name" then
        table.sort(out, function(p, q) return p.name < q.name end)
    elseif sort == "progress" then
        -- Closest to done first; earned ones last.
        local frac = {}
        for _, a in ipairs(out) do
            if Earned(a.key) then
                frac[a] = 2
            else
                local cur, need = a.progress()
                -- Unknown progress sorts after known unfinished rows without
                -- inventing a zero counter for display or completion.
                frac[a] = ProgressKnown(cur, need) and (1 - cur / math.max(1, need)) or 1.5
            end
        end
        table.sort(out, function(p, q)
            if frac[p] ~= frac[q] then return frac[p] < frac[q] end
            return p.name < q.name
        end)
    end
    return out
end

-- Points shown on an earned series tier: the whole series up to it.
local function SeriesPoints(a)
    if not a.series then return a.pts end
    local sum = 0
    for _, t in ipairs(SERIES[a.series]) do
        sum = sum + t.pts
        if t == a then break end
    end
    return sum
end

local function ToggleTrack(a)
    local d = DB()
    if Earned(a.key) then
        print(TAG .. " " .. a.name .. " is already earned.")
        return
    end
    if not d.tracked[a.key] and Count(d.tracked) >= 10 then
        print(TAG .. " you can track up to 10 achievements.")
        return
    end
    d.tracked[a.key] = (not d.tracked[a.key]) or nil
    if RefreshWindow then RefreshWindow() end
    for _, fn in ipairs(CHECK_HOOKS) do pcall(fn) end
end

-- Shift-click: the achievement as text into the open chat box. Readable for
-- everyone; players with the addon see it as a link.
local function InsertLink(a)
    local box = ChatEdit_GetActiveWindow and ChatEdit_GetActiveWindow()
    if not box then return false end
    box:Insert("[ach:" .. a.name .. "]")
    return true
end

local function CardTooltip(owner, a)
    local r, g, b = Accent()
    GameTooltip:SetOwner(owner, "ANCHOR_CURSOR_RIGHT", 16, 0)
    GameTooltip:AddLine(a.name, 1, 1, 1)
    GameTooltip:AddLine(a.desc, nil, nil, nil, true)
    if a.title then
        GameTooltip:AddLine("Reward: title \"" .. a.title:format(UnitName("player")) .. "\"", r, g, b, true)
    end
    if COMPARE.name then
        local t = COMPARE.done and COMPARE.done[a.key]
        GameTooltip:AddLine(COMPARE.name .. (t and ": earned" or ": not earned"), t and r or 0.6, t and g or 0.6, t and b or 0.6)
    end
    if Settings().showIDs then
        GameTooltip:AddLine("key " .. a.key .. (a.id and ("   WotLK ID " .. a.id) or ""), 0.55, 0.55, 0.55)
    end
    GameTooltip:AddLine(" ")
    GameTooltip:AddLine("Right-click: track   Shift-click: link in chat", 0.55, 0.55, 0.55)
    GameTooltip:Show()
end

-- Grows or shrinks one card; everything listed after it slides along.
-- win.placed holds each element's spot as built (cards at their full height).
local function AnimateCard(entry, fromH, toH, done)
    local placed, idx = win.placed or {}, nil
    for i, e in ipairs(placed) do if e == entry then idx = i break end end
    if not idx then if done then done() end return end
    local card = entry.frame
    Kit.Tween("cardExpand", 0.22, function(e)
        local h = Kit.Lerp(fromH, toH, e)
        card:SetHeight(h)
        local shift = h - entry.fullH
        for i = idx + 1, #placed do
            local p = placed[i]
            p.frame:ClearAllPoints()
            p.frame:SetPoint("TOPLEFT", p.x, p.y - shift)
        end
    end, function()
        Kit.RealignBorders()
        if done then done() end
    end)
end

local function BuildList(child, width)
    ROW_H = Settings().compact and 46 or 56
    local placed = {}
    win.placed = placed
    win.barFrac = win.barFrac or {}
    local barFrac = win.barFrac
    local r, g, b = Accent()
    local C = Kit.COLORS
    local W = Kit.W
    local GAP = 6
    local y = 0
    local _, h
    local any = false
    local sections = {}
    -- Summary, Statistics and Settings draw their own page.
    if search == "" and VIEWS[win.cat or ""] then
        child:SetHeight(math.max(1, VIEWS[win.cat](child, width) or 1))
        return
    end
    if search ~= "" then
        for _, catKey in ipairs(CATEGORY_ORDER) do
            for _, sec in ipairs(CATEGORY_SECTIONS[catKey]) do sections[#sections + 1] = sec end
        end
    else
        sections = CATEGORY_SECTIONS[win.cat or "general"]
    end
    for _, sec in ipairs(sections) do
        local visible = VisibleOf(sec.list)
        if #visible > 0 then
            any = true
            local header
            header, h = W:SectionHeader(child, sec.title, y)
            placed[#placed + 1] = { frame = header, x = 20, y = y }
            y = y - h
        end
        for _, a in ipairs(visible) do
            local done = Earned(a.key)
            local cur, need = a.progress()
            local progressKnown = ProgressKnown(cur, need)
            local dyn = a.dynamicList and a.dynamicList()
            if dyn and #dyn < 2 then dyn = nil end
            local hasList = a.list or a.seen or dyn
            -- An earned tier of a series expands to the series strip.
            local hasSeries = a.series and done and SERIES[a.series][1] ~= a
            local expandable = hasList or hasSeries
            local open = expandable and (expanded[a.key] or (hasList and ListMatches(a)))

            -- One card holds the row and, when open, what it expands to.
            local items, listH = nil, 0
            if open and hasList then
                items = {}
                if a.list then
                    for _, n in ipairs(a.list) do items[#items + 1] = { n, a.has(n) } end
                elseif dyn then
                    items = dyn
                else
                    for _, n in pairs(a.seen()) do items[#items + 1] = { n, true } end
                    table.sort(items, function(p, q) return p[1] < q[1] end)
                    if #items == 0 then items[1] = { "Nothing yet: eat or drink something new.", false } end
                end
                listH = math.ceil(#items / 3) * 18 + 20
            elseif open and hasSeries then
                listH = 62
            end
            local card = CreateFrame("Button", nil, child)
            card:SetSize(width - 40, ROW_H + listH)
            card:SetPoint("TOPLEFT", 20, y)
            -- Always clipped: switching clipping on only for the animation
            -- redraws the card and nudges the icon by a pixel.
            card:SetClipsChildren(true)
            local entry = { frame = card, x = 20, y = y, key = a.key, fullH = ROW_H + listH }
            placed[#placed + 1] = entry
            local bg = card:CreateTexture(nil, "BACKGROUND")
            bg:SetAllPoints()
            bg:SetColorTexture(C.card[1], C.card[2], C.card[3], C.card[4])
            local edge = Kit.MakeBorder(card, unpack(C.edge))
            if done then edge:SetColor(r, g, b, 0.35) end
            -- Hover: lighter card and a brighter edge.
            card:SetScript("OnEnter", function(self)
                bg:SetColorTexture(C.cardHover[1], C.cardHover[2], C.cardHover[3], C.cardHover[4])
                edge:SetColor(r, g, b, done and 0.7 or 0.4)
                CardTooltip(self, a)
            end)
            card:SetScript("OnLeave", function()
                bg:SetColorTexture(C.card[1], C.card[2], C.card[3], C.card[4])
                if done then edge:SetColor(r, g, b, 0.35) else edge:SetColor(unpack(C.edge)) end
                GameTooltip:Hide()
            end)
            card:RegisterForClicks("LeftButtonUp", "RightButtonUp")
            card:SetScript("OnClick", function(_, button)
                if button == "RightButton" then ToggleTrack(a) return end
                if IsShiftKeyDown() and InsertLink(a) then return end
                if expandable then
                    if expanded[a.key] and open then
                        -- Fold up, then rebuild without the list.
                        AnimateCard(entry, entry.fullH, ROW_H, function()
                            expanded[a.key] = nil
                            RefreshWindow()
                        end)
                    else
                        expanded[a.key] = true
                        win.animOpen = a.key
                        RefreshWindow()
                    end
                end
            end)
            if DB().tracked[a.key] then
                local tr = Kit.MakeFont(card, 9, nil, r, g, b, 1)
                tr:SetPoint("TOPRIGHT", -12, -5)
                tr:SetText("TRACKED")
            end
            if COMPARE.name then
                local t = COMPARE.done and COMPARE.done[a.key]
                local cmp = Kit.MakeFont(card, 10, nil, C.dim[1], C.dim[2], C.dim[3], 1)
                cmp:SetPoint("BOTTOMRIGHT", -12, 5)
                cmp:SetText(COMPARE.name .. (t and ": earned" or ": not yet"))
                if t then cmp:SetTextColor(r, g, b, 1) end
            end

            local icon = card:CreateTexture(nil, "ARTWORK")
            icon:SetSize(34, 34)
            icon:SetPoint("TOPLEFT", 12, -(ROW_H - 34) / 2)
            icon:SetTexture((a.icon or ns.ICONS[a.id] or 236376))
            icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
            icon:SetDesaturated(not done)
            icon:SetAlpha(done and 1 or 0.55)

            local name = Kit.MakeFont(card, 14, nil, C.text[1], C.text[2], C.text[3], done and 1 or 0.8)
            name:SetPoint("TOPLEFT", icon, "TOPRIGHT", 12, 0)
            name:SetText(a.name)
            if done then name:SetTextColor(r, g, b, 1) end
            -- Description: a size smaller, and kept clear of the progress on the right.
            local desc = Kit.MakeFont(card, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            desc:SetPoint("TOPLEFT", name, "BOTTOMLEFT", 0, -4)
            desc:SetPoint("RIGHT", card, "RIGHT", -230, 0)
            desc:SetJustifyH("LEFT")
            desc:SetWordWrap(false)
            desc:SetText(a.desc)

            -- Points badge: an earned series tier shows the series total.
            local badge = CreateFrame("Frame", nil, card)
            badge:SetSize(30, 20)
            badge:SetPoint("TOPRIGHT", -12, -(ROW_H - 20) / 2)
            local bbg = badge:CreateTexture(nil, "BACKGROUND")
            bbg:SetAllPoints()
            bbg:SetColorTexture(r, g, b, done and 0.85 or 0.12)
            local pts = Kit.MakeFont(badge, 12, nil, 1, 1, 1, 1)
            pts:SetPoint("CENTER")
            pts:SetText(tostring(done and SeriesPoints(a) or a.pts))
            if done then pts:SetTextColor(0.03, 0.07, 0.09) else pts:SetTextColor(r, g, b, 1) end

            local right = Kit.MakeFont(card, 12, nil, C.text[1], C.text[2], C.text[3], 0.85)
            right:SetPoint("RIGHT", badge, "LEFT", -16, (not done and progressKnown and need > 1) and 5 or 0)
            if done then
                right:SetText(date("%d.%m.%Y", done))
                right:SetTextColor(r, g, b, 1)
            elseif not progressKnown then
                right:SetText("Unavailable")
            elseif a.money then
                right:SetText(Money(cur) .. " / " .. Money(need))
            else
                right:SetText(cur .. " / " .. need)
            end
            if not done and progressKnown and need > 1 then
                local track = card:CreateTexture(nil, "ARTWORK")
                track:SetColorTexture(1, 1, 1, 0.1)
                track:SetSize(150, 2)
                track:SetPoint("TOPRIGHT", right, "BOTTOMRIGHT", 0, -6)
                local fill = card:CreateTexture(nil, "OVERLAY")
                fill:SetColorTexture(r, g, b, 1)
                local frac = math.min(1, cur / need)
                local prev = barFrac[a.key]
                if win.fillFromZero then prev = 0 end
                barFrac[a.key] = frac
                fill:SetSize(math.max(1, 150 * (prev or frac)), 2)
                if prev and prev ~= frac then
                    Kit.Tween("bar" .. a.key, 0.6, function(e)
                        fill:SetWidth(math.max(1, 150 * Kit.Lerp(prev, frac, e)))
                    end)
                end
                fill:SetPoint("LEFT", track, "LEFT")
            end

            if expandable then
                -- Chevron after the name: right when closed, down when open.
                local chev = CreateFrame("Frame", nil, card)
                chev:SetSize(10, 10)
                chev:SetPoint("LEFT", name, "RIGHT", 8, 0)
                for _, side in ipairs({ -1, 1 }) do
                    local bar = chev:CreateTexture(nil, "OVERLAY")
                    bar:SetSize(6, 1.5)
                    bar:SetColorTexture(r, g, b, 1)
                    if open then
                        bar:SetPoint("CENTER", chev, "CENTER", side * 2, 0)
                        bar:SetRotation(side * math.pi / 4)
                    else
                        bar:SetPoint("CENTER", chev, "CENTER", 0, side * 2)
                        bar:SetRotation(-side * math.pi / 4)
                    end
                end
            end

            if open then
                local sep = card:CreateTexture(nil, "ARTWORK")
                sep:SetHeight(1)
                sep:SetPoint("TOPLEFT", 12, -ROW_H)
                sep:SetPoint("TOPRIGHT", -12, -ROW_H)
                sep:SetColorTexture(1, 1, 1, 0.08)
            end

            if open and hasSeries then
                -- The series up to this tier: icon, points under it, date in the tooltip.
                local k = 0
                for _, t in ipairs(SERIES[a.series]) do
                    k = k + 1
                    local tdone = Earned(t.key)
                    local mini = CreateFrame("Frame", nil, card)
                    mini:SetSize(30, 30)
                    mini:SetPoint("TOPLEFT", 58 + (k - 1) * 40, -ROW_H - 10)
                    local tex = mini:CreateTexture(nil, "ARTWORK")
                    tex:SetAllPoints()
                    tex:SetTexture(t.icon or ns.ICONS[t.id] or 236376)
                    tex:SetTexCoord(0.08, 0.92, 0.08, 0.92)
                    Kit.MakeBorder(mini, r, g, b, 0.6)
                    local mp = Kit.MakeFont(card, 11, nil, r, g, b, 1)
                    mp:SetPoint("TOP", mini, "BOTTOM", 0, -3)
                    mp:SetText(tostring(t.pts))
                    mini:EnableMouse(true)
                    mini:SetScript("OnEnter", function(self)
                        GameTooltip:SetOwner(self, "ANCHOR_TOP")
                        GameTooltip:AddLine(t.name, 1, 1, 1)
                        GameTooltip:AddLine(t.desc, nil, nil, nil, true)
                        if tdone then GameTooltip:AddLine("Earned " .. date("%d.%m.%Y", tdone), r, g, b) end
                        GameTooltip:Show()
                    end)
                    mini:SetScript("OnLeave", function() GameTooltip:Hide() end)
                    if t == a then break end
                end
            elseif open and hasList then
                local colW = math.floor((width - 80) / 3)
                for idx, it in ipairs(items) do
                    local col = (idx - 1) % 3
                    local line = math.floor((idx - 1) / 3)
                    local mark = card:CreateTexture(nil, "OVERLAY")
                    mark:SetSize(6, 6)
                    mark:SetPoint("TOPLEFT", 22 + col * colW, -ROW_H - 15 - line * 18)
                    if it[2] then mark:SetColorTexture(r, g, b, 1) else mark:SetColorTexture(1, 1, 1, 0.15) end
                    local fs = Kit.MakeFont(card, 12, nil, C.text[1], C.text[2], C.text[3], it[2] and 1 or 0.45)
                    fs:SetPoint("LEFT", mark, "RIGHT", 8, 0)
                    fs:SetWidth(colW - 26)
                    fs:SetJustifyH("LEFT")
                    fs:SetWordWrap(false)
                    fs:SetText(it[1])
                end
            end
            y = y - ROW_H - listH - GAP
        end
        if #visible > 0 then y = y - 6 end
    end
    if not any then
        local e = Kit.MakeFont(child, 13, nil, C.dim[1], C.dim[2], C.dim[3], 1)
        e:SetPoint("TOPLEFT", 30, -10)
        e:SetText(search ~= "" and "No achievement matches the search." or "Nothing here with this filter.")
        y = -40
    end
    child:SetHeight(-y)
    win.fillFromZero = nil
    -- A card just opened: grow it from the collapsed height.
    if win.animOpen then
        local key = win.animOpen
        win.animOpen = nil
        for _, e in ipairs(placed) do
            if e.key == key and e.fullH > ROW_H then AnimateCard(e, ROW_H, e.fullH) break end
        end
    end
end

RefreshWindow = function()
    if not (win and win:IsShown()) then return end
    if win.scroll then win.scroll:Hide(); win.scroll:SetParent(nil) end
    local done, all, n, avail = TotalPoints()
    local function Summary(pts)
        local text = ("%d / %d earned   |   %d / %d points"):format(n, avail, pts, all)
        if COMPARE.name then text = text .. "   |   comparing with " .. COMPARE.name end
        win.summary:SetText(text)
    end
    local frac = all > 0 and done / all or 0
    local barW = WIN_W - 30 - CONTENT_X
    local prevPts, prevFrac = win.shownPoints, win.shownFrac
    win.shownPoints, win.shownFrac = done, frac
    if win.fillFromZero and frac > 0 then
        Summary(done)
        Kit.Tween("summaryBar", 0.7, function(e) win.progFill:SetWidth(math.max(1, barW * frac * e)) end)
    elseif prevPts and prevPts ~= done then
        -- New points: the number counts up and the bar slides to it.
        Kit.Tween("summaryPoints", 0.9, function(e)
            Summary(math.floor(Kit.Lerp(prevPts, done, e) + 0.5))
            win.progFill:SetWidth(math.max(1, barW * Kit.Lerp(prevFrac, frac, e)))
        end)
    else
        Summary(done)
        win.progFill:SetWidth(math.max(1, barW * frac))
    end
    for _, t in ipairs(win.tabs) do
        if CATEGORY_SECTIONS[t.key] then
            local en, ea = 0, 0
            for _, sec in ipairs(CATEGORY_SECTIONS[t.key]) do
                for _, a in ipairs(sec.list) do
                    if Available(a) then
                        ea = ea + 1
                        if Earned(a.key) then en = en + 1 end
                    end
                end
            end
            t.count:SetText(en .. "/" .. ea)
        end
    end

    local scroll = CreateFrame("ScrollFrame", nil, win)
    scroll:SetPoint("TOPLEFT", CONTENT_X - 20, -104)
    scroll:SetPoint("BOTTOMRIGHT", -10, 14)
    local child = CreateFrame("Frame", nil, scroll)
    child:SetWidth(CHILD_W)
    child:SetHeight(1)
    scroll:SetScrollChild(child)
    scroll:EnableMouseWheel(true)
    scroll:SetScript("OnMouseWheel", function(self, delta)
        local max = math.max(0, child:GetHeight() - self:GetHeight())
        self:SetVerticalScroll(math.min(max, math.max(0, self:GetVerticalScroll() - delta * 60)))
    end)
    win.scroll = scroll
    BuildList(child, CHILD_W)
    if win.scrollPos then scroll:SetVerticalScroll(win.scrollPos) end
    scroll:SetScript("OnVerticalScroll", function(self, offset)
        win.scrollPos = offset
        Kit.RealignBorders()
    end)
end

local function Open()
    if not win then
        local r, g, b = Accent()
        win = CreateFrame("Frame", "ForeverAchievementsWindow", UIParent)
        win:SetSize(WIN_W, WIN_H)
        win:SetPoint("CENTER")
        win:SetScale(Settings().scale or 1)
        win:SetFrameStrata("DIALOG")
        win:SetClampedToScreen(true)
        win:EnableMouse(true)
        win:SetMovable(true)
        win:RegisterForDrag("LeftButton")
        win:SetScript("OnDragStart", win.StartMoving)
        win:SetScript("OnDragStop", function(self)
            self:StopMovingOrSizing()
            Kit.RealignBorders()
        end)
        tinsert(UISpecialFrames, "ForeverAchievementsWindow")
        Kit.Chrome(win, "Forever Achievements", "", function() win:Hide() end)

        -- Category sidebar: one row per category with its earned count;
        -- Statistics and Settings sit apart, pinned to the bottom.
        win.cat = DB().tab or "summary"
        if not CATEGORY_SECTIONS[win.cat] and not VIEWS[win.cat] and win.cat ~= "statistics" and win.cat ~= "settings" then
            win.cat = "summary"
        end
        win.tabs = {}
        local C = Kit.COLORS
        local side = CreateFrame("Frame", nil, win)
        side:SetPoint("TOPLEFT", 20, Kit.TAB_Y)
        side:SetPoint("BOTTOMLEFT", 20, 14)
        side:SetWidth(SIDE_W)
        local sbg = side:CreateTexture(nil, "BACKGROUND")
        sbg:SetAllPoints()
        sbg:SetColorTexture(C.card[1], C.card[2], C.card[3], 0.55)
        Kit.MakeBorder(side, unpack(C.edge))
        local BOTTOM = { statistics = 38, settings = 8 }
        local rule = side:CreateTexture(nil, "ARTWORK")
        rule:SetHeight(1)
        rule:SetPoint("BOTTOMLEFT", 12, 72)
        rule:SetPoint("BOTTOMRIGHT", -12, 72)
        rule:SetColorTexture(1, 1, 1, 0.08)
        local sy = -8
        for _, cat in ipairs(CATEGORIES) do
            local item = CreateFrame("Button", nil, side)
            item:SetSize(SIDE_W - 12, 28)
            if BOTTOM[cat.key] then
                item:SetPoint("BOTTOMLEFT", 6, BOTTOM[cat.key])
            else
                item:SetPoint("TOPLEFT", 6, sy)
                sy = sy - 30
            end
            local ibg = item:CreateTexture(nil, "BACKGROUND")
            ibg:SetAllPoints()
            local bar = item:CreateTexture(nil, "ARTWORK")
            bar:SetSize(3, 16)
            bar:SetPoint("LEFT", 0, 0)
            bar:SetColorTexture(r, g, b, 1)
            local label = Kit.MakeFont(item, 13, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            label:SetPoint("LEFT", 12, 0)
            label:SetText(cat.label)
            item.count = Kit.MakeFont(item, 11, nil, C.dim[1], C.dim[2], C.dim[3], 0.8)
            item.count:SetPoint("RIGHT", -8, 0)
            item.key = cat.key
            local active = false
            function item:SetActive(on)
                active = on
                bar:SetShown(on)
                if on then
                    ibg:SetColorTexture(r, g, b, 0.16)
                    label:SetTextColor(C.text[1], C.text[2], C.text[3], 1)
                    self.count:SetTextColor(r, g, b, 1)
                else
                    ibg:SetColorTexture(1, 1, 1, 0)
                    label:SetTextColor(C.dim[1], C.dim[2], C.dim[3], 1)
                    self.count:SetTextColor(C.dim[1], C.dim[2], C.dim[3], 0.8)
                end
            end
            item:SetScript("OnEnter", function() if not active then ibg:SetColorTexture(1, 1, 1, 0.05) end end)
            item:SetScript("OnLeave", function() if not active then ibg:SetColorTexture(1, 1, 1, 0) end end)
            item:SetActive(cat.key == win.cat)
            item:SetScript("OnClick", function()
                win.cat = cat.key
                DB().tab = cat.key
                win.scrollPos = 0
                win.fillFromZero = true
                for _, t in ipairs(win.tabs) do t:SetActive(t.key == cat.key) end
                RefreshWindow()
            end)
            win.tabs[#win.tabs + 1] = item
        end

        -- Overall progress, the search and the filter on the row under the tabs.
        win.summary = Kit.MakeFont(win, 12, nil, Kit.COLORS.dim[1], Kit.COLORS.dim[2], Kit.COLORS.dim[3], 1)
        local filters = { all = "All", completed = "Completed", incomplete = "Incomplete" }
        local filterDD = Kit.Dropdown(win, 130, filters, { "all", "completed", "incomplete" },
            function() return DB().filter or "all" end,
            function(v) DB().filter = v; win.scrollPos = 0; RefreshWindow() end)

        -- Search box left of the filter.
        local C = Kit.COLORS
        local box = CreateFrame("EditBox", nil, win)
        box:SetSize(200, 26)
        box:SetPoint("RIGHT", filterDD, "LEFT", -8, 0)
        box:SetAutoFocus(false)
        box:SetFont(Kit.FONT, 12, "")
        box:SetTextColor(C.text[1], C.text[2], C.text[3])
        box:SetTextInsets(10, 24, 0, 0)
        box:SetMaxLetters(40)
        local sbg = box:CreateTexture(nil, "BACKGROUND")
        sbg:SetAllPoints()
        sbg:SetColorTexture(0, 0, 0, 0.35)
        local sborder = Kit.MakeBorder(box, 1, 1, 1, 0.2)
        local hint = Kit.MakeFont(box, 12, nil, C.dim[1], C.dim[2], C.dim[3], 0.7)
        hint:SetPoint("LEFT", 10, 0)
        hint:SetText("Search")
        local clear = CreateFrame("Button", nil, box)
        clear:SetSize(18, 18)
        clear:SetPoint("RIGHT", -4, 0)
        for _, angle in ipairs({ math.pi / 4, -math.pi / 4 }) do
            local bar = clear:CreateTexture(nil, "OVERLAY")
            bar:SetSize(9, 1.5)
            bar:SetPoint("CENTER")
            bar:SetColorTexture(C.dim[1], C.dim[2], C.dim[3], 1)
            bar:SetRotation(angle)
        end
        clear:SetScript("OnClick", function() box:SetText(""); box:ClearFocus() end)
        clear:Hide()
        local pending
        box:SetScript("OnTextChanged", function(self)
            local text = self:GetText() or ""
            hint:SetShown(text == "")
            clear:SetShown(text ~= "")
            local token = {}
            pending = token
            C_Timer.After(0.2, function()
                if pending ~= token then return end
                search = text:lower():match("^%s*(.-)%s*$")
                win.scrollPos = 0
                RefreshWindow()
            end)
        end)
        box:SetScript("OnEditFocusGained", function() sborder:SetColor(r, g, b, 0.8) end)
        box:SetScript("OnEditFocusLost", function() sborder:SetColor(1, 1, 1, 0.2) end)
        box:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
        win.searchBox = box
        box:SetScript("OnEnterPressed", function(self) self:ClearFocus() end)
        local track = win:CreateTexture(nil, "ARTWORK")
        track:SetColorTexture(1, 1, 1, 0.08)
        track:SetHeight(3)
        win.progFill = win:CreateTexture(nil, "OVERLAY")
        win.progFill:SetColorTexture(r, g, b, 1)
        win.progFill:SetHeight(3)
        win.progFill:SetPoint("LEFT", track, "LEFT")

        -- Summary, search and filter in line with the top of the sidebar,
        -- the progress bar under them.
        local y = Kit.TAB_Y
        filterDD:SetPoint("TOPRIGHT", -30, y)
        win.summary:SetPoint("LEFT", win, "TOPLEFT", CONTENT_X, y - 13)
        track:SetPoint("TOPLEFT", CONTENT_X, y - 36)
        track:SetPoint("TOPRIGHT", -30, y - 36)
    end
    if not win:IsShown() then
        win.fillFromZero = true
        win:SetAlpha(0)
        win:Show()
        Kit.Tween("windowFade", 0.18, function(e) win:SetAlpha(e) end)
    end
    RefreshWindow()
end

SLASH_FOREVERACHIEVEMENTS1 = "/fach"
SLASH_FOREVERACHIEVEMENTS2 = "/qa" -- short alias, same commands
SLASH_FOREVERACHIEVEMENTS3 = "/fa" -- also used by the experimental native Legacy UI
SlashCmdList.FOREVERACHIEVEMENTS = function(input)
    local msg, rest = (input or ""):match("^%s*(%S*)%s*(.-)%s*$")
    msg = (msg or ""):lower()
    if SLASH[msg] then
        SLASH[msg](rest or "")
        return
    end
    if msg == "help" or msg == "?" then
        local r, g, b = Kit.Accent()
        local accent = ("|cff%02x%02x%02x"):format(math.floor(r * 255), math.floor(g * 255), math.floor(b * 255))
        print(TAG .. " commands:")
        for _, line in ipairs({
            { "/fach", "open the window" },
            { "/fach compare Firstname Lastname", "compare with a player who runs the addon (or right-click them)" },
            { "/fach compare off", "stop comparing" },
            { "/fach welcome", "show the welcome screen again" },
            { "/fa legacyui on|off", "enable or disable the unified Wrath Legacy interface" },
            { "/fa legacyui size compact|standard|large", "choose a saved window size" },
            { "/fa legacyui reset", "reset the Legacy window position without changing progress" },
            { "/fach debug", "debug messages for critters, pests and kills" },
            { "/fach reset", "clear this character's progress" },
            { "/fach help", "this list" },
            { "/qa", "short for /fach (works with every command above)" },
        }) do
            print("  " .. accent .. line[1] .. "|r - " .. line[2])
        end
        return
    end
    if msg == "debug" then
        debugOn = not debugOn
        print(TAG .. " debug " .. (debugOn and "ON: /love a critter or kill a targeted pest" or "OFF"))
        return
    end
    if msg == "reset" then
        ForeverAchievementsCharDB = {}
        print(TAG .. " progress for this character cleared.")
        CheckAll(true)
    else
        Open()
    end
end

-------------------------------------------------------------------------------
--  What the other files (social, tooltips, tracker, pages) build on
-------------------------------------------------------------------------------
local ZONE_ACH = {} -- [zone name] = its exploration achievement
for _, list in ipairs({ ekZones, kalZones, otherZones }) do
    for _, a in ipairs(list) do
        local zone = a.name:gsub("^Explore ", "")
        ZONE_ACH[zone] = a
        -- The game calls "Tanaris Desert" just "Tanaris".
        ZONE_ACH[(zone:gsub(" Desert$", ""))] = a
    end
end
local BY_KEY = {}
for _, a in ipairs(ALL) do BY_KEY[a.key] = a end

ns.FA = {
    TAG = TAG, Kit = Kit, secret = secret, Count = Count, ProgressKnown = ProgressKnown,
    IsDebug = function() return debugOn end, -- /fach debug, for messages in the other files
    DB = DB, Account = AccountDB, Settings = Settings,
    ALL = ALL, BY_KEY = BY_KEY, SERIES = SERIES, Available = Available, Earned = Earned,
    CATEGORIES = CATEGORIES, CATEGORY_SECTIONS = CATEGORY_SECTIONS, CATEGORY_ORDER = CATEGORY_ORDER,
    EARN_HOOKS = EARN_HOOKS, CHECK_HOOKS = CHECK_HOOKS, VIEWS = VIEWS, SLASH = SLASH, COMPARE = COMPARE, LINK = LINK,
    CheckAll = CheckAll, TotalPoints = TotalPoints, SeriesPoints = SeriesPoints, ToggleTrack = ToggleTrack,
    Money = Money, StatText = StatText, NpcID = NpcID, IsDrink = IsDrink,
    -- Read-only seams for a later compatible quest-database adapter. No new
    -- Questie integration or imported quest catalog is introduced here.
    QuestTracking = { CompletedIDs = CompletedIDs, Count = QuestCount,
        LoremasterCounts = function() return loreCount.ek, loreCount.kal end },
    CRITTERS = CRITTERS, PESTS = PESTS, PEST_NAMES = PEST_NAMES, BOSS_IDS = BOSS_IDS, BOSS_BY_NAME = BOSS_BY_NAME,
    BOSS_ACH = BOSS_ACH, BOOKSET = BOOKSET, ZONE_ACH = ZONE_ACH,
    Open = Open,
    Refresh = function() if RefreshWindow then RefreshWindow() end end,
    -- Opens the window with the search box filled in.
    OpenSearch = function(text)
        Open()
        if win.searchBox then win.searchBox:SetText(text or "") end
    end,
    -- Builds the window again (a new theme): reopened on the same tab.
    RebuildWindow = function()
        if not win then return end
        local shown = win:IsShown()
        win:Hide()
        win = nil
        if shown then Open() end
    end,
    SetScale = function(v)
        if win then win:SetScale(v) end
        Kit.RealignBorders()
    end,
    -- A sample toast, for the settings page.
    PreviewToast = function()
        queue[#queue + 1] = { name = "Forever Achievements", icon = 132347, pts = 10 }
        if not showing then ShowNextToast() end
    end,
    IsShown = function() return win and win:IsShown() end,
    Hide = function() if win then win:Hide() end end,
    -- The toast is built again with the next achievement.
    ResetToast = function() if not showing then toast = nil end end,
    -- Switches the window to a tab.
    ShowTab = function(key)
        Open()
        win.cat = key
        DB().tab = key
        for _, t in ipairs(win.tabs) do t:SetActive(t.key == key) end
        RefreshWindow()
    end,
}
