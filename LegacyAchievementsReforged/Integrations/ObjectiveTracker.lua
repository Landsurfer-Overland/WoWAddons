-- A real client objective-tracker module for custom, per-character watches.
-- No fake native achievement IDs, quest watch edits, or Blizzard API overrides.
local _, ns = ...
local LAR = ns.LAR
local T = { entries = {}, byKey = {}, state = "Waiting for client objective tracker", dirty = true }
ns.ObjectiveTrackerIntegration = T

local function combat() return InCombatLockdown and InCombatLockdown() end
local function blocked(frame)
    return not frame or frame.IsForbidden and frame:IsForbidden()
        or frame.IsProtected and frame:IsProtected()
end
local function notify(text) print(LAR.TAG .. " Objective tracker: " .. text) end

function T:BuildEntries(list)
    local entries = {}
    if LAR.Settings().trackerShown == false then return entries end
    for i = 1, math.min(10, #list) do
        local a = list[i]
        local cur, need = a.progress()
        local text
        if not LAR.ProgressKnown(cur, need) then text = "Unavailable"
        elseif a.money then text = math.floor(cur / 10000) .. "/" .. math.floor(need / 10000) .. "g"
        else text = cur .. "/" .. need end
        entries[#entries + 1] = { key = a.key, name = a.name, text = text, achievement = a }
    end
    return entries
end

local function same(a, b)
    if #a ~= #b then return false end
    for i, row in ipairs(a) do
        local other = b[i]
        if row.key ~= other.key or row.name ~= other.name or row.text ~= other.text then return false end
    end
    return true
end

function T:Layout(module)
    if combat() or blocked(module) then self.dirty = true; return end
    -- Native refreshes consume a small immutable display snapshot. Progress is
    -- read by UpdateTracker, never by Blizzard's layout/collapse callbacks.
    for _, row in ipairs(self.entries) do
        local block = module:GetBlock(row.key)
        block:SetHeader(row.name)
        block:AddObjective("progress", row.text, nil, nil, OBJECTIVE_DASH_STYLE_SHOW)
        if not module:LayoutBlock(block) then return end
    end
end

function T:Focus(key)
    local a = LAR.BY_KEY[key]
    if not a then return end
    if combat() then self.openPending = key; return end
    local controller = ns.LegacyUIController
    local function focus()
        if combat() then self.openPending = key; return end
        local ui = controller and controller.ui
        if ui and controller:PresentationAllowed() then
            controller:Guard(function()
                ui:SetTab("achievements", true)
                ui.searchBox:SetText(a.name)
                ui.contentScroll:SetVerticalScroll(0)
            end)
        elseif ns.OriginalUI and ns.OriginalUI.IsEnabled() then LAR.OpenSearch(a.name)
        else notify("Open the Legacy panel to view " .. a.name .. ".") end
    end
    -- Use the client's normal entry point if it is already available. Do not
    -- load a guessed addon, call a protected frame, or toggle native progression.
    if LAR.Settings().legacyUI == true and not blocked(LegacySystemFrame)
        and type(LegacySystemFrame.ShowChallenges) == "function" then
        LegacySystemFrame:ShowChallenges()
        C_Timer.After(0, focus)
    else focus() end
end

function T:Register()
    if self.module then return true end
    if combat() then self.state = "Deferred until combat ends"; return false end
    local container, manager, base = ObjectiveTrackerFrame, ObjectiveTrackerManager, ObjectiveTrackerModuleMixin
    if blocked(container) then self.state = "Client tracker unavailable or protected"; return false end
    if type(container.AddModule) ~= "function" or type(base) ~= "table"
        or type(base.Update) ~= "function" or type(base.GetBlock) ~= "function"
        or type(base.LayoutBlock) ~= "function" or type(base.MarkDirty) ~= "function" then
        self.state = "Waiting for client objective-tracker module initialization"; return false
    end
    local managed = type(manager) == "table" and type(manager.SetModuleContainer) == "function"
    if managed and (type(manager.containers) ~= "table" or not manager.containers[container]) then
        self.state = "Waiting for client objective-tracker manager initialization"; return false
    end
    local module = self.createdModule
    if not module then
        module = CreateFrame("Frame", "LARObjectiveTrackerModule", UIParent, "ObjectiveTrackerModuleTemplate")
        self.createdModule = module
        if blocked(module) then self.state = "Owned tracker module is restricted"; return false end
        module:SetHeader("Reforged Achievements")
        module.uiOrder = (AchievementObjectiveTracker and AchievementObjectiveTracker.uiOrder or 1000) + .1
        module.LayoutContents = function(owner) self:Layout(owner) end
        module.OnBlockHeaderClick = function(_, block, button)
            local row = self.byKey[block.id]
            if not row then return end
            if button == "RightButton" then LAR.ToggleTrack(row.achievement)
            else self:Focus(row.key) end
        end
        -- Do not create, release, reposition or show/hide native blocks during
        -- lockdown, even when Blizzard initiates a refresh or collapse itself.
        module.Update = function(owner, ...)
            if combat() or blocked(owner) then
                self.dirty = true
                return owner:GetContentsHeight(), owner:IsTruncated()
            end
            return base.Update(owner, ...)
        end
    elseif blocked(module) then self.state = "Owned tracker module is restricted"; return false end
    -- Older module clients have a global routing manager; frame-managed builds
    -- expose AddModule directly (confirmed on Forever), without that global.
    if managed then manager:SetModuleContainer(module, container)
    else container:AddModule(module) end
    if module:GetParent() ~= container then self.state = "Waiting for tracker registration"; return false end
    self.module, self.state, self.dirty = module, "Registered in client objectives", true
    return true
end

function T:Update(list)
    local entries = self:BuildEntries(list)
    if not same(entries, self.entries) then
        self.entries, self.byKey, self.dirty = entries, {}, true
        for _, row in ipairs(entries) do self.byKey[row.key] = row end
    end
    if #entries == 0 and not self.module then return end
    if not self:Register() then
        if #entries > 0 and not combat() and not self.warned then
            self.warned = true
            notify(self.state .. ". Watches are retained; /lar tracker status reports availability.")
        end
        return
    end
    if self.dirty and not combat() and not blocked(self.module) and not blocked(self.module:GetParent()) then
        self.dirty = false
        self.module:MarkDirty() -- native scheduler coalesces layout; no quest data rebuild
    end
end

function T:NeedsPolling()
    return self.module ~= nil and #self.entries > 0 and not combat()
end

function T:QueueRefresh()
    if combat() then self.dirty = true; return end
    if self.queued then return end
    self.queued = true
    C_Timer.After(0, function()
        self.queued = false
        if combat() then self.dirty = true; return end
        if LAR.UpdateTracker then LAR.UpdateTracker() end
        if self.openPending then local key = self.openPending; self.openPending = nil; self:Focus(key) end
    end)
end

LAR.SLASH.tracker = function(input)
    input = (input or ""):lower():match("^%s*(.-)%s*$")
    if input == "on" or input == "off" then
        LAR.Settings().trackerShown = input == "on"
        if LAR.UpdateTracker then LAR.UpdateTracker() end
    end
    notify(T.state .. "; " .. #T.entries .. " displayed watches; combat=" .. tostring(combat() == true)
        .. ". Use /lar tracker on|off|status.")
end
local events = CreateFrame("Frame")
T.events = events
for _, event in ipairs({ "PLAYER_LOGIN", "PLAYER_ENTERING_WORLD", "ADDON_LOADED", "PLAYER_REGEN_ENABLED" }) do events:RegisterEvent(event) end
events:SetScript("OnEvent", function(_, event)
    if event ~= "ADDON_LOADED" or not T.module then T:QueueRefresh() end
end)
