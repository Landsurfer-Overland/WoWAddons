"""Bounded UI work and honest invalidation, exercised with Lua/XML fixtures.

These count real renderer calls and frame allocations. They do not substitute
for a live-client profile, texture validation or a native gameplay session.
"""
import unittest

import test_wrath_iteration3_ui as iteration3


class WrathUIPerformanceTests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check

    def large_rows(self, count=10000):
        self.check("""
            function installRows(count)
                local model=view.model
                model.records={}; model.byKey={}
                for i=1,count do
                    local row={key='custom:entry'..i,source='custom',sourceType='custom_character',
                        category='general',name='Entry '..i,description='A measured description',
                        achievement={},completed=false,scopeType='character',pointType='character',
                        pointValue=10,completionDetail='Not completed on this character'}
                    model.records[i]=row; model.byKey[row.key]=row
                end
                ns.LegacyPresentation.Invalidate(model)
                view.category='general'; view:SetModel(model)
            end
        """)
        self.check(f"installRows({count})")

    def test_large_list_scroll_reuses_query_and_navigation_and_bounds_cards(self):
        self.large_rows()
        self.check("""
            local P,originalRows=ns.LegacyPresentation,ns.LegacyPresentation.Rows
            local queries=0
            P.Rows=function(...) queries=queries+1; return originalRows(...) end
            debugprofilestop=function() return 1 end; ns.LegacyPerf.Enable(true)
            view:Render(); assert(queries==1)
            local before=ns.LegacyPerf.Snapshot()
            local categoryCalls=before.timings['UI.CategoryRender'] and before.timings['UI.CategoryRender'].calls or 0
            for i=1,100 do view.contentScroll:SetVerticalScroll(i*4400) end
            local after=ns.LegacyPerf.Snapshot()
            assert(queries==1 and after.timings['UI.ScrollRender'].calls==100)
            assert((after.timings['UI.CategoryRender'] and after.timings['UI.CategoryRender'].calls or 0)==categoryCalls)
            assert(#view.cards<=math.ceil(view.contentScroll:GetHeight()/88)+4)
            local last=cardFor('custom:entry5000')
            assert(last and last:GetHeight()==84 and view.contentChild:GetHeight()>800000)
            assert(view.root:GetScale()==1 and #calls==0)
        """)

    def test_offscreen_selected_measurement_creates_no_objective_widgets(self):
        self.large_rows(1000)
        self.check("""
            local P=ns.LegacyPresentation
            local criteriaCalls=0
            P.Criteria=function(row)
                criteriaCalls=criteriaCalls+1
                return {available=true,complete=true,items={{name='Large objective',current=3,required=10}}}
            end
            view.selected='custom:entry900'; view:Render()
            assert(criteriaCalls==1 and view.measureCache.row.key=='custom:entry900')
            for _,card in ipairs(view.cards) do
                assert(#card.criteriaPool==0 and #card.progressPool==0 and #card.metaPool==0)
            end
            view.contentScroll:SetVerticalScroll(view.listPlan.y+899*88)
            local selected=cardFor('custom:entry900')
            assert(selected==view.cards[1] and selected:GetHeight()+4==view.measureCache.advance)
            local measuredCalls=criteriaCalls
            for i=1,15 do view.contentScroll:SetVerticalScroll(view.listPlan.y+899*88+i) end
            assert(criteriaCalls==measuredCalls)
            local objectives=0
            for _,card in ipairs(view.cards) do objectives=objectives+#card.progressPool end
            assert(objectives==1)
            view.contentScroll:SetVerticalScroll(0)
            view.selected='custom:entry2'; view:Render()
            assert(cardFor('custom:entry2')==view.cards[1])
            objectives=0
            for _,card in ipairs(view.cards) do objectives=objectives+#card.progressPool end
            assert(objectives==1 and #calls==0)
        """)

    def test_expanded_objective_render_cap_preserves_adapter_data(self):
        self.large_rows(100)
        self.check("""
            local data={available=true,complete=true,items={}}
            for i=1,1000 do data.items[i]={name='Criterion '..i,completed=false} end
            ns.LegacyPresentation.Criteria=function() return data end
            view.selected='custom:entry1'; view:Render()
            local card=cardFor('custom:entry1')
            assert(#data.items==1000 and #card.criteriaPool==257)
            assert(card.criteriaPool[257].label:GetText()=='More objectives…')
            assert(card:GetHeight()+4==view.measureCache.advance)
            for i=1,20 do view.contentScroll:SetVerticalScroll(i*25) end
            assert(#card.criteriaPool==257 and #view.cards<=12 and #calls==0)
        """)

    def test_search_user_keystrokes_coalesce_and_programmatic_changes_remain_immediate(self):
        self.large_rows(200)
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            for _,query in ipairs({'E','En','Ent','Entry','Entry ','Entry 1','Entry 12'}) do
                view.searchBox:SetText(query); view.searchBox:Fire('OnTextChanged',true)
            end
            assert(view.search=='Entry 12' and #timers==1 and renders==0)
            FlushTimers()
            assert(renders==1 and #view.listPlan.rows==11 and cardFor('custom:entry12'))
            view.searchBox:SetText('Entry 199'); view.searchBox:Fire('OnTextChanged',false)
            assert(renders==2 and #view.listPlan.rows==1 and cardFor('custom:entry199'))
            assert(#calls==0)
        """)

    def test_canceled_search_timer_cannot_consume_new_typing_generation(self):
        self.large_rows(200)
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            view.searchBox:SetText('Entry 1'); view.searchBox:Fire('OnTextChanged',true)
            local canceled=timers[1]
            view.searchClear:Fire('OnClick'); assert(renders==1 and not view.searchQueued)
            view.searchBox:SetText('Entry 19'); view.searchBox:Fire('OnTextChanged',true)
            canceled(); assert(renders==1 and view.searchQueued)
            FlushTimers(); assert(renders==2 and #view.listPlan.rows==11)
            assert(view.filter=='All' and #calls==0)
        """)

    def test_unchanged_fit_and_deferred_layout_do_not_rebuild_twice(self):
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            for i=1,10 do view:Fit(host) end
            assert(renders==0)
            host:SetSize(1024,860); view:Fit(host,true)
            assert(renders==0 and view.contentWidth>600)
            view:SetModel(ns.LegacyPresentation.Build())
            assert(renders==1)
            host:SetSize(768,640); view:Fit(host)
            assert(renders==2 and view.contentWidth<600 and #calls==0)
        """)

    def test_consumed_tab_callback_renders_once_and_standalone_callback_still_works(self):
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            view.callbacks.onTab=function() view:Render(); return true end
            view:SetTab('statistics',true); assert(renders==1)
            view.callbacks.onTab=function() end
            view:SetTab('achievements',true); assert(renders==2)
            assert(view.tab=='achievements' and #calls==0)
        """)

    def test_reentrant_state_change_defers_latest_query_without_recursive_render(self):
        self.large_rows(200)
        self.check("""
            local original=view.RenderCard; local depth,maxDepth,changed=0,0,false
            view.RenderCard=function(self,...)
                depth=depth+1; maxDepth=math.max(maxDepth,depth)
                if not changed then
                    changed=true; self.search='Entry 199'; self:Render(); self:Render('scroll')
                end
                local result=original(self,...); depth=depth-1; return result
            end
            view:Render()
            assert(maxDepth==1 and #timers==1 and view.pendingRender=='full')
            FlushTimers()
            assert(maxDepth==1 and #timers==0 and not view.rendering and not view.renderQueued)
            assert(#view.listPlan.rows==1 and cardFor('custom:entry199'))
            assert(not cardFor('custom:entry1') and #calls==0)
        """)

    def test_recurring_unchanged_setter_callback_does_not_queue_an_endless_cycle(self):
        self.large_rows(100)
        self.check("""
            local original=view.RenderCard; local callbacks=0
            view.RenderCard=function(self,...)
                callbacks=callbacks+1; self:Render(); return original(self,...)
            end
            view:Render(); assert(callbacks>0 and #timers==0)
            for i=1,5 do FlushTimers() end
            assert(#timers==0 and not view.rendering and not view.pendingRender)
            assert(cardFor('custom:entry1') and #calls==0)
        """)

    def test_genuine_reentrant_model_replacement_redraws_completion_truth(self):
        self.check("""
            view.category=view.model.byKey['custom:second'].category; view:Render()
            local original=view.RenderCard; local changed=false
            view.RenderCard=function(self,...)
                if not changed then
                    changed=true; saved.done.second=1730001000
                    self:SetModel(ns.LegacyPresentation.Build())
                end
                return original(self,...)
            end
            view:Render(); assert(#timers==1)
            FlushTimers()
            local card=cardFor('custom:second')
            assert(card.saturated and card.record.completed and view.model.custom.points==30)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='30')
            assert(not view.renderQueued and #timers==0 and #calls==0)
        """)

    def test_render_error_clears_deferred_work_and_preserves_original_failure(self):
        self.large_rows(100)
        self.check("""
            local original=view.RenderCard
            view.RenderCard=function(self,...)
                self.searchBox:SetText('Entry 2'); self.searchBox:Fire('OnTextChanged',true)
                self:Render(); error('Injected card rendering failure')
            end
            local ok,err=pcall(view.Render,view)
            assert(not ok and tostring(err):find('Injected card rendering failure',1,true))
            assert(not view.rendering and not view.renderQueued and not view.pendingRender and not view.searchQueued)
            FlushTimers(); assert(not view.rendering and #timers==0)
            view.RenderCard=original; view:Render()
            assert(cardFor('custom:entry2') and not view.rendering and #calls==0)
        """)

    def test_close_cancellation_retires_queued_jobs_without_losing_latest_query(self):
        self.large_rows(100)
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            view.searchBox:SetText('Entry 99'); view.searchBox:Fire('OnTextChanged',true)
            view:QueueRender('full'); assert(#timers==2)
            view:CancelPending(); host:Hide(); FlushTimers()
            assert(renders==0 and view.search=='Entry 99' and not view.searchQueued and not view.renderQueued)
            host:Show(); view:SetModel(view.model)
            assert(renders==1 and cardFor('custom:entry99') and #view.listPlan.rows==1)
            assert(#calls==0)
        """)

    def test_cancellation_during_active_pass_discards_old_session_followup(self):
        self.large_rows(100)
        self.check("""
            local original=view.RenderCard; local changed=false
            view.RenderCard=function(self,...)
                if not changed then
                    changed=true; self.search='Entry 99'; self:Render(); self:CancelPending()
                end
                return original(self,...)
            end
            view:Render(); assert(#timers==0 and not view.pendingRender and not view.renderQueued)
            view:SetModel(view.model)
            assert(cardFor('custom:entry99') and #view.listPlan.rows==1 and #calls==0)
        """)

    def test_immediate_data_refresh_consumes_already_pending_search(self):
        self.large_rows(100)
        self.check("""
            local original=view.Render; local renders=0
            view.Render=function(self,...) renders=renders+1; return original(self,...) end
            view.searchBox:SetText('Entry 99'); view.searchBox:Fire('OnTextChanged',true)
            view:SetModel(view.model); assert(renders==1 and cardFor('custom:entry99'))
            FlushTimers(); assert(renders==1 and not view.searchQueued and #calls==0)
        """)

    def test_summary_scroll_keeps_static_counts_recent_cards_and_navigation(self):
        self.check("""
            local P=ns.LegacyPresentation; local summaryCalls=0
            local original=P.Summary
            P.Summary=function(...) summaryCalls=summaryCalls+1; return original(...) end
            view:Render(); assert(summaryCalls==1)
            local headingCount=#view.headings
            for i=1,20 do view.contentScroll:SetVerticalScroll(i*5) end
            assert(summaryCalls==1 and #view.headings==headingCount and cardFor('custom:first'))
            assert(#calls==0)
        """)

    def test_statistics_scroll_reuses_groups_and_bounds_visible_row_pool(self):
        self.check("""
            local rows={}
            for i=1,10000 do rows[i]={key='statistic:fixture:'..i,name='Statistic '..i,value=tostring(i),
                category='stats:fixture',available=true,source='native_statistic'} end
            local category={key='stats:fixture',name='Fixture Statistics',children={}}
            local summary={key='stats:summary',name='Summary',children={}}
            local catalog={roots={summary,category},byCategory={['stats:summary']=summary,['stats:fixture']=category},rows=rows}
            local queries=0
            ns.StatisticsAdapter.Catalog=function() return catalog end
            ns.StatisticsAdapter.Rows=function() queries=queries+1; return rows end
            view:SetTab('statistics'); assert(queries==1)
            for i=1,100 do view.contentScroll:SetVerticalScroll(i*1000) end
            assert(queries==1 and #view.statisticsPlan.items==10001)
            assert(#view.stats<=math.ceil(view.contentScroll:GetHeight()/26)+4)
            local visible=0
            for _,row in ipairs(view.stats) do if row:IsShown() then visible=visible+1 end end
            assert(visible>0 and #calls==0)
        """)

    def test_ui_diagnostics_off_do_not_read_clocks_and_on_report_actual_scroll_work(self):
        self.large_rows(100)
        self.check("""
            local clocks=0
            debugprofilestop=function() clocks=clocks+1; return clocks end
            ns.LegacyPerf.Enable(false); view:Render(); view.contentScroll:SetVerticalScroll(10)
            assert(clocks==0)
            ns.LegacyPerf.Enable(true); view:Render(); view.contentScroll:SetVerticalScroll(20)
            local perf=ns.LegacyPerf.Snapshot()
            assert(perf.timings['UI.Render'].calls==1 and perf.timings['UI.ScrollRender'].calls==1)
            assert(perf.timings['UI.ListRender'].calls==2 and perf.timings['UI.ListRender'].measured==2)
            assert(clocks>0 and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
