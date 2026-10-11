"""Iteration 5 parent navigation and source-safe exploration presentation.

Runs the real Lua presentation and XML callbacks. Logical geometry does not
claim native rendering, game input propagation, or in-game progression tests.
"""
import unittest

from test_legacy_wrath_ui import Harness
from test_iteration3_categories import FIXTURES
from test_iteration4_presentation import ZONE_FIXTURES
from test_progression_addendum import CoreHarness


class Iteration5CategoryTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute(FIXTURES + ZONE_FIXTURES)

    def check(self, code):
        self.h.execute(code)

    def create_view(self):
        self.check('''
            local broad=CustomRow('gold100','general','MONEY','gold')
            local level=CustomRow('lvl10','general','LEVELS','level')
            local collection=CustomRow('pet1','general','COLLECTIONS','pets')
            local profession=CustomRow('prof75','professions','PROFESSIONS','prof')
            local alchemy=CustomRow('alchemy75','professions','ALCHEMY',nil)
            SetCustomRows({broad,level,collection,profession,alchemy})
            model=ns.LegacyPresentation.Build(nil,NativeCatalog({},{}))
            GameFontNormal={name='normal'}; GameFontNormalSmall={name='small'}
            host=CreateFrame('Frame','Iteration5CategoryHost'); host:SetSize(1024,860)
            function guard(fn) fn() end
            refreshCalls=0
            view=ns.WrathAchievementUI.Create(host,guard,function() refreshCalls=refreshCalls+1 end,{})
            view:Fit(host); view:SetModel(model)
            function categoryButton(key)
                for _,button in ipairs(view.categories) do
                    if button:IsShown() and button.category.key==key then return button end
                end
            end
            renderCalls=0
            local originalRender=view.Render
            view.Render=function(self,reason) renderCalls=renderCalls+1; return originalRender(self,reason) end
        ''')

    def test_whole_parent_row_selects_direct_list_and_toggles_once(self):
        self.create_view()
        self.check('''
            local before=view.navigationVersion or 0
            categoryButton('general'):Fire('OnClick')
            assert(view.category=='general' and view.expanded.general and renderCalls==1)
            assert(view.navigationVersion==before+1 and view.focus==nil and view.selected==nil)
            assert(categoryButton('general').selection:IsShown())
            assert(categoryButton('general:progression') and categoryButton('general:character'))
            local rows=ns.LegacyPresentation.Rows(view.model,view.category)
            assert(#rows==1 and rows[1].savedKey=='gold100')
            categoryButton('general'):Fire('OnClick')
            assert(view.category=='general' and not view.expanded.general and renderCalls==2)
            assert(view.navigationVersion==before+2 and not categoryButton('general:progression'))
            assert(refreshCalls==0 and #calls==0 and #timers==0)
        ''')

    def test_indicator_only_toggles_without_selecting_or_double_refresh(self):
        self.create_view()
        self.check('''
            categoryButton('general').expandButton:Fire('OnClick')
            assert(view.category=='summary' and view.expanded.general and renderCalls==1)
            categoryButton('general').expandButton:Fire('OnClick')
            assert(view.category=='summary' and not view.expanded.general and renderCalls==2)
            assert(refreshCalls==0 and #calls==0 and #timers==0)
        ''')

    def test_leaf_selection_preserves_parent_expansion_and_clears_card_focus(self):
        self.create_view()
        self.check('''
            categoryButton('general'):Fire('OnClick')
            view.focus=view.model.byKey['custom:gold100']; view.selected='custom:gold100'
            local before=view.navigationVersion
            categoryButton('general:progression'):Fire('OnClick')
            assert(view.category=='general:progression' and view.expanded.general)
            assert(view.focus==nil and view.selected==nil and view.navigationVersion==before)
            assert(#ns.LegacyPresentation.Rows(view.model,view.category)==1 and renderCalls==2)
            assert(not categoryButton('general:progression').expandButton:IsShown())
            assert(refreshCalls==0 and #calls==0)
        ''')

    def test_sidebar_rows_are_thicker_without_erasing_child_distinction(self):
        self.create_view()
        self.check('''
            categoryButton('general'):Fire('OnClick')
            local parent,child=categoryButton('general'),categoryButton('general:progression')
            assert(parent:GetHeight()==24 and child:GetHeight()==24)
            assert(child.depth==1 and child.points[1][4]==4)
            assert(child:GetWidth()==parent:GetWidth())
            assert(child.connector:IsShown() and not parent.connector:IsShown())
            assert(parent.label:GetFontObject()==GameFontNormal and child.label:GetFontObject()==GameFontNormalSmall)
            assert(parent.expandButton:GetHeight()==20 and child.expandButton:GetHeight()==20)
            assert(child.label:GetWidth()>100 and child.label.wordWrap==false)
        ''')

    def test_repeat_parent_toggles_reuse_rows_and_never_rebuild_catalog(self):
        self.create_view()
        self.check('''
            categoryButton('general'):Fire('OnClick'); categoryButton('general'):Fire('OnClick')
            local before=#frames; local catalog=view.model
            ns.CustomAchievementAdapter.Catalog=function() error('No catalog rebuild during navigation') end
            ns.LegacyAdapter.Catalog=ns.CustomAchievementAdapter.Catalog
            for i=1,40 do categoryButton('general'):Fire('OnClick') end
            assert(#frames==before and view.model==catalog and not view.expanded.general)
            assert(renderCalls==42 and refreshCalls==0 and #timers==0 and #calls==0)
        ''')

    def test_uniform_category_geometry_and_margins_on_each_size(self):
        self.create_view()
        self.check('''
            view.expanded.general=true
            view:Render()
            local model=view.model
            ns.CustomAchievementAdapter.Catalog=function() error('Sizing rescanned catalog') end
            ns.LegacyAdapter.Catalog=ns.CustomAchievementAdapter.Catalog
            for _,name in ipairs({'Compact','Standard','Large','Compact'}) do
                local size=ns.WrathAchievementUI.PRESETS[name]
                view:Layout(size[1],size[2])
                local previous,foundChild
                for _,button in ipairs(view.categories) do
                    if button:IsShown() then
                        assert(button:GetWidth()==view.categoryScroll:GetWidth()-8)
                        assert(button:GetHeight()==24 and view.categoryRowHeight==24 and view.categoryRowGap==1)
                        assert(button.points[1][4]==4)
                        assert(button.label.points[1][4]==21+math.min(button.depth,3)*14)
                        if previous then
                            assert(previous:GetBottom()-button:GetTop()==view.categoryRowGap)
                        end
                        if button.depth>0 then foundChild=true end
                        previous=button
                    end
                end
                assert(foundChild and view.expanded.general and view.model==model)
                assert(view.categoryChild:GetHeight()>=view.categoryHeight and #calls==0)
            end
        ''')

    def test_cached_sidebar_does_not_resize_rows_or_allocate_frames_on_repeat_render(self):
        self.create_view()
        self.check('''
            view.expanded.general=true; view:Render()
            local count=#frames
            for _,button in ipairs(view.categories) do
                button.SetSize=function() error('Unchanged sidebar resized rows') end
            end
            for i=1,30 do view:RenderCategories() end
            assert(#frames==count and refreshCalls==0 and #calls==0)
        ''')

    def test_selected_summary_uses_additive_original_wrath_artwork_without_black_backing(self):
        self.create_view()
        self.check('''
            local summary=categoryButton('summary')
            assert(summary.selection:IsShown() and summary.selection:GetBlendMode()=='ADD')
            assert(summary.selection.textureValue=='Interface\\\\AchievementFrame\\\\UI-Achievement-Category-Highlight')
            assert(summary.selection.allPoints==nil and #summary.selection.points==2)
            assert(summary.selection.points[1][1]=='TOPLEFT' and summary.selection.points[2][1]=='BOTTOMRIGHT')
            assert(summary.selection.points[2][4]==-1 and summary.selection.points[2][5]==-7)
            assert(summary.background:GetHeight()==32 and summary.background.allPoints==nil)
            assert(summary:GetHeight()==24 and #calls==0)
        ''')

    def test_expansion_inserts_compact_rows_and_pushes_following_stack_down(self):
        self.create_view()
        self.check('''
            local parent=categoryButton('general')
            local parentY=parent:GetTop()
            local followingY=categoryButton('professions'):GetTop()
            parent.expandButton:Fire('OnClick')
            local childCount=0
            for _,button in ipairs(view.categories) do
                if button:IsShown() and button.depth>0 and button.category.key:find('^general:') then
                    childCount=childCount+1
                end
            end
            assert(childCount>0 and categoryButton('general'):GetTop()==parentY)
            assert(categoryButton('professions'):GetTop()==followingY-childCount*25)
            local framesBefore=#frames
            categoryButton('general').expandButton:Fire('OnClick')
            assert(categoryButton('professions'):GetTop()==followingY)
            assert(categoryButton('general:progression')==nil and #frames==framesBefore)
            assert(refreshCalls==0 and #timers==0 and #calls==0)
        ''')

    def test_statistics_parent_navigation_uses_its_independent_expansion_state(self):
        self.create_view()
        self.check('''
            local child={key='stats:child',name='Child',children={}}
            local parent={key='stats:parent',name='Parent',children={child}}
            view.tab='statistics'; view.statisticsCatalog={roots={parent},byCategory={[parent.key]=parent,[child.key]=child}}
            view.sidebarSignature=nil
            -- The navigation callback uses the actual renderer for its sidebar;
            -- statistic retrieval is a separate adapter outside this assertion.
            view.Render=function(self) renderCalls=renderCalls+1; self:RenderCategories() end
            view:RenderCategories()
            categoryButton(parent.key):Fire('OnClick')
            assert(view.statisticsCategory==parent.key and view.statisticsExpanded[parent.key])
            assert(view.category=='summary' and view.expanded[parent.key]==nil and renderCalls==1)
            categoryButton(child.key):Fire('OnClick')
            assert(view.statisticsCategory==child.key and view.statisticsExpanded[parent.key] and renderCalls==2)
            categoryButton(parent.key).expandButton:Fire('OnClick')
            assert(view.statisticsCategory==child.key and not view.statisticsExpanded[parent.key] and renderCalls==3)
            assert(refreshCalls==0 and #calls==0)
        ''')

    def test_broad_general_rows_stay_parent_and_explicit_children_remain_narrow(self):
        self.check('''
            local broad=CustomRow('fall','general','AROUND AZEROTH',nil)
            local money=CustomRow('gold100','general','MONEY','gold')
            local food=CustomRow('foods','general','FOOD & DRINK',nil)
            local level=CustomRow('lvl10','general','LEVELS','level')
            local riding=CustomRow('riding75','general','RIDING','riding')
            local mount=CustomRow('mount10','general','COLLECTIONS',nil)
            local misc=CustomRow('authoredMisc','general','MISCELLANEOUS',nil)
            SetCustomRows({broad,money,food,level,riding,mount,misc})
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog({},{})); local P=ns.LegacyPresentation
            assert(#P.Rows(m,'general')==3)
            assert(m.byKey[broad.key].category=='general' and m.byKey[food.key].category=='general')
            assert(#P.Rows(m,'general:progression')==2 and #P.Rows(m,'general:character')==1)
            assert(#P.Rows(m,'general:miscellaneous')==1)
            local _,total=P.Count(m,'general'); assert(total==7)
            P.Invalidate(m)
            assert(#P.Rows(m,'general')==3 and #P.Rows(m,'general:progression')==2)
            _,total=P.Count(m,'general'); assert(total==7)
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_native_general_maps_broad_rows_to_parent_using_category_metadata(self):
        self.check('''
            SetCustomRows({})
            local categories={NativeCategory(1,'General'),NativeCategory(2,'Progression',1),
                NativeCategory(3,'Collections',1),NativeCategory(4,'Miscellaneous',1)}
            local native=NativeCatalog(categories,{NativeRow(1,'Broad challenge',1),NativeRow(2,'Level title',2),
                NativeRow(3,'Mount title',3),NativeRow(4,'Misc title',4)})
            local m=ns.LegacyPresentation.Build(nil,native); local P=ns.LegacyPresentation
            assert(#P.Rows(m,'general')==1 and P.Rows(m,'general')[1].key=='legacy:1')
            assert(m.byKey['legacy:2'].category=='general:progression')
            assert(m.byKey['legacy:3'].category=='general:character')
            assert(m.byKey['legacy:4'].category=='general:miscellaneous')
            local _,total=P.Count(m,'general'); assert(total==4)
            assert(#P.Rows(m,'legacy-category:1')==4 and #calls==0)
        ''')

    def test_broad_profession_and_reputation_lists_are_direct_without_aggregation(self):
        self.check('''
            local profession=CustomRow('prof75','professions','PROFESSIONS','prof')
            local professionMeta=CustomRow('paythebills','professions','SECONDARY',nil)
            local skill=CustomRow('alchemy75','professions','ALCHEMY',nil)
            local reputation=CustomRow('ex5','reputation','EXALTED','exalted')
            local faction=CustomRow('repArgent','reputation','AZEROTH FACTIONS',nil)
            SetCustomRows({profession,professionMeta,skill,reputation,faction})
            local cats={NativeCategory(1,'Tradeskills'),NativeCategory(2,'Alchemy',1),
                NativeCategory(3,'Reputation'),NativeCategory(4,'Exalted',3),
                NativeCategory(5,'Alliance',3),NativeCategory(6,'Timbermaw Hold',3)}
            local m=ns.LegacyPresentation.Build(nil,NativeCatalog(cats,{
                NativeRow(1,'Broad skills',1),NativeRow(2,'Alchemy',2),NativeRow(3,'Broad reputation',3),
                NativeRow(4,'Exalted totals',4),NativeRow(5,'Alliance faction',5),NativeRow(6,'Timbermaw faction',6)}))
            local P=ns.LegacyPresentation
            assert(#P.Rows(m,'professions')==3 and #P.Rows(m,'professions:alchemy')==2)
            assert(#P.Rows(m,'reputation')==3 and #P.Rows(m,'reputation:other-factions')==2)
            assert(#P.Rows(m,'reputation:alliance')==1)
            assert(m.byKey['legacy:4'].category=='reputation')
            local _,total=P.Count(m,'professions'); assert(total==5)
            _,total=P.Count(m,'reputation'); assert(total==6)
            assert(#calls==0)
        ''')

    def test_verified_world_meta_preserves_stable_keys_fifty_points_and_native_relationship(self):
        self.check('''
            local east,en=ZonePair(776,'Elwynn Forest')
            local west,kn=ZonePair(855,'Moonglade'); west.customGeography='Kalimdor'
            local ek=CustomRow('exploreEK','exploration','AZEROTH',nil); ek.name='Explore Eastern Kingdoms'
            ek.exploration={kind='continent',children={east.key}}; ek.customGeography='Eastern Kingdoms'
            local kal=CustomRow('exploreKal','exploration','AZEROTH',nil); kal.name='Explore Kalimdor'
            kal.exploration={kind='continent',children={west.key}}; kal.customGeography='Kalimdor'
            local world=CustomRow('worldexplorer','exploration','AZEROTH',nil); world.name='Explore Azeroth'
            world.id=46; world.pointValue=50; world.points=50
            world.exploration={kind='world',children={ek.key,kal.key}}
            local ne=NativeRow(62353,'Explore Eastern Kingdoms',1)
            local nk=NativeRow(62355,'Explore Kalimdor',1)
            local nw=NativeRow(62053,'Explore Azeroth',1); nw.completed=true
            nw.scopeType='account'; nw.pointValue=0; nw.points=0
            local wrapper=NativeRow(64015,'Explorer',1); wrapper.pointValue=1; wrapper.points=1
            SetCustomRows({east,west,ek,kal,world})
            local oldGetter=GetAchievementCriteriaInfo
            GetAchievementNumCriteria=function(id) return id==62053 and 2 or 1 end
            GetAchievementCriteriaInfo=function(id,index)
                local child=({[62353]=776,[62355]=855})[id]
                if id==62053 then child=index==1 and 62353 or 62355 end
                if child then return 'Child',8,true,1,1,nil,0,child end
                return oldGetter(id,index)
            end
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({en,kn,ne,nk,nw,wrapper}))
            local card=m.byKey['custom:worldexplorer']
            assert(card.source=='combined' and card.name=='Explore Azeroth' and card.id==46)
            assert(card==m.byKey['legacy:62053'] and card.native.id==62053)
            assert(card.pointValue==50 and card.points==50 and card.native.pointValue==0)
            assert(card.completed==false and card.native.completed==true)
            assert(m.byKey['legacy:64015']~=card and m.byKey['legacy:64015'].pointValue==1)
            assert(#ns.LegacyPresentation.Rows(m,'exploration:world')==2)
            assert(saved.done.first==1730000000 and saved.done.worldexplorer==nil and #calls==0)
        ''')

    def test_unverified_same_title_world_meta_stays_separate_without_fake_points_or_awards(self):
        self.check('''
            local world=CustomRow('worldexplorer','exploration','AZEROTH',nil); world.name='Explore Azeroth'
            world.pointValue=50; world.points=50; world.completed=false
            world.exploration={kind='world',children={'custom:exploreEK','custom:exploreKal'}}
            local native=NativeRow(62053,'Explore Azeroth',1); native.completed=true
            native.pointValue=0; native.points=0
            SetCustomRows({world})
            local m=ns.LegacyPresentation.Build(nil,ZoneCatalog({native}))
            assert(#m.records==2 and m.byKey[world.key]~=m.byKey[native.key])
            assert(m.byKey[world.key].pointValue==50 and m.byKey[world.key].completed==false)
            assert(m.byKey[native.key].pointValue==0 and m.byKey[native.key].completed==true)
            assert(#m.relationshipAudit==1 and #m.relationships==0)
            assert(saved.done.worldexplorer==nil and #calls==0)
        ''')


class Iteration5ExplorationDefinitionTests(unittest.TestCase):
    def test_production_catalog_has_actual_broad_parent_records_and_separate_children(self):
        h = CoreHarness()
        # CoreHarness begins with adapter/UI doubles, then loads the production
        # definitions. Rebind the real adapter to those production definitions.
        h.load('Integrations/CustomAdapter.lua')
        h.execute(FIXTURES)
        h.execute('''
            local P=ns.LegacyPresentation
            local m=P.Build(nil,NativeCatalog({},{}))
            for _,key in ipairs({'gold100','fall','critters','books'}) do
                assert(m.byKey['custom:'..key].category=='general')
            end
            assert(m.byKey['custom:lvl10'].category=='general:progression')
            assert(m.byKey['custom:pet1'].category=='general:character')
            assert(m.byKey['custom:prof75'].category=='professions')
            assert(m.byKey['custom:paythebills'].category=='professions')
            assert(m.byKey['custom:ex5'].category=='reputation')
            assert(#P.Rows(m,'general')>0 and #P.Rows(m,'professions')>0 and #P.Rows(m,'reputation')>0)
            local _,generalTotal=P.Count(m,'general')
            assert(generalTotal>#P.Rows(m,'general'))
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_authored_exploration_points_and_stable_world_definition_remain_consistent(self):
        h = CoreHarness()
        h.execute('''
            local world=ns.FA.BY_KEY.worldexplorer
            assert(world.key=='worldexplorer' and world.id==46 and world.pts==50)
            assert(world.name=='Explore Azeroth')
            assert(ns.FA.BY_KEY.exploreEK.pts==25 and ns.FA.BY_KEY.exploreKal.pts==25)
            for _,zone in ipairs(ns.EXPLORE) do
                local key=zone.key or 'explore'..zone.id
                local a=ns.FA.BY_KEY[key]
                assert(a and a.pts==10 and a.id==zone.id)
            end
            assert(saved.done.first==1730000000 and saved.history[1]=='keep')
        ''')


if __name__ == '__main__':
    unittest.main()
