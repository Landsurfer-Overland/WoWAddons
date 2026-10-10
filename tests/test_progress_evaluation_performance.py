"""Actual-core API counting checks for one synchronous progress evaluation.

The real definitions and CustomAdapter execute; assertions count expensive
observations rather than timing a mock client or asserting implementation loops.
"""
import unittest

from test_progression_addendum import CoreHarness


class EvaluationHarness(CoreHarness):
    def load(self, path):
        if path == "ForeverAchievements.lua":
            # The core captures this API at load time. Install its observer
            # before that capture, preserving its exact return tuple.
            self.execute('''
                globalStandingSentinel=function() error("Unrelated global Standing must stay untouched") end
                globalCriteriaSentinel=function() error("Unrelated global FvCriteria must stay untouched") end
                Standing=globalStandingSentinel; FvCriteria=globalCriteriaSentinel
                classReads={}
                local classify=C_Item.GetItemInfoInstant
                C_Item.GetItemInfoInstant=function(id)
                    classReads[id]=(classReads[id] or 0)+1
                    return classify(id)
                end
            ''')
        super().load(path)

    def __init__(self):
        super().__init__()
        # The integration harness initially loads a small fake FA. Reload this
        # adapter so it observes the production FA and its snapshot wrapper.
        self.load("Integrations/CustomAdapter.lua")
        self.execute('''
            function SelectCatalog(...)
                local wanted={}
                for _,key in ipairs({...}) do wanted[key]=true; assert(ns.FA.BY_KEY[key]) end
                for _,sections in pairs(ns.FA.CATEGORY_SECTIONS) do
                    for _,section in ipairs(sections) do
                        for i=#section.list,1,-1 do
                            if not wanted[section.list[i].key] then table.remove(section.list,i) end
                        end
                    end
                end
            end
            function AssertNoAwardsOrNativeMutations()
                assert(saved.done.first==1730000000 and saved.history[1]=="keep")
                assert(saved.explored.zone.old and next(saved.tracked)==nil and #calls==0)
                assert(ns.FA.Count(saved.done)==1 and #ns.FA.ProgressionDiagnostics.records==0)
                assert(Standing==globalStandingSentinel and FvCriteria==globalCriteriaSentinel)
            end
        ''')


class ProgressEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.h=EvaluationHarness()

    def check(self, code):
        self.h.execute(code)
        self.h.execute("AssertNoAwardsOrNativeMutations()")

    def test_guarded_unknown_quest_statistics_are_shared_but_fresh_on_the_next_pass(self):
        self.check('''
            SelectCatalog("q50","q100","q500")
            local statReads,questReads=0,0
            GetStatistic=function(id) assert(id==98); statReads=statReads+1; error("Statistic unavailable") end
            C_QuestLog={GetAllCompletedQuestIDs=function() questReads=questReads+1; error("Quest IDs unavailable") end}
            local unknown=ns.CustomAchievementAdapter.Catalog()
            assert(#unknown.records==3 and statReads==1 and questReads==1)
            for _,row in ipairs(unknown.records) do assert(row.current==nil and not row.progress.available and not row.completed) end
            GetStatistic=function(id) assert(id==98); statReads=statReads+1; return "10" end
            local known=ns.CustomAchievementAdapter.Catalog()
            assert(statReads==2 and questReads==1)
            for _,row in ipairs(known.records) do assert(row.current==10 and row.progress.available and not row.completed) end
        ''')

    def test_statistics_snapshot_preserves_nil_returns_and_ends_after_one_pass(self):
        self.check('''
            local reads,value=0,"7"
            GetStatistic=function(id) assert(id==98); reads=reads+1; return value end
            local first,hole,last=ns.FA.WithProgressSnapshot(function(argument)
                assert(argument=="input")
                assert(ns.FA.StatText(98)=="7")
                value="8"
                assert(ns.FA.StatText(98)=="7" and reads==1)
                return "first",nil,"last"
            end,"input")
            assert(first=="first" and hole==nil and last=="last")
            assert(ns.FA.StatText(98)=="8" and reads==2)
            ns.FA.WithProgressSnapshot(function() assert(ns.FA.StatText(98)=="8") end)
            assert(reads==3)
        ''')

    def test_error_cleanup_and_nested_snapshots_do_not_leak_or_replace_the_outer_pass(self):
        self.check('''
            local reads,value=0,"7"
            GetStatistic=function() reads=reads+1; return value end
            local ok,message=pcall(ns.FA.WithProgressSnapshot,function()
                assert(ns.FA.StatText(98)=="7")
                error("Injected evaluation failure")
            end)
            assert(not ok and message:find("Injected evaluation failure",1,true))
            value="8"
            assert(ns.FA.StatText(98)=="8" and reads==2)
            ns.FA.WithProgressSnapshot(function()
                assert(ns.FA.StatText(98)=="8")
                value="9"
                local nestedOk=pcall(ns.FA.WithProgressSnapshot,function()
                    assert(ns.FA.StatText(98)=="8")
                    error("Injected nested failure")
                end)
                assert(not nestedOk and ns.FA.StatText(98)=="8" and reads==3)
            end)
            assert(ns.FA.StatText(98)=="9" and reads==4)
        ''')

    def test_nested_character_db_switch_cannot_reuse_another_characters_observation(self):
        self.check('''
            local firstDB=ForeverAchievementsCharDB
            local secondDB={done={},tracked={},history={"second"},explored={},fixtureStat="20"}
            firstDB.fixtureStat="10"
            local reads=0
            GetStatistic=function() reads=reads+1; return ForeverAchievementsCharDB.fixtureStat end
            ns.FA.WithProgressSnapshot(function()
                assert(ns.FA.StatText(98)=="10")
                ForeverAchievementsCharDB=secondDB
                ns.FA.WithProgressSnapshot(function()
                    assert(ns.FA.StatText(98)=="20" and ns.FA.StatText(98)=="20")
                end)
                assert(reads==2)
                assert(ns.FA.StatText(98)=="20" and reads==3)
                ForeverAchievementsCharDB=firstDB
                assert(ns.FA.StatText(98)=="10" and reads==3)
            end)
            firstDB.fixtureStat="30"
            assert(ns.FA.StatText(98)=="30" and reads==4)
            assert(next(secondDB.done)==nil and secondDB.history[1]=="second")
        ''')

    def test_pet_and_mount_catalog_reads_share_slots_items_and_item_classification(self):
        self.check('''
            SelectCatalog("pet1","pet15","mount10")
            bagItems[0]={1001,1001,2001}; bagItems[1]={3001}
            itemClasses[1001]={15,2}; itemClasses[2001]={15,5}; itemClasses[3001]={0,5}
            local slotReads,itemReads=0,0
            local slots,item=C_Container.GetContainerNumSlots,C_Container.GetContainerItemID
            C_Container.GetContainerNumSlots=function(bag) slotReads=slotReads+1; return slots(bag) end
            C_Container.GetContainerItemID=function(bag,slot) itemReads=itemReads+1; return item(bag,slot) end
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(slotReads==5 and itemReads==4)
            assert(classReads[1001]==1 and classReads[2001]==1 and classReads[3001]==1)
            assert(catalog.byKey["custom:pet1"].current==1 and catalog.byKey["custom:pet15"].current==1)
            assert(catalog.byKey["custom:mount10"].current==1)
            itemClasses[3001]={15,2}
            catalog=ns.CustomAchievementAdapter.Catalog()
            assert(slotReads==10 and itemReads==8)
            assert(classReads[1001]==2 and classReads[2001]==2 and classReads[3001]==2)
            assert(catalog.byKey["custom:pet15"].current==2 and catalog.byKey["custom:mount10"].current==1)
        ''')

    def test_failed_map_fallback_is_once_per_zone_with_shared_hierarchy_reads(self):
        self.check('''
            local westfall=ns.FA.ZONE_ACH.Westfall
            SelectCatalog("explore855",westfall.key)
            local mapReads,bestReads,childrenReads={},0,0
            Enum={UIMapType={Zone=3}}
            C_Map={
                GetMapInfo=function(id)
                    mapReads[id]=(mapReads[id] or 0)+1
                    if id==9000 then return {mapID=9000,name="World",parentMapID=0} end
                end,
                GetBestMapForUnit=function(unit) assert(unit=="player"); bestReads=bestReads+1; return 9000 end,
                GetMapChildrenInfo=function() childrenReads=childrenReads+1; error("Map hierarchy unavailable") end,
            }
            C_MapExplorationInfo={GetExploredMapTextures=function() error("No verified zone map") end}
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(#catalog.records==2 and bestReads==1 and childrenReads==1 and mapReads[9000]==1)
            for id,count in pairs(mapReads) do assert(count==1) end
            for _,row in ipairs(catalog.records) do assert(row.current==nil and not row.progress.available) end
            catalog=ns.CustomAchievementAdapter.Catalog()
            assert(bestReads==2 and childrenReads==2)
            for id,count in pairs(mapReads) do assert(count==2) end
        ''')

    def test_profession_and_riding_scans_are_bounded_across_catalog_and_criteria(self):
        self.check('''
            SelectCatalog("riding75","riding150","prof75","prof150","prof225","prof300",
                "dayandnight","paythebills","cook75","cook150","fish75","aid75")
            local skillRows={{"Alchemy",40},{"Cooking",10},{"Fishing",5},{"First Aid",10},{"Riding",75}}
            local countReads,lineReads=0,0
            GetNumSkillLines=function() countReads=countReads+1; return #skillRows end
            GetSkillLineInfo=function(index)
                lineReads=lineReads+1
                return skillRows[index][1],false,nil,skillRows[index][2]
            end
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(countReads==2 and lineReads==2*#skillRows)
            assert(catalog.byKey["custom:prof75"].current==40 and catalog.byKey["custom:riding150"].current==75)
            local criteria=ns.CustomAchievementAdapter.Criteria(catalog.byKey["custom:paythebills"])
            assert(#criteria.items==3 and countReads==3 and lineReads==3*#skillRows)
            skillRows[1][2]=60
            catalog=ns.CustomAchievementAdapter.Catalog()
            assert(catalog.byKey["custom:prof75"].current==60)
            assert(countReads==5 and lineReads==5*#skillRows)
        ''')

    def test_thrown_skill_evaluator_failure_is_memoized_without_becoming_zero_or_permanent(self):
        self.check('''
            SelectCatalog("prof75","prof150","prof225","prof300","cook75","cook150","paythebills")
            local reads=0
            GetNumSkillLines=function() reads=reads+1; error("Skills unavailable") end
            GetSkillLineInfo=function() error("Failing skill-list call must stop the scan") end
            local catalog=ns.CustomAchievementAdapter.Catalog()
            assert(reads==1)
            for _,row in ipairs(catalog.records) do assert(row.current==nil and not row.progress.available) end
            GetNumSkillLines=function() reads=reads+1; return 1 end
            GetSkillLineInfo=function() return "Alchemy",false,nil,50 end
            catalog=ns.CustomAchievementAdapter.Catalog()
            assert(reads==2 and catalog.byKey["custom:prof75"].current==50)
        ''')

    def test_reputation_observations_are_once_per_faction_and_refresh_next_pass(self):
        self.check('''
            SelectCatalog("ex5","ex10","ex30","ambAlliance","repTimbermaw")
            local reads,value={},1000
            GetFactionInfoByID=function(id)
                reads[id]=(reads[id] or 0)+1
                return "Faction",false,0,0,0,value
            end
            local catalog=ns.CustomAchievementAdapter.Catalog()
            for id,count in pairs(reads) do assert(count==1) end
            assert(catalog.byKey["custom:repTimbermaw"].current==1000)
            value=2000
            catalog=ns.CustomAchievementAdapter.Catalog()
            for id,count in pairs(reads) do assert(count==2) end
            assert(catalog.byKey["custom:repTimbermaw"].current==2000)
            local before={}
            for id,count in pairs(reads) do before[id]=count end
            local criteria=ns.CustomAchievementAdapter.Criteria(catalog.byKey["custom:ambAlliance"])
            assert(#criteria.items==4)
            local changed=0
            for id,count in pairs(reads) do
                if count~=before[id] then assert(count==before[id]+1); changed=changed+1 end
            end
            assert(changed==4)
        ''')

    def test_overlay_bucket_candidates_preserve_exact_two_unit_match_boundaries(self):
        self.check('''
            testZone="Moonglade"; testSubzone="Moonglade"
            local dx,dy=0,0
            C_MapExplorationInfo={GetExploredMapTextures=function(id)
                assert(id==1450)
                return {{offsetX=244+dx,offsetY=89+dy,textureWidth=64,textureHeight=64,isShownByMouseOver=false}}
            end}
            for _,case in ipairs({{2,2,true},{-2,-2,true},{1.999,-1.999,true},
                                  {2.001,0,false},{-2.001,0,false},{0,2.001,false},{0,-2.001,false}}) do
                dx,dy=case[1],case[2]
                saved.explorationEvidence=nil
                testClock=testClock+6
                local current,needed=ns.FA.WithProgressSnapshot(ns.FA.BY_KEY.explore855.progress)
                assert(current==(case[3] and 1 or 0) and needed==1)
            end
        ''')

    def test_native_oversized_criteria_are_unknown_without_iteration_or_loss_of_authoritative_completion(self):
        self.check('''
            local achievement
            for _,a in ipairs(ns.FA.ALL) do if a.native then achievement=a; break end end
            assert(achievement)
            local countReads,criteriaReads,completed=0,0,false
            GetAchievementInfo=function(id) return id,"Native challenge",0,completed end
            GetAchievementNumCriteria=function() countReads=countReads+1; return 257 end
            GetAchievementCriteriaInfo=function() criteriaReads=criteriaReads+1; error("Oversized criteria must not be read") end
            ns.FA.WithProgressSnapshot(function()
                local current,needed=achievement.progress()
                assert(current==nil and needed==257)
                local list=achievement.dynamicList()
                assert(#list==0 and list.truncated and list.count==257)
                current,needed=achievement.progress()
                assert(current==nil and needed==257)
            end)
            assert(countReads==1 and criteriaReads==0)
            completed=true
            local current,needed=ns.FA.WithProgressSnapshot(achievement.progress)
            assert(current==1 and needed==1 and countReads==1 and criteriaReads==0)
        ''')

    def test_native_criteria_at_the_supported_limit_are_read_once_per_pass(self):
        self.check('''
            local achievement
            for _,a in ipairs(ns.FA.ALL) do if a.native then achievement=a; break end end
            assert(achievement)
            local countReads,criteriaReads=0,0
            GetAchievementInfo=function(id) return id,"Native challenge",0,false end
            GetAchievementNumCriteria=function() countReads=countReads+1; return 256 end
            GetAchievementCriteriaInfo=function(id,index)
                criteriaReads=criteriaReads+1
                return "Criterion "..index,0,index<=128
            end
            ns.FA.WithProgressSnapshot(function()
                local current,needed=achievement.progress()
                assert(current==128 and needed==256)
                assert(#achievement.dynamicList()==256)
                current,needed=achievement.progress()
                assert(current==128 and needed==256)
            end)
            assert(countReads==1 and criteriaReads==256)
        ''')


if __name__ == "__main__":
    unittest.main()
