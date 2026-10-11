-- Owned Wrath-style notifications. Preview never calls completion, progression,
-- native alert managers or achievement APIs. One frame and a bounded FIFO.
local _, ns = ...
local LAR = ns.LAR
local A = { queue = {}, MAX_QUEUE = 32, overflow = 0 }
ns.AchievementAlerts = A

A.SOUNDS = {
    -- Keep the existing selection key, but play the supplied recording directly:
    -- Forever accepts sound kit 12891 without audibly playing it.
    { key = "UI_ACHIEVEMENT_AWARDED", name = "Achievement chime (bundled)", file = "Interface\\AddOns\\LegacyAchievementsReforged\\Media\\AchievementEarned.ogg" },
    { key = "LEVELUP", name = "Level up" },
    { key = "IG_QUEST_LIST_COMPLETE", name = "Quest complete" },
    { key = "READY_CHECK", name = "Ready check" },
    { key = "LAR_ACHIEVEMENT_KIT", name = "Classic chime (client kit)", kit = 12891 },
    -- Explicit probes: modern clients may no longer resolve these legacy paths.
    { key = "LAR_CLASSIC_WAV", name = "Classic chime (client WAV)", file = "Sound\\Interface\\UI_Achievement_Toast_Alert.wav" },
    { key = "LAR_CLASSIC_OGG", name = "Classic chime (client OGG)", file = "Sound\\Interface\\UI_Achievement_Toast_Alert.ogg" },
    { key = "LAR_REFORGED_CHIME", name = "Reforged chime (bundled)", file = "Interface\\AddOns\\LegacyAchievementsReforged\\Media\\ReforgedChime.wav" },
}
local function number(value, fallback, low, high)
    if type(value) ~= "number" or value ~= value or value == math.huge or value == -math.huge then return fallback end
    return math.max(low, math.min(high, value))
end
local function message(text) print(LAR.TAG .. " " .. text) end
function A.SelectAchievementRecordingOnce()
    local s = LAR.Settings()
    if s.bundledAchievementSoundVersion == nil then
        s.soundName = "UI_ACHIEVEMENT_AWARDED"
        s.bundledAchievementSoundVersion = 1
    end
end
function A.SoundChoice()
    local key = LAR.Settings().soundName or A.SOUNDS[1].key
    for _, choice in ipairs(A.SOUNDS) do if choice.key == key then return choice end end
    return { key = key, name = tostring(key) } -- preserve an existing user's selection
end
function A.AudioStatus(channel)
    if not GetCVar then return "" end
    local fields = { { "Sound_EnableAllSound", "audio" }, { "Sound_MasterVolume", "master volume" } }
    if channel == "SFX" then
        fields[#fields + 1] = { "Sound_EnableSFX", "effects" }
        fields[#fields + 1] = { "Sound_SFXVolume", "effects volume" }
    end
    local out = {}
    for _, field in ipairs(fields) do
        local ok, value = pcall(GetCVar, field[1])
        value = ok and tonumber(value)
        if value then out[#out + 1] = field[2] .. "=" .. value end
    end
    return #out > 0 and " [" .. table.concat(out, ", ") .. "]" or ""
end
function A.PlaySelectedSound()
    local choice = A.SoundChoice()
    local kit = SOUNDKIT and SOUNDKIT[choice.key]
    if type(kit) ~= "number" then kit = choice.kit end
    local channel = LAR.Settings().alertSoundChannel == "SFX" and "SFX" or "Master"
    local player, source, method
    if choice.file then player, source, method = PlaySoundFile, choice.file, "file"
    elseif type(kit) == "number" then player, source, method = PlaySound, kit, "kit" end
    if not player then return false, choice.name .. " is unavailable on this client." end
    local status = A.AudioStatus(channel)
    local ok, played = pcall(player, source, channel)
    if not ok then return false, "Sound playback failed: " .. tostring(played) .. status end
    if played == false then return false, "Client declined " .. choice.name .. " (" .. method .. " " .. source .. ")." .. status end
    return true, choice.name .. " requested on " .. channel .. " (" .. method .. " " .. source .. "). Audible playback unverified." .. status
end
local function texture(parent, layer, file, width, height, point, relative, x, y, coords)
    local region = parent:CreateTexture(nil, layer)
    region:SetTexture(file); region:SetSize(width, height)
    region:SetPoint(point, parent, relative or point, x or 0, y or 0)
    if coords then region:SetTexCoord(unpack(coords)) end
    return region
end
local function font(parent, style, width, height, point, x, y)
    local region = parent:CreateFontString(nil, "OVERLAY", style)
    region:SetSize(width, height); region:SetPoint(point, parent, point, x, y)
    region:SetJustifyH("CENTER")
    return region
end
function A.Create()
    if A.frame then return A.frame end
    local f = CreateFrame("Frame", "LARAchievementAlert", UIParent)
    f:Hide(); f:SetSize(300, 88); f:SetFrameStrata("DIALOG")
    f:EnableMouse(false); f:SetClampedToScreen(true)
    -- Blizzard's classic alert crop and icon/shield geometry, without inheriting
    -- its scripts, protected frames, global queue, or load-on-demand backend.
    f.background = texture(f, "BACKGROUND", "Interface\\AchievementFrame\\UI-Achievement-Alert-Background",
        300, 88, "CENTER", "CENTER", 0, 0, { 0, .605, 0, .703 })
    f.icon = texture(f, "ARTWORK", nil, 50, 50, "TOPLEFT", "TOPLEFT", 11, -18)
    f.iconFrame = texture(f, "OVERLAY", "Interface\\AchievementFrame\\UI-Achievement-IconFrame",
        72, 72, "TOPLEFT", "TOPLEFT", -1, -8, { 0, .5625, 0, .5625 })
    f.shield = texture(f, "ARTWORK", "Interface\\AchievementFrame\\UI-Achievement-Shields",
        52, 48, "TOPRIGHT", "TOPRIGHT", -9, -19, { 0, .5, 0, .45 })
    f.heading = font(f, "GameFontBlackTiny", 168, 12, "TOPLEFT", 72, -23)
    f.heading:SetText(ACHIEVEMENT_UNLOCKED or "Achievement Earned")
    -- The original title line occupies y=-36..-52, between icon and shield.
    -- The previous 28-high box centered a single line eight units too low.
    f.name = font(f, "GameFontHighlight", 168, 16, "TOPLEFT", 72, -36)
    f.name:SetJustifyV("MIDDLE")
    f.name:SetWordWrap(true)
    f.points = font(f, "GameFontNormal", 40, 20, "CENTER", 0, 0)
    f.points:ClearAllPoints(); f.points:SetPoint("CENTER", f.shield, "CENTER", 0, 0)
    f.points:SetJustifyV("MIDDLE")
    f.preview = font(f, "GameFontNormalSmall", 300, 16, "BOTTOM", 0, -12)
    f.preview:SetText("PREVIEW — no achievement awarded"); f.preview:Hide()
    f.glow = texture(f, "OVERLAY", "Interface\\AchievementFrame\\UI-Achievement-Alert-Glow",
        400, 171, "CENTER", "CENTER", 0, 0, { 0, .78125, 0, .66796875 })
    f.glow:SetBlendMode("ADD"); f.glow:Hide()
    f.shine = texture(f, "OVERLAY", "Interface\\AchievementFrame\\UI-Achievement-Alert-Glow",
        67, 72, "BOTTOMLEFT", "BOTTOMLEFT", 0, 8, { .78125, .912109375, 0, .28125 })
    f.shine:SetBlendMode("ADD"); f.shine:Hide()
    f:SetScript("OnHide", function(self)
        self:SetScript("OnUpdate", nil)
        A.active = nil -- external hide also stops the owned animation
    end)
    A.frame = f
    return f
end
function A.Reposition()
    if not A.frame then return end
    local s = LAR.Settings()
    A.frame:ClearAllPoints()
    A.frame:SetPoint("TOP", UIParent, "TOP", 0, -number(s.toastY, 140, 60, 500))
    A.frame:SetScale(number(s.alertScale, 1, .75, 1.5))
end
function A.Finish()
    A.active = nil
    A.frame:SetScript("OnUpdate", nil); A.frame:Hide()
    A.StartNext()
end
function A.Update(self, elapsed)
    local state = A.active
    if not state then self:SetScript("OnUpdate", nil); return end
    if type(elapsed) ~= "number" or elapsed ~= elapsed or elapsed < 0 or elapsed == math.huge then return end
    state.time = state.time + elapsed
    local time, alpha = state.time, 1
    local entrance, exit = state.animate and .2 or 0, state.animate and 1.5 or 0
    if time >= entrance + state.hold + exit then A.Finish(); return end
    if time < entrance then alpha = time / entrance
    elseif time > entrance + state.hold then alpha = 1 - (time - entrance - state.hold) / exit end
    if alpha ~= state.alpha then self:SetAlpha(alpha); state.alpha = alpha end
    if state.animate and time < .7 then
        self.glow:SetAlpha(time < .2 and time / .2 or 1 - (time - .2) / .5)
    elseif self.glow:IsShown() then self.glow:Hide() end
    if state.animate and time < 1.05 then
        self.shine:ClearAllPoints()
        self.shine:SetPoint("BOTTOMLEFT", self, "BOTTOMLEFT", math.max(0, time - .2) / .85 * 240, 8)
        self.shine:SetAlpha(time < .2 and time / .2 or math.min(1, (1.05 - time) / .5))
    elseif self.shine:IsShown() then self.shine:Hide() end
end
function A.Start(record)
    local f, s = A.Create(), LAR.Settings()
    A.Reposition()
    f.icon:SetTexture(record.icon or ns.ICONS and ns.ICONS[record.id] or 236376)
    f.name:SetHeight(28) -- retain room for wrapped names while measuring
    f.name:SetText(record.name or "Achievement")
    f.name:SetHeight(math.max(16, math.min(28, f.name:GetStringHeight())))
    local points = record.pts
    f.points:SetText(type(points) == "number" and points == points and tostring(points) or "")
    f.preview:SetShown(record.preview == true)
    local animate = s.animations ~= false
    f.glow:SetShown(animate); f.shine:SetShown(animate)
    f.glow:SetAlpha(0); f.shine:SetAlpha(0)
    A.active = { record = record, time = 0, hold = number(s.toastTime, 4, 2, 10), animate = animate, alpha = animate and 0 or 1 }
    f:SetAlpha(A.active.alpha); f:SetScript("OnUpdate", A.Update); f:Show()
    if s.sound ~= false then
        local ok, reason = A.PlaySelectedSound()
        if not ok then message(reason) end
    end
end
function A.StartNext()
    if A.active then return end
    local record = table.remove(A.queue, 1)
    if not record and A.overflow > 0 then
        record = { name = A.overflow .. " additional achievements earned", icon = 236376 }
        A.overflow = 0
    end
    if record then A.Start(record) end
end
function A.Enqueue(record)
    if LAR.Settings().toasts == false then return false end
    -- A real unlock takes priority over a test. Neither path touches saves.
    if A.active and A.active.record.preview then A.StopPreview() end
    if #A.queue >= A.MAX_QUEUE then A.overflow = A.overflow + 1; return false end
    A.queue[#A.queue + 1] = { name = record.name, icon = record.icon, id = record.id, pts = record.pts }
    A.StartNext()
    return true
end
function A.Preview()
    if A.active and not A.active.record.preview then return false, "Wait for the earned achievement notification to finish." end
    A.Start({ name = "Reforged Test Achievement", icon = 132347, pts = 10, preview = true })
    return true, "Preview only. No progress or points awarded."
end
function A.StopPreview()
    if not A.active or not A.active.record.preview then return false, "No preview is playing." end
    A.Finish()
    return true, "Preview stopped."
end
LAR.SLASH.alert = function(input)
    local command = (input or ""):lower():match("^%s*(.-)%s*$")
    local ok, reason
    if command == "test" or command == "" then ok, reason = A.Preview()
    elseif command == "sound" then ok, reason = A.PlaySelectedSound()
    elseif command == "stop" then ok, reason = A.StopPreview()
    else reason = "Use /lar alert test|sound|stop." end
    message(reason)
end
