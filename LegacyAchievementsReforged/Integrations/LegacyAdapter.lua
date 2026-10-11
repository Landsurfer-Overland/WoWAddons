-- Read-only Forever backend. Never select native categories, set native search,
-- update providers, grant achievements, spend traits, or claim rewards here.
local _, ns = ...
local R = {}
ns.LegacyReadOnly = R
function R.Safe(v)
    if type(issecretvalue) == "function" then
        local ok, secret = pcall(issecretvalue, v)
        if not ok or secret then return false end
    end
    return true
end
function R.Number(v)
    if R.Safe(v) and type(v) == "number" and v == v and v > -math.huge and v < math.huge then return v end
end
function R.ID(v)
    local n = R.Number(v)
    if n and n > 0 and n == math.floor(n) then return n end
end
function R.Text(v)
    if R.Safe(v) and type(v) == "string" then return v end
end
function R.Bool(v)
    if R.Safe(v) and type(v) == "boolean" then return v end
end
-- Flags are an independent property: neither points nor source establish
-- account scope or Feat of Strength classification. Reject malformed masks.
function R.HasFlag(flags, mask)
    flags, mask = R.Number(flags), R.ID(mask)
    if not flags or flags < 0 or flags ~= math.floor(flags) or not mask then return nil end
    local bitValue = mask
    while bitValue > 1 and bitValue % 2 == 0 do bitValue = bitValue / 2 end
    if bitValue ~= 1 then return nil end
    return math.floor(flags / mask) % 2 == 1
end
function R.CompletionState(completed)
    if completed == true then return "complete" end
    if completed == false then return "incomplete" end
    return "unknown"
end
function R.Call(fn, ...)
    if not R.Safe(fn) or type(fn) ~= "function" then return nil end
    local function pack(...) return { n = select("#", ...), ... } end
    local result = pack(pcall(fn, ...))
    if not result[1] then return nil end
    local values = { n = result.n - 1 }
    for i = 2, result.n do if R.Safe(result[i]) then values[i - 1] = result[i] end end
    return values
end
function R.Field(object, key)
    if not R.Safe(object) or (type(object) ~= "table" and type(object) ~= "userdata") then return nil end
    local ok, value = pcall(function() return object[key] end)
    if ok and R.Safe(value) then return value end
end
function R.Method(object, method, ...)
    return R.Call(R.Field(object, method), object, ...)
end

local A = { MAX_CATEGORIES = 256, MAX_RECORDS = 2500, MAX_CRITERIA = 256, MAX_CATEGORY_DEPTH = 32 }
ns.LegacyAdapter = A
local function constant(key, fallback)
    local constants = R.Field(Constants, "LegacyConsts")
    return R.ID(R.Field(constants, key)) or fallback
end
function A.Points(id)
    local r = R.Call(R.Field(C_Traits, "GetTraitCurrencyForAchievement"),
        constant("LEGACY_POINTS_TRAIT_CURRENCY_ID", 4225), id)
    local n = r and R.Number(r[1])
    if n and n >= 0 then return n end -- nil means unavailable, distinct from zero
end
function A.TotalPoints()
    local r = R.Call(R.Field(C_MajorFactions, "GetCurrentRenownLevel"),
        constant("LEGACY_REWARD_TRACK_FACTION_ID", 2802))
    local value = r and R.Number(r[1])
    if value and value >= 0 then return value end
end
local function scope(flags)
    local account = R.HasFlag(flags, ACHIEVEMENT_FLAGS_ACCOUNT)
    if account == true then return "Account", "account" end
    if account == false then return "Character", "character" end
    return "Scope unavailable", "unknown"
end
local function completionProvenance(row, wasEarnedByMe)
    row.wasEarnedByMe = wasEarnedByMe
    if row.completed == false then
        row.completionScope, row.completionDetail = "incomplete", "Not completed"
        row.completedOnCurrentCharacter, row.completedByOtherCharacter = false, false
    elseif row.completed == true then
        row.completedOnCurrentCharacter = wasEarnedByMe
        -- Build 70338's LegacyChallengeDetailPane reads this exact thirteenth
        -- GetAchievementInfo return to distinguish accomplishments by others.
        if wasEarnedByMe == true then
            row.completionScope, row.completionDetail = "current_character", "Completed on this character"
            row.completedByOtherCharacter = false
        elseif row.scopeType == "account" then
            row.completionScope, row.completionDetail = "native_account", "Legacy challenge completed account-wide"
            if wasEarnedByMe == false then row.completedByOtherCharacter = true end
        elseif wasEarnedByMe == false then
            row.completionScope, row.completionDetail = "other_character", "Completed by another character"
            row.completedByOtherCharacter = true
        else
            row.completionScope, row.completionDetail = "unknown", "Completion scope unavailable"
        end
    else
        row.completionScope, row.completionDetail = "unknown", "Completion unavailable"
    end
    if row.scopeType == "account" then row.nativeAccountCompleted = row.completed
    elseif row.scopeType == "character" then row.nativeAccountCompleted = false end
end
-- Build 70338's AchievementUtil identifies Feats through native category 81
-- or guild category 15093 and their ancestors. Read the same category contract
-- with cycle/depth bounds; never classify from a zero point value, a Legacy
-- source, account scope, or our navigation fallback under Feats of Strength.
function A.AchievementType(id, categoryID, categories, categoryReader)
    categoryID = R.ID(categoryID)
    if not categoryID then
        local result = R.Call(GetAchievementCategory, id)
        categoryID = result and R.ID(result[1])
    end
    if not categoryID then return "unknown", "Native category unavailable" end
    local visited = {}
    for _ = 1, A.MAX_CATEGORY_DEPTH do
        if categoryID == 81 or categoryID == 15093 then return "feat_of_strength", "Native Feats of Strength category" end
        if visited[categoryID] then return "unknown", "Native category ancestry is cyclic" end
        visited[categoryID] = true
        local category = categories and categories[categoryID]
        local parent
        if category and category.metadataAvailable then
            parent = R.Number(category.parentID)
        else
            local info
            if categoryReader then info = categoryReader(categoryID)
            else info = R.Call(GetCategoryInfo, categoryID) end
            if not info or not R.Text(info[1]) then return "unknown", "Native category metadata unavailable" end
            parent = R.Number(info[2])
        end
        if parent == -1 or parent == 0 then return "standard", "Native category is outside Feats of Strength" end
        categoryID = R.ID(parent)
        if not categoryID then return "unknown", "Native category ancestry unavailable" end
    end
    return "unknown", "Native category ancestry exceeds inspection bound"
end
local function record(info, category, categoryID, categories, typeCache, categoryReader)
    local id = info and R.ID(info[1])
    if not id then return nil end
    local flags = R.Number(info[9])
    local completed = R.Bool(info[4])
    local month, day, year = R.Number(info[5]), R.Number(info[6]), R.Number(info[7])
    local completionDate, dateSort, completionDateParts
    if completed and month and month == math.floor(month) and month >= 1 and month <= 12 and
        day and day == math.floor(day) and day >= 1 and year and year == math.floor(year) and year >= 0 and year <= 9999 then
        local fullYear = year < 100 and year + 2000 or year
        local leap = fullYear % 4 == 0 and (fullYear % 100 ~= 0 or fullYear % 400 == 0)
        local maxDays = ({ 31, leap and 29 or 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 })[month]
        if day <= maxDays then
            completionDate = ("%d/%d/%02d"):format(month, day, year % 100)
            dateSort = fullYear * 10000 + month * 100 + day
            completionDateParts = { year = fullYear, month = month, day = day }
        end
    end
    local key, points = "legacy:" .. id, A.Points(id)
    local scopeLabel, scopeType = scope(flags)
    -- Category classification is shared within one catalog snapshot, including
    -- unavailable ancestry. A later catalog/Resolve still reads live metadata.
    local knownCategoryID = R.ID(categoryID)
    local cachedType = typeCache and knownCategoryID and typeCache[knownCategoryID]
    local achievementType, typeEvidence
    if cachedType then achievementType, typeEvidence = cachedType[1], cachedType[2]
    else
        achievementType, typeEvidence = A.AchievementType(id, categoryID, categories, categoryReader)
        if typeCache and knownCategoryID then typeCache[knownCategoryID] = { achievementType, typeEvidence } end
    end
    local row = { key = key, uniqueID = key, source = "legacy", sourceType = "native_legacy", id = id, category = category,
        name = R.Text(info[2]) or ("Legacy Challenge " .. id), description = R.Text(info[8]) or "Description unavailable.",
        completed = completed, completionState = R.CompletionState(completed),
        date = completionDate, completionDate = completionDate, dateSort = dateSort, completionDateParts = completionDateParts,
        flags = flags, scope = scopeLabel, scopeType = scopeType,
        achievementType = achievementType, achievementTypeEvidence = typeEvidence,
        pointType = points ~= nil and (points > 0 and "legacy" or "none") or "unknown",
        pointValue = points, points = points, pts = points,
        nativeAchievementPoints = R.Number(info[3]), progress = { available = false },
        icon = R.ID(info[10]) or R.Text(info[10]), reward = R.Text(info[11]) }
    completionProvenance(row, R.Bool(info[13]))
    return row
end
function A.Resolve(id)
    id = R.ID(id)
    return id and record(R.Call(GetAchievementInfo, id))
end
function A.Criteria(achievement)
    local data = { items = {}, available = false, complete = false }
    local result = R.Call(GetAchievementNumCriteria, achievement.id)
    local count = result and R.Number(result[1])
    if not count or count < 0 or count ~= math.floor(count) then
        achievement.criteria = data
        achievement.progress = { available = false }
        return data
    end
    data.available = true
    data.complete = count <= A.MAX_CRITERIA
    data.count = count
    for i = 1, math.min(count, A.MAX_CRITERIA) do
        local r = R.Call(GetAchievementCriteriaInfo, achievement.id, i)
        if not r or not R.Text(r[1]) then
            data.complete = false
            data.items[#data.items + 1] = { name = "Criterion " .. i .. " unavailable", unavailable = true }
        else
            local item = { name = R.Text(r[1]), type = R.Number(r[2]), completed = R.Bool(r[3]),
                current = R.Number(r[4]), required = R.Number(r[5]), flags = R.Number(r[7]),
                assetID = R.ID(r[8]), quantityText = R.Text(r[9]), criteriaID = R.ID(r[10]) }
            if item.type == 8 and item.assetID then item.link = "legacy:" .. item.assetID end
            data.items[#data.items + 1] = item
        end
    end
    -- Native completion always comes from GetAchievementInfo, never from these
    -- criteria, including zero-criteria challenges and account/character metas.
    achievement.criteria = data
    achievement.progress = { available = data.available, complete = data.complete, criteria = data.items, count = data.count }
    return data
end
local function providerRecords(page)
    local pane = R.Field(page, "DetailPane")
    local box = R.Field(pane, "ScrollBox")
    local result = R.Method(box, "GetDataProvider")
    local provider = result and result[1] or R.Field(box, "dataProvider")
    if not provider then
        local view = R.Field(box, "view")
        result = R.Method(view, "GetDataProvider")
        provider = result and result[1] or R.Field(view, "dataProvider")
    end
    result = R.Method(provider, "GetCollection")
    local collection = result and result[1] or R.Field(provider, "collection")
    if type(collection) ~= "table" then return {} end
    local ids, seen = {}, {}
    for i = 1, A.MAX_RECORDS do
        local row = rawget(collection, i)
        if row == nil then break end
        local id = R.ID(R.Field(row, "achievementID")) or R.ID(R.Field(row, "challengeID")) or R.ID(R.Field(row, "id"))
        if id and not seen[id] then ids[#ids + 1] = id; seen[id] = true end
    end
    return ids
end
function A.Catalog(page)
    local perf = ns.LegacyPerf
    local token = perf and perf.Begin and perf.Begin("native.enumerate")
    local out = { categories = {}, records = {}, byKey = {}, duplicates = {}, duplicateIDs = {},
        partial = false, available = false, points = A.TotalPoints(), attemptedRecords = 0, attemptedCategories = 0 }
    local function readRecord(...)
        if out.attemptedRecords >= A.MAX_RECORDS then out.partial = true; return nil end
        out.attemptedRecords = out.attemptedRecords + 1
        return R.Call(GetAchievementInfo, ...)
    end
    local categoryInfoCache = {}
    local function readCategory(id)
        local cached = categoryInfoCache[id]
        if cached ~= nil then return cached or nil end
        if out.attemptedCategories >= A.MAX_CATEGORIES then out.partial = true; return nil end
        out.attemptedCategories = out.attemptedCategories + 1
        local info = R.Call(GetCategoryInfo, id)
        -- Failed metadata shares the same snapshot lifetime as successful
        -- reads. Distinct provider IDs cannot multiply ancestry work unboundedly.
        categoryInfoCache[id] = info or false
        return info
    end
    local listResult = R.Call(GetCategoryList)
    local list = listResult and listResult[1]
    local categories = {}
    if type(list) == "table" then
        if next(list) == nil then out.available = true end
        for i = 1, A.MAX_CATEGORIES do
            local id = R.ID(rawget(list, i))
            if not id then break end
            if not categories[id] then
                local info = readCategory(id)
                local parent = info and R.Number(info[2])
                local cat = { key = "legacy-category:" .. id, id = id, source = "legacy",
                    name = info and R.Text(info[1]) or ("Category " .. id),
                    parent = parent and parent > 0 and ("legacy-category:" .. parent) or "legacy",
                    parentID = parent, flags = info and R.Number(info[3]), metadataAvailable = info ~= nil and R.Text(info[1]) ~= nil, records = {} }
                categories[id] = cat
                out.categories[#out.categories + 1] = cat
            end
        end
        if rawget(list, A.MAX_CATEGORIES + 1) then out.partial = true end
    end
    local seen, typeCache = {}, {}
    local function append(a, cat)
        if not a then return end
        if seen[a.key] then
            if #out.duplicates < A.MAX_RECORDS then
                out.duplicates[#out.duplicates + 1] = { id = a.id, key = a.key, category = cat.key }
                out.duplicateIDs[#out.duplicateIDs + 1] = a.id
            end
            return
        end
        seen[a.key] = true
        out.records[#out.records + 1] = a
        out.byKey[a.key] = a
        cat.records[#cat.records + 1] = a
    end
    for _, cat in ipairs(out.categories) do
        local n = R.Call(GetCategoryNumAchievements, cat.id)
        local count = n and R.Number(n[1])
        cat.reportedTotal = count
        cat.reportedCompleted = n and R.Number(n[2])
        cat.reportedIncomplete = n and R.Number(n[3])
        n = count
        if not n or n < 0 or n ~= math.floor(n) then out.partial = true; n = 0 else out.available = true end
        if not cat.metadataAvailable then out.partial = true end
        -- Duplicate and unavailable reads consume the same global budget as
        -- unique records; overlapping categories must not multiply API work.
        local remaining = A.MAX_RECORDS - out.attemptedRecords
        if n > remaining then out.partial = true end
        for index = 1, math.min(n, remaining) do
            local a = record(readRecord(cat.id, index), cat.key, cat.id, categories, typeCache, readCategory)
            if not a then out.partial = true end
            append(a, cat)
        end
    end
    if #out.records == 0 and (not out.available or out.partial) then
        local cat = { key = "legacy-current", parent = "legacy", name = "Current native category", source = "legacy", records = {} }
        -- The passive provider contains IDs only. Recover documented category
        -- metadata where available so fallback records need not all be unmapped.
        -- This reads ancestry without selecting a category or refreshing native UI.
        local unavailableCategories = {}
        local function fallbackCategory(id, visiting)
            if categories[id] then return categories[id] end
            if unavailableCategories[id] then return nil end
            if #out.categories >= A.MAX_CATEGORIES then return nil end
            visiting = visiting or {}
            if visiting[id] then return nil end
            visiting[id] = true
            local info = readCategory(id)
            if not info or not R.Text(info[1]) then unavailableCategories[id] = true; return nil end
            local parent = R.Number(info[2])
            local result = { key = "legacy-category:" .. id, id = id, source = "legacy", name = R.Text(info[1]),
                parent = parent and parent > 0 and ("legacy-category:" .. parent) or "legacy",
                parentID = parent, metadataAvailable = true, records = {} }
            categories[id] = result; out.categories[#out.categories + 1] = result
            if parent and parent > 0 then fallbackCategory(parent, visiting) end
            return result
        end
        for _, id in ipairs(providerRecords(page)) do
            if out.attemptedRecords >= A.MAX_RECORDS then out.partial = true; break end
            local info = readRecord(id)
            local categoryResult = R.Call(GetAchievementCategory, id)
            local categoryID = categoryResult and R.ID(categoryResult[1])
            local target = categoryID and fallbackCategory(categoryID) or cat
            target = target or cat
            local a = record(info, target.key, categoryID, categories, typeCache, readCategory)
            append(a, target)
        end
        if #cat.records > 0 then out.categories[#out.categories + 1] = cat end
        out.partial = true
    end
    if #out.records > 0 then out.available = true end
    if out.partial then
        out.notice = #out.records == 0 and "Native challenges unavailable. Character achievements remain available."
            or "Native catalog is partial; unavailable records are not counted. Reopen after selecting a native category if needed."
    end
    if perf and perf.Count then perf.Count("native.info_attempts", out.attemptedRecords) end
    if perf and perf.Count then perf.Count("native.category_attempts", out.attemptedCategories) end
    if perf and perf.Finish then perf.Finish(token) end
    return out
end
