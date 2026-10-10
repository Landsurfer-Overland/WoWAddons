-------------------------------------------------------------------------------
--  Minimap button (LibDBIcon): left click opens the window, right click the
--  Summary page.
-------------------------------------------------------------------------------
local _, ns = ...
local FA = ns.FA

local LDB = LibStub and LibStub("LibDataBroker-1.1", true)
local DBIcon = LibStub and LibStub("LibDBIcon-1.0", true)
if not (LDB and DBIcon) then return end

local function IconDB()
    local S = FA.Settings()
    S.minimap = S.minimap or {}
    return S.minimap
end

local broker = LDB:NewDataObject("ForeverAchievements", {
    type = "launcher",
    label = "Forever Achievements",
    icon = "Interface\\AddOns\\ForeverAchievements\\Media\\icon",
    OnClick = function(_, button)
        if button == "RightButton" then FA.ShowTab("summary") else FA.Open() end
    end,
    OnTooltipShow = function(tt)
        local pts, all, n, avail = FA.TotalPoints()
        tt:AddLine("Forever Achievements")
        tt:AddDoubleLine("Earned", n .. " / " .. avail, 1, 1, 1, 1, 1, 1)
        tt:AddDoubleLine("Points", pts .. " / " .. all, 1, 1, 1, 1, 1, 1)
        tt:AddLine(" ")
        tt:AddLine("Left click: window   Right click: summary", 0.6, 0.6, 0.6)
    end,
})

function FA.SetMinimapShown(on)
    IconDB().hide = not on
    if on then DBIcon:Show("ForeverAchievements") else DBIcon:Hide("ForeverAchievements") end
end

local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:SetScript("OnEvent", function()
    local db = IconDB()
    if FA.Settings().minimapShown == false then db.hide = true end
    DBIcon:Register("ForeverAchievements", broker, db)
end)
