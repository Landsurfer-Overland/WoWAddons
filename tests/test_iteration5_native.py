"""Bounded native-page fit and reversible mounts with the real Lua bridge.

Frame doubles exercise logical geometry and callbacks. They do not establish
live WoW artwork quality, taint safety, click targeting, or client performance.
"""
import unittest

from test_legacy_wrath_ui import Harness


class Iteration5NativeFitTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute("""
            SetupNative()
            fitHost=CreateFrame('Frame','Iteration5NativeHost',UIParent)
            fitHost:SetSize(974,674)
            fitHost:SetPoint('CENTER',UIParent,'CENTER',0,0)
            function nearly(a,b) assert(math.abs(a-b)<.00001,tostring(a)..' ~= '..tostring(b)) end
            function fitted(page,host)
                local scale=page:GetEffectiveScale()
                local hostScale=host:GetEffectiveScale()
                local width,height=page:GetWidth()*scale,page:GetHeight()*scale
                assert(width<=host:GetWidth()*hostScale+.00001)
                assert(height<=host:GetHeight()*hostScale+.00001)
                local px,py=page:GetCenter(); local hx,hy=host:GetCenter()
                nearly(px*scale,hx*hostScale); nearly(py*scale,hy*hostScale)
                local point,relative,relativePoint,x,y=page:GetPoint(1)
                assert(point=='CENTER' and relative==host and relativePoint=='CENTER' and x==0 and y==0)
                assert(page:GetNumPoints()==1 and page:GetParent()==LegacySystemFrame)
                return width,height
            end
        """)
        self.h.load("Integrations/LegacyWindowBridge.lua")

    def check(self, code):
        self.h.execute(code)

    def test_large_host_enlarges_both_pages_without_changing_original_dimensions(self):
        self.check("""
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            for _,pair in ipairs({{'rewards',LegacySystemFrame.RewardTrackPage,910,569},
                {'trees',LegacySystemFrame.TreePage,920,575}}) do
                b:Mount(pair[1],fitHost)
                local page=pair[2]
                assert(page:GetScale()>1)
                assert(page:GetWidth()==pair[3] and page:GetHeight()==pair[4])
                local width,height=fitted(page,fitHost)
                nearly(width/height,pair[3]/pair[4])
                nearly(math.max(width/974,height/674),1)
                assert(page.Background:IsShown())
            end
            assert(LegacySystemFrame.TreePage.VerticalDivider:IsShown() and #calls==0)
        """)

    def test_distinct_effective_scales_fit_in_screen_space_and_restore_original_scale(self):
        self.check("""
            UIParent:SetScale(.77); LegacySystemFrame.scale=1.23; fitHost:SetScale(.61)
            LegacySystemFrame.RewardTrackPage.scale=.88
            LegacySystemFrame.TreePage.scale=1.14
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            for _,view in ipairs({'rewards','trees'}) do
                b:Mount(view,fitHost)
                local page=view=='rewards' and LegacySystemFrame.RewardTrackPage or LegacySystemFrame.TreePage
                fitted(page,fitHost)
                nearly(page:GetScale(),math.min(1.5,974/page:GetWidth(),674/page:GetHeight())*.61/1.23)
            end
            assert(b:Restore())
            nearly(LegacySystemFrame.RewardTrackPage:GetScale(),.88)
            nearly(LegacySystemFrame.TreePage:GetScale(),1.14)
            assert(#calls==0)
        """)

    def test_repeat_mounts_reuse_geometry_without_setters_new_frames_or_show_callbacks(self):
        self.check("""
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            b:Mount('rewards',fitHost)
            local page=LegacySystemFrame.RewardTrackPage
            local writes,frameCount,shows=0,#frames,rewardShows
            for _,name in ipairs({'SetPoint','ClearAllPoints','SetScale','SetSize','SetFrameLevel','SetFrameStrata'}) do
                local original=page[name]
                page[name]=function(self,...) writes=writes+1; return original(self,...) end
            end
            for i=1,50 do b:Mount('rewards',fitHost) end
            assert(writes==0 and #frames==frameCount and rewardShows==shows and #timers==0)
            assert(not page:GetScript('OnUpdate') and #calls==0)
        """)

    def test_resized_and_scaled_host_never_compounds_a_previous_mount(self):
        self.check("""
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            for _,size in ipairs({{718,454,.8},{974,674,1},{850,574,.6},{974,674,1}}) do
                fitHost:SetSize(size[1],size[2]); fitHost:SetScale(size[3])
                for _,view in ipairs({'rewards','trees'}) do
                    b:Mount(view,fitHost)
                    local page=view=='rewards' and LegacySystemFrame.RewardTrackPage or LegacySystemFrame.TreePage
                    fitted(page,fitHost)
                    nearly(page:GetScale(),math.min(1.5,size[1]/page:GetWidth(),size[2]/page:GetHeight())*size[3])
                end
            end
            nearly(LegacySystemFrame.TreePage:GetScale(),974/920)
            assert(#calls==0)
        """)

    def test_oversized_host_caps_uniform_artwork_enlargement(self):
        self.check("""
            fitHost:SetSize(4096,4096)
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            b:Mount('trees',fitHost)
            nearly(LegacySystemFrame.TreePage:GetScale(),1.5)
            fitted(LegacySystemFrame.TreePage,fitHost)
            assert(LegacySystemFrame.TreePage:GetWidth()==920 and LegacySystemFrame.TreePage:GetHeight()==575)
        """)

    def test_failed_host_preflight_cannot_select_or_suppress_native_pages(self):
        self.check("""
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            local original=fitHost.GetWidth
            for _,bad in ipairs({0,-1,9000,math.huge}) do
                fitHost.GetWidth=function() return bad end
                assert(not pcall(b.Mount,b,'rewards',fitHost))
                assert(not b.active and LegacySystemFrame.currentPage==2)
                assert(LegacySystemFrame.Background:IsShown() and LegacySystemFrame:IsMouseEnabled())
                assert(LegacySystemFrame.ChallengesPage:IsShown())
                assert(LegacySystemFrame.RewardTrackPage:GetScale()==1)
            end
            for _,getter in ipairs({function() return nil end,function() error('Unavailable') end,
                function() return 0/0 end}) do
                fitHost.GetWidth=getter
                assert(not pcall(b.Mount,b,'rewards',fitHost) and not b.active)
            end
            fitHost.GetWidth=original
            b:Mount('rewards',fitHost); assert(b:Restore() and #calls==0)
        """)

    def test_unreadable_or_zero_effective_scale_uses_existing_error_path(self):
        self.check("""
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            local getRoot=LegacySystemFrame.GetEffectiveScale
            LegacySystemFrame.GetEffectiveScale=function() return 0 end
            assert(not pcall(b.Mount,b,'trees',fitHost) and not b.active)
            LegacySystemFrame.GetEffectiveScale=function() return nil end
            assert(not pcall(b.Mount,b,'trees',fitHost) and not b.active)
            LegacySystemFrame.GetEffectiveScale=getRoot
            fitHost.GetEffectiveScale=function() return nil end
            assert(not pcall(b.Mount,b,'trees',fitHost) and not b.active)
            assert(LegacySystemFrame.currentPage==2 and LegacySystemFrame.NativeTabs:IsShown() and #calls==0)
        """)

    def test_restore_preserves_native_scripts_children_rewards_and_original_geometry(self):
        self.check("""
            local reward,tree=LegacySystemFrame.RewardTrackPage,LegacySystemFrame.TreePage
            local control=CreateFrame('Button','NativeRewardControl',reward)
            local clicks=0; control:SetScript('OnClick',function() clicks=clicks+1 end)
            local handler,provider=reward:GetScript('OnShow'),LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.dataProvider
            local rewardData=reward.majorFactionData
            tree.Background:Hide()
            local b=ns.LegacyWindowBridge.New(LegacySystemFrame)
            b:Mount('rewards',fitHost); control:Fire('OnClick')
            b:Mount('trees',fitHost)
            assert(b:Restore() and not b.active)
            local point,relative,relativePoint,x,y=reward:GetPoint(1)
            assert(point=='TOPLEFT' and relative==LegacySystemFrame and relativePoint=='TOPLEFT' and x==7 and y==-5)
            assert(reward:GetWidth()==910 and reward:GetHeight()==569 and reward:GetScale()==1)
            assert(reward:GetFrameLevel()==100 and reward:GetFrameStrata()=='DIALOG')
            assert(reward:GetScript('OnShow')==handler and reward.majorFactionData==rewardData)
            assert(LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.dataProvider==provider)
            assert(control:GetParent()==reward and clicks==1 and tree:GetWidth()==920 and tree:GetHeight()==575)
            assert(not tree.Background:IsShown() and tree.VerticalDivider:IsShown())
            assert(tree:IsShown() and not reward:IsShown())
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        """)

    def test_invalid_native_dimensions_fail_before_any_presentation_mutation(self):
        self.check("""
            LegacySystemFrame.TreePage.width=9000
            assert(not pcall(ns.LegacyWindowBridge.New,LegacySystemFrame))
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame.Background:IsShown())
            assert(LegacySystemFrame:IsMouseEnabled() and LegacySystemFrame.currentPage==2 and #calls==0)
        """)


class Iteration5NativeControllerTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness(controller=True)

    def check(self, code):
        self.h.execute(code)

    def test_large_and_other_presets_fit_both_live_pages_without_data_rebuilds(self):
        self.h.enable()
        self.check("""
            local c=ns.LegacyUIController
            local builds=0; local build=ns.LegacyPresentation.Build
            ns.LegacyPresentation.Build=function(...) builds=builds+1; return build(...) end
            local model=c.ui.model
            for _,preset in ipairs({'Large','Compact','Standard','Large'}) do
                c:SetSizePreset(preset)
                for _,pair in ipairs({{2,LegacySystemFrame.RewardTrackPage},{3,LegacySystemFrame.TreePage}}) do
                    c.ui.tabs[pair[1]]:Fire('OnClick')
                    local page,host=pair[2],c.ui.nativeHost
                    local width,height=page:GetWidth()*page:GetEffectiveScale(),page:GetHeight()*page:GetEffectiveScale()
                    assert(width<=host:GetWidth()*host:GetEffectiveScale()+.00001)
                    assert(height<=host:GetHeight()*host:GetEffectiveScale()+.00001)
                    if preset=='Large' then
                        assert(page:GetEffectiveScale()>LegacySystemFrame:GetEffectiveScale())
                    end
                    assert(page:GetParent()==LegacySystemFrame and page:IsVisible())
                    assert(c.ui.model==model and c.cover:IsVisible())
                end
            end
            assert(builds==0 and saved.done.first==1730000000 and #calls==0)
        """)

    def test_scale_setter_error_restores_native_window_through_retained_fallback(self):
        self.h.enable()
        self.check("""
            local c=ns.LegacyUIController
            c:SetSizePreset('Large')
            local reward=LegacySystemFrame.RewardTrackPage
            local original=reward.SetScale
            reward.SetScale=function(self,value)
                if value~=1 then error('Injected native upscale failure') end
                return original(self,value)
            end
            c.ui.tabs[2]:Fire('OnClick')
            assert(c.state:find('Fallback') and not c.cover:IsShown())
            assert(reward:GetScale()==1 and reward:GetWidth()==910 and reward:GetHeight()==569)
            assert(reward:IsVisible() and reward:GetParent()==LegacySystemFrame)
            assert(LegacySystemFrame.NativeTabs:IsShown() and LegacySystemFrame:IsMouseEnabled())
            assert(not c.restorePending and saved.done.first==1730000000 and #calls==0)
        """)

    def test_protected_page_and_combat_defer_scale_changes_and_restore_later(self):
        self.h.enable()
        self.check("""
            local c=ns.LegacyUIController
            c.ui.tabs[3]:Fire('OnClick')
            local tree=LegacySystemFrame.TreePage
            local writes=0; local setter=tree.SetScale
            tree.SetScale=function(self,value) writes=writes+1; return setter(self,value) end
            tree.protected=true; inCombat=true
            c:SetSizePreset('Large')
            assert(writes==0)
            ns.FA.SLASH.legacyui('off')
            assert(c.restorePending and c.cover:IsVisible() and writes==0)
            tree.protected=false; inCombat=false
            for _,frame in ipairs(frames) do
                if frame.events and frame.events.PLAYER_REGEN_ENABLED then frame:Fire('OnEvent','PLAYER_REGEN_ENABLED'); break end
            end
            assert(not c.restorePending and not c.cover:IsShown() and tree:GetScale()==1)
            assert(LegacySystemFrame.NativeTabs:IsShown() and saved.done.first==1730000000 and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
