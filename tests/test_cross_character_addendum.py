"""Completion provenance and identity-safe account snapshots using Lua 5.1.

The fixtures explicitly report native metadata and switch isolated character
databases. They do not claim live-client testing or identify an incident's cause.
"""
import unittest

from test_iteration3_achievement_classification import AdapterHarness


IDENTITIES = '''
    currentIdentity={key="character:5:Realm:Player-ALT",name="Same",surname="Alt",realm="Realm",guid="Player-ALT",verified=true}
    ns.FA.CharacterIdentity=function() return currentIdentity end
    account={chars={}}
    ns.FA.Account=function() return account end
    function Snapshot(identity,done)
        return {characterKey=identity.key,identityVersion=1,identity=identity,completionScope="character",done=done}
    end
    otherIdentity={key="character:5:Realm:Player-MAIN",name="Same",surname="Main",realm="Realm",guid="Player-MAIN",verified=true}
'''


class CrossCharacterAdapterTests(unittest.TestCase):
    def setUp(self):
        self.h = AdapterHarness()
        self.h.execute(IDENTITIES)

    def check(self, code):
        self.h.execute(code)

    def test_verified_other_character_adds_detail_without_current_completion_or_points(self):
        self.check('''
            settings.accountView=true
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=1731000000})
            local done,history=saved.done,saved.history
            local catalog=ns.CustomAchievementAdapter.Catalog()
            local row=catalog.byKey["custom:second"]
            assert(row.completed==false and row.completionState=="incomplete")
            assert(row.completionScope=="other_character" and row.completedByOtherCharacter==true)
            assert(row.completedOnCurrentCharacter==false and row.nativeAccountCompleted==false)
            assert(row.completionDetail=="Completed by Same Main")
            assert(row.timestamp==nil and row.date==nil and row.completionDate==nil)
            assert(row.points==20 and row.current==7 and row.required==10 and catalog.points==10)
            assert(saved.done==done and saved.history==history and saved.done.second==nil)
            assert(account.chars[otherIdentity.key].done.second==1731000000 and #calls==0)
        ''')

    def test_current_completion_takes_precedence_and_remains_character_scoped(self):
        self.check('''
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{first=1731000000})
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:first"]
            assert(row.completed and row.completedOnCurrentCharacter and not row.completedByOtherCharacter)
            assert(row.completionScope=="current_character" and row.completionDetail=="Completed on this character")
            assert(row.timestamp==1730000000 and row.scopeType=="character" and row.points==10)
        ''')

    def test_untagged_and_mismatched_snapshots_never_identify_another_character(self):
        self.check('''
            local old={name="Same",realm="Realm",done={second=100}}
            account.chars["Same-Realm"]=old
            account.chars.bad=Snapshot(otherIdentity,{second=100})
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            account.chars[otherIdentity.key].characterKey="Wrong identity"
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(row.completionScope=="incomplete" and row.completedByOtherCharacter==false)
            assert(row.completionDetail=="Not completed on this character")
            assert(account.chars["Same-Realm"]==old and old.done.second==100 and #calls==0)
        ''')

    def test_missing_current_identity_prevents_cross_character_inference(self):
        self.check('''
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            for _,identity in ipairs({false,{key="Alt",verified=false},{key="Alt",name="Alt",realm="Realm",verified=true}}) do
                currentIdentity=identity
                local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
                assert(not row.completed and not row.completedByOtherCharacter and row.completionScope=="incomplete")
            end
            ns.FA.CharacterIdentity=function() error("Client identity unavailable") end
            assert(not ns.CustomAchievementAdapter.Catalog().byKey["custom:second"].completedByOtherCharacter)
        ''')

    def test_same_character_guid_and_name_fallback_aliases_are_excluded_without_merging(self):
        self.check('''
            account.chars[currentIdentity.key]=Snapshot(currentIdentity,{second=100})
            local alias={key="character-name:Realm:Same:Alt",name="Same",surname="Alt",realm="Realm",verified=true}
            account.chars[alias.key]=Snapshot(alias,{second=200})
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(not row.completedByOtherCharacter and row.completionScope=="incomplete")
            assert(saved.done.second==nil and account.chars[alias.key].done.second==200)
        ''')

    def test_guid_identity_can_verify_other_characters_without_inventing_missing_surname(self):
        self.check('''
            currentIdentity.surname=nil
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            assert(ns.CustomAchievementAdapter.Catalog().byKey["custom:second"].completionScope=="other_character")
            otherIdentity.guid=nil
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(not row.completedByOtherCharacter and row.completionScope=="incomplete")
            assert(currentIdentity.surname==nil and saved.done.second==nil)
        ''')

    def test_invalid_other_character_history_and_secret_identity_are_not_evidence(self):
        self.check('''
            SecretValue={}
            issecretvalue=function(value) return value==SecretValue end
            local snapshot=Snapshot(otherIdentity,{})
            account.chars[otherIdentity.key]=snapshot
            for _,value in ipairs({0,-1,math.huge,0/0,"100",true,SecretValue}) do
                snapshot.done.second=value
                local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
                assert(row.completionScope=="incomplete" and not row.completedByOtherCharacter)
            end
            snapshot.done.second=100; snapshot.identity=SecretValue
            assert(not ns.CustomAchievementAdapter.Catalog().byKey["custom:second"].completedByOtherCharacter)
            assert(saved.done.second==nil and #calls==0)
        ''')

    def test_malformed_current_completion_stays_unknown_and_preserved(self):
        self.check('''
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            for _,value in ipairs({0,-1,math.huge,0/0,"100",true}) do
                saved.done.second=value
                local catalog=ns.CustomAchievementAdapter.Catalog()
                local row=catalog.byKey["custom:second"]
                assert(row.completed==nil and row.completionScope=="unknown" and row.completedByOtherCharacter==nil)
                assert(row.timestamp==nil and row.date==nil and catalog.points==nil)
                assert(type(saved.done.second)==type(value) and #calls==0)
            end
        ''')

    def test_native_completion_remains_independent_of_custom_and_native_earning_metadata(self):
        self.check('''
            local completed,flags,earned=true,ACHIEVEMENT_FLAGS_ACCOUNT,nil
            GetAchievementInfo=function(id) return id,"Native exploration",0,completed,10,27,24,
                "Description",flags,237388,"", "Do not infer this name",earned end
            local native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed and native.completionScope=="native_account" and native.nativeAccountCompleted)
            assert(native.completedOnCurrentCharacter==nil and native.completedByOtherCharacter==nil)
            assert(native.completionDetail=="Legacy challenge completed account-wide")
            assert(ns.CustomAchievementAdapter.Catalog().byKey["custom:second"].completed==false)
            earned=true; native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed and native.completionScope=="current_character" and native.completedOnCurrentCharacter)
            flags=0; earned=false; native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed and native.completionScope=="other_character" and native.completedByOtherCharacter)
            assert(native.completedOnCurrentCharacter==false and native.nativeAccountCompleted==false)
            earned=nil; native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed and native.completionScope=="unknown" and native.completionDetail=="Completion scope unavailable")
            assert(native.completedOnCurrentCharacter==nil and native.completedByOtherCharacter==nil)
            completed=false; native=ns.LegacyAdapter.Resolve(62053)
            assert(not native.completed and native.completionScope=="incomplete" and not native.completedOnCurrentCharacter)
            completed=nil; earned=true; native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed==nil and native.completionScope=="unknown" and native.completedOnCurrentCharacter==nil)
            assert(saved.done.second==nil and #calls==0)
        ''')

    def test_native_secret_and_non_boolean_earning_metadata_do_not_invent_provenance(self):
        self.check('''
            SecretValue={}; issecretvalue=function(value) return value==SecretValue end
            for _,earned in ipairs({SecretValue,1,"true"}) do
                GetAchievementInfo=function(id) return id,"Native",0,true,10,27,24,"Desc",0,237388,"",true,earned end
                local row=ns.LegacyAdapter.Resolve(62053)
                assert(row.completed and row.completionScope=="unknown" and row.wasEarnedByMe==nil)
                assert(row.completedOnCurrentCharacter==nil and row.completedByOtherCharacter==nil)
            end
            assert(#calls==0)
        ''')


class CharacterSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.h = AdapterHarness()
        self.h.execute(IDENTITIES + '''
            ns.FA.secret=function(value) return SecretValue~=nil and value==SecretValue end
            ns.FA.LINK={}; ns.FA.COMPARE={}; ns.FA.CurrentTitle=function() return nil end
            ns.FA.TotalPoints=function() error("Merged/native totals must not enter character snapshots") end
            UnitClass=function() return "Warrior","WARRIOR" end
            UnitLevel=function() return 21 end
            CreateFrame=function(kind,name,parent) return UIObject(kind,name,parent) end
        ''')
        self.h.load("Social.lua")

    def check(self, code):
        self.h.execute(code)

    def test_two_surnames_and_realms_save_isolated_history_and_character_points(self):
        self.check('''
            local old={name="Same",realm="Realm",done={second=99},pts=999}
            account.chars["Same-Realm"]=old
            settings.accountView=true; saved.done.imported=500
            assert(ns.FA.SaveCharacter())
            local altSnapshot=account.chars[currentIdentity.key]
            assert(altSnapshot.identityVersion==1 and altSnapshot.characterKey==currentIdentity.key)
            assert(altSnapshot.identity.name=="Same" and altSnapshot.surname=="Alt" and altSnapshot.name=="Same Alt")
            assert(altSnapshot.identity.verified and altSnapshot.completionScope=="character")
            assert(altSnapshot.done~=saved.done and altSnapshot.done.first==1730000000 and altSnapshot.done.imported==500)
            assert(altSnapshot.pts==10 and altSnapshot.count==1 and altSnapshot.pointType=="character")
            saved={done={second=1732000000},tracked={},history={"main"}}
            currentIdentity=otherIdentity
            assert(ns.FA.SaveCharacter())
            local mainSnapshot=account.chars[currentIdentity.key]
            assert(mainSnapshot.pts==20 and mainSnapshot.count==1 and mainSnapshot.done.first==nil)
            assert(altSnapshot.done.second==nil and saved.done.second==1732000000)
            assert(account.chars["Same-Realm"]==old and old.done.second==99 and old.pts==999)
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(catalog.byKey["custom:first"].completionScope=="other_character" and catalog.points==20)
            currentIdentity={key="character:11:Other Realm:Player-MAIN",name="Same",surname="Main",realm="Other Realm",guid="Player-MAIN",verified=true}
            saved={done={},tracked={},history={"other realm"}}
            assert(ns.FA.SaveCharacter())
            assert(account.chars[currentIdentity.key].pts==0 and mainSnapshot.pts==20)
            assert(account.chars[otherIdentity.key]==mainSnapshot and #calls==0)
        ''')

    def test_unknown_identity_does_not_overwrite_any_history(self):
        self.check('''
            local old={done={first=100}}
            account.chars["Same-Realm"]=old
            currentIdentity={name="Same",surname="Alt",realm="Realm",verified=false}
            local ok,reason=ns.FA.SaveCharacter()
            assert(ok==false and reason=="Character identity unavailable")
            assert(account.chars["Same-Realm"]==old and account.characterSnapshotArchives==nil)
            local count=0; for _ in pairs(account.chars) do count=count+1 end; assert(count==1)
            SecretValue={}; currentIdentity=SecretValue
            assert(ns.FA.SaveCharacter()==false and saved.done.first==1730000000 and #calls==0)
        ''')

    def test_guid_snapshot_preserves_unavailable_surname_without_losing_reliable_identity(self):
        self.check('''
            currentIdentity.surname=nil
            assert(ns.FA.SaveCharacter())
            local snapshot=account.chars[currentIdentity.key]
            assert(snapshot.identity.guid=="Player-ALT" and snapshot.identity.surname==nil)
            assert(snapshot.name=="Same" and snapshot.surname==nil and snapshot.pts==10)
            currentIdentity={key="Bad",name="Same",realm="Realm",guid="Unavailable",verified=true}
            assert(ns.FA.SaveCharacter()==false and account.chars.Bad==nil and #calls==0)
        ''')

    def test_unexpected_canonical_collision_is_archived_and_snapshot_updates_do_not_merge(self):
        self.check('''
            local old={name="Unknown",done={second=100}}
            account.chars[currentIdentity.key]=old
            assert(ns.FA.SaveCharacter())
            assert(#account.characterSnapshotArchives==1 and account.characterSnapshotArchives[1].snapshot==old)
            assert(old.done.second==100 and account.characterSnapshotArchives[1].key==currentIdentity.key)
            assert(account.chars[currentIdentity.key].done.second==nil)
            saved.done.first=nil; saved.done.second=1732000000
            assert(ns.FA.SaveCharacter())
            local snapshot=account.chars[currentIdentity.key]
            assert(snapshot.done.first==nil and snapshot.done.second==1732000000 and snapshot.pts==20)
            assert(#account.characterSnapshotArchives==1 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_malformed_done_values_are_preserved_without_counting_points(self):
        self.check('''
            saved.done.first=0; saved.done.second="Unreadable historical timestamp"
            assert(ns.FA.SaveCharacter())
            local snapshot=account.chars[currentIdentity.key]
            assert(snapshot.done.first==0 and snapshot.done.second==saved.done.second)
            assert(snapshot.pts==nil and snapshot.count==0 and not snapshot.pointsAvailable and not snapshot.countAvailable)
            ns.FA.BY_KEY.first.pts=nil; saved.done.first=100; saved.done.second=nil
            assert(ns.FA.SaveCharacter())
            snapshot=account.chars[currentIdentity.key]
            assert(snapshot.count==1 and snapshot.pts==nil and not snapshot.pointsAvailable and snapshot.countAvailable)
            assert(saved.done.first==100 and #calls==0)
        ''')


class ActualCoreSnapshotIntegrationTests(unittest.TestCase):
    def test_real_identity_export_and_isolated_character_databases_cooperate_with_adapters(self):
        from test_progression_addendum import CoreHarness

        h = CoreHarness()
        h.load("Integrations/LegacyAdapter.lua")
        h.load("Integrations/CustomAdapter.lua")
        h.load("Social.lua")
        h.execute('''
            SecretTestValue={}
            SelectAchievements("pet1","explore855")
            local surname,guid="Main","Player-MAIN"
            UnitFullName=function() return "Same",surname end
            UnitGUID=function() return guid end
            GetRealmName=function() return "Realm" end
            ForeverAchievementsDB.settings.accountView=true
            ForeverAchievementsCharDB.done={pet1=1731000000}
            assert(ns.FA.SaveCharacter())
            local main=ns.FA.CharacterIdentity()
            local snapshot=ns.FA.Account().chars[main.key]
            assert(snapshot.identityVersion==1 and snapshot.identity.surname=="Main" and snapshot.pts==10)
            surname,guid="Alt","Player-ALT"
            ForeverAchievementsCharDB={done={},tracked={},history={"alt history"}}
            local alt=ns.FA.CharacterIdentity()
            assert(alt.key~=main.key and ns.FA.Earned("pet1")==nil)
            assert(ns.FA.SaveCharacter())
            local catalog=ns.CustomAchievementAdapter.Catalog()
            local pet=catalog.byKey["custom:pet1"]
            assert(pet.completed==false and pet.completionScope=="other_character" and catalog.points==0)
            assert(ns.FA.Account().chars[alt.key].pts==0 and snapshot.done.pet1==1731000000)
            assert(ForeverAchievementsCharDB.done.pet1==nil and ForeverAchievementsCharDB.history[1]=="alt history")
            GetAchievementInfo=function(id) return id,"Explore Azeroth",0,true,10,27,24,"Description",
                ACHIEVEMENT_FLAGS_ACCOUNT,237388,"",nil,false end
            local native=ns.LegacyAdapter.Resolve(62053)
            assert(native.completed and native.completionScope=="native_account" and native.nativeAccountCompleted)
            assert(catalog.byKey["custom:explore855"].completed==false and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
