-- Runs against the actual launcher with minimal native UI / library doubles.
local source = ...
local checks = 0
local function scenario(name, run)
    local settings, log, frames = {}, {}, {}
    local ns = { LAR = { TAG = "LAR", SLASH = {} } }
    ns.LAR.Settings = function() return settings end
    ns.LAR.Open = function() error("Archived alpha window opened") end
    ns.LAR.ShowTab = ns.LAR.Open
    ns.LAR.TotalPoints = function() return 10, 30, 1, 3 end
    ns.OriginalUI = { IsEnabled = function() return false end }
    local broker, db
    local ldb = { NewDataObject = function(_, id, value)
        assert(id == "LegacyAchievementsReforged"); broker = value; return value
    end }
    local icon = {
        Register = function(_, id, object, value)
            assert(id == "LegacyAchievementsReforged" and object == broker)
            db = value; log.register = (log.register or 0) + 1
        end,
        Show = function() log.shown = true end,
        Hide = function() log.shown = false end,
    }
    LibStub = function(id) if id == "LibDataBroker-1.1" then return ldb else return icon end end
    CreateFrame = function()
        local frame = {}
        function frame:RegisterEvent(event) self.event = event end
        function frame:SetScript(_, callback) self.callback = callback end
        frames[#frames + 1] = frame
        return frame
    end
    LegacySystemFrame, C_AddOns, LoadAddOn = nil, nil, nil
    InCombatLockdown = function() return log.combat end
    ToggleLegacySystemUI = function() error("Level/point-gated toggle used") end
    UnitLevel = function() return 1 end
    print = function(message) log.message = message end
    local function native()
        local root = { shown = false }
        function root:IsShown() return self.shown end
        function root:IsForbidden() return log.forbidden end
        function root:IsProtected() return log.protected end
        function root:ShowChallenges()
            log.opens = (log.opens or 0) + 1
            self.shown, self.currentPage = true, 2
        end
        LegacySystemFrame = root
        return root
    end
    ns.LegacyUIController = {
        cover = { IsShown = function() return log.attached and LegacySystemFrame.shown end },
        Attach = function(self) self.root = LegacySystemFrame; log.attached = true end,
        SetEnabled = function(self, value) settings.legacyUI = value; self:Attach() end,
        Close = function() LegacySystemFrame.shown = false; log.closed = true end,
    }
    HideUIPanel = function(root) assert(not log.combat); root.shown = false; log.closed = true end
    ns.AddonSettings = { Open = function() log.settings = true end }
    assert(loadfile(source))("LegacyAchievementsReforged", ns)
    local context = { ns = ns, settings = settings, log = log, native = native,
        click = function(button) broker.OnClick(nil, button) end,
        login = function() frames[1].callback(nil, "PLAYER_LOGIN"); return db end }
    local ok, err = pcall(run, context)
    assert(ok, name .. ": " .. tostring(err))
    checks = checks + 1
end

scenario("level-one lazy load, open and close", function(c)
    assert(not c.login().hide and c.log.register == 1)
    C_AddOns = { LoadAddOn = function(name)
        assert(name == "Blizzard_LegacySystem"); c.native(); return true
    end }
    c.click("LeftButton")
    assert(c.log.opens == 1 and LegacySystemFrame.currentPage == 2)
    c.click("LeftButton")
    assert(c.log.closed and not LegacySystemFrame.shown)
end)
scenario("legacy loader fallback", function(c)
    LoadAddOn = function() c.native(); return true end
    assert(c.ns.LAR.ToggleAchievements() and c.log.opens == 1)
end)
scenario("attach before opening and close through controller", function(c)
    local root = c.native()
    c.settings.legacyUI = true
    c.ns.LegacyUIController = { root = root,
        cover = { IsShown = function() return root.shown end },
        Attach = function() assert(not root.shown); c.log.attached = true end,
        Close = function() c.log.controllerClose = true; root.shown = false end }
    c.click("LeftButton"); assert(c.log.attached and root.shown)
    c.click("LeftButton"); assert(c.log.controllerClose and not root.shown)
end)
scenario("disabled replacement opens combined pane", function(c)
    c.native(); c.settings.legacyUI = false
    c.click("LeftButton")
    assert(c.log.opens == 1 and c.settings.legacyUI == true and c.log.attached)
end)
scenario("visible native pane switches to combined instead of closing", function(c)
    local root = c.native(); root.shown = true
    c.click("LeftButton")
    assert(root.shown and c.log.opens == 1 and c.settings.legacyUI and c.log.attached)
end)
scenario("missing combined controller reports failure", function(c)
    c.native(); c.ns.LegacyUIController = nil
    assert(c.ns.LAR.ToggleAchievements() == false and not c.log.opens)
end)
scenario("combat blocks loading and panel writes", function(c)
    c.log.combat = true
    C_AddOns = { LoadAddOn = function() error("Combat addon load") end }
    assert(c.ns.LAR.ToggleAchievements() == false and c.log.message:find("combat"))
    c.native(); c.click("LeftButton"); assert(not c.log.opens)
end)
scenario("load failure and exception are reported", function(c)
    C_AddOns = { LoadAddOn = function() return nil, "DISABLED" end }
    assert(c.ns.LAR.ToggleAchievements() == false and c.log.message:find("DISABLED"))
    C_AddOns.LoadAddOn = function() error("loader failure") end
    assert(c.ns.LAR.ToggleAchievements() == false)
end)
scenario("missing and restricted native screens", function(c)
    assert(c.ns.LAR.ToggleAchievements() == false)
    C_AddOns = { LoadAddOn = function() return true end }
    assert(c.ns.LAR.ToggleAchievements() == false)
    c.native(); c.log.protected = true
    assert(c.ns.LAR.ToggleAchievements() == false and not c.log.opens)
    c.log.protected, c.log.forbidden = false, true
    assert(c.ns.LAR.ToggleAchievements() == false and not c.log.opens)
end)
scenario("settings and unknown mouse buttons", function(c)
    c.click("RightButton"); assert(c.log.settings and not c.log.opens)
    c.click("MiddleButton"); assert(not c.log.opens)
end)
scenario("saved position and hidden preference", function(c)
    c.settings.minimap = { hide = true, minimapPos = 123 }
    local db = c.login()
    assert(db.hide and db.minimapPos == 123)
    c.ns.LAR.SLASH.minimap("show")
    assert(c.settings.minimapShown and not db.hide and c.log.shown and db.minimapPos == 123)
    c.ns.LAR.SLASH.minimap("hide")
    assert(not c.settings.minimapShown and db.hide and not c.log.shown)
end)
scenario("explicit visibility reconciles saved library state", function(c)
    c.settings.minimap = { hide = true, minimapPos = 50 }
    c.settings.minimapShown = true
    assert(not c.login().hide and c.settings.minimap.minimapPos == 50)
end)
scenario("explicit hidden preference", function(c)
    c.settings.minimapShown = false
    assert(c.login().hide)
end)
return checks
