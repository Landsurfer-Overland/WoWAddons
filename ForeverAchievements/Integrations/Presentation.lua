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
-- Subjects are shared by both sources. Only subjects with actual records are
-- inserted into navigation; this table defines their labels and ordering.
local SUBJECTS = {
    general = { { "character", "Character" }, { "progression", "Progression" }, { "miscellaneous", "Miscellaneous" } },
    quests = { { "eastern-kingdoms", "Eastern Kingdoms" }, { "kalimdor", "Kalimdor" }, { "storylines", "Storylines" }, { "loremaster", "Loremaster" } },
    exploration = { { "eastern-kingdoms", "Eastern Kingdoms" }, { "kalimdor", "Kalimdor" }, { "world", "World Exploration" }, { "zephras-isle", "Zephras Isle" } },
    professions = { { "primary", "Primary Professions" }, { "alchemy", "Alchemy" }, { "blacksmithing", "Blacksmithing" },
        { "enchanting", "Enchanting" }, { "engineering", "Engineering" }, { "herbalism", "Herbalism" },
        { "leatherworking", "Leatherworking" }, { "mining", "Mining" }, { "skinning", "Skinning" },
        { "tailoring", "Tailoring" }, { "fishing", "Fishing" }, { "cooking", "Cooking" }, { "first-aid", "First Aid" } },
    dungeons = { { "dungeons", "Dungeons" }, { "raids", "Raids" }, { "bosses", "Boss Encounters" } },
    reputation = { { "alliance", "Alliance" }, { "horde", "Horde" }, { "other-factions", "Other Factions" } },
    pvp = { { "battlegrounds", "Battlegrounds" }, { "world", "World PvP" }, { "honorable-kills", "Honorable Kills" },
        { "ranks", "Ranks" }, { "reputations", "Battleground Reputations" }, { "season-journey", "Season Journey" } },
    classes = { { "challenges", "Class Challenges" }, { "progression", "Class Progression" } },
    feats = { { "special", "Special Achievements" }, { "other-legacy", "Other Legacy Challenges" } },
}
local function normalized(name)
    return type(name) == "string" and name:lower():gsub("[^%w]", "") or ""
end
-- These names describe runtime metadata, not fixed beta category IDs. Unknown
-- localized/new names receive a documented navigation fallback rather than a
-- fabricated achievement type. Ancestors supply semantic context.
local NAMES = {
    general = "general", quests = "quests", quest = "quests", questlines = "quests", questing = "quests",
    storylines = "quests", loremaster = "quests",
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
local PROFESSION_NAMES = { alchemy = "alchemy", blacksmithing = "blacksmithing", enchanting = "enchanting", engineering = "engineering",
    herbalism = "herbalism", leatherworking = "leatherworking", mining = "mining", skinning = "skinning", tailoring = "tailoring",
    fishing = "fishing", cooking = "cooking", firstaid = "first-aid" }
local SKILL_SUBJECTS = { [171] = "alchemy", [164] = "blacksmithing", [333] = "enchanting", [202] = "engineering", [182] = "herbalism",
    [165] = "leatherworking", [186] = "mining", [393] = "skinning", [197] = "tailoring", [356] = "fishing", [185] = "cooking", [129] = "first-aid" }
local SERIES_SUBJECTS = { cook = "cooking", recipes = "cooking", fishing = "fishing", fish = "fishing", firstaid = "first-aid",
    qfzones = "fishing", qfrares = "fishing", qfkinds = "fishing", prof = "primary" }
local FISH_KEYS = { oldgnome = true, diplomat = true, masterangler = true, rarefish = true }

-- Limited individual exceptions for the mixed Adventure category. Each ID is
-- checked against its live title to avoid misclassifying a reused beta ID.
-- IDs come from existing definitions/live inspector captures, not catalog
-- enumeration: this never inserts a missing record or substitutes a mirror.
local OVERRIDES = {
    [62054] = { name = "lordvalthalaklaidtorest", root = "quests", subject = "storylines" },
    [64014] = { name = "lordvalthalaklaidtorest", root = "quests", subject = "storylines" },
    [62382] = { name = "explorer", root = "exploration", subject = "world" },
    [64015] = { name = "explorer", root = "exploration", subject = "world" },
    [62053] = { name = "exploreazeroth", root = "exploration", subject = "world" },
    [62353] = { name = "exploreeasternkingdoms", root = "exploration", subject = "eastern-kingdoms", alternate = "easternkingdoms" },
    [62355] = { name = "explorekalimdor", root = "exploration", subject = "kalimdor", alternate = "kalimdor" },
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
    for _, place in ipairs(path) do
        if GEOGRAPHY[normalized(place.name)] then
            for _, ancestor in ipairs(path) do
                local name = normalized(ancestor.name)
                if name == "adventure" or name == "exploration" or name == "explorer" then return "exploration" end
            end
        end
    end
    return "unmapped"
end
function P.NativeCategory(row, categories)
    local root = categoryRoot(categories[row.category], categories)
    local override = OVERRIDES[row.id]
    if override and (normalized(row.name) == override.name or normalized(row.name) == override.alternate) and
        (root == "unmapped" or root == override.root) then return override.root, true, override.subject end
    return root, false
end
local function geography(value)
    local name = normalized(value)
    if name == "ek" or name == "easternkingdoms" then return "eastern-kingdoms" end
    if name == "kal" or name == "kalimdor" then return "kalimdor" end
    if name == "zephrasisle" then return "zephras-isle" end
end
local function subjectFromNames(root, names)
    for _, name in ipairs(names) do
        name = normalized(name)
        if root == "professions" and PROFESSION_NAMES[name] then return PROFESSION_NAMES[name] end
        if root == "exploration" or root == "quests" then
            local place = geography(name)
            if place then return place end
            if root == "quests" and name == "loremaster" then return "loremaster" end
            if root == "quests" and (name == "questlines" or name == "storylines") then return "storylines" end
        elseif root == "dungeons" then
            if name == "dungeons" or name == "foreverdungeons" or name == "dungeon" then return "dungeons" end
            if name == "raids" or name == "raid" then return "raids" end
            if name == "worldbosses" or name == "bossencounters" or name == "bosses" then return "bosses" end
        elseif root == "pvp" then
            if name == "battlegrounds" or name == "inthebattle" then return "battlegrounds" end
            if name == "worldpvp" then return "world" end
            if name == "honorablekills" then return "honorable-kills" end
            if name == "ranks" then return "ranks" end
            if name == "reputations" or name == "battlegroundreputation" then return "reputations" end
            if name == "seasonjourney" then return "season-journey" end
        elseif root == "general" then
            if name == "levels" or name == "riding" or name == "progression" then return "progression" end
            if name == "character" or name == "collections" then return "character" end
        elseif root == "reputation" then
            if name == "alliance" or name == "horde" then return name end
        elseif root == "classes" and (name == "classprogression" or name == "progression") then return "progression" end
    end
end
local function defaultSubject(root)
    return ({ general = "miscellaneous", exploration = "world", professions = "primary", reputation = "other-factions",
        classes = "challenges", feats = "special" })[root]
end
local function nativeSubject(row, root, categories, override)
    if override then return override end
    local names = {}
    for _, cat in ipairs(ancestors(categories[row.category], categories)) do names[#names + 1] = cat.name end
    return subjectFromNames(root, names) or defaultSubject(root)
end
local function customSubject(row, root)
    local a = row.achievement or {}
    local section = row.customSection or a.section
    if root == "professions" then
        -- Authored skill/skill-line metadata wins over section and series.
        local skill = row.skill or a.skill
        local subject = SKILL_SUBJECTS[row.skillLineID or a.skillLineID or skill] or PROFESSION_NAMES[normalized(skill)]
        if subject then return subject end
        subject = subjectFromNames(root, { section or "" })
        if subject then return subject end
        subject = SERIES_SUBJECTS[row.series or a.series]
        if subject then return subject end
        local key = row.savedKey or a.key or ""
        if key:match("^cook%d") or key:match("^recipes%d") then return "cooking" end
        if key:match("^fish%d") or key:match("^fished%d") or FISH_KEYS[key] then return "fishing" end
        if key:match("^aid%d") then return "first-aid" end
        -- A multi-secondary meta belongs to the profession parent, not to one
        -- arbitrary secondary profession or to three duplicate subject lists.
        if key == "paythebills" or normalized(section) == "secondary" then return nil end
    elseif root == "quests" then
        local sectionSubject = subjectFromNames(root, { section or "" })
        if sectionSubject then return sectionSubject end
    elseif root == "reputation" then
        local faction = normalized(row.faction or a.faction)
        if faction == "alliance" or faction == "horde" then return faction end
    elseif root == "exploration" then
        local place = geography(row.customGeography)
        if place then return place end
        local key = row.savedKey or a.key
        if key == "exploreEK" then return "eastern-kingdoms" end
        if key == "exploreKal" then return "kalimdor" end
    end
    return subjectFromNames(root, { section or "" }) or defaultSubject(root)
end

function P.Build(page, nativeCatalog)
    local native, custom = nativeCatalog or ns.LegacyAdapter.Catalog(page), ns.CustomAchievementAdapter.Catalog()
    local model = { records = {}, byKey = {}, categories = {}, roots = {}, byCategory = {}, native = native, custom = custom,
        unmapped = {}, unmappedIDs = {}, duplicateKeys = {}, criteriaSearchScope = "Loaded criteria only" }
    model.unmappedRecords = model.unmapped
    local subjects, nativeCategories = {}, {}
    for root, definitions in pairs(SUBJECTS) do
        for index, definition in ipairs(definitions) do
            subjects[root .. ":" .. definition[1]] = { name = definition[2], order = index }
        end
    end
    local function category(key, name, parent, order)
        local cat = { key = key, name = name, parent = parent and parent.key, records = {}, children = {}, order = order }
        model.categories[#model.categories + 1] = cat; model.byCategory[key] = cat
        if parent then parent.children[#parent.children + 1] = cat else model.roots[#model.roots + 1] = cat end
        return cat
    end
    category("summary", "Summary")
    for _, root in ipairs(ROOTS) do category(root[1], root[2]) end
    -- These source selectors support summaries without creating navigation
    -- groups or combining native and character points.
    for _, source in ipairs({ "legacy", "custom" }) do
        model.byCategory[source] = { key = source, name = source == "legacy" and "Native Legacy Challenges" or "Character Achievements",
            source = source, records = {}, children = {}, virtual = true }
    end
    for _, cat in ipairs(native.categories or {}) do
        nativeCategories[cat.key] = cat
        model.byCategory[cat.key] = { key = cat.key, name = cat.name, parent = cat.parent, records = {}, children = {},
            virtual = true, aliasRows = {}, aliasSubjects = {}, aliasRoots = {} }
    end
    local function targetCategory(root, subject)
        local key = subject and (root .. ":" .. subject)
        if not key or not subjects[key] then return model.byCategory[root] end
        return model.byCategory[key] or category(key, subjects[key].name, model.byCategory[root], subjects[key].order)
    end
    local function append(original)
        if model.byKey[original.key] then
            model.duplicateKeys[#model.duplicateKeys + 1] = original.key
            return
        end
        local row, root, subject = copy(original)
        local originalCategories = {}
        if row.source == "legacy" then
            local _, override
            root, override, subject = P.NativeCategory(row, nativeCategories)
            row.nativeCategory = original.category
            for _, cat in ipairs(ancestors(nativeCategories[original.category], nativeCategories)) do
                originalCategories[#originalCategories + 1] = cat.name
            end
            if root == "unmapped" then
                root, subject = "feats", "other-legacy"
                row.navigationFallback = true
                model.unmapped[#model.unmapped + 1] = { id = row.id, key = row.key, name = row.name,
                    nativeCategory = original.category, reason = "Native subject metadata is unavailable or not classified" }
                model.unmappedIDs[#model.unmappedIDs + 1] = row.id
            else subject = nativeSubject(row, root, nativeCategories, subject) end
        else
            root = row.customCategory or (row.category or ""):match("^custom%-category:(.+)$")
            row.customCategory = root
            if not model.byCategory[root] or model.byCategory[root].virtual then root = "general" end
            subject = customSubject(row, root)
            originalCategories[#originalCategories + 1] = row.customSection or ""
            originalCategories[#originalCategories + 1] = row.customGeography or ""
        end
        local target = targetCategory(root, subject)
        row.unifiedRoot, row.rootCategory, row.subcategory = root, root, target.key ~= root and target.key or nil
        row.category = target.key
        row.categoryMetadata = { model.byCategory[root].name, target.name }
        for _, name in ipairs(originalCategories) do row.categoryMetadata[#row.categoryMetadata + 1] = name end
        row.searchText = ((row.name or "") .. " " .. (row.description or "") .. " " .. table.concat(row.categoryMetadata, " ")):lower()
        target.records[#target.records + 1] = row
        model.records[#model.records + 1] = row; model.byKey[row.key] = row
        local source = model.byCategory[row.source]
        if source then source.records[#source.records + 1] = row end
        if row.source == "legacy" then
            for _, cat in ipairs(ancestors(nativeCategories[original.category], nativeCategories)) do
                local alias = model.byCategory[cat.key]
                alias.aliasRows[row.key] = true; alias.aliasSubjects[target.key] = true; alias.aliasRoots[root] = true
                alias.records[#alias.records + 1] = row
            end
        end
    end
    for _, row in ipairs(native.records or {}) do append(row) end
    for _, row in ipairs(custom.records or {}) do append(row) end
    -- Old native-category keys remain safe selectors during a model refresh.
    -- Prefer their stable subject/root key for selected-row artwork when possible.
    for _, cat in ipairs(native.categories or {}) do
        local alias = model.byCategory[cat.key]
        local function onlyKey(keys)
            local found
            for key in pairs(keys) do if found then return nil end; found = key end
            return found
        end
        alias.aliasTarget = onlyKey(alias.aliasSubjects) or onlyKey(alias.aliasRoots)
        if alias.aliasTarget then alias.parent = model.byCategory[alias.aliasTarget].parent or alias.aliasTarget end
    end
    if #model.unmapped > 0 then
        model.byCategory.unmapped = { key = "unmapped", name = "Other Legacy Challenges", children = {}, virtual = true,
            aliasTarget = "feats:other-legacy", aliasRows = {} }
        for _, record in ipairs(model.unmapped) do model.byCategory.unmapped.aliasRows[record.key] = true end
    end
    for _, root in ipairs(model.roots) do
        table.sort(root.children, function(a, b) return a.order < b.order end)
    end
    return model
end
function P.CategoryKey(model, key)
    local cat = model.byCategory[key]
    return cat and (cat.aliasTarget or cat.key) or "summary"
end

function P.Rows(model, key, search, filter)
    local allowed, out = {}, {}
    local selected = model.byCategory[key]
    local function visit(cat)
        if not cat or allowed[cat.key] then return end
        allowed[cat.key] = true
        for _, child in ipairs(cat.children or {}) do visit(child) end
    end
    visit(model.byCategory[key])
    search = (search or ""):lower()
    local selectedFilter = normalized(filter or "All")
    for _, row in ipairs(model.records) do
        local sourceMatches = selectedFilter == "all" or
            (selectedFilter == "complete" or selectedFilter == "completed") and row.completed == true or
            selectedFilter == "incomplete" and row.completed == false or
            (selectedFilter == "character" or selectedFilter == "characterachievements") and row.source == "custom" or
            (selectedFilter == "legacy" or selectedFilter == "legacychallenges") and row.source == "legacy"
        local searchMatches = search == "" or (row.searchText or ((row.name or "") .. " " .. (row.description or "")):lower()):find(search, 1, true) or
            row.criteriaSearchText and row.criteriaSearchText:find(search, 1, true)
        if (key == "summary" or key == row.source or allowed[row.category] or selected and selected.aliasRows and selected.aliasRows[row.key]) and
            sourceMatches and searchMatches then out[#out + 1] = row end
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
    if row.criteriaCache then return row.criteriaCache end
    local adapter = row.source == "legacy" and ns.LegacyAdapter or ns.CustomAchievementAdapter
    local result = R.Call(adapter.Criteria, row)
    local data = result and result[1]
    if type(data) ~= "table" then data = { items = {}, available = false, complete = false } end
    row.criteriaCache = data
    -- Search never enumerates all native criteria on each keypress. It adds
    -- only objectives already loaded for an expanded card, with a fixed bound.
    local text = {}
    for index, item in ipairs(data.items or {}) do
        if index > 64 then break end
        local name = R.Text(item.name)
        if name and not item.unavailable then text[#text + 1] = name:sub(1, 256) end
    end
    row.criteriaSearchText = table.concat(text, " "):lower()
    return data
end
function P.Resolve(model, key)
    if model.byKey[key] then return model.byKey[key] end
    local id = type(key) == "string" and key:match("^legacy:(%d+)$")
    return id and ns.LegacyAdapter.Resolve(tonumber(id))
end
