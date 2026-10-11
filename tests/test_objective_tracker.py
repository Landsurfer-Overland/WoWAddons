"""Real watch/progress callbacks against the modern client module contract.

The explicit native double models registration, pooled blocks, scheduling,
collapse and height budgets. Rendering, live client taint and native fonts are
not emulated. No fake native achievement/quest IDs are registered by the addon.
"""
import unittest

from test_progression_addendum import CoreHarness


NATIVE = r'''
local K=ns.LAR.Kit
K.MakeFont=function(parent,size,flags,r,g,b,a)
    local f=parent:CreateFontString(nil,'OVERLAY'); f.font={'fixture',size or 12,flags or ''}
    if r then f:SetTextColor(r,g,b,a or 1) end
    return f
end
K.MakeBorder=function() return {} end
K.RealignBorders=function() end
tickers={}; C_Timer.NewTicker=function(_,fn) tickers[#tickers+1]=fn; return {} end
OBJECTIVE_DASH_STYLE_SHOW=1
registerCount,dirtyRequests,layoutCalls=0,0,0
ObjectiveTrackerFrame=UIObject('Frame','ObjectiveTrackerFrame',UIParent)
local container=ObjectiveTrackerFrame
container.modules={}; container.available=600
container.questMarker={nativeQuest=true,name='Keep the client quest list'}
container.modules[1]=container.questMarker
function container:AddModule(module)
    assert(not InCombatLockdown() and not self:IsProtected())
    for _,current in ipairs(self.modules) do if current==module then return end end
    self.modules[#self.modules+1]=module; module:SetContainer(self); self:MarkDirty()
end
function container:MarkDirty() assert(not InCombatLockdown()); dirtyRequests=dirtyRequests+1; self.pending=true end
function container:Flush()
    if not self.pending then return end
    self.pending=false
    for _,module in ipairs(self.modules) do
        if not module.nativeQuest then module:Update(self.available,true) end
    end
end
ObjectiveTrackerManager={containers={[container]=true}}
function ObjectiveTrackerManager:SetModuleContainer(module,parent)
    assert(not InCombatLockdown()); registerCount=registerCount+1; parent:AddModule(module)
end
AchievementObjectiveTracker={uiOrder=6}
ObjectiveTrackerModuleMixin={}
local M=ObjectiveTrackerModuleMixin
function M:SetHeader(text) self.Header.Text:SetText(text) end
function M:SetContainer(parent) self.parentContainer=parent; self:SetParent(parent) end
function M:MarkDirty() assert(not InCombatLockdown()); self.isDirty=true; self.parentContainer:MarkDirty() end
function M:GetContentsHeight() return self.contentsHeight or 0 end
function M:IsTruncated() return self.truncated==true end
function M:GetBlock(id)
    assert(not InCombatLockdown())
    local block=self.pool[id]
    if not block then
        block=UIObject('Button',nil,self); block.id=id; block.header=block:CreateFontString()
        block.line=block:CreateFontString()
        function block:SetHeader(text) self.header:SetText(text) end
        function block:AddObjective(key,text) assert(key=='progress'); self.line:SetText(text) end
        self.pool[id]=block
    end
    return block
end
function M:LayoutBlock(block)
    assert(not InCombatLockdown())
    if self.contentsHeight+34>self.availableHeight then self.truncated=true; return false end
    self.contentsHeight=self.contentsHeight+34; self.active[#self.active+1]=block
    if not self.collapsed then block:Show() end
    return true
end
function M:Update(height,dirty)
    assert(not InCombatLockdown()); layoutCalls=layoutCalls+1
    self.active={}; self.contentsHeight=25; self.availableHeight=height; self.truncated=false
    for _,block in pairs(self.pool) do block:Hide() end
    self:LayoutContents()
    if #self.active==0 then self.contentsHeight=0; self:Hide()
    elseif self.collapsed then self.contentsHeight=25; self:Show()
    else self:Show() end
    self.isDirty=false
    return self.contentsHeight,self.truncated
end
function BuildStockModule(frame)
    for key,value in pairs(M) do frame[key]=value end
    frame.pool={}; frame.contentsHeight=0
    frame.Header=UIObject('Frame',nil,frame); frame.Header.Text=frame.Header:CreateFontString()
    frame:Hide(); return frame
end
'''


class ObjectiveHarness(CoreHarness):
    def __init__(self):
        super().__init__()
        self.load('UI/OriginalUIPolicy.lua')
        self.execute(NATIVE)
        self.load('Integrations/ObjectiveTracker.lua')
        self.load('Tracker.lua')

    def create(self, kind, name=None, parent=None, template=None):
        if template == 'ObjectiveTrackerModuleTemplate':
            return self.g.BuildStockModule(self.g.UIObject(kind, name, parent))
        return super().create(kind, name, parent, template)


class ObjectiveTrackerTests(unittest.TestCase):
    def setUp(self):
        self.h = ObjectiveHarness()

    def check(self, code):
        self.h.execute(code)

    def test_watch_appears_in_native_module_without_floating_box_or_native_ids(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function(id) assert(id==98); return '130' end
            L.DB().tracked.q500=true
            L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            local m=T.module; local block=m.pool.q500
            assert(m:GetParent()==ObjectiveTrackerFrame and m.Header.Text:GetText()=='Reforged Achievements')
            assert(block:IsShown() and block.line:GetText()=='130/500')
            assert(not LegacyAchievementsReforgedTracker:IsShown())
            assert(registerCount==1 and #ObjectiveTrackerFrame.modules==2 and m.uiOrder==6.1)
            assert(ObjectiveTrackerFrame.modules[1]==ObjectiveTrackerFrame.questMarker and #calls==0)
            assert(L.DB().done.first==1730000000 and L.DB().history[1]=='keep' and L.DB().tracked.q500)
        ''')

    def test_progress_snapshot_shared_and_unchanged_poll_does_not_dirty_native_layout(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            local reads,value=0,'7'
            GetStatistic=function() reads=reads+1; return value end
            for _,key in ipairs({'q50','q100','q500'}) do L.DB().tracked[key]=true end
            L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            local count,dirty=#frames,dirtyRequests
            assert(reads==1)
            for i=1,10 do L.UpdateTracker(); ObjectiveTrackerFrame:Flush() end
            assert(reads==11 and #frames==count and dirtyRequests==dirty and registerCount==1)
            value='8'; tickers[1](); ObjectiveTrackerFrame:Flush()
            assert(reads==12 and dirtyRequests==dirty+1 and T.module.pool.q100.line:GetText()=='8/100')
            -- Native UI refreshes consume cached text, never the progress API.
            T.module:Update(600,false); assert(reads==12)
        ''')

    def test_unknown_zero_and_money_labels_preserve_authoritative_progress(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            local value=nil; GetStatistic=function() return value end
            L.DB().tracked.q50=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            assert(T.module.pool.q50.line:GetText()=='Unavailable')
            value='0'; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            assert(T.module.pool.q50.line:GetText()=='0/50')
            L.BY_KEY.q50.money=true; L.BY_KEY.q50.progress=function() return 25000,50000 end
            L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            assert(T.module.pool.q50.line:GetText()=='2/5g' and not L.DB().done.q50)
        ''')

    def test_untrack_and_empty_section_leave_quests_and_saves_intact(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function() return '7' end
            L.DB().tracked.q50=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            local m=T.module; m:OnBlockHeaderClick(m.pool.q50,'RightButton'); ObjectiveTrackerFrame:Flush()
            assert(not L.DB().tracked.q50 and #T.entries==0 and not m:IsShown())
            assert(not LegacyAchievementsReforgedTracker:IsShown() and not T:NeedsPolling())
            assert(ObjectiveTrackerFrame.modules[1]==ObjectiveTrackerFrame.questMarker and #calls==0)
            assert(L.DB().done.first==1730000000 and L.DB().history[1]=='keep')
        ''')

    def test_combat_defers_registration_and_refresh_once_then_uses_latest_progress(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            local value='7'; GetStatistic=function() return value end
            L.DB().tracked.q50=true; inCombat=true; local count=#frames
            L.UpdateTracker(); T.events:Fire('OnEvent','PLAYER_REGEN_ENABLED')
            assert(not T.module and registerCount==0 and #frames==count)
            inCombat=false; T.events:Fire('OnEvent','PLAYER_REGEN_ENABLED'); FlushTimers(); ObjectiveTrackerFrame:Flush()
            assert(registerCount==1 and T.module.pool.q50.line:GetText()=='7/50')
            inCombat=true; local dirty,layouts=dirtyRequests,layoutCalls
            value='8'; L.UpdateTracker(); T.module:Update(600,false); T:Layout(T.module)
            assert(dirtyRequests==dirty and layoutCalls==layouts and T.module.pool.q50.line:GetText()=='7/50')
            value='9'; L.UpdateTracker(); inCombat=false
            T.events:Fire('OnEvent','PLAYER_REGEN_ENABLED'); T.events:Fire('OnEvent','PLAYER_REGEN_ENABLED')
            local queued=#timers; assert(queued==1)
            FlushTimers(); ObjectiveTrackerFrame:Flush()
            assert(registerCount==1 and dirtyRequests==dirty+1 and T.module.pool.q50.line:GetText()=='9/50')
        ''')

    def test_native_collapse_and_height_budget_are_respected(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function() return '7' end
            L.DB().tracked.q50=true; L.DB().tracked.q100=true; L.UpdateTracker()
            ObjectiveTrackerFrame.available=60; ObjectiveTrackerFrame:Flush()
            assert(#T.module.active==1 and T.module:IsTruncated())
            T.module.collapsed=true; T.module:Update(600,false)
            assert(T.module:GetContentsHeight()==25 and not T.module.active[1]:IsShown())
            T.module.collapsed=false; T.module:Update(600,false)
            assert(#T.module.active==2 and T.module.active[2]:IsShown())
        ''')

    def test_show_setting_uses_native_module_and_never_clears_watch_selection(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function() return '7' end
            L.DB().tracked.q50=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            L.SLASH.tracker('off'); ObjectiveTrackerFrame:Flush()
            assert(#T.entries==0 and not T.module:IsShown() and L.DB().tracked.q50)
            L.SLASH.tracker('on'); ObjectiveTrackerFrame:Flush()
            assert(T.module:IsShown() and T.module.pool.q50.line:GetText()=='7/50')
            assert(registerCount==1 and #calls==0)
        ''')

    def test_late_native_initialization_retains_watches_without_floating_fallback(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function() return '7' end
            ObjectiveTrackerManager.containers={}; L.DB().tracked.q50=true; L.UpdateTracker()
            assert(not T.module and L.DB().tracked.q50 and not LegacyAchievementsReforgedTracker:IsShown())
            ObjectiveTrackerManager.containers[ObjectiveTrackerFrame]=true
            T.events:Fire('OnEvent','ADDON_LOADED','Blizzard_ObjectiveTracker')
            T.events:Fire('OnEvent','PLAYER_ENTERING_WORLD'); assert(#timers==1)
            FlushTimers(); ObjectiveTrackerFrame:Flush(); assert(T.module and registerCount==1)
        ''')

    def test_restricted_native_tracker_is_not_modified(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            L.DB().tracked.q50=true; local count=#frames
            ObjectiveTrackerFrame.protected=true; L.UpdateTracker()
            assert(not T.module and #frames==count and registerCount==0 and L.DB().tracked.q50)
            ObjectiveTrackerFrame.protected=false; ObjectiveTrackerFrame.forbidden=true; L.UpdateTracker()
            assert(not T.module and #frames==count and #calls==0)
        ''')

    def test_frame_managed_clients_register_using_verified_add_module_api(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            ObjectiveTrackerManager=nil; GetStatistic=function() return '7' end
            function ObjectiveTrackerModuleMixin:SetContainer(parent) self:SetParent(parent) end
            function ObjectiveTrackerModuleMixin:MarkDirty() self:GetParent():MarkDirty() end
            L.DB().tracked.q50=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            assert(T.module and T.module:GetParent()==ObjectiveTrackerFrame and #ObjectiveTrackerFrame.modules==2)
            assert(T.module.pool.q50.line:GetText()=='7/50' and #calls==0)
            L.UpdateTracker(); assert(#ObjectiveTrackerFrame.modules==2)
        ''')

    def test_header_click_defers_native_open_in_combat_and_focuses_owned_presentation(self):
        self.check('''
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            GetStatistic=function() return '7' end
            L.DB().tracked.q50=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            L.Settings().legacyUI=true
            local opened=0
            LegacySystemFrame=UIObject('Frame','LegacySystemFrame',UIParent)
            function LegacySystemFrame:ShowChallenges() assert(not InCombatLockdown()); opened=opened+1 end
            local searchBox=UIObject('EditBox',nil,UIParent); local scroll=UIObject('ScrollFrame',nil,UIParent)
            ns.LegacyUIController={ui={searchBox=searchBox,contentScroll=scroll}}
            function ns.LegacyUIController:PresentationAllowed() return true end
            function ns.LegacyUIController:Guard(fn) fn(); return true end
            function ns.LegacyUIController.ui:SetTab(tab) assert(tab=='achievements') end
            inCombat=true; T.module:OnBlockHeaderClick(T.module.pool.q50,'LeftButton')
            assert(opened==0 and T.openPending=='q50')
            inCombat=false; T.events:Fire('OnEvent','PLAYER_REGEN_ENABLED'); FlushTimers(); FlushTimers()
            assert(opened==1 and not T.openPending and searchBox:GetText()==L.BY_KEY.q50.name)
            assert(scroll:GetVerticalScroll()==0 and #calls==0)
        ''')

    def test_natural_completion_removes_watch_from_native_section(self):
        self.check('''
            SelectAchievements('lvl10'); CoreEvent('PLAYER_LOGIN'); FlushTimers()
            local L,T=ns.LAR,ns.ObjectiveTrackerIntegration
            L.DB().tracked.lvl10=true; L.UpdateTracker(); ObjectiveTrackerFrame:Flush()
            assert(T.module.pool.lvl10:IsShown())
            function UnitLevel() return 10 end
            CoreEvent('PLAYER_LEVEL_UP'); FlushTimers(); ObjectiveTrackerFrame:Flush()
            assert(L.DB().done.lvl10 and not L.DB().tracked.lvl10 and #T.entries==0)
            assert(not T.module:IsShown() and #calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
