"""Current minimap launcher without exposing the archived alpha window."""
from pathlib import Path
import unittest

from test_legacy_wrath_ui import LuaRuntime, ADDON, Harness


class MinimapTests(unittest.TestCase):
    def test_native_launcher(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        checks = Path(__file__).with_name("minimap_checks.lua").read_text()
        run = lua.execute("return assert(loadstring(...))", checks)
        self.assertEqual(run(str(ADDON / "Minimap.lua")), 11)

    def test_level_one_open_uses_real_reforged_controller(self):
        h = Harness(controller=True)
        h.execute('''
            ns.OriginalUI={IsEnabled=function() return false end}
            ns.LAR.Open=function() error("Archived window opened") end
            UnitLevel=function() return 1 end
            ToggleLegacySystemUI=function() error("Unlock-gated toggle called") end
            LegacySystemFrame:Hide()
            function LegacySystemFrame:ShowChallenges()
                self:Show()
                EventRegistry:TriggerEvent("Legacy.SelectPage",2)
            end
            settings.legacyUI=true
        ''')
        h.load("Minimap.lua")
        h.execute('''
            assert(ns.LAR.ToggleAchievements())
            for i=1,8 do FlushTimers() end
            local c=ns.LegacyUIController
            assert(c.state=="Enabled" and c.cover:IsVisible() and c.ui.tab=="achievements")
            assert(ns.LAR.ToggleAchievements())
            for i=1,8 do FlushTimers() end
            assert(not LegacySystemFrame:IsShown() and not c.cover:IsShown())
            assert(LegacyAchievementsReforgedWindow==nil and #calls==0)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep")
        ''')
