#!/usr/bin/env python3
"""Subject navigation, stable selection, source isolation, and loaded search."""
import unittest

from test_legacy_wrath_ui import Harness


FIXTURES = r'''
function NativeCatalog(categories, records)
    return {categories=categories,records=records,byKey={},available=true,partial=false,points=16}
end
function NativeCategory(id,name,parent)
    return {key="legacy-category:"..id,id=id,name=name,parent=parent and "legacy-category:"..parent or "legacy",source="legacy"}
end
function NativeRow(id,name,category)
    return {key="legacy:"..id,id=id,source="legacy",name=name,description="Live description",category="legacy-category:"..category,
        completed=false,achievementType="standard",pointType="legacy",pointValue=0,points=0,scopeType="character"}
end
function CustomRow(key,category,section,series)
    return {key="custom:"..key,savedKey=key,id=1,source="custom",name="Authored achievement",description="Authored description",
        category="custom-category:"..category,customCategory=category,customSection=section,series=series,
        completed=false,achievementType="standard",pointType="character",pointValue=10,points=10,scopeType="character",
        achievement={key=key,series=series}}
end
function SetCustomRows(rows)
    ns.CustomAchievementAdapter.Catalog=function()
        return {categories={},records=rows,byKey={},available=true,partial=false,points=0,possiblePoints=10*#rows}
    end
end
'''


class Iteration3CategoryTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute(FIXTURES)

    def check(self, code):
        self.h.execute(code)

    def test_native_and_custom_fishing_share_one_populated_subject(self):
        self.check('''
            local custom=CustomRow("fished25","professions","FISHING","fish")
            SetCustomRows({custom})
            local native=NativeCatalog({NativeCategory(1,"Fishing",2),NativeCategory(2,"Tradeskills")},{NativeRow(100,"Fishing Challenge",1)})
            local m=ns.LegacyPresentation.Build(nil,native)
            assert(#m.byCategory.professions.children==1)
            assert(m.byCategory.professions.children[1].key=="professions:fishing")
            assert(#ns.LegacyPresentation.Rows(m,"professions:fishing")==2)
            assert(#ns.LegacyPresentation.Rows(m,"professions")==0)
            local _,total=ns.LegacyPresentation.Count(m,"professions"); assert(total==2)
            assert(m.byKey["custom:fished25"].pointType=="character" and m.byKey["legacy:100"].pointType=="legacy")
            assert(not m.byCategory["professions:cooking"] and not m.byCategory["professions:first-aid"])
        ''')

    def test_secondary_professions_split_from_authored_metadata_without_title_guessing(self):
        self.check('''
            local fish=CustomRow("fish150","professions","Secondary","fishing")
            local cook=CustomRow("recipes25","professions","Secondary",nil)
            local aid=CustomRow("aid150","professions","Secondary",nil)
            fish.name="A misleading cooking title"; cook.name="A misleading fishing title"; aid.name="A misleading alchemy title"
            SetCustomRows({fish,cook,aid})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byKey[fish.key].category=="professions:fishing")
            assert(m.byKey[cook.key].category=="professions:cooking")
            assert(m.byKey[aid.key].category=="professions:first-aid")
            assert(#m.byCategory.professions.children==3 and #ns.LegacyPresentation.Rows(m,"professions")==0)
            local _,total=ns.LegacyPresentation.Count(m,"professions"); assert(total==3)
        ''')

    def test_explicit_skill_is_stronger_than_section_series_and_title(self):
        self.check('''
            local a=CustomRow("fish150","professions","FISHING","fishing")
            a.skill="Cooking"; a.name="First Aid"
            SetCustomRows({a})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byKey[a.key].category=="professions:cooking")
            a.skill=nil; a.skillLineID=129
            m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byKey[a.key].category=="professions:first-aid")
        ''')

    def test_multi_secondary_meta_stays_once_on_profession_parent(self):
        self.check('''
            local a=CustomRow("paythebills","professions","PROFESSIONS",nil)
            SetCustomRows({a})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(m.byKey[a.key].category=="professions" and m.byKey[a.key].subcategory==nil)
            assert(#m.byCategory.professions.children==0 and #ns.LegacyPresentation.Rows(m,"professions")==1)
        ''')

    def test_continent_zones_and_metas_group_under_shared_exploration_subjects(self):
        self.check('''
            local east=CustomRow("exploreElwynn","exploration","EASTERN KINGDOMS",nil)
            local kal=CustomRow("exploreDesolace","exploration","KALIMDOR",nil)
            local meta=CustomRow("worldexplorer","exploration","AZEROTH",nil)
            SetCustomRows({east,kal,meta})
            local cats={NativeCategory(1,"Westfall",2),NativeCategory(2,"Eastern Kingdoms",4),NativeCategory(3,"Kalimdor",4),NativeCategory(4,"Adventure")}
            local rows={NativeRow(100,"Explore Westfall",1),NativeRow(101,"Explore Darkshore",3),NativeRow(62053,"Explore Azeroth",4)}
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog(cats,rows))
            assert(#ns.LegacyPresentation.Rows(m,"exploration:eastern-kingdoms")==2)
            assert(#ns.LegacyPresentation.Rows(m,"exploration:kalimdor")==2)
            assert(#ns.LegacyPresentation.Rows(m,"exploration:world")==2)
            assert(#ns.LegacyPresentation.Rows(m,"exploration")==0)
            local _,total=ns.LegacyPresentation.Count(m,"exploration"); assert(total==6)
            assert(#m.unmappedIDs==0)
        ''')

    def test_continent_meta_uses_continent_subject_instead_of_world(self):
        self.check('''
            SetCustomRows({})
            local cats={NativeCategory(1,"Explorer",2),NativeCategory(2,"Adventure")}
            local rows={NativeRow(62353,"Explore Eastern Kingdoms",1),NativeRow(62355,"Explore Kalimdor",1)}
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog(cats,rows))
            assert(m.byKey["legacy:62353"].category=="exploration:eastern-kingdoms")
            assert(m.byKey["legacy:62355"].category=="exploration:kalimdor")
            assert(not m.byCategory["exploration:world"])
        ''')

    def test_other_legacy_fallback_changes_navigation_only_and_records_actual_ids(self):
        self.check('''
            SetCustomRows({})
            local row=NativeRow(79999,"Unknown native subject",1)
            row.scopeType="account"; row.pointValue=3; row.points=3
            local native=NativeCatalog({NativeCategory(1,"Unfamiliar Subject")},{row})
            local m=ns.LegacyPresentation.Build(nil,native)
            local view=m.byKey[row.key]
            assert(view.category=="feats:other-legacy" and view.navigationFallback)
            assert(view.achievementType=="standard" and view.pointType=="legacy" and view.pointValue==3 and view.scopeType=="account")
            assert(row.category=="legacy-category:1" and row.navigationFallback==nil)
            assert(m.unmappedIDs[1]==79999 and m.unmappedRecords[1].id==79999 and m.unmapped==m.unmappedRecords)
            for _,root in ipairs(m.roots) do assert(root.key~="unmapped" and root.name~="Unmapped Challenges") end
            assert(#ns.LegacyPresentation.Rows(m,"feats")==0 and #ns.LegacyPresentation.Rows(m,"feats:other-legacy")==1)
            local _,total=ns.LegacyPresentation.Count(m,"feats"); assert(total==1)
        ''')

    def test_direct_parent_and_refresh_do_not_duplicate_stable_namespaced_keys(self):
        self.check('''
            local custom=CustomRow("same_activity","professions","ALCHEMY",nil)
            SetCustomRows({custom,custom})
            local nativeRow=NativeRow(100,"Same activity",1)
            local catalog=NativeCatalog({NativeCategory(1,"Alchemy",2),NativeCategory(2,"Tradeskills")},{nativeRow,nativeRow})
            local m=ns.LegacyPresentation.Build(nil,catalog)
            assert(#m.records==2 and #ns.LegacyPresentation.Rows(m,"professions")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy")==2)
            local _,total=ns.LegacyPresentation.Count(m,"professions"); assert(total==2)
            assert(#m.duplicateKeys==2)
            local refreshed=ns.LegacyPresentation.Build(nil,catalog)
            assert(#refreshed.records==2 and refreshed.byKey[nativeRow.key]~=m.byKey[nativeRow.key])
            assert(custom.category=="custom-category:professions" and nativeRow.category=="legacy-category:1")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_subject_selection_survives_native_category_id_changes(self):
        self.check('''
            SetCustomRows({CustomRow("fish150","professions","FISHING","fishing")})
            local first=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,"Fishing")},{NativeRow(100,"Live challenge",1)}))
            local nextModel=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(77,"Fishing")},{NativeRow(100,"Live challenge",77)}))
            assert(ns.LegacyPresentation.CategoryKey(first,"legacy-category:1")=="professions:fishing")
            assert(ns.LegacyPresentation.CategoryKey(nextModel,"professions:fishing")=="professions:fishing")
            assert(#ns.LegacyPresentation.Rows(nextModel,"professions:fishing")==2)
        ''')

    def test_native_ancestor_context_keeps_pvp_reputations_in_pvp(self):
        self.check('''
            SetCustomRows({CustomRow("repFrostwolf","pvp","BATTLEGROUND REPUTATION",nil)})
            local cats={NativeCategory(1,"Reputations",2),NativeCategory(2,"Player vs. Player")}
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog(cats,{NativeRow(100,"Native PvP reputation",1)}))
            assert(#ns.LegacyPresentation.Rows(m,"pvp:reputations")==2)
            assert(#ns.LegacyPresentation.Rows(m,"reputation")==0)
        ''')

    def test_subjects_are_populated_and_no_daily_quest_category_is_created(self):
        self.check('''
            SetCustomRows({CustomRow("greenhills","quests","QUEST LINES",nil),CustomRow("loreEK","quests","LOREMASTER",nil)})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            assert(#m.byCategory.quests.children==2)
            assert(m.byCategory["quests:storylines"] and m.byCategory["quests:loremaster"])
            for _,cat in ipairs(m.categories) do
                assert(not cat.name:lower():find("daily",1,true))
                if cat.parent then assert(#ns.LegacyPresentation.Rows(m,cat.key)>0) end
            end
        ''')

    def test_search_category_metadata_and_source_filters_cooperate_with_selection(self):
        self.check('''
            local custom=CustomRow("cook75","professions","COOKING","cook")
            SetCustomRows({custom})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,"Alchemy")},{NativeRow(100,"Native title",1)}))
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy","alchemy","Legacy Challenges")==1)
            assert(#ns.LegacyPresentation.Rows(m,"professions:cooking","cooking","Character Achievements")==1)
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy","","Character")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions","","Legacy")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy","","Legacy")==1)
            assert(#ns.LegacyPresentation.Rows(m,"professions","","Completed")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions","","Incomplete")==0)
            assert(#ns.LegacyPresentation.Rows(m,"professions:alchemy","","Incomplete")==1)
            assert(#ns.LegacyPresentation.Rows(m,"professions:cooking","","Incomplete")==1)
        ''')

    def test_search_loaded_criteria_is_bounded_and_performs_no_native_query_on_keypress(self):
        self.check('''
            SetCustomRows({})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({NativeCategory(1,"General")},{NativeRow(100,"Live challenge",1)}))
            local reads=0
            ns.LegacyAdapter.Criteria=function()
                reads=reads+1
                local items={{name="Hidden objective"},{name="Unavailable placeholder",unavailable=true}}
                for i=3,65 do items[i]={name="Objective "..i} end
                return {items=items,available=true,complete=true}
            end
            assert(#ns.LegacyPresentation.Rows(m,"general","hidden objective")==0 and reads==0)
            ns.LegacyPresentation.Criteria(m.byKey["legacy:100"])
            assert(#ns.LegacyPresentation.Rows(m,"general","hidden objective")==1 and reads==1)
            assert(#ns.LegacyPresentation.Rows(m,"general","objective 65")==0)
            assert(#ns.LegacyPresentation.Rows(m,"general","unavailable placeholder")==0)
            ns.LegacyPresentation.Criteria(m.byKey["legacy:100"])
            assert(reads==1 and m.criteriaSearchScope=="Loaded criteria only")
        ''')


if __name__ == "__main__":
    unittest.main()
