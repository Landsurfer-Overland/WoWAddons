-------------------------------------------------------------------------------
--  Minimap launcher for the current Legacy achievement screen, including
--  characters whose native microbutton has not unlocked yet.
-------------------------------------------------------------------------------
local _, ns = ...
local LAR = ns.LAR

function LAR.ToggleAchievements()
    -- Loading addons and updating Blizzard's panel manager are not combat-safe.
    if InCombatLockdown and InCombatLockdown() then
        print(LAR.TAG .. " Open achievements after combat ends.")
        return false
    end
    if not LegacySystemFrame then
        local load = C_AddOns and C_AddOns.LoadAddOn or LoadAddOn
        local ok, loaded, reason
        if type(load) == "function" then
            ok, loaded, reason = pcall(load, "Blizzard_LegacySystem")
        end
        if not ok or not loaded then
            print(LAR.TAG .. " Achievements are unavailable: " .. tostring(reason or "native addon could not load"))
            return false
        end
    end
    local root = LegacySystemFrame
    if not root or type(root.ShowChallenges) ~= "function"
        or (root.IsForbidden and root:IsForbidden())
        or (root.IsProtected and root:IsProtected()) then
        print(LAR.TAG .. " The native achievement screen is unavailable in this client.")
        return false
    end
    if root:IsShown() then
        if ns.LegacyUIController and ns.LegacyUIController.root == root then
            ns.LegacyUIController:Close()
        else
            HideUIPanel(root)
        end
    else
        -- Attach before ShowChallenges so the first opening uses the normal
        -- Reforged handoff. Respect the player's existing legacyUI setting.
        if LAR.Settings().legacyUI and ns.LegacyUIController then
            ns.LegacyUIController:Attach()
        end
        -- Unlike ToggleLegacySystemUI, this presentation method has no Legacy
        -- point unlock check. It does not grant points, rewards or tree access.
        root:ShowChallenges()
    end
    return true
end

LAR.SLASH.minimap = function(input)
    if not LAR.SetMinimapShown then
        print(LAR.TAG .. " Minimap button libraries are unavailable.")
        return
    end
    input = (input or ""):lower():match("^%s*(.-)%s*$")
    if input == "show" or input == "on" then LAR.SetMinimapShown(true)
    elseif input == "hide" or input == "off" then LAR.SetMinimapShown(false)
    else print(LAR.TAG .. " Use /lar minimap show|hide.") end
end

local LDB = LibStub and LibStub("LibDataBroker-1.1", true)
local DBIcon = LibStub and LibStub("LibDBIcon-1.0", true)
if not (LDB and DBIcon) then return end

local function IconDB()
    local S = LAR.Settings()
    S.minimap = S.minimap or {}
    return S.minimap
end

local broker = LDB:NewDataObject("LegacyAchievementsReforged", {
    type = "launcher",
    label = "Legacy Achievements Reforged",
    icon = "Interface\\AddOns\\LegacyAchievementsReforged\\Media\\icon",
    OnClick = function(_, button)
        if button == "RightButton" then
            if ns.AddonSettings then ns.AddonSettings.Open() end
        elseif button == "LeftButton" then LAR.ToggleAchievements() end
    end,
    OnTooltipShow = function(tt)
        local pts, all, n, avail = LAR.TotalPoints()
        tt:AddLine("Legacy Achievements Reforged")
        tt:AddDoubleLine("Earned", n .. " / " .. avail, 1, 1, 1, 1, 1, 1)
        tt:AddDoubleLine("Points", pts .. " / " .. all, 1, 1, 1, 1, 1, 1)
        tt:AddLine(" ")
        tt:AddLine("Left click: achievements", 0.6, 0.6, 0.6)
        tt:AddLine("Right click: settings", 0.6, 0.6, 0.6)
        tt:AddLine("Drag to move around the minimap", 0.6, 0.6, 0.6)
    end,
})

function LAR.SetMinimapShown(on)
    LAR.Settings().minimapShown = on == true
    IconDB().hide = not on
    if on then DBIcon:Show("LegacyAchievementsReforged") else DBIcon:Hide("LegacyAchievementsReforged") end
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
    local db = IconDB()
    local preference = LAR.Settings().minimapShown
    if preference ~= nil then db.hide = preference == false end
    DBIcon:Register("LegacyAchievementsReforged", broker, db)
end)

