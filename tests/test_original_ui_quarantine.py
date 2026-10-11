"""Retained alpha consumers cannot surface the archived UI by default."""
import unittest

from test_standalone_unknown_progress import ConsumerHarness


class OriginalUIQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.h = ConsumerHarness(original_ui=False)

    def test_local_slash_and_exported_openers_preserve_state_without_frames(self):
        self.h.execute('''
            local count=#frames
            local db=ns.FA.DB()
            db.tracked.q50=true
            assert(ns.FA.Open()==false)
            assert(ns.FA.OpenSearch("quest")==false)
            assert(ns.FA.ShowTab("summary")==false)
            SlashCmdList.FOREVERACHIEVEMENTS("")
            SlashCmdList.FOREVERACHIEVEMENTS("unknown-command")
            assert(ForeverAchievementsWindow==nil and #frames==count)
            assert(db.tab=="quests" and db.tracked.q50 and db.done.first==1730000000)
            assert(db.history[1]=="keep" and ns.FA.Settings().sort=="progress" and #calls==0)
        ''')

    def test_default_and_missing_policy_keep_window_closed(self):
        self.h.g.ns.OriginalUI.enabled = True
        self.h.load("UI/OriginalUIPolicy.lua")
        self.h.execute('''
            assert(not ns.OriginalUI.IsEnabled() and ns.FA.Open()==false)
            ns.OriginalUI=nil
            assert(ns.FA.OpenSearch("quest")==false and ns.FA.ShowTab("summary")==false)
            assert(ForeverAchievementsWindow==nil)
        ''')

    def test_minimap_and_broker_are_not_registered_or_preferences_changed(self):
        self.h.execute('''
            local settings=ns.FA.Settings()
            settings.minimap={hide=false,minimapPos=123}
            settings.minimapShown=true
            LibStub=function() error("Quarantined launcher accessed libraries") end
            before=#frames
        ''')
        self.h.load("Minimap.lua")
        self.h.execute('''
            assert(#frames==before and ns.FA.SetMinimapShown==nil)
            local settings=ns.FA.Settings()
            assert(settings.minimap.hide==false and settings.minimap.minimapPos==123)
            assert(settings.minimapShown==true)
        ''')

    def test_welcome_and_queued_retry_cannot_create_popup_or_mark_it_seen(self):
        self.h.load("Welcome.lua")
        self.h.execute('''
            timers={}
            local count=#frames
            assert(ns.FA.ShowWelcome()==false)
            ns.FA.SLASH.welcome()
            ns.FA.OnReady(true)
            assert(#timers==0 and #frames==count and not ns.FA.DB().welcomeSeen)
            -- A research session may have queued its first attempt before disabling.
            ns.OriginalUI.enabled=true
            ns.FA.OnReady(true)
            assert(#timers==1)
            ns.OriginalUI.enabled=false
            FlushTimers()
            assert(#timers==0 and #frames==count and ForeverAchievementsWelcome==nil)
            assert(not ns.FA.DB().welcomeSeen)
        ''')

    def test_binding_and_tracker_clicks_block_window_but_keep_tracking(self):
        self.h.load("Themes.lua")
        self.h.load("Tracker.lua")
        self.h.execute('''
            ns.FA.DB().tracked.q50=true
            ns.FA.UpdateTracker()
            local row=TrackerRow("q50")
            assert(row and ForeverAchievementsTracker:IsShown())
            ForeverAchievements_Toggle()
            ForeverAchievementsTracker.children[1]:Fire("OnClick","LeftButton")
            row:Fire("OnClick","LeftButton")
            assert(ForeverAchievementsWindow==nil and ns.FA.DB().tracked.q50)
            row:Fire("OnClick","RightButton")
            assert(not ns.FA.DB().tracked.q50)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_social_tooltip_retained_and_original_compare_menu_quarantined(self):
        self.h.execute('''
            Menu={ModifyMenu=function() error("Original comparison menu registered") end}
        ''')
        self.h.load("Social.lua")
        self.h.execute('''
            OpenAchievementLink("q50")
            assert(ItemRefTooltip.shown and TooltipContains("Open the Legacy panel to browse achievements."))
            IsShiftKeyDown=function() return true end
            OpenAchievementLink("q50")
            assert(ForeverAchievementsWindow==nil)
            assert(type(ns.FA.RequestCompare)=="function" and type(ns.FA.SLASH.compare)=="function")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_legacy_command_dispatch_remains_available(self):
        self.h.execute('''
            local received
            ns.FA.SLASH.legacyui=function(rest) received=rest end
            local count=#messages
            SlashCmdList.FOREVERACHIEVEMENTS("legacyui on")
            assert(received=="on" and #messages==count and ForeverAchievementsWindow==nil)
        ''')

    def test_real_legacy_controller_still_opens_with_original_ui_quarantined(self):
        # Core bootstrap timers need bag/inventory APIs outside this UI fixture.
        self.h.execute('timers={}; SetupNative()')
        for path in ("Integrations/CustomAdapter.lua", "Integrations/StatisticsAdapter.lua",
                     "Integrations/LegacyWindowBridge.lua", "Integrations/LegacyController.lua"):
            self.h.load(path)
        self.h.execute('''
            SlashCmdList.FOREVERACHIEVEMENTS("legacyui on")
            for i=1,8 do FlushTimers() end
            local c=ns.LegacyUIController
            assert(c.ui and c.ui.root:IsVisible() and c.state=="Enabled")
            assert(ForeverAchievementsWindow==nil and not ns.OriginalUI.IsEnabled())
            assert(ns.FA.OpenSearch("quest")==false and c.ui.root:IsVisible())
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_developer_switch_restores_retained_window_and_launcher(self):
        self.h.execute('''
            ns.OriginalUI.enabled=true
            assert(ns.FA.Open()==true and ForeverAchievementsWindow:IsShown())
            ns.FA.ShowTab("quests")
            assert(ns.FA.DB().tab=="quests")
            ns.FA.OpenSearch("quest")
            assert(ForeverAchievementsWindow.searchBox:GetText()=="quest")
            brokerCount,registerCount=0,0
            local ldb={NewDataObject=function(self,name,object)
                assert(name=="ForeverAchievements"); brokerCount=brokerCount+1; return object
            end}
            local icon={Register=function(self,name,object,db)
                assert(name=="ForeverAchievements" and object.OnClick and db)
                registerCount=registerCount+1
            end}
            LibStub=function(name) if name=="LibDataBroker-1.1" then return ldb else return icon end end
        ''')
        self.h.load("Minimap.lua")
        self.h.execute('''
            assert(brokerCount==1 and type(ns.FA.SetMinimapShown)=="function")
            frames[#frames]:Fire("OnEvent","PLAYER_LOGIN")
            assert(registerCount==1)
        ''')


if __name__ == "__main__":
    unittest.main()
