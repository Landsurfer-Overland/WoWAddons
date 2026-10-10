-------------------------------------------------------------------------------
--  Sharing: achievement links in chat, what other players with the addon have
--  earned, comparing, titles, guild announcements and the account overview.
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA
local TAG, secret = FA.TAG, FA.secret
local PREFIX = "FAch"
local LINK_COLOR = "ff2ec4b6"

local function Settings() return FA.Settings() end

-- Forever characters have a surname, and the client keeps it where the realm
-- normally goes: UnitFullName gives "Tne", "Pojajach" and whispers only reach
-- "Tne-Pojajach". First names are not unique ("Suldane Sellar" / "Suldane Two"),
-- so players are keyed and addressed by the full "Name-Surname".
local function FullName(unit)
    if not unit or not UnitFullName then return end
    local name, surname = UnitFullName(unit)
    if not name or secret(name) then return end
    if surname and not secret(surname) and surname ~= "" then return name .. "-" .. surname end
    return name
end
FA.FullName = FullName

local function First(name) return name and name:match("^([^%-]+)") end
local function Key(name) return name end
-- "Tne-Pojajach" -> "Tne Pojajach", the way the game shows it.
local function Display(name) return name and (name:gsub("%-", " ")) end
local function IsMe(name)
    return name == FullName("player") or name == UnitName("player")
end

local frame = CreateFrame("Frame")
local handlers = {}
local function On(event, fn)
    if pcall(frame.RegisterEvent, frame, event) then handlers[event] = fn end
end
frame:SetScript("OnEvent", function(_, event, ...) handlers[event](...) end)

-------------------------------------------------------------------------------
--  Titles
-------------------------------------------------------------------------------
local TITLED = {}
for _, a in ipairs(FA.ALL) do if a.title then TITLED[#TITLED + 1] = a end end

-- Titles this character has earned.
function FA.EarnedTitles()
    local out = {}
    for _, a in ipairs(TITLED) do
        if FA.DB().done[a.key] and FA.Available(a) then out[#out + 1] = a end
    end
    return out
end

-- The chosen title as a format string ("%s the Insane"), if still earned.
function FA.CurrentTitle()
    local key = FA.DB().title
    local a = key and FA.BY_KEY[key]
    if a and a.title and FA.DB().done[key] then return a.title end
end

-------------------------------------------------------------------------------
--  Links: "[ach:Name]" in chat turns into a clickable link
-------------------------------------------------------------------------------
local BY_NAME = {}
for _, a in ipairs(FA.ALL) do
    local k = a.name:lower()
    -- Series tiers share a name: the link points at the first tier still
    -- missing for the reader, which is what they would look up.
    BY_NAME[k] = BY_NAME[k] or a
end

FA.LINK.fn = function(a)
    return ("|c%s|Haddon:ForeverAchievements:%s|h[%s]|h|r"):format(LINK_COLOR, a.key, a.name)
end

local function Filter(_, _, msg, ...)
    if type(msg) ~= "string" or secret(msg) or not msg:find("[ach:", 1, true) then return false end
    local out = msg:gsub("%[ach:([^%]]+)%]", function(name)
        local a = BY_NAME[name:lower()]
        if a then return FA.LINK.fn(a) end
    end)
    if out ~= msg then return false, out, ... end
    return false
end

local addFilter = ChatFrame_AddMessageEventFilter or (ChatFrameUtil and ChatFrameUtil.AddMessageEventFilter)
if addFilter then
    for _, e in ipairs({ "CHAT_MSG_SAY", "CHAT_MSG_YELL", "CHAT_MSG_GUILD", "CHAT_MSG_OFFICER", "CHAT_MSG_PARTY",
        "CHAT_MSG_PARTY_LEADER", "CHAT_MSG_RAID", "CHAT_MSG_RAID_LEADER", "CHAT_MSG_WHISPER", "CHAT_MSG_WHISPER_INFORM",
        "CHAT_MSG_CHANNEL", "CHAT_MSG_INSTANCE_CHAT", "CHAT_MSG_INSTANCE_CHAT_LEADER", "CHAT_MSG_EMOTE" }) do
        pcall(addFilter, e, Filter)
    end
end

-- Clicking a link: the achievement in the item tooltip; shift-click opens it.
local lastLink, lastLinkTime = nil, 0
local function OnLink(link)
    local key = type(link) == "string" and link:match("^addon:ForeverAchievements:(.+)$")
    if not key then return end
    if key == lastLink and GetTime() - lastLinkTime < 0.2 then return end
    lastLink, lastLinkTime = key, GetTime()
    local a = FA.BY_KEY[key]
    if not a then return end
    if IsShiftKeyDown() then
        FA.OpenSearch(a.name)
        return
    end
    local r, g, b = FA.Kit.Accent()
    local tt = ItemRefTooltip
    tt:SetOwner(UIParent, "ANCHOR_PRESERVE")
    tt:ClearLines()
    tt:AddLine(a.name, 1, 1, 1)
    tt:AddLine(a.desc, nil, nil, nil, true)
    if a.pts and a.pts > 0 then tt:AddLine(a.pts .. " points", r, g, b) end
    local done = FA.Earned(a.key)
    if done then
        tt:AddLine("You earned it on " .. date("%d.%m.%Y", done), r, g, b)
    else
        local cur, need = a.progress()
        local progress = FA.ProgressKnown(cur, need) and ("%s / %s"):format(cur, need) or "Unavailable"
        tt:AddLine("Your progress: " .. progress, 0.8, 0.8, 0.8)
    end
    tt:AddLine("Shift-click the link to open Forever Achievements", 0.55, 0.55, 0.55, true)
    tt:Show()
end
if EventRegistry and EventRegistry.RegisterCallback then
    EventRegistry:RegisterCallback("SetItemRef", function(_, link) OnLink(link) end, "ForeverAchievements")
end
if SetItemRef then hooksecurefunc("SetItemRef", function(link) OnLink(link) end) end

-------------------------------------------------------------------------------
--  Talking to other players with the addon (hidden addon messages)
-------------------------------------------------------------------------------
local sendAddon = (C_ChatInfo and C_ChatInfo.SendAddonMessage) or SendAddonMessage
if C_ChatInfo and C_ChatInfo.RegisterAddonMessagePrefix then C_ChatInfo.RegisterAddonMessagePrefix(PREFIX) end

local function Send(msg, channel, target) pcall(sendAddon, PREFIX, msg, channel, target) end

local function Broadcast(msg)
    if Settings().share == false then return end
    if IsInGuild() then Send(msg, "GUILD") end
    if LE_PARTY_CATEGORY_INSTANCE and IsInGroup(LE_PARTY_CATEGORY_INSTANCE) then
        Send(msg, "INSTANCE_CHAT")
    elseif IsInRaid() then
        Send(msg, "RAID")
    elseif IsInGroup() then
        Send(msg, "PARTY")
    end
end

local function HelloMsg()
    local pts, _, n = FA.TotalPoints()
    return table.concat({ "HI", pts, n, FA.CurrentTitle() or "" }, "\t")
end

local peers = {}    -- [short name] = { pts, count, title, time }
local replied = {}  -- answered their hello this session
local incoming = {} -- [sender] = keys while a compare answer arrives
local pendingCompare

-- Exact "Name-Surname" first; a bare first name matches only when unambiguous.
function FA.Peer(name)
    if not name then return end
    if peers[name] then return peers[name] end
    if name:find("-", 1, true) then return end
    local found
    for key, p in pairs(peers) do
        if First(key) == name then
            if found then return end
            found = p
        end
    end
    return found
end

local function AnswerCompare(sender)
    local keys = {}
    for key in pairs(FA.DB().done) do keys[#keys + 1] = key end
    local chunk, chunks = {}, {}
    local size = 0
    for _, key in ipairs(keys) do
        if size + #key + 1 > 230 then
            chunks[#chunks + 1] = table.concat(chunk, ",")
            chunk, size = {}, 0
        end
        chunk[#chunk + 1] = key
        size = size + #key + 1
    end
    if #chunk > 0 then chunks[#chunks + 1] = table.concat(chunk, ",") end
    for i, c in ipairs(chunks) do
        C_Timer.After(i * 0.25, function() Send("DONE\t" .. c, "WHISPER", sender) end)
    end
    C_Timer.After((#chunks + 1) * 0.25, function() Send("END", "WHISPER", sender) end)
end

On("CHAT_MSG_ADDON", function(prefix, msg, channel, sender)
    if prefix ~= PREFIX or type(msg) ~= "string" or secret(msg) or not sender or secret(sender) then return end
    if IsMe(sender) then return end
    local short = Key(sender)
    local kind, a1, a2, a3 = strsplit("\t", msg)
    if kind == "HI" then
        peers[short] = { pts = tonumber(a1) or 0, count = tonumber(a2) or 0, title = (a3 ~= "" and a3) or nil, time = time() }
        if channel ~= "WHISPER" and not replied[short] and Settings().share ~= false then
            replied[short] = true
            Send(HelloMsg(), "WHISPER", sender)
        end
    elseif kind == "EARN" then
        local a = FA.BY_KEY[a1 or ""]
        if a and Settings().showOthers ~= false then
            print(TAG .. " " .. Display(short) .. " earned " .. FA.LINK.fn(a))
        end
        if peers[short] then peers[short].count = peers[short].count + 1 end
    elseif kind == "REQ" then
        if Settings().share ~= false then AnswerCompare(sender) end
    elseif kind == "DONE" then
        incoming[short] = incoming[short] or {}
        for key in (a1 or ""):gmatch("[^,]+") do incoming[short][key] = true end
    elseif kind == "END" then
        -- The answer may come back with or without the surname.
        if pendingCompare and (pendingCompare == short or First(pendingCompare) == First(short)
            and not (pendingCompare:find("-", 1, true) and short:find("-", 1, true))) then
            pendingCompare = nil
            FA.COMPARE.name, FA.COMPARE.done = Display(short), incoming[short] or {}
            incoming[short] = nil
            local n = 0
            for _ in pairs(FA.COMPARE.done) do n = n + 1 end
            print(TAG .. (" comparing with %s (%d earned). /fach compare off to stop."):format(Display(short), n))
            FA.ShowTab(FA.DB().tab ~= "summary" and FA.DB().tab or "general")
        end
    end
end)

-- Ask another player with the addon for what they have earned.
function FA.RequestCompare(name)
    if not name or name == "" then
        if UnitIsPlayer("target") and not secret(UnitIsPlayer("target")) then name = FullName("target") end
    end
    if not name or name == "" or secret(name) then
        print(TAG .. " target a player or type /fach compare Name-Surname.")
        return
    end
    -- Typed as "Tne Pojajach": the whisper target needs "Tne-Pojajach".
    name = name:gsub("^%s+", ""):gsub("%s+$", ""):gsub("%s+", "-")
    pendingCompare = name
    incoming[Key(name)] = {}
    Send("REQ", "WHISPER", name)
    print(TAG .. " asking " .. Display(name) .. " ...")
    C_Timer.After(6, function()
        if pendingCompare == name then
            pendingCompare = nil
            print(TAG .. " no answer from " .. Display(name) .. ": they may not run Forever Achievements.")
        end
    end)
end

function FA.StopCompare()
    FA.COMPARE.name, FA.COMPARE.done = nil, nil
    FA.Refresh()
end

FA.SLASH.compare = function(rest)
    if rest:lower() == "off" then
        FA.StopCompare()
        print(TAG .. " comparing stopped.")
    else
        FA.RequestCompare(rest)
    end
end

-- "Compare achievements" in the right-click menu of a player.
if Menu and Menu.ModifyMenu then
    for _, tag in ipairs({ "MENU_UNIT_PLAYER", "MENU_UNIT_PARTY", "MENU_UNIT_RAID_PLAYER", "MENU_UNIT_FRIEND",
        "MENU_UNIT_TARGET", "MENU_UNIT_GUILD" }) do
        pcall(Menu.ModifyMenu, tag, function(_, root, context)
            if not context then return end
            -- Unit menus (target, party, raid) know the surname via the unit.
            local name = context.unit and not secret(context.unit) and FullName(context.unit)
            if not name then
                name = context.name
                if not name or secret(name) then return end
                if context.server and not secret(context.server) and context.server ~= "" then
                    name = name .. "-" .. context.server
                end
            end
            if IsMe(name) then return end
            root:CreateDivider()
            root:CreateButton("Compare achievements", function() FA.RequestCompare(name) end)
        end)
    end
end

-------------------------------------------------------------------------------
--  Account overview: every character's points, for the Summary page
-------------------------------------------------------------------------------
local function SaveCharacter()
    local name, realm = UnitName("player"), GetRealmName()
    if not name or secret(name) then return end
    local pts, _, n = FA.TotalPoints()
    local done = {}
    for k, v in pairs(FA.DB().done) do done[k] = v end
    local _, class = UnitClass("player")
    FA.Account().chars[name .. "-" .. (realm or "")] = {
        name = name, realm = realm, class = class, level = UnitLevel("player"),
        pts = pts, count = n, last = time(), done = done, title = FA.CurrentTitle(),
    }
end
FA.SaveCharacter = SaveCharacter

-------------------------------------------------------------------------------
--  Earning: tell the guild and group, keep the overview current
-------------------------------------------------------------------------------
local sendChat = (C_ChatInfo and C_ChatInfo.SendChatMessage) or SendChatMessage
table.insert(FA.EARN_HOOKS, function(a)
    SaveCharacter()
    Broadcast("EARN\t" .. a.key)
    if Settings().announce and IsInGuild() and not a.native then
        pcall(sendChat, "earned the achievement [ach:" .. a.name .. "]!", "GUILD")
    end
end)

On("PLAYER_LOGIN", function()
    C_Timer.After(12, function()
        SaveCharacter()
        Broadcast(HelloMsg())
    end)
end)
On("GROUP_JOINED", function() C_Timer.After(3, function() Broadcast(HelloMsg()) end) end)
On("PLAYER_LOGOUT", SaveCharacter)
