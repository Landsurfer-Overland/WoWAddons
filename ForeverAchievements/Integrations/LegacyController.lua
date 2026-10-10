-- Opt-in full-window presentation. Original native lifecycle, pages, handlers,
-- progression, and the standalone custom achievement window remain intact.
local _, ns = ...
local FA, R, B = ns.FA, ns.LegacyReadOnly, ns.LegacyWindowBridge
local C = { hooked = setmetatable({}, { __mode = "k" }), state = "Disabled" }
ns.LegacyUIController = C
local function enabled() return FA.Settings().legacyUI == true end
local function notify(message) print(FA.TAG .. " Legacy UI: " .. message) end
local function combat()
    local r = R.Call(InCombatLockdown)
    return r and r[1] == true
end
local function gamepad()
    local r = R.Call(R.Field(InputUtil, "IsGamepadUIEnabled"))
    return r and r[1] == true
end
local function shown(root)
    local r = R.Method(root, "IsShown")
    return r and r[1] == true
end
function C:Release(state)
    self.busy = true
    if self.dragging and self.cover then
        -- Drag cleanup is best effort. Native restoration must still run if
        -- a geometry setter fails while combat/input mode changes the frame.
        pcall(self.cover.StopMovingOrSizing, self.cover)
        pcall(self.SavePosition, self)
        self.dragging = false
    end
    local ok, err = true, nil
    if self.bridge then
        local called, restored, reason = pcall(self.bridge.Restore, self.bridge)
        if called then ok, err = restored, reason else ok, err = false, restored end
    end
    self.busy = false
    if ok then
        self.bridge = nil
        if self.cover then pcall(self.cover.Hide, self.cover) end
        self.restorePending = false
        self.state = state
    else
        self.restorePending = true
        self.state = "Restoration pending: " .. tostring(err)
    end
    return ok
end
function C:Fail(reason)
    if self.ui then self.ui.rendering = false end
    self:Release("Fallback: " .. tostring(reason))
    if self.lastError ~= self.state then
        notify(self.state .. (self.restorePending and ". Restoration will retry after combat." or ". Native Legacy remains available."))
        self.lastError = self.state
    end
end
function C:Guard(fn)
    local ok, err = pcall(fn)
    if not ok then self:Fail(err) end
    return ok
end
local anchors = { TOPLEFT = { 0, 1 }, TOP = { .5, 1 }, TOPRIGHT = { 1, 1 }, LEFT = { 0, .5 },
    CENTER = { .5, .5 }, RIGHT = { 1, .5 }, BOTTOMLEFT = { 0, 0 }, BOTTOM = { .5, 0 }, BOTTOMRIGHT = { 1, 0 } }
function C:Preset()
    local name = R.Text(FA.Settings().legacyUISize)
    local sizes = ns.WrathAchievementUI.PRESETS
    if not name or not sizes[name] then name = "Standard" end
    return name, sizes[name]
end
function C:RestorePosition()
    if not self.cover or self.dragging then return end
    local saved = FA.Settings().legacyUIPosition
    local point, relativePoint = R.Text(R.Field(saved, "point")), R.Text(R.Field(saved, "relativePoint"))
    local x, y = R.Number(R.Field(saved, "x")), R.Number(R.Field(saved, "y"))
    if not anchors[point] or not anchors[relativePoint] or not x or not y then
        point, relativePoint, x, y = "CENTER", "CENTER", 0, 0
    end
    local width, height = UIParent:GetWidth(), UIParent:GetHeight()
    local scale = self.cover:GetScale()
    local fw, fh = self.cover:GetWidth() * scale, self.cover:GetHeight() * scale
    local a, b = anchors[point], anchors[relativePoint]
    local left, bottom = width * b[1] + x * scale - fw * a[1], height * b[2] + y * scale - fh * a[2]
    left = math.max(10, math.min(width - fw - 10, left))
    bottom = math.max(10, math.min(height - fh - 10, bottom))
    x, y = (left + fw * a[1] - width * b[1]) / scale, (bottom + fh * a[2] - height * b[2]) / scale
    self.cover:ClearAllPoints()
    self.cover:SetPoint(point, UIParent, relativePoint, x, y)
end
function C:SavePosition()
    self.dragging = false
    if not self.cover then return end
    local r = R.Method(self.cover, "GetPoint", 1)
    if not r or r[2] ~= nil and r[2] ~= UIParent then return end
    local point, relativePoint, x, y = R.Text(r[1]), R.Text(r[3]), R.Number(r[4]), R.Number(r[5])
    if anchors[point] and anchors[relativePoint] and x and y then
        FA.Settings().legacyUIPosition = { point = point, relativePoint = relativePoint, x = x, y = y }
        self:RestorePosition()
    end
end
function C:Fit()
    local width, height = UIParent:GetWidth(), UIParent:GetHeight()
    assert(width > 20 and height > 20, "UIParent dimensions unavailable")
    local name, size = self:Preset()
    self.cover:SetSize(size[1], size[2] + 140)
    self.cover:SetScale(math.min(1, (width - 20) / size[1], (height - 20) / (size[2] + 140)))
    self:RestorePosition()
    self.ui.sizePreset = name
    self.ui:Fit(self.cover)
end
function C:SetSizePreset(input)
    local normalized = type(input) == "string" and input:lower() or ""
    local name = normalized == "compact" and "Compact" or normalized == "standard" and "Standard" or
        normalized == "large" and "Large"
    if not name then notify("Use /fa legacyui size compact|standard|large."); return false end
    FA.Settings().legacyUISize = name
    if self.ui and self.cover and not combat() then
        if enabled() and self.root and shown(self.root) then self:Refresh()
        else self:Guard(function() self:Fit() end) end
    end
    return true
end
function C:CycleSizePreset()
    local name = self:Preset()
    self:SetSizePreset(name == "Compact" and "Standard" or name == "Standard" and "Large" or "Compact")
end
function C:ResetPosition()
    FA.Settings().legacyUIPosition = nil
    if self.cover then
        self.cover:StopMovingOrSizing(); self.dragging = false
        if not combat() then self:Guard(function() self:RestorePosition() end) end
    end
    notify("Window position reset. Achievement progress is preserved.")
end
function C:ReportUnmapped()
    local model = self.ui and self.ui.model
    if not model then notify("Open the enabled Legacy window first to obtain the current classification report."); return end
    local rows = model.unmapped or {}
    notify(tostring(#rows) .. " observed challenges use Feats of Strength > Other Legacy Challenges (navigation only).")
    for i = 1, math.min(30, #rows) do
        local row = rows[i]
        notify(tostring(row.id) .. " | " .. tostring(row.name) .. " | " .. tostring(row.nativeCategory) .. " | " .. tostring(row.reason))
    end
    if #rows > 30 then notify("Showing the first 30 records; the full list is retained in the current view model.") end
end
function C:Refresh()
    if self.busy then return end
    if not enabled() then self:Release("Disabled"); return end
    if gamepad() then self:Release("Native interface in gamepad mode"); return end
    if not self.root or not shown(self.root) then return end
    if combat() then
        self.pending = true
        self:Release("Waiting for combat to end")
        return
    end
    self:Guard(function()
        self.busy = true
        self:Fit()
        local model = ns.LegacyPresentation.Build(self.page, self.nativeCatalog)
        self.nativeCatalog = not model.native.partial and model.native or nil
        self.ui:SetModel(model)
        if not self.bridge then self.bridge = B.New(self.root) end
        self.bridge:Mount(self.ui.tab, self.ui.nativeHost)
        self.cover:Show()
        self.busy = false
        self.state, self.lastError, self.pending = "Enabled", nil, false
    end)
    self.busy = false
end
function C:Schedule()
    if not enabled() or not self.root or not shown(self.root) or self.queued then return end
    self.queued = true
    local timer = R.Field(C_Timer, "After")
    local function run()
        self.queued = false
        if enabled() then self:Refresh() end
    end
    if type(timer) == "function" then timer(.25, run) else run() end
end
function C:QueueAttach()
    if self.attachQueued then return end
    self.attachQueued = true
    local function run()
        self.attachQueued = false
        if enabled() then self:Attach() end
    end
    local timer = R.Field(C_Timer, "After")
    if type(timer) == "function" then timer(0, run) else run() end
end
function C:Close()
    local root = self.root
    if not root then return end
    if combat() and B.Blocked(root) then
        self:Fail("Native close is protected during combat"); return
    end
    if type(HideUIPanel) == "function" then HideUIPanel(root) else root:Hide() end
end
function C:NativeSelection()
    if self.busy or not enabled() or not self.bridge or not shown(self.root) then return end
    -- CallbackRegistry stores callbacks by owner, not registration order.
    -- Read the final currentPage after every native callback has completed.
    if self.selectionQueued then return end
    local timer = R.Field(C_Timer, "After")
    if type(timer) ~= "function" then
        self:Release("Fallback: Native page coordination unavailable"); return
    end
    self.selectionQueued = true
    timer(0, function()
        self.selectionQueued = false
        if not enabled() or not self.bridge or not shown(self.root) then return end
        local id = R.Number(R.Field(self.root, "currentPage"))
        local view = id == 1 and "rewards" or id == 3 and "trees" or "achievements"
        self:Guard(function() self.ui:SetTab(view) end)
        self:Refresh()
    end)
end
function C:InputHooks()
    if self.inputHooked then return end
    local high, pad, mkb = R.Field(InputUtil, "RegisterForHighPrioInterfaceTransitions"),
        R.Field(InputUtil, "RegisterGamepadInit"), R.Field(InputUtil, "RegisterMKBInit")
    if type(high) ~= "function" or type(pad) ~= "function" or type(mkb) ~= "function" then return end
    self.inputHooked = true
    high(self, nil)
    pad(self, function()
        if enabled() or self.bridge then self:Release("Native interface in gamepad mode") end
    end)
    mkb(self, function()
        -- RegisterMKBInit immediately invokes the current-mode callback. The
        -- enclosing Attach already handles that first invocation.
        if enabled() and self.inputReady then self:QueueAttach() end
    end)
    self.inputReady = true
end
function C:Attach()
    if self.restorePending and not self:Release(enabled() and "Waiting for native Legacy frame" or "Disabled") then return end
    if not enabled() then self:Release("Disabled"); return end
    if combat() then self.pending = true; self.state = "Waiting for combat to end"; return end
    if not self:Guard(function() self:InputHooks() end) then return end
    if gamepad() then self:Release("Native interface in gamepad mode"); return end
    local root, page = LegacySystemFrame, R.Field(LegacySystemFrame, "ChallengesPage")
    if not page then self.state = "Waiting for native Legacy frame"; return end
    if B.Blocked(root) or B.Blocked(page) then self:Fail("Native Legacy frame is protected or incompatible"); return end
    self:Guard(function()
        self.root, self.page = root, page
        if not self.cover then
            self.cover = CreateFrame("Frame", "FAWrathLegacyCover", UIParent)
            self.cover:Hide()
            local _, size = self:Preset()
            self.cover:SetSize(size[1], size[2] + 140)
            self.cover:SetPoint("CENTER", UIParent, "CENTER", 0, 0)
            self.cover:SetMovable(true); self.cover:SetClampedToScreen(true)
            self.cover:EnableMouse(false)
            self.cover:SetFrameStrata(root:GetFrameStrata())
            self.cover:SetFrameLevel(root:GetFrameLevel() + 10)
        end
        if not self.ui then
            self.ui = ns.WrathAchievementUI.Create(self.cover, function(fn) return self:Guard(fn) end,
                function() self:Refresh() end, {
                    onTab = function() self:Refresh() end,
                    onClose = function() self:Close() end,
                    onDragStart = function() self.dragging = true end,
                    onPositionSave = function() self:SavePosition() end,
                    onSizePresetCycle = function() self:CycleSizePreset() end,
                })
        end
        if not self.hooked[root] then
            root:HookScript("OnShow", function()
                if enabled() then
                    self.nativeCatalog = nil
                    local id = R.Number(R.Field(root, "currentPage"))
                    self.ui.tab = id == 1 and "rewards" or id == 3 and "trees" or "achievements"
                    self:Attach()
                end
            end)
            root:HookScript("OnHide", function() self:Release(enabled() and "Enabled; native window closed" or "Disabled") end)
            root:HookScript("OnSizeChanged", function() self:Schedule() end)
            self.hooked[root] = true
        end
        -- Observe the completed native selection event. Do not replace any
        -- native method, callback, provider, global toggle, or frame script.
        if not self.selectionHooked then
            local register = R.Field(EventRegistry, "RegisterCallback")
            assert(type(register) == "function", "Native selection observation unavailable")
            register(EventRegistry, "Legacy.SelectPage", function() self:NativeSelection() end, self)
            self.selectionHooked = true
        end
        if not self.currencyHooked then
            -- Verified build 70338 event, also emitted after native tree edits.
            -- Re-read authoritative values; never change the currency object.
            EventRegistry:RegisterCallback("Legacy.UpdateCurrencyInfo", function()
                if enabled() then self.nativeCatalog = nil; self:Schedule() end
            end, self)
            self.currencyHooked = true
        end
        if not self.hooked[UIParent] then
            UIParent:HookScript("OnSizeChanged", function() self:Schedule() end)
            self.hooked[UIParent] = true
        end
        if not self.bridge then
            local id = R.Number(R.Field(root, "currentPage"))
            self.ui.tab = id == 1 and "rewards" or id == 3 and "trees" or "achievements"
        end
        self.state = "Enabled; native window closed"
        self:Refresh()
    end)
end
function C:SetEnabled(value)
    FA.Settings().legacyUI = value == true
    if value then self:Attach()
    else
        self.pending, self.queued = false, false
        self:Release("Disabled")
    end
    notify(self.state)
end
FA.SLASH.legacyui = function(input)
    input = (input or ""):lower():match("^%s*(.-)%s*$")
    if input == "on" then C:SetEnabled(true)
    elseif input == "off" then C:SetEnabled(false)
    elseif input == "reset" then C:ResetPosition()
    elseif input == "unmapped" then C:ReportUnmapped()
    elseif input:match("^size%s+") then
        if C:SetSizePreset(input:match("^size%s+(.+)$")) then notify("Window size: " .. C:Preset()) end
    else notify(C.state .. ". Use /fa legacyui on|off, size compact|standard|large, reset, or unmapped.") end
end
local events = CreateFrame("Frame")
for _, event in ipairs({ "PLAYER_LOGIN", "ADDON_LOADED", "PLAYER_REGEN_ENABLED", "PLAYER_REGEN_DISABLED",
    "INPUT_DEVICE_INTERFACE_TRANSITION", "ACHIEVEMENT_EARNED", "CRITERIA_UPDATE", "CRITERIA_COMPLETE",
    "RECEIVED_ACHIEVEMENT_LIST", "MAJOR_FACTION_RENOWN_LEVEL_CHANGED" }) do
    pcall(events.RegisterEvent, events, event)
end
events:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_REGEN_ENABLED" and C.restorePending then
        C:Release(enabled() and "Waiting for native Legacy frame" or "Disabled")
    end
    if not enabled() then return end
    if event == "PLAYER_REGEN_DISABLED" then
        C.pending = true; C:Release("Waiting for combat to end")
    elseif event == "INPUT_DEVICE_INTERFACE_TRANSITION" then
        if gamepad() then C:Release("Native interface in gamepad mode") else C:QueueAttach() end
    elseif event == "PLAYER_LOGIN" or event == "ADDON_LOADED" or event == "PLAYER_REGEN_ENABLED" then C:Attach()
    else C.nativeCatalog = nil; C:Schedule() end
end)
FA.EARN_HOOKS[#FA.EARN_HOOKS + 1] = function() C:Schedule() end
FA.CHECK_HOOKS[#FA.CHECK_HOOKS + 1] = function() C:Schedule() end
-- File load does not open, load, hook or mutate the native Legacy window.
