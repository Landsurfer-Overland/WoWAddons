"""Identity-aware catalog and named historical indicators, using actual Lua 5.1.

These are controlled storage/API fixtures; live login and disk persistence still
need the documented two-character client check.
"""
import unittest

from test_cross_character_addendum import IDENTITIES
from test_iteration3_achievement_classification import AdapterHarness


class Iteration4CharacterAdapterTests(unittest.TestCase):
    def setUp(self):
        self.h = AdapterHarness()
        self.h.execute(IDENTITIES)

    def test_other_character_names_are_actual_sorted_and_never_award_current_points(self):
        self.h.execute('''
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            local another={key="character:5:Realm:Player-THIRD",name="Aldrin",surname="Oak",
                realm="Realm",guid="Player-THIRD",verified=true}
            account.chars[another.key]=Snapshot(another,{second=200})
            local catalog=ns.CustomAchievementAdapter.Catalog()
            local row=catalog.byKey["custom:second"]
            assert(row.completed==false and row.completedOnCurrentCharacter==false)
            assert(row.completionDetail=="Completed by Aldrin Oak")
            assert(row.completedByName=="Aldrin Oak" and #row.completedByNames==2)
            assert(row.completedByNames[2]=="Same Main" and catalog.points==10)
            assert(saved.done.second==nil and row.timestamp==nil and #calls==0)
        ''')

    def test_cross_realm_names_disambiguate_without_fabricating_surnames(self):
        self.h.execute('''
            otherIdentity.realm="Other Realm"; otherIdentity.surname=nil
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(row.completedByName=="Same @ Other Realm")
            assert(row.completionDetail=="Completed by Same @ Other Realm" and not row.completed)
            assert(otherIdentity.surname==nil and saved.done.second==nil)
        ''')

    def test_known_current_completion_stays_gold_eligible_with_independent_history(self):
        self.h.execute('''
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{first=200})
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:first"]
            assert(row.completed==true and row.completedOnCurrentCharacter==true)
            assert(row.completionScope=="current_character" and row.completedByOtherCharacter==false)
            assert(row.completedByName=="Same Main" and row.timestamp==1730000000)
            assert(saved.done.first==1730000000 and row.nativeAccountCompleted==false)
        ''')

    def test_ambiguous_unattributed_account_history_never_supplies_names(self):
        self.h.execute('''
            account.chars.old={name="Aldrin",done={second=100},realm="Realm"}
            account.chars[otherIdentity.key]=Snapshot(otherIdentity,{second=100})
            account.chars[otherIdentity.key].identityVersion=nil
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(row.completedByName==nil and row.completedByNames==nil)
            assert(row.completedByOtherCharacter==false and not row.completed)
            assert(account.chars.old.done.second==100 and saved.done.second==nil)
        ''')

    def test_identity_mismatch_hides_current_authority_without_changing_history_or_reading_progress(self):
        self.h.execute('''
            ns.LAR.CharacterScope=function() return nil end
            ns.LAR.BY_KEY.first.progress=function() error("Foreign database must not be evaluated") end
            ns.LAR.BY_KEY.second.progress=function() error("Foreign database must not be evaluated") end
            local original=saved.done
            local catalog=ns.CustomAchievementAdapter.Catalog()
            local row=catalog.byKey["custom:first"]
            assert(row.completed==nil and row.completionState=="unknown")
            assert(row.current==nil and row.timestamp==nil and catalog.points==nil)
            assert(saved.done==original and saved.done.first==1730000000 and saved.history[1]=="keep")
            local criteria=ns.CustomAchievementAdapter.Criteria(row)
            assert(not criteria.available and criteria.count==0 and #calls==0)
        ''')

    def test_scope_recovers_on_new_catalog_and_keeps_criterion_evaluation_read_only(self):
        self.h.execute('''
            local scope=nil
            ns.LAR.CharacterScope=function() return scope end
            assert(ns.CustomAchievementAdapter.Catalog().byKey["custom:first"].completed==nil)
            scope=true
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:first"]
            assert(row.completed and row.current==1 and row.required==2)
            assert(ns.CustomAchievementAdapter.Criteria(row).items[1].completed==true)
            assert(saved.done.first==1730000000 and #calls==0)
        ''')

    def test_exploration_metadata_keeps_reference_ids_maps_and_saved_keys_independent(self):
        self.h.execute('''
            ns.EXPLORE={{id=802,map=1436,zone="Westfall",cont="ek",areas={{"Sentinel Hill",1,2}}}}
            local a=ns.LAR.BY_KEY.second
            a.key="explore802"; a.id=802; a.name="Explore Westfall"
            ns.LAR.CATEGORIES={{key="exploration",label="Exploration"}}
            ns.LAR.CATEGORY_ORDER={"exploration"}
            ns.LAR.CATEGORY_SECTIONS.exploration={{title="EASTERN KINGDOMS",list={a}}}
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:explore802"]
            assert(row.savedKey=="explore802" and row.source=="custom" and row.completed==false)
            assert(row.exploration.zoneID==802 and row.exploration.mapID==1436)
            assert(row.exploration.areaCount==1 and row.exploration.kind=="zone")
            assert(row.exploration.zoneName=="Westfall" and row.exploration.continent=="ek")
            assert(row.key~="legacy:802" and row.points==20 and saved.done.explore802==nil)
        ''')

    def test_unsupported_money_keeps_units_notice_and_never_fabricates_zero(self):
        self.h.execute('''
            local a=ns.LAR.BY_KEY.second
            a.money=true; a.moneyMetric="quest"
            a.progress=function() return nil,1000000,"Unavailable lifetime quest earnings (100g target)" end
            local row=ns.CustomAchievementAdapter.Catalog().byKey["custom:second"]
            assert(row.money and row.moneyMetric=="quest" and row.current==nil and row.required==1000000)
            assert(not row.progress.available and row.completed==false)
            local criteria=ns.CustomAchievementAdapter.Criteria(row)
            assert(not criteria.available and #criteria.items==1 and criteria.items[1].current==nil)
            assert(criteria.items[1].quantityText==row.quantityText and saved.done.second==nil)
        ''')


class Iteration4SnapshotGuardTests(unittest.TestCase):
    def test_ambiguous_database_cannot_overwrite_known_account_snapshot(self):
        h = AdapterHarness()
        h.execute(IDENTITIES + '''
            ns.LAR.secret=function() return false end
            ns.LAR.LINK={}; ns.LAR.COMPARE={}; ns.LAR.CurrentTitle=function() return nil end
            UnitClass=function() return "Warrior","WARRIOR" end
            UnitLevel=function() return 21 end
            CreateFrame=function(kind,name,parent) return UIObject(kind,name,parent) end
            ns.LAR.CharacterScope=function() return nil end
            original={name="Recorded Alt",done={second=99}}
            account.chars[currentIdentity.key]=original
        ''')
        h.load("Social.lua")
        h.execute('''
            local ok,reason=ns.LAR.SaveCharacter()
            assert(ok==false and reason=="Character progress attribution unavailable")
            assert(account.chars[currentIdentity.key]==original and original.done.second==99)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep")
            ns.LAR.CharacterScope=function() return true end
            assert(ns.LAR.SaveCharacter())
            assert(account.chars[currentIdentity.key]~=original)
            assert(account.characterSnapshotArchives[1].snapshot==original and #calls==0)
        ''')
