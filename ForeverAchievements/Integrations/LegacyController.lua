-- Opt-in cover inside the existing Challenges page. Native frames, data
-- providers, functions, anchors, alpha, mouse settings and scripts are preserved.
local _, ns = ...
local FA, R = ns.FA, ns.LegacyReadOnly
local C = { hooked = setmetatable({}, { __mode = "k" }), state = "Disabled" }
ns.LegacyUIController = C
local function enabled() return FA.Settings().legacyUI == true end
local function notify(message) print(FA.TAG .. " Legacy UI: " .. message) end
local function combat()
    local result = R.Call(InCombatLockdown)
    return result and result[1] == true
end
local function blocked(frame)
    for _, method in ipairs({ "IsForbidden", "IsProtected" }) do
        local result = R.Method(frame, method)
        if result and result[1] == true then return true end
    end
    return false
end
local function visible(page)
    local result = R.Method(page, "IsVisible") or R.Method(page, "IsShown")
    local current = R.Number(R.Field(LegacySystemFrame, "currentPage"))
    return result and result[1] == true and (current == nil or current == 2)
end
function C:Fail(reason)
    if self.cover then self.cover:Hide() end
    if self.ui then self.ui.rendering = false end
    self.state = "Fallback: " .. tostring(reason)
    if self.lastError ~= self.state then notify(self.state .. ". Native Challenges remain available."); self.lastError = self.state end
end
function C:Guard(fn)
    local ok, err = pcall(fn)
    if not ok then self:Fail(err) end
    return ok
end
function C:Refresh()
    if not enabled() or not self.page or not visible(self.page) then
        if self.cover then self.cover:Hide() end
        return
    end
    if combat() then
        self.pending = true
        self.state = "Waiting for combat to end"
        if self.cover then self.cover:Hide() end
        return
    end
    self:Guard(function()
        assert(not blocked(self.page), "Challenges page is protected or forbidden")
        self.ui:Fit(self.page)
        local model = ns.LegacyPresentation.Build(self.page, self.nativeCatalog)
        -- Existing custom tracking hooks can fire frequently. Reuse native
        -- metadata until a native event or reopening invalidates it. Partial
        -- catalogs are retried as the native backend becomes available.
        self.nativeCatalog = not model.native.partial and model.native or nil
        self.ui:SetModel(model)
        self.cover:Show() -- only reveal a successfully populated interface
        self.state, self.lastError, self.pending = "Enabled", nil, false
    end)
end
function C:Schedule()
    if not enabled() or not self.page or not visible(self.page) or self.queued then return end
    self.queued = true
    local timer = R.Field(C_Timer, "After")
    if type(timer) == "function" then
        timer(.25, function()
            self.queued = false
            if enabled() then self:Refresh() end
        end)
    else self.queued = false; self:Refresh() end
end
local function maxLevel(page)
    local maximum, visited, budget = 0, {}, 256
    local strata, rank = nil, 0
    local ranks = { BACKGROUND = 1, LOW = 2, MEDIUM = 3, HIGH = 4, DIALOG = 5,
        FULLSCREEN = 6, FULLSCREEN_DIALOG = 7, TOOLTIP = 8 }
    local function scan(frame, depth)
        if frame == C.cover or visited[frame] or depth > 8 or budget <= 0 then return end
        visited[frame] = true; budget = budget - 1
        local level = R.Method(frame, "GetFrameLevel")
        maximum = math.max(maximum, level and R.Number(level[1]) or 0)
        local value = R.Method(frame, "GetFrameStrata")
        value = value and R.Text(value[1])
        if value and ranks[value] and ranks[value] > rank then strata, rank = value, ranks[value] end
        local children = R.Method(frame, "GetChildren")
        if children then for i = 1, children.n do if children[i] then scan(children[i], depth + 1) end end end
    end
    scan(page, 0)
    return maximum, strata
end
function C:Attach()
    if not enabled() then
        if self.cover then self.cover:Hide() end
        self.state = "Disabled"; return
    end
    if combat() then self.pending = true; self.state = "Waiting for combat to end"; return end
    local root = LegacySystemFrame
    local page = R.Field(root, "ChallengesPage")
    if not page then self.state = "Waiting for native Legacy Challenges frame"; return end
    local parent = R.Method(page, "GetParent")
    if not parent or parent[1] ~= root or blocked(root) or blocked(page) then self:Fail("Native Legacy frame is protected or incompatible"); return end
    self:Guard(function()
        local maximum, strata = maxLevel(page)
        local level = maximum + 10
        if not self.cover then
            self.cover = CreateFrame("Frame", "FAWrathLegacyCover", page)
            self.cover:Hide()
            self.cover:EnableMouse(true)
            self.cover:EnableMouseWheel(true)
            self.cover:SetScript("OnMouseWheel", function() end) -- consumes empty margins
            self.cover:SetAllPoints(page)
            self.cover:SetFrameLevel(level)
            if self.cover.SetClipsChildren then self.cover:SetClipsChildren(true) end
            local background = self.cover:CreateTexture(nil, "BACKGROUND")
            background:SetAllPoints(); background:SetColorTexture(.08, .05, .02, 1)
        else
            self.cover:Hide()
            self.cover:SetParent(page); self.cover:ClearAllPoints(); self.cover:SetAllPoints(page)
            self.cover:SetFrameLevel(level)
        end
        if strata then self.cover:SetFrameStrata(strata) end
        assert(self.cover:GetFrameLevel() > maximum, "Unable to cover native Challenges controls")
        self.page = page
        self.nativeCatalog = nil
        if not self.ui then
            self.ui = ns.WrathAchievementUI.Create(self.cover,
                function(fn) return self:Guard(fn) end, function() self:Refresh() end)
        end
        if not self.hooked[page] then
            -- HookScript appends to existing scripts. It never replaces them.
            -- These inert callbacks cannot be removed; off gates every callback.
            page:HookScript("OnShow", function()
                if enabled() and self.page == page then self.nativeCatalog = nil; self:Refresh() end
            end)
            page:HookScript("OnHide", function() if self.page == page and self.cover then self.cover:Hide() end end)
            page:HookScript("OnSizeChanged", function() if enabled() and self.page == page then self:Schedule() end end)
            self.hooked[page] = true
        end
        if not self.hooked[root] then
            root:HookScript("OnShow", function() if enabled() then self:Attach() end end)
            self.hooked[root] = true
        end
        self.state = "Enabled; waiting for Challenges page"
        self:Refresh()
    end)
end
function C:SetEnabled(value)
    FA.Settings().legacyUI = value == true
    if value then self:Attach() else
        self.pending, self.queued = false, false
        if self.cover then self.cover:Hide() end
        self.state = "Disabled"
    end
    notify(self.state)
end
FA.SLASH.legacyui = function(input)
    input = (input or ""):lower():match("^%s*(.-)%s*$")
    if input == "on" then C:SetEnabled(true)
    elseif input == "off" then C:SetEnabled(false)
    else notify(C.state .. ". Use /fa legacyui on or /fa legacyui off (experimental).") end
end
local events = CreateFrame("Frame")
for _, event in ipairs({ "PLAYER_LOGIN", "ADDON_LOADED", "PLAYER_REGEN_ENABLED", "PLAYER_REGEN_DISABLED",
    "ACHIEVEMENT_EARNED", "CRITERIA_UPDATE", "CRITERIA_COMPLETE", "RECEIVED_ACHIEVEMENT_LIST", "MAJOR_FACTION_RENOWN_LEVEL_CHANGED" }) do
    pcall(events.RegisterEvent, events, event) -- unsupported client events are optional
end
events:SetScript("OnEvent", function(_, event)
    if not enabled() then return end
    if event == "PLAYER_REGEN_DISABLED" then
        if C.cover then C.cover:Hide() end
        C.pending = true; C.state = "Waiting for combat to end"
    elseif event == "PLAYER_LOGIN" or event == "ADDON_LOADED" or event == "PLAYER_REGEN_ENABLED" then C:Attach()
    else C.nativeCatalog = nil; C:Schedule() end
end)
FA.EARN_HOOKS[#FA.EARN_HOOKS + 1] = function() C:Schedule() end
FA.CHECK_HOOKS[#FA.CHECK_HOOKS + 1] = function() C:Schedule() end
-- Do not create, show, inspect, or hook a native window during addon file load.
