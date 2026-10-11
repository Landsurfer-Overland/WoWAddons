"""Legacy reward browsing uses canonical cached rows, not a new achievement source."""
import unittest

from test_legacy_wrath_ui import Harness
from test_iteration3_categories import FIXTURES
from test_iteration4_presentation import ZONE_FIXTURES


class LegacyPointCategoryTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute(FIXTURES + ZONE_FIXTURES)

    def check(self, code):
        self.h.execute(code)

    def test_reward_api_selects_positive_values_not_reward_text_or_character_points(self):
        self.check('''
            C_Traits.GetTraitCurrencyForAchievement=function(_,id)
                if id==62013 then return 1 end
                if id==62053 then return 2 end
                return 0
            end
            local P=ns.LegacyPresentation; local m=P.Build()
            local cat=m.byCategory['feats:legacy-points']
            assert(cat.name=='Legacy Point Achievements' and cat.parent=='feats')
            assert(m.byCategory.feats.children[1]==cat)
            local rows=P.Rows(m,cat.key)
            assert(#rows==2 and cat.aliasRows['legacy:62013'] and cat.aliasRows['legacy:62053'])
            assert(m.byKey['legacy:62382'].reward=='Earn 1 Legacy Point.')
            assert(not cat.aliasRows['legacy:62382'] and not cat.aliasRows['custom:first'])
            assert(#P.Rows(m,cat.key,'','Incomplete')==2)
            assert(#P.Rows(m,cat.key,'','Completed')==0)
            assert(#calls==0)
        ''')

    def test_missing_reward_api_keeps_section_empty_without_guessing(self):
        self.check('''
            C_Traits.GetTraitCurrencyForAchievement=nil
            local P=ns.LegacyPresentation; local m=P.Build()
            assert(m.byCategory['feats:legacy-points'])
            assert(#P.Rows(m,'feats:legacy-points')==0)
            local done,total,unknown=P.Count(m,'feats:legacy-points')
            assert(done==0 and total==0 and unknown==0)
            assert(#m.records==5 and #P.Rows(m,'legacy')==3)
            assert(m.byKey['legacy:62013'].pointType=='unknown')
        ''')

    def test_original_categories_counts_points_and_saved_progress_stay_intact(self):
        self.check('''
            local P=ns.LegacyPresentation; local m=P.Build()
            local row=m.byKey['legacy:62013']
            assert(row.category=='professions:alchemy' and row.unifiedRoot=='professions')
            assert(P.Rows(m,'professions:alchemy')[1]==P.Rows(m,'feats:legacy-points')[1])
            assert(#m.records==5 and #P.Rows(m,'summary')==5)
            local done,total=P.Count(m,'summary'); assert(done==1 and total==5)
            done,total=P.Count(m,'professions'); assert(done==0 and total==1)
            done,total=P.Count(m,'feats'); assert(done==0 and total==0)
            assert(m.custom.points==10 and m.custom.possiblePoints==30 and m.native.points==16)
            assert(saved.done.first==1730000000 and saved.done.second==nil)
            assert(saved.history[1]=='keep' and saved.explored.zone.old and next(saved.tracked)==nil)
            P.Invalidate(m)
            done,total=P.Count(m,'feats'); assert(done==0 and total==0)
            assert(#P.Rows(m,'feats')==0 and #P.Rows(m,'feats:legacy-points')==1)
            assert(row.category=='professions:alchemy' and #calls==0)
        ''')

    def test_search_filters_and_counts_match_without_index(self):
        self.check('''
            SetCustomRows({})
            local rows={NativeRow(90001,'One',1),NativeRow(90002,'Two',1),NativeRow(90003,'Three',1)}
            for _,row in ipairs(rows) do row.pointValue=1 end
            rows[1].completed=true; rows[2].completed=false; rows[3].completed=nil
            rows[2].description='Find the hidden valley'
            local P=ns.LegacyPresentation
            local m=P.Build(nil,NativeCatalog({NativeCategory(1,'General')},rows))
            for pass=1,2 do
                assert(#P.Rows(m,'feats:legacy-points')==3)
                assert(P.Rows(m,'feats:legacy-points','VALLEY')[1].id==90002)
                assert(#P.Rows(m,'feats:legacy-points','missing')==0)
                assert(P.Rows(m,'feats:legacy-points','','Completed')[1].id==90001)
                assert(P.Rows(m,'feats:legacy-points','','Incomplete')[1].id==90002)
                assert(#P.Rows(m,'feats:legacy-points','','Legacy Challenges')==3)
                assert(#P.Rows(m,'feats:legacy-points','','Character Achievements')==0)
                local done,total,unknown=P.Count(m,'feats:legacy-points')
                assert(done==1 and total==3 and unknown==1)
                P.Invalidate(m)
            end
        ''')

    def test_combined_reward_is_selected_once_without_changing_card_completion(self):
        self.check('''
            local c,n=ZonePair(802,'Westfall'); SetCustomRows({c})
            local P=ns.LegacyPresentation; local m=P.Build(nil,ZoneCatalog({n,n}))
            local rows=P.Rows(m,'feats:legacy-points')
            assert(#rows==1 and #m.records==1 and rows[1].source=='combined')
            assert(rows[1].pointType=='character' and rows[1].native.pointValue==1)
            assert(rows[1].category=='exploration:eastern-kingdoms')
            assert(rows[1]==P.Rows(m,'exploration:eastern-kingdoms')[1])
            for pass=1,2 do
                local done,total=P.Count(m,'feats:legacy-points'); assert(done==0 and total==1)
                assert(#P.Rows(m,'feats:legacy-points','','Completed')==0)
                assert(#P.Rows(m,'feats:legacy-points','','Incomplete')==1)
                assert(#P.Rows(m,'legacy','','Completed')==1)
                assert(#P.Rows(m,'feats:legacy-points','','Character Achievements')==1)
                done,total=P.Count(m,'summary'); assert(done==0 and total==1)
                done,total=P.Count(m,'feats'); assert(done==0 and total==0)
                P.Invalidate(m)
            end
            n.pointValue=0; n.points=0
            m=P.Build(nil,ZoneCatalog({n}))
            assert(#P.Rows(m,'feats:legacy-points')==0 and #m.records==1)
        ''')

    def test_queries_reuse_cache_and_never_rescan_native_or_custom_catalog(self):
        self.check('''
            local P=ns.LegacyPresentation; local m=P.Build()
            ns.LegacyAdapter.Catalog=function() error('Unexpected native catalog rebuild') end
            ns.CustomAchievementAdapter.Catalog=function() error('Unexpected custom catalog rebuild') end
            C_Traits.GetTraitCurrencyForAchievement=function() error('Unexpected reward lookup') end
            GetAchievementInfo=function() error('Unexpected achievement lookup') end
            for i=1,30 do
                local rows=P.Rows(m,'feats:legacy-points','ALCHEMY','Incomplete')
                assert(#rows==1); rows[1]=nil
                local done,total=P.Count(m,'feats:legacy-points'); assert(done==0 and total==1)
            end
            assert(#m._queryOrder==1 and #m._membership['feats:legacy-points']==1)
            for i=1,40 do P.Rows(m,'feats:legacy-points','query'..i) end
            assert(#m._queryOrder==32 and #calls==0 and #timers==0)
        ''')

    def test_native_feat_and_cross_category_alias_do_not_double_parent_counts(self):
        self.check('''
            SetCustomRows({})
            local feat=NativeRow(91001,'True feat',81)
            feat.achievementType='feat_of_strength'; feat.pointValue=3; feat.completed=true
            local quest=NativeRow(91002,'A quest',2); quest.pointValue=1
            local P=ns.LegacyPresentation
            local m=P.Build(nil,NativeCatalog({NativeCategory(81,'Feats of Strength'),NativeCategory(2,'Quests')},{feat,quest}))
            for pass=1,2 do
                local done,total=P.Count(m,'feats'); assert(done==1 and total==1)
                done,total=P.Count(m,'summary'); assert(done==1 and total==2)
                done,total=P.Count(m,'feats:legacy-points'); assert(done==1 and total==2)
                assert(#P.Rows(m,'feats:legacy-points')==2)
                assert(m.byKey[feat.key].category=='feats:special')
                assert(m.byKey[quest.key].unifiedRoot=='quests')
                P.Invalidate(m)
            end
        ''')

    def test_partial_catalog_only_includes_confirmed_available_rewards(self):
        self.check('''
            SetCustomRows({})
            local known=NativeRow(91001,'Known reward',1); known.pointValue=1
            local unknown=NativeRow(91002,'Reward not yet available',1)
            unknown.pointType='unknown'; unknown.pointValue=nil
            local catalog=NativeCatalog({NativeCategory(1,'General')},{known,unknown})
            catalog.partial=true; catalog.notice='Visible challenges only'
            local P=ns.LegacyPresentation; local m=P.Build(nil,catalog)
            assert(m.native.partial and m.native.notice==catalog.notice)
            assert(#m.records==2 and #P.Rows(m,'feats:legacy-points')==1)
            assert(P.Rows(m,'feats:legacy-points')[1].id==known.id)
            unknown.pointType='legacy'; unknown.pointValue=2
            local nextModel=P.Build(nil,catalog)
            assert(#P.Rows(nextModel,'feats:legacy-points')==2)
            assert(P.CategoryKey(nextModel,'feats:legacy-points')=='feats:legacy-points')
        ''')

    def test_section_navigation_and_search_reuse_existing_view_without_refresh(self):
        self.check('''
            local m=ns.LegacyPresentation.Build()
            host=CreateFrame('Frame','LegacyPointCategoryHost'); host:SetSize(1024,860)
            local refreshCalls=0
            local view=ns.WrathAchievementUI.Create(host,function(fn) fn() end,
                function() refreshCalls=refreshCalls+1 end,{})
            view:Fit(host); view:SetModel(m)
            local function button(key)
                for _,b in ipairs(view.categories) do
                    if b:IsShown() and b.category.key==key then return b end
                end
            end
            assert(button('feats') and not button('feats:legacy-points'))
            button('feats').expandButton:Fire('OnClick')
            local child=button('feats:legacy-points'); assert(child)
            child:Fire('OnClick')
            assert(view.category=='feats:legacy-points' and view.expanded.feats)
            assert(view.categoryHeading.title:GetText()=='Feats of Strength')
            assert(view.categoryHeading.subtitle:GetText()=='Legacy Point Achievements')
            assert(view.cards[1]:IsShown() and view.cards[1].record.id==62013)
            local frameCount=#frames
            ns.LegacyPresentation.Build=function() error('Navigation rebuilt model') end
            for i=1,20 do view:Render() end
            assert(#frames==frameCount and refreshCalls==0 and #calls==0 and #timers==0)
        ''')


if __name__ == '__main__':
    unittest.main()
