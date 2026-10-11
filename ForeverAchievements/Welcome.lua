-------------------------------------------------------------------------------
--  Welcome screen: shown once per character, after the first quiet pass over
--  its history. Says this is an alpha, what already counted, the
--  three things worth knowing and lets the player pick a theme.
--  /fach welcome shows it again.
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA
local Kit = FA.Kit
local C = Kit.COLORS

local W, H = 540, 470
local frame

local TIPS = {
    { "Right-click", "an achievement to track it on screen." },
    { "Shift-click", "an achievement to post it in chat." },
    { "/qa", "(or /fach) or the minimap button opens the window." },
}

local function Hex(cr, cg, cb)
    return ("%02x%02x%02x"):format(math.floor(cr * 255 + 0.5), math.floor(cg * 255 + 0.5), math.floor(cb * 255 + 0.5))
end

local function Build(fromHistory)
    local r, g, b = Kit.Accent()
    local f = CreateFrame("Frame", "ForeverAchievementsWelcome", UIParent)
    f:SetSize(W, H)
    f:SetPoint("CENTER", 0, 40)
    f:SetFrameStrata("DIALOG")
    f:SetClampedToScreen(true)
    f:EnableMouse(true)
    f:SetMovable(true)
    f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving)
    f:SetScript("OnDragStop", f.StopMovingOrSizing)
    tinsert(UISpecialFrames, "ForeverAchievementsWelcome")
    Kit.Chrome(f, "Forever Achievements", "", function() f:Hide() end)

    local y = -68
    local head = Kit.MakeFont(f, 16, nil, C.text[1], C.text[2], C.text[3], 1)
    head:SetPoint("TOPLEFT", 30, y)
    head:SetText("Welcome!")
    y = y - 28

    -- Alpha notice, in an accent-edged box.
    local note = CreateFrame("Frame", nil, f)
    note:SetPoint("TOPLEFT", 30, y)
    note:SetPoint("TOPRIGHT", -30, y)
    note:SetHeight(64)
    local nbg = note:CreateTexture(nil, "BACKGROUND")
    nbg:SetAllPoints()
    nbg:SetColorTexture(r, g, b, 0.10)
    Kit.MakeBorder(note, r, g, b, 0.45)
    local ntext = Kit.MakeFont(note, 12, nil, C.text[1], C.text[2], C.text[3], 0.95)
    ntext:SetPoint("TOPLEFT", 12, -10)
    ntext:SetPoint("BOTTOMRIGHT", -12, 10)
    ntext:SetJustifyH("LEFT")
    ntext:SetJustifyV("TOP")
    ntext:SetText("This is an |cffffd100alpha|r for the WoW Forever beta. We are testing it every day, so things "
        .. "will change and a few achievements may not count yet. Please report anything odd on the CurseForge page.")
    y = y - 76

    -- What already counted from the character's history.
    -- The character's totals, filled in each time the screen opens.
    local hist = Kit.MakeFont(f, 13, nil, C.text[1], C.text[2], C.text[3], 1)
    hist:SetPoint("TOPLEFT", 30, y)
    hist:SetPoint("RIGHT", -30, 0)
    hist:SetJustifyH("LEFT")
    f.UpdateTotals = function()
        local pts, _, n = FA.TotalPoints()
        hist:SetText(("This character already has |cff%s%d achievements|r and %d points."):format(Hex(r, g, b), n, pts))
    end
    y = y - 32

    -- Three tips.
    for _, tip in ipairs(TIPS) do
        local dot = f:CreateTexture(nil, "ARTWORK")
        dot:SetSize(6, 6)
        dot:SetPoint("TOPLEFT", 34, y - 5)
        dot:SetColorTexture(r, g, b, 1)
        local line = Kit.MakeFont(f, 12, nil, C.dim[1], C.dim[2], C.dim[3], 1)
        line:SetPoint("TOPLEFT", 48, y)
        line:SetPoint("RIGHT", -30, 0)
        line:SetJustifyH("LEFT")
        line:SetText(("|cff%s%s|r %s"):format(Hex(C.text[1], C.text[2], C.text[3]), tip[1], tip[2]))
        y = y - 22
    end
    y = y - 12

    -- Theme swatches.
    local tl = Kit.MakeFont(f, 12, nil, C.text[1], C.text[2], C.text[3], 1)
    tl:SetPoint("TOPLEFT", 30, y)
    tl:SetText("Pick a theme (more options in Settings):")
    y = y - 24
    local current = FA.Settings().theme or "teal"
    local size, gap = 52, 8
    for i, t in ipairs(FA.THEMES) do
        local sw = CreateFrame("Button", nil, f)
        sw:SetSize(size, 34)
        sw:SetPoint("TOPLEFT", 30 + (i - 1) * (size + gap), y)
        local base = sw:CreateTexture(nil, "BACKGROUND")
        base:SetAllPoints()
        base:SetColorTexture(t.card[1], t.card[2], t.card[3], 1)
        local bar = sw:CreateTexture(nil, "ARTWORK")
        bar:SetPoint("BOTTOMLEFT", 4, 4)
        bar:SetPoint("BOTTOMRIGHT", -4, 4)
        bar:SetHeight(8)
        bar:SetColorTexture(t.accent[1], t.accent[2], t.accent[3], 1)
        local edge = Kit.MakeBorder(sw, 1, 1, 1, 0.15)
        if t.key == current then edge:SetColor(r, g, b, 1) end
        sw:SetScript("OnEnter", function(self)
            GameTooltip:SetOwner(self, "ANCHOR_TOP")
            GameTooltip:AddLine(t.label, 1, 1, 1)
            GameTooltip:Show()
        end)
        sw:SetScript("OnLeave", function() GameTooltip:Hide() end)
        sw:SetScript("OnClick", function()
            FA.Settings().theme = t.key
            FA.ApplyTheme(t.key)
            -- Built again in the new colours, where it stood.
            local point, _, rel, x, yy = f:GetPoint()
            f:Hide()
            frame = nil
            FA.ShowWelcome(fromHistory)
            frame:ClearAllPoints()
            frame:SetPoint(point, UIParent, rel, x, yy)
        end)
    end

    -- Buttons.
    local open = Kit.Button(f, "Open achievements", 220, function()
        f:Hide()
        FA.ShowTab("summary")
    end)
    open:SetPoint("BOTTOMLEFT", 30, 26)
    local close = Kit.Button(f, "Close", 220, function() f:Hide() end)
    close:SetPoint("BOTTOMRIGHT", -30, 26)
    return f
end

function FA.ShowWelcome(fromHistory)
    if not (ns.OriginalUI and ns.OriginalUI.IsEnabled()) then return false end
    if not frame then frame = Build(fromHistory) end
    frame.UpdateTotals()
    if not frame:IsShown() then
        frame:SetAlpha(0)
        frame:Show()
        Kit.Tween("welcomeFade", 0.25, function(e) frame:SetAlpha(e) end)
    end
    return true
end

-- True while the interface is away: the intro cinematic or a movie plays,
-- or the UI is hidden. Esc that skips a movie also closes open windows, so
-- the screen must not open before the intro is over.
local function InterfaceBusy()
    if not UIParent:IsShown() then return true end
    if CinematicFrame and CinematicFrame:IsShown() then return true end
    if MovieFrame and MovieFrame:IsShown() then return true end
    return false
end

local function Log(text)
    print(FA.TAG .. " welcome: " .. text)
end

-- Called by the main file once the first pass over the history is done.
-- Waits for the intro to end, then opens; marked as seen only once the
-- screen has really been on screen, so a skipped intro cannot eat it.
function FA.OnReady(fromHistory)
    if not (ns.OriginalUI and ns.OriginalUI.IsEnabled()) then return end
    if FA.DB().welcomeSeen then return end
    local waited, announced = 0, false
    local function Try()
        if not (ns.OriginalUI and ns.OriginalUI.IsEnabled()) then return end
        if InterfaceBusy() then
            if not announced then
                announced = true
                -- Only with /fach debug: nothing a player needs to read.
                if FA.IsDebug and FA.IsDebug() then Log("waiting for the intro to end.") end
            end
            waited = waited + 1
            if waited < 600 then C_Timer.After(1, Try) end
            return
        end
        local ok, err = pcall(FA.ShowWelcome, fromHistory)
        if not ok then
            frame = nil
            Log("could not open: " .. tostring(err) .. " (/fach welcome to try again)")
            return
        end
        -- Seen once it has stayed up for a moment.
        C_Timer.After(2, function()
            if not (ns.OriginalUI and ns.OriginalUI.IsEnabled()) then return end
            if frame and frame:IsVisible() then
                FA.DB().welcomeSeen = true
            else
                Log("was closed straight away; it will open again on your next login (/fach welcome any time).")
            end
        end)
    end
    C_Timer.After(1.5, Try)
end

FA.SLASH.welcome = function() FA.ShowWelcome() end
