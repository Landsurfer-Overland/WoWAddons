"""Actual standalone consumers keep unknown quest progress separate from zero.

Only Alpha UI styling and animation helpers are doubled. The achievement
definitions, standalone list/sort/card implementation, tracker and social
tooltip callbacks are executed from the addon source.
"""
import unittest

from test_legacy_wrath_ui import Harness


class ConsumerHarness(Harness):
    def __init__(self, original_ui=True):
        super().__init__()
        self.load("UI/OriginalUIPolicy.lua")
        # Archived UI regressions intentionally exercise the retained code.
        self.g.ns.OriginalUI.enabled = original_ui
        self.execute('''
            SlashCmdList={}; UISpecialFrames={}; tinsert=table.insert
            testClock=1
            function GetTime() return testClock end
            function UnitLevel() return 1 end
            function UnitFactionGroup() return "Alliance" end
            function UnitName() return "Test","Character" end
            function GetRealmName() return "Fixture Realm" end
            function UnitGUID() return "Player-TEST" end
            function IsShiftKeyDown() return false end
            function issecretvalue(value) return SecretTestProgress~=nil and value==SecretTestProgress end
            C_Timer.NewTicker=function() return {} end
            ForeverAchievementsCharDB=saved
            local originalUIObject=UIObject
            function UIObject(...)
                local f=originalUIObject(...)
                -- Ordinary frames do not own a numeric `.scroll` property;
                -- the standalone window uses that field for its ScrollFrame.
                f.scroll=nil
                f.verticalScroll=0
                function f:SetVerticalScroll(value)
                    self.verticalScroll=value
                    self:Fire("OnVerticalScroll",value)
                end
                function f:GetVerticalScroll() return self.verticalScroll end
                function f:SetFont(path,size,flags) self.font={path,size,flags} end
                function f:SetTextInsets(...) self.textInsets={...} end
                function f:RegisterForClicks(...) self.clickButtons={...} end
                function f:SetRotation(angle) self.rotation=angle end
                function f:SetDesaturated(value) self.desaturated=value end
                function f:CreateTexture(name,layer)
                    local texture=UIObject("Texture",name,self)
                    texture.layer=layer
                    return texture
                end
                return f
            end
        ''')
        for path in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua",
                     "DataExtra.lua", "MoneyTracking.lua", "ForeverAchievements.lua"):
            self.load(path)
        self.execute('''
            local Kit=ns.FA.Kit
            Kit.MakeFont=function(parent,size,flags,r,g,b,a)
                local font=parent:CreateFontString(nil,"OVERLAY")
                font:SetFont("test-font",size or 13,flags or "")
                if r then font:SetTextColor(r,g,b,a or 1) end
                return font
            end
            Kit.MakeBorder=function()
                return { SetColor=function(self,...) self.color={...} end }
            end
            Kit.Chrome=function() end
            Kit.RealignBorders=function() end
            Kit.Tween=function(_,_,step,done) step(1); if done then done() end end
            Kit.Dropdown=function(parent,width,options,order,getter,setter)
                local dropdown=CreateFrame("Button",nil,parent)
                dropdown:SetSize(width,26)
                dropdown.getter,dropdown.setter=getter,setter
                return dropdown
            end
            Kit.W.SectionHeader=function(_,parent,title,y)
                local header=CreateFrame("Frame",nil,parent)
                header:SetSize(600,30); header:SetPoint("TOPLEFT",20,y)
                return header,30
            end
            ns.FA.DB().tab="quests"
            ns.FA.Settings().sort="progress"
            ns.FA.CATEGORY_SECTIONS.quests={{title="QUEST PROGRESS",list={
                ns.FA.BY_KEY.q50,ns.FA.BY_KEY.loreEK,ns.FA.BY_KEY.d5,
            }}}
            function FindCard(key)
                for _,entry in ipairs(ForeverAchievementsWindow.placed or {}) do
                    if entry.key==key then return entry.frame end
                end
            end
            function CardHasText(card,text)
                for _,region in ipairs(card.regions) do
                    if region.kind=="FontString" and region:GetText()==text then return true end
                end
                return false
            end
            function CardHasFilledProgress(card)
                for _,region in ipairs(card.regions) do
                    if region.kind=="Texture" and region.layer=="OVERLAY" and region.height==2 and region:IsShown() then return true end
                end
                return false
            end
            function TrackerRow(key)
                for _,row in ipairs(ForeverAchievementsTracker.children) do
                    if row.a and row.a.key==key and row:IsVisible() then return row end
                end
            end
            ItemRefTooltip={lines={}}
            function ItemRefTooltip:SetOwner(owner) self.owner=owner end
            function ItemRefTooltip:ClearLines() self.lines={} end
            function ItemRefTooltip:AddLine(text) self.lines[#self.lines+1]=text end
            function ItemRefTooltip:Show() self.shown=true end
            function TooltipContains(text)
                for _,line in ipairs(ItemRefTooltip.lines) do if line==text then return true end end
                return false
            end
            function OpenAchievementLink(key)
                testClock=testClock+1
                EventRegistry:TriggerEvent("SetItemRef","addon:ForeverAchievements:"..key)
            end
        ''')


class UnknownProgressConsumerTests(unittest.TestCase):
    def setUp(self):
        self.h = ConsumerHarness()

    def test_tracker_tiers_share_reads_per_update_and_next_pass_is_fresh(self):
        self.h.load("Tracker.lua")
        self.h.execute('''
            local reads,value=0,"7"
            GetStatistic=function(id) assert(id==98); reads=reads+1; return value end
            local db=ns.FA.DB()
            for _,key in ipairs({"q50","q100","q500"}) do db.tracked[key]=true end
            ns.FA.UpdateTracker()
            assert(reads==1 and TrackerRow("q50").value:GetText()=="7/50")
            assert(TrackerRow("q100").value:GetText()=="7/100" and TrackerRow("q500").value:GetText()=="7/500")
            value="8"; ns.FA.UpdateTracker()
            assert(reads==2 and TrackerRow("q50").value:GetText()=="8/50")
            value=nil; ns.FA.UpdateTracker()
            assert(reads==3 and TrackerRow("q50").value:GetText()=="Unavailable")
            assert(TrackerRow("q100").value:GetText()=="Unavailable" and TrackerRow("q500").value:GetText()=="Unavailable")
            assert(db.tracked.q50 and db.tracked.q100 and db.tracked.q500)
            assert(db.done.first==1730000000 and db.history[1]=="keep" and #calls==0)
        ''')

    def test_tracker_snapshot_does_not_leak_after_progress_error(self):
        self.h.load("Tracker.lua")
        self.h.execute('''
            local reads,value=0,"7"
            GetStatistic=function(id) assert(id==98); reads=reads+1; return value end
            local a=ns.FA.BY_KEY.q50
            local progress=a.progress
            ns.FA.DB().tracked.q50=true
            a.progress=function() ns.FA.StatText(98); error("Injected progress failure") end
            local ok,reason=pcall(ns.FA.UpdateTracker)
            assert(not ok and reason:find("Injected progress failure") and reads==1)
            a.progress=progress; value="9"
            ns.FA.UpdateTracker()
            assert(reads==2 and TrackerRow("q50").value:GetText()=="9/50")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_real_quest_and_loremaster_unknowns_sort_and_render_without_filled_bars(self):
        self.h.execute('''
            GetStatistic=function() error("Statistics API unavailable") end
            C_QuestLog={GetAllCompletedQuestIDs=function() error("Quest API unavailable") end}
            GetQuestsCompleted=nil
            ns.FA.Open()
            for _,key in ipairs({"q50","loreEK"}) do
                local card=FindCard(key)
                assert(card and CardHasText(card,"Unavailable") and not CardHasFilledProgress(card))
            end
            assert(FindCard("d5")==nil and saved.done.first==1730000000)
            assert(saved.history[1]=="keep" and #calls==0)
        ''')

    def test_confirmed_zero_keeps_its_numeric_label_and_sorts_before_unknown(self):
        self.h.execute('''
            GetStatistic=function(id) assert(id==98); return "0" end
            C_QuestLog=nil; GetQuestsCompleted=nil
            ns.FA.Open()
            assert(CardHasText(FindCard("q50"),"0 / 50"))
            assert(CardHasText(FindCard("loreEK"),"Unavailable"))
            local keys={}
            for _,entry in ipairs(ForeverAchievementsWindow.placed) do if entry.key then keys[#keys+1]=entry.key end end
            assert(keys[1]=="q50" and keys[2]=="loreEK" and #calls==0)
        ''')

    def test_secret_progress_is_never_formatted_or_drawn_by_consumers(self):
        self.h.execute('''
            SecretTestProgress=setmetatable({}, {__tostring=function() error("Secret progress conversion") end})
            ns.FA.BY_KEY.q50.progress=function() return SecretTestProgress,50 end
            ns.FA.Open()
            assert(CardHasText(FindCard("q50"),"Unavailable") and not CardHasFilledProgress(FindCard("q50")))
            ns.FA.DB().tracked.q50=true
        ''')
        self.h.load("Tracker.lua")
        self.h.load("Social.lua")
        self.h.execute('''
            ns.FA.UpdateTracker()
            local row=TrackerRow("q50")
            assert(row and row.value:GetText()=="Unavailable" and not row.fill:IsShown())
            OpenAchievementLink("q50")
            assert(TooltipContains("Your progress: Unavailable") and #calls==0)
        ''')

    def test_tracker_pool_distinguishes_unknown_and_zero_and_retains_inactive_keys(self):
        self.h.execute('''
            GetStatistic=nil; C_QuestLog=nil; GetQuestsCompleted=nil
            local db=ns.FA.DB()
            db.tracked.q50=true; db.tracked.loreEK=true; db.tracked.d5=true; db.tracked.d50=true
            db.done.d5=112233
            for _,key in ipairs({"d5","d50"}) do
                ns.FA.BY_KEY[key].progress=function() error("Inactive daily progress was polled") end
            end
        ''')
        self.h.load("Tracker.lua")
        self.h.execute('''
            ns.FA.UpdateTracker()
            local row=TrackerRow("q50")
            assert(row and row.value:GetText()=="Unavailable" and not row.fill:IsShown())
            assert(TrackerRow("loreEK").value:GetText()=="Unavailable")
            assert(TrackerRow("d5")==nil and TrackerRow("d50")==nil)
            assert(saved.tracked.d5 and saved.tracked.d50 and saved.done.d5==112233)
            GetStatistic=function() return "0" end
            ns.FA.UpdateTracker()
            row=TrackerRow("q50")
            assert(row.value:GetText()=="0/50" and row.fill:IsShown())
            GetStatistic=nil
            ns.FA.UpdateTracker()
            assert(row.value:GetText()=="Unavailable" and not row.fill:IsShown())
            assert(saved.tracked.d5 and saved.tracked.d50 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_social_tooltip_preserves_unknown_quest_loremaster_and_confirmed_zero(self):
        self.h.load("Social.lua")
        self.h.execute('''
            GetStatistic=function() error("Statistic unavailable") end
            C_QuestLog=nil; GetQuestsCompleted=nil
            OpenAchievementLink("q50")
            assert(TooltipContains("Your progress: Unavailable"))
            OpenAchievementLink("loreEK")
            assert(TooltipContains("Your progress: Unavailable"))
            GetStatistic=function() return "0" end
            OpenAchievementLink("q50")
            assert(TooltipContains("Your progress: 0 / 50"))
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
