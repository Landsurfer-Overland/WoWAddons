"""Reference Summary layout, real navigation and bounded card reuse.

The client double verifies geometry/data contracts, not pixel rendering.
"""
import unittest
import test_wrath_iteration3_ui as fixtures


class WrathSummaryLayoutTests(unittest.TestCase):
    setUp = fixtures.Iteration3UITests.setUp
    check = fixtures.Iteration3UITests.check
    def test_recent_rows_precede_total_and_paired_category_progress_at_every_size(self):
        self.check('''
            for _,name in ipairs({'Compact','Standard','Large'}) do
                local size=ns.WrathAchievementUI.PRESETS[name]
                view:Layout(size[1],size[2])
                assert(view.headings[1]:GetText()=='Recent Achievements')
                assert(view.headings[2]:GetText()=='Progress Overview')
                assert(view.cards[1]:GetHeight()==48 and view.cards[1].compact)
                assert(view.cards[1]:GetTop()>view.headings[2]:GetTop())
                assert(view.bars[1].label:GetText()=='Achievements Earned')
                assert(view.bars[1].button.categoryKey=='summary')
                local done,total=ns.LegacyPresentation.Count(view.model,'summary')
                assert(view.bars[1].text:GetText()==done..'/'..total)
                assert(view.bars[1]:GetWidth()==view.contentWidth-30)
                local expected={'general','quests','exploration','pvp','dungeons','professions','reputation','classes','feats'}
                for i,key in ipairs(expected) do
                    local bar=view.bars[i+1]
                    assert(bar.button.categoryKey==key and bar:GetWidth()==(view.contentWidth-48)/2)
                    assert(bar.label:GetWidth()+bar.text:GetWidth()+16==bar:GetWidth())
                    assert(bar.label:GetWidth()>0 and bar.text.justify=='RIGHT')
                    if i%2==0 then
                        assert(bar:GetTop()==view.bars[i]:GetTop())
                        assert(bar:GetLeft()-view.bars[i]:GetRight()==18)
                    elseif i>1 then assert(view.bars[i-1]:GetTop()-bar:GetTop()==34) end
                end
                assert(not view.summaryNote:IsShown() and #calls==0)
            end
        ''')

    def test_recent_click_expands_details_and_reused_list_card_restores_geometry(self):
        self.check('''
            local recent=cardFor('custom:first')
            assert(recent.compact and recent:GetHeight()==48)
            assert(recent.icon:GetScale()==.6 and recent.shield:GetScale()==.7)
            assert(not recent.plusMinus:IsShown() and not recent.objectives:IsShown())
            assert(not recent.reward:IsShown() and not recent.tracked:IsShown())
            ns.LegacyPresentation.Criteria=function() return {items={{name='Recorded objective',completed=true}}} end
            recent:Fire('OnClick')
            local expanded=cardFor('custom:first')
            assert(expanded==view.cards[1] and expanded.selected and not expanded.compact)
            assert(expanded:GetHeight()>=110 and expanded.icon:GetScale()==1 and expanded.shield:GetScale()==1)
            assert(expanded.criteriaPool[1]:IsShown() and expanded.criteriaPool[1].label:GetText()=='Recorded objective')
            expanded:Fire('OnClick')
            assert(view.selected==nil and cardFor('custom:first').compact)
            view.category='general'; view:Render()
            for _,card in ipairs(view.cards) do
                if card:IsShown() then
                    assert(not card.compact and card:GetHeight()==84)
                    assert(card.icon:GetScale()==1 and card.shield:GetScale()==1)
                    assert(card.plusMinus:IsShown())
                    if card==expanded then
                        assert(card.description.points[1][5]==-30 and card.description.wordWrap)
                        assert(card.titleBackground:GetHeight()==24)
                        assert(card.dateCompleted.points[1][2]==card.shield)
                    end
                end
            end
            assert(#calls==0)
        ''')

    def test_four_most_recent_dated_records_only_without_fetching_criteria(self):
        self.check('''
            local dates={['custom:first']=20240101,['custom:second']=20240102,
                ['legacy:62013']=20240103,['legacy:62053']=20240104,['legacy:62382']=20240105}
            for key,day in pairs(dates) do
                local row=view.model.byKey[key]
                row.completed=true; row.dateSort=day; row.date='1/'..(day%100)..'/24'
                if row.source=='custom' then row.timestamp=1704067200+(day%100-1)*86400 end
            end
            ns.LegacyPresentation.Invalidate(view.model)
            ns.LegacyPresentation.Criteria=function() error('Collapsed Summary fetched criteria') end
            view:Render()
            local count=0
            for _,card in ipairs(view.cards) do if card:IsShown() then count=count+1; assert(card.compact) end end
            assert(count==4 and not cardFor('custom:first'))
            assert(view.cards[1].record.key=='legacy:62382' and view.cards[4].record.key=='custom:second')
            assert(#calls==0)
        ''')

    def test_category_progress_click_navigates_and_summary_total_keeps_summary(self):
        self.check('''
            view.bars[5].button:Fire('OnClick')
            assert(view.category=='pvp' and view.renderMode=='list')
            view.category='summary'; view:Render()
            view.bars[1].button:Fire('OnClick')
            assert(view.category=='summary' and view.renderMode=='summary')
            assert(#calls==0)
        ''')

    def test_summary_scroll_and_repeat_render_reuse_frames_without_catalog_work(self):
        self.check('''
            view:Render()
            local count,model=#frames,view.model
            ns.CustomAchievementAdapter.Catalog=function() error('Summary rebuilt custom catalog') end
            ns.LegacyAdapter.Catalog=function() error('Summary rebuilt native catalog') end
            ns.LegacyPresentation.Criteria=function() error('Collapsed Summary fetched criteria') end
            for i=1,30 do view:Render() end
            local summary=ns.LegacyPresentation.Summary
            ns.LegacyPresentation.Summary=function() error('Scroll rebuilt Summary') end
            for i=1,20 do view.contentScroll:SetVerticalScroll(i*4) end
            ns.LegacyPresentation.Summary=summary
            assert(#frames==count and view.model==model and #calls==0 and #timers==0)
        ''')

    def test_partial_unknown_markers_and_legend_do_not_leak_to_other_tabs(self):
        self.check('''
            view.model.native.partial=true; view.model.byKey['legacy:62013'].completed=nil
            ns.LegacyPresentation.Invalidate(view.model); view:Render()
            assert(view.bars[1].text:GetText()=='1/5 shown (1 unknown)')
            assert(view.summaryNote:IsShown() and view.summaryNote:GetText():find('Unknown completion',1,true))
            for _,bar in ipairs(view.bars) do
                if bar.button.categoryKey=='professions' then assert(bar.text:GetText()=='0/1* (?1)') end
            end
            for _,tab in ipairs({'rewards','trees','statistics'}) do
                view:SetTab(tab)
                assert(not view.summaryNote:IsShown())
            end
            view:SetTab('achievements'); assert(view.summaryNote:IsShown() and #calls==0)
        ''')
