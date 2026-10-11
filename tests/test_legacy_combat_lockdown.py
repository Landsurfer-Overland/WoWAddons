"""Restricted operations and silent panel-manager denial using production Lua.

These are behavioral fixtures, not an actual WoW secure execution/taint engine.
"""
import unittest

import test_legacy_refresh_lifecycle as lifecycle


class CombatLockdownTests(unittest.TestCase):
    setUp = lifecycle.LegacyRefreshLifecycleTests.setUp
    check = lifecycle.LegacyRefreshLifecycleTests.check

    def test_silent_panel_manager_denial_is_avoided_and_cleanup_deferred(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local hide=HideUIPanel
            blocked,panelCalls=0,0
            HideUIPanel=function(frame)
                panelCalls=panelCalls+1
                if inCombat then blocked=blocked+1; return end -- no Lua exception
                return hide(frame)
            end
            local model,ui,bridge=c.ui.model,c.ui,c.bridge
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            FAWrathAchievementFrameCloseButton:Fire('OnClick')
            assert(blocked==0 and panelCalls==0 and not LegacySystemFrame:IsShown())
            assert(not c.cover:IsShown() and c.panelClosePending and not c.closePending)
            assert(c.ui==ui and c.ui.model==model and c.bridge==bridge and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(panelCalls==1 and blocked==0 and not c.panelClosePending)
            assert(not c.cover:IsShown() and not LegacySystemFrame:IsShown() and #calls==0)
        ''')

    def test_protected_root_allows_owned_close_and_only_one_native_close_after_regen(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local nativeHides=rootHides
            LegacySystemFrame.protected=true
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            for i=1,20 do FAWrathAchievementFrameCloseButton:Fire('OnClick') end
            assert(c.closePending and not c.cover:IsShown() and LegacySystemFrame:IsShown())
            assert(rootHides==nativeHides and #timers==0 and c.lastError==nil and not c.restorePending)
            LegacySystemFrame.protected=false; inCombat=false
            ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(rootHides==nativeHides+1 and not c.closePending and not c.cover:IsShown())
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_protected_cover_blocks_scroll_menus_search_navigation_and_drag(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local ui=c.ui
            local framesBefore,builds,renders,category=#frames,buildCalls,renderCalls,ui.category
            local scroll=ui.contentScroll:GetVerticalScroll()
            ui.contentScroll.SetVerticalScroll=function() error('Restricted scroll mutation') end
            ui.filterMenu.Hide=function() error('Restricted menu mutation') end
            c.cover.StartMoving=function() error('Restricted drag') end
            c.cover.protected=true; inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            ui.contentScroll:Fire('OnMouseWheel',-1)
            ui.contentScroll.faScrollbar.down:Fire('OnClick')
            ui.filterDismiss:Fire('OnClick')
            ui.filterButton:Fire('OnClick')
            ui.sizeButton:Fire('OnClick')
            ui.searchBox:Fire('OnTextChanged',true)
            ui.categories[1]:Fire('OnClick')
            FAWrathAchievementFrameHeader:Fire('OnDragStart')
            assert(ui.contentScroll:GetVerticalScroll()==scroll and ui.category==category and not c.dragging)
            assert(c.dirtyRender and c.pending and c.lastError==nil and not c.restorePending)
            assert(#frames==framesBefore and buildCalls==builds and renderCalls==renders and #timers==0)
        ''')

    def test_protected_content_does_not_drop_close_request_at_ui_guard(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame.protected=true; c.cover.protected=true
            local hide=c.cover.Hide
            c.cover.Hide=function(self,...)
                assert(not inCombat,'Protected cover hide attempted'); return hide(self,...)
            end
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            FAWrathAchievementFrameCloseButton:Fire('OnClick')
            assert(c.closePending and c.cover:IsVisible() and LegacySystemFrame:IsShown())
            assert(c.lastError==nil and not c.restorePending and #timers==0)
            LegacySystemFrame.protected=false; c.cover.protected=false; inCombat=false
            ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(not c.closePending and not c.cover:IsShown() and not LegacySystemFrame:IsShown())
            assert(c.lastError==nil and #calls==0)
        ''')

    def test_unprotected_combat_drag_is_declined_because_native_pages_depend_on_host(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local framesBefore=#frames
            c.cover.StartMoving=function() error('Combat geometry mutation') end
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            for i=1,10 do FAWrathAchievementFrameHeader:Fire('OnDragStart') end
            assert(not c.dragging and c.cover:IsShown() and c.lastError==nil and #frames==framesBefore)
            assert(#timers==0 and #calls==0)
        ''')

    def test_drag_interrupted_by_combat_and_position_reset_finish_after_regen(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local stop,point=c.cover.StopMovingOrSizing,c.cover.SetPoint
            local stops,points=0,0
            c.cover.StopMovingOrSizing=function(self,...)
                assert(not inCombat); stops=stops+1; return stop(self,...)
            end
            c.cover.SetPoint=function(self,...)
                assert(not inCombat); points=points+1; return point(self,...)
            end
            FAWrathAchievementFrameHeader:Fire('OnDragStart'); assert(c.dragging)
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            FAWrathAchievementFrameHeader:Fire('OnDragStop')
            c:SavePosition(); c:RestorePosition(); c:ResetPosition()
            assert(stops==0 and points==0 and c.positionPending and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(stops==1 and points>0 and not c.dragging and not c.positionPending)
            assert(settings.legacyUIPosition==nil and not c.positionResetPending)
            assert(c.cover:IsVisible() and c.lastError==nil and #calls==0)
        ''')

    def test_currency_reads_and_counter_updates_wait_for_regen(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local points=c.ui.nativePoints:GetText()
            local framesBefore,builds,renders=#frames,buildCalls,renderCalls
            local total=ns.LegacyAdapter.TotalPoints; local reads=0
            ns.LegacyAdapter.TotalPoints=function()
                assert(not inCombat,'Currency read during combat'); reads=reads+1; return total()
            end
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            for i=1,40 do EventRegistry:TriggerEvent('Legacy.UpdateCurrencyInfo',{quantity=i}) end
            assert(reads==0 and c.currencyValue==16 and c.ui.nativePoints:GetText()==points)
            assert(c.ui.nativePoints:IsVisible() and c.cover:IsVisible() and c.pending)
            assert(#frames==framesBefore and buildCalls==builds and renderCalls==renders and #timers==0)
            C_MajorFactions.GetCurrentRenownLevel=function() return 21 end
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(reads==1 and buildCalls==builds+1 and c.ui.nativePoints:GetText()=='21')
            assert(c.currencyValue==21 and c.ui.nativePoints:IsVisible() and #calls==0)
        ''')

    def test_bridge_rejects_combat_mutations_before_native_page_changes(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local bridge=c.bridge
            local page=LegacySystemFrame.currentPage; local shows=rewardShows+treeShows
            inCombat=true
            assert(not pcall(bridge.Mount,bridge,'trees',c.ui.nativeHost))
            assert(not pcall(bridge.Select,bridge,1))
            assert(not pcall(bridge.Suppress,bridge,nil))
            local ok,reason=bridge:Restore()
            assert(not ok and reason:find('deferred during combat'))
            assert(LegacySystemFrame.currentPage==page and rewardShows+treeShows==shows)
            assert(c.cover:IsVisible() and bridge.active and not LegacySystemFrame.NativeTabs:IsShown())
            assert(saved.done.first==1730000000 and #calls==0)
        ''')

    def test_combat_reopen_reuses_counter_and_supersedes_panel_close_cleanup(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local points=c.ui.nativePoints:GetText()
            local ui,model,framesBefore=c.ui,c.ui.model,#frames
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); c:Close()
            assert(c.panelClosePending and not c.cover:IsShown())
            LegacySystemFrame:Show(); DrainTimers()
            assert(not c.panelClosePending and c.cover:IsVisible() and c.ui==ui and c.ui.model==model)
            assert(c.ui.nativePoints:GetText()==points and c.ui.nativePoints:IsVisible() and #frames==framesBefore)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and LegacySystemFrame:IsShown() and c.lastError==nil and #calls==0)
        ''')

    def test_new_native_open_supersedes_protected_close_with_replacement_on_or_off(self):
        for replacement in (True, False):
            with self.subTest(replacement=replacement):
                self.setUp()
                self.h.enable()
                self.check('''
                    local c=ns.LegacyUIController
                    LegacySystemFrame.protected=true
                    inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); c:Close()
                    assert(c.closePending and not c.cover:IsShown())
                ''')
                if not replacement:
                    self.check("ns.FA.SLASH.legacyui('off')")
                self.check('''
                    LegacySystemFrame:Hide(); LegacySystemFrame:Show(); DrainTimers()
                    local c=ns.LegacyUIController
                    assert(not c.closePending and not c.panelClosePending and LegacySystemFrame:IsShown())
                    if settings.legacyUI then assert(c.cover:IsVisible()) end
                    LegacySystemFrame.protected=false; inCombat=false
                    ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
                    assert(LegacySystemFrame:IsShown() and c.lastError==nil)
                    assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
                ''')

    def test_blocked_action_diagnostics_are_opt_in_bounded_and_do_not_activate_fallback(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local function blockedEvent(operation)
                for _,frame in ipairs(frames) do
                    if frame.events and frame.events.ADDON_ACTION_BLOCKED then
                        frame:Fire('OnEvent','ADDON_ACTION_BLOCKED','ForeverAchievements',operation); return
                    end
                end
                error('Missing blocked-action observer')
            end
            blockedEvent('HideUIPanel'); assert(c.combatSamples==nil)
            ns.FA.SLASH.combatdebug('on')
            local builds,renders,frameCount=buildCalls,renderCalls,#frames
            for i=1,40 do blockedEvent('RestrictedOperation'..i) end
            assert(#c.combatSamples==16 and c.combatSamples[16]:find('RestrictedOperation40'))
            assert(c.lastError==nil and not c.restorePending and #timers==0)
            assert(buildCalls==builds and renderCalls==renders and #frames==frameCount)
            ns.FA.SLASH.combatdebug('report'); assert(messages[#messages]:find('Report'))
            ns.FA.SLASH.combatdebug('off'); local last=c.combatSamples[16]
            blockedEvent('DoNotRecord'); assert(c.combatSamples[16]==last and #calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
