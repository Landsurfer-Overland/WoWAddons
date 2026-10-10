-- Presentation only. Existing definitions, progress evaluators and saved keys
-- remain authoritative. Old native imports stay in the standalone alpha UI.
local _, ns = ...
local FA, R = ns.FA, ns.LegacyReadOnly
local A = {}
ns.CustomAchievementAdapter = A
local function first(fn, ...)
    local result = R.Call(fn, ...)
    return result and result[1]
end
local TYPES = { standard = true, feat_of_strength = true, special = true, unknown = true }
local function achievementType(a, category)
    local explicit = R.Text(a.achievementType)
    if explicit and TYPES[explicit] then return explicit end
    -- This is the definition's authored category, not a navigation fallback.
    -- A zero-point record elsewhere remains a standard achievement.
    return category == "feats" and "feat_of_strength" or "standard"
end
local function explorationMetadata()
    local byKey, continents = {}, { ek = {}, kal = {} }
    for _, zone in ipairs(ns.EXPLORE or {}) do
        local key = R.Text(zone.key) or (R.ID(zone.id) and ("explore" .. zone.id))
        if key then
            byKey[key] = { zone = R.Text(zone.zone), geography = zone.cont == "ek" and "Eastern Kingdoms"
                or zone.cont == "kal" and "Kalimdor" or R.Text(zone.zone), continent = R.Text(zone.cont) }
            if continents[zone.cont] then continents[zone.cont][#continents[zone.cont] + 1] = "custom:" .. key end
        end
    end
    return byKey, continents
end
function A.Catalog()
    local d = FA.DB()
    local out = { categories = {}, records = {}, byKey = {}, points = 0, possiblePoints = 0,
        pointsAvailable = true, possiblePointsAvailable = true, available = true, partial = false }
    local labels, seen = {}, {}
    local zones, continents = explorationMetadata()
    for _, c in ipairs(FA.CATEGORIES) do labels[c.key] = c.label end
    for _, key in ipairs(FA.CATEGORY_ORDER) do
        local cat = { key = "custom-category:" .. key, customKey = key, parent = "custom", name = labels[key] or key, source = "custom", records = {} }
        out.categories[#out.categories + 1] = cat
        for _, section in ipairs(FA.CATEGORY_SECTIONS[key]) do
            for _, a in ipairs(section.list) do
                if not a.native and not seen[a.key] and first(FA.Available, a) == true then
                    seen[a.key] = true
                    local savedCompletion = rawget(d.done, a.key)
                    local timestamp = R.Number(savedCompletion)
                    local completed
                    if R.Safe(savedCompletion) then
                        if savedCompletion == nil then completed = false elseif timestamp then completed = true end
                    end
                    local progress = R.Call(a.progress)
                    local uniqueID = "custom:" .. a.key
                    local points, kind = R.Number(a.pts), achievementType(a, key)
                    local zone = zones[a.key]
                    local row = { key = uniqueID, uniqueID = uniqueID, source = "custom", sourceType = "custom_character", id = a.id,
                        savedKey = a.key, category = cat.key, customCategory = key, customSection = R.Text(section.title),
                        series = R.Text(a.series), skill = R.Text(a.skill), faction = R.Text(a.faction),
                        customGeography = R.Text(a.geography) or zone and zone.geography,
                        zoneName = zone and zone.zone, customContinent = zone and zone.continent,
                        achievement = a, name = a.name, description = a.desc or "",
                        completed = completed, completionState = R.CompletionState(completed), timestamp = timestamp,
                        scope = "Character", scopeType = "character", achievementType = kind,
                        achievementTypeEvidence = R.Text(a.achievementType) and "Explicit custom definition" or "Authored custom category",
                        icon = a.icon or ns.ICONS[a.id], pointValue = points, points = points, pts = points,
                        pointType = points ~= nil and (kind == "feat_of_strength" and points == 0 and "none" or "character") or "unknown",
                        current = progress and R.Number(progress[1]), required = progress and R.Number(progress[2]),
                        quantityText = progress and R.Text(progress[3]), tracked = d.tracked[a.key] == true,
                        reward = R.Text(a.rewardDescription) or R.Text(a.reward) }
                    row.progress = { current = row.current, required = row.required, quantityText = row.quantityText,
                        available = row.current ~= nil and row.required ~= nil }
                    if key == "exploration" then
                        if a.key == "exploreEK" then
                            row.customGeography, row.metaChildren = "Eastern Kingdoms", continents.ek
                        elseif a.key == "exploreKal" then
                            row.customGeography, row.metaChildren = "Kalimdor", continents.kal
                        elseif a.key == "worldexplorer" then
                            row.customGeography, row.metaChildren = "World Exploration", { "custom:exploreEK", "custom:exploreKal" }
                        end
                    end
                    if timestamp and type(date) == "function" then
                        row.date = first(date, "%m/%d/%y", timestamp)
                        row.completionDate = row.date
                    end
                    cat.records[#cat.records + 1] = row
                    out.records[#out.records + 1] = row
                    out.byKey[row.key] = row
                    out.possiblePoints = out.possiblePoints + (row.points or 0)
                    if row.completed then out.points = out.points + (row.points or 0) end
                    if row.completed == nil then out.pointsAvailable = false end
                    if row.points == nil then
                        out.possiblePointsAvailable = false
                        if row.completed then out.pointsAvailable = false end
                    end
                end
            end
        end
    end
    if not out.pointsAvailable then out.points = nil end
    if not out.possiblePointsAvailable then out.possiblePoints = nil end
    return out
end
function A.Criteria(row)
    local a = row.achievement
    local data = { items = {}, available = true, complete = true }
    if a.list then
        for i, name in ipairs(a.list) do
            if i > 256 then data.complete = false; break end
            data.items[#data.items + 1] = { name = name, completed = R.Bool(first(a.has, name)) }
        end
    elseif a.dynamicList then
        local list = first(a.dynamicList)
        if type(list) ~= "table" then data.available = false else
            for i, entry in ipairs(list) do
                if i > 256 then data.complete = false; break end
                data.items[#data.items + 1] = { name = R.Text(entry[1]) or "Criterion unavailable", completed = R.Bool(entry[2]) }
            end
        end
    elseif a.seen then
        local seen = first(a.seen)
        if type(seen) ~= "table" then data.available = false else
            for _, name in pairs(seen) do
                if #data.items >= 256 then data.complete = false; break end
                if R.Text(name) then data.items[#data.items + 1] = { name = name, completed = true } end
            end
            table.sort(data.items, function(x, y) return x.name < y.name end)
        end
    end
    if #data.items == 0 and row.required and row.required > 0 and row.current then
        data.items[1] = { name = row.name, current = row.current, required = row.required,
            quantityText = row.quantityText, completed = row.completed }
    elseif #data.items == 0 and not row.completed and not row.current then data.available = false end
    -- Earned series retain access to earlier tiers without changing their keys.
    if row.completed and a.series then
        for _, tier in ipairs(FA.SERIES[a.series] or {}) do
            if tier == a then break end
            if not tier.native then
                data.items[#data.items + 1] = { name = tier.name, link = "custom:" .. tier.key,
                    completed = R.Number(FA.DB().done[tier.key]) ~= nil }
            end
        end
    end
    data.count = #data.items
    row.criteria = data
    return data
end
function A.Track(row)
    if row and row.source == "custom" and row.achievement and not row.achievement.native then FA.ToggleTrack(row.achievement) end
end
function A.Statistics()
    local d, rows = FA.DB(), {}
    for _, stat in ipairs({ {"critters", "Critters loved"}, {"pests", "Pests slain"}, {"books", "Books read"},
        {"foods", "Different dishes eaten"}, {"drinks", "Different drinks"}, {"rares", "Rare enemies slain"}, {"bosses", "Bosses seen slain"} }) do
        rows[#rows + 1] = { stat[2], tostring(FA.Count(d[stat[1]])) }
    end
    rows[#rows + 1] = { "Fishing catches seen", tostring(d.fished or 0) }
    for _, section in ipairs(ns.STATS or {}) do
        rows[#rows + 1] = { section.title, "", heading = true }
        for _, stat in ipairs(section.list) do rows[#rows + 1] = { stat[2], first(FA.StatText, stat[1]) or "Unavailable" } end
    end
    return rows
end
