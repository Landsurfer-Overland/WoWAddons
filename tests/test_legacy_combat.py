"""Combat transitions against the actual Lua controller, bridge and UI.

These fixtures prove lifecycle and mutation contracts, not client taint safety,
real aggro, rendering, protected UI behavior or live script execution timing.
"""
import unittest

import test_legacy_refresh_lifecycle as lifecycle


class LegacyCombatTests(unittest.TestCase):
    setUp = lifecycle.LegacyRefreshLifecycleTests.setUp
    check = lifecycle.LegacyRefreshLifecycleTests.check

    def monitor(self):
        self.check('''
            local c=ns.LegacyUIController
            mountCalls,restoreCalls=0,0
            local mount,restore=ns.LegacyWindowBridge.Mount,ns.LegacyWindowBridge.Restore
            ns.LegacyWindowBridge.Mount=function(...)
                assert(not inCombat,"Native mount attempted during combat")
                mountCalls=mountCalls+1; return mount(...)
            end
            ns.LegacyWindowBridge.Restore=function(...)
                assert(not inCombat,"Native restore attempted during combat")
                restoreCalls=restoreCalls+1; return restore(...)
            end
        ''')

    def test_entering_combat_preserves_open_unprotected_presentation_on_every_tab(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController
            local row=c.ui.model.byKey['custom:first']
            row.description=string.rep('Long description ',240)
            c.ui.category=row.category; c.ui.selected=row.key; c.ui.expanded.general=true; c.ui:Render()
            c.ui.contentScroll:SetVerticalScroll(88); DrainTimers()
            assert(c.ui.contentChild:GetHeight()>c.ui.contentScroll:GetHeight()+88)
            for _,tab in ipairs({'achievements','rewards','trees','statistics'}) do
                c.ui:SetTab(tab,true); DrainTimers()
                local ui,cover,bridge,model=c.ui,c.cover,c.bridge,c.ui.model
                local scroll,sidebar=c.ui.contentScroll:GetVerticalScroll(),c.ui.categoryScroll:GetVerticalScroll()
                local framesBefore,builds,renders,fits=#frames,buildCalls,renderCalls,fitCalls
                local page,shows,messagesBefore=LegacySystemFrame.currentPage,rewardShows+treeShows,#messages
                assert(not ns.LegacyWindowBridge.Blocked(LegacySystemFrame))
                local mounts=mountCalls
                inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); DrainTimers()
                assert(c.cover:IsVisible() and c.bridge==bridge and bridge.active and not c.restorePending)
                assert(not LegacySystemFrame.Background:IsShown() and not LegacySystemFrame.NativeTabs:IsShown())
                assert(c.state:find('Enabled') and not c.state:find('Fallback') and c.lastError==nil)
                assert(c.ui==ui and c.cover==cover and c.ui.model==model and c.ui.tab==tab)
                assert(c.ui.category==row.category and c.ui.selected==row.key and c.ui.expanded.general)
                assert(c.ui.contentScroll:GetVerticalScroll()==scroll and c.ui.categoryScroll:GetVerticalScroll()==sidebar)
                assert(#frames==framesBefore and buildCalls==builds and renderCalls==renders and fitCalls==fits)
                assert(LegacySystemFrame.currentPage==page and rewardShows+treeShows==shows)
                assert(restoreCalls==0 and mountCalls==mounts and #messages==messagesBefore)
                inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
                assert(c.cover:IsVisible() and c.bridge==bridge and c.ui.tab==tab and c.state=='Enabled')
                assert(c.ui.model==model and c.ui.category==row.category and c.ui.selected==row.key)
                assert(c.ui.contentScroll:GetVerticalScroll()==scroll and c.ui.categoryScroll:GetVerticalScroll()==sidebar)
                assert(#frames==framesBefore and buildCalls==builds and renderCalls==renders and fitCalls==fits)
                assert(restoreCalls==0 and mountCalls==mounts+1 and rewardShows+treeShows==shows)
                assert(saved.done.first==1730000000 and saved.done.second==nil and saved.history[1]=='keep' and #calls==0)
            end
        ''')

    def test_refresh_during_lockdown_without_regen_event_defers_instead_of_releasing(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; local bridge,model=c.bridge,c.ui.model
            local builds,renders,fits=buildCalls,renderCalls,fitCalls
            inCombat=true
            for i=1,12 do assert(c:Refresh('custom')==false) end
            assert(c.cover:IsVisible() and c.bridge==bridge and c.ui.model==model and c.pending)
            assert(buildCalls==builds and renderCalls==renders and fitCalls==fits and #timers==0)
            assert(restoreCalls==0 and mountCalls==0 and not c.restorePending and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(buildCalls==builds+1 and renderCalls==renders+1 and mountCalls==1)
            assert(c.cover:IsVisible() and c.state=='Enabled' and not c.pending and #calls==0)
        ''')

    def test_combat_data_and_layout_notifications_coalesce_without_native_mutations(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('trees',true); DrainTimers()
            local tree=LegacySystemFrame.TreePage; local bridge=c.bridge
            local builds,renders,fits=buildCalls,renderCalls,fitCalls
            local mounts=mountCalls; local originalFrameCount=#frames
            local mutations=0
            for _,method in ipairs({'ClearAllPoints','SetPoint','SetSize','SetScale','SetFrameLevel','SetFrameStrata'}) do
                local original=tree[method]
                tree[method]=function(self,...)
                    assert(not inCombat,'Protected geometry write in combat')
                    mutations=mutations+1; return original(self,...)
                end
            end
            tree.protected=true; inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            for i=1,40 do
                ControllerEvent('CRITERIA_UPDATE'); ControllerEvent('UI_SCALE_CHANGED')
                EventRegistry:TriggerEvent('Legacy.RefreshChallenges')
                ns.FA.CHECK_HOOKS[1]()
                c:Attach(); c:QueueAttach()
            end
            DrainTimers()
            assert(#timers==0 and mountCalls==mounts and restoreCalls==0 and mutations==0)
            assert(c.cover:IsVisible() and c.bridge==bridge and c.ui.tab=='trees' and c.lastError==nil)
            assert(buildCalls==builds and renderCalls==renders and fitCalls==fits and #frames==originalFrameCount)
            tree.protected=false; inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(buildCalls==builds+1 and renderCalls==renders+1 and fitCalls==fits and mountCalls==mounts+1)
            assert(c.cover:IsVisible() and tree:IsVisible() and c.ui.tab=='trees' and c.state=='Enabled')
            assert(tree:GetParent()==LegacySystemFrame and saved.done.first==1730000000 and #calls==0)
        ''')

    def test_queued_controller_and_ui_work_is_cancelled_then_consumed_after_combat(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; local builds,renders=buildCalls,renderCalls
            c:Schedule('custom'); c:QueueAttach(); c:NativeSelection()
            c.ui.searchBox:SetText('Second')
            c.ui.searchBox:Fire('OnTextChanged',true)
            assert(c.queued and c.attachQueued and c.selectionQueued and c.ui.searchQueued)
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); DrainTimers()
            assert(not c.queued and not c.attachQueued and not c.selectionQueued and not c.ui.searchQueued)
            assert(buildCalls==builds and renderCalls==renders and mountCalls==0 and restoreCalls==0 and #timers==0)
            assert(c.ui.search=='Second' and c.dirtyRender and c.cover:IsVisible())
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(buildCalls==builds+1 and renderCalls==renders+1 and c.ui.search=='Second')
            assert(c.cover:IsVisible() and c.ui.tab=='achievements' and mountCalls==1 and #timers==0 and #calls==0)
        ''')

    def test_native_selection_during_combat_preserves_custom_tab_until_safe_remount(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('statistics',true); DrainTimers()
            local builds,renders,mounts=buildCalls,renderCalls,mountCalls
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            EventRegistry:TriggerEvent('Legacy.SelectPage',1); DrainTimers()
            assert(c.ui.tab=='statistics' and c.cover:IsVisible() and LegacySystemFrame.currentPage==1)
            assert(buildCalls==builds and renderCalls==renders and mountCalls==mounts and restoreCalls==0)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.ui.tab=='statistics' and LegacySystemFrame.currentPage==2 and c.cover:IsVisible())
            assert(not LegacySystemFrame.RewardTrackPage:IsShown() and not LegacySystemFrame.ChallengesPage:IsShown())
            assert(buildCalls==builds and renderCalls==renders and mountCalls==mounts+1 and #calls==0)
        ''')

    def test_selection_timer_checks_lockdown_again_before_changing_custom_tab(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('statistics',true); DrainTimers()
            EventRegistry:TriggerEvent('Legacy.SelectPage',1)
            assert(c.selectionQueued)
            inCombat=true; DrainTimers()
            assert(c.ui.tab=='statistics' and c.pending and c.dirtyMount and c.cover:IsVisible())
            assert(restoreCalls==0)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.ui.tab=='statistics' and LegacySystemFrame.currentPage==2 and c.lastError==nil and #calls==0)
        ''')

    def test_permitted_combat_close_hides_cover_without_restoring_or_reopening_native_root(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('statistics',true); DrainTimers()
            local bridge,ui,framesBefore=c.bridge,c.ui,#frames
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            c.ui.callbacks.onClose()
            assert(not LegacySystemFrame:IsShown() and not c.cover:IsShown() and c.bridge==bridge)
            assert(c.ui==ui and c.ui.tab=='statistics' and restoreCalls==0 and not c.closePending)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(not LegacySystemFrame:IsShown() and not c.cover:IsShown() and c.ui.tab=='statistics')
            assert(c.bridge==bridge and restoreCalls==0 and #frames==framesBefore)
            LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and c.ui==ui and c.ui.tab=='statistics' and c.state=='Enabled')
            assert(not LegacySystemFrame.NativeTabs:IsShown() and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_client_hide_and_reopen_in_combat_reuses_cover_without_protected_page_changes(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('trees',true); DrainTimers()
            local bridge,ui,model=c.bridge,c.ui,c.ui.model; local mounts=mountCalls
            LegacySystemFrame.protected=true; LegacySystemFrame.TreePage.protected=true
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            -- Simulate the game securely hiding its root; the addon must only
            -- hide its own ordinary cover, never restore protected pages.
            LegacySystemFrame:Hide()
            assert(not c.cover:IsShown() and c.bridge==bridge and not c.restorePending)
            LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and c.ui==ui and c.ui.model==model and c.ui.tab=='trees')
            assert(mountCalls==mounts and restoreCalls==0 and c.lastError==nil)
            LegacySystemFrame.protected=false; LegacySystemFrame.TreePage.protected=false
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and c.ui.tab=='trees' and c.bridge==bridge and c.state=='Enabled' and #calls==0)
        ''')

    def test_protected_close_is_deferred_once_and_never_treated_as_failure(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; local messageCount=#messages; local nativeHides=rootHides
            LegacySystemFrame.protected=true; inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            for i=1,12 do c.ui.callbacks.onClose() end
            assert(c.closePending and c.pending and c.cover:IsVisible() and LegacySystemFrame:IsShown())
            assert(rootHides==nativeHides and restoreCalls==0 and #timers==0)
            assert(not c.restorePending and c.lastError==nil and #messages==messageCount)
            LegacySystemFrame.protected=false; inCombat=false
            ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(not c.closePending and not c.cover:IsShown() and not LegacySystemFrame:IsShown())
            assert(rootHides==nativeHides+1 and restoreCalls==1 and LegacySystemFrame.NativeTabs:IsShown())
            LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and c.state=='Enabled' and #calls==0)
        ''')

    def test_restricted_cover_hide_is_deferred_and_completed_without_reopening_root(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('statistics',true); DrainTimers()
            local bridge,ui,model=c.bridge,c.ui,c.ui.model
            local hide=c.cover.Hide; local coverHides=0
            c.cover.Hide=function(self,...)
                assert(not inCombat,'Restricted cover hide attempted in combat')
                coverHides=coverHides+1; return hide(self,...)
            end
            c.cover.protected=true; inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            LegacySystemFrame:Hide()
            assert(c.cover:IsShown() and c.pending and coverHides==0 and c.lastError==nil)
            assert(c.bridge==bridge and restoreCalls==0)
            c.cover.protected=false; inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(not c.cover:IsShown() and not LegacySystemFrame:IsShown() and coverHides==1)
            assert(c.ui==ui and c.ui.model==model and c.ui.tab=='statistics' and c.bridge==bridge)
            assert(restoreCalls==0 and c.lastError==nil and #calls==0)
        ''')

    def test_initial_enable_waits_for_combat_without_creating_or_mutating_presentation(self):
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; local count=#frames
            inCombat=true; ns.FA.SLASH.legacyui('on')
            ControllerEvent('PLAYER_REGEN_DISABLED'); c:QueueAttach(); c:QueueRefresh(); DrainTimers()
            assert(c.cover==nil and c.bridge==nil and c.pending and #frames==count)
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            assert(buildCalls==0 and mountCalls==0 and restoreCalls==0 and not c.restorePending and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and c.state=='Enabled' and mountCalls==1 and buildCalls==1 and #calls==0)
        ''')

    def test_disabled_replacement_leaves_native_combat_lifecycle_untouched(self):
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; local count=#frames; local messageCount=#messages
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); DrainTimers()
            assert(c.cover==nil and c.bridge==nil and #frames==count)
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(mountCalls==0 and restoreCalls==0 and buildCalls==0 and #messages==messageCount)
            assert(LegacySystemFrame:GetScript('OnShow')==originalRootShow)
            assert(LegacySystemFrame:GetScript('OnHide')==originalRootHide and #calls==0)
        ''')

    def test_disabling_open_unprotected_replacement_defers_native_restore_until_regen(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController; c.ui:SetTab('rewards',true); DrainTimers()
            local bridge=c.bridge
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); ns.FA.SLASH.legacyui('off')
            assert(settings.legacyUI==false and c.restorePending and c.bridge==bridge and c.cover:IsVisible())
            assert(restoreCalls==0 and not LegacySystemFrame.NativeTabs:IsShown())
            for i=1,5 do c:Attach(); ControllerEvent('PLAYER_REGEN_DISABLED') end
            assert(restoreCalls==0 and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(not c.restorePending and c.bridge==nil and not c.cover:IsShown() and c.state=='Disabled')
            assert(restoreCalls==1 and LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            assert(LegacySystemFrame.RewardTrackPage:IsVisible() and LegacySystemFrame:IsMouseEnabled())
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_actual_failure_in_combat_still_reports_error_and_defers_restoration(self):
        self.h.enable()
        self.monitor()
        self.check('''
            local c=ns.LegacyUIController
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            assert(c:Guard(function() error('Injected genuine presentation failure') end)==false)
            assert(c.restorePending and c.cover:IsVisible() and restoreCalls==0)
            assert(c.state:find('Fallback') and c.lastError:find('Injected genuine presentation failure'))
            assert(messages[#messages]:find('Injected genuine presentation failure') and messages[#messages]:find('retry after combat'))
            local errorState=c.state
            c:Attach(); c:Schedule('custom'); DrainTimers()
            assert(c.state==errorState and restoreCalls==0)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(restoreCalls==1 and not c.restorePending and c.cover:IsVisible() and c.state=='Enabled')
            assert(saved.done.first==1730000000 and saved.done.second==nil and #calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
