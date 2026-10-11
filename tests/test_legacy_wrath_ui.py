#!/usr/bin/env python3
"""Lua 5.1 adapter/controller checks with an explicit XML-template UI double.

This loads the committed templates and executes their actual OnLoad callbacks.
It checks object contracts and behavior, not native rendering, taint or assets.
"""
from pathlib import Path
import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as ET

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    sys.path.insert(0, "/workspace/.cloud-tools/forever-achievements/python")
    from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "ForeverAchievements"
URI = "{http://www.blizzard.com/wow/ui/}"
BASE = r'''
ns = { ICONS = {}, STATS = {} }
calls, frames, timers, messages = {}, {}, {}, {}
settings = {}
saved = { done = { first = 1730000000 }, tracked = {}, history = { "keep" }, explored = { zone = { old = true } } }
local function poison(name)
    return function() calls[#calls + 1] = name; error("Native mutation: " .. name) end
end
SetAchievementSearchString = poison("SetAchievementSearchString")
AddTrackedAchievement = poison("AddTrackedAchievement")
RemoveTrackedAchievement = poison("RemoveTrackedAchievement")
ToggleLegacyChallenges = poison("ToggleLegacyChallenges")
C_Legacy = { ClaimReward = poison("ClaimReward") }
C_Traits = { PurchaseRank = poison("PurchaseRank"),
    GetTraitCurrencyForAchievement = function(currency, id) assert(currency == 4225); return id == 62013 and 1 or 0 end }
C_MajorFactions = { GetCurrentRenownLevel = function(id) assert(id == 2802); return 16 end,
    ClaimReward = poison("MajorFactionClaim") }
function print(v) messages[#messages + 1] = v end
function InCombatLockdown() return inCombat == true end
function date(fmt, timestamp) return "10/27/24" end
function time(tbl) return tbl and tbl.year * 31536000 + tbl.month * 2678400 + tbl.day * 86400 or 1 end
ACHIEVEMENT_FLAGS_ACCOUNT = 131072
C_Timer = { After = function(delay, fn) timers[#timers + 1] = fn end }
function FlushTimers() local q = timers; timers = {}; for _, fn in ipairs(q) do fn() end end
local a = { key = "first", id = 62013, name = "First custom", desc = "Keep this progress", pts = 10,
    list = { "Saved criterion", "Pending criterion" }, has = function(name) return name == "Saved criterion" end,
    progress = function() return 1, 2 end }
local b = { key = "second", id = 6, name = "Second custom", desc = "Numeric progress", pts = 20,
    progress = function() return 7, 10 end }
local imported = { key = "imported", name = "Old native import", native = true, pts = 10 }
ns.FA = { TAG = "FA", Settings = function() return settings end, DB = function() return saved end,
    Account = function() return { chars = { other = { done = { second = 100 } } } } end,
    Available = function() return true end, Earned = function() return true end,
    ALL = {a, b, imported}, BY_KEY = {first=a, second=b}, SERIES = {},
    CATEGORIES = {{key="general", label="General"}}, CATEGORY_ORDER = {"general"},
    CATEGORY_SECTIONS = {general = {{title="General", list={a, b, imported}}}},
    EARN_HOOKS = {}, CHECK_HOOKS = {}, SLASH = {},
    Count = function(t) local n = 0; for _ in pairs(t or {}) do n=n+1 end; return n end,
    StatText = function(id) return "17" end,
    ToggleTrack = function(row) saved.tracked[row.key] = not saved.tracked[row.key] or nil end }

-- An explicit set of ordinary WoW UI methods: missing methods fail tests.
function UIObject(kind, name, parent)
    local f = { kind=kind, name=name, parent=parent, children={}, regions={}, scripts={}, hooks={},
        shown=true, width=100, height=24, level=1, scroll=0, textValue="", scale=1, mouse=false }
    if name then _G[name] = f end
    if parent and parent.children then
        table.insert((kind == "Texture" or kind == "FontString" or kind == "Line") and parent.regions or parent.children, f)
    end
    frames[#frames+1] = f
    function f:GetName() return self.name end
    function f:GetParent() return self.parent end
    function f:GetChildren() return unpack(self.children) end
    function f:GetRegions() return unpack(self.regions) end
    function f:GetObjectType() return self.kind end
    function f:IsObjectType(kind) return self.kind==kind end
    function f:GetFrameLevel() return self.level end
    function f:GetFrameStrata() return self.strata or (self.parent and self.parent:GetFrameStrata()) or "MEDIUM" end
    function f:IsForbidden() return self.forbidden == true end
    function f:IsProtected() return self.protected == true end
    function f:IsShown() return self.shown end
    function f:IsVisible() return self.shown and (not self.parent or self.parent:IsVisible()) end
    function f:SetScript(event, fn) self.scripts[event] = fn end
    function f:GetScript(event) return self.scripts[event] end
    function f:HookScript(event, fn)
        self.hooks[event] = self.hooks[event] or {}; table.insert(self.hooks[event], fn)
    end
    function f:Fire(event, ...)
        if self.scripts[event] then self.scripts[event](self, ...) end
        for _, fn in ipairs(self.hooks[event] or {}) do fn(self, ...) end
    end
    function f:Show() local old = self.shown; self.shown = true; if not old then self:Fire("OnShow") end end
    function f:Hide() local old = self.shown; self.shown = false; if old then self:Fire("OnHide") end end
    function f:SetShown(v) if v then self:Show() else self:Hide() end end
    function f:SetSize(w,h) self.width=w; self.height=h end
    function f:SetWidth(w) self.width=w end
    function f:SetHeight(h) self.height=h end
    function f:GetWidth() return self.width end
    function f:GetHeight() return self.height end
    function f:GetCenter()
        if self.centerX ~= nil and self.centerY ~= nil then return self.centerX,self.centerY end
        if not self.parent then return self.width/2,self.height/2 end
        local anchors = self.points and self.points.kind and self.framePoints or self.points
        local anchor = anchors and anchors[1]
        local relative = anchor and anchor[2] or self.allPoints or self.parent
        if not relative or relative==self then return self.width/2,self.height/2 end
        local x,y=relative:GetCenter()
        local relativeScale,selfScale=relative:GetEffectiveScale(),self:GetEffectiveScale()
        x,y=x*relativeScale,y*relativeScale
        if anchor then
            local point,relativePoint=anchor[1],anchor[3] or anchor[1]
            if relativePoint:find("LEFT") then x=x-relative:GetWidth()*relativeScale/2 end
            if relativePoint:find("RIGHT") then x=x+relative:GetWidth()*relativeScale/2 end
            if relativePoint:find("TOP") then y=y+relative:GetHeight()*relativeScale/2 end
            if relativePoint:find("BOTTOM") then y=y-relative:GetHeight()*relativeScale/2 end
            x,y=x+(anchor[4] or 0)*selfScale,y+(anchor[5] or 0)*selfScale
            if point:find("LEFT") then x=x+self:GetWidth()*selfScale/2 end
            if point:find("RIGHT") then x=x-self:GetWidth()*selfScale/2 end
            if point:find("TOP") then y=y-self:GetHeight()*selfScale/2 end
            if point:find("BOTTOM") then y=y+self:GetHeight()*selfScale/2 end
        end
        return x/selfScale,y/selfScale
    end
    function f:GetLeft() local x=self:GetCenter(); return x-self:GetWidth()/2 end
    function f:GetRight() local x=self:GetCenter(); return x+self:GetWidth()/2 end
    function f:GetTop() local _,y=self:GetCenter(); return y+self:GetHeight()/2 end
    function f:GetBottom() local _,y=self:GetCenter(); return y-self:GetHeight()/2 end
    function f:SetText(t) self.textValue=tostring(t or ""); if type(self.text)=="table" then self.text:SetText(t) end end
    function f:GetText() return self.textValue end
    function f:GetStringHeight() return math.max(12, math.ceil(#self.textValue / math.max(1,self.width/6)) * 12) end
    function f:GetStringWidth() return #self.textValue * 6 end
    function f:SetTextColor(...) self.color={...} end
    function f:SetFontObject(object) self.fontObject=object end
    function f:GetFontObject() return self.fontObject end
    function f:SetVertexColor(...) self.color={...} end
    function f:SetTexCoord(...) self.coords={...} end
    function f:SetTexture(t) self.textureValue=t end
    function f:SetColorTexture(...) self.colorTexture={...} end
    function f:SetPoint(point,relative,relativePoint,x,y)
        if type(relative)=="number" then
            x,y,relative,relativePoint=relative,relativePoint,self.parent,point
        elseif type(relativePoint)=="number" then
            x,y,relativePoint=relativePoint,x,point
        end
        if type(relative)=="string" then relative=_G[relative] end
        relative=relative or self.parent
        -- ShieldOnLoad binds its points FontString to a public field. Native
        -- anchor storage is separate and must not overwrite that child region.
        local anchors
        if self.points and self.points.kind then
            self.framePoints=self.framePoints or {}; anchors=self.framePoints
        else self.points=self.points or {}; anchors=self.points end
        table.insert(anchors,{point,relative,relativePoint or point,x or 0,y or 0})
    end
    function f:ClearAllPoints()
        if self.points and self.points.kind then self.framePoints={} else self.points={} end
        self.allPoints=nil
    end
    function f:GetNumPoints()
        local anchors = self.points and self.points.kind and self.framePoints or self.points
        return #(anchors or {})
    end
    function f:GetPoint(index)
        local anchors = self.points and self.points.kind and self.framePoints or self.points
        return unpack((anchors or {})[index or 1] or {})
    end
    function f:SetAllPoints(relative) self.allPoints=relative or self.parent end
    function f:SetParent(p) self.parent=p end
    function f:SetScale(v) self.scale=v end
    function f:GetScale() return self.scale end
    function f:GetEffectiveScale() return self.scale * (self.parent and self.parent:GetEffectiveScale() or 1) end
    function f:GetAlpha() return self.alpha or 1 end
    function f:SetAlpha(v) self.alpha=v end
    function f:SetFrameLevel(v) self.level=v end
    function f:SetFrameStrata(v) self.strata=v end
    function f:SetBackdrop(v) self.backdrop=v end
    function f:SetBackdropColor(...) self.backdropColor={...} end
    function f:SetBackdropBorderColor(...) self.borderColor={...} end
    function f:SetStatusBarColor(...) self.barColor={...} end
    function f:SetMinMaxValues(a,b) self.minimum=a; self.maximum=b end
    function f:GetMinMaxValues() return self.minimum or 0,self.maximum or 0 end
    function f:SetValue(v)
        if self.kind=="Slider" then
            v=math.max(self.minimum or 0,math.min(v,self.maximum or 0))
            local changed=self.value~=v; self.value=v
            if changed then self:Fire("OnValueChanged",v) end
        else self.value=v end
    end
    function f:GetValue() return self.value or 0 end
    function f:SetOrientation(value) self.orientation=value end
    function f:SetValueStep(value) self.valueStep=value end
    function f:SetObeyStepOnDrag(value) self.obeyStep=value end
    function f:SetThumbTexture(texture) self.thumbTexture=texture end
    function f:GetThumbTexture() return self.thumbTexture end
    function f:SetEnabled(value) self.enabled=not not value end
    function f:IsEnabled() return self.enabled~=false end
    function f:Enable() self:SetEnabled(true) end
    function f:Disable() self:SetEnabled(false) end
    function f:SetNormalTexture(texture) self.normalTexture=texture end
    function f:SetPushedTexture(texture) self.pushedTexture=texture end
    function f:SetDisabledTexture(texture) self.disabledTexture=texture end
    function f:SetHighlightTexture(texture) self.highlightTexture=texture end
    function f:GetStatusBarTexture() if not self.barTexture then self.barTexture=UIObject("Texture",nil,self) end; return self.barTexture end
    function f:SetDrawLayer(v) self.layer=v end
    function f:SetBlendMode(v) self.blendMode=v end
    function f:GetBlendMode() return self.blendMode or "BLEND" end
    function f:SetScrollChild(v) self.scrollChild=v end
    function f:SetVerticalScroll(v) self.scroll=v; self:Fire("OnVerticalScroll",v) end
    function f:GetVerticalScroll() return self.scroll end
    function f:UpdateScrollChildRect() end
    function f:EnableMouse(v) self.mouse=v end
    function f:IsMouseEnabled() return self.mouse end
    function f:EnableMouseWheel(v) self.wheel=v end
    function f:SetClipsChildren(v) self.clips=v end
    function f:SetMovable(v) self.movable=v end
    function f:SetClampedToScreen(v) self.clamped=v end
    function f:SetToplevel(v) self.toplevel=v end
    function f:RegisterForDrag(button) self.dragButton=button end
    function f:StartMoving() self.moving=true end
    function f:StopMovingOrSizing() self.moving=false end
    function f:SetChecked(v) self.checked=v end
    function f:GetChecked() return self.checked end
    function f:RegisterEvent(v) self.events=self.events or {}; self.events[v]=true end
    function f:RegisterUnitEvent(v) self:RegisterEvent(v) end
    function f:SetAutoFocus(v) self.autoFocus=v end
    function f:SetMaxLetters(v) self.maxLetters=v end
    function f:ClearFocus() self.focused=false end
    function f:SetFocus() self.focused=true end
    function f:SetJustifyH(v) self.justify=v end
    function f:SetJustifyV(v) self.justifyVertical=v end
    function f:SetWordWrap(v) self.wordWrap=v end
    function f:SetShadowOffset(...) self.shadow={...} end
    function f:CreateTexture(name) return UIObject("Texture",name,self) end
    function f:CreateLine(name) return UIObject("Line",name,self) end
    function f:SetThickness(value) self.thickness=value end
    function f:SetStartPoint(...) self.startPoint={...} end
    function f:SetEndPoint(...) self.endPoint={...} end
    function f:CreateMaskTexture(name,layer)
        local mask=UIObject("MaskTexture",name,self); mask:SetDrawLayer(layer); return mask
    end
    function f:AddMaskTexture(mask)
        self.masks=self.masks or {}; self.masks[#self.masks+1]=mask
    end
    function f:RemoveMaskTexture(mask)
        for i=#(self.masks or {}),1,-1 do if self.masks[i]==mask then table.remove(self.masks,i) end end
    end
    function f:CreateFontString(name) return UIObject("FontString",name,self) end
    return f
end
UIParent=UIObject("Frame","UIParent")
UIParent:SetSize(1280,900)
UISpecialFrames={}
tinsert=table.insert
function HideUIPanel(frame) frame:Hide() end
function ShowUIPanel(frame) frame:Show() end
function CategoryRoot(model,key)
    local category,seen=model.byCategory[key],{}
    while category and category.parent and not seen[category.key] do
        seen[category.key]=true
        category=model.byCategory[category.parent]
    end
    return category and category.key
end

-- Default fixture order is native selector first. A regression test reverses
-- it because the actual owner-keyed CallbackRegistry has no ordering guarantee.
EventRegistry={callbacks={}}
function EventRegistry:RegisterCallback(event, fn, owner)
    self.callbacks[event]=self.callbacks[event] or {}
    self.callbacks[event][#self.callbacks[event]+1]={fn=fn,owner=owner}
end
function EventRegistry:UnregisterCallback(event, owner)
    for i=#(self.callbacks[event] or {}),1,-1 do
        if self.callbacks[event][i].owner==owner then table.remove(self.callbacks[event],i) end
    end
end
function EventRegistry:TriggerEvent(event,...)
    for _, entry in ipairs(self.callbacks[event] or {}) do entry.fn(entry.owner,...) end
end
InputUtil={high={},ordinary={}}
function InputUtil.IsGamepadUIEnabled() return gamepad==true end
function InputUtil.RegisterForHighPrioInterfaceTransitions(owner)
    InputUtil.high[owner]=InputUtil.high[owner] or {}
end
function InputUtil.RegisterForInterfaceTransitions(owner)
    InputUtil.ordinary[owner]=InputUtil.ordinary[owner] or {}
end
local function inputCallbacks(owner) return InputUtil.high[owner] or InputUtil.ordinary[owner] end
function InputUtil.RegisterGamepadInit(owner,fn)
    inputCallbacks(owner).gamepad=fn; if gamepad then fn() end
end
function InputUtil.RegisterMKBInit(owner,fn)
    inputCallbacks(owner).mkb=fn; if not gamepad then fn() end
end
function ChangeInputMode(toGamepad)
    gamepad=toGamepad
    for _, group in ipairs({InputUtil.high,InputUtil.ordinary}) do
        for _, callbacks in pairs(group) do
            local fn=toGamepad and callbacks.gamepad or callbacks.mkb
            if fn then fn() end
        end
    end
end
function NativeFrame(name, parent)
    local f = UIObject("Frame",name,parent)
    f.native=true
    local mountable=name=="RewardTrackPage" or name=="TreePage"
    local presentation={SetPoint=true,ClearAllPoints=true,SetAllPoints=true,SetScale=true,
        SetSize=true,SetWidth=true,SetHeight=true,SetFrameLevel=true,SetFrameStrata=true}
    for _, method in ipairs({"SetScript","SetParent","SetPoint","ClearAllPoints","SetAllPoints","SetScale","SetFrameLevel",
        "SetSize","SetWidth","SetHeight","EnableMouse","EnableMouseWheel","SetAlpha","SetFrameStrata","SetDataProvider",
        "SelectCategory","SelectChallenge","GenerateDataProvider","ClaimReward"}) do
        if not (mountable and presentation[method]) and not (name=="LegacySystemFrame" and (method=="EnableMouse" or method=="SetAlpha")) then
            f[method]=poison(name .. ":" .. method)
        end
    end
    return f
end
function SetupNative()
    LegacySystemFrame = NativeFrame("LegacySystemFrame",UIParent)
    LegacySystemFrame.strata="DIALOG"
    LegacySystemFrame.width=920; LegacySystemFrame.height=575
    LegacySystemFrame.mouse=true
    LegacySystemFrame.points={{"CENTER",UIParent,"CENTER",24,10}}
    LegacySystemFrame.currentPage=2
    LegacySystemFrame.Background=LegacySystemFrame:CreateTexture("LegacyRootBackground")
    LegacySystemFrame.EdgeArt=LegacySystemFrame:CreateTexture("LegacyRootEdge")
    for _, field in ipairs({"NineSlice","PortraitContainer","TitleContainer","CloseButton","NativeTabs"}) do
        LegacySystemFrame[field]=NativeFrame(field,LegacySystemFrame)
    end
    local page=NativeFrame("ChallengesPage",LegacySystemFrame)
    page.width=920; page.height=575
    page.points={{"TOPLEFT",LegacySystemFrame,"TOPLEFT",0,0}}
    LegacySystemFrame.ChallengesPage=page
    page.DetailPane=NativeFrame("DetailPane",page)
    page.DetailPane.ScrollBox=NativeFrame("ScrollBox",page.DetailPane)
    page.DetailPane.ScrollBox.level=40
    page.DetailPane.ScrollBox.dataProvider={collection={{achievementID=62013}}}
    local reward=NativeFrame("RewardTrackPage",LegacySystemFrame)
    reward.width=910; reward.height=569; reward.level=100
    reward.points={{"TOPLEFT",LegacySystemFrame,"TOPLEFT",7,-5}}
    reward.Background=reward:CreateTexture("RewardBackground")
    reward.majorFactionData={factionID=2802,renownLevel=16}
    LegacySystemFrame.RewardTrackPage=reward
    local tree=NativeFrame("TreePage",LegacySystemFrame)
    tree.width=920; tree.height=575; tree.level=100
    tree.points={{"TOPLEFT",LegacySystemFrame,"TOPLEFT",0,0}}
    tree.Background=tree:CreateTexture("TreeBackground")
    tree.VerticalDivider=tree:CreateTexture("TreeDivider")
    LegacySystemFrame.TreePage=tree
    LegacySystemFrame.Pages={reward,page,tree}
    LegacySystemFrame.Tabs={LegacySystemFrame.NativeTabs}
    reward.shown=false; tree.shown=false
    nativeShows,rootShows,rootHides,rewardShows,treeShows=0,0,0,0,0
    page.scripts.OnShow=function() nativeShows=nativeShows+1 end
    originalShow=page.scripts.OnShow
    reward.scripts.OnShow=function(self) assert(self:GetParent()==LegacySystemFrame); rewardShows=rewardShows+1 end
    tree.scripts.OnShow=function(self) assert(self:GetParent()==LegacySystemFrame); treeShows=treeShows+1 end
    LegacySystemFrame.scripts.OnShow=function() rootShows=rootShows+1 end
    LegacySystemFrame.scripts.OnHide=function() rootHides=rootHides+1 end
    originalRootShow,originalRootHide=LegacySystemFrame.scripts.OnShow,LegacySystemFrame.scripts.OnHide
    EventRegistry:RegisterCallback("Legacy.SelectPage",function(_,id)
        LegacySystemFrame.currentPage=id
        for i,nativePage in ipairs(LegacySystemFrame.Pages) do nativePage:SetShown(i==id) end
    end,LegacySystemFrame)
    InputUtil.RegisterForInterfaceTransitions(LegacySystemFrame)
    InputUtil.RegisterGamepadInit(LegacySystemFrame,function()
        nativeGamepadSawNormal=LegacySystemFrame.Background:IsShown() and LegacySystemFrame:IsMouseEnabled()
            and (not FAWrathLegacyCover or not FAWrathLegacyCover:IsShown())
    end)
    return page
end
function GetCategoryList() return {15607,15587,15596} end
function GetCategoryInfo(id)
    if id==15607 then return "Exploration",-1,0 end
    if id==15587 then return "Alchemy",15596,0 end
    return "Adventure",-1,0
end
function GetCategoryNumAchievements(id) return 1,0,1 end
function GetAchievementInfo(id,index)
    if index then id=({[15607]=62053,[15587]=62013,[15596]=62382})[id] end
    if id==62013 then return id,"Expert Alchemist",0,false,nil,nil,nil,"Reach 225 skill in Alchemy for the first time.",134349824,136240,"Earn 1 Legacy Point.",false,false end
    if id==62053 then return id,"Explore Azeroth",0,false,nil,nil,nil,"Complete the zone map on a single character.",0,237388,"",false,false end
    if id==62382 then return id,"Explorer",0,false,nil,nil,nil,"Have a character with Explore Azeroth.",134349824,237387,"Earn 1 Legacy Point.",false,false end
    if id==62353 then return id,"Eastern Kingdoms",0,false,nil,nil,nil,"Explore Eastern Kingdoms.",0,237388,"" end
end
function GetAchievementNumCriteria(id) return id==62053 and 2 or 1 end
function GetAchievementCriteriaInfo(id,index)
    if id==62013 then return "225 Alchemy Skill",7,false,0,225,1,1,2937,"0 / 225",111540,true end
    return index==1 and "Eastern Kingdoms" or "Kalimdor",8,false,0,1,0,0,62353,"0",117287,true
end
'''


class Harness:
    def __init__(self, controller=False):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(BASE)
        self.g = self.lua.globals()
        self.templates = {e.get("name"): e for e in ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()}
        self.g.CreateFrame = self.create
        for path in ("Integrations/LegacyAdapter.lua", "Integrations/Performance.lua", "Integrations/CustomAdapter.lua",
                     "Integrations/Presentation.lua", "Integrations/StatisticsAdapter.lua",
                     "UI/WrathAchievementUI.lua"):
            self.load(path)
        if controller:
            self.g.SetupNative()
            self.load("Integrations/LegacyWindowBridge.lua")
            self.load("Integrations/LegacyController.lua")

    def load(self, path):
        fn = self.lua.execute("return assert(loadstring(...))", (ADDON / path).read_text(), "@" + path)
        fn("ForeverAchievements", self.g.ns)

    def create(self, kind, name=None, parent=None, template=None):
        f = self.g.UIObject(kind, name, parent)
        if template in self.templates:
            self.build(f, self.templates[template])
        elif template not in (None, "BackdropTemplate", "InputBoxTemplate", "UIPanelScrollFrameTemplate", "UIPanelCloseButton"):
            raise AssertionError("Unadapted dependency: " + template)
        return f

    def build(self, f, element):
        inherit = element.get("inherits")
        if inherit in self.templates:
            self.build(f, self.templates[inherit])
        elif inherit and inherit not in ("BackdropTemplate", "UIPanelCloseButton"):
            raise AssertionError("Unexpected frame inheritance: " + inherit)
        size = element.find(URI + "Size")
        if size is not None:
            dimension = size.find(URI + "AbsDimension")
            dimension = dimension if dimension is not None else size
            if dimension.get("x"): f.width = float(dimension.get("x"))
            if dimension.get("y"): f.height = float(dimension.get("y"))
        f.shown = element.get("hidden") != "true"
        layers = element.find(URI + "Layers")
        if layers is not None:
            for layer in layers:
                for region in layer:
                    self.child(f, region)
        button_text = element.find(URI + "ButtonText")
        if button_text is not None:
            f.text = self.child(f, button_text)
        children = element.find(URI + "Frames")
        if children is not None:
            for child in children:
                self.child(f, child)
        scripts = element.find(URI + "Scripts")
        if scripts is not None:
            for script in scripts:
                body = script.text or ""
                callback = self.lua.execute("return function(self) " + body + " end")
                event = script.tag.removeprefix(URI)
                f.SetScript(f, event, callback)
                if event == "OnLoad":
                    callback(f)

    def child(self, parent, element):
        name = element.get("name")
        name = name.replace("$parent", parent.name) if name else None
        kind = element.tag.removeprefix(URI)
        if kind in ("Frame", "Button", "CheckButton", "StatusBar", "ScrollFrame"):
            child = self.create(kind, name, parent, element.get("inherits"))
            # Instances add attributes/regions to an inherited template.
            local = ET.fromstring(ET.tostring(element))
            local.attrib.pop("inherits", None)
            self.build(child, local)
        else:
            child = self.g.UIObject(kind, name, parent)
            if element.get("text"): child.SetText(child, element.get("text"))
        if element.get("parentKey"): parent[element.get("parentKey")] = child
        return child

    def execute(self, code):
        return self.lua.execute(code)

    def enable(self):
        self.execute('ns.FA.SLASH.legacyui("on")')
        self.execute('FlushTimers()')


class AdapterTests(unittest.TestCase):
    def setUp(self): self.h = Harness()
    def check(self, code): self.h.execute(code)

    def test_live_alchemist_preserves_real_points_and_numeric_criteria(self):
        self.check('''
            local a=ns.LegacyAdapter.Resolve(62013)
            assert(a.key=="legacy:62013" and a.points==1 and a.completed==false)
            local c=ns.LegacyAdapter.Criteria(a)
            assert(c.items[1].current==0 and c.items[1].required==225 and c.items[1].criteriaID==111540)
            assert(#calls==0)
        ''')

    def test_runtime_catalog_avoids_mirrored_ids_and_maps_native_children(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62382"] and not m.byKey["legacy:64015"])
            assert(CategoryRoot(m,"legacy-category:15587")=="professions")
            assert(#ns.LegacyPresentation.Rows(m,"professions")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy")==1)
            assert(m.byKey["legacy:62382"].unifiedRoot=="exploration")
            assert(m.byKey["legacy:62053"].unifiedRoot=="exploration")
        ''')

    def test_custom_native_ids_do_not_collide_or_import_synthetic_points(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62013"]~=m.byKey["custom:first"])
            assert(not m.byKey["custom:imported"])
            assert(m.custom.points==10 and m.custom.possiblePoints==30 and m.native.points==16)
        ''')

    def test_other_character_completion_is_not_granted_in_account_view(self):
        self.check('''
            settings.accountView=true
            local a=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(a.completed==false and saved.done.second==nil)
            assert(saved.history[1]=="keep" and saved.explored.zone.old)
        ''')

    def test_unavailable_points_are_unknown_not_zero_or_ten(self):
        self.check('''
            C_Traits.GetTraitCurrencyForAchievement=nil
            C_MajorFactions.GetCurrentRenownLevel=nil
            assert(ns.LegacyAdapter.Resolve(62013).points==nil)
            assert(ns.LegacyAdapter.Catalog().points==nil)
        ''')

    def test_unavailable_criteria_and_zero_criteria_are_distinct(self):
        self.check('''
            local a=ns.LegacyAdapter.Resolve(62013)
            GetAchievementNumCriteria=nil
            assert(not ns.LegacyAdapter.Criteria(a).available)
            GetAchievementNumCriteria=function() return 0 end
            local c=ns.LegacyAdapter.Criteria(a)
            assert(c.available and c.complete and c.count==0 and a.completed==false)
        ''')

    def test_all_criteria_done_does_not_invent_native_completion(self):
        self.check('''
            GetAchievementCriteriaInfo=function() return "Done",7,true,225,225,1,1,2937,"225 / 225",1 end
            local a=ns.LegacyAdapter.Resolve(62013)
            assert(ns.LegacyAdapter.Criteria(a).items[1].completed)
            assert(a.completed==false)
        ''')

    def test_partial_criteria_errors_and_bounds_are_reported(self):
        self.check('''
            GetAchievementNumCriteria=function() return 300 end
            GetAchievementCriteriaInfo=function() error("Not loaded") end
            local c=ns.LegacyAdapter.Criteria(ns.LegacyAdapter.Resolve(62013))
            assert(c.available and not c.complete and #c.items==256)
        ''')

    def test_meta_links_resolve_without_native_selection(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            local c=ns.LegacyPresentation.Criteria(m.byKey["legacy:62053"])
            assert(c.items[1].link=="legacy:62353")
            assert(ns.LegacyPresentation.Resolve(m,c.items[1].link).name=="Eastern Kingdoms")
            assert(#calls==0)
        ''')

    def test_current_provider_fallback_is_partial_and_re_reads_replacement(self):
        self.check('''
            local page=SetupNative()
            GetCategoryList=nil
            local box=page.DetailPane.ScrollBox
            box.dataProvider={collection={{achievementID=62013}}}
            local a=ns.LegacyAdapter.Catalog(page)
            assert(a.partial and #a.records==1 and a.records[1].id==62013 and a.notice)
            box.dataProvider={collection={{achievementID=62382}}}
            local b=ns.LegacyAdapter.Catalog(page)
            assert(b.records[1].id==62382)
        ''')

    def test_missing_native_data_retains_custom_ui_model(self):
        self.check('''
            GetCategoryList=nil
            local m=ns.LegacyPresentation.Build()
            assert(#m.native.records==0 and m.native.notice and #m.custom.records==2)
        ''')

    def test_search_and_completion_filters_are_local(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            assert(#ns.LegacyPresentation.Rows(m,"summary","alchemist","Incomplete")==1)
            assert(#ns.LegacyPresentation.Rows(m,"custom","","Complete")==1)
            assert(#calls==0)
        ''')

    def test_secret_and_nonfinite_fields_are_not_used(self):
        self.check('''
            local secret={}
            issecretvalue=function(v) return v==secret end
            assert(ns.LegacyReadOnly.Number(secret)==nil)
            assert(ns.LegacyReadOnly.Number(0/0)==nil)
            assert(ns.LegacyReadOnly.ID(math.huge)==nil)
            C_Traits.GetTraitCurrencyForAchievement=function() return secret end
            assert(ns.LegacyAdapter.Resolve(62013).points==nil)
        ''')

    def test_malformed_category_cycles_remain_browsable(self):
        self.check('''
            GetCategoryInfo=function(id) return "Cycle",id==15607 and 15587 or 15607 end
            local m=ns.LegacyPresentation.Build()
            assert(#ns.LegacyPresentation.Rows(m,"legacy")==3)
        ''')

    def test_custom_progress_failure_never_awards_or_deletes_saved_data(self):
        self.check('''
            ns.FA.BY_KEY.second.progress=function() error("API unavailable") end
            local a=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(a.current==nil and not a.completed)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep")
        ''')

    def test_custom_tracking_never_calls_native_tracking(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            ns.CustomAchievementAdapter.Track(m.byKey["legacy:62013"])
            ns.CustomAchievementAdapter.Track(m.byKey["custom:second"])
            assert(saved.tracked.second==true and #calls==0)
        ''')


class ControllerTests(unittest.TestCase):
    def setUp(self): self.h = Harness(controller=True)
    def check(self, code): self.h.execute(code)

    def test_default_off_creates_no_cover_or_native_hooks(self):
        self.check('''
            assert(settings.legacyUI==nil and FAWrathLegacyCover==nil)
            assert(next(LegacySystemFrame.ChallengesPage.hooks)==nil)
            assert(#calls==0)
        ''')

    def test_enable_uses_standard_size_and_restores_original_native_window(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            assert(c.state=="Enabled", c.state)
            assert(c.cover.parent==UIParent and c.cover.width==960 and c.cover.height==760)
            assert(c.cover:IsVisible() and c.ui.root.parent==c.cover and c.ui.root.scale==1)
            assert(c.ui.root.width==960 and c.ui.root.height==620)
            assert(not LegacySystemFrame.Background:IsShown() and not LegacySystemFrame.NineSlice:IsShown())
            assert(not LegacySystemFrame.NativeTabs:IsShown() and not LegacySystemFrame.ChallengesPage:IsShown())
            assert(not LegacySystemFrame:IsMouseEnabled())
            assert(LegacySystemFrame:GetScript("OnShow")==originalRootShow)
            assert(LegacySystemFrame:GetScript("OnHide")==originalRootHide)
            assert(#calls==0)
        ''')

    def test_size_presets_persist_real_content_dimensions_without_upscaling_art(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local done,history,explored=saved.done,saved.history,saved.explored
            local originalDefinition=ns.FA.BY_KEY.first
            local cases={{"compact","Compact",768,640,500},{"standard","Standard",960,760,620},{"large","Large",1024,860,720}}
            for _,case in ipairs(cases) do
                ns.FA.SLASH.legacyui("size "..case[1]); FlushTimers()
                assert(settings.legacyUISize==case[2])
                assert(c.cover:GetWidth()==case[3] and c.cover:GetHeight()==case[4])
                assert(c.ui.root:GetWidth()==case[3] and c.ui.root:GetHeight()==case[5])
                assert(c.ui.root:GetScale()==1 and c.cover:GetScale()<=1)
                assert(c.cover:GetParent()==UIParent and c.cover:IsVisible())
                local _,relative=c.cover:GetPoint(1)
                assert(relative==UIParent)
                assert(saved.done==done and saved.history==history and saved.explored==explored)
                assert(ns.FA.BY_KEY.first==originalDefinition and saved.done.first==1730000000)
            end
            assert(saved.history[1]=="keep" and saved.explored.zone.old and #calls==0)
        ''')

    def test_selecting_size_while_disabled_does_not_enable_native_replacement(self):
        self.check('''
            ns.FA.SLASH.legacyui("size large")
            assert(settings.legacyUISize=="Large" and not settings.legacyUI)
            assert(FAWrathLegacyCover==nil and LegacySystemFrame.NativeTabs:IsShown())
            assert(LegacySystemFrame:IsMouseEnabled() and next(LegacySystemFrame.ChallengesPage.hooks)==nil)
            ns.FA.SLASH.legacyui("on"); FlushTimers()
            assert(ns.LegacyUIController.cover:GetWidth()==1024 and #calls==0)
        ''')

    def test_size_cycle_callback_persists_choice_across_refreshes(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            assert(type(c.ui.callbacks.onSizePresetCycle)=="function")
            for _,expected in ipairs({"Large","Compact","Standard"}) do
                c.ui.callbacks.onSizePresetCycle(); FlushTimers()
                assert(settings.legacyUISize==expected and c.cover:IsVisible())
                local width=c.cover:GetWidth()
                c:Refresh()
                assert(c.cover:GetWidth()==width and settings.legacyUISize==expected)
            end
            assert(#calls==0)
        ''')

    def test_drag_position_persists_without_native_frame_reference(self):
        # The larger default needs room for the requested unconstrained drag;
        # screen-edge clamping is covered independently below.
        self.h.execute('UIParent:SetSize(1600,1000)')
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            FAWrathAchievementFrameHeader:Fire("OnDragStart")
            assert(c.cover.moving)
            c.cover:ClearAllPoints(); c.cover:SetPoint("CENTER",UIParent,"CENTER",85,-35)
            c:Refresh()
            local _,relative,_,x,y=c.cover:GetPoint(1)
            assert(relative==UIParent and x==85 and y==-35)
            FAWrathAchievementFrameHeader:Fire("OnDragStop")
            local position=settings.legacyUIPosition
            assert(not c.cover.moving and type(position)=="table")
            assert(position.point=="CENTER" and position.relativePoint=="CENTER")
            assert(math.abs(position.x-85)<.01 and math.abs(position.y+35)<.01)
            for _,value in pairs(position) do assert(type(value)=="string" or type(value)=="number") end
            LegacySystemFrame:Hide(); LegacySystemFrame:Show(); FlushTimers()
            local point,relative,relativePoint,x,y=c.cover:GetPoint(1)
            assert(point=="CENTER" and relative==UIParent and relativePoint=="CENTER")
            assert(math.abs(x-85)<.01 and math.abs(y+35)<.01)
            assert(saved.history[1]=="keep" and #calls==0)
        ''')

    def test_login_restores_preset_and_position_independently_of_native_anchor(self):
        h=Harness()
        h.execute('''
            SetupNative(); settings.legacyUI=true; settings.legacyUISize="Compact"
            settings.legacyUIPosition={point="CENTER",relativePoint="CENTER",x=110,y=45}
        ''')
        h.load("Integrations/LegacyWindowBridge.lua")
        h.load("Integrations/LegacyController.lua")
        h.execute('''
            for _,frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_LOGIN then frame:Fire("OnEvent","PLAYER_LOGIN"); break end
            end
            local c=ns.LegacyUIController
            assert(c.cover:IsVisible() and c.cover:GetWidth()==768 and c.cover:GetHeight()==640)
            local point,relative,relativePoint,x,y=c.cover:GetPoint(1)
            assert(point=="CENTER" and relative==UIParent and relativePoint=="CENTER" and x==110 and y==45)
            local _,nativeRelative,_,nativeX,nativeY=LegacySystemFrame:GetPoint(1)
            assert(nativeRelative==UIParent and nativeX==24 and nativeY==10)
            assert(saved.done.first==1730000000 and saved.explored.zone.old and #calls==0)
        ''')

    def test_reset_centers_window_without_resetting_size_selection_or_progress(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            ns.FA.SLASH.legacyui("size large"); FlushTimers()
            c.ui.tabs[3]:Fire("OnClick")
            settings.legacyUIPosition={point="CENTER",relativePoint="CENTER",x=99999,y=-99999}
            ns.FA.SLASH.legacyui("reset"); FlushTimers()
            local position=settings.legacyUIPosition
            assert(position==nil or position.point=="CENTER" and position.relativePoint=="CENTER" and position.x==0 and position.y==0)
            local point,relative,relativePoint,x,y=c.cover:GetPoint(1)
            assert(point=="CENTER" and relative==UIParent and relativePoint=="CENTER" and x==0 and y==0)
            assert(settings.legacyUISize=="Large" and settings.legacyUI and c.ui.tab=="trees")
            assert(LegacySystemFrame.TreePage:IsVisible() and LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_offscreen_saved_position_is_clamped_into_available_screen(self):
        self.check('''
            settings.legacyUIPosition={point="CENTER",relativePoint="CENTER",x=99999,y=-99999}
            ns.FA.SLASH.legacyui("on"); FlushTimers()
            local cover=ns.LegacyUIController.cover
            local scale=cover:GetEffectiveScale()/UIParent:GetEffectiveScale()
            assert(cover:GetLeft()*scale>=9.99 and cover:GetBottom()*scale>=9.99)
            assert(cover:GetRight()*scale<=UIParent:GetWidth()-9.99)
            assert(cover:GetTop()*scale<=UIParent:GetHeight()-9.99)
            assert(cover:IsVisible() and #calls==0)
        ''')

    def test_malformed_saved_geometry_uses_safe_defaults(self):
        self.check('''
            settings.legacyUISize="Enormous"
            settings.legacyUIPosition={point="NOT_AN_ANCHOR",relativePoint={},x=0/0,y=math.huge}
            ns.FA.SLASH.legacyui("on"); FlushTimers()
            local c=ns.LegacyUIController
            assert(c.cover:IsVisible() and c.cover:GetWidth()==960 and c.cover:GetHeight()==760)
            local point,relative,relativePoint,x,y=c.cover:GetPoint(1)
            assert(point=="CENTER" and relative==UIParent and relativePoint=="CENTER" and x==0 and y==0)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_invalid_preset_command_keeps_active_geometry_and_settings(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            ns.FA.SLASH.legacyui("size compact"); FlushTimers()
            ns.FA.SLASH.legacyui("size unsupported")
            assert(settings.legacyUISize=="Compact" and settings.legacyUI)
            assert(c.cover:GetWidth()==768 and c.cover:GetHeight()==640 and c.cover:IsVisible())
            assert(LegacySystemFrame.ChallengesPage:GetScript("OnShow")==originalShow and #calls==0)
        ''')

    def test_combat_preset_change_defers_protected_native_geometry(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            local tree=LegacySystemFrame.TreePage
            local writes=0
            for _,name in ipairs({"SetPoint","ClearAllPoints","SetScale","SetSize","SetFrameLevel","SetFrameStrata"}) do
                local original=tree[name]
                tree[name]=function(self,...)
                    writes=writes+1
                    return original(self,...)
                end
            end
            tree.protected=true; inCombat=true
            ns.FA.SLASH.legacyui("size large")
            assert(settings.legacyUISize=="Large" and writes==0)
            assert(tree:GetParent()==LegacySystemFrame and saved.done.first==1730000000)
            tree.protected=false; inCombat=false
            for _,frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_REGEN_ENABLED then frame:Fire("OnEvent","PLAYER_REGEN_ENABLED"); break end
            end
            FlushTimers()
            assert(c.cover:IsVisible() and c.cover:GetWidth()==1024 and c.ui.tab=="trees")
            assert(tree:IsVisible() and tree:GetParent()==LegacySystemFrame and #calls==0)
        ''')

    def test_size_layout_failure_restores_native_page_and_keeps_saved_history(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[2]:Fire("OnClick")
            local fit=c.ui.Fit
            c.ui.Fit=function() error("Injected preset layout failure") end
            ns.FA.SLASH.legacyui("size compact"); FlushTimers()
            local reward=LegacySystemFrame.RewardTrackPage
            assert(not c.cover:IsShown() and c.state:find("Fallback"))
            assert(reward:IsVisible() and reward:GetParent()==LegacySystemFrame and reward:GetScale()==1)
            assert(reward:GetWidth()==910 and reward:GetHeight()==569 and reward.Background:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and settings.legacyUISize=="Compact")
            c.ui.Fit=fit; ns.FA.SLASH.legacyui("on"); FlushTimers()
            assert(c.cover:IsVisible() and c.cover:GetWidth()==768 and #calls==0)
        ''')

    def test_disable_preserves_native_function_script_provider_and_rewards(self):
        self.h.enable()
        self.check('''
            local page=LegacySystemFrame.ChallengesPage
            local provider=page.DetailPane.ScrollBox.dataProvider
            local reward=LegacySystemFrame.RewardTrackPage.majorFactionData
            ns.FA.SLASH.legacyui("off")
            assert(not ns.LegacyUIController.cover:IsShown() and settings.legacyUI==false)
            assert(page:GetScript("OnShow")==originalShow and page.DetailPane.ScrollBox.dataProvider==provider)
            assert(page.parent==LegacySystemFrame and page.width==920 and reward.renownLevel==16)
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NineSlice:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            local previousShows=nativeShows
            page:Fire("OnShow")
            assert(nativeShows==previousShows+1 and not ns.LegacyUIController.cover:IsShown() and #calls==0)
        ''')

    def test_native_external_page_events_use_unified_tabs_and_keep_native_ancestry(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            EventRegistry:TriggerEvent("Legacy.SelectPage",1); FlushTimers()
            assert(c.cover:IsVisible() and c.ui.tab=="rewards")
            assert(LegacySystemFrame.RewardTrackPage:IsVisible())
            assert(LegacySystemFrame.RewardTrackPage:GetParent()==LegacySystemFrame)
            EventRegistry:TriggerEvent("Legacy.SelectPage",3); FlushTimers()
            assert(c.ui.tab=="trees" and LegacySystemFrame.TreePage:IsVisible())
            assert(LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame)
            EventRegistry:TriggerEvent("Legacy.SelectPage",2); FlushTimers()
            assert(c.ui.tab=="achievements" and not LegacySystemFrame.ChallengesPage:IsShown())
            local level=c.cover.level
            LegacySystemFrame:Hide(); LegacySystemFrame:Show()
            FlushTimers()
            assert(c.cover:IsVisible() and c.cover.level==level)
            assert(LegacySystemFrame.ChallengesPage:GetScript("OnShow")==originalShow and #calls==0)
        ''')

    def test_unordered_native_event_callbacks_read_final_selection_after_dispatch(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            -- Client CallbackRegistry owners have no guaranteed dispatch order.
            -- Deliberately run the addon observer before the native selector.
            EventRegistry.TriggerEvent=function(self,event,...)
                local entries=self.callbacks[event] or {}
                for i=#entries,1,-1 do entries[i].fn(entries[i].owner,...) end
            end
            EventRegistry:TriggerEvent("Legacy.SelectPage",1)
            assert(LegacySystemFrame.currentPage==1)
            FlushTimers()
            assert(c.ui.tab=="rewards" and LegacySystemFrame.currentPage==1)
            assert(LegacySystemFrame.RewardTrackPage:IsVisible())
            EventRegistry:TriggerEvent("Legacy.SelectPage",1)
            EventRegistry:TriggerEvent("Legacy.SelectPage",3)
            assert(LegacySystemFrame.currentPage==3)
            FlushTimers()
            assert(c.ui.tab=="trees" and LegacySystemFrame.currentPage==3)
            assert(LegacySystemFrame.TreePage:IsVisible() and not LegacySystemFrame.RewardTrackPage:IsShown())
            assert(c.cover:IsVisible() and #calls==0)
        ''')

    def test_four_tabs_mount_live_pages_and_restore_geometry_on_disable(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local reward,tree=LegacySystemFrame.RewardTrackPage,LegacySystemFrame.TreePage
            local function checkOriginalReward()
                local point,relative,relativePoint,x,y=reward:GetPoint(1)
                assert(point=="TOPLEFT" and relative==LegacySystemFrame and relativePoint=="TOPLEFT" and x==7 and y==-5)
                assert(reward:GetScale()==1 and reward:GetFrameLevel()==100 and reward:GetFrameStrata()=="DIALOG")
                assert(reward.width==910 and reward.height==569 and reward.Background:IsShown())
            end
            c.ui.tabs[2]:Fire("OnClick")
            assert(c.ui.tab=="rewards" and LegacySystemFrame.currentPage==1 and reward:IsVisible())
            assert(FAWrathAchievementFrameCloseButton:GetFrameLevel()>reward:GetFrameLevel())
            local _,relative=reward:GetPoint(1)
            assert(relative==c.ui.nativeHost and reward:GetParent()==LegacySystemFrame)
            assert(reward.Background:IsShown())
            assert(reward:GetWidth()*reward:GetEffectiveScale()<=c.ui.nativeHost:GetWidth()*c.ui.nativeHost:GetEffectiveScale()+.01)
            assert(reward:GetHeight()*reward:GetEffectiveScale()<=c.ui.nativeHost:GetHeight()*c.ui.nativeHost:GetEffectiveScale()+.01)
            c.ui.tabs[3]:Fire("OnClick")
            assert(c.ui.tab=="trees" and LegacySystemFrame.currentPage==3 and tree:IsVisible())
            assert(FAWrathAchievementFrameCloseButton:GetFrameLevel()>tree:GetFrameLevel())
            assert(tree:GetParent()==LegacySystemFrame and tree.Background:IsShown() and tree.VerticalDivider:IsShown())
            assert(not reward:IsShown() and reward:GetParent()==LegacySystemFrame)
            c.ui.tabs[4]:Fire("OnClick")
            assert(c.ui.tab=="statistics" and not reward:IsShown() and not tree:IsShown())
            assert(tree:GetParent()==LegacySystemFrame)
            c.ui.tabs[2]:Fire("OnClick")
            ns.FA.SLASH.legacyui("off")
            checkOriginalReward()
            assert(tree:GetScale()==1 and tree.width==920 and tree.height==575 and tree.VerticalDivider:IsShown())
            assert(reward:GetParent()==LegacySystemFrame and reward:IsVisible())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(#calls==0)
        ''')

    def test_normal_close_restores_native_page_then_reopening_reapplies(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            FAWrathAchievementFrameCloseButton:Fire("OnClick")
            assert(not LegacySystemFrame:IsShown() and not c.cover:IsShown() and rootHides==1)
            assert(LegacySystemFrame.TreePage:GetScale()==1 and LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame)
            LegacySystemFrame:Show()
            FlushTimers()
            assert(rootShows==1 and c.cover:IsVisible() and c.ui.tab=="trees")
            assert(LegacySystemFrame:GetScript("OnHide")==originalRootHide)
            assert(LegacySystemFrame:GetScript("OnShow")==originalRootShow and #calls==0)
        ''')

    def test_gamepad_restores_before_native_initialization_and_mkb_resumes(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            ChangeInputMode(true)
            assert(nativeGamepadSawNormal)
            assert(not c.cover:IsShown() and LegacySystemFrame.TreePage:GetScale()==1)
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(settings.legacyUI)
            ChangeInputMode(false); FlushTimers()
            assert(c.cover:IsVisible() and c.ui.tab=="trees" and #calls==0)
            ns.FA.SLASH.legacyui("off")
            ChangeInputMode(true); ChangeInputMode(false); FlushTimers()
            assert(not c.cover:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
        ''')

    def test_initial_gamepad_enable_resumes_on_mkb_with_already_open_root(self):
        self.check('''
            gamepad=true
            ns.FA.SLASH.legacyui("on")
            assert(settings.legacyUI and LegacySystemFrame:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(not FAWrathLegacyCover or not FAWrathLegacyCover:IsShown())
            ChangeInputMode(false); FlushTimers()
            local c=ns.LegacyUIController
            assert(c.root==LegacySystemFrame and c.cover:IsVisible())
            assert(not LegacySystemFrame.NativeTabs:IsShown() and #calls==0)
        ''')

    def test_initial_gamepad_enable_attaches_to_closed_root_without_opening_it(self):
        self.check('''
            LegacySystemFrame:Hide()
            gamepad=true
            ns.FA.SLASH.legacyui("on")
            assert(not LegacySystemFrame:IsShown())
            ChangeInputMode(false); FlushTimers()
            local c=ns.LegacyUIController
            assert(c.root==LegacySystemFrame and not c.cover:IsVisible())
            assert(not LegacySystemFrame:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            LegacySystemFrame:Show()
            FlushTimers()
            assert(c.cover:IsVisible() and not LegacySystemFrame.NativeTabs:IsShown() and #calls==0)
        ''')

    def test_custom_refresh_does_not_reinitialize_selected_native_page(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            local before=treeShows
            c:Refresh(); c:Refresh()
            assert(treeShows==before and LegacySystemFrame.TreePage:IsVisible())
            assert(LegacySystemFrame.currentPage==3 and #calls==0)
        ''')

    def test_rejected_restoration_keeps_working_ui_until_protection_clears(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            LegacySystemFrame.TreePage.protected=true
            inCombat=true
            ns.FA.SLASH.legacyui("off")
            assert(not settings.legacyUI and c.restorePending and c.cover:IsVisible())
            assert(not LegacySystemFrame.NativeTabs:IsShown())
            LegacySystemFrame.TreePage.protected=false
            inCombat=false
            for _, frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_REGEN_ENABLED then frame:Fire("OnEvent","PLAYER_REGEN_ENABLED"); break end
            end
            assert(not c.restorePending and not c.cover:IsShown())
            assert(LegacySystemFrame.TreePage:GetScale()==1 and LegacySystemFrame.NativeTabs:IsShown())
            assert(LegacySystemFrame:IsMouseEnabled() and #calls==0)
        ''')

    def test_drag_cleanup_failure_does_not_block_native_restoration(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire("OnClick")
            FAWrathAchievementFrameHeader:Fire("OnDragStart")
            assert(c.dragging and c.cover.moving)
            c.cover.StopMovingOrSizing=function() error("Injected drag cleanup failure") end
            ns.FA.SLASH.legacyui("off")
            local tree=LegacySystemFrame.TreePage
            local point,relative,relativePoint,x,y=tree:GetPoint(1)
            assert(not c.busy and not c.dragging and not c.restorePending and c.bridge==nil)
            assert(c.state=="Disabled" and not c.cover:IsShown() and not settings.legacyUI)
            assert(tree:IsVisible() and tree:GetParent()==LegacySystemFrame and tree:GetScale()==1)
            assert(tree:GetWidth()==920 and tree:GetHeight()==575)
            assert(point=="TOPLEFT" and relative==LegacySystemFrame and relativePoint=="TOPLEFT" and x==0 and y==0)
            assert(tree.Background:IsShown() and tree.VerticalDivider:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_throwing_bridge_restore_retains_pending_cover_and_allows_safe_retry(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[2]:Fire("OnClick")
            local bridge=c.bridge
            local originalRestore=bridge.Restore
            bridge.Restore=function() error("Injected restoration exception") end
            ns.FA.SLASH.legacyui("off")
            assert(not settings.legacyUI and not c.busy and c.restorePending)
            assert(c.bridge==bridge and c.cover:IsVisible())
            assert(c.state:find("Restoration pending") and c.state:find("Injected restoration exception"))
            assert(LegacySystemFrame.RewardTrackPage:IsVisible() and not LegacySystemFrame.NativeTabs:IsShown())
            bridge.Restore=originalRestore
            for _,frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_REGEN_ENABLED then frame:Fire("OnEvent","PLAYER_REGEN_ENABLED"); break end
            end
            local reward=LegacySystemFrame.RewardTrackPage
            assert(not c.busy and not c.restorePending and c.bridge==nil and not c.cover:IsShown())
            assert(c.state=="Disabled" and reward:IsVisible() and reward:GetParent()==LegacySystemFrame)
            assert(reward:GetScale()==1 and reward:GetWidth()==910 and reward:GetHeight()==569)
            assert(reward.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            assert(LegacySystemFrame:IsMouseEnabled() and saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_partial_mount_failure_restores_anchors_scale_and_native_access(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local reward=LegacySystemFrame.RewardTrackPage
            local original=reward.SetFrameLevel
            local failures=0
            reward.SetFrameLevel=function(self,value)
                if failures==0 then failures=failures+1; error("Injected late mount failure") end
                original(self,value)
            end
            c.ui.tabs[2]:Fire("OnClick")
            local point,relative,relativePoint,x,y=reward:GetPoint(1)
            assert(point=="TOPLEFT" and relative==LegacySystemFrame and x==7 and y==-5)
            assert(reward:GetScale()==1 and reward:GetFrameLevel()==100 and reward:GetParent()==LegacySystemFrame)
            assert(reward.Background:IsShown() and reward:IsVisible())
            assert(not c.cover:IsShown() and c.state:find("Fallback"))
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(reward.majorFactionData.renownLevel==16 and saved.done.first==1730000000 and #calls==0)
        ''')

    def test_disabled_native_selection_and_input_callbacks_leave_original_ui(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            ns.FA.SLASH.legacyui("off")
            EventRegistry:TriggerEvent("Legacy.SelectPage",3)
            ChangeInputMode(true); ChangeInputMode(false); FlushTimers()
            assert(not c.cover:IsShown() and LegacySystemFrame.TreePage:IsVisible())
            assert(LegacySystemFrame.TreePage:GetScale()==1 and LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame)
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled() and #calls==0)
        ''')

    def test_smaller_screen_and_changed_ui_scale_fit_visible_native_content(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            ns.FA.SLASH.legacyui("size large"); FlushTimers()
            c.ui.tabs[2]:Fire("OnClick")
            UIParent:SetSize(640,480); UIParent:SetScale(.75)
            UIParent:Fire("OnSizeChanged"); FlushTimers()
            assert(c.cover:GetScale()<1 and c.cover:IsVisible())
            assert(c.cover:GetWidth()*c.cover:GetScale()<=UIParent:GetWidth()-20+.01)
            assert(c.cover:GetHeight()*c.cover:GetScale()<=UIParent:GetHeight()-20+.01)
            assert(c.cover:GetWidth()==1024 and c.cover:GetHeight()==860)
            assert(c.ui.root:GetWidth()==1024 and c.ui.root:GetHeight()==720 and c.ui.root:GetScale()==1)
            local page=LegacySystemFrame.RewardTrackPage
            assert(page:GetWidth()*page:GetEffectiveScale()<=c.ui.nativeHost:GetWidth()*c.ui.nativeHost:GetEffectiveScale()+.01)
            assert(page:GetHeight()*page:GetEffectiveScale()<=c.ui.nativeHost:GetHeight()*c.ui.nativeHost:GetEffectiveScale()+.01)
            UIParent:SetSize(1920,1080); UIParent:SetScale(1)
            UIParent:Fire("OnSizeChanged"); FlushTimers()
            assert(c.cover:GetScale()==1 and c.ui.root:GetScale()==1 and settings.legacyUISize=="Large")
            ns.FA.SLASH.legacyui("off")
            assert(page:GetScale()==1 and page:GetParent()==LegacySystemFrame and #calls==0)
        ''')

    def test_preexisting_hidden_art_and_root_alpha_survive_restoration(self):
        self.check('''
            LegacySystemFrame.EdgeArt:Hide()
            LegacySystemFrame.TitleContainer:Hide()
            LegacySystemFrame.alpha=.73
            ns.FA.SLASH.legacyui("on")
            assert(LegacySystemFrame:GetAlpha()==.73)
            ns.FA.SLASH.legacyui("off")
            assert(not LegacySystemFrame.EdgeArt:IsShown() and not LegacySystemFrame.TitleContainer:IsShown())
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame:GetAlpha()==.73 and #calls==0)
        ''')

    def test_missing_native_frame_waits_without_loading_or_toggling_blizzard(self):
        self.check('''
            LegacySystemFrame=nil
            ns.FA.SLASH.legacyui("on")
            assert(settings.legacyUI and FAWrathLegacyCover==nil)
            assert(ns.LegacyUIController.state:find("Waiting"))
            SetupNative(); ns.LegacyUIController:Attach()
            assert(ns.LegacyUIController.state=="Enabled" and #calls==0)
        ''')

    def test_combat_defers_initialization_then_resumes(self):
        self.check('''
            inCombat=true; ns.FA.SLASH.legacyui("on")
            assert(FAWrathLegacyCover==nil and ns.LegacyUIController.pending)
            inCombat=false; ns.LegacyUIController:Attach()
            assert(ns.LegacyUIController.cover:IsVisible() and #calls==0)
        ''')

    def test_protected_native_page_falls_back_without_hooks(self):
        self.check('''
            LegacySystemFrame.protected=true
            ns.FA.SLASH.legacyui("on")
            assert(FAWrathLegacyCover==nil and ns.LegacyUIController.state:find("Fallback"))
            assert(next(LegacySystemFrame.ChallengesPage.hooks)==nil and #calls==0)
        ''')

    def test_render_failure_removes_cover_immediately(self):
        self.h.enable()
        self.check('''
            ns.LegacyUIController.ui.Render=function() error("Render failed") end
            ns.LegacyUIController:Refresh()
            assert(not ns.LegacyUIController.cover:IsShown())
            assert(ns.LegacyUIController.state:find("Fallback") and #calls==0)
        ''')

    def test_initialization_failure_keeps_native_scripts_and_content(self):
        self.check('''
            ns.WrathAchievementUI.Create=function() error("Unsupported template") end
            ns.FA.SLASH.legacyui("on")
            assert(not ns.LegacyUIController.cover:IsShown())
            local page=LegacySystemFrame.ChallengesPage
            assert(page:IsVisible() and page:GetScript("OnShow")==originalShow)
            assert(next(page.hooks)==nil and #calls==0)
            ns.FA.SLASH.legacyui("off")
            assert(settings.legacyUI==false)
        ''')

    def test_custom_refresh_uses_native_cache_until_native_event(self):
        self.h.enable()
        self.check('''
            local reads=0
            local original=GetCategoryList
            GetCategoryList=function() reads=reads+1; return original() end
            ns.LegacyUIController:Refresh()
            assert(reads==0)
            for _, frame in ipairs(frames) do
                if frame.events and frame.events.ACHIEVEMENT_EARNED then frame:Fire("OnEvent","ACHIEVEMENT_EARNED"); break end
            end
            FlushTimers()
            assert(reads==1)
        ''')

    def test_persisted_setting_enables_on_login(self):
        h = Harness()
        h.execute("SetupNative(); settings.legacyUI=true")
        h.load("Integrations/LegacyWindowBridge.lua")
        h.load("Integrations/LegacyController.lua")
        h.execute('''
            for _, frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_LOGIN then frame:Fire("OnEvent","PLAYER_LOGIN"); break end
            end
            assert(ns.LegacyUIController.state=="Enabled" and ns.LegacyUIController.cover:IsVisible())
        ''')

    def test_native_currency_event_refreshes_authoritative_header_without_payload_writes(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            assert(c.ui.nativePoints:GetText()=="16")
            C_MajorFactions.GetCurrentRenownLevel=function(id) assert(id==2802); return 21 end
            local payload={renownCurrency=999,quantity=12,sentinel="keep"}
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload)
            FlushTimers()
            assert(c.ui.nativePoints:GetText()=="21")
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="10")
            assert(payload.renownCurrency==999 and payload.quantity==12 and payload.sentinel=="keep")
            ns.FA.SLASH.legacyui("off")
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload)
            assert(#timers==0 and #calls==0)
        ''')

    def test_pending_refresh_is_coalesced_and_gated_when_disabled(self):
        self.h.enable()
        self.check('''
            ns.LegacyUIController:Schedule(); ns.LegacyUIController:Schedule()
            assert(#timers==1)
            ns.FA.SLASH.legacyui("off"); FlushTimers()
            assert(not ns.LegacyUIController.cover:IsShown() and #calls==0)
        ''')

    def test_real_templates_render_native_criteria_meta_and_custom_statistics(self):
        self.h.enable()
        self.check('''
            local ui=ns.LegacyUIController.ui
            ui.category="legacy"; ui.selected="legacy:62013"; ui:Render()
            local card
            for _, c in ipairs(ui.cards) do if c.record.key=="legacy:62013" then card=c end end
            assert(card.shield.points:GetText()=="1" and card.progressPool[1].maximum==225)
            assert(card.progressPool[1].value==0 and card.progressPool[1].text:GetText():find("0 / 225",1,true))
            ui.selected="legacy:62053"; ui:Render()
            for _, c in ipairs(ui.cards) do if c.record.key=="legacy:62053" then card=c end end
            ns.WrathAchievementUI.MetaClick(card.metaPool[1])
            assert(ui.focus.key=="legacy:62353" and #calls==0)
            saved.critters={}
            ui.tab="statistics"; ui.focus=nil; ui:Render()
            local critters
            for _,row in ipairs(ui.stats) do
                if row:IsShown() and not row.isHeader and row.record and row.record.key=="statistic:tracked:critters" then critters=row end
            end
            assert(critters and critters.value:GetText()=="0")
        ''')

    def test_large_catalog_uses_visible_card_pool_and_scrolls(self):
        self.h.enable()
        self.check('''
            local ui=ns.LegacyUIController.ui
            local m=ui.model
            m.records={}
            for i=1,1000 do
                m.records[i]={key="legacy:"..i,source="legacy",category="legacy-category:15607",
                    name="Challenge "..i,description="Read only",scope="Character",completed=false}
            end
            ui.category="legacy"; ui.selected=nil; ui:Render()
            assert(#ui.cards<12 and ui.contentChild.height>88000)
            ui.contentScroll:SetVerticalScroll(44000)
            assert(#ui.cards<12)
            local seen=false
            for _, c in ipairs(ui.cards) do if c.shown and c.record.key=="legacy:500" then seen=true end end
            assert(seen and #calls==0)
        ''')

    def test_native_missing_data_and_unknown_values_are_visible(self):
        self.check('''
            GetCategoryList=nil; C_MajorFactions.GetCurrentRenownLevel=nil
            LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.dataProvider=nil
            ns.FA.SLASH.legacyui("on")
            local ui=ns.LegacyUIController.ui
            assert(ui.notice:GetText():find("unavailable"))
            assert(ui.nativePoints:GetText()=="—")
            assert(ns.LegacyUIController.cover:IsVisible())
        ''')


class CoreIntegrationTests(unittest.TestCase):
    def core_harness(self):
        h = Harness()
        h.execute('''
            SlashCmdList={}; UISpecialFrames={}; tinsert=table.insert
            function GetTime() return 0 end
            function UnitLevel() return 1 end
            function UnitFactionGroup() return "Alliance" end
            function UnitName() return "Test","Character" end
            function GetRealmName() return "Fixture Realm" end
            function UnitGUID() return "Player-TEST" end
            C_Timer.NewTicker=function() return {} end
            ForeverAchievementsCharDB=saved
        ''')
        for name in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua",
                     "DataExtra.lua", "MoneyTracking.lua", "ForeverAchievements.lua", "Integrations/CustomAdapter.lua"):
            h.load(name)
        return h

    def test_real_definitions_keep_saved_keys_and_build_custom_criteria(self):
        h = self.core_harness()
        h.execute('''
            ForeverAchievementsCharDB.done.lvl10=1730000000
            local c=ns.CustomAchievementAdapter.Catalog()
            assert(#ns.FA.ALL==322 and #c.records>100)
            assert(c.byKey["custom:lvl10"].completed)
            assert(ForeverAchievementsCharDB.done.first==1730000000)
            assert(ForeverAchievementsCharDB.history[1]=="keep")
            for _, row in ipairs(c.records) do
                assert(not row.achievement.native)
                ns.CustomAchievementAdapter.Criteria(row)
            end
            assert(SLASH_FOREVERACHIEVEMENTS3=="/fa")
            assert(#calls==0)
        ''')

    def test_unsupported_daily_definitions_preserve_history_without_reading_progress(self):
        h=self.core_harness()
        h.execute('''
            local db=ns.FA.DB()
            db.done.d5=12345; db.done.request=54321; db.tracked.d5=true
            db.dailyLast=17; db.dailyDays={old=true}
            local dailyKeys={"d5","d50","d200","d500","d1000","request"}
            for _,key in ipairs(dailyKeys) do
                local definition=ns.FA.BY_KEY[key]
                assert(definition and definition.unsupported and not ns.FA.Available(definition))
                definition.progress=function() error("Unsupported daily progress must not be queried") end
            end
            GetStatistic=function(id) assert(id~=97); return nil end
            local catalog=ns.CustomAchievementAdapter.Catalog()
            for _,key in ipairs(dailyKeys) do assert(catalog.byKey["custom:"..key]==nil) end
            assert(#ns.FA.ALL==322 and db.done.d5==12345 and db.done.request==54321)
            assert(db.dailyLast==17 and db.dailyDays.old and db.tracked.d5)
            assert(db.history[1]=="keep" and db.done.first==1730000000 and #calls==0)
        ''')

    def test_quest_seam_distinguishes_missing_counts_zero_and_completed_ids(self):
        h=self.core_harness()
        h.execute('''
            local quests=ns.FA.QuestTracking
            GetStatistic=nil; C_QuestLog=nil; GetQuestsCompleted=nil
            assert(quests.Count()==nil and quests.CompletedIDs()==nil)
            local current,required=ns.FA.BY_KEY.q50.progress()
            assert(current==nil and required==50)
            local loreEK,loreKal=quests.LoremasterCounts()
            assert(loreEK==nil and loreKal==nil)
            current=ns.FA.BY_KEY.loreEK.progress(); assert(current==nil)
            GetStatistic=function(id) assert(id==98); return "0" end
            assert(quests.Count()==0)
            current=ns.FA.BY_KEY.q50.progress(); assert(current==0)
            C_QuestLog={GetAllCompletedQuestIDs=function() return {100,200,300} end}
            assert(quests.Count()==3 and #quests.CompletedIDs()==3)
            GetStatistic=function() return "75" end
            assert(quests.Count()==75)
            GetStatistic=nil
            C_QuestLog.GetAllCompletedQuestIDs=function() error("Client API unavailable") end
            GetQuestsCompleted=function(target) target[44]=true; target[55]=true end
            assert(quests.Count()==2 and #quests.CompletedIDs()==2)
            GetQuestsCompleted=function() error("Fallback unavailable") end
            assert(quests.Count()==nil and quests.CompletedIDs()==nil)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


class PackagingTests(unittest.TestCase):
    def test_original_reference_bytes_match_upload_manifest(self):
        folder = ROOT / "References/WrathAchievementUI"
        manifest = json.loads((folder / "SOURCE_HASHES.json").read_text())
        self.assertEqual(len(manifest), 5)
        for name, expected in manifest.items():
            data = (folder / name).read_bytes()
            self.assertEqual(len(data), expected["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected["sha256"])

    def test_runtime_templates_are_namespaced_and_do_not_load_native_backend(self):
        root = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        for element in root:
            self.assertTrue(element.get("name").startswith("FAWrath"))
            self.assertEqual(element.get("virtual"), "true")
        for element in root.iter():
            self.assertFalse(element.get("parent") == "UIParent")
            self.assertNotEqual(element.get("toplevel"), "true")
            if element.tag == URI + "Scripts":
                for callback in element:
                    self.assertIn("ForeverAchievementsWrathUI.", callback.text)
        toc = (ADDON / "ForeverAchievements.toc").read_text()
        self.assertNotIn("References", toc)
        self.assertLess(toc.index("UI\\WrathAchievementUI.lua"), toc.index("UI\\WrathAchievementUI.xml"))
        self.assertLess(toc.index("UI\\WrathAchievementUI.xml"), toc.index("Integrations\\LegacyController.lua"))

    def test_texture_files_and_coordinates_preserve_wrath_art_and_explicit_page_crops(self):
        original = ET.parse(ROOT / "References/WrathAchievementUI/Blizzard_AchievementUI.xml").getroot()
        adapted = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        original_files = {e.get("file") for e in original.iter() if e.get("file")}
        # A stock client search icon accompanies the new unified search field.
        original_files.add("Interface\\Common\\UI-Searchbox-Icon")
        # The neutral header seal uses the original backend's Feat shield art;
        # that file is selected in Wrath Lua rather than its XML templates.
        seal = "Interface\\AchievementFrame\\UI-Achievement-Shields-NoPoints"
        reference_lua = (ROOT / "References/WrathAchievementUI/Blizzard_AchievementUI.lua").read_text()
        self.assertIn(seal, reference_lua)
        original_files.add(seal)
        adapted_files = {e.get("file") for e in adapted.iter() if e.get("file")}
        self.assertTrue(adapted_files <= original_files)
        slices = {tuple(sorted(e.attrib.items())) for e in original.iter(URI + "TexCoords")}
        parents = {child: parent for parent in adapted.iter() for child in parent}
        for e in adapted.iter(URI + "TexCoords"):
            texture = parents[e]
            if texture.get("name") in ("$parentPageParchment", "$parentCategoriesBG"):
                # The shared parchment page replaces the original mismatched
                # panels. Runtime layout divides this exact crop at the seam;
                # independent shell tests verify matching U coordinates.
                self.assertEqual(texture.get("file"), "Interface\\AchievementFrame\\UI-Achievement-AchievementBackground")
                self.assertEqual(e.attrib, {"left": "0", "right": "1", "top": "0", "bottom": ".5"})
                continue
            # Iteration 6 splits each original plaque into fixed ends and a
            # widened center. Validate exact subregions, not arbitrary crops.
            name = texture.get("name", "")
            owner = parents.get(parents.get(parents.get(texture)))
            if owner is not None and owner.get('name') == '$parentHeader' and name in ('$parentLeft', '$parentRight', '$parentRoofLeft', '$parentRoofRight'):
                expected = {'$parentLeft': (77/512, 224/512, 147), '$parentRight': (224/512, 77/512, 147),
                            '$parentRoofLeft': (224/512, 440/512, 216), '$parentRoofRight': (440/512, 224/512, 216)}
                left, right, width = expected[name]
                self.assertEqual({k: float(v) for k, v in e.attrib.items()},
                                 {'left': left, 'right': right, 'top': 0, 'bottom': 106/256})
                size = texture.find(URI + 'Size/' + URI + 'AbsDimension')
                self.assertEqual((int(size.get('x')), int(size.get('y'))), (width, 106))
                continue
            if name.startswith(("$parentPointBorder", "$parentLegacyPointBorder")):
                left, right, width = (.455078125, .64453125, 116)
                if name.endswith("Left"):
                    left, right, width = (.419921875, .455078125, 18)
                elif name.endswith("Right"):
                    left, right, width = (.64453125, .6796875, 18)
                self.assertEqual(texture.get("file"), "Interface\\AchievementFrame\\UI-Achievement-Header")
                self.assertEqual({k: float(v) for k, v in e.attrib.items()},
                                 {"left": left, "right": right, "top": .4140625, "bottom": .56640625})
                size = texture.find(URI + "Size").find(URI + "AbsDimension")
                self.assertEqual((int(size.get("x")), int(size.get("y"))), (width, 39))
                continue
            # Forever's current shield sheet adds the guild row below the
            # original player row. This one compatibility crop is deliberate.
            if e.get("bottom") == ".5" and e.get("top") == "0" and e.get("right") == ".5":
                adjusted = dict(e.attrib); adjusted["bottom"] = "1"
                self.assertIn(tuple(sorted(adjusted.items())), slices)
            else:
                self.assertIn(tuple(sorted(e.attrib.items())), slices)


if __name__ == "__main__":
    unittest.main()
