-- Account criteria can prove either of two dungeons without identifying the
-- current character. Record personal corroboration separately from that API.
local _, ns = ...
local LAR, R, E = ns.LAR, ns.LegacyReadOnly, ns.NativeAchievementEvidence
local D = {}
ns.DungeonRecovery = D
local function normalize(value)
    value = R.Text(value)
    return value and value:lower():gsub("^the%s+", ""):gsub("[%p%s]", "")
end
local function notify(message) print(LAR.TAG .. " " .. message) end
local function eligible(a)
    local available = a and R.Call(LAR.Available, a)
    return available and available[1] == true and not a.native and not a.unsupported
        and a.dungeon and #a.dungeon.bosses == 1
end
local function held(db, key)
    local corrections = R.Field(db, "completionCorrections")
    return corrections ~= nil and (type(corrections) ~= "table" or R.Field(corrections, key) ~= nil)
end
local function recordFor(key)
    local db = LAR.DB()
    if LAR.CharacterScope(db) ~= true then return nil end
    local identity = LAR.BindCharacter(db)
    local records = R.Field(db, "nativeDungeonEvidence")
    local record = R.Field(records, key)
    if not identity or R.Field(record, "version") ~= 1 or R.Field(record, "key") ~= key
        or not LAR.CharacterEvidenceMatches(R.Text(R.Field(record, "characterKey")), identity, db)
        or not R.ID(R.Field(record, "achievementID")) or not R.ID(R.Field(record, "criteriaID"))
        or not R.Text(R.Field(record, "source")) or not R.Text(R.Field(record, "bossName"))
        or not LAR.ValidCompletionTime(R.Field(record, "observedAt")) then return nil end
    local kind = R.Text(R.Field(record, "kind"))
    if kind ~= "player-confirmed" and kind ~= "native-event-in-instance" then return nil end
    return record
end
function E.PersonalBoss(dungeon, boss)
    local key = dungeon.key or ("dungeon" .. tostring(dungeon.id))
    local record = #dungeon.bosses == 1 and recordFor(key)
    return record and R.Text(record.bossName) == boss[1] and record or nil
end
local function store(a, row, kind, instanceName)
    if not eligible(a) or row.completed ~= true or not R.ID(row.criteriaID)
        or not E.MatchBoss(a.dungeon, a.dungeon.bosses[1], row) then return false end
    local db = LAR.DB()
    if held(db, a.key) or LAR.CharacterScope(db) ~= true then return false end
    local records = R.Field(db, "nativeDungeonEvidence")
    if records ~= nil and type(records) ~= "table" then return false end
    if records and R.Field(records, a.key) ~= nil then return recordFor(a.key) ~= nil, false end
    local clock = R.Call(time)
    local at = clock and LAR.ValidCompletionTime(clock[1])
    if not at then return false end
    local identity = LAR.BindCharacter(db)
    if not identity then return false end
    if not records then records = {}; db.nativeDungeonEvidence = records end
    records[a.key] = { version = 1, key = a.key, characterKey = identity.key,
        achievementID = row.achievementID, criteriaID = row.criteriaID, criterion = row.name,
        nativeScope = row.scope, kind = kind, observedAt = at, bossName = a.dungeon.bosses[1][1],
        instanceName = instanceName,
        source = kind == "player-confirmed" and "player-confirmed dungeon; native account criterion"
            or "native criterion event in matching dungeon (context inference)" }
    return true, true
end

function D.Recover(input)
    local key, confirmation = (input or ""):match("^%s*(%S+)%s*(.-)%s*$")
    local a = key and LAR.BY_KEY[key]
    if not eligible(a) or confirmation ~= "" and confirmation ~= "confirm" then
        notify("Use /lar recover <single-boss dungeon key> [confirm].")
        return false
    end
    if LAR.CharacterScope() ~= true then notify("Character identity is unavailable or tracking belongs to another character."); return false end
    local db = LAR.DB()
    if held(db, key) then notify("This achievement has a correction hold; recovery leaves it intact."); return false end
    if LAR.ValidCompletionTime(db.done[key]) then notify(a.name .. " is already completed on this character."); return true end
    return LAR.WithProgressSnapshot(function()
        local candidate
        for _, row in ipairs(E.DungeonCriteria()) do
            if row.completed == true and R.ID(row.criteriaID) and E.MatchBoss(a.dungeon, a.dungeon.bosses[1], row) then
                candidate = row; break
            end
        end
        if not candidate then notify("No completed matching native criterion is available. No recovery recorded."); return false end
        if confirmation ~= "confirm" then
            notify("Native criterion: " .. candidate.name .. " (" .. candidate.achievementID .. "/"
                .. candidate.criteriaID .. ", scope=" .. candidate.scope .. ").")
            notify("It does not establish which character or alternative dungeon completed it.")
            notify("If THIS character completed " .. a.name .. ", use /lar recover " .. key .. " confirm.")
            notify("Recovery records your confirmation; it does not claim a server-verified personal kill.")
            return false
        end
        if not store(a, candidate, "player-confirmed") then notify("Recovery could not be recorded; existing evidence was preserved."); return false end
        LAR.CheckAll(false, "PLAYER_CONFIRMED_DUNGEON_RECOVERY")
        notify("Recorded your completion of " .. a.name .. " on this character (player-confirmed recovery).")
        return true
    end)
end
LAR.SLASH.recover = D.Recover

-- A completion event while inside the matching instance can attribute a new
-- account criterion to this character. Merely visiting an already-credited
-- instance, login, or a generic update of an old true flag is not sufficient.
local seen, seenDB, seenCharacter = {}, nil, nil
local pending
local function context()
    local inside, instance = R.Call(IsInInstance), R.Call(GetInstanceInfo)
    local name, kind = instance and R.Text(instance[1]), instance and R.Text(instance[2])
    local zone = R.Call(GetRealZoneText)
    zone = zone and R.Text(zone[1])
    if name and zone and normalize(name) ~= normalize(zone) then return nil end
    if inside and inside[1] == true and name and (kind == "party" or kind == "raid") then return name end
end
function D.Observe(event, criteriaID)
    local db, identity = LAR.DB(), LAR.CharacterIdentity()
    if not identity or LAR.CharacterScope(db) ~= true then return end
    if db ~= seenDB or identity.key ~= seenCharacter then
        seen, seenDB, seenCharacter = {}, db, identity.key
    end
    local progress = event == "CRITERIA_UPDATE" or event == "CRITERIA_COMPLETE" or event == "CRITERIA_EARNED"
    local instanceName = progress and context() or nil
    if not pending or pending.db ~= db or pending.characterKey ~= identity.key then
        local work = { db = db, characterKey = identity.key, ids = {}, progress = progress,
            instanceName = instanceName, event = event }
        pending = work
        C_Timer.After(0.1, function()
            if pending ~= work then return end
            pending = nil
            local current = LAR.CharacterIdentity()
            if LAR.DB() ~= work.db or not current or current.key ~= work.characterKey
                or LAR.CharacterScope(work.db) ~= true then return end
            LAR.WithProgressSnapshot(function()
                local changed = false
                for _, row in ipairs(E.DungeonCriteria()) do
                    local id = R.ID(row.criteriaID)
                    if id then
                        local key = row.achievementID .. ":" .. id
                        local newlyComplete = row.completed == true and (seen[key] == false or work.ids[id])
                        if work.progress and work.instanceName and not work.conflictingContext and newlyComplete then
                            for _, a in ipairs(LAR.ALL) do
                                if eligible(a) and normalize(a.dungeon.name) == normalize(work.instanceName)
                                    and E.MatchBoss(a.dungeon, a.dungeon.bosses[1], row) then
                                    local _, added = store(a, row, "native-event-in-instance", work.instanceName)
                                    changed = added == true or changed
                                end
                            end
                        end
                        if row.completed ~= nil then seen[key] = row.completed end
                    end
                end
                if changed then LAR.CheckAll(false, "PERSONAL_NATIVE_DUNGEON_EVENT") end
            end)
        end)
    else
        pending.progress = pending.progress or progress
        if instanceName then
            if pending.instanceName and normalize(pending.instanceName) ~= normalize(instanceName) then pending.conflictingContext = true end
            pending.instanceName = pending.instanceName or instanceName
        end
    end
    if event == "CRITERIA_COMPLETE" and R.ID(criteriaID) then pending.ids[criteriaID] = true end
end
local frame = CreateFrame("Frame")
D.frame = frame
for _, event in ipairs({ "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "CRITERIA_UPDATE", "CRITERIA_COMPLETE", "CRITERIA_EARNED" }) do
    pcall(frame.RegisterEvent, frame, event)
end
frame:SetScript("OnEvent", function(_, event, ...) D.Observe(event, ...) end)
