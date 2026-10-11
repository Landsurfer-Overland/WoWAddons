-------------------------------------------------------------------------------
--  Tracker: the achievements you right-clicked, with their progress, in a
--  small frame you can move (Settings locks it).
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA
local Kit = FA.Kit
local C = Kit.COLORS

local WIDTH, ROW = 250, 30
local tracker = CreateFrame("Frame", "ForeverAchievementsTracker", UIParent)
tracker:SetSize(WIDTH, 30)
tracker:SetFrameStrata("LOW")
tracker:SetClampedToScreen(true)
tracker:SetMovable(true)
tracker:Hide()

local bg = tracker:CreateTexture(nil, "BACKGROUND")
bg:SetAllPoints()
bg:SetColorTexture(C.bg[1], C.bg[2], C.bg[3], 0.72)
Kit.MakeBorder(tracker, 1, 1, 1, 0.08)

local header = CreateFrame("Button", nil, tracker)
header:SetPoint("TOPLEFT")
header:SetPoint("TOPRIGHT")
header:SetHeight(24)
header:RegisterForDrag("LeftButton")
local title = Kit.MakeFont(header, 12, nil, Kit.Accent())
title:SetPoint("LEFT", 10, 0)
title:SetText("Achievements")
header:SetScript("OnDragStart", function()
    if not FA.Settings().trackerLocked then tracker:StartMoving() end
end)
header:SetScript("OnDragStop", function()
    tracker:StopMovingOrSizing()
    Kit.RealignBorders()
    local point, _, rel, x, y = tracker:GetPoint()
    FA.Settings().trackerPos = { point, rel, x, y }
end)
header:SetScript("OnClick", function() FA.Open() end)

local function Place()
    tracker:ClearAllPoints()
    local pos = FA.Settings().trackerPos
    if pos then
        tracker:SetPoint(pos[1], UIParent, pos[2], pos[3], pos[4])
    else
        tracker:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", -250, -260)
    end
end

function FA.ResetTracker()
    FA.Settings().trackerPos = nil
    Place()
end

local rows = {}
local function Row(i)
    if rows[i] then return rows[i] end
    local r, g, b = Kit.Accent()
    local row = CreateFrame("Button", nil, tracker)
    row:SetSize(WIDTH - 16, ROW)
    row:SetPoint("TOPLEFT", 8, -24 - (i - 1) * ROW)
    row:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    row.name = Kit.MakeFont(row, 11, nil, C.text[1], C.text[2], C.text[3], 1)
    row.name:SetPoint("TOPLEFT", 2, -2)
    row.name:SetPoint("RIGHT", -60, 0)
    row.name:SetJustifyH("LEFT")
    row.name:SetWordWrap(false)
    row.value = Kit.MakeFont(row, 11, nil, C.dim[1], C.dim[2], C.dim[3], 1)
    row.value:SetPoint("TOPRIGHT", -2, -2)
    row.track = row:CreateTexture(nil, "ARTWORK")
    row.track:SetColorTexture(1, 1, 1, 0.1)
    row.track:SetHeight(2)
    row.track:SetPoint("BOTTOMLEFT", 2, 7)
    row.track:SetPoint("BOTTOMRIGHT", -2, 7)
    row.fill = row:CreateTexture(nil, "OVERLAY")
    row.fill:SetColorTexture(r, g, b, 1)
    row.fill:SetHeight(2)
    row.fill:SetPoint("LEFT", row.track, "LEFT")
    row:SetScript("OnClick", function(self, button)
        if not self.a then return end
        if button == "RightButton" then FA.ToggleTrack(self.a) else FA.OpenSearch(self.a.name) end
    end)
    rows[i] = row
    return row
end

local function update()
    local d = FA.DB()
    local list = {}
    for key in pairs(d.tracked or {}) do
        local a = FA.BY_KEY[key]
        if a and not FA.Available(a) then
            -- Keep historical tracked keys while unsupported definitions are
            -- inactive, including earned daily records; never poll them.
        elseif a and not d.done[key] then
            list[#list + 1] = a
        else d.tracked[key] = nil end
    end
    table.sort(list, function(p, q) return p.name < q.name end)
    if #list == 0 or FA.Settings().trackerShown == false then
        tracker:Hide()
        return
    end
    for i, a in ipairs(list) do
        local row = Row(i)
        local cur, need = a.progress()
        row.a = a
        row.name:SetText(a.name)
        if not FA.ProgressKnown(cur, need) then
            row.value:SetText("Unavailable")
            row.fill:Hide()
        elseif a.money then
            row.value:SetText(math.floor(cur / 10000) .. "/" .. math.floor(need / 10000) .. "g")
        else
            row.value:SetText(cur .. "/" .. need)
        end
        if FA.ProgressKnown(cur, need) then
            row.fill:SetWidth(math.max(1, (WIDTH - 20) * math.min(1, cur / math.max(1, need))))
            row.fill:Show()
        end
        row:Show()
    end
    for i = #list + 1, #rows do rows[i]:Hide() end
    tracker:SetHeight(28 + #list * ROW)
    tracker:Show()
end
local function Update()
    -- Related tracked tiers share observations for this update only. A later
    -- ticker/event pass gets fresh data through the existing snapshot scope.
    if FA.WithProgressSnapshot then return FA.WithProgressSnapshot(update) end
    return update()
end
FA.UpdateTracker = Update

-- Theme colours, size and opacity from the settings.
function FA.StyleTracker()
    local S = FA.Settings()
    local r, g, b = Kit.Accent()
    bg:SetColorTexture(C.bg[1], C.bg[2], C.bg[3], S.trackerAlpha or 0.72)
    title:SetTextColor(r, g, b, 1)
    for _, row in ipairs(rows) do
        row.fill:SetColorTexture(r, g, b, 1)
        row.name:SetTextColor(C.text[1], C.text[2], C.text[3], 1)
        row.value:SetTextColor(C.dim[1], C.dim[2], C.dim[3], 1)
    end
    tracker:SetScale(S.trackerScale or 1)
end

table.insert(FA.CHECK_HOOKS, Update)
local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
    Place()
    C_Timer.After(4, Update)
end)
C_Timer.NewTicker(3, function() if tracker:IsShown() then Update() end end)
