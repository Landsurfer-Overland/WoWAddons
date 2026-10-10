"""Targeted historical Moonglade display authority, using production Lua 5.1.

Saved timestamps remain intact. These fixtures reproduce a stale display path;
they do not establish the source of a live character's reported completion.
"""
import unittest

from test_progression_addendum import CoreHarness
from test_iteration3_categories import FIXTURES


SETUP = r'''
SelectAchievements("explore855", "explore802", "exploreEK", "exploreKal", "worldexplorer")
testZone="Elwynn Forest"; testSubzone="Goldshire"
function MoonTextures()
    return {{offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=false}}
end
C_Map.GetBestMapForUnit=function() return testZone=="Moonglade" and 1450 or 1429 end
C_Map.GetMapInfo=function(id)
    if id==1450 then return {mapID=id,name="Moonglade"} end
    if id==1429 then return {mapID=id,name="Elwynn Forest"} end
end
C_MapExplorationInfo={GetExploredMapTextures=function(id)
    assert(id==1450); return MoonTextures()
end}
function UseExplorationCatalog(...)
    local rows={}
    for _,key in ipairs({...}) do rows[#rows+1]=ns.FA.BY_KEY[key] end
    ns.FA.CATEGORIES={{key="exploration",label="Exploration"}}
    ns.FA.CATEGORY_ORDER={"exploration"}
    ns.FA.CATEGORY_SECTIONS={exploration={{title="KALIMDOR",list=rows}}}
end
UseExplorationCatalog("explore855", "explore802", "exploreEK", "exploreKal", "worldexplorer")
'''


class Iteration5ExplorationTests(unittest.TestCase):
    def setUp(self):
        self.h=CoreHarness()
        self.h.execute(SETUP)
        self.h.load("Integrations/CustomAdapter.lua")

    def test_remote_revealed_map_is_not_a_new_custom_completion(self):
        self.h.execute('''
            ns.FA.CheckAll(true)
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row and row.completed==false and row.current==nil)
            assert(row.timestamp==nil and saved.done.explore855==nil)
            assert(ns.FA.Earned("explore855")==nil and #calls==0)
        ''')

    def test_unattributed_stale_moonglade_timestamp_is_unknown_and_kept_verbatim(self):
        self.h.execute('''
            saved.done.explore855=123456
            local original=saved.done
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row.completed==nil and row.completionState=="unknown" and row.timestamp==nil)
            assert(row.historicalTimestamp==123456 and row.completionVerificationReason:find("retained",1,true))
            assert(ns.FA.Earned("explore855")==nil)
            local points,possible,done,available,known=ns.FA.TotalPoints()
            assert(points==0 and possible==120 and done==0 and available==5 and known==false)
            ns.FA.CheckAll(true)
            assert(saved.done==original and saved.done.explore855==123456)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_valid_current_local_proof_preserves_old_completion_away_from_zone(self):
        self.h.execute('''
            saved.done.explore855=123456
            testZone="Moonglade"; testSubzone="Nighthaven"
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row.completed==true and row.timestamp==123456)
            testZone="Elwynn Forest"; testSubzone="Goldshire"; C_Map=nil; C_MapExplorationInfo=nil
            row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row.completed==true and row.timestamp==123456 and row.current==1)
            assert(ns.FA.Earned("explore855")==123456 and saved.completionAttribution==nil)
            assert(saved.done.explore855==123456)
        ''')

    def test_verified_completion_attribution_survives_missing_map_api_or_saved_sample(self):
        self.h.execute('''
            testZone="Moonglade"; testSubzone="Nighthaven"
            ns.FA.CheckAll(true)
            local original=saved.done.explore855
            assert(original and ns.FA.CompletionAttribution("explore855"))
            saved.explorationEvidence=nil; C_Map=nil; C_MapExplorationInfo=nil
            testZone="Elwynn Forest"
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row.completed==true and row.timestamp==original and row.current==nil)
            assert(ns.FA.Earned("explore855")==original and saved.done.explore855==original)
        ''')

    def test_copied_foreign_attribution_does_not_validate_an_unbound_character_db(self):
        self.h.execute('''
            testZone="Moonglade"; testSubzone="Nighthaven"; ns.FA.CheckAll(true)
            local previous=ForeverAchievementsCharDB
            local attribution=previous.completionAttribution
            currentName="Fresh"; currentSurname="Character"
            ForeverAchievementsCharDB={done={explore855=previous.done.explore855},tracked={},completionAttribution=attribution}
            testZone="Elwynn Forest"; testSubzone="Goldshire"
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"]
            assert(row.completed==nil and ns.FA.Earned("explore855")==nil)
            assert(ForeverAchievementsCharDB.done.explore855==previous.done.explore855)
            assert(ForeverAchievementsCharDB.completionAttribution==attribution and previous.done.explore855)
        ''')

    def test_malformed_or_secret_attribution_cannot_supply_a_completion(self):
        self.h.execute('''
            saved.done.explore855=123456
            local identity=ns.FA.CharacterIdentity()
            SecretTestValue={}
            local cases={false,1,{},SecretTestValue,
                {completedAt=SecretTestValue,characterKey=identity.key,identity=identity},
                {completedAt=123456,characterKey=SecretTestValue,identity=identity},
                {completedAt=123456,characterKey=identity.key,identity=SecretTestValue}}
            for _,entry in ipairs(cases) do
                saved.completionAttribution={explore855=entry}
                local ok,state=pcall(ns.FA.CompletionStatus,"explore855")
                assert(ok and state==nil and saved.done.explore855==123456)
                assert(ns.CustomAchievementAdapter.Catalog().byKey["custom:explore855"].completed==nil)
            end
            saved.completionAttribution={explore855={completedAt=123456,characterKey=identity.key,
                identity={verified=true,key=identity.key,name=identity.name,realm=identity.realm,guid=SecretTestValue}}}
            assert(ns.FA.CompletionStatus("explore855")==nil and saved.done.explore855==123456)
        ''')

    def test_old_other_zone_and_eastern_kingdoms_history_keep_existing_points(self):
        self.h.execute('''
            saved.done.explore802=120000; saved.done.exploreEK=120100
            assert(ns.FA.Earned("explore802")==120000 and ns.FA.Earned("exploreEK")==120100)
            local c=ns.CustomAchievementAdapter.Catalog()
            assert(c.byKey["custom:explore802"].completed and c.byKey["custom:exploreEK"].completed)
            assert(c.points==35 and c.possiblePoints==120)
            local points,_,done,_,known=ns.FA.TotalPoints()
            assert(points==35 and done==2 and known==true)
        ''')

    def test_dependent_historical_meta_display_waits_for_moonglade_only(self):
        self.h.execute('''
            saved.done.explore855=120000; saved.done.exploreEK=120100
            saved.done.exploreKal=120200; saved.done.worldexplorer=120300
            assert(ns.FA.CompletionStatus("exploreKal")==nil and ns.FA.CompletionStatus("worldexplorer")==nil)
            assert(ns.FA.CompletionStatus("exploreEK")==true)
            local c=ns.CustomAchievementAdapter.Catalog()
            assert(c.byKey["custom:exploreKal"].completed==nil and c.byKey["custom:worldexplorer"].completed==nil)
            assert(c.points==nil and saved.done.worldexplorer==120300)
            testZone="Moonglade"; testSubzone="Nighthaven"
            c=ns.CustomAchievementAdapter.Catalog()
            assert(c.byKey["custom:exploreKal"].completed and c.byKey["custom:worldexplorer"].completed)
            assert(c.byKey["custom:worldexplorer"].timestamp==120300 and c.points==110)
            assert(saved.done.exploreKal==120200 and saved.done.worldexplorer==120300)
        ''')

    def test_world_meta_rename_preserves_key_id_50_points_and_two_continent_conditions(self):
        self.h.execute('''
            local a=ns.FA.BY_KEY.worldexplorer
            assert(a.key=="worldexplorer" and a.id==46 and a.name=="Explore Azeroth" and a.pts==50)
            assert(a.list[1]=="Eastern Kingdoms" and a.list[2]=="Kalimdor")
            assert(ns.FA.BY_KEY.exploreEK.pts==25 and ns.FA.BY_KEY.exploreKal.pts==25)
            for _,z in ipairs(ns.EXPLORE) do
                assert(ns.FA.BY_KEY[z.key or ("explore"..z.id)].pts==10)
            end
            saved.done.exploreEK=120100; saved.done.exploreKal=120200
            assert(a.progress()==nil)
            assert(a.has("Eastern Kingdoms")==true and a.has("Kalimdor")==nil)
            testZone="Moonglade"; testSubzone="Nighthaven"; ns.FA.CheckAll(true); ns.FA.CheckAll(true)
            assert(saved.done.worldexplorer and a.progress()==2)
        ''')

    def test_status_checks_saved_proof_without_map_database_scans(self):
        self.h.execute('''
            saved.done.explore855=120000; testZone="Moonglade"; testSubzone="Nighthaven"
            assert(ns.FA.BY_KEY.explore855.progress()==1)
            C_Map={GetMapInfo=function() error("Completion read must not inspect maps") end,
                GetBestMapForUnit=function() error("Completion read must not inspect unit maps") end}
            C_MapExplorationInfo={GetExploredMapTextures=function() error("Completion read must not scan textures") end}
            ns.FA.WithProgressSnapshot(function()
                for i=1,100 do
                    assert(ns.FA.CompletionStatus("explore855")==true)
                    assert(ns.FA.Earned("explore855")==120000)
                end
            end)
            assert(saved.done.explore855==120000 and saved.completionAttribution==nil)
        ''')

    def test_inspector_exposes_retained_timestamp_and_unverified_reason(self):
        self.h.execute('''
            saved.done.explore855=120000
            ns.FA.SLASH.inspectachievement("explore855")
            local text=messages[#messages]
            assert(text:find("savedCompletionTimestamp=120000",1,true))
            assert(text:find("completionVerified=false",1,true))
            assert(text:find("Historical exploration completion retained",1,true))
            assert(saved.done.explore855==120000 and #calls==0)
        ''')

    def test_combined_native_completion_never_supplies_custom_gold_points_or_recent(self):
        self.h.execute(FIXTURES+'''
            saved.done.explore855=120000
            local a=ns.FA.BY_KEY.explore855
            local n=NativeRow(855,a.name,1)
            n.description=a.desc; n.completed=true; n.scopeType="account"; n.completionScope="native_account"
            n.pointValue=1; n.points=1; n.date="10/10/26"; n.dateSort=20261010
            GetAchievementNumCriteria=function(id) assert(id==855); return 1 end
            GetAchievementCriteriaInfo=function(id,index)
                assert(id==855 and index==1); return "Moonglade",43,true,1,1,nil,0,493,"1 / 1",123,true
            end
            local native=NativeCatalog({NativeCategory(1,"Kalimdor",2),NativeCategory(2,"Exploration")},{n})
            local m=ns.LegacyPresentation.Build(nil,native)
            local card=m.byKey["custom:explore855"]
            assert(card.source=="combined" and m.byKey["legacy:855"]==card)
            assert(card.completed==nil and card.timestamp==nil and card.native.completed==true)
            local summary=ns.LegacyPresentation.Summary(m)
            assert(summary.custom.points==nil and #summary.custom.recent==0)
            assert(summary.native.points==16 and #summary.native.recent==1)
            assert(#ns.LegacyPresentation.Rows(m,"custom","","Completed")==0)
            assert(#ns.LegacyPresentation.Rows(m,"legacy","","Completed")==1)
            assert(saved.done.explore855==120000 and #calls==0)
        ''')

    def test_social_snapshot_preserves_raw_history_and_exports_verification_state(self):
        self.h.load("Social.lua")
        self.h.execute('''
            saved.done.explore855=120000; saved.done.explore802=120100
            assert(ns.FA.SaveCharacter())
            local identity=ns.FA.CharacterIdentity()
            local snapshot=ns.FA.Account().chars[identity.key]
            assert(snapshot.done.explore855==120000 and snapshot.done.explore802==120100)
            assert(snapshot.completionValidationVersion==1)
            assert(snapshot.completionStates.explore855=="unknown" and snapshot.completionStates.explore802=="verified")
            assert(snapshot.pts==nil and snapshot.pointsAvailable==false and snapshot.countAvailable==false)
            assert(saved.done.explore855==120000 and saved.done.explore802==120100)
        ''')

    def test_other_character_snapshot_does_not_republish_unverified_moonglade_history(self):
        self.h.load("Social.lua")
        self.h.execute('''
            saved.done.explore855=120000; saved.done.explore802=120100
            assert(ns.FA.SaveCharacter())
            local account=ns.FA.Account()
            local oldIdentity=ns.FA.CharacterIdentity()
            local snapshot=account.chars[oldIdentity.key]
            currentName="Fresh"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={}}
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(catalog.byKey["custom:explore855"].completedByName==nil)
            assert(catalog.byKey["custom:explore802"].completedByName=="Alt Surname")
            assert(snapshot.done.explore855==120000 and snapshot.done.explore802==120100)
        ''')

    def test_social_snapshot_shares_identity_reads_across_completion_validation(self):
        self.h.load("Social.lua")
        self.h.execute('''
            local names,realms=0,0
            UnitName=function() names=names+1; return currentName,currentSurname end
            GetRealmName=function() realms=realms+1; return currentRealm end
            saved.done.explore855=120000; saved.done.explore802=120100
            assert(ns.FA.SaveCharacter())
            assert(names==1 and realms==1)
            assert(ns.FA.SaveCharacter())
            assert(names==2 and realms==2 and saved.done.explore855==120000)
        ''')


if __name__=="__main__":
    unittest.main()
