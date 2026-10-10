"""Iteration 4 character proof checks against the production Lua 5.1 core."""
import unittest

from test_progression_addendum import CoreHarness


class Iteration4CoreTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("pet1","pet15","explore855","explore802","explore776","forAlliance","forHorde",
                "thunderfury","deathcharger","charger","dreadsteed")
            testZone="Moonglade"; testSubzone="Moonglade"
            function MoonTextures()
                return {{offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=false}}
            end
            C_MapExplorationInfo={GetExploredMapTextures=function(id) assert(id==1450); return MoonTextures() end}
        ''')

    def test_new_completions_record_identity_without_attributing_old_history(self):
        self.h.execute('''
            bagItems[0]={12345}; ns.FA.CheckAll(true)
            local attribution=ns.FA.CompletionAttribution("pet1")
            assert(attribution and attribution.key==ns.FA.CharacterIdentity().key)
            assert(attribution.name=="Alt" and attribution.realm=="Realm One")
            assert(saved.done.first==1730000000 and ns.FA.CompletionAttribution("first")==nil)
            assert(saved.trackingIdentity.key==attribution.key and saved.history[1]=="keep")
            attribution.name="Mutated caller copy"
            assert(ns.FA.CompletionAttribution("pet1").name=="Alt")
        ''')

    def test_known_db_owner_mismatch_is_unavailable_without_erasing_records(self):
        self.h.execute('''
            bagItems[0]={12345}; ns.FA.CheckAll(true)
            local original=saved.done.pet1
            currentName="Different"; currentSurname="Character"
            local known,reason=ns.FA.CharacterScope()
            assert(known==nil and reason:find("different character",1,true))
            assert(ns.FA.Earned("pet1")==nil)
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==nil and need==15)
            ns.FA.CheckAll(true)
            assert(saved.done.pet1==original and saved.done.pet15==nil)
            assert(saved.trackingIdentity.name=="Alt" and saved.history[1]=="keep")
        ''')

    def test_unreadable_saved_guid_metadata_cannot_be_treated_as_an_unbound_identity(self):
        self.h.execute('''
            ns.FA.BY_KEY.explore855.progress()
            saved.done.pet1=123456
            for _,value in ipairs({false,1,{},"invalid-guid"}) do
                saved.trackingIdentity.observedGUID=value
                assert(ns.FA.CharacterScope()==nil and ns.FA.Earned("pet1")==nil)
                ns.FA.CheckAll(true)
                assert(saved.done.pet1==123456 and saved.done.pet15==nil)
            end
            saved.trackingIdentity.observedGUID=nil
            assert(ns.FA.CharacterScope()==true and ns.FA.Earned("pet1")==123456)
        ''')

    def test_name_identity_and_guid_readiness_do_not_disable_this_character(self):
        self.h.execute('''
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and need==1)
            local proof=saved.explorationEvidence.explore855.Moonglade
            local originalKey=saved.trackingIdentity.key
            UnitGUID=function() return "Player-18-ABCDEF" end
            assert(ns.FA.CharacterIdentity().key~=originalKey and ns.FA.CharacterScope()==true)
            C_Map=nil; C_MapExplorationInfo=nil
            current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and saved.explorationEvidence.explore855.Moonglade==proof)
            ns.FA.CheckAll(true)
            assert(ns.FA.Earned("explore855") and saved.trackingIdentity.key==originalKey)
            UnitGUID=nil
            assert(ns.FA.CharacterScope()==true and ns.FA.Earned("explore855"))
        ''')

    def test_guid_identity_keeps_valid_full_name_when_fallback_api_is_unavailable(self):
        self.h.execute('''
            UnitFullName=function() return "Aldrin",nil end
            UnitName=function() error("Name fallback unavailable") end
            UnitGUID=function() return "Player-18-AAAA" end
            local identity=ns.FA.CharacterIdentity()
            assert(identity and identity.name=="Aldrin" and identity.surname==nil)
            assert(identity.guid=="Player-18-AAAA" and identity.realm=="Realm One")
            assert(ns.FA.CharacterScope()==true)
        ''')

    def test_first_later_observed_guid_is_pinned_without_rewriting_name_binding(self):
        self.h.execute('''
            assert(ns.FA.BY_KEY.explore855.progress()==1)
            local owner=saved.trackingIdentity
            local originalKey=owner.key
            UnitGUID=function() return "Player-18-AAAA" end
            assert(ns.FA.BY_KEY.explore855.progress()==1)
            assert(owner.key==originalKey and owner.guid==nil and owner.observedGUID=="Player-18-AAAA")
            UnitGUID=function() return "Player-18-BBBB" end
            assert(ns.FA.CharacterScope()==nil and ns.FA.BY_KEY.explore855.progress()==nil)
            assert(owner.observedGUID=="Player-18-AAAA" and saved.done.first==1730000000)
        ''')

    def test_two_known_different_guids_cannot_match_by_name(self):
        self.h.execute('''
            UnitGUID=function() return "Player-18-AAAA" end
            ns.FA.BY_KEY.explore855.progress()
            UnitGUID=function() return "Player-18-BBBB" end
            assert(ns.FA.CharacterScope()==nil)
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil and need==1 and saved.done.explore855==nil)
            assert(saved.trackingIdentity.guid=="Player-18-AAAA")
            UnitGUID=nil
            assert(ns.FA.CharacterScope()==true)
            C_Map=nil; C_MapExplorationInfo=nil
            current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and need==1)
        ''')

    def test_old_overlay_without_character_attribution_is_unknown_and_retained(self):
        self.h.execute('''
            local previous={kind="revealed-map-overlay",verified=true,mapID=1450,zoneName="Moonglade",
                offsetX=244,offsetY=89,observedOffsetX=244,observedOffsetY=89,textureWidth=512,textureHeight=512}
            saved.explorationEvidence={explore855={Moonglade=previous}}
            C_MapExplorationInfo=nil
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil and need==1 and saved.explorationEvidence.explore855.Moonglade==previous)
            ns.FA.CheckAll(true); assert(saved.done.explore855==nil)
            C_MapExplorationInfo={GetExploredMapTextures=function() return MoonTextures() end}
            current,need=ns.FA.BY_KEY.explore855.progress()
            local proof=saved.explorationEvidence.explore855.Moonglade
            assert(current==1 and proof.evidenceVersion==2)
            assert(proof.characterKey==ns.FA.CharacterIdentity().key and proof.previousEvidence==previous)
        ''')

    def test_prelocal_observation_v2_sample_stays_unknown_until_reobserved(self):
        self.h.execute('''
            local previous={kind="revealed-map-overlay",verified=true,mapID=1450,zoneName="Moonglade",
                evidenceVersion=2,characterKey=ns.FA.CharacterIdentity().key,
                offsetX=244,offsetY=89,observedOffsetX=244,observedOffsetY=89,textureWidth=512,textureHeight=512}
            saved.explorationEvidence={explore855={Moonglade=previous}}
            C_MapExplorationInfo=nil
            assert(ns.FA.BY_KEY.explore855.progress()==nil)
            assert(saved.explorationEvidence.explore855.Moonglade==previous)
            C_MapExplorationInfo={GetExploredMapTextures=function() return MoonTextures() end}
            assert(ns.FA.BY_KEY.explore855.progress()==1)
            local proof=saved.explorationEvidence.explore855.Moonglade
            assert(proof.characterLocationVerified and proof.previousEvidence==previous)
        ''')

    def test_copied_overlay_proof_does_not_award_another_character(self):
        self.h.execute('''
            local current=ns.FA.BY_KEY.explore855.progress(); assert(current==1)
            local proof=saved.explorationEvidence.explore855.Moonglade
            local mainDB=ForeverAchievementsCharDB
            currentName="Other"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={},explorationEvidence={explore855={Moonglade=proof}}}
            C_MapExplorationInfo=nil
            current=ns.FA.BY_KEY.explore855.progress(); assert(current==nil)
            ns.FA.CheckAll(true)
            assert(ForeverAchievementsCharDB.done.explore855==nil)
            assert(mainDB.explorationEvidence.explore855.Moonglade==proof and proof.characterKey~=ns.FA.CharacterIdentity().key)
        ''')

    def test_historical_false_completion_is_preserved_until_explicit_correction(self):
        self.h.execute('''
            saved.done.explore855=123456
            C_Map=nil; C_MapExplorationInfo=nil
            ns.FA.CheckAll(true)
            assert(saved.done.explore855==123456 and ns.FA.Earned("explore855")==123456)
            assert(ns.FA.CompletionAttribution("explore855")==nil)
            ns.FA.SLASH.correctachievement("explore855")
            local pending=ns.FA.ProgressionDiagnostics.PendingCorrection()
            ns.FA.SLASH.correctachievement("explore855 confirm "..pending.token)
            assert(saved.done.explore855==nil and saved.correctionHistory[1].completion==123456)
            assert(saved.completionCorrections.explore855 and saved.done.first==1730000000)
        ''')

    def test_correction_rejects_a_known_other_character_db(self):
        self.h.execute('''
            bagItems[0]={12345}; ns.FA.CheckAll(true)
            local timestamp=saved.done.pet1
            currentName="Other"; currentSurname="Character"
            ns.FA.SLASH.correctachievement("pet1")
            assert(ns.FA.ProgressionDiagnostics.PendingCorrection()==nil)
            assert(saved.done.pet1==timestamp and saved.correctionHistory==nil)
        ''')

    def test_correction_archives_new_completion_attribution(self):
        self.h.execute('''
            bagItems[0]={12345}; ns.FA.CheckAll(true)
            local attribution=saved.completionAttribution.pet1
            ns.FA.SLASH.correctachievement("pet1")
            local pending=ns.FA.ProgressionDiagnostics.PendingCorrection()
            ns.FA.SLASH.correctachievement("pet1 confirm "..pending.token)
            assert(saved.correctionHistory[1].attribution==attribution)
            assert(attribution.identity.name=="Alt" and ns.FA.CompletionAttribution("pet1")==nil)
        ''')

    def test_unattributed_collection_history_is_unknown_and_not_reassigned(self):
        self.h.execute('''
            saved.characterPetItems={[12345]=true}
            local old=saved.characterPetItems
            local current,need=ns.FA.BY_KEY.pet1.progress()
            assert(current==nil and need==1 and saved.characterPetItems==old and old[12345])
            ns.FA.CheckAll(true); assert(saved.done.pet1==nil)
            bagItems[0]={23456}
            current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==1 and need==15 and old[12345] and old[23456])
            assert(saved.characterCollectionEvidence.characterPetItems.items[12345]==nil)
            assert(saved.characterCollectionEvidence.characterPetItems.items[23456])
        ''')

    def test_collection_ledger_survives_reload_and_isolated_character_switch(self):
        self.h.execute('''
            bagItems[0]={12345}; ns.FA.CheckAll(true); bagItems={}
            assert(ns.FA.BY_KEY.pet15.progress()==1)
            local mainDB=ForeverAchievementsCharDB
            local evidence=mainDB.characterCollectionEvidence
            currentName="Other"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={},characterCollectionEvidence=evidence,
                characterPetItems=mainDB.characterPetItems}
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==nil and need==15)
            ns.FA.CheckAll(true); assert(ForeverAchievementsCharDB.done.pet1==nil)
            assert(mainDB.done.pet1 and evidence.characterPetItems.characterKey==mainDB.trackingIdentity.key)
        ''')

    def test_for_alliance_exclusion_uses_exact_custom_id_and_keeps_history(self):
        self.h.execute('''
            local a,b=ns.FA.BY_KEY.forAlliance,ns.FA.BY_KEY.forHorde
            assert(a.id==614 and not ns.FA.Available(a) and not b.unsupported)
            for _,boss in ipairs({4949,3057,10181,10540}) do ns.FA.DB().bosses[boss]=123456 end
            ns.FA.CheckAll(true); assert(saved.done.forAlliance==nil)
            saved.done.forAlliance=987654
            ns.FA.CheckAll(true); assert(saved.done.forAlliance==987654 and saved.history[1]=="keep")
            UnitFactionGroup=function() return "Horde" end
            assert(ns.FA.Available(b) and b.id==619)
        ''')

    def test_globally_revealed_remote_texture_does_not_award_moonglade(self):
        self.h.execute('''
            testZone="Elwynn Forest"; testSubzone="Goldshire"
            C_Map.GetBestMapForUnit=function() return 1429 end
            C_Map.GetMapInfo=function(id)
                return {mapID=id,name=id==1450 and "Moonglade" or "Elwynn Forest"}
            end
            ns.FA.CheckAll(true)
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil and need==1 and saved.done.explore855==nil)
            assert(not saved.explorationEvidence or not saved.explorationEvidence.explore855)
        ''')

    def test_local_zone_text_without_a_matching_actual_unit_map_is_unknown(self):
        self.h.execute('''
            C_Map.GetBestMapForUnit=function() return 1448 end
            C_Map.GetMapInfo=function(id)
                return {mapID=id,name=id==1450 and "Moonglade" or "Felwood"}
            end
            ns.FA.CheckAll(true)
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil and need==1 and saved.done.explore855==nil)
        ''')

    def test_exposed_discovered_area_api_requires_a_positive_nonpreview_discovery(self):
        self.h.execute('''
            C_Map.GetPlayerMapPosition=function(id,unit) assert(id==1450 and unit=="player"); return {} end
            C_Map.GetAreaInfo=function(id) assert(id==493); return "Moonglade" end
            C_MapExplorationInfo.GetExploredAreaIDsAtPosition=function() return {} end
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil and need==1 and saved.done.explore855==nil)
            C_MapExplorationInfo.GetExploredAreaIDsAtPosition=function() return {493} end
            current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and saved.explorationEvidence.explore855.Moonglade.exploredAreaAPIConfirmed)
        ''')

    def test_two_characters_keep_elwynn_and_westfall_independent_of_shared_native_completion(self):
        self.h.execute('''
            local currentMap
            local names={[1429]="Elwynn Forest",[1436]="Westfall",[1453]="Stormwind City",[1450]="Moonglade"}
            C_Map.GetBestMapForUnit=function() return currentMap end
            C_Map.GetMapInfo=function(id) return names[id] and {mapID=id,name=names[id]} end
            C_MapExplorationInfo.GetExploredMapTextures=function(id)
                local out={}
                for _,zone in ipairs(ns.EXPLORE) do
                    if zone.map==id then
                        for _,area in ipairs(zone.areas) do
                            out[#out+1]={offsetX=area[2],offsetY=area[3],textureWidth=256,textureHeight=256,isShownByMouseOver=false}
                        end
                    end
                end
                return out
            end
            GetAchievementInfo=function(id) return id,"Native account progression",0,true end
            for _,zone in ipairs(ns.EXPLORE) do
                if zone.id==776 or zone.id==802 then
                    for _,area in ipairs(zone.areas) do
                        testZone=zone.zone; testSubzone=area[1]; currentMap=zone.map
                        if area[1]=="Stormwind City" then testZone="Stormwind City"; currentMap=1453 end
                        ns.FA.CheckAll(true)
                    end
                    assert(ns.FA.Earned("explore"..zone.id))
                end
            end
            local mainDB=ForeverAchievementsCharDB
            local elwynnAt,westfallAt=mainDB.done.explore776,mainDB.done.explore802
            ns.FA.Account().chars.main={done={explore776=elwynnAt,explore802=westfallAt}}
            currentName="Second"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={}}
            testZone="Moonglade"; testSubzone="Nighthaven"; currentMap=1450
            ns.FA.CheckAll(true)
            assert(ns.FA.Earned("explore776")==nil and ns.FA.Earned("explore802")==nil)
            assert(ForeverAchievementsCharDB.done.explore776==nil and ForeverAchievementsCharDB.done.explore802==nil)
            assert(mainDB.done.explore776==elwynnAt and mainDB.done.explore802==westfallAt)
            local current,need=ns.FA.BY_KEY.explore802.progress()
            assert(current==nil and need==14)
            assert(#calls==0 and mainDB.done.first==1730000000)
        ''')

    def test_character_identity_and_geographic_reads_are_shared_within_one_pass(self):
        self.h.execute('''
            local names,zones,subzones,maps=0,0,0,0
            UnitName=function() names=names+1; return currentName,currentSurname end
            GetRealZoneText=function() zones=zones+1; return testZone end
            GetSubZoneText=function() subzones=subzones+1; return testSubzone end
            C_Map.GetBestMapForUnit=function() maps=maps+1; return 1450 end
            ns.FA.WithProgressSnapshot(function()
                for i=1,20 do
                    assert(ns.FA.CharacterScope()==true)
                    assert(ns.FA.BY_KEY.explore855.progress()==1)
                end
            end)
            assert(names==1 and zones==1 and subzones==1 and maps==1)
            ns.FA.WithProgressSnapshot(ns.FA.BY_KEY.explore855.progress)
            assert(names==2 and zones==2 and subzones==2 and maps==2)
        ''')

    def test_entering_world_clears_map_samples_alongside_money_and_battleground_work(self):
        self.h.execute('''
            local discovered,reads=false,0
            C_MapExplorationInfo.GetExploredMapTextures=function()
                reads=reads+1; return discovered and MoonTextures() or {}
            end
            assert(ns.FA.BY_KEY.explore855.progress()==0 and reads==1)
            discovered=true
            assert(ns.FA.BY_KEY.explore855.progress()==0 and reads==1)
            CoreEvent("PLAYER_ENTERING_WORLD")
            assert(ns.FA.BY_KEY.explore855.progress()==1 and reads==2)
            FlushTimers()
            assert(ns.FA.Earned("explore855") and saved.done.first==1730000000)
        ''')

    def test_account_mount_journal_and_old_owned_flags_cannot_award_character_feats(self):
        self.h.execute('''
            saved.owned={[13335]=true}
            local old=saved.owned
            C_Item.GetItemCount=function() return 0 end
            IsEquippedItem=function() return false end
            IsPlayerSpell=function() return false end
            C_MountJournal={GetMountFromSpell=function() error("Account mount journal must not be queried") end,
                GetMountInfoByID=function() error("Account ownership must not be queried") end}
            local current,need=ns.FA.BY_KEY.deathcharger.progress()
            assert(current==nil and need==1)
            ns.FA.CheckAll(true)
            assert(saved.done.deathcharger==nil and saved.owned==old and old[13335])
            saved.done.deathcharger=123456
            ns.FA.CheckAll(true); assert(saved.done.deathcharger==123456)
        ''')

    def test_current_character_bank_item_or_equipped_item_proves_feat_ownership(self):
        self.h.execute('''
            C_Item.GetItemCount=function(id,includeBank)
                assert(includeBank==true); return id==19019 and 1 or 0
            end
            IsEquippedItem=function(id) return id==13335 end
            IsPlayerSpell=function() return false end
            ns.FA.CheckAll(true)
            assert(ns.FA.Earned("thunderfury") and ns.FA.Earned("deathcharger"))
            assert(saved.featOwnershipEvidence.items[19019] and saved.featOwnershipEvidence.items[13335])
            C_Item.GetItemCount=nil; IsEquippedItem=nil
            assert(ns.FA.BY_KEY.thunderfury.progress()==1 and ns.FA.BY_KEY.deathcharger.progress()==1)
            local mainDB=ForeverAchievementsCharDB
            currentName="Different"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={},owned=mainDB.owned,featOwnershipEvidence=mainDB.featOwnershipEvidence}
            assert(ns.FA.BY_KEY.thunderfury.progress()==nil)
            ns.FA.CheckAll(true); assert(ForeverAchievementsCharDB.done.thunderfury==nil)
        ''')

    def test_class_bound_feats_need_the_current_class_even_if_a_spell_api_reports_true(self):
        self.h.execute('''
            IsPlayerSpell=function(id) return id==23214 or id==23161 end
            local charger,dreadsteed=ns.FA.BY_KEY.charger,ns.FA.BY_KEY.dreadsteed
            assert(charger.class=="PALADIN" and dreadsteed.class=="WARLOCK")
            ns.FA.CheckAll(true)
            assert(saved.done.charger==nil and saved.done.dreadsteed==nil)
            UnitClass=function() return "Paladin","PALADIN" end
            assert(ns.FA.Available(charger) and not ns.FA.Available(dreadsteed))
            ns.FA.CheckAll(true)
            assert(saved.done.charger and saved.done.dreadsteed==nil)
            UnitClass=function() return "Warrior","WARRIOR" end
            assert(saved.done.charger and not ns.FA.Available(charger))
        ''')

    def test_missing_or_malformed_ownership_apis_stay_unknown(self):
        self.h.execute('''
            C_Item.GetItemCount=function() return "1" end
            IsEquippedItem=function() return "yes" end
            IsPlayerSpell=nil
            local current,need=ns.FA.BY_KEY.thunderfury.progress()
            assert(current==nil and need==1 and saved.done.thunderfury==nil)
            ns.FA.CheckAll(true)
            assert(saved.done.thunderfury==nil and saved.done.deathcharger==nil)
        ''')


if __name__ == "__main__":
    unittest.main()
