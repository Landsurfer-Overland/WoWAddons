"""Actual reported account-wide OR criterion, not a fabricated personal row."""
import unittest

from test_client_api_evidence import ClientAPIEvidenceTests


class DungeonRecoveryTests(unittest.TestCase):
    check = ClientAPIEvidenceTests.check

    def setUp(self):
        ClientAPIEvidenceTests.setUp(self)
        self.h.load("Integrations/DungeonRecovery.lua")
        self.h.execute('''
            SelectAchievements("dungeonThanes","dungeon629")
            GetStatistic=function() return "--" end
            function SharedCriterion(done)
                local a=Spelunker("Ragefire Chasm or Hall of Thanes",done,ACHIEVEMENT_FLAGS_ACCOUNT,false)
                a.criteria[1][10]=19213
                return a
            end
            activeInstance=nil
            IsInInstance=function() return activeInstance~=nil,"party" end
            GetInstanceInfo=function() return activeInstance,"party",1,"Normal",5,nil,nil,999 end
            function RecoveryEvent(event,...)
                ns.DungeonRecovery.frame:Fire("OnEvent",event,...)
            end
        ''')

    def test_reported_record_matches_both_alternatives_but_grants_neither_automatically(self):
        self.check('''
            SharedCriterion(true)
            ns.LAR.CheckAll(true)
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
            ns.LAR.SLASH.apicheck("dungeonThanes")
            local found=false
            for _,message in ipairs(messages) do if message:find("match=shared-dungeon",1,true) then found=true end end
            assert(found)
        ''')

    def test_recovery_preview_does_not_grant_or_record_personal_completion(self):
        self.check('''
            SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeonThanes")==false)
            assert(not saved.done.dungeonThanes and saved.nativeDungeonEvidence==nil)
        ''')

    def test_confirmed_hall_completion_recovers_only_hall_and_preserves_native_statistic(self):
        self.check('''
            SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            local proof=saved.nativeDungeonEvidence.dungeonThanes
            assert(proof.criteriaID==19213 and proof.achievementID==62031)
            assert(proof.kind=="player-confirmed" and proof.nativeScope=="account")
            assert(proof.characterKey==ns.LAR.CharacterIdentity().key)
            assert(saved.bosses["Durgen Dirgehammer"]==nil and GetStatistic(63573)=="--")
            local date=saved.done.dungeonThanes
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm") and saved.done.dungeonThanes==date)
            assert(ns.LAR.ProgressEvidence("dungeonThanes").source:find("player-confirmed",1,true))
        ''')

    def test_recovery_of_other_alternative_does_not_grant_hall(self):
        self.check('''
            SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeon629 confirm"))
            assert(saved.done.dungeon629 and not saved.done.dungeonThanes)
        ''')

    def test_uncompleted_native_record_cannot_be_recovered(self):
        self.check('''
            SharedCriterion(false)
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            assert(not saved.done.dungeonThanes and saved.nativeDungeonEvidence==nil)
        ''')

    def test_whole_personal_meta_still_cannot_identify_which_alternative(self):
        self.check('''
            local a=SharedCriterion(true); a.completed=true; a.mine=true
            ns.LAR.CheckAll(true)
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_reused_criterion_id_wrong_label_and_wrong_parent_are_rejected(self):
        self.check('''
            local a=SharedCriterion(true); a.criteria[1][1]="Unrelated objective"
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            a.criteria[1][1]="Ragefire Chasm or Hall of Thanes"; a.criteria[1][10]=999999
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            a.criteria[1][10]=19213; a.name="Different native achievement"
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
        ''')

    def test_login_and_visiting_previously_credited_instance_do_not_grant(self):
        self.check('''
            SharedCriterion(true); activeInstance="The Hall of Thanes"
            RecoveryEvent("PLAYER_LOGIN"); FlushTimers()
            RecoveryEvent("CRITERIA_UPDATE"); FlushTimers()
            ns.LAR.CheckAll(true)
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_new_native_transition_in_hall_grants_hall_with_context_evidence(self):
        self.check('''
            local a=SharedCriterion(false); activeInstance="The Hall of Thanes"
            RecoveryEvent("PLAYER_LOGIN"); FlushTimers()
            a.criteria[1][3]=true
            CoreEvent("CRITERIA_UPDATE"); FlushTimers()
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
            local proof=saved.nativeDungeonEvidence.dungeonThanes
            assert(proof.kind=="native-event-in-instance" and proof.instanceName==activeInstance)
        ''')

    def test_explicit_criterion_event_can_attribute_first_observed_completion(self):
        self.check('''
            SharedCriterion(true); activeInstance="Hall of Thanes"
            CoreEvent("CRITERIA_COMPLETE",19213); FlushTimers()
            assert(saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_native_event_in_ragefire_grants_only_ragefire(self):
        self.check('''
            SharedCriterion(true); activeInstance="Ragefire Chasm"
            CoreEvent("CRITERIA_COMPLETE",19213); FlushTimers()
            assert(saved.done.dungeon629 and not saved.done.dungeonThanes)
        ''')

    def test_outside_or_unrelated_instance_cannot_supply_personal_attribution(self):
        self.check('''
            SharedCriterion(true)
            CoreEvent("CRITERIA_COMPLETE",19213); FlushTimers()
            activeInstance="The Deadmines"
            CoreEvent("CRITERIA_COMPLETE",19213); FlushTimers()
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_conflicting_instance_context_in_event_burst_is_not_used(self):
        self.check('''
            SharedCriterion(true); activeInstance="Hall of Thanes"
            RecoveryEvent("CRITERIA_COMPLETE",19213)
            activeInstance="Ragefire Chasm"
            RecoveryEvent("CRITERIA_COMPLETE",19213)
            FlushTimers()
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_conflicting_zone_and_instance_names_cannot_choose_the_wrong_alternative(self):
        self.check('''
            SharedCriterion(true); activeInstance="Ragefire Chasm"
            GetRealZoneText=function() return "Hall of Thanes" end
            CoreEvent("CRITERIA_COMPLETE",19213); FlushTimers()
            assert(not saved.done.dungeonThanes and not saved.done.dungeon629)
        ''')

    def test_diagnostics_stop_prompting_for_recovery_once_personal_evidence_is_recorded(self):
        self.check('''
            SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            messages={}
            ns.LAR.SLASH.apicheck("dungeonThanes")
            local found=false
            for _,message in ipairs(messages) do
                assert(not message:find("needs character/dungeon attribution",1,true))
                if message:find("player-confirmed",1,true) then found=true end
            end
            assert(found)
        ''')

    def test_evidence_cannot_be_reused_by_another_character(self):
        self.check('''
            SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            local proof=saved.nativeDungeonEvidence
            currentName="Other"; currentSurname="Character"
            LegacyAchievementsReforgedCharDB={done={},nativeDungeonEvidence=proof}
            assert(ns.LAR.BY_KEY.dungeonThanes.progress()==0)
            ns.LAR.CheckAll(true)
            assert(not LegacyAchievementsReforgedCharDB.done.dungeonThanes)
        ''')

    def test_pending_event_cannot_follow_a_character_database_switch(self):
        self.check('''
            SharedCriterion(true); activeInstance="Hall of Thanes"
            RecoveryEvent("CRITERIA_COMPLETE",19213)
            currentName="Other"; currentSurname="Character"
            LegacyAchievementsReforgedCharDB={done={}}
            FlushTimers()
            assert(saved.nativeDungeonEvidence==nil and not saved.done.dungeonThanes)
            assert(not LegacyAchievementsReforgedCharDB.done.dungeonThanes)
        ''')

    def test_correction_hold_and_malformed_evidence_are_preserved(self):
        self.check('''
            SharedCriterion(true)
            saved.completionCorrections={dungeonThanes={reason="keep"}}
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            assert(saved.completionCorrections.dungeonThanes.reason=="keep")
            saved.completionCorrections=nil; saved.nativeDungeonEvidence=false
            assert(not ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            assert(saved.nativeDungeonEvidence==false and not saved.done.dungeonThanes)
        ''')

    def test_recovery_alias_uses_completed_alias_without_needing_both(self):
        self.check('''
            local a=SharedCriterion(true); a.criteria[1][10]=117733
            nativeRecords[64016]=a; nativeRecords[62031]=nil
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            assert(saved.nativeDungeonEvidence.dungeonThanes.achievementID==64016)
        ''')

    def test_later_guid_is_pinned_and_recreated_namesake_cannot_inherit_evidence(self):
        self.check('''
            UnitGUID=nil; SharedCriterion(true)
            assert(ns.DungeonRecovery.Recover("dungeonThanes confirm"))
            UnitGUID=function() return "Player-18-FIRST" end
            assert(ns.LAR.BY_KEY.dungeonThanes.progress()==1)
            assert(saved.trackingIdentity.observedGUID=="Player-18-FIRST")
            UnitGUID=function() return "Player-18-SECOND" end
            assert(ns.LAR.BY_KEY.dungeonThanes.progress()==0)
        ''')
