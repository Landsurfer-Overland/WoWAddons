"""Observe the opening handoff before deferred callbacks are allowed to run."""
import unittest

import test_legacy_refresh_lifecycle as lifecycle


class LegacyOpeningTests(unittest.TestCase):
    setUp = lifecycle.LegacyRefreshLifecycleTests.setUp
    check = lifecycle.LegacyRefreshLifecycleTests.check

    def prepare_closed(self):
        # Root opacity is the one additional reversible presentation setter.
        self.check('''
            LegacySystemFrame.SetAlpha=function(self,value)
                assert(not inCombat and not self.protected, 'Restricted opacity write')
                self.alpha=value
            end
            LegacySystemFrame.alpha=.73
            LegacySystemFrame:Hide()
            ns.LAR.SLASH.legacyui('on'); DrainTimers()
            assert(buildCalls==0 and LegacySystemFrame:GetAlpha()==.73)
        ''')

    def test_first_open_conceals_native_before_deferred_build_and_final_selection(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            -- ShowChallenges first shows the root, then selects Challenges.
            EventRegistry:TriggerEvent('Legacy.SelectPage',1)
            LegacySystemFrame:Show()
            assert(LegacySystemFrame:GetAlpha()==0, 'Stock window can paint before deferred attach')
            EventRegistry:TriggerEvent('Legacy.SelectPage',2)
            assert(LegacySystemFrame.ChallengesPage:IsShown() and LegacySystemFrame:GetAlpha()==0)
            assert(buildCalls==0 and renderCalls==0 and fitCalls==0)
            DrainTimers()
            assert(c.cover:IsVisible() and c.ui.tab=='achievements' and c.state=='Enabled')
            assert(LegacySystemFrame:GetAlpha()==.73 and not LegacySystemFrame.ChallengesPage:IsShown())
            assert(buildCalls==1 and renderCalls==1 and fitCalls==1 and #calls==0)
        ''')

    def test_reopen_conceals_every_native_page_and_reuses_existing_frames(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame:Show(); DrainTimers()
            local cover,ui,frameCount=c.cover,c.ui,#frames
            for _,id in ipairs({1,3,2,1}) do
                c:Close(); DrainTimers()
                assert(LegacySystemFrame:GetAlpha()==.73 and not c.cover:IsShown())
                LegacySystemFrame:Show()
                EventRegistry:TriggerEvent('Legacy.SelectPage',id)
                assert(LegacySystemFrame:GetAlpha()==0)
                DrainTimers()
                assert(c.cover:IsVisible() and c.cover==cover and c.ui==ui and #frames==frameCount)
                assert(LegacySystemFrame:GetAlpha()==.73 and LegacySystemFrame.currentPage==id)
                assert(not LegacySystemFrame.NativeTabs:IsShown() and not LegacySystemFrame.Background:IsShown())
                if id~=2 then assert(LegacySystemFrame.Pages[id]:IsVisible()) end
            end
            assert(c.lastError==nil and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_close_before_attach_restores_opacity_and_stale_work_stays_closed(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            c:Close()
            assert(LegacySystemFrame:GetAlpha()==.73)
            DrainTimers()
            assert(not LegacySystemFrame:IsShown() and not c.cover:IsShown() and buildCalls==0)
            LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and LegacySystemFrame:GetAlpha()==.73 and #calls==0)
        ''')

    def test_disable_before_attach_restores_native_and_cancels_opening_work(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            ns.LAR.SLASH.legacyui('off'); DrainTimers()
            assert(LegacySystemFrame:IsVisible() and LegacySystemFrame:GetAlpha()==.73)
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            assert(c.bridge==nil and not c.cover:IsShown() and buildCalls==0)
            LegacySystemFrame:Hide(); LegacySystemFrame:Show(); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and buildCalls==0 and #calls==0)
        ''')

    def test_genuine_initialization_failure_restores_native_opacity_and_reports_error(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            ns.LegacyPresentation.Build=function() error('Injected opening build failure') end
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and c.state:find('Fallback'))
            assert(not c.cover:IsShown() and LegacySystemFrame.Background:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(c.lastError:find('Injected opening build failure'))
            assert(messages[#messages]:find('Native Legacy remains available') and #calls==0)
        ''')

    def test_combat_interrupts_opening_without_restricted_opacity_writes(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            -- Ordinary frame setters remain permitted during lockdown; the
            -- fixture still rejects protected frames and counts writes.
            local alphaWrites=0
            LegacySystemFrame.SetAlpha=function(self,value)
                assert(not self.protected, 'Protected opacity write')
                alphaWrites=alphaWrites+1; self.alpha=value
            end
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and alphaWrites==1)
            assert(buildCalls==0 and c.pending and c.lastError==nil)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and LegacySystemFrame:GetAlpha()==.73 and c.state=='Enabled')
            assert(saved.done.first==1730000000 and #calls==0)
        ''')

    def test_partial_native_mount_failure_restores_opacity_and_native_geometry(self):
        self.prepare_closed()
        self.check('''
            local mount=ns.LegacyWindowBridge.Mount
            ns.LegacyWindowBridge.Mount=function(self,...)
                mount(self,...); error('Injected opening mount failure')
            end
            LegacySystemFrame:Show()
            EventRegistry:TriggerEvent('Legacy.SelectPage',3)
            assert(LegacySystemFrame:GetAlpha()==0)
            DrainTimers()
            local c=ns.LegacyUIController
            assert(c.state:find('Fallback') and c.lastError:find('Injected opening mount failure'))
            assert(LegacySystemFrame:GetAlpha()==.73 and not c.cover:IsShown() and c.bridge==nil)
            assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame.NativeTabs:IsShown())
            assert(LegacySystemFrame.TreePage:GetScale()==1 and LegacySystemFrame.TreePage:IsVisible())
            assert(LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame and #calls==0)
        ''')

    def test_partial_opacity_write_error_is_reported_and_original_alpha_is_recovered(self):
        self.prepare_closed()
        self.check('''
            local setter=LegacySystemFrame.SetAlpha
            LegacySystemFrame.SetAlpha=function(self,value)
                setter(self,value)
                if value==0 then error('Injected opening opacity failure') end
            end
            LegacySystemFrame:Show(); DrainTimers()
            local c=ns.LegacyUIController
            assert(c.state:find('Fallback') and c.lastError:find('Injected opening opacity failure'))
            assert(LegacySystemFrame:GetAlpha()==.73 and not c.cover:IsShown() and c.bridge==nil)
            assert(LegacySystemFrame.Background:IsShown() and buildCalls==0)
            assert(messages[#messages]:find('Native Legacy remains available') and #calls==0)
        ''')

    def test_rejected_page_restore_does_not_leave_ordinary_native_root_concealed(self):
        self.prepare_closed()
        self.check('''
            local mount=ns.LegacyWindowBridge.Mount
            ns.LegacyWindowBridge.Mount=function(self,...)
                mount(self,...)
                LegacySystemFrame.TreePage.protected=true
                error('Injected opening failure before restricted page restore')
            end
            LegacySystemFrame:Show(); DrainTimers()
            local c=ns.LegacyUIController
            assert(c.restorePending and c.lastError and c.bridge)
            assert(LegacySystemFrame:GetAlpha()==.73 and not c.cover:IsShown())
            assert(messages[#messages]:find('Restoration will retry'))
            LegacySystemFrame.TreePage.protected=false
            ns.LegacyWindowBridge.Mount=mount
            ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and not c.restorePending and c.state=='Enabled')
            assert(LegacySystemFrame:GetAlpha()==.73 and #calls==0)
        ''')

    def test_protected_opening_restore_waits_for_regen_and_closed_window_stays_closed(self):
        self.prepare_closed()
        self.check('''
            local c=ns.LegacyUIController
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            LegacySystemFrame.protected=true
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED')
            LegacySystemFrame:Hide(); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==0 and c.lastError==nil)
            LegacySystemFrame.protected=false; inCombat=false
            ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and not LegacySystemFrame:IsShown())
            assert(not c.cover:IsShown() and not c.restorePending and buildCalls==0)
            LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and LegacySystemFrame:GetAlpha()==.73 and #calls==0)
        ''')

    def test_gamepad_transition_restores_opacity_before_native_initialization(self):
        self.prepare_closed()
        self.check('''
            -- The native callback is in the later ordinary-priority group.
            InputUtil.ordinary['opacity-observer']={gamepad=function()
                assert(LegacySystemFrame:GetAlpha()==.73)
            end}
            LegacySystemFrame:Show(); assert(LegacySystemFrame:GetAlpha()==0)
            ChangeInputMode(true); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and nativeGamepadSawNormal)
            assert(buildCalls==0 and LegacySystemFrame.NativeTabs:IsShown())
            LegacySystemFrame:Hide(); LegacySystemFrame:Show(); DrainTimers()
            assert(LegacySystemFrame:GetAlpha()==.73 and buildCalls==0)
            ChangeInputMode(false); DrainTimers()
            assert(ns.LegacyUIController.cover:IsVisible() and LegacySystemFrame:GetAlpha()==.73 and #calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
