-- Opt-in full-window presentation. Original native lifecycle, pages, handlers,
-- progression, and the standalone custom achievement window remain intact.
local _, ns = ...
local FA, R, B = ns.FA, ns.LegacyReadOnly, ns.LegacyWindowBridge
local C = { hooked = setmetatable({}, { __mode = "k" }), state = "Disabled",
    dirtyData = true, dirtyLayout = true, dirtyMount = true, lifecycle = 0, refreshTicket = 0, nativeRevision = 0,
    NATIVE_MAX_AGE = 30, NATIVE_MAX_UNTIMED_REUSES = 8, nativeDataReuses = 0 }
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
local function perfBegin(name)
    local perf = ns.LegacyPerf
    if perf and type(perf.Begin) == "function" then return perf.Begin(name) end
end
local function perfFinish(token)
    local perf = ns.LegacyPerf
    if token and perf and type(perf.Finish) == "function" then perf.Finish(token) end
end
local function perfCount(name)
    local perf = ns.LegacyPerf
    if perf and type(perf.Count) == "function" then perf.Count(name, 1) end
end
local function measured(name, fn)
    local token = perfBegin(name)
    local ok, result = pcall(fn)
    perfFinish(token)
    if not ok then error(result, 0) end
    return result
end
function C:Dirty(reason)
    if reason == "native" or reason == "open" then
        self.nativeRevision = self.nativeRevision + 1
        self.nativeCatalog, self.dirtyData = nil, true
    elseif reason == "custom" or reason == nil then self.dirtyData = true
    elseif reason == "layout" then self.dirtyLayout = true
    elseif reason == "tab" or reason == "statistics" then self.dirtyRender = true end
    if reason ~= "pending" then self.dirtyMount = true end
end
function C:CancelQueuedWork()
    self.lifecycle = self.lifecycle + 1
    self.refreshTicket = self.refreshTicket + 1
    self.queued, self.selectionQueued, self.attachQueued = false, false, false
    self.attachPending = false
    if self.ui and type(self.ui.CancelPending) == "function" then pcall(self.ui.CancelPending, self.ui) end
end
function C:Release(state)
    self:CancelQueuedWork()
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
    self.dirtyMount = true
    return ok
end
function C:Fail(reason)
    if self.ui then self.ui.rendering = false end
    self.mounting = false
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
    measured("window.fit", function()
        local width, height = UIParent:GetWidth(), UIParent:GetHeight()
        assert(width > 20 and height > 20, "UIParent dimensions unavailable")
        local name, size = self:Preset()
        self.cover:SetSize(size[1], size[2] + 140)
        self.cover:SetScale(math.min(1, (width - 20) / size[1], (height - 20) / (size[2] + 140)))
        self:RestorePosition()
        self.ui.sizePreset = name
        self.ui:Fit(self.cover, true)
        self.layoutState = { width = width, height = height, scale = UIParent:GetScale(), preset = name }
    end)
end
function C:LayoutChanged()
    local state = self.layoutState
    return not state or state.width ~= UIParent:GetWidth() or state.height ~= UIParent:GetHeight()
        or state.scale ~= UIParent:GetScale() or state.preset ~= self:Preset()
end
local function nativeClock()
    local r = R.Call(GetTime)
    local now = r and R.Number(r[1])
    if now and now >= 0 then return now end
end
function C:NativeStale()
    local now = nativeClock()
    if now ~= nil then
        return self.nativeCatalogAt == nil or now < self.nativeCatalogAt or now - self.nativeCatalogAt >= self.NATIVE_MAX_AGE
    end
    -- Missing/secret clocks cannot establish an age of zero. Fall back to a
    -- bounded number of actual data refreshes, without another event ticker.
    return self.nativeDataReuses >= self.NATIVE_MAX_UNTIMED_REUSES
end
function C:SetSizePreset(input)
    local normalized = type(input) == "string" and input:lower() or ""
    local name = normalized == "compact" and "Compact" or normalized == "standard" and "Standard" or
        normalized == "large" and "Large"
    if not name then notify("Use /fa legacyui size compact|standard|large."); return false end
    FA.Settings().legacyUISize = name
    if self.ui and self.cover and not combat() then
        if enabled() and self.root and shown(self.root) then self:Refresh("layout")
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
function C:Refresh(reason)
    self:Dirty(reason)
    if self.busy then self:QueueRefresh(); return false end
    if not enabled() then self:Release("Disabled"); return end
    if gamepad() then self:Release("Native interface in gamepad mode"); return end
    if not self.root or not shown(self.root) then return false end
    if combat() then
        self.pending = true
        self:Release("Waiting for combat to end")
        return false
    end
    -- An immediate opening/selection pass consumes earlier queued work. Its
    -- timer remains harmless even if it runs after the window closes/reopens.
    self.refreshTicket, self.queued = self.refreshTicket + 1, false
    if self.dirtyData and self.nativeCatalog then
        self.nativeDataReuses = self.nativeDataReuses + 1
        if self:NativeStale() then self:Dirty("native"); perfCount("native.cache.expired") end
    end
    -- Geometry callbacks request a comparison, not an unconditional relayout.
    -- Our own native-page setters can emit the same size notification again.
    local layout = self:LayoutChanged()
    local data = self.dirtyData or not self.ui.model
    local render, mount = self.dirtyRender, self.dirtyMount or not self.bridge
    if not layout and not data and not render and not mount then return true end
    self.dirtyData, self.dirtyLayout, self.dirtyRender, self.dirtyMount = false, false, false, false
    local token = perfBegin("controller.refresh")
    local ok = self:Guard(function()
        self.busy = true
        if layout then self:Fit() end
        if data then
            local revision = self.nativeRevision
            local newNative = self.nativeCatalog == nil
            local model = ns.LegacyPresentation.Build(self.page, self.nativeCatalog)
            -- Retain bounded partial catalogs until a genuine native change;
            -- tab and character updates must not retry the entire native scan.
            if revision == self.nativeRevision then
                self.nativeCatalog = model.native
                if newNative then self.nativeCatalogAt, self.nativeDataReuses = nativeClock(), 0 end
            end
            self.currencyValue, self.currencyObserved = model.native.points, true
            self.ui:SetModel(model)
        elseif layout or render then self.ui:Render() end
        if not self.bridge then self.bridge = B.New(self.root) end
        self.mounting = true
        measured("native.mount", function() self.bridge:Mount(self.ui.tab, self.ui.nativeHost) end)
        self.mounting = false
        if not shown(self.cover) then self.cover:Show() end
        self.busy = false
        self.state, self.lastError, self.pending = "Enabled", nil, false
    end)
    self.busy, self.mounting = false, false
    perfFinish(token)
    if ok and (self.dirtyData or self.dirtyLayout or self.dirtyRender or self.dirtyMount) then self:QueueRefresh() end
    if ok and self.attachPending and not self.attaching then self.attachPending = false; self:QueueAttach() end
    return ok
end
function C:QueueRefresh()
    if not enabled() or not self.root or not shown(self.root) or self.queued then return end
    local timer = R.Field(C_Timer, "After")
    if type(timer) ~= "function" then
        if not self.busy then self:Fail("Deferred refresh scheduling unavailable") end
        self.pending = true
        return
    end
    self.queued = true
    self.refreshTicket = self.refreshTicket + 1
    local ticket, lifecycle = self.refreshTicket, self.lifecycle
    local function run()
        if ticket ~= self.refreshTicket or lifecycle ~= self.lifecycle then return end
        self.queued = false
        if enabled() then self:Refresh("pending") end
    end
    timer(.25, run)
end
function C:Schedule(reason)
    self:Dirty(reason)
    if self.queued then perfCount("controller.refresh.coalesced") end
    self:QueueRefresh()
end
function C:CurrencyChanged(payload)
    local r = R.Call(ns.LegacyAdapter.TotalPoints)
    local value = r and R.Number(r[1])
    local currencyChanged = false
    if payload then
        self.currencyState = self.currencyState or {}
        for _, key in ipairs({ "quantity", "spentInTree", "maxQuantity", "traitCurrencyID" }) do
            local observed = R.Number(R.Field(payload, key))
            if observed ~= nil and self.currencyState[key] ~= observed then
                self.currencyState[key], currencyChanged = observed, true
            end
        end
    end
    if currencyChanged and self.ui then
        self.ui.statisticsCatalog = nil
        if self.ui.tab == "statistics" then self:Schedule("statistics") end
    end
    -- Mounting native Rewards/Trees can emit currency notifications without
    -- changing the authoritative Legacy point total. Native pages process
    -- their own tree currency payload; our header never writes that object.
    if self.currencyObserved and value == self.currencyValue then return end
    self.currencyValue, self.currencyObserved = value, true
    self:Schedule("native")
end
function C:QueueAttach()
    if self.attachQueued then return end
    local timer = R.Field(C_Timer, "After")
    if type(timer) ~= "function" then
        -- Never retry inline while Attach/Refresh is in progress. The outer
        -- pass consumes this pending request after releasing its guard.
        if self.attaching or self.busy then self.attachPending = true; return end
        if enabled() then self:Attach() end
        return
    end
    self.attachQueued = true
    local lifecycle = self.lifecycle
    local function run()
        if lifecycle ~= self.lifecycle then return end
        self.attachQueued = false
        if enabled() then self:Attach() end
    end
    timer(0, run)
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
    if self.mounting or not enabled() or not self.bridge or not shown(self.root) then return end
    -- CallbackRegistry stores callbacks by owner, not registration order.
    -- Read the final currentPage after every native callback has completed.
    if self.selectionQueued then return end
    local timer = R.Field(C_Timer, "After")
    if type(timer) ~= "function" then
        self:Release("Fallback: Native page coordination unavailable"); return
    end
    self.selectionQueued = true
    local lifecycle = self.lifecycle
    timer(0, function()
        if lifecycle ~= self.lifecycle then return end
        self.selectionQueued = false
        if not enabled() or not self.bridge or not shown(self.root) then return end
        local id = R.Number(R.Field(self.root, "currentPage"))
        local view = id == 1 and "rewards" or id == 3 and "trees" or "achievements"
        if self.ui.tab == view then self:Refresh("mount"); return end
        self:Guard(function() self.ui:SetTab(view, true) end)
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
    if self.attaching or self.busy then self.attachPending = true; self:QueueAttach(); return end
    if self.restorePending and not self:Release(enabled() and "Waiting for native Legacy frame" or "Disabled") then return end
    if not enabled() then self:Release("Disabled"); return end
    if combat() then self.pending = true; self.state = "Waiting for combat to end"; return end
    if not self:Guard(function() self:InputHooks() end) then return end
    if gamepad() then self:Release("Native interface in gamepad mode"); return end
    local root, page = LegacySystemFrame, R.Field(LegacySystemFrame, "ChallengesPage")
    if not page then self.state = "Waiting for native Legacy frame"; return end
    if B.Blocked(root) or B.Blocked(page) then self:Fail("Native Legacy frame is protected or incompatible"); return end
    if self.root and self.root ~= root and self.bridge and not self:Release("Waiting for native Legacy frame") then return end
    if self.root ~= root or self.page ~= page then self:Dirty("open"); self.dirtyLayout = true end
    self.attaching = true
    local token = perfBegin("controller.attach")
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
                function() self:Refresh("custom") end, {
                    onTab = function() self:Refresh("tab"); return true end,
                    onClose = function() self:Close() end,
                    onDragStart = function() self.dragging = true end,
                    onPositionSave = function() self:SavePosition() end,
                    onSizePresetCycle = function() self:CycleSizePreset() end,
                })
        end
        if not self.hooked[root] then
            root:HookScript("OnShow", function()
                if enabled() and root == LegacySystemFrame then
                    self:CancelQueuedWork()
                    self:Dirty("open")
                    -- Let ShowChallenges/native callbacks finish selecting
                    -- their final page before building or rendering a model.
                    self:QueueAttach()
                end
            end)
            root:HookScript("OnHide", function()
                if root == self.root then self:Release(enabled() and "Enabled; native window closed" or "Disabled") end
            end)
            root:HookScript("OnSizeChanged", function() if root == self.root then self:Schedule("layout") end end)
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
            EventRegistry:RegisterCallback("Legacy.UpdateCurrencyInfo", function(_, payload)
                if enabled() then self:CurrencyChanged(payload) end
            end, self)
            self.currencyHooked = true
        end
        if not self.challengeHooked then
            EventRegistry:RegisterCallback("Legacy.RefreshChallenges", function()
                if enabled() then self:Schedule("native") end
            end, self)
            self.challengeHooked = true
        end
        if not self.hooked[UIParent] then
            UIParent:HookScript("OnSizeChanged", function() self:Schedule("layout") end)
            self.hooked[UIParent] = true
        end
        if not self.bridge then
            local id = R.Number(R.Field(root, "currentPage"))
            self.ui.tab = id == 1 and "rewards" or id == 3 and "trees" or "achievements"
        end
        if not shown(root) then self.state = "Enabled; native window closed" end
        self:Refresh("pending")
    end)
    self.attaching = false
    perfFinish(token)
    if self.attachPending then self.attachPending = false; self:QueueAttach() end
end
function C:SetEnabled(value)
    local previous = enabled()
    FA.Settings().legacyUI = value == true
    if value then
        if not previous then self:Dirty("open") end
        self:Attach()
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
    "RECEIVED_ACHIEVEMENT_LIST", "MAJOR_FACTION_RENOWN_LEVEL_CHANGED", "UI_SCALE_CHANGED", "DISPLAY_SIZE_CHANGED" }) do
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
    elseif event == "UI_SCALE_CHANGED" or event == "DISPLAY_SIZE_CHANGED" then C:Schedule("layout")
    else C:Schedule("native") end
end)
FA.EARN_HOOKS[#FA.EARN_HOOKS + 1] = function() C:Schedule("custom") end
FA.CHECK_HOOKS[#FA.CHECK_HOOKS + 1] = function() C:Schedule("custom") end
-- File load does not open, load, hook or mutate the native Legacy window.
