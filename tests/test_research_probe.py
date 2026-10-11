#!/usr/bin/env python3
"""Read-only diagnostic contracts; not evidence of Forever API support."""
from pathlib import Path
import unittest

from lupa.lua51 import LuaRuntime


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/research/LARResearchProbe/LARResearchProbe.lua"

BASE = r'''
SlashCmdList = {}
frames, messages, prohibited = {}, {}, {}
inCombat = false
function InCombatLockdown() return inCombat end
function GetBuildInfo() return "1.60.1", "70338", "Oct 9 2026", 16001 end
function UnitName(unit) assert(unit=="player"); return "Researcher" end
function GetRealmName() return "TestRealm" end
function UnitLevel() return 60 end
function UnitClass() return "Mage", "MAGE" end
function UnitFactionGroup() return "Alliance" end
function UnitRace() return "Human", "Human" end
DEFAULT_CHAT_FRAME = { AddMessage=function(self,text) messages[#messages+1]=text end }
UIParent = { IsForbidden=function() return false end }
LegacyAchievementsReforgedDB = { marker="untouched", settings={ legacyUIEnabled=true } }
LegacyAchievementsReforgedCharDB = { earned={old=123}, tracking={old=true} }

local function forbid(name)
    return function() prohibited[#prohibited+1]=name; error("forbidden "..name) end
end
SetCVar=forbid("SetCVar")
LoadAddOn=forbid("LoadAddOn")
hooksecurefunc=forbid("hooksecurefunc")
GetQuestsCompleted=forbid("whole quest scan")
C_QuestLog={GetAllCompletedQuestIDs=forbid("whole quest scan")}
C_MountJournal={GetMountIDs=forbid("account collection")}
C_PetJournal={GetNumPets=forbid("account collection")}
C_Timer={After=forbid("timer"),NewTicker=forbid("ticker")}
ns={LAR={Award=forbid("award"),Evaluate=forbid("progress evaluator"),DB=forbid("DB")}}
LegacySystemFrame={Show=forbid("native show"),Hide=forbid("native hide"),SetPoint=forbid("native layout"),SetParent=forbid("native parenting")}

function CreateFrame(kind, name, parent, template)
    assert(not inCombat,"frame creation during combat")
    local f={ kind=kind,name=name,parent=parent,template=template,scripts={},text="",mutations=0 }
    frames[#frames+1]=f
    function f:IsProtected() return self.protected or false end
    function f:IsForbidden() return self.forbidden or false end
    local function mutate(self) assert(not inCombat,"UI mutation during combat"); self.mutations=self.mutations+1 end
    for _,method in ipairs({"SetSize","SetPoint","SetWidth","SetHeight","SetMultiLine","SetAutoFocus","SetFontObject","SetMaxLetters","HighlightText","SetFocus","ClearFocus","SetFrameStrata","SetAllPoints","SetColorTexture","SetVerticalScroll","UpdateScrollChildRect","SetClampedToScreen","EnableMouse"}) do
        f[method]=mutate
    end
    function f:SetText(text) mutate(self); self.text=text end
    function f:Show() mutate(self); self.shown=true end
    function f:Hide() mutate(self); self.shown=false end
    function f:SetScript(event,func) mutate(self); self.scripts[event]=func end
    function f:SetScrollChild(child) mutate(self); self.child=child end
    function f:CreateTexture() return self end
    function f:CreateFontString() return {SetPoint=function() end,SetText=function() end} end
    return f
end
function Run(command) SlashCmdList.LARRESEARCHPROBE(command) end
function Report() return frames[1] and frames[1].edit.text or "" end
'''


class ResearchProbeTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(BASE)
        self.lua.execute(PROBE.read_text(encoding="utf-8"))

    def check(self, code):
        self.lua.execute(code)

    def test_load_has_no_queries_frames_hooks_events_or_saved_state_changes(self):
        self.check('''
            assert(#frames==0 and #messages==0 and #prohibited==0)
            assert(SLASH_LARRESEARCHPROBE1=="/larprobe")
            Run("build")
            assert(Report():find('GetBuildInfo.return[2] = "70338"',1,true))
            assert(Report():find('UnitLevel(player).return[1] = 60',1,true))
            assert(Report():find('GetStatistic = UNAVAILABLE',1,true))
            assert(#frames==4 and #prohibited==0)
            assert(LegacyAchievementsReforgedDB.marker=="untouched")
            assert(LegacyAchievementsReforgedDB.settings.legacyUIEnabled==true)
            assert(LegacyAchievementsReforgedCharDB.earned.old==123)
            assert(LegacyAchievementsReforgedCharDB.tracking.old==true)
            for _,frame in ipairs(frames) do assert(not frame.scripts.OnUpdate and not frame.scripts.OnEvent) end
        ''')

    def test_stat_retains_raw_units_and_zero_and_queries_only_explicit_id(self):
        self.check(r'''
            local reads=0
            GetStatistic=function(id) assert(id==1456); reads=reads+1; return "1,234 fish |Tcoin:0|t" end
            GetAchievementInfo=function(id) assert(id==1456); return id,"Fish and other things caught",0,true,nil,nil,nil,"Description",131072,123,"",false,false end
            ACHIEVEMENT_FLAGS_ACCOUNT=131072
            Run("stat 1456")
            assert(reads==1 and Report():find('1,234 fish |Tcoin:0|t',1,true))
            assert(Report():find('GetAchievementInfo(1456).return[13] = false',1,true))
            assert(Report():find('Account completion alone is not character proof',1,true))
            assert(Report():find('ACHIEVEMENT_FLAGS_ACCOUNT = 131072',1,true))
            GetStatistic=function(id) assert(id==353); return "0" end
            GetAchievementInfo=nil
            Run("stat 353")
            assert(Report():find('GetStatistic(353).return[1] = "0"',1,true))
            assert(Report():find('UNAVAILABLE (function absent)',1,true))
            assert(#frames==4 and #prohibited==0)
        ''')

    def test_unknown_error_false_and_zero_are_not_conflated(self):
        self.check('''
            C_QuestLog.IsQuestFlaggedCompleted=function(id) assert(id==123); return false end
            Run("quest 123")
            assert(Report():find('return[1] = false',1,true))
            C_QuestLog.IsQuestFlaggedCompleted=function() return nil end
            Run("quest 123")
            assert(Report():find('<nil / unknown>',1,true))
            C_QuestLog.IsQuestFlaggedCompleted=function() error("not ready") end
            Run("quest 123")
            assert(Report():find('ERROR',1,true) and Report():find('not ready',1,true))
            C_QuestLog.IsQuestFlaggedCompleted=nil
            IsQuestFlaggedCompleted=function(id) assert(id==123); return true end
            Run("quest 123")
            assert(Report():find('IsQuestFlaggedCompleted(123).return[1] = true',1,true))
            assert(#prohibited==0)
        ''')

    def test_achievement_criteria_are_bounded_and_never_follow_links(self):
        self.check('''
            local reads=0
            GetAchievementInfo=function(id) assert(id==62053); return id,"Explore Azeroth",0,false,nil,nil,nil,"Explore",0,237388,"",false,false end
            GetAchievementNumCriteria=function(id) assert(id==62053); return 100000 end
            GetAchievementCriteriaInfo=function(id,index)
                assert(id==62053 and index<=20); reads=reads+1
                return "Linked record",8,false,0,1,nil,0,62353,"0 / 1",index
            end
            Run("achievement 62053")
            assert(reads==20)
            assert(Report():find('Criteria truncated: first 20 of 100000',1,true))
            assert(Report():find('GetAchievementInfo(62053).return[4] = false',1,true))
            assert(Report():find('GetAchievementCriteriaInfo(62053,20)',1,true))
            assert(#prohibited==0)
        ''')

    def test_invalid_or_unavailable_criteria_count_never_starts_a_scan(self):
        self.check('''
            local reads=0
            GetAchievementCriteriaInfo=function() reads=reads+1; error("must not query") end
            for _,result in ipairs({-1,1.5,"10"}) do
                GetAchievementNumCriteria=function() return result end
                Run("achievement 64015")
                assert(Report():find('Criteria count unknown',1,true))
            end
            GetAchievementNumCriteria=function() error("not ready") end
            Run("achievement 64015")
            assert(reads==0 and Report():find('ERROR',1,true))
        ''')

    def test_secret_values_are_not_stringified_or_used_as_scan_counts(self):
        self.check('''
            local hidden=setmetatable({}, {__tostring=function() error("secret leaked") end})
            issecretvalue=function(value) return value==hidden end
            GetStatistic=function() return hidden end
            Run("stat 353")
            assert(Report():find('<restricted>',1,true))
            GetAchievementNumCriteria=function() return hidden end
            GetAchievementCriteriaInfo=function() error("secret scan") end
            Run("achievement 62382")
            assert(Report():find('Criteria count unknown',1,true))
            assert(#messages==0)
        ''')

    def test_reputation_currency_and_recipe_reads_expose_scope_limits(self):
        self.check('''
            C_Reputation={GetFactionDataByID=function(id) assert(id==2586); return {name="Azeroth Commerce Authority",currentStanding=6000} end}
            GetFactionInfoByID=function(id) assert(id==2586); error("legacy unavailable") end
            Run("reputation 2586")
            assert(Report():find('currentStanding',1,true) and Report():find('6000',1,true))
            assert(Report():find('ERROR',1,true) and Report():find('Current standing is not best-ever standing',1,true))
            C_CurrencyInfo={GetCurrencyInfo=function(id) assert(id==3402); return {quantity=0,isAccountWide=true,totalEarned=45} end}
            Run("currency 3402")
            assert(Report():find('quantity',1,true) and Report():find('Matching-build API documented',1,true))
            assert(Report():find('Held balance is not lifetime earned/spent',1,true))
            C_TradeSkillUI={GetRecipeInfo=function(id) assert(id==123); return {learned=false,name="Unlearned"} end}
            Run("recipe 123")
            assert(Report():find('learned',1,true) and Report():find('false',1,true))
            assert(Report():find('another player',1,true) and Report():find('No character ownership',1,true))
            assert(#prohibited==0)
        ''')

    def test_profession_fallback_is_bounded_and_nil_slots_remain_unknown(self):
        self.check('''
            local reads=0
            GetProfessions=function() return 5,nil,7,false,5,9,99 end
            GetProfessionInfo=function(index)
                assert(index==5 or index==7 or index==9)
                reads=reads+1
                if index==7 then return nil end
                return "Alchemy",123,225,300,nil,nil,171
            end
            Run("skills")
            assert(reads==3)
            assert(Report():find('GetProfessions.return[2] = <nil / unknown>',1,true))
            assert(Report():find('Profession slot 2 = unknown',1,true))
            assert(Report():find('Profession slot 5 = unknown, invalid, or duplicate',1,true))
            assert(Report():find('GetProfessionInfo(7) [slot 3].return[1] = <nil / unknown>',1,true))
            GetProfessions=function() error("not ready") end
            Run("skills")
            assert(reads==3 and Report():find('ERROR',1,true))
            assert(#prohibited==0)
        ''')

    def test_totems_read_exactly_four_slots_and_keep_unknown_distinct(self):
        self.check('''
            local slots={}
            MAX_TOTEMS=4
            FIRE_TOTEM_SLOT=1; EARTH_TOTEM_SLOT=2; WATER_TOTEM_SLOT=3; AIR_TOTEM_SLOT=4
            GetTotemInfo=function(slot)
                assert(slot>=1 and slot<=4); slots[#slots+1]=slot
                if slot==1 then return true,"Fire",1,120,123,1,99 end
                if slot==2 then return false,"",0,0 end
                if slot==3 then return nil end
                error("slot restricted")
            end
            Run("totems")
            assert(#slots==4 and slots[1]==1 and slots[4]==4)
            assert(Report():find('FIRE_TOTEM_SLOT = 1',1,true) and Report():find('AIR_TOTEM_SLOT = 4',1,true))
            assert(Report():find('GetTotemInfo(1).return[1] = true',1,true))
            assert(Report():find('GetTotemInfo(2).return[1] = false',1,true))
            assert(Report():find('GetTotemInfo(3).return[1] = <nil / unknown>',1,true))
            assert(Report():find('GetTotemInfo(4) = ERROR',1,true))
            assert(Report():find('No historical casts',1,true) and #prohibited==0)
        ''')

    def test_skills_only_first_twenty_and_bind_only_current_location(self):
        self.check('''
            local reads=0
            GetNumSkillLines=function() return 500 end
            GetSkillLineInfo=function(index) assert(index<=20); reads=reads+1; return "Alchemy",false,nil,225 end
            Run("skills")
            assert(reads==20 and Report():find('Only first 20 skill rows',1,true))
            GetBindLocation=function() return "Goldshire" end
            Run("bind")
            assert(Report():find('Goldshire',1,true) and Report():find('no prior inns',1,true))
            assert(reads==20 and #prohibited==0)
        ''')

    def test_combat_retains_report_without_ui_creation_or_retry(self):
        self.check('''
            inCombat=true
            GetStatistic=function() return "123" end
            Run("stat 353")
            Run("copy")
            assert(#frames==0 and #prohibited==0)
            assert(messages[#messages]:find('no UI operation attempted',1,true))
            inCombat=false
            assert(#frames==0) -- no automatic event/timer retry
            Run("copy")
            assert(#frames==4 and Report():find('GetStatistic(353).return[1] = "123"',1,true))
            local mutations=frames[1].mutations+frames[4].mutations
            inCombat=true
            Run("bind")
            assert(#frames==4 and mutations==frames[1].mutations+frames[4].mutations)
            assert(#prohibited==0)
        ''')

    def test_invalid_requests_do_not_query_ids_or_create_frames(self):
        self.check('''
            GetStatistic=function() error("invalid request queried") end
            for _,request in ipairs({"stat 0","stat -1","stat 353 349","stat 3.5","stat 9999999999","achievement nan","unknown"}) do Run(request) end
            assert(#frames==0 and #messages==7 and #prohibited==0)
            Run("copy")
            assert(messages[#messages]:find('No report yet',1,true))
        ''')


if __name__ == "__main__":
    unittest.main()
