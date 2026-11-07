"""Build-70862 evidence and refresh regressions against the actual core."""
import unittest

from test_progression_addendum import CoreHarness


class ClientAPIEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.load("Integrations/AchievementEvidence.lua")
        self.h.execute('''
            nativeRecords={}
            GetStatistic=function() return nil end
            GetAchievementInfo=function(id)
                local a=nativeRecords[id]
                if a then return id,a.name,0,a.completed,false,false,false,"Native objective",a.flags,1,nil,false,a.mine end
            end
            GetAchievementNumCriteria=function(id)
                local a=nativeRecords[id]; return a and #a.criteria or 0
            end
            GetAchievementCriteriaInfo=function(id,index) return unpack(nativeRecords[id].criteria[index]) end
            function Spelunker(name,done,flags,mine)
                nativeRecords[62031]={name="Novice Spelunker",completed=false,flags=flags or 0,mine=mine,
                    criteria={{name,0,done,done and 1 or 0,1,"",0,0,"",111111}}}
                return nativeRecords[62031]
            end
        ''')

    def check(self, code):
        self.h.execute(code)
        self.h.execute('assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)')

    def test_hall_of_thanes_native_criterion_backfills_without_kill_statistic(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            Spelunker("Hall of Thanes",true)
            local current,needed=ns.LAR.BY_KEY.dungeonThanes.progress()
            assert(current==1 and needed==1 and saved.done.dungeonThanes==nil)
            ns.LAR.CheckAll(true)
            assert(saved.done.dungeonThanes and saved.bosses["Durgen Dirgehammer"]==nil)
        ''')

    def test_partial_criteria_events_refresh_custom_awards_and_coalesce(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local a=Spelunker("Hall of Thanes",false)
            CoreEvent("CRITERIA_UPDATE"); CoreEvent("CRITERIA_COMPLETE",111111)
            CoreEvent("CRITERIA_EARNED",62031); CoreEvent("ACHIEVEMENT_EARNED",62031)
            assert(#timers==1 and saved.done.dungeonThanes==nil)
            a.criteria[1][3]=true
            FlushTimers()
            assert(saved.done.dungeonThanes and not a.completed)
        ''')

    def test_wrong_native_identity_incomplete_and_unrelated_criteria_do_not_award(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local a=Spelunker("Hall of Thanes",false)
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.criteria[1][3]=true; a.name="Reused unrelated ID"
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.name="Novice Spelunker"; a.criteria[1][1]="Ruins of Lordaeron"
            a.completed=true; a.mine=true
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
        ''')

    def test_other_character_and_ambiguous_account_completion_do_not_award(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local a=Spelunker("Hall of Thanes",true,ACHIEVEMENT_FLAGS_ACCOUNT,false)
            a.completed=true
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.flags=0
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.mine=nil
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.mine=true
            ns.LAR.CheckAll(true); assert(saved.done.dungeonThanes)
        ''')

    def test_unknown_scope_and_missing_completion_flag_are_not_success(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local a=Spelunker("Hall of Thanes",true); a.flags=nil
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            a.flags=0; a.criteria[1][3]=nil
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
        ''')

    def test_native_aliases_work_but_do_not_require_full_spelunker_completion(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local a=Spelunker("Durgen Dirgehammer",true)
            nativeRecords[64016]=a; nativeRecords[62031]=nil
            ns.LAR.CheckAll(true)
            assert(saved.done.dungeonThanes and not a.completed)
        ''')

    def test_multi_boss_dungeon_requires_individual_boss_evidence(self):
        self.check('''
            SelectAchievements("dungeon645")
            local a=Spelunker("Scholomance",true)
            assert(ns.LAR.BY_KEY.dungeon645.progress()==0)
            a.criteria={{"Boss",0,true,1,1,"",0,1853,"",1}, {"Unrelated linked achievement",8,true,1,1,"",0,10508,"",2}}
            assert(ns.LAR.BY_KEY.dungeon645.progress()==1)
            a.criteria[2][2]=0
            assert(ns.LAR.BY_KEY.dungeon645.progress()==2)
            ns.LAR.CheckAll(true); assert(saved.done.dungeon645)
        ''')

    def test_exact_personal_native_achievement_recovers_custom_completion(self):
        self.check('''
            SelectAchievements("pet1")
            nativeRecords[1017]={name="Can I Keep Him?",completed=true,flags=0,mine=false,criteria={}}
            ns.LAR.CheckAll(true); assert(not saved.done.pet1)
            nativeRecords[1017].mine=true; nativeRecords[1017].name="Something else"
            ns.LAR.CheckAll(true); assert(not saved.done.pet1)
            nativeRecords[1017].name="Can I Keep Him?"
            ns.LAR.CheckAll(true); assert(saved.done.pet1)
        ''')

    def test_native_reads_share_one_snapshot_and_refresh_on_the_next(self):
        self.check('''
            local count=0
            Spelunker("Hall of Thanes",true)
            local original=GetAchievementNumCriteria
            GetAchievementNumCriteria=function(...) count=count+1; return original(...) end
            ns.LAR.WithProgressSnapshot(function()
                assert(ns.LAR.BY_KEY.dungeonThanes.progress()==1)
                ns.LAR.BY_KEY.dungeonLordaeron.progress()
                ns.LAR.BY_KEY.dungeonThanes.progress()
            end)
            assert(count==1)
            ns.LAR.BY_KEY.dungeonThanes.progress(); assert(count==2)
        ''')

    def test_oversized_and_secret_native_criteria_are_not_read_as_complete(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            Spelunker("Hall of Thanes",true)
            GetAchievementNumCriteria=function() return 257 end
            GetAchievementCriteriaInfo=function() error("Must not enumerate oversized data") end
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
            SecretTestValue={}
            GetAchievementNumCriteria=function() return SecretTestValue end
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
        ''')

    def test_namespaced_skills_support_localized_profession_and_riding_names(self):
        self.check('''
            SelectAchievements("cook150","riding150")
            GetNumSkillLines=nil; GetSkillLineInfo=nil; GetProfessions=nil; IsPlayerSpell=nil
            C_SkillInfo={GetSkillLineInfoByID=function(id)
                if id==185 or id==762 then return {skillID=id,name="Localized skill",rank=150,isHeader=false} end
            end}
            ns.LAR.CheckAll(true)
            assert(saved.done.cook150 and saved.done.riding150)
        ''')

    def test_namespaced_skill_mismatch_headers_and_hidden_rank_are_rejected(self):
        self.check('''
            SelectAchievements("cook150")
            SecretTestValue={}
            C_SkillInfo={GetSkillLineInfoByID=function(id)
                return {skillID=185,name="Cooking",rank=SecretTestValue,isHeader=false}
            end}
            ns.LAR.CheckAll(true); assert(not saved.done.cook150)
            C_SkillInfo.GetSkillLineInfoByID=function(id) return {skillID=999,rank=300,isHeader=false} end
            ns.LAR.CheckAll(true); assert(not saved.done.cook150)
            C_SkillInfo.GetSkillLineInfoByID=function(id) return {skillID=id,rank=300,isHeader=true} end
            ns.LAR.CheckAll(true); assert(not saved.done.cook150)
        ''')

    def test_namespaced_player_spell_fallback_and_spells_changed_refresh(self):
        self.check('''
            SelectAchievements("riding150")
            IsPlayerSpell=nil
            C_SpellBook={IsSpellKnown=function(id,bank) assert(bank==nil); return id==33391 end}
            CoreEvent("SPELLS_CHANGED"); FlushTimers()
            assert(saved.done.riding150)
        ''')

    def test_statistic_fraction_does_not_become_a_kill_or_victory_total(self):
        self.check('''
            SelectAchievements("wsgWin")
            for _,value in ipairs({"1/10","0.5","-1","unknown","1g 20s"}) do
                GetStatistic=function() return value end
                ns.LAR.CheckAll(true); assert(not saved.done.wsgWin)
            end
            GetStatistic=function() return "1,000" end
            ns.LAR.CheckAll(true); assert(saved.done.wsgWin)
        ''')

    def test_disappearing_living_target_is_not_a_kill_but_successful_encounter_is(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            local exists=true
            ns.LAR.DB()
            function strsplit(separator,text)
                local parts={}
                for part in text:gmatch("[^"..separator.."]+") do parts[#parts+1]=part end
                return unpack(parts)
            end
            UnitExists=function() return exists end
            UnitGUID=function(unit) return unit=="target" and "Creature-0-0-0-0-12345-000000" or "Player-18-ABC" end
            local name=UnitName
            UnitName=function(unit) if unit=="target" then return "Durgen Dirgehammer" end; return name(unit) end
            UnitIsDead=function() return false end
            UnitClassification=function() return "elite" end
            CoreEvent("PLAYER_TARGET_CHANGED")
            exists=false; inCombat=true
            CoreEvent("PLAYER_TARGET_CHANGED")
            assert(not saved.bosses["Durgen Dirgehammer"] and not saved.done.dungeonThanes)
            inCombat=false
            CoreEvent("ENCOUNTER_END",1,"Durgen Dirgehammer",1,5,0)
            assert(not saved.done.dungeonThanes)
            CoreEvent("ENCOUNTER_END",1,"Durgen Dirgehammer",1,5,1)
            assert(saved.done.dungeonThanes)
        ''')

    def test_diagnostic_report_shows_native_evidence_without_awarding(self):
        self.check('''
            Spelunker("Hall of Thanes",true)
            ns.LAR.SLASH.apicheck("dungeonThanes")
            assert(not saved.done.dungeonThanes)
            local found=false
            for _,message in ipairs(messages) do if message:find("criterion=111111",1,true) then found=true end end
            assert(found)
        ''')

    def test_correction_hold_is_respected_even_when_native_evidence_exists(self):
        self.check('''
            SelectAchievements("dungeonThanes")
            Spelunker("Hall of Thanes",true)
            saved.completionCorrections={dungeonThanes={}}
            ns.LAR.CheckAll(true); assert(not saved.done.dungeonThanes)
        ''')
