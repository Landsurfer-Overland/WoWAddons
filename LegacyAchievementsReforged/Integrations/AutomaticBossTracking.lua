-- Automatic personal boss evidence. Shared account checkboxes are not kills.
local _, ns = ...
local LAR, R, E = ns.LAR, ns.LegacyReadOnly, ns.NativeAchievementEvidence
local B = { state = "Waiting for native statistics", attempts = 0, attemptLimit = 3, counters = {}, scanned = 0 }
ns.AutomaticBossTracking = B
local function normalize(value)
    value = R.Text(value)
    return value and value:lower():gsub("^the%s+", ""):gsub("[%p%s]", "")
end
local function key(dungeon, boss)
    return (dungeon.key or ("dungeon" .. tostring(dungeon.id))) .. ":" .. boss[1]
end
local labels = {}
local function label(value, target)
    value = normalize(value)
    labels[value] = labels[value] or {}
    labels[value][target] = true
end
for _, a in ipairs(LAR.ALL) do
    if not a.native and not a.unsupported and a.dungeon then
        local d = a.dungeon
        for _, boss in ipairs(d.bosses) do
            local target = key(d, boss)
            -- Exact semantic labels only. No substring/fuzzy matching of deaths,
            -- wipes, unrelated difficulty totals or similarly named encounters.
            label(boss[1] .. " Kills (" .. d.name .. ")", target)
            label(boss[1] .. " Kills (" .. d.name:gsub("^[Tt]he%s+", "") .. ")", target)
            if d.stat or #(ns.BOSS_STATS[boss[1]] or {}) > 0 then label(boss[1] .. " Kills", target) end
        end
    end
end

function B.Discover()
    if B.state == "Ready" then return true end
    if B.attempts >= B.attemptLimit then return false end
    if InCombatLockdown and InCombatLockdown() then B.deferred = true; return false end
    B.attempts = B.attempts + 1
    local result = R.Call(GetStatisticsCategoryList)
    local categories = result and result[1]
    if type(categories) ~= "table" or not R.Safe(categories) or #categories == 0 then
        B.state = "Native statistics catalog unavailable"
        return false
    end
    local seen, scanned, partial = {}, 0, #categories > 256
    for i = 1, math.min(#categories, 256) do
        local category = R.ID(categories[i])
        local count = category and R.Call(GetCategoryNumAchievements, category)
        count = count and R.Number(count[1])
        if count and count >= 0 and count == math.floor(count) then
            local budget = 2500 - scanned
            if count > budget then partial = true end
            for index = 1, math.min(count, budget) do
                scanned = scanned + 1
                local data = R.Call(GetAchievementInfo, category, index)
                local id, name = data and R.ID(data[1]), data and R.Text(data[2])
                if not id or not name then partial = true end
                local matches = name and labels[normalize(name)]
                if id and not seen[id] and matches and R.HasFlag(data[9], ACHIEVEMENT_FLAGS_ACCOUNT) == false then
                    seen[id] = true
                    for target in pairs(matches) do
                        B.counters[target] = B.counters[target] or {}
                        B.counters[target][id] = { id = id, name = name }
                    end
                end
            end
        else partial = true end
        if scanned >= 2500 then if i < #categories then partial = true end; break end
    end
    B.scanned = scanned
    if scanned == 0 then B.state = "Native statistics catalog not ready"; return false end
    B.state = partial and "Partial native statistics catalog" or "Ready"
    LAR.CheckAll(true, "AUTOMATIC_BOSS_HISTORY_DISCOVERY")
    return not partial
end

local function count(id)
    local data = R.Call(GetAchievementInfo, id)
    if not data or R.ID(data[1]) ~= id or R.HasFlag(data[9], ACHIEVEMENT_FLAGS_ACCOUNT) ~= false then return nil end
    local name = R.Text(data[2])
    local value = name and LAR.StatisticCount(id)
    return value, name
end
count = LAR.CacheProgressRead("automatic-boss-counter", count)
function E.HistoricalBoss(dungeon, boss)
    for id, counter in pairs(B.counters[key(dungeon, boss)] or {}) do
        local value, name = count(id)
        if name == counter.name and value and value > 0 then
            LAR.SetProgressEvidence(dungeon.key or ("dungeon" .. tostring(dungeon.id)),
                "discovered personal boss-kill statistic", { statisticID = id, counter = name, kills = value,
                    currentCharacter = true, inferred = false })
            return true
        end
    end
    return false
end

-- Capture the actual creature GUID/name when readable, including corpse target
-- names after combat. A matching loot-source GUID proves more than a vanished
-- target. No combat log access or secret-value coercion is used.
local units, order, actorDB, actorKey = {}, {}, nil, nil
local function actor()
    local db, identity = LAR.DB(), LAR.CharacterIdentity()
    if not identity or LAR.CharacterScope(db) ~= true then return false end
    if actorDB ~= db or actorKey ~= identity.key then
        units, order, actorDB, actorKey = {}, {}, db, identity.key
    end
    return true
end
function B.Remember(unit)
    if not actor() then return end
    local guid, name = R.Call(UnitGUID, unit), R.Call(UnitName, unit)
    guid, name = guid and R.Text(guid[1]), name and R.Text(name[1])
    if not guid or not name or not LAR.BOSS_BY_NAME[name] then return end
    local id = R.Call(LAR.NpcID, guid)
    id = id and R.ID(id[1])
    if not id then return end
    if not units[guid] then order[#order + 1] = guid end
    units[guid] = { id = id, name = name }
    if #order > 32 then units[table.remove(order, 1)] = nil end
end
function B.Loot()
    if not actor() then return end
    B.Remember("target")
    for i = 1, 5 do B.Remember("boss" .. i) end
    local result = R.Call(GetNumLootItems)
    local slots = result and R.Number(result[1])
    if not slots or slots < 0 or slots ~= math.floor(slots) then return end
    for slot = 1, math.min(slots, 64) do
        local sources = R.Call(GetLootSourceInfo, slot)
        if sources then
            for i = 1, math.min(sources.n, 128), 2 do
                local guid = R.Text(sources[i])
                local boss = guid and units[guid]
                if boss then
                    LAR.NoteBossKill(boss.id, boss.name, { source = "boss corpse loot source (loot-eligibility inference)",
                        creatureID = boss.id, inferred = true })
                end
            end
        end
    end
end
function B.Report()
    local counters = 0
    for _, matches in pairs(B.counters) do for _ in pairs(matches) do counters = counters + 1 end end
    print(LAR.TAG .. " Automatic boss history: " .. B.state .. "; " .. B.scanned
        .. " records scanned; " .. counters .. " mapped counter references; " .. B.attempts .. "/" .. B.attemptLimit .. " discovery attempts.")
end

local frame = CreateFrame("Frame")
B.frame = frame
for _, event in ipairs({ "PLAYER_LOGIN", "ADDON_LOADED", "PLAYER_REGEN_ENABLED",
    "PLAYER_TARGET_CHANGED", "INSTANCE_ENCOUNTER_ENGAGE_UNIT", "LOOT_READY", "LOOT_OPENED", "PLAYER_ENTERING_WORLD" }) do
    pcall(frame.RegisterEvent, frame, event)
end
frame:SetScript("OnEvent", function(_, event, addon)
    if event == "PLAYER_LOGIN" then
        for _, delay in ipairs({ 1, 5, 15 }) do C_Timer.After(delay, B.Discover) end
    elseif event == "ADDON_LOADED" then
        -- One extra readiness opportunity if native UI APIs appear after login.
        -- Progress updates only re-read mapped counters via the core evaluator.
        if not B.nativeLoadRetried and B.state ~= "Ready"
            and (addon == "Blizzard_AchievementUI" or addon == "Blizzard_LegacySystem") then
            B.nativeLoadRetried, B.attemptLimit = true, 4
            B.Discover()
        end
    elseif event == "PLAYER_REGEN_ENABLED" then
        if B.deferred then B.deferred = false; B.Discover() end
        B.Remember("target")
    elseif event == "LOOT_READY" or event == "LOOT_OPENED" then B.Loot()
    elseif event == "PLAYER_TARGET_CHANGED" then B.Remember("target")
    elseif event == "INSTANCE_ENCOUNTER_ENGAGE_UNIT" then for i = 1, 5 do B.Remember("boss" .. i) end
    elseif event == "PLAYER_ENTERING_WORLD" then units, order = {}, {}; B.Remember("target") end
end)
