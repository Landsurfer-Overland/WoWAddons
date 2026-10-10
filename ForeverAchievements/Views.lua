-------------------------------------------------------------------------------
--  Pages that are not achievement lists: Summary, Statistics and Settings.
--  Each draws into the scroll child and returns the height it used.
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA
local Kit = FA.Kit
local W = Kit.W
local C = Kit.COLORS

local CLASS_COLORS = RAID_CLASS_COLORS or {}

local function SnapshotSafe(value)
    if type(FA.secret) ~= "function" then return true end
    local ok, hidden = pcall(FA.secret, value)
    return ok and not hidden
end
local function SnapshotField(object, key)
    if not SnapshotSafe(object) or type(object) ~= "table" then return nil end
    local ok, value = pcall(function() return object[key] end)
    if ok and SnapshotSafe(value) then return value end
end
local function SnapshotText(value)
    if SnapshotSafe(value) and type(value) == "string" and value ~= "" then return value end
end
local function SnapshotNumber(value)
    if SnapshotSafe(value) and type(value) == "number" and value == value and value >= 0 and value < math.huge then return value end
end
local function CharacterSnapshots()
    local entries, omitted = {}, 0
    local chars = SnapshotField(FA.Account(), "chars")
    if type(chars) ~= "table" then return entries, omitted end
    for key, snapshot in pairs(chars) do
        local identity = SnapshotField(snapshot, "identity")
        local identityKey = SnapshotText(SnapshotField(identity, "key"))
        local name, surname, realm = SnapshotText(SnapshotField(identity, "name")), SnapshotText(SnapshotField(identity, "surname")), SnapshotText(SnapshotField(identity, "realm"))
        local guid = SnapshotText(SnapshotField(identity, "guid"))
        if guid and not guid:match("^Player%-%w[%w%-]*$") then guid = nil end
        if SnapshotText(key) == identityKey and identityKey and name and realm and (surname or guid)
            and SnapshotField(identity, "verified") == true and SnapshotField(snapshot, "identityVersion") == 1
            and SnapshotField(snapshot, "characterKey") == identityKey and SnapshotField(snapshot, "completionScope") == "character"
            and SnapshotField(snapshot, "pointType") == "character" then
            entries[#entries + 1] = { snapshot = snapshot, key = identityKey, name = name, surname = surname, realm = realm,
                guid = guid, last = SnapshotNumber(SnapshotField(snapshot, "last")) }
        else omitted = omitted + 1 end
    end
    table.sort(entries, function(a, b)
        if a.last ~= b.last then
            if a.last == nil then return false elseif b.last == nil then return true else return a.last > b.last end
        end
        if (a.guid ~= nil) ~= (b.guid ~= nil) then return a.guid ~= nil end
        return a.key < b.key
    end)
    local unique = {}
    for _, entry in ipairs(entries) do
        local duplicate = false
        for _, other in ipairs(unique) do
            if entry.realm == other.realm and (entry.guid and other.guid and entry.guid == other.guid
                or (not entry.guid or not other.guid) and entry.name == other.name and entry.surname == other.surname) then
                duplicate = true; break
            end
        end
        if not duplicate then unique[#unique + 1] = entry end
    end
    return unique, omitted
end
local function SnapshotValue(snapshot, key, available)
    local value = SnapshotNumber(SnapshotField(snapshot, key))
    if value == nil or available and SnapshotField(snapshot, available) == false then return "Unavailable" end
    return tostring(value)
end

local function Line(child, y, height)
    local f = CreateFrame("Frame", nil, child)
    f:SetSize(child:GetWidth() - 40, height or 26)
    f:SetPoint("TOPLEFT", 20, y)
    return f
end

local function CardBg(f, hover)
    local bg = f:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(C.card[1], C.card[2], C.card[3], C.card[4])
    Kit.MakeBorder(f, unpack(C.edge))
    if hover then
        f:SetScript("OnEnter", function() bg:SetColorTexture(C.cardHover[1], C.cardHover[2], C.cardHover[3], C.cardHover[4]) end)
        f:SetScript("OnLeave", function() bg:SetColorTexture(C.card[1], C.card[2], C.card[3], C.card[4]) end)
    end
end

local function Bar(parent, x, width, frac)
    local r, g, b = Kit.Accent()
    local track = parent:CreateTexture(nil, "ARTWORK")
    track:SetColorTexture(1, 1, 1, 0.1)
    track:SetSize(width, 3)
    track:SetPoint("LEFT", x, 0)
    local fill = parent:CreateTexture(nil, "OVERLAY")
    fill:SetColorTexture(r, g, b, 1)
    fill:SetSize(math.max(1, width * math.min(1, frac)), 3)
    fill:SetPoint("LEFT", track, "LEFT")
end

-------------------------------------------------------------------------------
--  Summary
-------------------------------------------------------------------------------
local function CategoryCounts(key)
    local n, all = 0, 0
    for _, sec in ipairs(FA.CATEGORY_SECTIONS[key]) do
        for _, a in ipairs(sec.list) do
            if FA.Available(a) then
                all = all + 1
                if FA.Earned(a.key) then n = n + 1 end
            end
        end
    end
    return n, all
end

-- What can be done where you stand: unexplored areas, bosses of the
-- instance you are in, critters still waiting for /love.
local function Suggestions()
    local out = {}
    local zone = GetRealZoneText()
    local zoneAch = zone and FA.ZONE_ACH[zone]
    if zoneAch and not FA.Earned(zoneAch.key) then
        local missing = {}
        for _, n in ipairs(zoneAch.list) do if not zoneAch.has(n) then missing[#missing + 1] = n end end
        if #missing > 0 then out[#out + 1] = { zoneAch, "Unexplored: " .. table.concat(missing, ", ") } end
    end
    local inInstance = IsInInstance()
    if inInstance then
        local name = GetInstanceInfo()
        for _, key in ipairs({ "dungeons" }) do
            for _, sec in ipairs(FA.CATEGORY_SECTIONS[key]) do
                for _, a in ipairs(sec.list) do
                    if name and a.name and (name:find(a.name, 1, true) or a.name:find(name, 1, true)) and not FA.Earned(a.key) then
                        out[#out + 1] = { a, a.desc }
                    end
                end
            end
        end
    end
    local crit = FA.BY_KEY.critters
    if crit and not FA.Earned("critters") then
        local missing = {}
        for _, n in ipairs(FA.CRITTERS) do if not FA.DB().critters[n] then missing[#missing + 1] = n end end
        out[#out + 1] = { crit, "Still to /love: " .. table.concat(missing, ", ") }
    end
    local pests = FA.BY_KEY.pests
    if pests and not FA.Earned("pests") then
        local missing = {}
        for _, n in pairs(FA.PESTS) do if not FA.DB().pests[n] then missing[#missing + 1] = n end end
        table.sort(missing)
        out[#out + 1] = { pests, "Still to slay: " .. table.concat(missing, ", ") }
    end
    return out, zone
end

FA.VIEWS.summary = function(child, width)
    local r, g, b = Kit.Accent()
    local y = 0
    local _, h

    -- Title
    local titles = FA.EarnedTitles()
    local values, order = { none = "No title" }, { "none" }
    for _, a in ipairs(titles) do
        values[a.key] = a.title:format(UnitName("player"))
        order[#order + 1] = a.key
    end
    _, h = W:SectionHeader(child, "OVERVIEW", y)
    y = y - h
    _, h = W:Dropdown(child, "Title shown to other players with the addon", y, values,
        function() return FA.CurrentTitle() and FA.DB().title or "none" end,
        function(v)
            FA.DB().title = (v ~= "none") and v or nil
            if FA.SaveCharacter then FA.SaveCharacter() end
        end, order,
        #titles == 0 and "Earn achievements like The Loremaster, World Explorer or Insane in the Membrane for titles." or nil)
    y = y - h

    -- Recently earned
    local recent = {}
    for key, t in pairs(FA.DB().done) do
        local a = FA.BY_KEY[key]
        local timestamp = SnapshotNumber(t)
        if a and timestamp and timestamp > 0 then recent[#recent + 1] = { a, timestamp } end
    end
    table.sort(recent, function(p, q) return p[2] > q[2] end)
    if #recent > 0 then
        _, h = W:SectionHeader(child, "RECENTLY EARNED", y)
        y = y - h
        for i = 1, math.min(5, #recent) do
            local a, t = recent[i][1], recent[i][2]
            local row = CreateFrame("Button", nil, child)
            row:SetSize(width - 40, 36)
            row:SetPoint("TOPLEFT", 20, y)
            CardBg(row, true)
            local icon = row:CreateTexture(nil, "ARTWORK")
            icon:SetSize(24, 24)
            icon:SetPoint("LEFT", 8, 0)
            icon:SetTexture(a.icon or ns.ICONS[a.id] or 236376)
            icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
            local name = Kit.MakeFont(row, 13, nil, r, g, b, 1)
            name:SetPoint("LEFT", icon, "RIGHT", 10, 0)
            name:SetText(a.name)
            local when = Kit.MakeFont(row, 12, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            when:SetPoint("RIGHT", -12, 0)
            when:SetText(date("%d.%m.%Y", t))
            row:SetScript("OnClick", function() FA.OpenSearch(a.name) end)
            y = y - 42
        end
        y = y - 6
    end

    -- Progress per category
    _, h = W:SectionHeader(child, "PROGRESS", y)
    y = y - h
    for _, cat in ipairs(FA.CATEGORIES) do
        if FA.CATEGORY_SECTIONS[cat.key] then
            local n, all = CategoryCounts(cat.key)
            local row = CreateFrame("Button", nil, child)
            row:SetSize(width - 40, 30)
            row:SetPoint("TOPLEFT", 20, y)
            CardBg(row, true)
            local label = Kit.MakeFont(row, 12, nil, C.text[1], C.text[2], C.text[3], 1)
            label:SetPoint("LEFT", 12, 0)
            label:SetText(cat.label)
            Bar(row, 190, width - 360, all > 0 and n / all or 0)
            local v = Kit.MakeFont(row, 12, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            v:SetPoint("RIGHT", -12, 0)
            v:SetText(n .. " / " .. all)
            row:SetScript("OnClick", function() FA.ShowTab(cat.key) end)
            y = y - 36
        end
    end
    y = y - 6

    -- Where you stand
    local tips, zone = Suggestions()
    if #tips > 0 then
        _, h = W:SectionHeader(child, "SUGGESTIONS" .. (zone and zone ~= "" and (" IN " .. zone:upper()) or ""), y)
        y = y - h
        for _, tip in ipairs(tips) do
            local a, text = tip[1], tip[2]
            local row = CreateFrame("Button", nil, child)
            row:SetSize(width - 40, 46)
            row:SetPoint("TOPLEFT", 20, y)
            CardBg(row, true)
            local name = Kit.MakeFont(row, 13, nil, C.text[1], C.text[2], C.text[3], 1)
            name:SetPoint("TOPLEFT", 12, -8)
            name:SetText(a.name)
            local desc = Kit.MakeFont(row, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            desc:SetPoint("TOPLEFT", name, "BOTTOMLEFT", 0, -4)
            desc:SetPoint("RIGHT", -12, 0)
            desc:SetJustifyH("LEFT")
            desc:SetWordWrap(false)
            desc:SetText(text)
            row:SetScript("OnClick", function() FA.OpenSearch(a.name) end)
            y = y - 52
        end
        y = y - 6
    end

    -- Verified saved character snapshots are separate observations, not an
    -- authoritative account total or native Legacy point balance.
    local chars, omitted = CharacterSnapshots()
    if #chars > 0 then
        _, h = W:SectionHeader(child, "CHARACTER SNAPSHOTS", y)
        y = y - h
        for _, entry in ipairs(chars) do
            local c = entry.snapshot
            local row = Line(child, y, 30)
            CardBg(row)
            local col = CLASS_COLORS[SnapshotText(SnapshotField(c, "class")) or ""]
            local name = Kit.MakeFont(row, 12, nil, col and col.r or 1, col and col.g or 1, col and col.b or 1, 1)
            name:SetPoint("LEFT", 12, 0)
            local fullName = entry.name .. (entry.surname and (" " .. entry.surname) or "")
            local title = SnapshotText(SnapshotField(c, "title"))
            if title then local ok, display = pcall(string.format, title, fullName); if ok then fullName = display end end
            name:SetText(fullName .. "  |cff9aa5b1" .. entry.realm .. "|r")
            local info = Kit.MakeFont(row, 12, nil, C.dim[1], C.dim[2], C.dim[3], 1)
            info:SetPoint("RIGHT", -12, 0)
            info:SetText(("level %s   |   %s earned   |   %s character points   |   %s"):format(SnapshotValue(c, "level"),
                SnapshotValue(c, "count", "countAvailable"), SnapshotValue(c, "pts", "pointsAvailable"),
                entry.last and entry.last > 0 and date("%d.%m.%Y", entry.last) or "Last seen unavailable"))
            y = y - 34
        end
    end
    if omitted > 0 then
        local note = Kit.MakeFont(child, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
        note:SetPoint("TOPLEFT", 20, y - 4); note:SetWidth(width - 40); note:SetHeight(26)
        note:SetText("Older or unverified character snapshots are preserved but are not shown here.")
        y = y - 32
    end
    return -y + 10
end

-------------------------------------------------------------------------------
--  Statistics
-------------------------------------------------------------------------------
local function StatRows(child, width, y, title, rows)
    local _, h = W:SectionHeader(child, title, y)
    y = y - h
    local colW = math.floor((width - 46) / 2)
    for i, row in ipairs(rows) do
        local col = (i - 1) % 2
        if col == 0 and i > 1 then y = y - 28 end
        local f = CreateFrame("Frame", nil, child)
        f:SetSize(colW, 24)
        f:SetPoint("TOPLEFT", 20 + col * (colW + 6), y)
        CardBg(f)
        local label = Kit.MakeFont(f, 11, nil, C.text[1], C.text[2], C.text[3], 0.9)
        label:SetPoint("LEFT", 10, 0)
        label:SetPoint("RIGHT", -110, 0)
        label:SetJustifyH("LEFT")
        label:SetWordWrap(false)
        label:SetText(row[1])
        local value = Kit.MakeFont(f, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
        value:SetPoint("RIGHT", -10, 0)
        value:SetText(row[2] or "--")
    end
    return y - 34
end

FA.VIEWS.statistics = function(child, width)
    local d = FA.DB()
    local Count = FA.Count
    local y = StatRows(child, width, 0, "TRACKED BY FOREVER ACHIEVEMENTS", {
        { "Critters loved", tostring(Count(d.critters)) },
        { "Pests slain", tostring(Count(d.pests)) },
        { "Books read", tostring(Count(d.books)) },
        { "Different dishes eaten", tostring(Count(d.foods)) },
        { "Different drinks", tostring(Count(d.drinks)) },
        { "Rare enemies slain", tostring(Count(d.rares)) },
        { "Bosses seen slain", tostring(Count(d.bosses)) },
        { "Fishing catches seen", tostring(d.fished or 0) },
    })
    for _, sec in ipairs(ns.STATS) do
        local rows = {}
        for _, s in ipairs(sec.list) do rows[#rows + 1] = { s[2], FA.StatText(s[1]) } end
        y = StatRows(child, width, y, sec.title, rows)
    end
    return -y
end

-------------------------------------------------------------------------------
--  Settings
-------------------------------------------------------------------------------
local function Toggle(child, y, text, key, default, tooltip, after)
    local S = FA.Settings()
    local _, h = W:Toggle(child, text, y,
        function()
            if S[key] == nil then return default end
            return S[key]
        end,
        function(v)
            S[key] = v
            if after then after(v) end
            for _, fn in ipairs(FA.CHECK_HOOKS) do pcall(fn) end
        end, tooltip)
    return y - h
end

local function Slider(child, y, text, min, max, step, get, set, tooltip)
    local _, h = W:Slider(child, text, y, min, max, step, get, set, tooltip)
    return y - h
end

local function Choice(child, y, text, key, default, values, order, tooltip, after)
    local S = FA.Settings()
    local _, h = W:Dropdown(child, text, y, values,
        function() return S[key] or default end,
        function(v)
            S[key] = v
            if after then after(v) end
        end, order, tooltip)
    return y - h
end

FA.VIEWS.settings = function(child, width)
    local S = FA.Settings()
    local y = 0
    local _, h = W:SectionHeader(child, "APPEARANCE", y)
    y = y - h
    local themes, order = {}, {}
    for _, t in ipairs(FA.THEMES) do
        themes[t.key] = t.label
        order[#order + 1] = t.key
    end
    y = Choice(child, y, "Theme", "theme", "teal", themes, order, "Colours of the window, the toast and the tracker.",
        function(v) FA.ApplyTheme(v) end)
    y = Slider(child, y, "Window size (%)", 70, 130, 5,
        function() return (S.scale or 1) * 100 end,
        function(v) S.scale = v / 100; FA.SetScale(v / 100) end)
    y = Slider(child, y, "Window opacity (%)", 50, 100, 1,
        function() return (S.opacity or 0.97) * 100 end,
        function(v) FA.SetOpacity(v / 100) end)
    y = Toggle(child, y, "Animations", "animations", true, "Toasts sliding in, cards opening, bars filling.",
        function(on) Kit.animate = on end)
    y = Toggle(child, y, "Compact cards", "compact", false, "Lower achievement rows, more on screen.",
        function() C_Timer.After(0, FA.Refresh) end)
    y = Choice(child, y, "Order inside a section", "sort", "default",
        { default = "As in WotLK", name = "By name", progress = "Closest to done first" }, { "default", "name", "progress" })
    y = y - 6

    _, h = W:SectionHeader(child, "TOASTS", y)
    y = y - h
    y = Slider(child, y, "Toast time on screen (s)", 2, 10, 1,
        function() return S.toastTime or 4 end, function(v) S.toastTime = v end)
    y = Slider(child, y, "Toast distance from the top", 60, 500, 10,
        function() return S.toastY or 140 end, function(v) S.toastY = v; FA.ResetToast() end)
    y = Choice(child, y, "Sound", "soundName", "UI_ACHIEVEMENT_AWARDED",
        { UI_ACHIEVEMENT_AWARDED = "Achievement", LEVELUP = "Level up", IG_QUEST_LIST_COMPLETE = "Quest complete",
          READY_CHECK = "Ready check", RAID_WARNING = "Raid warning", AUCTION_WINDOW_OPEN = "Auction house" },
        { "UI_ACHIEVEMENT_AWARDED", "LEVELUP", "IG_QUEST_LIST_COMPLETE", "READY_CHECK", "RAID_WARNING", "AUCTION_WINDOW_OPEN" })
    y = Toggle(child, y, "Take a screenshot when earning", "screenshot", false, "Like the old achievement screenshot addons.")
    _, h = W:WideDualButton(child, "Show a test toast", "Play the sound", y,
        function() FA.PreviewToast() end,
        function()
            local kit = SOUNDKIT and SOUNDKIT[S.soundName or "UI_ACHIEVEMENT_AWARDED"]
            if kit then PlaySound(kit, "Master") end
        end)
    y = y - h - 6

    _, h = W:SectionHeader(child, "TRACKER", y)
    y = y - h
    y = Slider(child, y, "Tracker size (%)", 70, 150, 5,
        function() return (S.trackerScale or 1) * 100 end,
        function(v) S.trackerScale = v / 100; FA.StyleTracker() end)
    y = Slider(child, y, "Tracker background (%)", 0, 100, 5,
        function() return (S.trackerAlpha or 0.72) * 100 end,
        function(v) S.trackerAlpha = v / 100; FA.StyleTracker() end)
    y = y - 6

    _, h = W:SectionHeader(child, "ON SCREEN", y)
    y = y - h
    y = Toggle(child, y, "Achievement toasts", "toasts", true, "The banner at the top of the screen when you earn one.")
    y = Toggle(child, y, "Play a sound when earning", "sound", true)
    y = Toggle(child, y, "Show the tracker", "trackerShown", true, "Right-click an achievement to track it.")
    y = Toggle(child, y, "Lock the tracker", "trackerLocked", false, "Unlocked, drag the tracker by its title.")
    y = Toggle(child, y, "Achievement hints in tooltips", "tooltips", true,
        "Critters to /love, pests and bosses to slay, food not yet tasted, books not yet read.")
    y = Toggle(child, y, "Minimap button", "minimapShown", true, nil, function(v)
        if FA.SetMinimapShown then FA.SetMinimapShown(v) end
    end)
    y = y - 6
    _, h = W:SectionHeader(child, "SHARING", y)
    y = y - h
    y = Toggle(child, y, "Share achievements with guild and group", "share", true,
        "Other players with the addon see what you earn, your points and title, and can compare with you.")
    y = Toggle(child, y, "Show what others earn", "showOthers", true, "A chat line when a guild or group member earns one.")
    y = Toggle(child, y, "Announce in guild chat", "announce", false, "A guild chat message with the achievement for everyone.")
    y = y - 6
    _, h = W:SectionHeader(child, "PROGRESS", y)
    y = y - h
    -- Keep the historical accountView setting intact. Earned state now always
    -- means this character; no control should promise a union of completions.
    local scope = Kit.MakeFont(child, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
    scope:SetPoint("TOPLEFT", 20, y); scope:SetWidth(width - 40); scope:SetHeight(32)
    scope:SetText("Achievements and points use this character's progress. Verified completion on another character appears in achievement details in the Wrath view.")
    y = y - 38
    y = Toggle(child, y, "Show keys and IDs in tooltips", "showIDs", false, "For reporting a problem with an achievement.")
    y = y - 6
    _, h = W:WideDualButton(child, "Reset tracker position", "Stop comparing", y,
        function() if FA.ResetTracker then FA.ResetTracker() end end,
        function() if FA.StopCompare then FA.StopCompare() end end)
    y = y - h
    return -y + 10
end
