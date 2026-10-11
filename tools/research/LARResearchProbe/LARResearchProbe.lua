-- Standalone, optional research tool. Never loaded by the production addon.
-- Function presence and successful reads are evidence to investigate, not proof
-- of record scope, exact criteria, persistence, or historical recovery.
local MAX_CRITERIA, MAX_SKILLS, MAX_FIELDS, MAX_TEXT = 20, 20, 30, 32000
local latest, window = "", nil

local function secret(value)
    if type(issecretvalue) ~= "function" then return false end
    local ok, restricted = pcall(issecretvalue, value)
    return not ok or restricted == true
end

local function scalar(value)
    if secret(value) then return "<restricted>" end
    local kind = type(value)
    if kind == "nil" then return "<nil / unknown>" end
    if kind == "string" then return string.format("%q", value:sub(1, 1000)) .. (#value > 1000 and " <string truncated>" or "") end
    if kind == "number" or kind == "boolean" then return tostring(value) end
    return "<" .. kind .. ">"
end

local function emitValue(lines, label, value)
    if secret(value) or type(value) ~= "table" then
        lines[#lines + 1] = label .. " = " .. scalar(value)
        return
    end
    -- Tables are shallow snapshots only; never traverse collections or objects.
    local fields, total = {}, 0
    local ok = pcall(function()
        for key, item in pairs(value) do
            total = total + 1
            if total > MAX_FIELDS then break end
            fields[#fields + 1] = { key = scalar(key), value = scalar(item) }
        end
    end)
    if not ok then lines[#lines + 1] = label .. " = <restricted / unreadable table>"; return end
    table.sort(fields, function(a, b) return a.key < b.key end)
    if #fields == 0 then lines[#lines + 1] = label .. " = <empty table>" end
    for _, field in ipairs(fields) do lines[#lines + 1] = label .. "[" .. field.key .. "] = " .. field.value end
    if total > MAX_FIELDS then lines[#lines + 1] = label .. " = <table fields truncated at " .. MAX_FIELDS .. ">" end
end

local function pack(...) return { n = select("#", ...), ... } end
local function read(lines, name, fn, ...)
    if type(fn) ~= "function" then lines[#lines + 1] = name .. " = UNAVAILABLE (function absent)"; return end
    local result = pack(pcall(fn, ...))
    if not result[1] then lines[#lines + 1] = name .. " = ERROR " .. scalar(result[2]); return end
    local values = { n = math.min(result.n - 1, MAX_FIELDS) }
    lines[#lines + 1] = name .. " = READ OK (" .. (result.n - 1) .. " returned fields; semantics unverified)"
    if values.n == 0 then lines[#lines + 1] = name .. " = <no returned value / unknown>" end
    for index = 1, values.n do
        values[index] = result[index + 1]
        emitValue(lines, name .. ".return[" .. index .. "]", values[index])
    end
    if result.n - 1 > MAX_FIELDS then lines[#lines + 1] = name .. " = <return fields truncated>" end
    return values
end

local function field(namespace, name)
    if type(namespace) ~= "table" or secret(namespace) then return end
    local ok, value = pcall(function() return namespace[name] end)
    if ok and not secret(value) then return value end
end

local function focusedFields(lines, label, result, names)
    local value = result and result[1]
    if secret(value) or type(value) ~= "table" then return end
    for _, name in ipairs(names) do
        local ok, item = pcall(function() return value[name] end)
        if ok then emitValue(lines, label .. ".field[" .. name .. "]", item)
        else lines[#lines + 1] = label .. ".field[" .. name .. "] = <restricted / unreadable>" end
    end
end

local function header(lines)
    lines[#lines + 1] = "=== LAR READ-ONLY RESEARCH PROBE ==="
    lines[#lines + 1] = "No awards, saves, mass scans, account collections, or native UI changes."
    lines[#lines + 1] = "Successful reads do NOT establish lifetime/character scope or historical recovery."
    read(lines, "GetBuildInfo", GetBuildInfo)
    read(lines, "UnitName(player)", UnitName, "player")
    read(lines, "GetRealmName", GetRealmName)
    read(lines, "UnitLevel(player)", UnitLevel, "player")
    read(lines, "UnitClass(player)", UnitClass, "player")
    read(lines, "UnitFactionGroup(player)", UnitFactionGroup, "player")
    read(lines, "UnitRace(player)", UnitRace, "player")
end

local function combat()
    if type(InCombatLockdown) ~= "function" then return false end
    local ok, value = pcall(InCombatLockdown)
    return not ok or secret(value) or value == true
end

local function chat(message)
    if DEFAULT_CHAT_FRAME and type(DEFAULT_CHAT_FRAME.AddMessage) == "function" then
        DEFAULT_CHAT_FRAME:AddMessage("LAR Probe: " .. message)
    elseif type(print) == "function" then print("LAR Probe: " .. message) end
end

local function show()
    if combat() then
        chat("Report retained in memory. Leave combat and use /larprobe copy; no UI operation attempted.")
        return
    end
    if not window then
        if not UIParent or (UIParent.IsForbidden and UIParent:IsForbidden()) then
            chat("Copy window unavailable. Use /larprobe chat for the retained report."); return
        end
        local frame = CreateFrame("Frame", "LARResearchProbeCopy", UIParent)
        frame:SetSize(640, 460); frame:SetPoint("CENTER")
        frame:SetFrameStrata("DIALOG"); frame:SetClampedToScreen(true); frame:EnableMouse(true)
        local background = frame:CreateTexture(nil, "BACKGROUND")
        background:SetAllPoints(); background:SetColorTexture(0.04, 0.04, 0.04, 0.98)
        local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormal")
        title:SetPoint("TOPLEFT", 14, -12); title:SetText("Research only: Ctrl+A, Ctrl+C to copy; Escape to close")
        local close = CreateFrame("Button", nil, frame, "UIPanelCloseButton")
        close:SetPoint("TOPRIGHT", 0, 0)
        close:SetScript("OnClick", function() frame:Hide() end)
        local scroll = CreateFrame("ScrollFrame", nil, frame, "UIPanelScrollFrameTemplate")
        scroll:SetPoint("TOPLEFT", 14, -40); scroll:SetPoint("BOTTOMRIGHT", -30, 14)
        local edit = CreateFrame("EditBox", nil, scroll)
        edit:SetWidth(590); edit:SetMultiLine(true); edit:SetAutoFocus(false)
        edit:SetFontObject("ChatFontNormal"); edit:SetMaxLetters(MAX_TEXT)
        edit:SetScript("OnEscapePressed", function() edit:ClearFocus(); frame:Hide() end)
        scroll:SetScrollChild(edit)
        frame.edit, frame.scroll, window = edit, scroll, frame
    end
    if window.IsForbidden and window:IsForbidden() or window.IsProtected and window:IsProtected() then
        chat("Copy window restricted; report retained. Use /larprobe chat."); return
    end
    window.edit:SetText(latest)
    local rows = 0
    for row in (latest .. "\n"):gmatch("(.-)\n") do rows = rows + math.max(1, math.ceil(#row / 72)) end
    window.edit:SetHeight(math.max(400, rows * 14 + 20))
    if window.scroll.UpdateScrollChildRect then window.scroll:UpdateScrollChildRect() end
    window.scroll:SetVerticalScroll(0)
    window.edit:HighlightText(); window.edit:SetFocus(); window:Show()
end

local function report(lines)
    latest = table.concat(lines, "\n")
    if #latest > MAX_TEXT then latest = latest:sub(1, MAX_TEXT - 40) .. "\n<report truncated at 32000 characters>" end
    local ok, err = pcall(show)
    if not ok then chat("Copy window unavailable: " .. scalar(err) .. ". Report retained; use /larprobe chat.") end
end

local function integer(text)
    local id = tonumber(text)
    if not id or id < 1 or id > 2147483647 or id ~= math.floor(id) then return end
    return id
end

local function achievement(lines, id, withCriteria)
    read(lines, "GetAchievementInfo(" .. id .. ")", GetAchievementInfo, id)
    lines[#lines + 1] = "Forever adapter field guide: [4] completed; [9] flags; [13] wasEarnedByMe."
    lines[#lines + 1] = "Account completion alone is not character proof; no completion is inferred from criteria."
    emitValue(lines, "ACHIEVEMENT_FLAGS_ACCOUNT", ACHIEVEMENT_FLAGS_ACCOUNT)
    if not withCriteria then return end
    local result = read(lines, "GetAchievementNumCriteria(" .. id .. ")", GetAchievementNumCriteria, id)
    local count = result and result[1]
    if secret(count) or type(count) ~= "number" or count < 0 or count ~= math.floor(count) then
        lines[#lines + 1] = "Criteria count unknown; no criterion reads attempted."; return
    end
    if count > MAX_CRITERIA then lines[#lines + 1] = "Criteria truncated: first 20 of " .. count .. "; this is not a full record." end
    for index = 1, math.min(count, MAX_CRITERIA) do
        read(lines, "GetAchievementCriteriaInfo(" .. id .. "," .. index .. ")", GetAchievementCriteriaInfo, id, index)
    end
    lines[#lines + 1] = "Criteria field guide: [1] name; [2] type; [3] completed; [4] quantity; [5] required; [7] flags; [8] assetID; [9] quantityText; [10] criteriaID."
end

local function command(message)
    local action, argument = tostring(message or ""):match("^%s*(%S*)%s*(.-)%s*$")
    action = action:lower()
    if action == "copy" then
        if latest == "" then chat("No report yet. Run /larprobe build first.") else local ok = pcall(show); if not ok then chat("Copy window unavailable; use /larprobe chat.") end end
        return
    elseif action == "chat" then
        if latest == "" then chat("No report yet. Run /larprobe build first.") end
        for line in latest:gmatch("[^\n]+") do chat(line) end
        return
    end
    local id = integer(argument)
    local single = action == "quest" or action == "stat" or action == "achievement" or action == "reputation" or action == "currency" or action == "recipe" or action == "recipes"
    if action ~= "build" and action ~= "bind" and action ~= "skills" and action ~= "totems" and not single then
        chat("Commands: build | quest ID | stat ID | achievement ID | reputation ID | currency ID | bind | skills | totems | recipe ID | copy | chat"); return
    end
    if single and not id then chat("Supply one positive numeric ID; no ranges, guesses, or mass scanning."); return end
    local lines = {}; header(lines)
    if action == "quest" then
        local modern = field(C_QuestLog, "IsQuestFlaggedCompleted")
        if type(modern) == "function" then read(lines, "C_QuestLog.IsQuestFlaggedCompleted(" .. id .. ")", modern, id)
        else read(lines, "IsQuestFlaggedCompleted(" .. id .. ")", IsQuestFlaggedCompleted, id) end
        lines[#lines + 1] = "Verify this exact quest ID, hidden/faction/class variants, persistence, and recovery; false does not prove API readiness."
    elseif action == "stat" then
        read(lines, "GetStatistic(" .. id .. ")", GetStatistic, id)
        achievement(lines, id, false)
        lines[#lines + 1] = "Raw text retained: no numeric parsing, unit conversion, or lifetime inference. Metadata can be unavailable for statistic IDs."
    elseif action == "achievement" then achievement(lines, id, true)
    elseif action == "reputation" then
        read(lines, "C_Reputation.GetFactionDataByID(" .. id .. ")", field(C_Reputation, "GetFactionDataByID"), id)
        read(lines, "GetFactionInfoByID(" .. id .. ")", GetFactionInfoByID, id)
        lines[#lines + 1] = "Current standing is not best-ever standing; verify faction name/ID, character scope, reset/faction-change behavior."
    elseif action == "currency" then
        read(lines, "C_CurrencyInfo.GetCurrencyInfo(" .. id .. ")", field(C_CurrencyInfo, "GetCurrencyInfo"), id)
        lines[#lines + 1] = "Matching-build API documented; availability, record scope, and history remain unverified."
        lines[#lines + 1] = "Held balance is not lifetime earned/spent or a transaction history; totalEarned requires independent retention/scope tests."
    elseif action == "bind" then
        read(lines, "GetBindLocation", GetBindLocation)
        lines[#lines + 1] = "Current localized bind name only; no prior inns, uses, or unique bind history inferred."
    elseif action == "skills" then
        if type(GetNumSkillLines) == "function" and type(GetSkillLineInfo) == "function" then
            local result = read(lines, "GetNumSkillLines", GetNumSkillLines)
            local count = result and result[1]
            if not secret(count) and type(count) == "number" and count >= 0 and count == math.floor(count) then
                for index = 1, math.min(count, MAX_SKILLS) do read(lines, "GetSkillLineInfo(" .. index .. ")", GetSkillLineInfo, index) end
                if count > MAX_SKILLS then lines[#lines + 1] = "Only first 20 skill rows queried; not a full profession catalog." end
            else lines[#lines + 1] = "Skill count unknown; no skill rows queried." end
        else
            lines[#lines + 1] = "Skill-line list unavailable; using the six profession slots from the production source contract."
            local slots = read(lines, "GetProfessions", GetProfessions)
            local seen = {}
            for slot = 1, 6 do
                local index = slots and slots[slot]
                if not secret(index) and type(index) == "number" and index >= 1 and index <= 2147483647 and index == math.floor(index) and not seen[index] then
                    seen[index] = true
                    read(lines, "GetProfessionInfo(" .. index .. ") [slot " .. slot .. "]", GetProfessionInfo, index)
                else lines[#lines + 1] = "Profession slot " .. slot .. " = unknown, invalid, or duplicate; no info read." end
            end
            lines[#lines + 1] = "Only first six profession slots considered; absent slots do not prove historical non-ownership."
        end
        lines[#lines + 1] = "Current learned skills only; forgotten professions and historical maxima are not reconstructed."
    elseif action == "totems" then
        for slot = 1, 4 do read(lines, "GetTotemInfo(" .. slot .. ")", GetTotemInfo, slot) end
        emitValue(lines, "MAX_TOTEMS", MAX_TOTEMS)
        for _, name in ipairs({ "FIRE_TOTEM_SLOT", "EARTH_TOTEM_SLOT", "WATER_TOTEM_SLOT", "AIR_TOTEM_SLOT" }) do
            emitValue(lines, name, rawget(_G, name))
        end
        lines[#lines + 1] = "Only four active totem slots queried. No historical casts, ownership conditions, or timing sequence inferred."
        lines[#lines + 1] = "Matching-build field guide: [1] haveTotem; [2] name; [3] startTime; [4] duration; [5] icon; [6] modRate; [7] spellID."
    elseif action == "recipe" or action == "recipes" then
        local result = read(lines, "C_TradeSkillUI.GetRecipeInfo(" .. id .. ")", field(C_TradeSkillUI, "GetRecipeInfo"), id)
        focusedFields(lines, "Recipe", result, { "recipeID", "name", "learned", "firstCraft" })
        lines[#lines + 1] = "Matching-build API documented; availability, record scope, and history remain unverified."
        lines[#lines + 1] = "No trade UI opened/selected; returned data may depend on an already-open profession or be another player's linked view."
        lines[#lines + 1] = "No character ownership or crafting history inferred. Use your own already-open profession and record context manually."
    else
        for _, item in ipairs({
            { "C_QuestLog.IsQuestFlaggedCompleted", field(C_QuestLog, "IsQuestFlaggedCompleted") },
            { "GetStatistic", GetStatistic }, { "GetAchievementInfo", GetAchievementInfo },
            { "GetAchievementNumCriteria", GetAchievementNumCriteria }, { "GetAchievementCriteriaInfo", GetAchievementCriteriaInfo },
            { "C_Reputation.GetFactionDataByID", field(C_Reputation, "GetFactionDataByID") }, { "GetFactionInfoByID", GetFactionInfoByID },
            { "C_CurrencyInfo.GetCurrencyInfo", field(C_CurrencyInfo, "GetCurrencyInfo") },
            { "GetBindLocation", GetBindLocation }, { "GetNumSkillLines", GetNumSkillLines }, { "GetSkillLineInfo", GetSkillLineInfo },
            { "GetProfessions", GetProfessions }, { "GetProfessionInfo", GetProfessionInfo }, { "GetTotemInfo", GetTotemInfo },
            { "C_TradeSkillUI.GetRecipeInfo", field(C_TradeSkillUI, "GetRecipeInfo") },
        }) do lines[#lines + 1] = item[1] .. " = " .. (type(item[2]) == "function" and "FUNCTION PRESENT (not verified)" or "UNAVAILABLE") end
    end
    report(lines)
end

SLASH_LARRESEARCHPROBE1 = "/larprobe"
SlashCmdList.LARRESEARCHPROBE = command
