-------------------------------------------------------------------------------
--  Minimap button (LibDBIcon): left click opens the window, right click the
--  Summary page.
-------------------------------------------------------------------------------
local _, ns = ...
local LAR = ns.LAR

-- Retain the old launcher for research, without registering a minimap/broker
-- object or changing the user's saved minimap preference while quarantined.
if not (ns.OriginalUI and ns.OriginalUI.IsEnabled()) then return end

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
        if button == "RightButton" then LAR.ShowTab("summary") else LAR.Open() end
    end,
    OnTooltipShow = function(tt)
        local pts, all, n, avail = LAR.TotalPoints()
        tt:AddLine("Legacy Achievements Reforged")
        tt:AddDoubleLine("Earned", n .. " / " .. avail, 1, 1, 1, 1, 1, 1)
        tt:AddDoubleLine("Points", pts .. " / " .. all, 1, 1, 1, 1, 1, 1)
        tt:AddLine(" ")
        tt:AddLine("Left click: window   Right click: summary", 0.6, 0.6, 0.6)
    end,
})

function LAR.SetMinimapShown(on)
    IconDB().hide = not on
    if on then DBIcon:Show("LegacyAchievementsReforged") else DBIcon:Hide("LegacyAchievementsReforged") end
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
    local db = IconDB()
    if LAR.Settings().minimapShown == false then db.hide = true end
    DBIcon:Register("LegacyAchievementsReforged", broker, db)
end)
