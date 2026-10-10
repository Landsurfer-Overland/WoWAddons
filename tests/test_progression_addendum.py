"""Actual-core progression regressions for the cross-character addendum.

Only the achievement list exercised by each event is reduced. Definitions,
login/event handlers, storage, and award conditions execute from addon source.
These tests do not assert live-client rendering or in-game behavior.
"""
import unittest

from test_legacy_wrath_ui import Harness


class CoreHarness(Harness):
    def __init__(self):
        super().__init__()
        self.execute('''
            SlashCmdList={}; UISpecialFrames={}; tinsert=table.insert
            testClock=10; currentName="Alt"; currentSurname="Surname"; currentRealm="Realm One"
            function GetTime() return testClock end
            function UnitName() return currentName,currentSurname end
            function GetRealmName() return currentRealm end
            function UnitLevel() return 1 end
            function UnitFactionGroup() return "Alliance" end
            function UnitClass() return "Warrior","WARRIOR" end
            function wipe(t) for k in pairs(t) do t[k]=nil end; return t end
            function issecretvalue(value) return SecretTestValue~=nil and value==SecretTestValue end
            function GetRealZoneText() return testZone end
            function GetZoneText() return testZone end
            function GetSubZoneText() return testSubzone end
            function GetNumCompanions(kind) assert(kind=="CRITTER"); return companionCount end
            C_PetJournal={GetNumPets=function() return 100,accountPetCount end}
            bagItems={}; companionCount=0; accountPetCount=0
            C_Container={
                GetContainerNumSlots=function(bag) return #(bagItems[bag] or {}) end,
                GetContainerItemID=function(bag,slot) return (bagItems[bag] or {})[slot] end,
                GetContainerItemInfo=function(bag,slot)
                    local id=(bagItems[bag] or {})[slot]
                    return id and {itemID=id,stackCount=1}
                end,
            }
            itemClasses={}
            C_Item={GetItemInfoInstant=function(id)
                local info=itemClasses[id] or {15,2}
                return id,"Collection Item",nil,nil,nil,info[1],info[2]
            end}
            GetItemInfoInstant=C_Item.GetItemInfoInstant
            C_Map={GetBestMapForUnit=function() return testZone=="Moonglade" and 1450 or nil end,
              GetMapInfo=function(mapID)
                return mapID==1450 and {mapID=1450,name="Moonglade"} or nil
            end}
            C_Timer.NewTicker=function() return {} end
            ForeverAchievementsCharDB=saved
            ForeverAchievementsDB={chars={},settings={toasts=false,sound=false}}
        ''')
        for path in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua",
                     "DataExtra.lua", "MoneyTracking.lua", "ForeverAchievements.lua"):
            self.load(path)
        self.execute('''
            -- Keep the exact production definitions/closure-held ALL table;
            -- unrelated achievements need no fabricated WoW API answers.
            function SelectAchievements(...)
                local wanted={}
                for _,key in ipairs({...}) do wanted[key]=true end
                for i=#ns.FA.ALL,1,-1 do
                    if not wanted[ns.FA.ALL[i].key] then table.remove(ns.FA.ALL,i) end
                end
            end
            function CoreEvent(event,...)
                for _,frame in ipairs(frames) do
                    if frame.events and frame.events[event] and frame:GetScript("OnEvent") then
                        frame:Fire("OnEvent",event,...)
                    end
                end
            end
            timers={}
        ''')


class PetOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('SelectAchievements("pet1","pet15")')

    def test_account_journal_and_stale_best_do_not_award_a_fresh_character(self):
        self.h.execute('''
            accountPetCount=15; companionCount=0; saved.petsBest=15
            local done,history=saved.done,saved.history
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.pet1==nil and saved.done.pet15==nil)
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==0 and need==15)
            assert(saved.done==done and saved.history==history and saved.history[1]=="keep")
            assert(saved.done.first==1730000000 and saved.petsBest==15 and #calls==0)
        ''')

    def test_ambiguous_companion_api_does_not_become_character_specific_login_proof(self):
        self.h.execute('''
            companionCount=15; accountPetCount=99
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.pet1==nil and saved.done.pet15==nil)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_current_character_bag_evidence_counts_unique_companion_items(self):
        self.h.execute('''
            GetNumCompanions=nil; C_PetJournal.GetNumPets=function() error("Account journal unavailable") end
            bagItems[0]={12345,12345}; bagItems[1]={12345}
            ns.FA.CheckAll(true)
            assert(saved.done.pet1 and saved.done.pet15==nil)
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==1 and need==15 and #calls==0)
        ''')

    def test_verified_pet_item_history_survives_bag_removal_without_leaking_to_an_alt(self):
        self.h.execute('''
            bagItems[0]={12345}
            ns.FA.CheckAll(true)
            local originalDB=ForeverAchievementsCharDB
            local completedAt=originalDB.done.pet1
            assert(completedAt)
            bagItems={}
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==1 and need==15 and originalDB.done.pet1==completedAt)
            currentName="Other"; currentSurname="Character"
            ForeverAchievementsCharDB={done={},tracked={},history={"other"},explored={}}
            ns.FA.CheckAll(true)
            current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==0 and need==15 and ForeverAchievementsCharDB.done.pet1==nil)
            assert(originalDB.done.pet1==completedAt and originalDB.history[1]=="keep" and #calls==0)
        ''')

    def test_unknown_or_malformed_ownership_never_awards_or_erases_previous_completion(self):
        self.h.execute('''
            saved.done.pet1=112233
            saved.petsBest=99
            GetNumCompanions=function() error("Character collection unavailable") end
            C_Container.GetContainerNumSlots=function() error("Bag data unavailable") end
            C_PetJournal.GetNumPets=function() return 100,99 end
            ns.FA.CheckAll(true)
            assert(saved.done.pet1==112233 and saved.done.pet15==nil)
            local current,need=ns.FA.BY_KEY.pet15.progress()
            assert(current==nil and need==15)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_invalid_character_companion_counts_never_become_completion(self):
        self.h.execute('''
            accountPetCount=15
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret value conversion") end})
            for _,value in ipairs({-1,math.huge,0/0,"15",true,SecretTestValue}) do
                companionCount=value
                ns.FA.CheckAll(true)
                assert(saved.done.pet1==nil and saved.done.pet15==nil)
            end
            companionCount=nil
            ns.FA.CheckAll(true)
            assert(saved.done.pet1==nil and saved.done.pet15==nil and #calls==0)
        ''')


class ExplorationTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("explore855")
            testZone="Moonglade"; testSubzone="Moonglade"
            C_MapExplorationInfo=nil
        ''')

    def test_zone_entry_and_login_do_not_complete_moonglades_single_criterion(self):
        self.h.execute('''
            assert(ns.FA.BY_KEY.explore855.id==855)
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            CoreEvent("ZONE_CHANGED_NEW_AREA"); FlushTimers()
            assert(saved.done.explore855==nil)
            local current,need=ns.FA.BY_KEY.explore855.progress()
            assert(current==nil or current<need)
            assert(saved.explored.zone.old and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_matching_current_character_overlay_positively_verifies_moonglade(self):
        self.h.execute('''
            C_MapExplorationInfo={GetExploredMapTextures=function(mapID)
                assert(mapID==1450)
                return {{offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=false}}
            end}
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.explore855 and ns.FA.BY_KEY.explore855.has("Moonglade"))
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_malformed_and_mismatched_overlay_samples_do_not_complete(self):
        self.h.execute('''
            C_MapExplorationInfo={GetExploredMapTextures=function(mapID)
                assert(mapID==1450)
                return {{},{offsetX=244},{offsetY=89},{offsetX=244,offsetY=math.huge},
                        {offsetX=244,offsetY=0/0},{offsetX=100,offsetY=100},
                        {offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=true}}
            end}
            ns.FA.CheckAll(true)
            assert(saved.done.explore855==nil and saved.explored.zone.old and #calls==0)
        ''')

    def test_legacy_zone_presence_flags_are_preserved_without_becoming_new_completion(self):
        self.h.execute('''
            saved.explored.explore855={Moonglade=true}
            saved.explored[855]={Moonglade=true}
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.explore855==nil)
            assert(saved.explored.explore855.Moonglade and saved.explored[855].Moonglade)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_secret_hover_flag_cannot_be_treated_as_genuine_revealed_map_data(self):
        self.h.execute('''
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret hover conversion") end})
            C_MapExplorationInfo={GetExploredMapTextures=function(mapID)
                assert(mapID==1450)
                return {{offsetX=244,offsetY=89,textureWidth=512,textureHeight=512,isShownByMouseOver=SecretTestValue}}
            end}
            ns.FA.CheckAll(true)
            assert(saved.done.explore855==nil and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_exploration_api_failure_preserves_existing_completion_and_legacy_subzone_evidence(self):
        self.h.execute('''
            saved.done.explore855=123456
            saved.explored[855]={Moonglade=true}
            C_MapExplorationInfo={GetExploredMapTextures=function() error("Map unavailable") end}
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.explore855==123456 and saved.explored[855].Moonglade)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_dynamic_map_proof_survives_reload_with_map_apis_unavailable(self):
        self.h.execute('''
            Enum={UIMapType={Zone=3}}
            C_Map={
                GetBestMapForUnit=function(unit) assert(unit=="player"); return 9450 end,
                GetMapInfo=function(mapID)
                    if mapID==1450 then return {mapID=1450,name="Wrong authored-map zone"} end
                    if mapID==9450 then return {mapID=9450,name="Moonglade",parentMapID=9000} end
                    if mapID==9000 then return {mapID=9000,name="World",parentMapID=0} end
                end,
                GetMapChildrenInfo=function(mapID,mapType,recursive)
                    assert(mapID==9000 and mapType==3 and recursive)
                    return {{mapID=9450,name="Moonglade"}}
                end,
            }
            C_MapExplorationInfo={GetExploredMapTextures=function(mapID)
                assert(mapID==9450)
                return {{offsetX=245,offsetY=88,textureWidth=256,textureHeight=128,isShownByMouseOver=false}}
            end}
            local current,needed=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and needed==1 and saved.done.explore855==nil)
            local proof=saved.explorationEvidence.explore855.Moonglade
            assert(proof.kind=="revealed-map-overlay" and proof.verified)
            assert(proof.mapID==9450 and proof.zoneName=="Moonglade")
            assert(proof.offsetX==244 and proof.offsetY==89 and proof.observedOffsetX==245 and proof.observedOffsetY==88)
            assert(proof.textureWidth==256 and proof.textureHeight==128)
            C_Map=nil; C_MapExplorationInfo=nil
        ''')
        self.h.load("ForeverAchievements.lua")
        self.h.execute('''
            SelectAchievements("explore855"); timers={}
            local current,needed=ns.FA.BY_KEY.explore855.progress()
            assert(current==1 and needed==1 and ns.FA.BY_KEY.explore855.has("Moonglade")==true)
            ns.FA.CheckAll(true)
            assert(ns.FA.Earned("explore855") and saved.explorationEvidence.explore855.Moonglade.mapID==9450)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_saved_overlay_proof_requires_the_verified_zone_name(self):
        self.h.execute('''
            C_Map=nil; C_MapExplorationInfo=nil
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret saved zone conversion") end})
            for _,case in ipairs({{name="Felwood"},{name=""},{},{name=false},{name=true},{name=SecretTestValue}}) do
                local proof={kind="revealed-map-overlay",verified=true,mapID=9450,zoneName=case.name,
                    offsetX=244,offsetY=89,textureWidth=256,textureHeight=128}
                saved.explorationEvidence={explore855={Moonglade=proof}}
                local current,needed=ns.FA.BY_KEY.explore855.progress()
                assert(current==nil and needed==1 and ns.FA.BY_KEY.explore855.has("Moonglade")==nil)
                ns.FA.CheckAll(true)
                assert(saved.done.explore855==nil and saved.explorationEvidence.explore855.Moonglade==proof)
            end
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_saved_overlay_proof_rejects_unknown_dimensions_and_malformed_map_ids(self):
        self.h.execute('''
            C_Map=nil; C_MapExplorationInfo=nil
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret saved map conversion") end})
            local invalid={{},{value=0},{value=-1},{value=math.huge},{value=0/0},{value="9450"},
                {value=false},{value=true},{value={}},{value=SecretTestValue},{value=1.5,mapOnly=true}}
            for _,field in ipairs({"mapID","textureWidth","textureHeight"}) do
                for _,case in ipairs(invalid) do
                    if not case.mapOnly or field=="mapID" then
                        local proof={kind="revealed-map-overlay",verified=true,mapID=9450,zoneName="Moonglade",
                            offsetX=244,offsetY=89,textureWidth=256,textureHeight=128}
                        proof[field]=case.value
                        saved.explorationEvidence={explore855={Moonglade=proof}}
                        local current,needed=ns.FA.BY_KEY.explore855.progress()
                        assert(current==nil and needed==1)
                        ns.FA.CheckAll(true)
                        assert(saved.done.explore855==nil and saved.explorationEvidence.explore855.Moonglade==proof)
                    end
                end
            end
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


class CharacterScopeTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('SelectAchievements("pet1","explore855")')

    def test_account_view_never_changes_current_character_completion_or_points(self):
        self.h.execute('''
            local account=ns.FA.Account()
            account.chars["Main-Realm One"]={name="Main",realm="Realm One",done={pet1=123456,explore855=123457}}
            local snapshot=account.chars["Main-Realm One"]
            ns.FA.Settings().accountView=true
            assert(ns.FA.Earned("pet1")==nil and ns.FA.Earned("explore855")==nil)
            local points,possible,count=ns.FA.TotalPoints()
            assert(points==0 and possible==20 and count==0)
            assert(saved.done.pet1==nil and saved.done.explore855==nil)
            assert(snapshot.done.pet1==123456 and snapshot.done.explore855==123457)
            saved.done.pet1=234567
            assert(ns.FA.Earned("pet1")==234567)
            points,possible,count=ns.FA.TotalPoints()
            assert(points==10 and possible==20 and count==1)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_switching_same_name_on_different_realms_uses_the_loaded_character_db(self):
        self.h.execute('''
            ns.FA.Settings().accountView=true
            saved.done.pet1=345678
            ns.FA.Account().chars["Alt-Realm One"]={name="Alt",realm="Realm One",done={pet1=345678}}
            local previousDB=ForeverAchievementsCharDB
            currentRealm="Realm Two"
            ForeverAchievementsCharDB={done={},tracked={},history={"alt history"},explored={}}
            assert(ns.FA.Earned("pet1")==nil and ns.FA.Earned("explore855")==nil)
            ns.FA.CheckAll(true)
            assert(ForeverAchievementsCharDB.done.pet1==nil and ForeverAchievementsCharDB.done.explore855==nil)
            assert(ForeverAchievementsCharDB.history[1]=="alt history")
            assert(previousDB.done.pet1==345678 and previousDB.done.first==1730000000)
            assert(ns.FA.Account().chars["Alt-Realm One"].done.pet1==345678 and #calls==0)
            currentRealm="Realm One"; ForeverAchievementsCharDB=previousDB
            assert(ns.FA.Earned("pet1")==345678)
        ''')

    def test_malformed_completion_records_are_preserved_without_counting_as_earned(self):
        self.h.execute('''
            for _,value in ipairs({0,-1,math.huge,0/0,"123456",true,{}}) do
                saved.done.pet1=value
                assert(ns.FA.Earned("pet1")==nil)
                local points,_,count=ns.FA.TotalPoints()
                assert(points==0 and count==0)
                assert(saved.done.pet1==value or value~=value)
            end
            saved.done.pet1=567890
            assert(ns.FA.Earned("pet1")==567890 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_character_identity_keeps_surname_and_realm_distinct_and_rejects_unknowns(self):
        self.h.execute('''
            local first=ns.FA.CharacterIdentity()
            assert(type(first)=="table" and type(first.key)=="string" and first.name=="Alt")
            assert(first.surname=="Surname" and first.realm=="Realm One")
            currentRealm="Realm Two"
            local otherRealm=ns.FA.CharacterIdentity()
            assert(otherRealm.key~=first.key and otherRealm.realm=="Realm Two")
            currentRealm="Realm One"; currentSurname="Other Surname"
            assert(ns.FA.CharacterIdentity().key~=first.key)
            currentSurname="Surname"; currentName=nil
            assert(ns.FA.CharacterIdentity()==nil)
            currentName="Alt"; GetRealmName=function() error("Realm unavailable") end
            assert(ns.FA.CharacterIdentity()==nil and saved.done.first==1730000000 and #calls==0)
        ''')


class MetaCompletionTests(unittest.TestCase):
    def setUp(self):
        self.h=CoreHarness()
        self.h.execute('''
            SelectAchievements("loremaster","exploreEK","exploreKal","worldexplorer")
            function SaveContinentChildren(key,timestamp)
                local meta=ns.FA.BY_KEY[key]
                for _,name in ipairs(meta.list) do
                    local child=ns.FA.ZONE_ACH[name]
                    assert(child)
                    saved.done[child.key]=timestamp
                end
            end
        ''')

    def test_malformed_child_completions_cannot_unlock_character_metas(self):
        self.h.execute('''
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret meta timestamp conversion") end})
            local firstName=ns.FA.BY_KEY.exploreEK.list[1]
            local firstKey=ns.FA.ZONE_ACH[firstName].key
            for _,value in ipairs({0,-1,true,false,"123456",{},math.huge,0/0,SecretTestValue}) do
                SaveContinentChildren("exploreEK",123456)
                saved.done[firstKey]=value
                saved.done.exploreEK=nil; saved.done.exploreKal=value
                saved.done.worldexplorer=nil; saved.done.loremaster=nil
                saved.done.loreEK=123456; saved.done.loreKal=value
                for _,key in ipairs({"loremaster","exploreEK","worldexplorer"}) do
                    local current,needed=ns.FA.BY_KEY[key].progress()
                    assert(current==nil and needed>0)
                end
                ns.FA.CheckAll(true)
                assert(saved.done.loremaster==nil and saved.done.exploreEK==nil and saved.done.worldexplorer==nil)
                assert(saved.done[firstKey]==value or value~=value)
            end
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_genuine_saved_child_completions_still_unlock_metas_with_unavailable_apis(self):
        self.h.execute('''
            SaveContinentChildren("exploreEK",123456)
            SaveContinentChildren("exploreKal",234567)
            -- This fixture represents genuine history, including the owning
            -- character's Moonglade attribution introduced in Iteration 4.
            assert(ns.FA.CompletionStatus("explore855")==nil)
            local identity=ns.FA.CharacterIdentity()
            saved.completionAttribution={explore855={completedAt=saved.done.explore855,
                characterKey=identity.key,identity=identity,version=1}}
            assert(ns.FA.CompletionStatus("explore855")==true)
            saved.done.loreEK=345678; saved.done.loreKal=456789
            GetStatistic=nil; C_QuestLog=nil; GetQuestsCompleted=nil
            C_Map=nil; C_MapExplorationInfo=nil
            ns.FA.CheckAll(true)
            for _,key in ipairs({"loremaster","exploreEK","exploreKal","worldexplorer"}) do
                assert(ns.FA.Earned(key))
                local current,needed=ns.FA.BY_KEY[key].progress()
                assert(current==needed and needed>0)
            end
            local points,possible,count=ns.FA.TotalPoints()
            assert(points==110 and possible==110 and count==4)
            assert(saved.done.loreEK==345678 and saved.done.loreKal==456789)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_meta_details_keep_eastern_kingdoms_and_kalimdor_completion_independent(self):
        self.h.execute('''
            local world,lore=ns.FA.BY_KEY.worldexplorer,ns.FA.BY_KEY.loremaster
            saved.done.exploreEK=123456; saved.done.exploreKal=nil
            saved.done.loreEK=234567; saved.done.loreKal=nil
            assert(world.has("Eastern Kingdoms")==true and world.has("Kalimdor")==false)
            assert(lore.has("Loremaster of Eastern Kingdoms")==true and lore.has("Loremaster of Kalimdor")==false)
            local current,needed=world.progress()
            assert(current==1 and needed==2)
            saved.done.exploreKal=true; saved.done.loreKal=0
            assert(world.has("Kalimdor")==nil and lore.has("Loremaster of Kalimdor")==nil)
            current,needed=world.progress()
            assert(current==nil and needed==2)
            saved.done.exploreKal=345678; saved.done.loreKal=456789
            assert(world.has("Kalimdor")==nil)
            saved.done.explore855=345600
            local identity=ns.FA.CharacterIdentity()
            saved.completionAttribution={explore855={completedAt=saved.done.explore855,
                characterKey=identity.key,identity=identity,version=1}}
            assert(world.has("Kalimdor")==true and lore.has("Loremaster of Kalimdor")==true)
            local continent=ns.FA.BY_KEY.exploreEK
            local first,second=continent.list[1],continent.list[2]
            saved.done[ns.FA.ZONE_ACH[first].key]=567890
            saved.done[ns.FA.ZONE_ACH[second].key]=nil
            assert(continent.has(first)==true and continent.has(second)==false)
            saved.done[ns.FA.ZONE_ACH[second].key]={}
            assert(continent.has(second)==nil)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


class MountOwnershipTests(unittest.TestCase):
    def test_account_collection_and_unproven_best_never_grant_character_mount_achievement(self):
        h=CoreHarness()
        h.execute('''
            SelectAchievements("mount10")
            saved.mountsBest=100
            C_MountJournal={
                GetMountIDs=function() return {1,2,3,4,5,6,7,8,9,10} end,
                GetMountInfoByID=function() return nil,nil,nil,nil,nil,nil,nil,nil,nil,nil,true end,
            }
            GetNumCompanions=function() return 100 end
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.mount10==nil and saved.mountsBest==100)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


class FallVerificationTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("fall")
            for _,frame in ipairs(frames) do
                if frame:GetScript("OnUpdate") then fallFrame=frame end
            end
            assert(fallFrame)
            function IsFalling() return fallingValue end
            function UnitIsDeadOrGhost() return deadValue end
            function IsFlying() return false end
            function UnitOnTaxi() return false end
            function IsSwimming() return false end
            function TickFall(t,falling,dead)
                testClock=t; fallingValue=falling; deadValue=dead
                fallFrame:Fire("OnUpdate",.1)
            end
        ''')

    def test_elapsed_falling_without_verified_distance_cannot_award(self):
        self.h.execute('''
            UnitPosition=nil
            TickFall(10,true,false)
            TickFall(13,false,false)
            FlushTimers()
            assert(saved.done.fall==nil and not saved.fall)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_unknown_landing_and_survival_samples_cannot_be_truthiness_checks(self):
        self.h.execute('''
            function UnitPosition() return 1,2,testZ,1 end
            testZ=100; TickFall(9,false,false); TickFall(10,true,false)
            testZ=0; TickFall(13,nil,nil)
            FlushTimers()
            assert(saved.done.fall==nil and not saved.fall)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_invalid_timestamp_and_death_data_never_award_or_erase_history(self):
        self.h.execute('''
            function UnitPosition() return 1,2,testZ,1 end
            testZ=100; TickFall(9,false,false); TickFall(10,true,false)
            testZ=0; TickFall(math.huge,false,true)
            FlushTimers()
            assert(saved.done.fall==nil and not saved.fall)
            saved.done.fall=456789; saved.fall=true
            TickFall(20,true,false)
            TickFall(23,false,nil)
            FlushTimers()
            assert(saved.done.fall==456789 and saved.fall==true and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_old_unverified_fall_boolean_cannot_create_a_new_completion(self):
        self.h.execute('''
            saved.fall=true
            ns.FA.CheckAll(true)
            assert(saved.done.fall==nil and saved.fall==true)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("pet1","explore855")
            saved.done.pet1=123456; saved.done.explore855=234567
            ns.FA.Account().chars["another-character"]={name="Other",realm="Realm One",done={pet1=345678}}
            function PreviewCorrection(key)
                ns.FA.SLASH.correctachievement(key)
                local pending=ns.FA.ProgressionDiagnostics.PendingCorrection()
                local token=type(pending)=="table" and pending.token or pending
                assert(type(token)=="string" and token~="")
                return token
            end
        ''')

    def test_preview_inspection_and_wrong_confirmation_never_delete_progress(self):
        self.h.execute('''
            local db,done,history=ForeverAchievementsCharDB,saved.done,saved.history
            ns.FA.SLASH.inspectachievement("pet1")
            local token=PreviewCorrection("pet1")
            ns.FA.SLASH.correctachievement("pet1 confirm WRONG_TOKEN")
            ns.FA.SLASH.correctachievement("explore855 confirm "..token)
            assert(ForeverAchievementsCharDB==db and saved.done==done and saved.history==history)
            assert(saved.done.pet1==123456 and saved.done.explore855==234567)
            assert(ns.FA.Account().chars["another-character"].done.pet1==345678 and #calls==0)
        ''')

    def test_confirmed_correction_is_limited_to_the_target_on_the_current_character(self):
        self.h.execute('''
            local token=PreviewCorrection("pet1")
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==nil and saved.done.explore855==234567)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and saved.explored.zone.old)
            assert(ns.FA.Account().chars["another-character"].done.pet1==345678)
            ns.FA.CheckAll(true)
            assert(saved.done.pet1==nil and saved.done.explore855==234567 and #calls==0)
            saved.done.pet1=987654
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==987654)
        ''')

    def test_confirmation_bound_to_original_timestamp_cannot_remove_new_completion(self):
        self.h.execute('''
            local token=PreviewCorrection("pet1")
            saved.done.pet1=987654
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==987654 and saved.done.explore855==234567)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_confirmation_is_bound_to_character_identity_and_expires(self):
        self.h.execute('''
            local token=PreviewCorrection("pet1")
            currentRealm="Realm Two"
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==123456)
            currentRealm="Realm One"
            token=PreviewCorrection("pet1")
            testClock=testClock+61
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==123456 and saved.done.explore855==234567)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_correction_hold_preserves_source_evidence_until_separately_confirmed_resume(self):
        self.h.execute('''
            bagItems[0]={12345}
            ns.FA.BY_KEY.pet1.progress() -- observe actual current-character acquisition
            bagItems={}
            local evidence=saved.characterPetItems
            local token=PreviewCorrection("pet1")
            local copy=ns.FA.ProgressionDiagnostics.PendingCorrection()
            copy.token="changed by caller"; copy.key="explore855"
            ns.FA.SLASH.correctachievement("pet1 confirm "..token)
            assert(saved.done.pet1==nil and saved.completionCorrections.pet1)
            assert(saved.characterPetItems==evidence and evidence[12345])
            assert(saved.correctionHistory[1].key=="pet1" and saved.correctionHistory[1].completion==123456)
            assert(saved.correctionHistory[1].characterKey==ns.FA.CharacterIdentity().key)
            CoreEvent("BAG_UPDATE_DELAYED"); ns.FA.CheckAll(true)
            assert(saved.done.pet1==nil and saved.completionCorrections.pet1)
            ns.FA.SLASH.correctachievement("pet1 resume")
            local pending=ns.FA.ProgressionDiagnostics.PendingCorrection()
            assert(pending.action=="resume" and pending.token~=token)
            ns.FA.SLASH.correctachievement("pet1 resume confirm "..token)
            ns.FA.CheckAll(true)
            assert(saved.done.pet1==nil and saved.completionCorrections.pet1)
            ns.FA.SLASH.correctachievement("pet1 resume confirm "..pending.token)
            assert(saved.completionCorrections.pet1==nil and saved.done.pet1==nil)
            ns.FA.CheckAll(true)
            assert(saved.done.pet1 and saved.characterPetItems==evidence and evidence[12345])
            assert(#saved.correctionHistory==2 and saved.correctionHistory[2].action=="resume")
            assert(saved.done.explore855==234567 and saved.done.first==1730000000)
            assert(saved.history[1]=="keep" and ns.FA.Account().chars["another-character"].done.pet1==345678 and #calls==0)
        ''')

    def test_unknown_identity_unknown_key_and_broad_reset_cannot_clear_saved_data(self):
        self.h.execute('''
            local db,done,history=ForeverAchievementsCharDB,saved.done,saved.history
            ns.FA.SLASH.correctachievement("does-not-exist")
            currentName=nil
            ns.FA.SLASH.correctachievement("pet1")
            SlashCmdList.FOREVERACHIEVEMENTS("reset")
            assert(ForeverAchievementsCharDB==db and saved.done==done and saved.history==history)
            assert(saved.done.pet1==123456 and saved.done.explore855==234567 and saved.done.first==1730000000)
            assert(saved.history[1]=="keep" and saved.explored.zone.old and #calls==0)
        ''')


class AwardDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("pet1")
            function ReportContains(value,wanted,seen)
                if type(value)=="string" and type(wanted)=="string" then
                    return value:find(wanted,1,true)~=nil
                end
                if type(value)~="table" then return value==wanted end
                seen=seen or {}
                if seen[value] then return false end
                seen[value]=true
                for _,entry in pairs(value) do
                    if ReportContains(entry,wanted,seen) then return true end
                end
                return false
            end
        ''')

    def test_default_off_does_not_retain_award_diagnostics(self):
        self.h.execute('''
            assert(#ns.FA.ProgressionDiagnostics.records==0)
            bagItems[0]={12345}
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            assert(saved.done.pet1 and #ns.FA.ProgressionDiagnostics.records==0)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_enabled_diagnostic_preserves_event_character_and_positive_condition_evidence(self):
        self.h.execute('''
            ns.FA.SLASH.progressdebug("on")
            bagItems[0]={12345}
            CoreEvent("PLAYER_LOGIN"); FlushTimers()
            local records=ns.FA.ProgressionDiagnostics.records
            assert(saved.done.pet1 and #records>0)
            local award
            for _,record in ipairs(records) do if record.key=="pet1" and record.awarded then award=record end end
            assert(award and ReportContains(award,"PLAYER_LOGIN"))
            assert(ReportContains(award,"Alt") and ReportContains(award,"Surname") and ReportContains(award,"Realm One"))
            assert(ReportContains(award,"current-character companion items"))
            assert(award.current==1 and award.required==1 and award.progressKnown)
            assert(type(award.condition)=="string" and award.condition:find(">=",1,true))
            assert(award.characterKey==ns.FA.CharacterIdentity().key)
            local before=#records
            ns.FA.SLASH.progressdebug("off")
            saved.done.pet1=nil
            ns.FA.CheckAll(true)
            assert(saved.done.pet1 and #records==before and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_enabled_diagnostics_handle_secret_unavailable_observations_safely(self):
        self.h.execute('''
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret diagnostic conversion") end})
            C_Container.GetContainerNumSlots=function() return SecretTestValue end
            ns.FA.SLASH.progressdebug("on")
            ns.FA.CheckAll(true)
            ns.FA.SLASH.inspectachievement("pet1")
            assert(saved.done.pet1==nil and saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_diagnostic_history_is_bounded_and_retains_the_latest_observation(self):
        self.h.execute('''
            ns.FA.SLASH.progressdebug("on")
            for i=1,80 do ns.FA.CheckAll(true,"DIAGNOSTIC_SAMPLE_"..i) end
            local records=ns.FA.ProgressionDiagnostics.records
            assert(#records==64 and records[#records].event=="DIAGNOSTIC_SAMPLE_80")
            assert(records[#records].current==0 and records[#records].required==1)
            assert(not records[#records].awarded and saved.done.pet1==nil)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
