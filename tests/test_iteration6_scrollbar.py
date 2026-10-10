"""Iteration 6 owned Wrath scroll controls with the actual Lua renderer.

Tests use genuine Slider value-change contracts in the XML fixture. Geometry,
bounds, feedback guards and allocation limits do not assert native rendering or
in-game mouse input; the release checklist covers those client-only checks.
"""
import unittest

import test_wrath_iteration3_ui as iteration3
import test_wrath_ui_performance as performance


class Iteration6ScrollbarTests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check
    large_rows = performance.WrathUIPerformanceTests.large_rows

    def test_owned_controls_stay_inside_content_panel_at_all_presets(self):
        self.large_rows(100)
        self.check('''
            for _,preset in pairs(ns.WrathAchievementUI.PRESETS) do
                view:Layout(preset[1],preset[2])
                local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
                assert(view.contentPanelWidth-view.contentWidth==22)
                assert(bar.holder:GetLeft()==scroll:GetRight()+2)
                assert(bar.holder:GetWidth()==18)
                assert(bar.holder:GetRight()<=view.root:GetRight()-25)
                assert(bar.up:GetTop()==scroll:GetTop())
                assert(bar.down:GetBottom()==scroll:GetBottom())
                assert(bar.holder:GetHeight()==scroll:GetHeight())
                assert(bar:GetTop()==scroll:GetTop()-18)
                assert(bar:GetBottom()==scroll:GetBottom()+18)
                for _,card in ipairs(view.cards) do
                    if card:IsShown() then assert(card:GetRight()<bar.holder:GetLeft()) end
                end
                assert(scroll:GetScript('OnUpdate')==nil and bar:GetScript('OnUpdate')==nil)
            end
        ''')

    def test_original_wrath_arrow_and_knob_assets_have_independent_states(self):
        self.check('''
            local bar=view.contentScroll.faScrollbar
            assert(bar.orientation=='VERTICAL' and bar.valueStep==1 and bar.obeyStep==false)
            assert(bar:GetThumbTexture()==bar.thumb)
            assert(bar.thumb.textureValue=='Interface\\\\Buttons\\\\UI-ScrollBar-Knob')
            assert(bar.thumb.coords[1]==.20 and bar.thumb.coords[4]==.875)
            for _,button in ipairs({bar.up,bar.down}) do
                assert(button:GetWidth()==18 and button:GetHeight()==16)
                assert(button.normalTexture~=button.pushedTexture)
                assert(button.disabledTexture~=button.highlightTexture)
                assert(button.normalTexture.coords[3]==.25 and button.normalTexture.coords[4]==.75)
                assert(button.highlightTexture:GetBlendMode()=='ADD')
            end
        ''')

    def test_thumb_is_proportional_to_visible_content_with_minimum_drag_target(self):
        self.large_rows(12)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            local track=scroll:GetHeight()-36
            local expected=math.min(track,math.max(18,track*scroll:GetHeight()/view.contentChild:GetHeight()))
            assert(math.abs(bar.thumb:GetHeight()-expected)<.001)
            shortThumb=bar.thumb:GetHeight()
        ''')
        self.large_rows(10000)
        self.check('''
            local bar=view.contentScroll.faScrollbar
            assert(bar.thumb:GetHeight()==18 and bar.thumb:GetHeight()<shortThumb)
            assert(bar.thumb:IsShown() and bar.maximum>800000)
        ''')

    def test_wheel_reuses_list_query_and_navigation_once_per_movement(self):
        self.large_rows(1000)
        self.check('''
            view.contentScroll.faScrollbar:SetValue(440)
            view.contentScroll.faScrollbar:SetValue(0)
            local beforeFrames=#frames
            local queries,renders=0,0
            local P,original=ns.LegacyPresentation,ns.LegacyPresentation.Rows
            P.Rows=function(...) queries=queries+1; return original(...) end
            local render=view.Render
            view.Render=function(self,reason) renders=renders+1; return render(self,reason) end
            for i=1,40 do view.contentScroll:Fire('OnMouseWheel',-1) end
            assert(view.contentScroll:GetVerticalScroll()==1760 and renders==40 and queries==0)
            assert(view.contentScroll.faScrollbar:GetValue()==1760)
            assert(#frames==beforeFrames and #timers==0 and #calls==0)
        ''')

    def test_wheel_clamps_both_scroll_limits(self):
        self.large_rows(100)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            scroll:Fire('OnMouseWheel',10000)
            assert(scroll:GetVerticalScroll()==0 and bar:GetValue()==0)
            scroll:Fire('OnMouseWheel',-10000)
            assert(scroll:GetVerticalScroll()==bar.maximum and bar:GetValue()==bar.maximum)
            scroll:Fire('OnMouseWheel',-1)
            assert(scroll:GetVerticalScroll()==bar.maximum)
            scroll:Fire('OnMouseWheel',10000)
            assert(scroll:GetVerticalScroll()==0)
        ''')

    def test_slider_value_changes_scroll_and_virtualized_cards(self):
        self.large_rows(500)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            bar:SetValue(view.listPlan.y+249*88)
            assert(scroll:GetVerticalScroll()==bar:GetValue() and cardFor('custom:entry250'))
            bar:SetValue(bar.maximum)
            assert(scroll:GetVerticalScroll()==bar.maximum and cardFor('custom:entry500'))
            bar:SetValue(-999)
            assert(scroll:GetVerticalScroll()==0 and cardFor('custom:entry1'))
            assert(#view.cards<=math.ceil(scroll:GetHeight()/88)+4 and #timers==0)
        ''')

    def test_arrow_buttons_scroll_and_disable_at_actual_bounds(self):
        self.large_rows(100)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            assert(not bar.up:IsEnabled() and bar.down:IsEnabled())
            bar.down:Fire('OnClick')
            assert(scroll:GetVerticalScroll()==44 and bar.up:IsEnabled())
            bar.up:Fire('OnClick')
            assert(scroll:GetVerticalScroll()==0 and not bar.up:IsEnabled())
            bar:SetValue(bar.maximum)
            assert(bar.up:IsEnabled() and not bar.down:IsEnabled())
            bar.down:Fire('OnClick')
            assert(scroll:GetVerticalScroll()==bar.maximum)
            bar.up:Fire('OnClick')
            assert(scroll:GetVerticalScroll()==bar.maximum-44 and bar.down:IsEnabled())
        ''')

    def test_short_content_disables_controls_without_fictional_scroll_range(self):
        self.large_rows(1)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            local minimum,maximum=bar:GetMinMaxValues()
            assert(minimum==0 and maximum==0 and bar:GetValue()==0)
            assert(not bar.thumb:IsShown() and not bar:IsMouseEnabled())
            assert(not bar.up:IsEnabled() and not bar.down:IsEnabled())
            scroll:Fire('OnMouseWheel',-50); bar.down:Fire('OnClick'); bar:SetValue(999)
            assert(scroll:GetVerticalScroll()==0 and bar:GetValue()==0)
            assert(view.contentChild:GetHeight()==scroll:GetHeight())
        ''')

    def test_resize_preserves_absolute_offset_and_updates_thumb_geometry(self):
        self.large_rows(100)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            bar:SetValue(440)
            view:Layout(768,500)
            local compactThumb,compactRange=bar.thumb:GetHeight(),bar.maximum
            assert(scroll:GetVerticalScroll()==440 and bar:GetValue()==440)
            view:Layout(1024,720)
            assert(scroll:GetVerticalScroll()==440 and bar:GetValue()==440)
            assert(bar.thumb:GetHeight()>compactThumb and bar.maximum<compactRange)
            assert(bar.holder:GetHeight()==scroll:GetHeight())
        ''')

    def test_expansion_preserves_offset_and_last_objectives_remain_accessible(self):
        self.large_rows(1)
        self.check('''
            local data={available=true,complete=true,items={}}
            for i=1,120 do data.items[i]={name='Criterion '..i,completed=false} end
            ns.LegacyPresentation.Criteria=function() return data end
            view.selected='custom:entry1'; view:Render()
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            local expanded=cardFor('custom:entry1')
            assert(expanded:GetHeight()>scroll:GetHeight() and bar.maximum>0)
            bar:SetValue(bar.maximum)
            expanded=cardFor('custom:entry1')
            assert(expanded and expanded.criteriaPool[120]:IsShown())
            local last=expanded.criteriaPool[120]
            assert(last.points[1][5]<-2600)
            assert(scroll:GetVerticalScroll()==bar.maximum)
            view:Render()
            assert(scroll:GetVerticalScroll()==bar.maximum and bar:GetValue()==bar.maximum)
            expanded:Fire('OnClick')
            assert(view.selected==nil and scroll:GetVerticalScroll()==0 and bar.maximum==0)
            assert(not bar.thumb:IsShown())
        ''')

    def test_expansion_before_end_only_clamps_when_content_shrinks(self):
        self.large_rows(30)
        self.check('''
            ns.LegacyPresentation.Criteria=function() return {available=true,complete=true,
                items={{name='One objective',current=0,required=1}}} end
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            bar:SetValue(88)
            view.selected='custom:entry2'; view:Render()
            assert(scroll:GetVerticalScroll()==88)
            bar:SetValue(bar.maximum)
            local expandedMaximum=bar.maximum
            view.selected=nil; view:Render()
            assert(bar.maximum<expandedMaximum and scroll:GetVerticalScroll()==bar.maximum)
            assert(cardFor('custom:entry30'))
        ''')

    def test_search_reset_synchronizes_value_range_and_arrow_states(self):
        self.large_rows(200)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            bar:SetValue(4400)
            view.searchBox:SetText('Entry 199'); view.searchBox:Fire('OnTextChanged',false)
            assert(#view.listPlan.rows==1 and scroll:GetVerticalScroll()==0 and bar:GetValue()==0)
            assert(bar.maximum==0 and not bar.up:IsEnabled() and not bar.down:IsEnabled())
            view.searchClear:Fire('OnClick')
            assert(#view.listPlan.rows==200 and bar.maximum>0 and bar.down:IsEnabled())
        ''')

    def test_sidebar_scroll_controls_are_independent_and_reused(self):
        self.large_rows(50)
        self.check('''
            local scroll,bar=view.categoryScroll,view.categoryScroll.faScrollbar
            view.categoryChild:SetHeight(scroll:GetHeight()+900)
            scroll:Fire('OnMouseWheel',-1)
            assert(scroll:GetVerticalScroll()==44 and bar:GetValue()==44 and bar.maximum==900)
            assert(view.contentScroll:GetVerticalScroll()==0)
            local before=#frames
            for i=1,20 do bar.down:Fire('OnClick') end
            assert(scroll:GetVerticalScroll()==900 and #frames==before)
            assert(bar.holder:GetTop()==scroll:GetTop() and bar.holder:GetBottom()==scroll:GetBottom())
            assert(bar.holder:GetRight()<=view.root:GetLeft()+view.sidebarWidth+25)
        ''')

    def test_synchronization_resists_unconditional_native_setter_callbacks(self):
        self.large_rows(100)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            local callbacks,renders=0,0
            bar.SetValue=function(self,value)
                callbacks=callbacks+1; assert(callbacks<15)
                self.value=math.max(self.minimum,math.min(value,self.maximum))
                self:Fire('OnValueChanged',self.value)
            end
            bar.SetMinMaxValues=function(self,minimum,maximum)
                self.minimum,self.maximum=minimum,maximum
                self:SetValue(math.max(minimum,math.min(self:GetValue(),maximum)))
            end
            local render=view.Render
            view.Render=function(self,reason) renders=renders+1; return render(self,reason) end
            ns.WrathAchievementUI.LayoutContentScrollbar(view)
            bar:SetValue(440)
            assert(scroll:GetVerticalScroll()==440 and bar:GetValue()==440 and renders==1)
            local oldCallbacks=callbacks
            ns.WrathAchievementUI.LayoutContentScrollbar(view)
            assert(callbacks==oldCallbacks and renders==1)
            view:Layout(1024,720)
            assert(scroll:GetVerticalScroll()==440 and callbacks<15 and not bar.syncing)
            assert(#timers==0 and #calls==0)
        ''')

    def test_repeated_input_creates_no_scroll_controls_or_queued_refreshes(self):
        self.large_rows(1000)
        self.check('''
            local scroll,bar=view.contentScroll,view.contentScroll.faScrollbar
            local holder,up,down,thumb=bar.holder,bar.up,bar.down,bar.thumb
            -- Warm the bounded card slots at both ends before allocation checks.
            bar:SetValue(4400); bar:SetValue(0)
            local before=#frames
            for i=1,100 do
                scroll:Fire('OnMouseWheel',-1); bar.down:Fire('OnClick')
                bar.up:Fire('OnClick'); bar:SetValue(440)
                ns.WrathAchievementUI.LayoutContentScrollbar(view)
            end
            assert(bar==scroll.faScrollbar and bar.holder==holder)
            assert(bar.up==up and bar.down==down and bar.thumb==thumb)
            assert(#frames==before and #timers==0 and #calls==0)
            for _,frame in ipairs({scroll,holder,bar,up,down}) do assert(frame:GetScript('OnUpdate')==nil) end
        ''')


if __name__ == '__main__':
    unittest.main()
