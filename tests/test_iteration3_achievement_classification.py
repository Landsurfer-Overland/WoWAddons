"""Independent source, scope, achievement-type, point, and history contracts.

Uses Lua 5.1 and explicit API doubles. These tests do not prove game rendering
or the server's actual reward values; the values supplied by APIs stay exact.
"""
from collections import Counter
import unittest

from test_legacy_wrath_ui import ADDON, BASE, LuaRuntime


class AdapterHarness:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(BASE)
        self.g = self.lua.globals()
        for path in ("Integrations/LegacyAdapter.lua", "Integrations/CustomAdapter.lua"):
            self.load(path)

    def load(self, path):
        fn = self.lua.execute("return assert(loadstring(...))", (ADDON / path).read_text(), "@" + path)
        fn("ForeverAchievements", self.g.ns)

    def execute(self, code):
        return self.lua.execute(code)


class AchievementClassificationTests(unittest.TestCase):
    def setUp(self):
        self.h = AdapterHarness()

    def check(self, code):
        self.h.execute(code)

    def test_explore_azeroth_zero_legacy_award_is_standard_and_account_scope_is_independent(self):
        self.check('''
            GetAchievementCategory=function(id) assert(id==62053); return 15607 end
            GetCategoryInfo=function(id) assert(id==15607); return "Explorer",-1 end
            GetAchievementInfo=function(id) return id,"Explore Azeroth",0,false,nil,nil,nil,
                "Native world exploration",ACHIEVEMENT_FLAGS_ACCOUNT,237388,"" end
            C_Traits.GetTraitCurrencyForAchievement=function(currency,id) assert(currency==4225 and id==62053); return 0 end
            local a=ns.LegacyAdapter.Resolve(62053)
            assert(a.uniqueID=="legacy:62053" and a.source=="legacy" and a.sourceType=="native_legacy")
            assert(a.scope=="Account" and a.scopeType=="account")
            assert(a.achievementType=="standard" and a.pointType=="none")
            assert(a.pointValue==0 and a.points==0 and a.pts==0 and a.nativeAchievementPoints==0)
            assert(a.completionState=="incomplete" and a.completionDate==nil and #calls==0)
        ''')

    def test_reward_text_and_native_achievement_points_never_replace_missing_legacy_api(self):
        self.check('''
            GetAchievementInfo=function(id) return id,"Challenge",999,true,10,27,24,
                "Native description",0,237388,"Earn 1 Legacy Point." end
            C_Traits.GetTraitCurrencyForAchievement=nil
            local a=ns.LegacyAdapter.Resolve(62053)
            assert(a.pointType=="unknown" and a.pointValue==nil and a.points==nil and a.pts==nil)
            assert(a.nativeAchievementPoints==999 and a.reward=="Earn 1 Legacy Point.")
            assert(a.achievementType=="unknown" and a.completionState=="complete")
            assert(a.completionDate==a.date and a.dateSort==20241027)
            assert(a.completionDateParts.year==2024 and #calls==0)
        ''')

    def test_native_feat_requires_real_native_category_ancestry(self):
        self.check('''
            GetAchievementInfo=function(id) return id,"Native record",0,false,nil,nil,nil,"Description",0,237388,"" end
            GetAchievementCategory=function(id) return id==91 and 92 or 93 end
            GetCategoryInfo=function(id)
                if id==92 then return "A native subcategory",81 end
                return "Future Legacy Challenges",-1
            end
            local feat=ns.LegacyAdapter.Resolve(91)
            assert(feat.achievementType=="feat_of_strength" and feat.pointValue==0)
            local other=ns.LegacyAdapter.Resolve(94)
            other.category="feats:other-legacy" -- presentation fallback cannot reclassify data
            assert(other.achievementType=="standard" and other.pointType=="none" and other.pointValue==0)
            assert(#calls==0)
        ''')

    def test_invalid_or_cyclic_native_metadata_stays_unknown_with_bounded_reads(self):
        self.check('''
            local reads=0
            GetAchievementCategory=function() return 91 end
            GetCategoryInfo=function(id) reads=reads+1; return "Cyclic",id==91 and 92 or 91 end
            assert(ns.LegacyAdapter.Resolve(62013).achievementType=="unknown" and reads<=3)
            GetCategoryInfo=function(id) reads=reads+1; return "No reliable parent",nil end
            assert(ns.LegacyAdapter.Resolve(62013).achievementType=="unknown")
            GetAchievementCategory=nil
            assert(ns.LegacyAdapter.Resolve(62013).achievementType=="unknown")
        ''')

    def test_invalid_scope_mask_flags_and_missing_completion_are_not_guessed(self):
        self.check('''
            GetAchievementInfo=function(id) return id,"Unavailable",0,nil,nil,nil,nil,"Description",-1,237388,"" end
            local a=ns.LegacyAdapter.Resolve(62013)
            assert(a.completed==nil and a.completionState=="unknown" and a.scopeType=="unknown")
            ACHIEVEMENT_FLAGS_ACCOUNT=3
            assert(ns.LegacyAdapter.Resolve(62013).scope=="Scope unavailable")
            assert(ns.LegacyReadOnly.HasFlag(0,131072)==false)
            assert(ns.LegacyReadOnly.HasFlag(131072,131072)==true)
            assert(ns.LegacyReadOnly.HasFlag(1.5,131072)==nil)
        ''')

    def test_native_lazy_criteria_does_not_change_authoritative_completion(self):
        self.check('''
            local a=ns.LegacyAdapter.Resolve(62013)
            local before=a.completionState
            local c=ns.LegacyAdapter.Criteria(a)
            assert(a.criteria==c and a.progress.available and a.progress.criteria==c.items)
            assert(a.progress.criteria[1].current==0 and a.progress.criteria[1].required==225)
            assert(a.completionState==before and a.completed==false and #calls==0)
            GetAchievementNumCriteria=nil
            c=ns.LegacyAdapter.Criteria(a)
            assert(not a.progress.available and not c.available and a.completed==false)
        ''')

    def test_native_criterion_flags_use_the_flags_field_not_character_name(self):
        self.check('''
            GetAchievementNumCriteria=function() return 1 end
            GetAchievementCriteriaInfo=function() return "Eastern Kingdoms",8,false,0,1,
                "Character name",64,62353,"0 / 1",123 end
            local a=ns.LegacyAdapter.Resolve(62053)
            local item=ns.LegacyAdapter.Criteria(a).items[1]
            assert(item.flags==64 and item.assetID==62353 and item.link=="legacy:62353")
            assert(item.criteriaID==123 and a.completed==false and #calls==0)
        ''')

    def test_native_same_id_in_two_categories_is_audited_once_without_mirror_aliasing(self):
        self.check('''
            GetCategoryList=function() return {91,92} end
            GetCategoryInfo=function(id) return id==91 and "Explorer" or "Adventure",-1 end
            GetCategoryNumAchievements=function() return 1,0,1 end
            GetAchievementInfo=function() return 62053,"Explore Azeroth",0,false,nil,nil,nil,
                "Description",0,237388,"" end
            local c=ns.LegacyAdapter.Catalog()
            assert(#c.records==1 and #c.duplicates==1 and c.duplicateIDs[1]==62053)
            assert(c.duplicates[1].key=="legacy:62053" and c.duplicates[1].category=="legacy-category:92")
            assert(c.byKey["legacy:62053"].achievementType=="standard" and c.byKey["legacy:62053"].pointType=="none")
            assert(not c.byKey["legacy:64015"] and c.points==16 and #calls==0)
        ''')

    def test_custom_zero_is_not_feat_and_authored_feat_does_not_overwrite_points(self):
        self.check('''
            local ordinary={key="ordinary-zero",name="No point custom",pts=0,progress=function()return 0,1 end}
            local feat={key="real-feat",name="Authored feat",pts=0,progress=function()return 0,1 end}
            local unusual={key="special",name="Special",pts=25,achievementType="special",progress=function()return 0,1 end}
            table.insert(ns.FA.CATEGORY_SECTIONS.general[1].list,ordinary)
            table.insert(ns.FA.CATEGORY_SECTIONS.general[1].list,unusual)
            ns.FA.CATEGORY_ORDER[#ns.FA.CATEGORY_ORDER+1]="feats"
            ns.FA.CATEGORY_SECTIONS.feats={{title="Authored special achievements",list={feat}}}
            local c=ns.CustomAchievementAdapter.Catalog()
            ordinary=c.byKey["custom:ordinary-zero"]; feat=c.byKey["custom:real-feat"]
            assert(ordinary.achievementType=="standard" and ordinary.pointType=="character" and ordinary.pointValue==0)
            assert(feat.achievementType=="feat_of_strength" and feat.pointType=="none" and feat.pointValue==0)
            assert(c.byKey["custom:special"].achievementType=="special" and c.byKey["custom:special"].pointValue==25)
            assert(c.byKey["custom:second"].pointValue==20 and c.possiblePoints==55)
        ''')

    def test_custom_identity_metadata_and_character_history_remain_separate(self):
        self.check('''
            settings.accountView=true
            local a=ns.FA.BY_KEY.second
            a.skill="Cooking"; a.series="cook"; a.faction="Alliance"
            ns.FA.CATEGORY_SECTIONS.general[1].title="COOKING"
            local c=ns.CustomAchievementAdapter.Catalog()
            local row=c.byKey["custom:second"]
            assert(row.uniqueID==row.key and row.savedKey=="second" and row.sourceType=="custom_character")
            assert(row.scopeType=="character" and row.scope=="Character" and row.completionState=="incomplete")
            assert(row.skill=="Cooking" and row.series=="cook" and row.customSection=="COOKING" and row.faction=="Alliance")
            assert(row.progress.available and row.progress.current==7 and row.progress.required==10)
            assert(saved.done.second==nil and saved.done.first==1730000000 and saved.history[1]=="keep")
            assert(c.points==10 and not c.byKey["custom:imported"] and #calls==0)
        ''')

    def test_custom_unavailable_points_and_invalid_history_are_not_fabricated(self):
        self.check('''
            ns.FA.BY_KEY.first.pts=nil
            saved.done.second="Unreadable saved timestamp"
            local c=ns.CustomAchievementAdapter.Catalog()
            assert(c.points==nil and c.possiblePoints==nil and not c.pointsAvailable)
            assert(c.byKey["custom:first"].pointType=="unknown" and c.byKey["custom:first"].pointValue==nil)
            assert(c.byKey["custom:second"].completed==nil and c.byKey["custom:second"].completionState=="unknown")
            assert(saved.done.second=="Unreadable saved timestamp")
        ''')

    def test_unknown_custom_completion_makes_earned_total_unavailable(self):
        self.check('''
            saved.done.second="Unreadable saved timestamp"
            local c=ns.CustomAchievementAdapter.Catalog()
            assert(c.points==nil and not c.pointsAvailable and c.possiblePoints==30)
            assert(c.byKey["custom:second"].completionState=="unknown")
            assert(saved.done.first==1730000000 and saved.done.second=="Unreadable saved timestamp")
        ''')


class RealCoreAuditTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            function CreateFrame() return {SetScript=function()end,RegisterEvent=function()end,
                RegisterUnitEvent=function()end,Hide=function()end} end
            C_Timer={After=function()end,NewTicker=function()return{}end}
            SlashCmdList={}; ns={}; time=function()return 100 end; GetTime=function()return 0 end
            UnitLevel=function()return 21 end; UnitFactionGroup=function()return "Alliance" end
        ''')
        for path in ("AlphaUI.lua", "Data.lua", "DataQuests.lua", "DataProfDungeons.lua", "DataExtra.lua",
                     "MoneyTracking.lua", "ForeverAchievements.lua", "Integrations/LegacyAdapter.lua", "Integrations/CustomAdapter.lua"):
            fn = self.lua.execute("return assert(loadstring(...))", (ADDON / path).read_text(), "@" + path)
            fn("ForeverAchievements", self.lua.globals().ns)

    def test_real_core_retains_all_322_unique_saved_keys_and_authored_point_values(self):
        definitions = [a for _, a in self.lua.globals().ns.FA.ALL.items()]
        self.assertEqual(len(definitions), 322)
        self.assertEqual(len({a.key for a in definitions}), 322)
        self.assertEqual(sum(bool(a.native) for a in definitions), 59)
        self.assertEqual(Counter(a.pts for a in definitions if not a.native),
                         Counter({10: 235, 0: 13, 20: 6, 25: 4, 50: 3, 15: 2}))

    def test_real_custom_zones_keep_character_points_and_explicit_geography_and_meta_relationships(self):
        self.lua.execute('''
            local d=ns.FA.DB()
            d.done.explore848=1730000000; d.done.exploreEK=1730000001; d.done.exploreKal=1730000002
            local c=ns.CustomAchievementAdapter.Catalog()
            for key,geography in pairs({explore848="Kalimdor",explore844="Kalimdor",
                explore776="Eastern Kingdoms",explore802="Eastern Kingdoms"}) do
                local row=c.byKey["custom:"..key]
                assert(row and row.pointType=="character" and row.pointValue==10 and row.achievementType=="standard")
                assert(row.customGeography==geography and row.scopeType=="character")
            end
            assert(c.byKey["custom:exploreEK"].pointValue==25 and #c.byKey["custom:exploreEK"].metaChildren==23)
            assert(c.byKey["custom:exploreKal"].pointValue==25 and #c.byKey["custom:exploreKal"].metaChildren==20)
            assert(c.byKey["custom:worldexplorer"].pointValue==50 and #c.byKey["custom:worldexplorer"].metaChildren==2)
            assert(d.done.explore848==1730000000 and d.done.exploreEK==1730000001 and d.done.exploreKal==1730000002)
            local seen={}
            for _,row in ipairs(c.records) do assert(not seen[row.uniqueID]); seen[row.uniqueID]=true end
        ''')


if __name__ == "__main__":
    unittest.main()
