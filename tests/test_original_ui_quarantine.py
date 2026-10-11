"""Retained alpha consumers cannot surface the archived UI by default."""
import unittest

from test_standalone_unknown_progress import ConsumerHarness


class OriginalUIQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.h = ConsumerHarness(original_ui=False)

    def test_local_slash_and_exported_openers_preserve_state_without_frames(self):
        self.h.execute('''
            local count=#frames
            local db=ns.LAR.DB()
            db.tracked.q50=true
            assert(ns.LAR.Open()==false)
            assert(ns.LAR.OpenSearch("quest")==false)
            assert(ns.LAR.ShowTab("summary")==false)
            SlashCmdList.LEGACYACHIEVEMENTSREFORGED("")
            SlashCmdList.LEGACYACHIEVEMENTSREFORGED("unknown-command")
            assert(LegacyAchievementsReforgedWindow==nil and #frames==count)
            assert(db.tab=="quests" and db.tracked.q50 and db.done.first==1730000000)
            assert(db.history[1]=="keep" and ns.LAR.Settings().sort=="progress" and #calls==0)
        ''')

    def test_default_and_missing_policy_keep_window_closed(self):
        self.h.g.ns.OriginalUI.enabled = True
        self.h.load("UI/OriginalUIPolicy.lua")
        self.h.execute('''
            assert(not ns.OriginalUI.IsEnabled() and ns.LAR.Open()==false)
            ns.OriginalUI=nil
            assert(ns.LAR.OpenSearch("quest")==false and ns.LAR.ShowTab("summary")==false)
            assert(LegacyAchievementsReforgedWindow==nil)
        ''')

    def test_minimap_and_broker_are_not_registered_or_preferences_changed(self):
        self.h.execute('''
            local settings=ns.LAR.Settings()
            settings.minimap={hide=false,minimapPos=123}
            settings.minimapShown=true
            LibStub=function() error("Quarantined launcher accessed libraries") end
            before=#frames
        ''')
        self.h.load("Minimap.lua")
        self.h.execute('''
            assert(#frames==before and ns.LAR.SetMinimapShown==nil)
            local settings=ns.LAR.Settings()
            assert(settings.minimap.hide==false and settings.minimap.minimapPos==123)
            assert(settings.minimapShown==true)
        ''')

    def test_welcome_and_queued_retry_cannot_create_popup_or_mark_it_seen(self):
        self.h.load("Welcome.lua")
        self.h.execute('''
            timers={}
            local count=#frames
            assert(ns.LAR.ShowWelcome()==false)
            ns.LAR.SLASH.welcome()
            ns.LAR.OnReady(true)
            assert(#timers==0 and #frames==count and not ns.LAR.DB().welcomeSeen)
            -- A research session may have queued its first attempt before disabling.
            ns.OriginalUI.enabled=true
            ns.LAR.OnReady(true)
            assert(#timers==1)
            ns.OriginalUI.enabled=false
            FlushTimers()
            assert(#timers==0 and #frames==count and LegacyAchievementsReforgedWelcome==nil)
            assert(not ns.LAR.DB().welcomeSeen)
        ''')

    def test_binding_and_tracker_clicks_block_window_but_keep_tracking(self):
        self.h.load("Themes.lua")
        self.h.load("Tracker.lua")
        self.h.execute('''
            ns.LAR.DB().tracked.q50=true
            ns.LAR.UpdateTracker()
            local row=TrackerRow("q50")
            assert(row and LegacyAchievementsReforgedTracker:IsShown())
            LegacyAchievementsReforged_Toggle()
            LegacyAchievementsReforgedTracker.children[1]:Fire("OnClick","LeftButton")
            row:Fire("OnClick","LeftButton")
            assert(LegacyAchievementsReforgedWindow==nil and ns.LAR.DB().tracked.q50)
            row:Fire("OnClick","RightButton")
            assert(not ns.LAR.DB().tracked.q50)
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
            assert(LegacyAchievementsReforgedWindow==nil)
            assert(type(ns.LAR.RequestCompare)=="function" and type(ns.LAR.SLASH.compare)=="function")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_legacy_command_dispatch_remains_available(self):
        self.h.execute('''
            local received
            ns.LAR.SLASH.legacyui=function(rest) received=rest end
            local count=#messages
            SlashCmdList.LEGACYACHIEVEMENTSREFORGED("legacyui on")
            assert(received=="on" and #messages==count and LegacyAchievementsReforgedWindow==nil)
        ''')

    def test_real_legacy_controller_still_opens_with_original_ui_quarantined(self):
        # Core bootstrap timers need bag/inventory APIs outside this UI fixture.
        self.h.execute('timers={}; SetupNative()')
        for path in ("Integrations/CustomAdapter.lua", "Integrations/StatisticsAdapter.lua",
                     "Integrations/LegacyWindowBridge.lua", "Integrations/LegacyController.lua"):
            self.h.load(path)
        self.h.execute('''
            SlashCmdList.LEGACYACHIEVEMENTSREFORGED("legacyui on")
            for i=1,8 do FlushTimers() end
            local c=ns.LegacyUIController
            assert(c.ui and c.ui.root:IsVisible() and c.state=="Enabled")
            assert(LegacyAchievementsReforgedWindow==nil and not ns.OriginalUI.IsEnabled())
            assert(ns.LAR.OpenSearch("quest")==false and c.ui.root:IsVisible())
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_developer_switch_restores_retained_window_and_launcher(self):
        self.h.execute('''
            ns.OriginalUI.enabled=true
            assert(ns.LAR.Open()==true and LegacyAchievementsReforgedWindow:IsShown())
            ns.LAR.ShowTab("quests")
            assert(ns.LAR.DB().tab=="quests")
            ns.LAR.OpenSearch("quest")
            assert(LegacyAchievementsReforgedWindow.searchBox:GetText()=="quest")
            brokerCount,registerCount=0,0
            local ldb={NewDataObject=function(self,name,object)
                assert(name=="LegacyAchievementsReforged"); brokerCount=brokerCount+1; return object
            end}
            local icon={Register=function(self,name,object,db)
                assert(name=="LegacyAchievementsReforged" and object.OnClick and db)
                registerCount=registerCount+1
            end}
            LibStub=function(name) if name=="LibDataBroker-1.1" then return ldb else return icon end end
        ''')
        self.h.load("Minimap.lua")
        self.h.execute('''
            assert(brokerCount==1 and type(ns.LAR.SetMinimapShown)=="function")
            frames[#frames]:Fire("OnEvent","PLAYER_LOGIN")
            assert(registerCount==1)
        ''')


if __name__ == "__main__":
    unittest.main()
