-- Read native evidence for custom achievements without changing native progress.
-- Source contract: Forever 1.60.1.70862. All reads remain capability guarded.
local _, ns = ...
local LAR, R = ns.LAR, ns.LegacyReadOnly
local E = { build = "1.60.1.70862", wrapped = 0 }
ns.NativeAchievementEvidence = E

local function normalize(value)
    value = R.Text(value)
    if value then return value:lower():gsub("^the%s+", ""):gsub("[%p%s]", "") end
end
local function info(id)
    local r = R.Call(GetAchievementInfo, id)
    if not r or R.ID(r[1]) ~= id or not R.Text(r[2]) then return nil end
    return { id = id, name = r[2], completed = R.Bool(r[4]), flags = R.Number(r[9]),
        earnedByMe = R.Bool(r[13]) }
end
info = LAR.CacheProgressRead("native-evidence-info", info)

local function criteria(id)
    local out, count = {}, R.Call(GetAchievementNumCriteria, id)
    count = count and R.Number(count[1])
    if not count or count < 0 or count ~= math.floor(count) or count > 256 then return out end
    for i = 1, count do
        local r = R.Call(GetAchievementCriteriaInfo, id, i)
        if r and R.Text(r[1]) then
            out[#out + 1] = { name = r[1], type = R.Number(r[2]), completed = R.Bool(r[3]),
                current = R.Number(r[4]), required = R.Number(r[5]), character = R.Text(r[6]),
                assetID = R.ID(r[8]), criteriaID = R.ID(r[10]) }
        end
    end
    return out
end
criteria = LAR.CacheProgressRead("native-evidence-criteria", criteria)

local function criterionEarnedHere(row)
    local identity = LAR.CharacterIdentity()
    if not identity or identity.verified ~= true or not row.character or row.character == "" then return false end
    local name = identity.name .. (identity.surname and identity.surname ~= "" and (" " .. identity.surname) or "")
    local earner = row.character:lower()
    return earner == name:lower() or earner == (name .. "-" .. identity.realm):lower()
end

local function dungeonCriteria()
    local out = {}
    for _, section in ipairs(ns.FOREVER_ACH or {}) do
        if section.title == "DUNGEONS" then
            for _, source in ipairs(section.list) do
                for _, id in ipairs(source.ids) do
                    local parent = info(id)
                    -- Old IDs can be reused: verify their identity first.
                    if parent and normalize(parent.name) == normalize(source.name) then
                        local account = R.HasFlag(parent.flags, ACHIEVEMENT_FLAGS_ACCOUNT)
                        -- Partial character-scoped criteria are usable before
                        -- the whole meta is earned. Account/other-character
                        -- completions alone cannot prove this character's kill.
                        local personal = parent.earnedByMe == true
                            or account == false and parent.completed == false
                        for _, row in ipairs(criteria(id)) do
                            row.achievementID, row.personal = id, personal or criterionEarnedHere(row)
                            row.scope = account == true and "account" or account == false and "character" or "unknown"
                            out[#out + 1] = row
                        end
                    end
                end
            end
        end
    end
    return out
end
dungeonCriteria = LAR.CacheProgressRead("native-dungeon-evidence", dungeonCriteria)
E.DungeonCriteria = dungeonCriteria

-- Observed in build 70862: one account criterion intentionally covers either
-- instance. The ID and label establish alternatives, not which one was run.
local sharedDungeonCriteria = {
    [62031] = { [19213] = true }, [64016] = { [117733] = true },
}
function E.MatchBoss(dungeon, boss, row)
    local key = dungeon.key or ("dungeon" .. tostring(dungeon.id))
    local shared = sharedDungeonCriteria[row.achievementID]
    if shared and shared[row.criteriaID] and normalize(row.name) == "ragefirechasmorhallofthanes" then
        return key == "dungeonThanes" or key == "dungeon629", "shared-dungeon"
    end
    if row.type == 0 and boss[2] and row.assetID == boss[2] then return true, "creature-id" end
    if normalize(row.name) == normalize(boss[1]) then return true, "boss-name" end
    if #dungeon.bosses == 1 and normalize(row.name) == normalize(dungeon.name) then return true, "dungeon-name" end
    return false
end

function E.Boss(dungeon, boss)
    if E.HistoricalBoss and E.HistoricalBoss(dungeon, boss) then return true end
    local record = E.PersonalBoss and E.PersonalBoss(dungeon, boss)
    if record then
        LAR.SetProgressEvidence(dungeon.key or ("dungeon" .. tostring(dungeon.id)), record.source, {
            achievementID = record.achievementID, criteriaID = record.criteriaID, inferred = true,
            nativeScope = record.nativeScope, attribution = record.kind, currentCharacter = true })
        return true
    end
    for _, row in ipairs(dungeonCriteria()) do
        local matches, kind = E.MatchBoss(dungeon, boss, row)
        if row.personal and row.completed == true and matches and kind ~= "shared-dungeon" then
            local exact = kind == "creature-id"
            -- Bounded inference: a completed named dungeon in Spelunker proves
            -- its sole authored final boss, never an entire multi-boss roster.
            LAR.SetProgressEvidence(dungeon.key or ("dungeon" .. tostring(dungeon.id)),
                exact and "native boss criterion" or "native named criterion (objective inference)", {
                    achievementID = row.achievementID, criteriaID = row.criteriaID, assetID = row.assetID,
                    criterion = row.name, inferred = not exact,
                    currentCharacter = true, clientBuild = E.build })
            return true
        end
    end
    return false
end

local function direct(a)
    local native = a.id and info(a.id)
    if native and native.completed == true and native.earnedByMe == true
        and normalize(native.name) == normalize(a.name) then
        LAR.SetProgressEvidence(a.key, "matching native achievement earned by this character", {
            achievementID = a.id, inferred = false, currentCharacter = true, clientBuild = E.build })
        return true
    end
    return false
end
for _, achievement in ipairs(LAR.ALL) do
    local a = achievement
    if not a.native and not a.unsupported and a.id and type(a.progress) == "function" then
        local original = a.progress
        a.progress = function()
            local r = R.Call(original)
            local current, required = r and R.Number(r[1]), r and R.Number(r[2])
            if current and required and required > 0 and current >= required then
                return current, required, r[3]
            end
            if direct(a) then
                required = required and required > 0 and required or 1
                return required, required
            end
            if r then return unpack(r, 1, r.n) end
            return nil, required
        end
        if type(a.has) == "function" then
            local originalHas = a.has
            a.has = function(name)
                for _, criterion in ipairs(a.list or {}) do
                    if name == criterion and direct(a) then return true end
                end
                return originalHas(name)
            end
        end
        E.wrapped = E.wrapped + 1
    end
end

function E.Report(input)
    input = (input or ""):match("^%s*(.-)%s*$")
    local build = R.Call(GetBuildInfo)
    local version = R.Call(C_AddOns and C_AddOns.GetAddOnMetadata or GetAddOnMetadata,
        "LegacyAchievementsReforged", "Version")
    print(LAR.TAG .. " API check: client=" .. tostring(build and build[1] or "unavailable")
        .. " build=" .. tostring(build and build[2] or "unavailable") .. "; addon="
        .. tostring(version and R.Text(version[1]) or "unavailable") .. "; reviewed=" .. E.build)
    if ns.AutomaticBossTracking then ns.AutomaticBossTracking.Report() end
    if input == "" then
        for _, api in ipairs({ { "GetAchievementInfo", GetAchievementInfo },
            { "GetAchievementCriteriaInfo", GetAchievementCriteriaInfo }, { "GetStatistic", GetStatistic },
            { "C_SkillInfo.GetSkillLineInfoByID", C_SkillInfo and C_SkillInfo.GetSkillLineInfoByID },
            { "C_SpellBook.IsSpellKnown", C_SpellBook and C_SpellBook.IsSpellKnown },
            { "C_QuestLog.GetAllCompletedQuestIDs", C_QuestLog and C_QuestLog.GetAllCompletedQuestIDs },
            { "C_Reputation.GetFactionDataByID", C_Reputation and C_Reputation.GetFactionDataByID } }) do
            print(LAR.TAG .. " " .. api[1] .. ": " .. (type(api[2]) == "function" and "available" or "unavailable"))
        end
        print(LAR.TAG .. " Use /lar apicheck <achievement key>|dungeons|native|all. This only reads progress.")
        return
    end
    LAR.WithProgressSnapshot(function()
        if input == "native" then
            for _, row in ipairs(dungeonCriteria()) do
                print(LAR.TAG .. " native=" .. row.achievementID .. " criterion=" .. tostring(row.criteriaID)
                    .. " " .. row.name .. " complete=" .. tostring(row.completed)
                    .. " personal=" .. tostring(row.personal) .. " scope=" .. row.scope .. " asset=" .. tostring(row.assetID))
            end
            return
        end
        local found = false
        for _, a in ipairs(LAR.ALL) do
            if not a.native and (input == "all" or a.key == input or input == "dungeons" and a.dungeon) then
                found = true
                local r = R.Call(a.progress)
                print(LAR.TAG .. " " .. a.key .. " (" .. a.name .. "): " .. tostring(r and r[1] or "unavailable")
                    .. "/" .. tostring(r and r[2] or "unavailable"))
                local evidence = LAR.ProgressEvidence(a.key)
                if evidence then
                    print(LAR.TAG .. " source=" .. evidence.source
                        .. "; inferred=" .. tostring(evidence.observations.inferred == true))
                end
                if a.dungeon and a.dungeon.stat then
                    local stat = R.Call(GetStatistic, a.dungeon.stat)
                    print(LAR.TAG .. " raw statistic " .. a.dungeon.stat .. "="
                        .. tostring(stat and (R.Text(stat[1]) or R.Number(stat[1])) or "unavailable"))
                end
                if a.dungeon then
                    for _, row in ipairs(dungeonCriteria()) do
                        local matches, kind = false, nil
                        for _, boss in ipairs(a.dungeon.bosses) do
                            local match, matchKind = E.MatchBoss(a.dungeon, boss, row)
                            if match then matches, kind = true, matchKind end
                        end
                        if matches then
                            print(LAR.TAG .. " native=" .. row.achievementID .. " criterion=" .. tostring(row.criteriaID)
                                .. " " .. row.name .. " complete=" .. tostring(row.completed)
                                .. " personal=" .. tostring(row.personal) .. " scope=" .. row.scope .. " asset=" .. tostring(row.assetID)
                                .. " match=" .. tostring(kind))
                            local corroborated = E.PersonalBoss and E.PersonalBoss(a.dungeon, a.dungeon.bosses[1])
                            local complete = r and R.Number(r[1]) and R.Number(r[2]) and r[2] > 0 and r[1] >= r[2]
                            if row.completed and not complete and not corroborated and (not row.personal or kind == "shared-dungeon") then
                                print(LAR.TAG .. " Shared native progress does not identify a personal kill."
                                    .. " Automatic encounter, loot and history tracking are used for personal credit.")
                            end
                        end
                    end
                end
            end
        end
        if not found then print(LAR.TAG .. " Unknown achievement key: " .. input) end
    end)
end
LAR.SLASH.apicheck = E.Report
