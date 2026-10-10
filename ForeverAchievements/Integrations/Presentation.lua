-- A view model only: neither catalog snapshots nor progression databases are
-- changed by unified navigation, filtering, counts, or completion summaries.
local _, ns = ...
local P, R = {}, ns.LegacyReadOnly
ns.LegacyPresentation = P

local ROOTS = {
    { "general", "General" }, { "quests", "Quests" }, { "exploration", "Exploration" },
    { "professions", "Professions" }, { "dungeons", "Dungeons & Raids" },
    { "reputation", "Reputation" }, { "pvp", "PvP" }, { "classes", "Classes" },
    { "feats", "Feats of Strength" },
}
local function normalized(name)
    return type(name) == "string" and name:lower():gsub("[^%w]", "") or ""
end
-- These names describe runtime metadata, not fixed beta category IDs. Unknown
-- localized/new names stay browsable under Unmapped Challenges rather than
-- silently receiving an unrelated category. Ancestors supply semantic context.
local NAMES = {
    general = "general", quests = "quests", quest = "quests", questlines = "quests", questing = "quests",
    exploration = "exploration", explorer = "exploration",
    tradeskills = "professions", tradeskill = "professions", professions = "professions",
    alchemy = "professions", blacksmithing = "professions", enchanting = "professions",
    engineering = "professions", leatherworking = "professions", tailoring = "professions",
    cooking = "professions", fishing = "professions", firstaid = "professions",
    herbalism = "professions", mining = "professions", skinning = "professions",
    dungeons = "dungeons", dungeon = "dungeons", raids = "dungeons", raid = "dungeons", dungeonsraids = "dungeons",
    reputation = "reputation", reputations = "reputation",
    pvp = "pvp", playervsplayer = "pvp", playerversusplayer = "pvp",
    classes = "classes", class = "classes", druid = "classes", hunter = "classes", mage = "classes",
    paladin = "classes", priest = "classes", rogue = "classes", shaman = "classes", warlock = "classes", warrior = "classes",
    featsofstrength = "feats", feats = "feats",
}
local CONTEXT_ROOTS = { tradeskills = "professions", professions = "professions", classes = "classes",
    playervsplayer = "pvp", playerversusplayer = "pvp", pvp = "pvp", dungeons = "dungeons", raids = "dungeons" }
local GEOGRAPHY = { easternkingdoms = true, kalimdor = true }
local COLLAPSE = { general = true, quests = true, exploration = true, tradeskills = true, professions = true,
    reputation = true, reputations = true, pvp = true, playervsplayer = true, playerversusplayer = true,
    classes = true, featsofstrength = true, feats = true, dungeonsraids = true }

-- Limited individual exceptions for the mixed Adventure category. Each ID is
-- checked against its live title to avoid misclassifying a reused beta ID.
-- IDs come from existing definitions/live inspector captures, not catalog
-- enumeration: this never inserts a missing record or substitutes a mirror.
local OVERRIDES = {
    [62054] = { name = "lordvalthalaklaidtorest", root = "quests" },
    [64014] = { name = "lordvalthalaklaidtorest", root = "quests" },
    [62382] = { name = "explorer", root = "exploration" },
    [64015] = { name = "explorer", root = "exploration" },
    [62053] = { name = "exploreazeroth", root = "exploration" },
    [62353] = { name = "exploreeasternkingdoms", root = "exploration" },
    [62355] = { name = "explorekalimdor", root = "exploration" },
}

local function copy(value)
    local out = {}
    for key, field in pairs(value) do out[key] = field end
    return out
end
local function ancestors(cat, byKey)
    local path, seen = {}, {}
    while cat and not seen[cat.key] do
        path[#path + 1], seen[cat.key] = cat, true
        cat = byKey[cat.parent]
    end
    return path
end
local function categoryRoot(cat, byKey)
    local path = ancestors(cat, byKey)
    -- PvP reputations/ranks and class/profession subcategories retain their
    -- actual native context even when a child name also describes another root.
    for i = #path, 1, -1 do
        local root = CONTEXT_ROOTS[normalized(path[i].name)]
        if root then return root end
    end
    for _, ancestor in ipairs(path) do
        local root = NAMES[normalized(ancestor.name)]
        if root then return root end
    end
    if cat and GEOGRAPHY[normalized(cat.name)] then
        for _, ancestor in ipairs(path) do
            local name = normalized(ancestor.name)
            if name == "adventure" or name == "exploration" or name == "explorer" then return "exploration" end
        end
    end
    return "unmapped"
end
function P.NativeCategory(row, categories)
    local root = categoryRoot(categories[row.category], categories)
    if root ~= "unmapped" then return root, false end
    local override = OVERRIDES[row.id]
    if override and normalized(row.name) == override.name then return override.root, true end
    return root, false
end

function P.Build(page, nativeCatalog)
    local native, custom = nativeCatalog or ns.LegacyAdapter.Catalog(page), ns.CustomAchievementAdapter.Catalog()
    local model = { records = {}, byKey = {}, categories = {}, roots = {}, byCategory = {}, native = native, custom = custom }
    local function category(cat, root)
        cat.children = {}; cat.records = cat.records or {}
        model.categories[#model.categories + 1] = cat; model.byCategory[cat.key] = cat
        if root then model.roots[#model.roots + 1] = cat end
        return cat
    end
    category({ key = "summary", name = "Summary" }, true)
    for _, root in ipairs(ROOTS) do category({ key = root[1], name = root[2] }, true) end
    -- Virtual selectors keep source-specific summaries/API callers supported,
    -- but never create source-separated navigation entries.
    model.byCategory.legacy = { key = "legacy", name = "Native Legacy Challenges", source = "legacy", records = {}, children = {}, virtual = true }
    model.byCategory.custom = { key = "custom", name = "Character Achievements", source = "custom", records = {}, children = {}, virtual = true }
    local nativeCategories = {}
    for _, cat in ipairs(native.categories or {}) do nativeCategories[cat.key] = cat end
    local function rootCategory(key)
        if not model.byCategory[key] then category({ key = "unmapped", name = "Unmapped Challenges" }, true) end
        return model.byCategory[key] or model.byCategory.unmapped
    end
    local function nativeCategory(cat, root, visiting)
        local parent = rootCategory(root)
        if not cat or COLLAPSE[normalized(cat.name)] and NAMES[normalized(cat.name)] == root then return parent end
        if model.byCategory[cat.key] then return model.byCategory[cat.key] end
        visiting = visiting or {}
        if visiting[cat.key] then return parent end
        visiting[cat.key] = true
        local originalParent = nativeCategories[cat.parent]
        if originalParent and categoryRoot(originalParent, nativeCategories) == root then
            parent = nativeCategory(originalParent, root, visiting)
        end
        visiting[cat.key] = nil
        -- A recursion cycle may have already inserted this category while
        -- unwinding. Return it rather than creating a duplicate navigation key.
        if model.byCategory[cat.key] then return model.byCategory[cat.key] end
        local view = category({ key = cat.key, name = cat.name, parent = parent.key, nativeID = cat.id,
            nativeCategory = cat.key, unifiedRoot = root })
        parent.children[#parent.children + 1] = view
        return view
    end
    local function append(original)
        if model.byKey[original.key] then return end
        local row, target = copy(original)
        if row.source == "legacy" then
            local root, override = P.NativeCategory(row, nativeCategories)
            row.nativeCategory = original.category
            row.unifiedRoot = root
            -- A record-level override in a mixed category belongs directly to
            -- its unified root; its siblings retain their own independent map.
            target = override and rootCategory(root) or nativeCategory(nativeCategories[original.category], root)
        else
            local root = row.customCategory or (row.category or ""):match("^custom%-category:(.+)$")
            row.customCategory = root
            if not model.byCategory[root] or model.byCategory[root].virtual then root = "unmapped" end
            row.unifiedRoot = root
            target = rootCategory(root)
        end
        row.category = target.key
        target.records[#target.records + 1] = row
        model.records[#model.records + 1] = row; model.byKey[row.key] = row
        local source = model.byCategory[row.source]
        if source then source.records[#source.records + 1] = row end
    end
    for _, row in ipairs(native.records or {}) do append(row) end
    for _, row in ipairs(custom.records or {}) do append(row) end
    return model
end

function P.Rows(model, key, search, filter)
    local allowed, out = {}, {}
    local function visit(cat)
        if not cat or allowed[cat.key] then return end
        allowed[cat.key] = true
        for _, child in ipairs(cat.children or {}) do visit(child) end
    end
    visit(model.byCategory[key])
    search = (search or ""):lower()
    for _, row in ipairs(model.records) do
        if (key == "summary" or key == row.source or allowed[row.category]) and
            (filter == nil or filter == "All" or filter == "Complete" and row.completed == true or filter == "Incomplete" and row.completed == false) and
            (search == "" or ((row.name or "") .. " " .. (row.description or "")):lower():find(search, 1, true)) then out[#out + 1] = row end
    end
    return out
end
function P.Count(model, key)
    local rows = P.Rows(model, key)
    local done, unknown = 0, 0
    for _, row in ipairs(rows) do
        if row.completed == true then done = done + 1 elseif row.completed == nil then unknown = unknown + 1 end
    end
    return done, #rows, unknown
end
function P.Recent(model, source, limit)
    local rows = {}
    for _, row in ipairs(P.Rows(model, source)) do
        local reliable = source == "custom" and R.Number(row.timestamp) and row.timestamp > 0 or
            source == "legacy" and R.Number(row.dateSort) and row.date ~= nil
        if row.completed == true and reliable then rows[#rows + 1] = row end
    end
    table.sort(rows, function(a, b)
        local av, bv = source == "custom" and a.timestamp or a.dateSort, source == "custom" and b.timestamp or b.dateSort
        if av == bv then return a.key < b.key end
        return av > bv
    end)
    if limit then while #rows > math.max(0, math.floor(limit)) do rows[#rows] = nil end end
    return rows
end
function P.Summary(model)
    local summary = { categories = {} }
    for _, source in ipairs({ "custom", "native" }) do
        local catalog, key = model[source], source == "native" and "legacy" or "custom"
        local completed, total, unknown = P.Count(model, key)
        summary[source] = { points = catalog.points, completed = completed, total = total, unknown = unknown,
            available = catalog.available ~= false and (source == "custom" or catalog.available == true or total > 0),
            partial = catalog.partial == true, recent = P.Recent(model, key, 4) }
    end
    for _, cat in ipairs(model.roots) do
        if cat.key ~= "summary" then
            local completed, total, unknown = P.Count(model, cat.key)
            summary.categories[#summary.categories + 1] = { key = cat.key, name = cat.name, completed = completed,
                total = total, unknown = unknown, partial = model.native.partial == true }
        end
    end
    return summary
end
function P.Criteria(row)
    return (row.source == "legacy" and ns.LegacyAdapter or ns.CustomAchievementAdapter).Criteria(row)
end
function P.Resolve(model, key)
    if model.byKey[key] then return model.byKey[key] end
    local id = type(key) == "string" and key:match("^legacy:(%d+)$")
    return id and ns.LegacyAdapter.Resolve(tonumber(id))
end
