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
    local f = { kind=kind, name=name, parent=parent, children={}, scripts={}, hooks={},
        shown=true, width=100, height=24, level=1, scroll=0, textValue="" }
    if name then _G[name] = f end
    if parent and parent.children then table.insert(parent.children, f) end
    frames[#frames+1] = f
    function f:GetName() return self.name end
    function f:GetParent() return self.parent end
    function f:GetChildren() return unpack(self.children) end
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
    function f:SetSize(w,h) self.width=w; self.height=h end
    function f:SetWidth(w) self.width=w end
    function f:SetHeight(h) self.height=h end
    function f:GetWidth() return self.width end
    function f:GetHeight() return self.height end
    function f:SetText(t) self.textValue=tostring(t or ""); if type(self.text)=="table" then self.text:SetText(t) end end
    function f:GetText() return self.textValue end
    function f:GetStringHeight() return math.max(12, math.ceil(#self.textValue / math.max(1,self.width/6)) * 12) end
    function f:SetTextColor(...) self.color={...} end
    function f:SetVertexColor(...) self.color={...} end
    function f:SetTexCoord(...) self.coords={...} end
    function f:SetTexture(t) self.textureValue=t end
    function f:SetColorTexture(...) self.colorTexture={...} end
    function f:SetPoint(...) self.points=self.points or {}; table.insert(self.points,{...}) end
    function f:ClearAllPoints() self.points={} end
    function f:SetAllPoints(relative) self.allPoints=relative or self.parent end
    function f:SetParent(p) self.parent=p end
    function f:SetScale(v) self.scale=v end
    function f:SetFrameLevel(v) self.level=v end
    function f:SetFrameStrata(v) self.strata=v end
    function f:SetBackdrop(v) self.backdrop=v end
    function f:SetBackdropBorderColor(...) self.borderColor={...} end
    function f:SetStatusBarColor(...) self.barColor={...} end
    function f:SetMinMaxValues(a,b) self.minimum=a; self.maximum=b end
    function f:SetValue(v) self.value=v end
    function f:GetStatusBarTexture() if not self.barTexture then self.barTexture=UIObject("Texture",nil,self) end; return self.barTexture end
    function f:SetDrawLayer(v) self.layer=v end
    function f:SetScrollChild(v) self.scrollChild=v end
    function f:SetVerticalScroll(v) self.scroll=v; self:Fire("OnVerticalScroll",v) end
    function f:GetVerticalScroll() return self.scroll end
    function f:UpdateScrollChildRect() end
    function f:EnableMouse(v) self.mouse=v end
    function f:EnableMouseWheel(v) self.wheel=v end
    function f:SetClipsChildren(v) self.clips=v end
    function f:SetChecked(v) self.checked=v end
    function f:GetChecked() return self.checked end
    function f:RegisterEvent(v) self.events=self.events or {}; self.events[v]=true end
    function f:RegisterUnitEvent(v) self:RegisterEvent(v) end
    function f:SetAutoFocus(v) self.autoFocus=v end
    function f:SetMaxLetters(v) self.maxLetters=v end
    function f:ClearFocus() self.focused=false end
    function f:SetJustifyH(v) self.justify=v end
    function f:SetWordWrap(v) self.wordWrap=v end
    function f:SetShadowOffset(...) self.shadow={...} end
    function f:CreateTexture(name) return UIObject("Texture",name,self) end
    function f:CreateFontString(name) return UIObject("FontString",name,self) end
    return f
end
function NativeFrame(name, parent)
    local f = UIObject("Frame",name,parent)
    f.native=true
    for _, method in ipairs({"SetScript","SetParent","SetPoint","ClearAllPoints","SetAllPoints","SetScale","SetFrameLevel",
        "EnableMouse","EnableMouseWheel","SetAlpha","SetFrameStrata","SetDataProvider","SelectCategory","SelectChallenge","GenerateDataProvider","ClaimReward"}) do
        f[method]=poison(name .. ":" .. method)
    end
    return f
end
function SetupNative()
    LegacySystemFrame = NativeFrame("LegacySystemFrame",nil)
    LegacySystemFrame.strata="DIALOG"
    LegacySystemFrame.currentPage=2
    local page=NativeFrame("ChallengesPage",LegacySystemFrame)
    page.width=900; page.height=560
    LegacySystemFrame.ChallengesPage=page
    page.DetailPane=NativeFrame("DetailPane",page)
    page.DetailPane.ScrollBox=NativeFrame("ScrollBox",page.DetailPane)
    page.DetailPane.ScrollBox.level=40
    page.DetailPane.ScrollBox.dataProvider={collection={{achievementID=62013}}}
    local reward=NativeFrame("RewardTrackPage",LegacySystemFrame)
    reward.majorFactionData={factionID=2802,renownLevel=16}
    LegacySystemFrame.RewardTrackPage=reward
    LegacySystemFrame.TreePage=NativeFrame("TreePage",LegacySystemFrame)
    nativeShows=0
    page.scripts.OnShow=function() nativeShows=nativeShows+1 end
    originalShow=page.scripts.OnShow
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
        for path in ("Integrations/LegacyAdapter.lua", "Integrations/CustomAdapter.lua",
                     "Integrations/Presentation.lua", "UI/WrathAchievementUI.lua"):
            self.load(path)
        if controller:
            self.g.SetupNative()
            self.load("Integrations/LegacyController.lua")

    def load(self, path):
        fn = self.lua.execute("return assert(loadstring(...))", (ADDON / path).read_text(), "@" + path)
        fn("ForeverAchievements", self.g.ns)

    def create(self, kind, name=None, parent=None, template=None):
        f = self.g.UIObject(kind, name, parent)
        if template in self.templates:
            self.build(f, self.templates[template])
        elif template not in (None, "BackdropTemplate", "InputBoxTemplate", "UIPanelScrollFrameTemplate"):
            raise AssertionError("Unadapted dependency: " + template)
        return f

    def build(self, f, element):
        inherit = element.get("inherits")
        if inherit in self.templates:
            self.build(f, self.templates[inherit])
        elif inherit and inherit != "BackdropTemplate":
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

    def test_runtime_catalog_avoids_mirrored_ids_and_handles_parent_after_child(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62382"] and not m.byKey["legacy:64015"])
            assert(m.byCategory["legacy-category:15587"].parent=="legacy-category:15596")
            assert(#m.byCategory["legacy-category:15596"].children==1)
            assert(#ns.LegacyPresentation.Rows(m,"legacy-category:15596")==2)
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

    def test_enable_attaches_fits_and_consumes_clicks_inside_challenges(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            assert(c.state=="Enabled", c.state)
            assert(c.cover.parent==LegacySystemFrame.ChallengesPage and c.cover.mouse and c.cover.wheel and c.cover.clips)
            assert(c.cover.level>40 and c.cover:IsVisible() and c.cover:GetFrameStrata()=="DIALOG")
            assert(c.ui.root.parent==c.cover and c.ui.root.scale==math.min(900/768,560/640))
            assert(#calls==0)
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
            assert(page.parent==LegacySystemFrame and page.width==900 and reward.renownLevel==16)
            page:Fire("OnShow")
            assert(nativeShows==1 and not ns.LegacyUIController.cover:IsShown() and #calls==0)
        ''')

    def test_native_pages_and_reopening_hide_and_restore_cover(self):
        self.h.enable()
        self.check('''
            local page=LegacySystemFrame.ChallengesPage
            LegacySystemFrame.currentPage=1; page:Hide()
            assert(not ns.LegacyUIController.cover:IsShown())
            LegacySystemFrame.currentPage=3; ns.LegacyUIController:Refresh()
            assert(not ns.LegacyUIController.cover:IsShown())
            LegacySystemFrame.currentPage=2; page:Show()
            assert(ns.LegacyUIController.cover:IsVisible())
            local level=ns.LegacyUIController.cover.level
            LegacySystemFrame:Hide(); LegacySystemFrame:Show()
            assert(ns.LegacyUIController.cover:IsVisible() and ns.LegacyUIController.cover.level==level)
            assert(page:GetScript("OnShow")==originalShow and #calls==0)
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
            LegacySystemFrame.ChallengesPage.protected=true
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
        h.load("Integrations/LegacyController.lua")
        h.execute('''
            for _, frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_LOGIN then frame:Fire("OnEvent","PLAYER_LOGIN"); break end
            end
            assert(ns.LegacyUIController.state=="Enabled" and ns.LegacyUIController.cover:IsVisible())
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
            ui.tab="statistics"; ui.focus=nil; ui:Render()
            assert(#ui.stats>=8 and ui.stats[1].value:GetText()=="0")
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
            assert(ui.nativePoints:GetText():find("Unavailable"))
            assert(ns.LegacyUIController.cover:IsVisible())
        ''')


class CoreIntegrationTests(unittest.TestCase):
    def test_real_definitions_keep_saved_keys_and_build_custom_criteria(self):
        h = Harness()
        h.execute('''
            SlashCmdList={}; UISpecialFrames={}; tinsert=table.insert
            function GetTime() return 0 end
            function UnitLevel() return 1 end
            function UnitFactionGroup() return "Alliance" end
            C_Timer.NewTicker=function() return {} end
            ForeverAchievementsCharDB=saved
        ''')
        for name in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua",
                     "DataExtra.lua", "ForeverAchievements.lua", "Integrations/CustomAdapter.lua"):
            h.load(name)
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

    def test_texture_files_and_coordinates_come_from_wrath_source(self):
        original = ET.parse(ROOT / "References/WrathAchievementUI/Blizzard_AchievementUI.xml").getroot()
        adapted = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        original_files = {e.get("file") for e in original.iter() if e.get("file")}
        adapted_files = {e.get("file") for e in adapted.iter() if e.get("file")}
        self.assertTrue(adapted_files <= original_files)
        slices = {tuple(sorted(e.attrib.items())) for e in original.iter(URI + "TexCoords")}
        for e in adapted.iter(URI + "TexCoords"):
            self.assertIn(tuple(sorted(e.attrib.items())), slices)


if __name__ == "__main__":
    unittest.main()
