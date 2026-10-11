-------------------------------------------------------------------------------
--  Tooltip hints: what a creature, item or book still means for an
--  achievement, and what another player with the addon has earned.
-------------------------------------------------------------------------------
local _, ns = ...
local LAR = ns.LAR
local secret = LAR.secret

local GetItemInfoInstant = (C_Item and C_Item.GetItemInfoInstant) or GetItemInfoInstant
local GetItemName = (C_Item and C_Item.GetItemNameByID) or function(id) return (GetItemInfo(id)) end

local CRITTER_SET = {}
for _, n in ipairs(LAR.CRITTERS) do CRITTER_SET[n] = true end
local RARE_FISH = {}
for _, f in ipairs(ns.RARE_FISH) do RARE_FISH[f[2]] = true end

local function On() return LAR.Settings().tooltips ~= false end

local function Hint(tt, text)
    local r, g, b = LAR.Kit.Accent()
    tt:AddLine("|T132347:14:14|t " .. text, r, g, b, true)
end

local function Done(key) return LAR.DB().done[key] end

local function UnitHints(tt)
    if not On() or not tt.GetUnit then return end
    local name, unit = tt:GetUnit()
    if not unit or secret(unit) or not name or secret(name) then return end
    local isPlayer = UnitIsPlayer(unit)
    if secret(isPlayer) then return end
    if isPlayer then
        local peer = (name == UnitName("player")) and {
            pts = select(1, LAR.TotalPoints()), count = select(3, LAR.TotalPoints()), title = LAR.CurrentTitle(),
        } or LAR.Peer((LAR.FullName and LAR.FullName(unit)) or name)
        if peer then
            if peer.title then Hint(tt, peer.title:format(name)) end
            Hint(tt, ("%d achievements, %d points"):format(peer.count or 0, peer.pts or 0))
            tt:Show()
        end
        return
    end
    local guid = UnitGUID(unit)
    local id = guid and not secret(guid) and LAR.NpcID(guid) or nil
    local d = LAR.DB()
    local added = false
    if CRITTER_SET[name] and not d.critters[name] and not Done("critters") then
        Hint(tt, "Needs your /love (To All The Squirrels I've Loved Before)")
        added = true
    end
    local pest = (id and LAR.PESTS[id]) or (LAR.PEST_NAMES[name] and name)
    if pest and not d.pests[pest] and not Done("pests") then
        Hint(tt, "Slay it for Pest Control")
        added = true
    end
    -- Your own faction's leaders are bosses only for the other side.
    local friend = UnitIsFriend("player", unit)
    if secret(friend) then friend = false end
    if not friend and ((id and LAR.BOSS_IDS[id]) or LAR.BOSS_BY_NAME[name]) then
        local bossName = (id and LAR.BOSS_IDS[id]) or name
        if not d.bosses[id or 0] and not d.bosses[bossName] then
            Hint(tt, "Not yet defeated: " .. (LAR.BOSS_ACH[bossName] or "achievement"))
            added = true
        end
    end
    local class = UnitClassification(unit)
    if not secret(class) and (class == "rare" or class == "rareelite") and not d.rares[name] then
        Hint(tt, "Rare: not yet slain (Rare Hunter)")
        added = true
    end
    if added then tt:Show() end
end

local function ItemHints(tt)
    if not On() or not tt.GetItem then return end
    local _, link = tt:GetItem()
    if not link or secret(link) then return end
    local id = tonumber(link:match("item:(%d+)"))
    if not id then return end
    local d = LAR.DB()
    local _, _, _, _, _, c, s = GetItemInfoInstant(id)
    if c == 0 and s == 5 then
        if LAR.IsDrink(id, GetItemName(id)) then
            if not d.drinks[id] and not Done("drinks") then Hint(tt, "Not yet tasted: It's Happy Hour Somewhere") tt:Show() end
        elseif not d.foods[id] and not Done("foods") then
            Hint(tt, "Not yet tasted: Tastes Like Chicken")
            tt:Show()
        end
    end
    if RARE_FISH[id] and not Done("rarefish") then
        Hint(tt, "Counts for One That Didn't Get Away")
        tt:Show()
    end
end

if TooltipDataProcessor and TooltipDataProcessor.AddTooltipPostCall and Enum and Enum.TooltipDataType then
    TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Unit, function(tt) if tt == GameTooltip then UnitHints(tt) end end)
    TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Item, ItemHints)
else
    GameTooltip:HookScript("OnTooltipSetUnit", UnitHints)
    GameTooltip:HookScript("OnTooltipSetItem", ItemHints)
end

-- Books and plaques in the world: their title is the tooltip's first line.
local bookShown
GameTooltip:HookScript("OnShow", function(tt)
    if not On() or bookShown == tt then return end
    if (tt.GetUnit and tt:GetUnit()) or (tt.GetItem and tt:GetItem()) then return end
    local line = _G.GameTooltipTextLeft1
    local text = line and line:GetText()
    if not text or secret(text) then return end
    local book = LAR.BOOKSET[text:lower()]
    if book and not LAR.DB().books[book] and not Done("books") then
        bookShown = tt
        Hint(tt, "Not yet read: Well Read")
        tt:Show()
    end
end)
GameTooltip:HookScript("OnHide", function() bookShown = nil end)
