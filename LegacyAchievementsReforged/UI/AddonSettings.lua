-- Accessible addon settings, independent of the quarantined alpha window.
local _, ns = ...
local LAR, Alerts = ns.LAR, ns.AchievementAlerts
local U = {}
ns.AddonSettings = U
local function combat() return InCombatLockdown and InCombatLockdown() end
local function label(parent, text, x, y, width, height, style)
    local f = parent:CreateFontString(nil, "OVERLAY", style or "GameFontNormal")
    f:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y); f:SetSize(width, height)
    f:SetJustifyH("LEFT"); f:SetWordWrap(true); f:SetText(text)
    return f
end
local function button(parent, text, x, y, width, callback)
    local f = CreateFrame("Button", nil, parent, "UIPanelButtonTemplate")
    f:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y); f:SetSize(width, 26); f:SetText(text)
    f:SetScript("OnClick", callback)
    return f
end
function U.Status(ok, text)
    local f = U.panel and U.panel.status
    if f then
        f:SetText(text or "")
        if ok then f:SetTextColor(.6, 1, .6) else f:SetTextColor(1, .7, .3) end
    end
end
function U.Create()
    if U.panel then return U.panel end
    local p = CreateFrame("Frame", "LegacyAchievementsReforgedSettings", UIParent, "BackdropTemplate")
    p.name = "Legacy Achievements Reforged"; p:SetSize(560, 560); p:Hide()
    U.panel = p
    label(p, p.name, 16, -16, 528, 28, "GameFontNormalLarge")
    label(p, "Achievement Alerts\nPreviews never award progress or points. Client audio settings still apply.",
        16, -50, 528, 40, "GameFontHighlightSmall")
    p.checks, p.sliders = {}, {}
    local function check(text, key, y)
        local f = CreateFrame("CheckButton", nil, p, "UICheckButtonTemplate")
        f:SetPoint("TOPLEFT", p, "TOPLEFT", 16, y); f:SetSize(26, 26)
        label(p, text, 48, y - 4, 470, 20)
        f.key = key; p.checks[key] = f
        f:SetScript("OnClick", function(self)
            LAR.Settings()[key] = self:GetChecked() == true
            if key == "animations" then LAR.Kit.animate = LAR.Settings()[key] end
        end)
    end
    check("Enable achievement popups", "toasts", -100)
    check("Play sound on unlock / popup preview", "sound", -130)
    check("Fade, glow and shine animations", "animations", -160)
    p.sound = button(p, "", 16, -204, 320, function()
        local current, choices, index = Alerts.SoundChoice(), Alerts.SOUNDS, 0
        for i, choice in ipairs(choices) do if choice.key == current.key then index = i; break end end
        LAR.Settings().soundName = choices[index % #choices + 1].key
        U.Sync()
    end)
    p.channel = button(p, "", 346, -204, 198, function()
        LAR.Settings().alertSoundChannel = LAR.Settings().alertSoundChannel == "SFX" and "Master" or "SFX"
        U.Sync()
    end)
    local function slider(text, key, y, low, high, step, fallback, suffix)
        local textRegion = label(p, "", 16, y + 22, 528, 20)
        local f = CreateFrame("Slider", nil, p, "BackdropTemplate")
        f:SetPoint("TOPLEFT", p, "TOPLEFT", 16, y); f:SetSize(510, 18)
        f:SetOrientation("HORIZONTAL"); f:SetMinMaxValues(low, high); f:SetValueStep(step)
        if f.SetObeyStepOnDrag then f:SetObeyStepOnDrag(true) end
        f:SetBackdrop({ bgFile = "Interface\\Buttons\\UI-SliderBar-Background", edgeFile = "Interface\\Buttons\\UI-SliderBar-Border",
            tile = true, tileSize = 8, edgeSize = 8, insets = { left = 3, right = 3, top = 6, bottom = 6 } })
        f:SetThumbTexture("Interface\\Buttons\\UI-SliderBar-Button-Horizontal")
        f.key, f.fallback, f.title, f.suffix, f.label = key, fallback, text, suffix, textRegion
        p.sliders[key] = f
        f:SetScript("OnValueChanged", function(self, value)
            value = math.floor(value / step + .5) * step
            self.label:SetText(self.title .. ": " .. string.format(step < 1 and "%.2f" or "%d", value) .. self.suffix)
            if U.syncing then return end
            LAR.Settings()[key] = value
            if key ~= "toastTime" then Alerts.Reposition() end
        end)
    end
    slider("Hold time", "toastTime", -264, 2, 10, 1, 4, " s")
    slider("Distance from top", "toastY", -322, 60, 500, 10, 140, "")
    slider("Popup scale", "alertScale", -380, .75, 1.5, .05, 1, "×")
    p.test = button(p, "Test popup", 16, -426, 164, function() U.Status(Alerts.Preview()) end)
    p.soundTest = button(p, "Play selected sound", 194, -426, 172, function() U.Status(Alerts.PlaySelectedSound()) end)
    p.stop = button(p, "Stop preview", 380, -426, 164, function() U.Status(Alerts.StopPreview()) end)
    p.bundledSound = button(p, "Use bundled Reforged chime", 16, -460, 250, function()
        LAR.Settings().soundName = "LAR_REFORGED_CHIME"
        U.Sync(); U.Status(Alerts.PlaySelectedSound())
    end)
    p.achievementSound = button(p, "Use original achievement chime", 278, -460, 266, function()
        LAR.Settings().soundName = "UI_ACHIEVEMENT_AWARDED"
        U.Sync(); U.Status(Alerts.PlaySelectedSound())
    end)
    p.status = label(p, "Change settings, then test the popup or sound. No achievement is awarded.",
        16, -494, 528, 54, "GameFontHighlightSmall")
    p:SetScript("OnShow", U.Sync)
    U.Sync()
    return p
end
function U.Sync()
    if not U.panel then return end
    local p, s = U.panel, LAR.Settings()
    U.syncing = true
    for key, f in pairs(p.checks) do f:SetChecked(s[key] ~= false) end
    for key, f in pairs(p.sliders) do
        local value = s[key]
        if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then value = f.fallback end
        f:SetValue(value)
        -- OnValueChanged need not fire if a re-open uses the same value.
        f:GetScript("OnValueChanged")(f, f:GetValue())
    end
    p.sound:SetText("Sound: " .. Alerts.SoundChoice().name)
    p.channel:SetText("Channel: " .. (s.alertSoundChannel == "SFX" and "SFX" or "Master"))
    U.syncing = false
end
function U.Register()
    if U.registered then return true end
    if combat() then U.registerPending = true; return false end
    local p = U.Create()
    if Settings and Settings.RegisterCanvasLayoutCategory and Settings.RegisterAddonCategory then
        U.category = U.category or Settings.RegisterCanvasLayoutCategory(p, p.name)
        Settings.RegisterAddonCategory(U.category)
        U.mode = "modern"
    elseif InterfaceOptions_AddCategory then
        InterfaceOptions_AddCategory(p); U.mode = "legacy"
    else U.mode = "standalone" end
    U.registered, U.registerPending = true, false
    return true
end
function U.Open()
    if combat() then
        U.openPending = true
        print(LAR.TAG .. " Addon settings will open when combat ends. /lar alert test can preview in combat.")
        return
    end
    U.Register()
    if U.mode == "modern" and Settings.OpenToCategory then
        Settings.OpenToCategory(U.category:GetID())
    elseif U.mode == "legacy" and InterfaceOptionsFrame_OpenToCategory then
        InterfaceOptionsFrame_OpenToCategory(U.panel)
    else
        local p = U.panel
        if not U.standalone then
            p:SetPoint("CENTER", UIParent, "CENTER", 0, 0); p:SetFrameStrata("DIALOG"); p:EnableMouse(true)
            p:SetBackdrop({ bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background", edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
                tile = true, tileSize = 32, edgeSize = 32, insets = { left = 11, right = 11, top = 12, bottom = 12 } })
            button(p, "Close", 452, -12, 80, function() p:Hide() end)
            if UISpecialFrames then table.insert(UISpecialFrames, "LegacyAchievementsReforgedSettings") end
            U.standalone = true
        end
        p:Show()
    end
end
LAR.SLASH.settings = U.Open
local events = CreateFrame("Frame")
U.events = events
events:RegisterEvent("PLAYER_LOGIN"); events:RegisterEvent("PLAYER_REGEN_ENABLED")
events:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_LOGIN" then Alerts.SelectAchievementRecordingOnce() end
    if event == "PLAYER_LOGIN" or U.registerPending then U.Register() end
    if event == "PLAYER_REGEN_ENABLED" and U.openPending then U.openPending = false; U.Open() end
end)
if IsLoggedIn and IsLoggedIn() then Alerts.SelectAchievementRecordingOnce(); U.Register() end
