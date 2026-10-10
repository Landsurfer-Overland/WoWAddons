-- A view model only: neither catalog snapshots nor progression databases are
-- changed by unified navigation, filtering, counts, or completion summaries.
local _, ns = ...
local P, R = {}, ns.LegacyReadOnly
ns.LegacyPresentation = P
local function begin(name)
    local perf = ns.LegacyPerf
    return perf and perf.Begin and perf.Begin(name)
end
local function finish(token)
    local perf = ns.LegacyPerf
    if perf and perf.Finish then perf.Finish(token) end
end
local function count(name, amount)
    local perf = ns.LegacyPerf
    if perf and perf.Count then perf.Count(name, amount) end
end
local function arrayCopy(rows, limit)
    local result = {}
    for i = 1, math.min(#rows, limit or #rows) do result[i] = rows[i] end
    return result
end

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
    professions = { { "alchemy", "Alchemy" }, { "blacksmithing", "Blacksmithing" },
        { "enchanting", "Enchanting" }, { "engineering", "Engineering" }, { "herbalism", "Herbalism" },
        { "leatherworking", "Leatherworking" }, { "mining", "Mining" }, { "skinning", "Skinning" },
        { "tailoring", "Tailoring" }, { "fishing", "Fishing" }, { "cooking", "Cooking" }, { "first-aid", "First Aid" } },
    dungeons = { { "dungeons", "Dungeons" }, { "raids", "Raids" }, { "bosses", "Boss Encounters" } },
    reputation = { { "alliance", "Alliance" }, { "horde", "Horde" }, { "other-factions", "Other Factions" } },
    pvp = { { "battlegrounds", "Battlegrounds" }, { "world", "World PvP" }, { "honorable-kills", "Honorable Kills" },
        { "ranks", "Ranks" }, { "reputations", "Battleground Reputations" }, { "season-journey", "Season Journey" } },
    classes = {},
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
    qfzones = "fishing", qfrares = "fishing", qfkinds = "fishing" }
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
local function categoryRoot(cat, byKey, path)
    path = path or ancestors(cat, byKey)
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
function P.NativeCategory(row, categories, context)
    local root = context and context.roots[row.category] or categoryRoot(categories[row.category], categories)
    local class = context and context.classes.nativeIDs[row.id]
    if class and normalized(row.name) == class.name then return "classes", true, class.subject end
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
local function subjectFromNames(root, names, classSubjects)
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
            if name == "miscellaneous" then return "miscellaneous" end
        elseif root == "reputation" then
            if name == "alliance" or name == "horde" then return name end
            if name == "otherfactions" or name == "foreverfactions" or name == "neutralfactions" then return "other-factions" end
        elseif root == "classes" then
            if classSubjects and classSubjects[name] then return classSubjects[name] end
            if name == "classprogression" or name == "progression" then return "progression" end
        end
    end
end
local function defaultSubject(root, leafName)
    -- Broad General records belong to its selected parent list. Narrow subjects
    -- still use their authored metadata; this does not aggregate child lists.
    if root == "general" then return nil end
    if root == "reputation" then
        local name = normalized(leafName)
        if name == "general" or name == "reputation" or name == "reputations" or name == "exalted" or
            name == "exaltedreputation" or name == "exaltedreputations" then return nil end
    end
    return ({ exploration = "world", reputation = "other-factions",
        feats = "special" })[root]
end
local function nativeSubject(row, root, categories, override, context)
    if override then return override end
    if context then return context.subjects[row.category] or nil end
    local names = {}
    for _, cat in ipairs(ancestors(categories[row.category], categories)) do names[#names + 1] = cat.name end
    return subjectFromNames(root, names) or defaultSubject(root, names[1])
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
        local series = row.series or a.series
        if series == "prof" then return nil end
        subject = SERIES_SUBJECTS[series]
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
        if (row.series or a.series) == "exalted" or normalized(section) == "exalted" then return nil end
        local faction = normalized(row.faction or a.faction)
        if faction == "alliance" or faction == "horde" then return faction end
    elseif root == "exploration" then
        local place = geography(row.customGeography)
        if place then return place end
        local key = row.savedKey or a.key
        if key == "exploreEK" then return "eastern-kingdoms" end
        if key == "exploreKal" then return "kalimdor" end
    end
    return subjectFromNames(root, { section or "" }) or defaultSubject(root, section)
end

-- Playable classes come from this client's enumeration. If that API is absent,
-- only the Forever client references with actual class challenge definitions
-- supply a fallback; icon/color globals are not proof of playable classes.
local classCache
local function classDefinitions(native)
    if classCache then return classCache end
    local definitions, names, byID, byToken = {}, {}, {}, {}
    local function add(label, token, id)
        label, token, id = R.Text(label), R.Text(token), R.ID(id)
        if not label or label == "" then return end
        local subject = normalized(token or label)
        if subject == "" or names[subject] then return end
        definitions[#definitions + 1] = { subject, label }
        names[normalized(label)], names[subject] = subject, subject
        if id then byID[id] = subject end
        if token then byToken[token:upper()] = subject end
    end
    local evidence, nativeByCategory = {}, {}
    for _, section in ipairs(ns.FOREVER_ACH or {}) do
        if normalized(section.title) == "classes" then
            for _, achievement in ipairs(section.list or {}) do evidence[normalized(achievement.group)] = true end
        end
    end
    local current = R.Call(UnitClass, "player")
    if current then evidence[normalized(current[1])], evidence[normalized(current[2])] = true, true end
    for _, category in ipairs(native.categories or {}) do nativeByCategory[category.key] = category end
    for _, category in ipairs(native.categories or {}) do
        for _, ancestor in ipairs(ancestors(category, nativeByCategory)) do
            if normalized(ancestor.name) == "classes" then evidence[normalized(category.name)] = true; break end
        end
    end
    local allowedAPI = C_GameRules and C_GameRules.IsClassAllowedForGameMode
    local runtimeKnown = false
    local function supported(label, token, id)
        if type(allowedAPI) == "function" then
            local result = R.Call(allowedAPI, id)
            local state = result and R.Bool(result[1])
            if state ~= nil then runtimeKnown = true end
            return state == true
        end
        return evidence[normalized(label)] or evidence[normalized(token)]
    end
    local number = R.Call(GetNumClasses)
    number = number and R.Number(number[1])
    if not number and type(allowedAPI) == "function" and C_CreatureInfo and type(C_CreatureInfo.GetClassInfo) == "function" then number = 32 end
    if number and number == math.floor(number) and number >= 1 and number <= 32 then
        for i = 1, number do
            local info = R.Call(GetClassInfo, i)
            if info and supported(info[1], info[2], info[3] or i) then add(info[1], info[2], info[3] or i) end
            if C_CreatureInfo and C_CreatureInfo.GetClassInfo then
                local result = R.Call(C_CreatureInfo.GetClassInfo, i)
                local data = result and R.Field(result, 1)
                if type(data) == "table" and supported(R.Field(data, "className"), R.Field(data, "classFile"), R.Field(data, "classID")) then
                    add(R.Field(data, "className"), R.Field(data, "classFile"), R.Field(data, "classID"))
                end
            end
        end
    end
    if current and (type(allowedAPI) ~= "function" or supported(current[1], current[2], current[3])) then
        add(current[1], current[2], current[3])
    end
    local references = {}
    for _, section in ipairs(ns.FOREVER_ACH or {}) do
        if normalized(section.title) == "classes" then
            for _, achievement in ipairs(section.list or {}) do
                local group = R.Text(achievement.group)
                if #definitions == 0 and not runtimeKnown and group then references[group] = true end
            end
        end
    end
    -- This ordered list determines display order only. Presence in the actual
    -- Forever reference above is required; extra captured classes are retained.
    for _, group in ipairs({"Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"}) do
        if references[group] then add(group, group); references[group] = nil end
    end
    local extra = {}; for group in pairs(references) do extra[#extra + 1] = group end
    table.sort(extra); for _, group in ipairs(extra) do add(group, group) end
    local nativeIDs = {}
    for _, section in ipairs(ns.FOREVER_ACH or {}) do
        if normalized(section.title) == "classes" then
            for _, achievement in ipairs(section.list or {}) do
                local subject = names[normalized(achievement.group)]
                if subject then
                    for _, id in ipairs(achievement.ids or {}) do
                        nativeIDs[id] = { subject = subject, name = normalized(achievement.name) }
                    end
                end
            end
        end
    end
    local result = { definitions = definitions, names = names, byID = byID, byToken = byToken, nativeIDs = nativeIDs }
    -- Empty early-login results can become available later; do not cache them.
    if #definitions > 0 and runtimeKnown then classCache = result end
    return result
end
-- Relation proof caches contain objective definitions only, never completion,
-- quantities, dates, account scope, or points. Reads are bounded across all
-- candidate zones in a Build; missing/changed/partial proofs remain separate.
local relationProofs, relationProofOrder = {}, {}
local relationSnapshots = setmetatable({}, { __mode = "k" })
local EXTRA_ZONE_IDS = { exploreRiverglades = 62354, exploreHyjal = 62356, exploreShendralas = 63684 }
P.MAX_RELATION_READS = 256
local function zoneRelationship(custom, native, budget)
    local zone = custom.exploration
    if not zone or zone.kind ~= "zone" then return false, "No authored zone definition" end
    local id = R.ID(zone.zoneID) or EXTRA_ZONE_IDS[custom.savedKey]
    if not id or native.id ~= id then return false, "No explicit native zone identity" end
    local expectedName = "Explore " .. (zone.zoneName or custom.zoneName or "")
    local expectedDescription = expectedName .. ", revealing the covered areas of the world map."
    if normalized(native.name) ~= normalized(expectedName) or normalized(custom.name) ~= normalized(expectedName) then
        return false, "Stable ID has a different zone identity"
    end
    if normalized(native.description) ~= normalized(expectedDescription) or
        normalized(custom.description) ~= normalized(expectedDescription) then
        return false, "Zone requirement description differs or is unavailable"
    end
    local required, signature = {}, {}
    for _, area in ipairs(zone.areas or {}) do
        local name = R.Text(area[1])
        if not name or required[name] then return false, "Authored zone objectives are ambiguous" end
        required[name] = true; signature[#signature + 1] = name
    end
    if #signature == 0 or #signature > 256 then return false, "Authored zone objective set is unavailable" end
    table.sort(signature)
    signature = table.concat(signature, "\031")
    local client = R.Call(GetBuildInfo)
    local build = client and (tostring(R.Text(client[1]) or "") .. ":" .. tostring(R.Text(client[2]) or "") .. ":" .. tostring(R.Number(client[4]) or "")) or "session"
    local identity = build .. "\031" .. normalized(native.name) .. "\031" .. normalized(native.description) .. "\031" .. signature
    local known = relationProofs[id]
    if known and known.identity == identity then return known.matches, known.reason end
    local prior = budget.results[id]
    if prior and prior.identity == identity then return prior.matches, prior.reason end
    local function outcome(matches, reason)
        budget.results[id] = { identity = identity, matches = matches, reason = reason }
        return matches, reason
    end
    local loaded = native.criteriaCache or native.criteria
    if not (type(loaded) == "table" and loaded.available == true and loaded.complete == true and type(loaded.items) == "table") then loaded = nil end
    local number
    if loaded then number = R.Number(loaded.count) or #loaded.items
    else
        if budget.remaining <= 0 then return outcome(false, "Objective verification deferred by bounded read budget") end
        budget.remaining = budget.remaining - 1; count("relationship.criteria_reads", 1)
        local result = R.Call(GetAchievementNumCriteria, id)
        number = result and R.Number(result[1])
    end
    if not number or number ~= math.floor(number) or number < 1 or number > 256 then
        return outcome(false, "Native zone objective count is unavailable")
    end
    local matches, reason = false, "Native zone objective count differs"
    if number == #zone.areas then
        if not loaded and budget.remaining < number then return outcome(false, "Objective verification deferred by bounded read budget") end
        local seen = {}
        matches, reason = true, "Exact zone ID, requirement description, and revealed-area objective set"
        for i = 1, number do
            local name, kind, amount
            if loaded then
                local item = loaded.items[i]
                name, kind, amount = R.Text(R.Field(item, "name")), R.Number(R.Field(item, "type")), R.Number(R.Field(item, "required"))
            else
                budget.remaining = budget.remaining - 1; count("relationship.criteria_reads", 1)
                local info = R.Call(GetAchievementCriteriaInfo, id, i)
                name, kind, amount = info and R.Text(info[1]), info and R.Number(info[2]), info and R.Number(info[5])
            end
            if not name or kind == nil or amount == nil then return outcome(false, "Native zone objectives are unavailable") end
            -- Native type 43 is a map-area revelation. A quest, account wrapper,
            -- visited zone, or differently scaled criterion cannot prove parity.
            if kind ~= 43 or amount ~= 1 or not required[name] or seen[name] then
                matches, reason = false, "Native zone revealed-area requirements differ"
            end
            seen[name] = true
        end
    end
    if not matches then return outcome(matches, reason) end
    if #relationProofOrder >= 128 and not relationProofs[id] then
        relationProofs[table.remove(relationProofOrder, 1)] = nil
    end
    if not relationProofs[id] then relationProofOrder[#relationProofOrder + 1] = id end
    relationProofs[id] = { identity = identity, matches = matches, reason = reason }
    return matches, reason
end
local META_RELATIONS = {
    exploreEK = { id = 62353, names = { exploreeasternkingdoms = true, easternkingdoms = true }, kind = "continent" },
    exploreKal = { id = 62355, names = { explorekalimdor = true, kalimdor = true }, kind = "continent" },
    worldexplorer = { id = 62053, names = { exploreazeroth = true }, kind = "world" },
}
local function metaRelationship(custom, native, customByKey, combinedByKey, budget)
    local relation, definition = META_RELATIONS[custom.savedKey], custom.exploration
    if not relation or not definition or definition.kind ~= relation.kind or native.id ~= relation.id or
        not relation.names[normalized(native.name)] then return false, "Meta identity is not explicitly mapped" end
    local expected, dependencies, number = {}, {}, 0
    for _, childKey in ipairs(definition.children or {}) do
        local child = customByKey[childKey]
        if not child or not child.exploration then return false, "A custom meta child definition is unavailable" end
        local childID, proof
        if relation.kind == "continent" then
            childID = R.ID(child.exploration.zoneID) or EXTRA_ZONE_IDS[child.savedKey]
            if not childID then return false, "A zone lacks an explicit native identity" end
            -- A previously verified objective signature is sufficient even when
            -- this partial catalog does not include the corresponding zone row.
            -- No synthetic achievement is inserted or its progress inferred.
            proof = zoneRelationship(child, { id = childID, name = child.name, description = child.description },
                { remaining = 0, results = {} })
            local known = relationProofs[childID]
            if not proof or not known then return false, "All underlying zone requirements are not yet verified" end
            dependencies[#dependencies + 1] = known.identity
        else
            local combined = combinedByKey[child.key]
            childID = combined and combined.native.id
            if not childID then return false, "All underlying continent requirements are not yet verified" end
            dependencies[#dependencies + 1] = relationProofs[childID] and relationProofs[childID].identity or child.key
        end
        if expected[childID] then return false, "Custom meta children contain duplicate native identities" end
        expected[childID], number = true, number + 1
    end
    if number == 0 or number > 256 then return false, "Custom meta child set is unavailable" end
    table.sort(dependencies)
    local client = R.Call(GetBuildInfo)
    local build = client and (tostring(R.Text(client[1]) or "") .. ":" .. tostring(R.Text(client[2]) or "") .. ":" .. tostring(R.Number(client[4]) or "")) or "session"
    local identity = build .. "\031" .. normalized(native.name) .. "\031" .. normalized(native.description)
        .. "\031" .. table.concat(dependencies, "\030")
    local known = relationProofs[native.id]
    if known and known.identity == identity then return known.matches, known.reason end
    local prior = budget.results[native.id]
    if prior and prior.identity == identity then return prior.matches, prior.reason end
    local function outcome(matches, reason)
        budget.results[native.id] = { identity = identity, matches = matches, reason = reason }
        return matches, reason
    end
    local loaded = native.criteriaCache or native.criteria
    if not (type(loaded) == "table" and loaded.available == true and loaded.complete == true and type(loaded.items) == "table") then loaded = nil end
    local nativeCount
    if loaded then nativeCount = R.Number(loaded.count) or #loaded.items
    else
        if budget.remaining <= 0 then return outcome(false, "Meta verification deferred by bounded read budget") end
        budget.remaining = budget.remaining - 1; count("relationship.criteria_reads", 1)
        local result = R.Call(GetAchievementNumCriteria, native.id)
        nativeCount = result and R.Number(result[1])
    end
    if not nativeCount then return outcome(false, "Native meta objective count is unavailable") end
    if nativeCount ~= number then return outcome(false, "Native meta child set differs") end
    if not loaded and budget.remaining < number then return outcome(false, "Meta verification deferred by bounded read budget") end
    local seen = {}
    for i = 1, number do
        local kind, asset, amount
        if loaded then
            local item = loaded.items[i]
            kind, asset, amount = R.Number(R.Field(item, "type")), R.ID(R.Field(item, "assetID")), R.Number(R.Field(item, "required"))
        else
            budget.remaining = budget.remaining - 1; count("relationship.criteria_reads", 1)
            local info = R.Call(GetAchievementCriteriaInfo, native.id, i)
            kind, asset, amount = info and R.Number(info[2]), info and R.ID(info[8]), info and R.Number(info[5])
        end
        if kind == nil or asset == nil or amount == nil then return outcome(false, "Native meta objectives are unavailable") end
        if kind ~= 8 or amount ~= 1 or not expected[asset] or seen[asset] then return outcome(false, "Native meta child requirements differ") end
        seen[asset] = true
    end
    local reason = "Explicit meta ID, exact native child identities, and verified underlying zone requirements"
    if #relationProofOrder >= 128 and not relationProofs[native.id] then relationProofs[table.remove(relationProofOrder, 1)] = nil end
    if not relationProofs[native.id] then relationProofOrder[#relationProofOrder + 1] = native.id end
    relationProofs[native.id] = { identity = identity, matches = true, reason = reason }
    return true, reason
end
function P.Build(page, nativeCatalog)
    local token = begin("presentation.build")
    local native, custom = nativeCatalog or ns.LegacyAdapter.Catalog(page), ns.CustomAchievementAdapter.Catalog()
    local model = { records = {}, byKey = {}, categories = {}, roots = {}, byCategory = {}, native = native, custom = custom,
        unmapped = {}, unmappedIDs = {}, duplicateKeys = {}, criteriaSearchScope = "Loaded criteria only", criteriaVersion = 0,
        _membership = {}, _counts = {}, _queries = {}, _queryOrder = {}, _queryVersion = 0,
        relationshipAudit = {}, relationships = {}, sourceRecords = { custom = {}, legacy = {} }, originalByKey = {} }
    model.unmappedRecords = model.unmapped
    local subjects, nativeCategories, classes = {}, {}, classDefinitions(native)
    for root, definitions in pairs(SUBJECTS) do
        for index, definition in ipairs(definitions) do
            subjects[root .. ":" .. definition[1]] = { name = definition[2], order = index }
        end
    end
    for i, definition in ipairs(classes.definitions) do
        subjects["classes:" .. definition[1]] = { name = definition[2], order = i }
    end
    local function category(key, name, parent, order)
        local cat = { key = key, name = name, parent = parent and parent.key, records = {}, children = {}, order = order }
        model.categories[#model.categories + 1] = cat; model.byCategory[key] = cat
        if parent then parent.children[#parent.children + 1] = cat else model.roots[#model.roots + 1] = cat end
        return cat
    end
    category("summary", "Summary")
    for _, root in ipairs(ROOTS) do category(root[1], root[2]) end
    for i, definition in ipairs(classes.definitions) do
        category("classes:" .. definition[1], definition[2], model.byCategory.classes, i)
    end
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
    -- Ancestry and category semantics are stable for this snapshot. Compute
    -- them once per category instead of walking the same path per record.
    local categoryToken = begin("category.generate")
    local context = { paths = {}, roots = {}, subjects = {}, names = {}, classes = classes }
    for _, cat in ipairs(native.categories or {}) do
        local path, names = ancestors(cat, nativeCategories), {}
        for _, ancestor in ipairs(path) do names[#names + 1] = ancestor.name end
        local root = categoryRoot(cat, nativeCategories, path)
        for _, name in ipairs(names) do
            if classes.names[normalized(name)] then root = "classes"; break end
        end
        context.paths[cat.key], context.names[cat.key], context.roots[cat.key] = path, names, root
        context.subjects[cat.key] = subjectFromNames(root, names, classes.names) or defaultSubject(root, names[1]) or false
        if root == "professions" and not context.subjects[cat.key] and cat.parent and nativeCategories[cat.parent] then
            local name = normalized(cat.name)
            if name ~= "primaryprofessions" and name ~= "primary" and name ~= "general" and
                name ~= "tradeskills" and name ~= "professions" and name ~= "secondaryprofessions" then
                local subject = "skill-" .. name
                subjects["professions:" .. subject] = { name = cat.name, order = 100 }
                context.subjects[cat.key] = subject
            end
        end
    end
    local function index(row, key, seen, totalsOnly)
        if not key or seen[key] then return end
        seen[key] = true
        local rows, totals = model._membership[key], model._counts[key]
        if not rows then
            rows, totals = {}, { completed = 0, total = 0, unknown = 0 }
            model._membership[key], model._counts[key] = rows, totals
        end
        if not totalsOnly then rows[#rows + 1] = row end
        totals.total = totals.total + 1
        if row.completed == true then totals.completed = totals.completed + 1
        elseif row.completed == nil then totals.unknown = totals.unknown + 1 end
    end
    local function targetCategory(root, subject)
        local key = subject and (root .. ":" .. subject)
        if not key or not subjects[key] then return model.byCategory[root] end
        return model.byCategory[key] or category(key, subjects[key].name, model.byCategory[root], subjects[key].order)
    end
    local nativeByID, combinedByKey, combinedSeen, originalsSeen = {}, {}, {}, {}
    for _, row in ipairs(native.records or {}) do
        if not nativeByID[row.id] then nativeByID[row.id] = row end
    end
    local function combine(original, candidate, reason)
        local row = copy(original)
        row.source, row.sourceType, row.sources = "combined", "unified_exploration", { custom = true, legacy = true }
        row.character, row.native = copy(original), copy(candidate)
        row.relationship = { characterKey = original.key, nativeKey = candidate.key, nativeID = candidate.id, evidence = reason }
        combinedByKey[original.key], combinedByKey[candidate.key] = row, row
        model.relationships[#model.relationships + 1] = row.relationship
    end
    local function audit(original, candidate, reason)
        model.relationshipAudit[#model.relationshipAudit + 1] = { characterKey = original.key,
            nativeKey = candidate.key, nativeID = candidate.id, reason = reason }
    end
    local relationToken, budget = begin("relationship.verify"), relationSnapshots[native]
    if not budget then
        budget = { remaining = math.min(256, P.MAX_RELATION_READS), results = {} }
        relationSnapshots[native] = budget
    end
    local candidates = arrayCopy(custom.records or {})
    local priority = { [802] = 1, [776] = 2, [855] = 3 }
    table.sort(candidates, function(a, b)
        local az, bz = a.exploration, b.exploration
        local av, bv = priority[az and az.zoneID] or 4, priority[bz and bz.zoneID] or 4
        if av == bv then return a.key < b.key end
        return av < bv
    end)
    for _, original in ipairs(candidates) do
        local zone = original.exploration
        local nativeID = zone and zone.kind == "zone" and (R.ID(zone.zoneID) or EXTRA_ZONE_IDS[original.savedKey])
        local candidate = nativeID and nativeByID[nativeID]
        if candidate and not combinedByKey[candidate.key] then
            local matches, reason = zoneRelationship(original, candidate, budget)
            if matches then
                combine(original, candidate, reason)
            else
                audit(original, candidate, reason)
            end
        end
    end
    local customByKey = {}
    for _, original in ipairs(custom.records or {}) do customByKey[original.key] = original end
    for _, savedKey in ipairs({"exploreEK", "exploreKal", "worldexplorer"}) do
        local original = customByKey["custom:" .. savedKey]
        local candidate = nativeByID[META_RELATIONS[savedKey].id]
        if original and candidate then
            local matches, reason = metaRelationship(original, candidate, customByKey, combinedByKey, budget)
            if matches then combine(original, candidate, reason) else audit(original, candidate, reason) end
        end
    end
    finish(relationToken)
    local function append(input)
        if originalsSeen[input.key] then model.duplicateKeys[#model.duplicateKeys + 1] = input.key; return end
        originalsSeen[input.key] = true
        local original = combinedByKey[input.key] or input
        if original.source == "combined" then
            if combinedSeen[original.key] then return end
            combinedSeen[original.key] = true
        end
        if model.byKey[original.key] then
            model.duplicateKeys[#model.duplicateKeys + 1] = original.key
            return
        end
        local row, root, subject = copy(original)
        local originalCategories = {}
        if row.source == "legacy" then
            local _, override
            root, override, subject = P.NativeCategory(row, nativeCategories, context)
            row.nativeCategory = original.category
            originalCategories = context.names[original.category] or {}
            if root == "unmapped" then
                root, subject = "feats", "other-legacy"
                row.navigationFallback = true
                model.unmapped[#model.unmapped + 1] = { id = row.id, key = row.key, name = row.name,
                    nativeCategory = original.category, reason = "Native subject metadata is unavailable or not classified" }
                model.unmappedIDs[#model.unmappedIDs + 1] = row.id
            else
                subject = nativeSubject(row, root, nativeCategories, subject, context)
                local class = classes.nativeIDs[row.id]
                if class and normalized(row.name) == class.name then root, subject = "classes", class.subject end
            end
        else
            root = row.customCategory or (row.category or ""):match("^custom%-category:(.+)$")
            row.customCategory = root
            if not model.byCategory[root] or model.byCategory[root].virtual then root = "general" end
            subject = customSubject(row, root)
            if root == "professions" and not subject then
                local skill = R.Text(row.skill) or R.Text((row.achievement or {}).skill)
                if skill and not PROFESSION_NAMES[normalized(skill)] then
                    subject = "skill-" .. normalized(skill)
                    subjects["professions:" .. subject] = { name = skill, order = 100 }
                end
            end
            if root == "classes" then
                local a = row.achievement or {}
                subject = classes.byID[row.classID or a.classID] or classes.byToken[(row.classToken or a.classToken or ""):upper()]
                    or classes.names[normalized(row.class or a.class or row.customSection or a.section)] or subject
            end
            originalCategories[#originalCategories + 1] = row.customSection or ""
            originalCategories[#originalCategories + 1] = row.customGeography or ""
        end
        local target = targetCategory(root, subject)
        row.unifiedRoot, row.rootCategory, row.subcategory = root, root, target.key ~= root and target.key or nil
        row.category = target.key
        row.categoryMetadata = { model.byCategory[root].name, target.name }
        for _, name in ipairs(originalCategories) do row.categoryMetadata[#row.categoryMetadata + 1] = name end
        row.searchText = ((row.name or "") .. " " .. (row.description or "") .. " " .. table.concat(row.categoryMetadata, " ")):lower()
        if row.source == "combined" then
            row.searchText = row.searchText .. " " .. (row.native.name or ""):lower() .. " " .. (row.native.description or ""):lower()
            for _, name in ipairs(context.names[row.native.category] or {}) do row.searchText = row.searchText .. " " .. name:lower() end
        end
        target.records[#target.records + 1] = row
        model.records[#model.records + 1] = row; model.byKey[row.key] = row
        row._presentationModel = model
        if row.source == "combined" then
            model.byKey[row.native.key], model.byKey[row.character.key] = row, row
            row.character._presentationModel, row.native._presentationModel = model, model
            row.nativeCategory = row.native.category
        end
        for _, component in ipairs(row.source == "combined" and {row.character, row.native} or {row}) do
            model.originalByKey[component.key] = component
            model.sourceRecords[component.source][#model.sourceRecords[component.source] + 1] = component
        end
        local indexed, ancestor = {}, target
        index(row, "summary", indexed)
        if row.source == "combined" then
            index(row.character, "custom", {}, true)
            model._membership.custom[#model._membership.custom + 1] = row
            index(row.native, "legacy", {}, true)
            model._membership.legacy[#model._membership.legacy + 1] = row
        else index(row, row.source, indexed) end
        while ancestor and not indexed[ancestor.key] do
            index(row, ancestor.key, indexed, ancestor ~= target)
            ancestor = model.byCategory[ancestor.parent]
        end
        if row.navigationFallback then index(row, "unmapped", indexed) end
        local source = model.byCategory[row.source]
        if source then source.records[#source.records + 1] = row end
        if row.source == "combined" then
            for _, key in ipairs({"custom", "legacy"}) do
                model.byCategory[key].records[#model.byCategory[key].records + 1] = row
            end
        end
        if row.source == "legacy" or row.source == "combined" then
            for _, cat in ipairs(context.paths[row.nativeCategory] or {}) do
                local alias = model.byCategory[cat.key]
                alias.aliasRows[row.key] = true; alias.aliasSubjects[target.key] = true; alias.aliasRoots[root] = true
                alias.records[#alias.records + 1] = row
                index(row, cat.key, indexed)
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
        table.sort(root.children, function(a, b)
            if a.order == b.order then return a.name < b.name end
            return a.order < b.order
        end)
    end
    model._indexedRecords = model.records
    count("category.records", #model.records)
    finish(categoryToken)
    finish(token)
    return model
end
-- Runtime data changes produce a new Build snapshot. Explicit callers that
-- edit a snapshot can drop its indexes rather than retain stale aggregates.
function P.Invalidate(model)
    model._indexedRecords, model._membership, model._counts = nil, nil, nil
    model._recent, model._summary, model._queries, model._queryOrder = nil, nil, nil, nil
    model._resolved, model._resolvedOrder = nil, nil
end
function P.CategoryKey(model, key)
    local cat = model.byCategory[key]
    return cat and (cat.aliasTarget or cat.key) or "summary"
end

local function indexed(model)
    return model._indexedRecords == model.records and model._membership ~= nil
end
local function rows(model, key, search, selectedFilter)
    local allowed, out = {}, {}
    local selected = model.byCategory[key]
    local function visit(cat)
        if not cat or allowed[cat.key] then return end
        allowed[cat.key] = true
        -- Lists use direct assignment. Descendant totals are a separate index.
    end
    local candidates
    if indexed(model) then candidates = model._membership[key] or {}
    else visit(model.byCategory[key]); candidates = model.records end
    count("search.rows", #candidates)
    for _, row in ipairs(candidates) do
        local component = row.source == "combined" and (key == "legacy" and row.native or row.character) or row
        local sourceMatches = selectedFilter == "all" or
            (selectedFilter == "complete" or selectedFilter == "completed") and component.completed == true or
            selectedFilter == "incomplete" and component.completed == false or
            (selectedFilter == "character" or selectedFilter == "characterachievements") and (row.source == "custom" or row.source == "combined") or
            (selectedFilter == "legacy" or selectedFilter == "legacychallenges") and (row.source == "legacy" or row.source == "combined")
        local searchMatches = search == "" or (row.searchText or ((row.name or "") .. " " .. (row.description or "")):lower()):find(search, 1, true) or
            row.criteriaSearchText and row.criteriaSearchText:find(search, 1, true)
        if (indexed(model) or key == "summary" or key == row.source or row.source == "combined" and (key == "custom" or key == "legacy") or allowed[row.category] or selected and selected.aliasRows and selected.aliasRows[row.key]) and
            sourceMatches and searchMatches then out[#out + 1] = row end
    end
    return out
end
function P.Rows(model, key, search, filter)
    local token = begin("search.filter")
    search = (search or ""):lower()
    local selectedFilter = normalized(filter or "All")
    local result
    if not indexed(model) then
        result = rows(model, key, search, selectedFilter)
    elseif search == "" and selectedFilter == "all" then
        result = arrayCopy(model._membership[key] or {})
    else
        if model._queryVersion ~= model.criteriaVersion then
            model._queries, model._queryOrder, model._queryVersion = {}, {}, model.criteriaVersion
        end
        local query = tostring(key or "") .. "\031" .. selectedFilter .. "\031" .. search
        local cached = model._queries[query]
        if not cached then
            cached = rows(model, key, search, selectedFilter)
            -- A typing session must not retain an unbounded set of arrays.
            if #model._queryOrder >= 32 then
                local oldest = table.remove(model._queryOrder, 1)
                model._queries[oldest] = nil
            end
            model._queries[query] = cached
            model._queryOrder[#model._queryOrder + 1] = query
        else count("search.cache_hits", 1) end
        result = arrayCopy(cached)
    end
    finish(token)
    return result
end
function P.Count(model, key)
    if indexed(model) then
        local totals = model._counts[key]
        return totals and totals.completed or 0, totals and totals.total or 0, totals and totals.unknown or 0
    end
    local selected, countRows = model.byCategory[key], {}
    for _, original in ipairs(model.records) do
        local row = original.source == "combined" and (key == "legacy" and original.native or key == "custom" and original.character or original) or original
        local matches = key == "summary" or key == row.source
        local cat, seen = model.byCategory[original.category], {}
        while cat and not seen[cat.key] do
            if cat.key == key then matches = true; break end
            seen[cat.key] = true; cat = model.byCategory[cat.parent]
        end
        if matches or selected and selected.aliasRows and selected.aliasRows[original.key] then countRows[#countRows + 1] = row end
    end
    local done, unknown = 0, 0
    for _, row in ipairs(countRows) do
        if row.completed == true then done = done + 1 elseif row.completed == nil then unknown = unknown + 1 end
    end
    return done, #countRows, unknown
end
function P.Recent(model, source, limit)
    if indexed(model) and model._recent and model._recent[source] then
        return arrayCopy(model._recent[source], limit and math.max(0, math.floor(limit)))
    end
    local rows = {}
    for _, record in ipairs(indexed(model) and model.sourceRecords and model.sourceRecords[source] or P.Rows(model, source)) do
        local row = record.source == "combined" and (source == "legacy" and record.native or record.character) or record
        local reliable = source == "custom" and R.Number(row.timestamp) and row.timestamp > 0 or
            source == "legacy" and R.Number(row.dateSort) and row.date ~= nil
        if row.completed == true and reliable then rows[#rows + 1] = row end
    end
    table.sort(rows, function(a, b)
        local av, bv = source == "custom" and a.timestamp or a.dateSort, source == "custom" and b.timestamp or b.dateSort
        if av == bv then return a.key < b.key end
        return av > bv
    end)
    if indexed(model) then
        model._recent = model._recent or {}
        model._recent[source] = rows
        return arrayCopy(rows, limit and math.max(0, math.floor(limit)))
    end
    if limit then while #rows > math.max(0, math.floor(limit)) do rows[#rows] = nil end end
    return rows
end
local function summaryCopy(summary)
    local result = { categories = {} }
    for _, source in ipairs({ "custom", "native" }) do
        result[source] = copy(summary[source])
        result[source].recent = arrayCopy(summary[source].recent)
    end
    for i, category in ipairs(summary.categories) do result.categories[i] = copy(category) end
    return result
end
function P.Summary(model)
    local token = begin("summary.refresh")
    if indexed(model) and model._summary then
        count("summary.cache_hits", 1)
        finish(token)
        return summaryCopy(model._summary)
    end
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
    if indexed(model) then model._summary = summary end
    finish(token)
    return summaryCopy(summary)
end
function P.SourceRecord(model, key)
    return model.originalByKey and model.originalByKey[key] or model.byKey[key]
end
function P.Criteria(row)
    if row.criteriaCache then return row.criteriaCache end
    if row.source == "combined" then
        local character, native = P.Criteria(row.character), P.Criteria(row.native)
        local data = { items = character.items, available = character.available, complete = character.complete,
            count = character.count, nativeCriteria = native,
            sections = { { source = "custom", record = row.character, data = character },
                { source = "legacy", record = row.native, data = native } } }
        row.criteriaCache = data
        row.criteriaSearchText = ((row.character.criteriaSearchText or "") .. " " .. (row.native.criteriaSearchText or ""))
        return data
    end
    local adapter = row.source == "legacy" and ns.LegacyAdapter or ns.CustomAchievementAdapter
    local result = R.Call(adapter.Criteria, row)
    local data = result and result[1]
    if type(data) ~= "table" then data = { items = {}, available = false, complete = false } end
    row.criteriaCache = data
    local model = row._presentationModel
    if model then model.criteriaVersion = (model.criteriaVersion or 0) + 1 end
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
    if not id then return nil end
    if not indexed(model) then return ns.LegacyAdapter.Resolve(tonumber(id)) end
    model._resolved, model._resolvedOrder = model._resolved or {}, model._resolvedOrder or {}
    local cached = model._resolved[key]
    if cached ~= nil then return cached or nil end
    count("native.resolve_reads", 1)
    local result = ns.LegacyAdapter.Resolve(tonumber(id))
    -- Expanded native meta cards can reference entries outside this catalog.
    -- Cache misses too, but keep a long click session bounded and snapshot-local.
    if #model._resolvedOrder >= 256 then
        local oldest = table.remove(model._resolvedOrder, 1)
        model._resolved[oldest] = nil
    end
    model._resolved[key] = result or false
    model._resolvedOrder[#model._resolvedOrder + 1] = key
    return result
end
