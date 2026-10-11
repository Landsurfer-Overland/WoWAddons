"""Requested logical window sizes must not be inferred from frame readback.

The real controller/UI run with fractional cover geometry readbacks, which the
ordinary frame fixture represents as exact integers. Client validation is separate.
"""
import unittest

import test_legacy_refresh_lifecycle as lifecycle


class LegacyLogicalFitTests(unittest.TestCase):
    setUp = lifecycle.LegacyRefreshLifecycleTests.setUp
    check = lifecycle.LegacyRefreshLifecycleTests.check

    def fractional_cover(self, width_delta=-.0001, height_delta=-.0001):
        self.h.g.widthReadbackDelta = width_delta
        self.h.g.heightReadbackDelta = height_delta
        self.check('''
            local original=UIObject
            UIObject=function(...)
                local frame=original(...)
                if frame:GetName()=='FAWrathLegacyCover' then
                    local width,height=frame.GetWidth,frame.GetHeight
                    frame.GetWidth=function(self) return width(self)+widthReadbackDelta end
                    frame.GetHeight=function(self) return height(self)+heightReadbackDelta end
                end
                return frame
            end
        ''')

    def test_compact_opens_with_fractional_cover_readback_at_the_minimum_boundary(self):
        # Actual client dump: 767.99981689453 x 640.00006103516, scale 1.
        self.fractional_cover(767.99981689453-768, 640.00006103516-640)
        self.check('''
            settings.legacyUISize='Compact'
            ns.FA.SLASH.legacyui('on'); DrainTimers()
            local c=ns.LegacyUIController
            assert(c.cover:IsVisible(),c.state)
            assert(c.state=='Enabled' and c.lastError==nil)
            assert(c.cover:GetWidth()<768 and c.cover:GetHeight()>640 and c.cover:GetScale()==1)
            assert(c.ui.width==768 and c.ui.height==500 and c.ui.layoutName=='Compact')
            assert(not LegacySystemFrame.NativeTabs:IsShown() and not LegacySystemFrame.Background:IsShown())
            assert(settings.legacyUISize=='Compact' and saved.done.first==1730000000 and #calls==0)
        ''')

    def test_every_preset_uses_its_exact_requested_body_and_stays_open_on_repeated_switches(self):
        self.fractional_cover()
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController; local model=c.ui.model
            for _,name in ipairs({'Compact','Standard','Large','Compact'}) do
                assert(c:SetSizePreset(name)); DrainTimers()
                local size=ns.WrathAchievementUI.PRESETS[name]
                assert(c.cover:IsVisible() and c.ui.layoutName==name,c.state)
                assert(c.ui.width==size[1] and c.ui.height==size[2])
                assert(c.ui.root:GetWidth()==size[1] and c.ui.root:GetHeight()==size[2])
                assert(c.ui.model==model and c.state=='Enabled' and c.lastError==nil)
            end
            local framesBefore=#frames
            LegacySystemFrame:Hide(); LegacySystemFrame:Show(); DrainTimers()
            assert(c.cover:IsVisible() and c.ui.width==768 and c.ui.height==500 and #frames==framesBefore)
            assert(settings.legacyUISize=='Compact' and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_compact_uses_logical_body_when_outer_window_scales_down_to_a_small_screen(self):
        self.fractional_cover()
        self.check('''
            UIParent:SetSize(640,480); UIParent:SetScale(.75)
            settings.legacyUISize='Compact'; ns.FA.SLASH.legacyui('on'); DrainTimers()
            local c=ns.LegacyUIController
            assert(c.cover:IsVisible() and c.cover:GetScale()<1,c.state)
            assert(c.ui.width==768 and c.ui.height==500 and c.ui.root:GetScale()==1)
            assert(c.cover:GetWidth()*c.cover:GetScale()<=620+.01)
            assert(c.cover:GetHeight()*c.cover:GetScale()<=460+.01)
            c.ui:SetTab('rewards',true); DrainTimers()
            assert(c.cover:IsVisible() and LegacySystemFrame.RewardTrackPage:IsVisible())
            assert(LegacySystemFrame.RewardTrackPage:GetParent()==LegacySystemFrame and c.lastError==nil and #calls==0)
        ''')

    def test_exact_logical_fit_survives_combat_without_rebuilding_the_frame(self):
        self.fractional_cover()
        self.check('''
            settings.legacyUISize='Compact'; ns.FA.SLASH.legacyui('on'); DrainTimers()
            local c=ns.LegacyUIController; local framesBefore=#frames; local bridge=c.bridge
            assert(c.cover:IsVisible(),c.state)
            inCombat=true; ControllerEvent('PLAYER_REGEN_DISABLED'); DrainTimers()
            assert(c.cover:IsVisible() and c.bridge==bridge and c.ui.width==768 and c.ui.height==500)
            inCombat=false; ControllerEvent('PLAYER_REGEN_ENABLED'); DrainTimers()
            assert(c.cover:IsVisible() and c.state=='Enabled' and c.bridge==bridge and #frames==framesBefore)
            assert(c.ui.width==768 and c.ui.height==500 and c.lastError==nil and #calls==0)
        ''')

    def test_unprovided_dimensions_still_reject_genuinely_undersized_host(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local host=CreateFrame('Frame','UndersizedLogicalFitHost'); host:SetSize(700,600)
            local ok,reason=pcall(c.ui.Fit,c.ui,host,true)
            assert(not ok and reason:find('Compact logical dimensions',1,true))
            assert(c.ui.width==960 and c.ui.height==620 and c.cover:IsVisible())
            host:SetSize(768,640); c.ui:Fit(host,true)
            assert(c.ui.width==768 and c.ui.height==500)
        ''')

    def test_invalid_explicit_logical_dimensions_are_not_silently_clamped(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local ok,reason=pcall(c.ui.Fit,c.ui,c.cover,true,700,450)
            assert(not ok and reason:find('Compact logical dimensions',1,true))
            assert(c.ui.width==960 and c.ui.height==620 and c.cover:IsVisible())
            ok,reason=pcall(c.ui.Fit,c.ui,c.cover,true,768,nil)
            assert(not ok and reason:find('logical dimensions',1,true))
            assert(c.ui.width==960 and c.ui.height==620 and c.lastError==nil and #calls==0)
        ''')


if __name__ == '__main__':
    unittest.main()
