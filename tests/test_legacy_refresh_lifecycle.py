"""Refresh/mount lifecycle regressions with the real Lua controller and bridge.

These fixtures measure invocation counts and state preservation, not elapsed
client time, real rendering, taint, or a confirmed live timeout incident.
"""
import unittest

from test_legacy_wrath_ui import Harness


class LegacyRefreshLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness(controller=True)
        self.h.execute('''
            buildCalls,renderCalls,fitCalls=0,0,0
            local build=ns.LegacyPresentation.Build
            ns.LegacyPresentation.Build=function(...)
                buildCalls=buildCalls+1; return build(...)
            end
            local render=ns.WrathAchievementUI.Render
            ns.WrathAchievementUI.Render=function(...)
                renderCalls=renderCalls+1; return render(...)
            end
            local fit=ns.LegacyUIController.Fit
            ns.LegacyUIController.Fit=function(...)
                fitCalls=fitCalls+1; return fit(...)
            end
            function DrainTimers(maximum)
                local passes=0
                while #timers>0 do
                    passes=passes+1
                    assert(passes<=(maximum or 8),"Refresh timers failed to settle")
                    FlushTimers()
                end
                return passes
            end
            function ControllerEvent(event)
                for _,frame in ipairs(frames) do
                    if frame.events and frame.events[event] then frame:Fire("OnEvent",event); return end
                end
                error("Missing controller event "..event)
            end
        ''')

    def check(self, code):
        self.h.execute(code)

    def test_open_currency_and_native_selection_share_one_model_build(self):
        self.check('''
            LegacySystemFrame:Hide()
            EventRegistry:TriggerEvent("Legacy.SelectPage",1)
            ns.FA.SLASH.legacyui("on")
            local original=LegacySystemFrame:GetScript("OnShow")
            LegacySystemFrame.scripts.OnShow=function(self)
                original(self); EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",{quantity=17})
            end
            assert(buildCalls==0)
            LegacySystemFrame:Show()
            EventRegistry:TriggerEvent("Legacy.SelectPage",2)
            DrainTimers()
            local c=ns.LegacyUIController
            assert(buildCalls==1 and renderCalls==1 and fitCalls==1)
            assert(c.cover:IsVisible() and c.ui.tab=="achievements" and LegacySystemFrame.currentPage==2)
            assert(not LegacySystemFrame.ChallengesPage:IsShown() and #calls==0)
        ''')

    def test_repeated_attach_and_same_page_selection_do_not_rebuild_or_render(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local builds,renders,fits=buildCalls,renderCalls,fitCalls
            local frameCount=#frames
            local hooks=#LegacySystemFrame.hooks.OnShow
            for i=1,12 do c:Attach(); ControllerEvent("ADDON_LOADED") end
            for i=1,30 do EventRegistry:TriggerEvent("Legacy.SelectPage",2) end
            DrainTimers()
            assert(buildCalls==builds and renderCalls==renders and fitCalls==fits)
            assert(#frames==frameCount and #LegacySystemFrame.hooks.OnShow==hooks)
            assert(c.cover:IsVisible() and c.ui.tab=="achievements" and #calls==0)
        ''')

    def test_custom_tabs_and_layout_reuse_model_and_do_not_rescan_native(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local model,builds=c.ui.model,buildCalls
            local reads=0; local categoryList=GetCategoryList
            GetCategoryList=function() reads=reads+1; return categoryList() end
            for _,index in ipairs({2,3,4,1,2,1}) do
                local renders=renderCalls
                c.ui.tabs[index]:Fire("OnClick")
                assert(renderCalls==renders+1)
                assert(c.ui.model==model and buildCalls==builds)
            end
            UIParent:SetSize(1600,1000); UIParent:Fire("OnSizeChanged")
            DrainTimers()
            assert(c.ui.model==model and buildCalls==builds and reads==0)
            assert(c.cover:IsVisible() and saved.done.first==1730000000 and #calls==0)
        ''')

    def test_dirty_bursts_refresh_once_and_keep_authoritative_state_changes(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local builds,reads=buildCalls,0
            local categoryList=GetCategoryList
            GetCategoryList=function() reads=reads+1; return categoryList() end
            saved.done.second=1731000000
            GetAchievementInfo=function(id,index)
                if index then id=({[15607]=62053,[15587]=62013,[15596]=62382})[id] end
                return id,"Updated native",0,true,10,27,24,"Description",0,237388,"",nil,true
            end
            for i=1,30 do
                ControllerEvent("CRITERIA_UPDATE")
                ns.FA.CHECK_HOOKS[1]()
                EventRegistry:TriggerEvent("Legacy.RefreshChallenges")
            end
            assert(#timers==1)
            DrainTimers()
            assert(buildCalls==builds+1 and reads==1)
            assert(c.ui.model.custom.points==30 and c.ui.model.byKey["legacy:62013"].completed)
            assert(saved.done.second==1731000000 and #calls==0)
        ''')

    def test_refresh_during_refresh_defers_one_followup_without_recursive_build(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local build=ns.LegacyPresentation.Build
            local injected,depth,maximum=false,0,0
            ns.LegacyPresentation.Build=function(...)
                depth=depth+1; maximum=math.max(maximum,depth)
                local model=build(...)
                if not injected then
                    injected=true; saved.done.second=1731000000; c:Refresh("custom")
                end
                depth=depth-1; return model
            end
            local builds=buildCalls
            c:Refresh("custom")
            assert(maximum==1 and c.queued and buildCalls==builds+1)
            DrainTimers()
            assert(maximum==1 and buildCalls==builds+2 and c.ui.model.custom.points==30)
            assert(not c.busy and not c.queued and c.cover:IsVisible() and #calls==0)
        ''')

    def test_native_change_during_build_is_not_overwritten_by_stale_catalog(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local build,injected=ns.LegacyPresentation.Build,false
            local categoryList,reads=GetCategoryList,0
            GetCategoryList=function() reads=reads+1; return categoryList() end
            ns.LegacyPresentation.Build=function(...)
                local model=build(...)
                if not injected then injected=true; ControllerEvent("ACHIEVEMENT_EARNED") end
                return model
            end
            c:Refresh("custom")
            assert(c.nativeCatalog==nil and c.queued)
            DrainTimers()
            assert(reads==1 and c.nativeCatalog==c.ui.model.native and not c.queued and #calls==0)
        ''')

    def test_stale_refresh_selection_and_attach_timers_cannot_reopen_closed_window(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local builds=buildCalls
            c:Schedule("native"); c:QueueAttach()
            EventRegistry:TriggerEvent("Legacy.SelectPage",3)
            c:Close()
            DrainTimers()
            assert(buildCalls==builds and not LegacySystemFrame:IsShown() and not c.cover:IsShown())
            assert(LegacySystemFrame.TreePage:GetParent()==LegacySystemFrame and LegacySystemFrame.TreePage:GetScale()==1)
            LegacySystemFrame:Show()
            DrainTimers()
            assert(buildCalls==builds+1 and c.cover:IsVisible() and c.ui.tab=="trees")
            local reopened=buildCalls
            DrainTimers()
            assert(buildCalls==reopened and #calls==0)
        ''')

    def test_close_cancels_ui_query_work_and_reopen_retains_latest_search(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.category="general"; c.ui:Render()
            local renders=renderCalls
            c.ui.searchBox:SetText("Second")
            c.ui.searchBox:Fire("OnTextChanged",true)
            assert(c.ui.searchQueued and c.ui.search=="Second")
            c:Close(); DrainTimers()
            assert(not c.ui.searchQueued and not c.ui.renderQueued and renderCalls==renders)
            assert(not c.cover:IsVisible() and c.ui.search=="Second")
            LegacySystemFrame:Show(); DrainTimers()
            assert(renderCalls==renders+1 and c.cover:IsVisible() and c.ui.search=="Second")
            assert(c.ui.cards[1].record.key=="custom:second" and #calls==0)
        ''')

    def test_partial_native_catalog_is_retained_until_real_native_invalidation(self):
        self.check('''
            GetCategoryNumAchievements=function() return nil end
            local reads=0; local categoryList=GetCategoryList
            GetCategoryList=function() reads=reads+1; return categoryList() end
            ns.FA.SLASH.legacyui("on"); DrainTimers()
            local c=ns.LegacyUIController
            assert(c.nativeCatalog and c.nativeCatalog.partial and reads==1)
            for i=1,5 do c:Refresh("custom"); c.ui.tabs[2]:Fire("OnClick"); c.ui.tabs[1]:Fire("OnClick") end
            assert(reads==1)
            EventRegistry:TriggerEvent("Legacy.RefreshChallenges"); DrainTimers()
            assert(reads==2 and c.nativeCatalog.partial and #calls==0)
        ''')

    def test_geometry_notifications_generated_by_layout_settle_after_one_followup(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local fit=c.ui.Fit
            c.ui.Fit=function(...)
                fit(...); LegacySystemFrame:Fire("OnSizeChanged")
            end
            local builds,fits=buildCalls,fitCalls
            UIParent:SetSize(1600,1000); UIParent:Fire("OnSizeChanged")
            local passes=DrainTimers(4)
            assert(passes<=2 and fitCalls==fits+1 and buildCalls==builds)
            assert(c.cover:IsVisible() and not c.queued and #calls==0)
        ''')

    def test_native_page_mount_skips_unchanged_setters_and_repairs_changed_geometry(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[2]:Fire("OnClick")
            local reward=LegacySystemFrame.RewardTrackPage
            local mutations=0
            for _,method in ipairs({"ClearAllPoints","SetPoint","SetSize","SetScale","SetFrameStrata","SetFrameLevel"}) do
                local original=reward[method]
                reward[method]=function(self,...)
                    mutations=mutations+1; return original(self,...)
                end
            end
            for i=1,8 do c:Refresh("custom") end
            assert(mutations==0)
            reward.scale=.13
            c:Refresh("custom")
            assert(mutations==1 and reward:GetScale()~=.13)
            assert(reward:GetParent()==LegacySystemFrame and reward:IsVisible() and #calls==0)
        ''')

    def test_unchanged_currency_notifications_do_not_rebuild_and_changed_header_updates(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local builds=buildCalls
            local payload={renownCurrency=999,quantity=17,sentinel="keep"}
            for i=1,30 do EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload) end
            assert(#timers==0 and buildCalls==builds)
            C_MajorFactions.GetCurrentRenownLevel=function() return 21 end
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload); DrainTimers()
            assert(buildCalls==builds+1 and c.ui.nativePoints:GetText()=="21")
            assert(payload.quantity==17 and payload.renownCurrency==999 and payload.sentinel=="keep" and #calls==0)
        ''')

    def test_native_snapshot_refreshes_at_thirty_seconds_on_existing_data_updates(self):
        self.check('''
            local now,reads=0,0
            GetTime=function() return now end
            local categoryList=GetCategoryList
            GetCategoryList=function() reads=reads+1; return categoryList() end
            ns.FA.SLASH.legacyui("on"); DrainTimers()
            local c=ns.LegacyUIController
            assert(reads==1 and c.nativeCatalogAt==0)
            now=29.9; c:Refresh("custom")
            assert(reads==1)
            local info=GetAchievementInfo
            GetAchievementInfo=function(...)
                local function pack(...) return {n=select("#",...),...} end
                local values=pack(info(...)); values[4]=true
                return unpack(values,1,values.n)
            end
            now=30; c:Refresh("custom")
            assert(reads==2 and c.nativeCatalogAt==30 and c.ui.model.byKey["legacy:62013"].completed)
            now=31; c:Refresh("custom")
            assert(reads==2 and #timers==0 and saved.done.second==nil and #calls==0)
        ''')

    def test_unknown_clock_uses_bounded_data_reuses_without_inventing_an_age(self):
        self.check('''
            GetTime=function() error("Clock unavailable") end
            local categoryList,reads=GetCategoryList,0
            GetCategoryList=function() reads=reads+1; return categoryList() end
            ns.FA.SLASH.legacyui("on"); DrainTimers()
            local c=ns.LegacyUIController
            assert(reads==1 and c.nativeCatalogAt==nil)
            for i=1,c.NATIVE_MAX_UNTIMED_REUSES-1 do c:Refresh("custom") end
            assert(reads==1 and c.nativeCatalogAt==nil)
            c:Refresh("custom")
            assert(reads==2 and c.nativeCatalogAt==nil and c.nativeDataReuses==0)
            assert(#timers==0 and c.cover:IsVisible() and #calls==0)
        ''')

    def test_changed_tree_currency_refreshes_active_statistics_without_rebuilding_achievements(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            c.ui.tabs[4]:Fire("OnClick")
            local previous=c.ui.statisticsCatalog
            local builds,renders=buildCalls,renderCalls
            local payload={quantity=10,spentInTree=5,maxQuantity=100,traitCurrencyID=4225,sentinel="keep"}
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload)
            assert(c.ui.statisticsCatalog==nil)
            DrainTimers()
            assert(buildCalls==builds and renderCalls==renders+1)
            assert(c.ui.statisticsCatalog and c.ui.statisticsCatalog~=previous)
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo",payload)
            assert(#timers==0 and buildCalls==builds)
            assert(payload.quantity==10 and payload.spentInTree==5 and payload.sentinel=="keep")
            assert(LegacySystemFrame.currentPage==2 and #calls==0)
        ''')

    def test_missing_attach_timer_retains_pending_request_without_inline_recursion(self):
        self.h.enable()
        self.check('''
            local c=ns.LegacyUIController
            local attach,callsCount=c.Attach,0
            c.Attach=function(...)
                callsCount=callsCount+1; assert(callsCount<4,"Recursive inline Attach")
                return attach(...)
            end
            C_Timer.After=nil
            c.busy=true; c:Attach()
            assert(callsCount==1 and c.attachPending and not c.attachQueued)
            c.busy=false; c.attaching=true; c:Attach()
            assert(callsCount==2 and c.attachPending and not c.attachQueued)
            c.attaching=false; c.attachPending=false
            assert(c.cover:IsVisible() and LegacySystemFrame.currentPage==2 and #calls==0)
        ''')

    def test_repeated_unknown_currency_is_unchanged_but_known_transitions_refresh(self):
        self.check('''
            C_MajorFactions.GetCurrentRenownLevel=function() return nil end
            ns.FA.SLASH.legacyui("on"); DrainTimers()
            local c=ns.LegacyUIController
            local builds=buildCalls
            assert(c.currencyObserved and c.currencyValue==nil and c.ui.nativePoints:GetText()=="Unavailable")
            for i=1,4 do EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo"); DrainTimers() end
            assert(buildCalls==builds)
            C_MajorFactions.GetCurrentRenownLevel=function() return 21 end
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo"); DrainTimers()
            assert(buildCalls==builds+1 and c.ui.nativePoints:GetText()=="21")
            C_MajorFactions.GetCurrentRenownLevel=function() error("Renown unavailable") end
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo"); DrainTimers()
            assert(buildCalls==builds+2 and c.ui.nativePoints:GetText()=="Unavailable")
            EventRegistry:TriggerEvent("Legacy.UpdateCurrencyInfo"); DrainTimers()
            assert(buildCalls==builds+2 and #calls==0)
        ''')

    def test_optional_performance_hooks_capture_controller_work_without_dependency(self):
        self.check('''
            local names,finished,coalesced={},0,0
            ns.LegacyPerf={Begin=function(name) names[name]=true; return {} end,
                Finish=function(token) assert(type(token)=="table"); finished=finished+1 end,
                Count=function(name,n) if name=="controller.refresh.coalesced" then coalesced=coalesced+n end end}
            ns.FA.SLASH.legacyui("on")
            ns.LegacyUIController:Schedule("custom"); ns.LegacyUIController:Schedule("custom")
            DrainTimers()
            assert(names["controller.attach"] and names["controller.refresh"] and names["native.mount"] and names["window.fit"])
            assert(finished>=5 and coalesced>=1 and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
