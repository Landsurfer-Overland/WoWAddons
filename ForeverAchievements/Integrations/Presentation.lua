local _, ns = ...
local P = {}
ns.LegacyPresentation = P
function P.Build(page, nativeCatalog)
    local native, custom = nativeCatalog or ns.LegacyAdapter.Catalog(page), ns.CustomAchievementAdapter.Catalog()
    local model = { records = {}, byKey = {}, categories = {}, byCategory = {}, native = native, custom = custom }
    local function category(cat)
        cat.children = {}; model.categories[#model.categories + 1] = cat; model.byCategory[cat.key] = cat
    end
    category({ key = "summary", name = "Summary", records = {} })
    category({ key = "legacy", name = "Legacy Challenges", source = "legacy", records = {} })
    category({ key = "custom", name = "Character Achievements", source = "custom", records = {} })
    for _, source in ipairs({ native, custom }) do
        for _, cat in ipairs(source.categories) do category(cat) end
        for _, row in ipairs(source.records) do model.records[#model.records + 1] = row; model.byKey[row.key] = row end
    end
    for _, cat in ipairs(model.categories) do
        if cat.parent then
            local parent = model.byCategory[cat.parent]
            if not parent or parent == cat or parent.source ~= cat.source then parent = model.byCategory[cat.source] end
            -- Reject malformed native cycles rather than losing navigation.
            local cursor, seen = parent, { [cat.key] = true }
            while cursor do
                if seen[cursor.key] then parent = model.byCategory[cat.source]; break end
                seen[cursor.key] = true; cursor = model.byCategory[cursor.parent]
            end
            cat.parent = parent.key; parent.children[#parent.children + 1] = cat
        end
    end
    return model
end
function P.Rows(model, key, search, filter)
    local allowed, out = {}, {}
    local function visit(cat)
        if not cat or allowed[cat.key] then return end
        allowed[cat.key] = true
        for _, child in ipairs(cat.children) do visit(child) end
    end
    visit(model.byCategory[key])
    search = (search or ""):lower()
    for _, row in ipairs(model.records) do
        if (key == "summary" or allowed[row.category]) and
            (filter == nil or filter == "All" or filter == "Complete" and row.completed == true or filter == "Incomplete" and row.completed == false) and
            (search == "" or (row.name .. " " .. row.description):lower():find(search, 1, true)) then out[#out + 1] = row end
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
function P.Criteria(row)
    return (row.source == "legacy" and ns.LegacyAdapter or ns.CustomAchievementAdapter).Criteria(row)
end
function P.Resolve(model, key)
    if model.byKey[key] then return model.byKey[key] end
    local id = key:match("^legacy:(%d+)$")
    return id and ns.LegacyAdapter.Resolve(tonumber(id))
end
