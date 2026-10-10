#!/usr/bin/env python3
"""Unified navigation and reliable source summaries; no native UI mutations."""
import unittest

from test_legacy_wrath_ui import Harness


class UnifiedCategoryTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()

    def check(self, code):
        self.h.execute(code)

    def test_roots_merge_native_and_custom_professions_without_source_sections(self):
        self.check('''
            local a = ns.FA.BY_KEY.second
            ns.FA.CATEGORIES[#ns.FA.CATEGORIES+1]={key="professions",label="Professions"}
            ns.FA.CATEGORY_ORDER[#ns.FA.CATEGORY_ORDER+1]="professions"
            ns.FA.CATEGORY_SECTIONS.general[1].list={ns.FA.BY_KEY.first}
            ns.FA.CATEGORY_SECTIONS.professions={{list={a}}}
            local m=ns.LegacyPresentation.Build()
            local expected={"summary","general","quests","exploration","professions","dungeons","reputation","pvp","classes","feats"}
            assert(#m.roots==#expected)
            for i,key in ipairs(expected) do assert(m.roots[i].key==key) end
            local rows=ns.LegacyPresentation.Rows(m,"professions")
            assert(#rows==2 and rows[1].source=="legacy" and rows[2].source=="custom")
            assert(m.byKey["legacy:62013"].nativeCategory=="legacy-category:15587")
            assert(m.byKey["custom:second"].unifiedRoot=="professions")
            assert(#ns.LegacyPresentation.Rows(m,"legacy")==3)
            assert(#ns.LegacyPresentation.Rows(m,"custom")==2 and #calls==0)
        ''')

    def test_mixed_adventure_maps_individual_quest_and_explorer_keeps_unknown_browsable(self):
        self.check('''
            GetCategoryList=function() return {91} end
            GetCategoryInfo=function() return "Adventure",-1 end
            GetCategoryNumAchievements=function() return 3,0,3 end
            GetAchievementInfo=function(id,index)
                if index then id=({62054,62382,79999})[index] end
                local name=({[62054]="Lord Valthalak Laid to Rest",[62382]="Explorer",[79999]="New Adventure"})[id]
                return id,name,0,false,nil,nil,nil,"Live description",0,237387,""
            end
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62054"].unifiedRoot=="quests")
            assert(m.byKey["legacy:62382"].unifiedRoot=="exploration")
            assert(m.byKey["legacy:79999"].unifiedRoot=="feats")
            assert(m.byKey["legacy:79999"].category=="feats:other-legacy")
            assert(#ns.LegacyPresentation.Rows(m,"quests")==1)
            assert(#ns.LegacyPresentation.Rows(m,"exploration")==1)
            assert(#ns.LegacyPresentation.Rows(m,"feats:other-legacy")==1)
            assert(m.byCategory["feats:other-legacy"].parent=="feats")
            for _,root in ipairs(m.roots) do assert(root.key~="unmapped" and root.name~="Unmapped Challenges") end
            assert(#m.records==5)
        ''')

    def test_reused_beta_id_does_not_receive_old_individual_mapping(self):
        self.check('''
            GetCategoryList=function() return {91} end
            GetCategoryInfo=function() return "Adventure",-1 end
            GetCategoryNumAchievements=function() return 1,0,1 end
            GetAchievementInfo=function() return 62382,"Completely New Challenge",0,false,nil,nil,nil,"Description",0,237387,"" end
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62382"].unifiedRoot=="feats")
            assert(m.byKey["legacy:62382"].category=="feats:other-legacy")
            assert(#ns.LegacyPresentation.Rows(m,"exploration")==0)
        ''')

    def test_explicit_runtime_category_precedes_an_old_record_exception(self):
        self.check('''
            GetCategoryList=function() return {91} end
            GetCategoryInfo=function() return "Quests",-1 end
            GetCategoryNumAchievements=function() return 1,0,1 end
            GetAchievementInfo=function() return 62382,"Explorer",0,false,nil,nil,nil,"New quest context",0,237387,"" end
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:62382"].unifiedRoot=="quests")
        ''')

    def test_actual_ancestor_context_preserves_pvp_reputation_and_class_children(self):
        self.check('''
            GetCategoryList=function() return {11,12,13,14,15,16} end
            GetCategoryInfo=function(id)
                local names={[11]="Reputations",[12]="Player vs. Player",[13]="Warrior",[14]="Classes",[15]="New Profession Specialization",[16]="Tradeskills"}
                local parents={[11]=12,[13]=14,[15]=16}
                return names[id],parents[id] or -1
            end
            GetCategoryNumAchievements=function(id) return id%2==1 and 1 or 0,0,1 end
            GetAchievementInfo=function(cat,index) return 80000+cat,"Live Challenge "..cat,0,false,nil,nil,nil,"Description",0,237387,"" end
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:80011"].unifiedRoot=="pvp")
            assert(m.byKey["legacy:80013"].unifiedRoot=="classes")
            assert(m.byKey["legacy:80015"].unifiedRoot=="professions")
            assert(CategoryRoot(m,"legacy-category:11")=="pvp")
            assert(CategoryRoot(m,"legacy-category:13")=="classes")
        ''')

    def test_adventure_geography_and_quest_subcategories_map_by_metadata(self):
        self.check('''
            GetCategoryList=function() return {1,2,3} end
            GetCategoryInfo=function(id)
                if id==1 then return "Eastern Kingdoms",3 end
                if id==2 then return "Quests",3 end
                return "Adventure",-1
            end
            GetCategoryNumAchievements=function(id) return id<3 and 1 or 0,0,1 end
            GetAchievementInfo=function(cat,index) return 80000+cat,"Challenge",0,false,nil,nil,nil,"Description",0,237387,"" end
            local m=ns.LegacyPresentation.Build()
            assert(m.byKey["legacy:80001"].unifiedRoot=="exploration")
            assert(m.byKey["legacy:80002"].unifiedRoot=="quests")
            assert(not m.byCategory["feats:other-legacy"])
        ''')

    def test_unknown_and_cyclic_categories_remain_reachable_without_duplicate_rows(self):
        self.check('''
            GetCategoryInfo=function(id) return "Unfamiliar",id==15607 and 15587 or 15607 end
            local m=ns.LegacyPresentation.Build()
            local seen={}
            for _,row in ipairs(ns.LegacyPresentation.Rows(m,"summary")) do
                assert(not seen[row.key]); seen[row.key]=true
            end
            assert(#ns.LegacyPresentation.Rows(m,"feats:other-legacy")==1)
            assert(#ns.LegacyPresentation.Rows(m,"legacy")==3)
            local visited={}
            local function visit(cat)
                assert(not visited[cat.key]); visited[cat.key]=true
                for _,child in ipairs(cat.children) do visit(child) end
            end
            for _,root in ipairs(m.roots) do visit(root) end
            assert(visited[m.byKey["legacy:62013"].category])
        ''')

    def test_build_does_not_mutate_catalogs_saved_history_or_custom_definitions(self):
        self.check('''
            local catalog=ns.LegacyAdapter.Catalog()
            local original=catalog.byKey["legacy:62013"]
            local originalCategory=original.category
            local m=ns.LegacyPresentation.Build(nil,catalog)
            assert(m.byKey[original.key]~=original)
            assert(original.category==originalCategory and original.unifiedRoot==nil)
            assert(catalog.categories[2].children==nil)
            assert(ns.FA.BY_KEY.second.category==nil)
            assert(saved.done.first==1730000000 and saved.done.second==nil)
            assert(saved.history[1]=="keep" and saved.explored.zone.old and next(saved.tracked)==nil)
            assert(#calls==0)
        ''')

    def test_summary_preserves_separate_totals_and_unknown_completion(self):
        self.check('''
            local original=GetAchievementInfo
            GetAchievementInfo=function(id,index)
                local values={original(id,index)}
                if values[1]==62013 then values[4]=nil end
                return unpack(values,1,13)
            end
            local m=ns.LegacyPresentation.Build()
            local s=ns.LegacyPresentation.Summary(m)
            assert(s.custom.points==10 and s.native.points==16)
            assert(s.custom.completed==1 and s.custom.total==2 and s.custom.unknown==0)
            assert(s.native.completed==0 and s.native.total==3 and s.native.unknown==1)
            assert(s.native.available and not s.native.partial)
            assert(#s.custom.recent==1 and #s.native.recent==0)
        ''')

    def test_native_recent_uses_valid_dates_only_and_deterministic_calendar_order(self):
        self.check('''
            GetCategoryList=function() return {1} end
            GetCategoryInfo=function() return "General",-1 end
            GetCategoryNumAchievements=function() return 4,4,0 end
            GetAchievementInfo=function(id,index)
                id=index or id
                local days={27,30,26,25}
                return id,"Completed "..id,0,true,id==2 and 2 or 10,days[id],24,"Description",0,237387,""
            end
            local m=ns.LegacyPresentation.Build()
            local recent=ns.LegacyPresentation.Recent(m,"legacy",4)
            assert(#recent==3 and recent[1].id==1 and recent[2].id==3 and recent[3].id==4)
            assert(m.byKey["legacy:2"].completed and m.byKey["legacy:2"].date==nil)
            assert(recent[1].dateSort==20241027 and recent[1].completionDateParts.year==2024)
            assert(recent[1].timestamp==nil)
        ''')

    def test_known_empty_catalog_and_unavailable_catalog_are_distinct(self):
        self.check('''
            GetCategoryNumAchievements=function() return 0,0,0 end
            local empty=ns.LegacyPresentation.Summary(ns.LegacyPresentation.Build())
            assert(empty.native.available and not empty.native.partial and empty.native.total==0)
            GetCategoryList=function() return {} end
            local none=ns.LegacyPresentation.Summary(ns.LegacyPresentation.Build())
            assert(none.native.available and not none.native.partial and none.native.total==0)
            GetCategoryList=nil
            local unavailable=ns.LegacyPresentation.Summary(ns.LegacyPresentation.Build())
            assert(not unavailable.native.available and unavailable.native.partial and unavailable.native.total==0)
            assert(unavailable.custom.completed==1)
        ''')

    def test_provider_fallback_recovers_runtime_category_ancestry_read_only(self):
        self.check('''
            local page=SetupNative()
            GetCategoryList=nil
            GetAchievementCategory=function(id) assert(id==62013); return 99 end
            GetCategoryInfo=function(id)
                if id==99 then return "Alchemy",100 end
                return "Tradeskills",-1
            end
            local m=ns.LegacyPresentation.Build(page)
            assert(m.native.partial and #m.native.records==1)
            assert(m.byKey["legacy:62013"].unifiedRoot=="professions")
            assert(m.byKey["legacy:62013"].nativeCategory=="legacy-category:99")
            assert(CategoryRoot(m,"legacy-category:99")=="professions")
            assert(#calls==0)
        ''')

    def test_repeated_custom_definition_does_not_duplicate_points_or_entries(self):
        self.check('''
            local list=ns.FA.CATEGORY_SECTIONS.general[1].list
            list[#list+1]=ns.FA.BY_KEY.first
            local m=ns.LegacyPresentation.Build()
            assert(#ns.LegacyPresentation.Rows(m,"custom")==2)
            assert(m.custom.points==10 and m.custom.possiblePoints==30)
        ''')

    def test_partial_native_catalog_counts_only_observed_records(self):
        self.check('''
            local page=SetupNative()
            GetCategoryList=nil
            local s=ns.LegacyPresentation.Summary(ns.LegacyPresentation.Build(page))
            assert(s.native.partial and s.native.available and s.native.total==1)
            assert(s.native.points==16 and #s.native.recent==0)
        ''')

    def test_reward_area_uses_explicit_rewards_and_keeps_social_title_unchanged(self):
        self.check('''
            local a=ns.FA.BY_KEY.first
            a.title="%s the Tester"
            local without=ns.CustomAchievementAdapter.Catalog().byKey["custom:first"]
            assert(without.reward==nil and a.title=="%s the Tester")
            a.rewardDescription="A real authored reward description"
            local with=ns.CustomAchievementAdapter.Catalog().byKey["custom:first"]
            assert(with.reward==a.rewardDescription)
        ''')


if __name__ == "__main__":
    unittest.main()
