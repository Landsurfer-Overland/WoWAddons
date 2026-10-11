-- Read-only subject navigation for statistics. These are observed values, not
-- achievement progress, and never combine character and account histories.
local _, ns = ...
local LAR, R = ns.LAR, ns.LegacyReadOnly
local A = {}
ns.LegacyStatistics, ns.StatisticsAdapter = A, A

local ROOTS = {
    { "character", "Character" }, { "combat", "Combat" },
    { "quests", "Quests" }, { "exploration", "Exploration" },
    { "professions", "Professions" }, { "dungeons", "Dungeons & Raids" },
    { "pvp", "PvP" }, { "misc", "Miscellaneous" },
}
local CHILDREN = {
    character = { { "general", "General" }, { "progression", "Progression" }, { "consumables", "Consumables" } },
    combat = { { "damage", "Damage" }, { "healing", "Healing" }, { "kills", "Kills" }, { "deaths", "Deaths" } },
    professions = { { "fishing", "Fishing" }, { "cooking", "Cooking" }, { "firstaid", "First Aid" } },
}

-- Authored IDs disambiguate mixed sections without guessing from labels.
local SUBJECT_BY_ID = {
    [193] = "combat/damage", [527] = "combat/damage", [197] = "combat/damage", [528] = "combat/damage",
    [189] = "combat/healing", [829] = "combat/healing", [198] = "combat/healing", [830] = "combat/healing",
    [1519] = "professions/fishing", [1518] = "professions/fishing", [1456] = "professions/fishing",
    [1524] = "professions/cooking", [1745] = "professions/cooking",
    [281] = "professions/firstaid", [1748] = "professions/firstaid",
    [1202] = "character/progression", -- weapon skills are not a crafting profession
}
local SECTION_SUBJECT = {
    ["CHARACTER"] = "character/general", ["CHARACTER / CONSUMABLES"] = "character/consumables",
    ["CHARACTER / GEAR"] = "character/progression", ["CHARACTER / REPUTATION"] = "character/progression",
    ["CHARACTER / WEALTH"] = "character/general", ["COMBAT"] = "combat",
    ["DEATHS"] = "combat/deaths", ["DEATHS / BATTLEGROUNDS"] = "combat/deaths",
    ["DEATHS / DUNGEONS AND RAIDS"] = "combat/deaths", ["DEATHS / RESURRECTION"] = "combat/deaths",
    ["DEATHS / WORLD"] = "combat/deaths", ["DUNGEONS & RAIDS"] = "dungeons",
    ["DUNGEONS & RAIDS / BOSS KILLS"] = "dungeons", ["KILLS"] = "combat/kills",
    ["KILLS / CREATURES"] = "combat/kills", ["KILLS / HONORABLE KILLS"] = "pvp",
    ["KILLS / KILLING BLOWS"] = "pvp", ["PLAYER VS. PLAYER"] = "pvp",
    ["PLAYER VS. PLAYER / BATTLEGROUNDS"] = "pvp", ["PLAYER VS. PLAYER / WORLD"] = "pvp",
    ["QUESTS"] = "quests", ["SKILLS"] = "professions", ["SKILLS / PROFESSIONS"] = "professions",
    ["SKILLS / SECONDARY SKILLS"] = "professions", ["SOCIAL"] = "misc", ["TRAVEL"] = "misc",
}

-- Keep historical ns.STATS definitions intact. Daily quests and Dalaran
-- Cooking Awards have no supported Forever counterpart and are not presented.
local OMITTED = { [97] = "Daily quests unavailable in Forever", [1525] = "Daily quests unavailable in Forever",
    [1526] = "Daily quests unavailable in Forever", [1976] = "Dalaran Cooking Awards unavailable in Forever" }
local UNAVAILABLE = { ["--"] = true, ["-"] = true, ["?"] = true, ["unknown"] = true,
    ["unavailable"] = true, ["n/a"] = true, ["not available"] = true, ["nil"] = true }

local function textValue(value)
    local number = R.Number(value)
    if number then return number >= 0 and tostring(number) or nil end
    local text = R.Text(value)
    if not text then return nil end
    local plain = text:gsub("|c%x%x%x%x%x%x%x%x", ""):gsub("|r", ""):match("^%s*(.-)%s*$")
    if plain == "" or UNAVAILABLE[plain:lower()] then return nil end
    return text -- preserve native grouping, currency textures and named values
end
local function nativeValue(id)
    local result = R.Call(GetStatistic, id)
    return result and textValue(result[1])
end
local function countValue(data, field)
    local collection = R.Field(data, field)
    if type(collection) ~= "table" then return nil end
    local result = R.Call(LAR.Count, collection)
    local n = result and R.Number(result[1])
    return n and n >= 0 and n == math.floor(n) and tostring(n) or nil
end
local function numberValue(data, field)
    local n = R.Number(R.Field(data, field))
    return n and n >= 0 and n == math.floor(n) and tostring(n) or nil
end
local function exploredValue(data)
    local zones = R.Field(data, "explored")
    if type(zones) ~= "table" then return nil end
    -- Older character saves used the numeric achievement ID as the zone key.
    -- Both aliases can coexist; the same stored subzone counts only once.
    local aliases, unique, n = {}, {}, 0
    for _, zone in ipairs(ns.EXPLORE or {}) do
        local id, key = R.ID(zone.id), R.Text(zone.key)
        if id then
            key = key or ("explore" .. id)
            aliases[id], aliases[key] = key, key
        end
    end
    for zone, areas in pairs(zones) do
        if not R.Safe(zone) then return nil end
        if not R.Safe(areas) or type(areas) ~= "table" then return nil end
        local identity = aliases[zone] or (type(zone) .. ":" .. tostring(zone))
        unique[identity] = unique[identity] or {}
        for area, seen in pairs(areas) do
            if not R.Safe(area) or not R.Safe(seen) then return nil end
            if seen == true and not unique[identity][area] then
                unique[identity][area], n = true, n + 1
            end
        end
    end
    return tostring(n)
end
local TRACKED = {
    { "critters", "Critters loved", "misc" }, { "pests", "Pests slain", "combat/kills" },
    { "books", "Books read", "misc" }, { "foods", "Different dishes eaten", "character/consumables" },
    { "drinks", "Different drinks", "character/consumables" }, { "rares", "Rare enemies slain", "combat/kills" },
    { "bosses", "Bosses seen slain", "dungeons" },
    { "fished", "Fishing catches seen", "professions/fishing", numberValue },
    { "fishedIn", "Fishing locations recorded", "professions/fishing" },
    { "rareFish", "Rare fish recorded", "professions/fishing" },
    { "explored", "Exploration areas recorded", "exploration", exploredValue },
}

function A.Catalog()
    local model = { roots = {}, categories = {}, byCategory = {}, rows = {}, byKey = {}, omitted = {} }
    model.records = model.rows
    local function category(subject, name, parent)
        local key = "stats:" .. subject
        local cat = { key = key, name = name, parent = parent, children = {}, rows = {} }
        model.categories[#model.categories + 1], model.byCategory[key] = cat, cat
        if parent then
            local p = model.byCategory[parent]
            p.children[#p.children + 1] = cat
        else model.roots[#model.roots + 1] = cat end
        return cat
    end
    category("summary", "Summary")
    for _, entry in ipairs(ROOTS) do
        local parent = category(entry[1], entry[2])
        for _, child in ipairs(CHILDREN[entry[1]] or {}) do category(entry[1] .. "/" .. child[1], child[2], parent.key) end
    end
    local function add(key, name, value, subject, source, section, id)
        if model.byKey[key] then return end
        local cat = model.byCategory["stats:" .. subject] or model.byCategory["stats:misc"]
        local row = { key = key, name = name, value = value or "Unavailable", available = value ~= nil,
            category = cat.key, source = source, scope = "Character", section = section, id = id }
        cat.rows[#cat.rows + 1], model.rows[#model.rows + 1], model.byKey[key] = row, row, row
    end
    -- Normal runtime has a character SavedVariables table. Read it directly so
    -- this view never adds defaults. The existing accessor is a guarded fallback
    -- for hosts that expose the state only through the addon namespace.
    local data = R.Field(_G, "LegacyAchievementsReforgedCharDB")
    if data == nil then
        local result = R.Call(LAR.DB)
        data = result and result[1]
    end
    for _, stat in ipairs(TRACKED) do
        add("statistic:tracked:" .. stat[1], stat[2], (stat[4] or countValue)(data, stat[1]), stat[3],
            "custom_tracking", "TRACKED BY LEGACY ACHIEVEMENTS REFORGED")
    end
    for _, section in ipairs(ns.STATS or {}) do
        local title = R.Text(section.title) or "MISCELLANEOUS"
        for _, stat in ipairs(section.list or {}) do
            local id, name = R.ID(stat[1]), R.Text(stat[2])
            if id and name then
                local omit = OMITTED[id]
                -- Additional imported daily definitions are omitted by explicit
                -- terminology, without confusing average quests per day with
                -- a daily quest feature.
                if not omit and name:lower():find("daily quest", 1, true) then omit = "Daily quests unavailable in Forever" end
                if omit then model.omitted[id] = omit
                elseif not model.byKey["statistic:native:" .. id] then
                    add("statistic:native:" .. id, name, nativeValue(id), SUBJECT_BY_ID[id] or SECTION_SUBJECT[title] or "misc",
                        "native_statistic", title, id)
                end
            end
        end
    end
    local function prune(cat)
        for i = #cat.children, 1, -1 do
            local child = cat.children[i]
            if not prune(child) then model.byCategory[child.key] = nil; table.remove(cat.children, i) end
        end
        return #cat.rows > 0 or #cat.children > 0 or cat.key == "stats:summary"
    end
    for i = #model.roots, 1, -1 do
        local cat = model.roots[i]
        if not prune(cat) then model.byCategory[cat.key] = nil; table.remove(model.roots, i) end
    end
    local populated = {}
    for _, cat in ipairs(model.categories) do if model.byCategory[cat.key] then populated[#populated + 1] = cat end end
    model.categories = populated
    return model
end

function A.Rows(model, key)
    if not model then return {} end
    key = key or "stats:summary"
    if key == "summary" or key == "stats:summary" then return model.rows end
    local out, seen, visited = {}, {}, {}
    local function visit(cat)
        if not cat or visited[cat.key] then return end
        visited[cat.key] = true
        for _, row in ipairs(cat.rows or {}) do
            if not seen[row.key] then seen[row.key] = true; out[#out + 1] = row end
        end
        for _, child in ipairs(cat.children or {}) do visit(child) end
    end
    visit(model.byCategory[key])
    return out
end
