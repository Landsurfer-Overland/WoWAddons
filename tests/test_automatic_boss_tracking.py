"""Automatic credit without confirmation, including already-true account flags."""
import unittest

from test_dungeon_recovery import DungeonRecoveryTests


class AutomaticBossTrackingTests(unittest.TestCase):
    check = DungeonRecoveryTests.check

    def setUp(self):
        DungeonRecoveryTests.setUp(self)
        self.h.load("Integrations/AutomaticBossTracking.lua")
        self.h.execute('''
            SharedCriterion(true)
            stats={}; statByID={}
            local baseInfo=GetAchievementInfo
            GetAchievementInfo=function(id,index)
                local s=id==900 and index and stats[index] or statByID[id]
                if s then return s.id,s.name,0,false,nil,nil,nil,"Boss kill counter",s.flags,1,nil,false,false end
                return baseInfo(id,index)
            end
            GetStatisticsCategoryList=function() return {900} end
            GetCategoryNumAchievements=function(id) assert(id==900); return #stats end
            GetStatistic=function(id) return statByID[id] and statByID[id].value or "--" end
            function AddStat(id,name,value,flags)
                local s={id=id,name=name,value=value,flags=flags or 0}
                stats[#stats+1]=s; statByID[id]=s; return s
            end
            function AutomaticEvent(event,...)
                ns.AutomaticBossTracking.frame:Fire("OnEvent",event,...)
            end
            function strsplit(separator,text)
                local parts={}
                for part in text:gmatch("[^"..separator.."]+") do parts[#parts+1]=part end
                return unpack(parts)
            end
        ''')

    def test_successful_encounter_unit_list_awards_hall_without_target_or_new_account_tick(self):
        self.check('''
            CoreEvent("ENCOUNTER_END",7000,"Ragefire Chasm or Hall of Thanes",1,5,1,
                {{creatureID=260999,creatureName="Durgen Dirgehammer",remainingHealthPercent=0}})
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            assert(saved.nativeDungeonEvidence==nil)
            local proof=saved.bossEvidence["Durgen Dirgehammer"]
            assert(proof.encounterID==7000 and proof.creatureID==260999 and proof.inferred==false)
            assert(proof.source=="native encounter boss-status list")
        ''')

    def test_encounter_unit_list_awards_only_the_boss_actually_defeated(self):
        self.check('''
            CoreEvent("ENCOUNTER_END",7000,"Combined encounter",1,5,1,
                {{creatureID=11520,creatureName="Taragaman the Hungerer",remainingHealthPercent=0},
                 {creatureID=260999,creatureName="Durgen Dirgehammer",remainingHealthPercent=100}})
            assert(saved.done.dungeon629 and not saved.done.dungeonThanes)
        ''')

    def test_failed_encounter_and_unreadable_health_do_not_award(self):
        self.check('''
            local units={{creatureID=260999,creatureName="Durgen Dirgehammer",remainingHealthPercent=0}}
            CoreEvent("ENCOUNTER_END",7000,"Combined encounter",1,5,0,units)
            assert(not saved.done.dungeonThanes)
            SecretTestValue={}; units[1].remainingHealthPercent=SecretTestValue
            CoreEvent("ENCOUNTER_END",7000,"Combined encounter",1,5,1,units)
            assert(not saved.done.dungeonThanes)
        ''')

    def test_successful_known_creature_id_works_when_unit_name_is_unavailable(self):
        self.check('''
            CoreEvent("ENCOUNTER_END",7000,"Combined encounter",1,5,1,
                {{creatureID=11520,remainingHealthPercent=0}})
            assert(saved.done.dungeon629 and not saved.done.dungeonThanes)
        ''')

    def test_kill_event_is_automatic_even_when_account_criterion_was_already_true(self):
        self.check('''
            CoreEvent("BOSS_KILL",7000,"Durgen Dirgehammer")
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            assert(saved.bossEvidence["Durgen Dirgehammer"].source=="native BOSS_KILL event")
        ''')

    def test_login_discovers_historical_counter_with_a_different_id_automatically(self):
        self.check('''
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","1")
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            assert(ns.LAR.ProgressEvidence("dungeonThanes").observations.statisticID==910001)
            assert(GetStatistic(63573)=="--" and saved.nativeDungeonEvidence==nil)
        ''')

    def test_account_wide_and_unrelated_counters_are_not_personal_boss_history(self):
        self.check('''
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","100",ACHIEVEMENT_FLAGS_ACCOUNT)
            AddStat(910002,"Durgen Dirgehammer Deaths (Hall of Thanes)","100")
            AddStat(910003,"Durgen Dirgehammer Kills (A Different Dungeon)","100")
            ns.AutomaticBossTracking.Discover()
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_lagging_statistic_refreshes_without_another_catalog_scan(self):
        self.check('''
            local s=AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","--")
            ns.AutomaticBossTracking.Discover()
            assert(not saved.done.dungeonThanes)
            s.value="1"
            CoreEvent("CRITERIA_UPDATE"); FlushTimers()
            assert(saved.done.dungeonThanes and ns.AutomaticBossTracking.attempts==1)
        ''')

    def test_discovered_statistic_metadata_is_revalidated_before_use(self):
        self.check('''
            local s=AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","0")
            ns.AutomaticBossTracking.Discover()
            assert(not saved.done.dungeonThanes)
            s.name="Different objective"; s.value="5"
            ns.LAR.CheckAll(true)
            assert(not saved.done.dungeonThanes)
        ''')

    def test_discovery_is_bounded_and_missing_apis_do_not_require_player_actions(self):
        self.check('''
            GetStatisticsCategoryList=nil
            for i=1,10 do ns.AutomaticBossTracking.Discover() end
            assert(ns.AutomaticBossTracking.attempts==3 and not saved.done.dungeonThanes)
            CoreEvent("BOSS_KILL",7000,"Durgen Dirgehammer")
            assert(saved.done.dungeonThanes)
        ''')

    def test_metadata_scan_does_not_exceed_record_budget(self):
        self.check('''
            local reads=0
            GetCategoryNumAchievements=function() return 5000 end
            GetAchievementInfo=function(category) if category==900 then reads=reads+1 end; return nil end
            ns.AutomaticBossTracking.Discover()
            assert(reads==2500 and ns.AutomaticBossTracking.scanned==2500)
        ''')

    def test_native_addon_loading_retries_history_when_api_was_unavailable_at_login(self):
        self.check('''
            local categories=GetStatisticsCategoryList
            GetStatisticsCategoryList=nil
            for i=1,3 do ns.AutomaticBossTracking.Discover() end
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","1")
            GetStatisticsCategoryList=categories
            AutomaticEvent("ADDON_LOADED","Blizzard_LegacySystem")
            assert(saved.done.dungeonThanes and ns.AutomaticBossTracking.attempts==4)
            AutomaticEvent("ADDON_LOADED","Blizzard_AchievementUI")
            assert(ns.AutomaticBossTracking.attempts==4)
        ''')

    def test_initial_empty_catalog_is_retried_when_server_metadata_arrives(self):
        self.check('''
            assert(not ns.AutomaticBossTracking.Discover())
            assert(ns.AutomaticBossTracking.state~="Ready")
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","1")
            assert(ns.AutomaticBossTracking.Discover())
            assert(saved.done.dungeonThanes and ns.AutomaticBossTracking.attempts==2)
        ''')

    def test_missing_metadata_does_not_freeze_discovery_as_ready(self):
        self.check('''
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","1")
            local info=GetAchievementInfo
            local ready=false
            GetAchievementInfo=function(id,index)
                if id==900 and index and not ready then return nil end
                return info(id,index)
            end
            assert(not ns.AutomaticBossTracking.Discover() and not saved.done.dungeonThanes)
            ready=true
            assert(ns.AutomaticBossTracking.Discover() and saved.done.dungeonThanes)
        ''')

    def test_catalog_scan_defers_during_combat_and_resumes_after_regen(self):
        self.check('''
            AddStat(910001,"Durgen Dirgehammer Kills (Hall of Thanes)","1")
            inCombat=true
            ns.AutomaticBossTracking.Discover()
            assert(ns.AutomaticBossTracking.attempts==0 and not saved.done.dungeonThanes)
            inCombat=false
            AutomaticEvent("PLAYER_REGEN_ENABLED")
            assert(saved.done.dungeonThanes)
        ''')

    def test_corpse_loot_records_personal_kill_when_encounter_events_are_missing(self):
        self.check('''
            local name=UnitName
            UnitName=function(unit) if unit=="target" then return "Durgen Dirgehammer" end; return name(unit) end
            UnitGUID=function(unit) if unit=="target" then return "Creature-0-0-0-0-260999-00AB" end end
            GetNumLootItems=function() return 1 end
            GetLootSourceInfo=function() return "Creature-0-0-0-0-260999-00AB",1 end
            AutomaticEvent("LOOT_OPENED")
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            assert(saved.bossEvidence["Durgen Dirgehammer"].source:find("corpse loot",1,true))
            assert(saved.bossEvidence["Durgen Dirgehammer"].inferred==true)
        ''')

    def test_unrelated_corpse_and_disappearing_living_target_do_not_award(self):
        self.check('''
            local name=UnitName
            UnitName=function(unit) if unit=="target" then return "Durgen Dirgehammer" end; return name(unit) end
            local guid="Creature-0-0-0-0-260999-00AB"
            UnitGUID=function(unit) if unit=="target" then return guid end end
            AutomaticEvent("PLAYER_TARGET_CHANGED")
            guid=nil
            AutomaticEvent("PLAYER_TARGET_CHANGED")
            assert(not saved.done.dungeonThanes)
            GetNumLootItems=function() return 1 end
            GetLootSourceInfo=function() return "Creature-0-0-0-0-260999-00AC",1 end
            AutomaticEvent("LOOT_OPENED")
            assert(not saved.done.dungeonThanes)
        ''')

    def test_cached_loot_identity_does_not_follow_a_character_switch(self):
        self.check('''
            local name=UnitName
            UnitName=function(unit) if unit=="target" then return "Durgen Dirgehammer" end; return name(unit) end
            local guid="Creature-0-0-0-0-260999-00AB"
            UnitGUID=function(unit) if unit=="target" then return guid end end
            AutomaticEvent("PLAYER_TARGET_CHANGED")
            currentName="Other"; currentSurname="Character"; guid=nil
            LegacyAchievementsReforgedCharDB={done={}}
            GetNumLootItems=function() return 1 end
            GetLootSourceInfo=function() return "Creature-0-0-0-0-260999-00AB",1 end
            AutomaticEvent("LOOT_OPENED")
            assert(not LegacyAchievementsReforgedCharDB.done.dungeonThanes and not saved.done.dungeonThanes)
        ''')

    def test_duplicate_native_events_preserve_completion_date(self):
        self.check('''
            CoreEvent("BOSS_KILL",7000,"Durgen Dirgehammer")
            local at=saved.done.dungeonThanes
            CoreEvent("ENCOUNTER_END",7000,"Durgen Dirgehammer",1,5,1,
                {{creatureID=260999,creatureName="Durgen Dirgehammer",remainingHealthPercent=0}})
            assert(saved.done.dungeonThanes==at)
        ''')
