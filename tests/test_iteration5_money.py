"""Iteration 5 player-facing currency text and persisted layout choices.

These execute the actual Lua tracker/controller; they do not test game rendering.
"""
import unittest

from test_iteration4_money import MoneyHarness
from test_legacy_wrath_ui import Harness


class Iteration5MoneyPresentationTests(unittest.TestCase):
    def setUp(self):
        self.h = MoneyHarness()

    def test_known_earnings_show_amount_and_target_without_provenance_filler(self):
        self.h.execute('''
            M.Sync(db)
            assert(M.ObserveLoot(db,"You loot 2 Gold, 3 Silver, 4 Copper.",15))
            local current,goal,label=M.Progress(db,"gold100")
            assert(current==20304 and goal==50000 and label=="2g 3s 4c / 5g")
            assert(M.Description("gold100")=="Loot 5g.")
            local report=table.concat(M.Report(db),"\\n")
            assert(report:find("source=since_tracking",1,true))
            assert(db.moneyTracking.observedLootCopper==20304 and db.money==38)
        ''')

    def test_unknown_quest_income_keeps_unknown_amount_and_plain_goal(self):
        self.h.execute('''
            stats[326]="38"
            local current,goal,label=M.Progress(db,"breadwinner")
            assert(current==nil and goal==1000000 and label=="— / 100g")
            assert(M.Description("breadwinner")=="Earn 100g from quest rewards.")
            local _,mode,detail=M.Read(db,"quest")
            assert(mode=="unsupported" and detail.raw=="38")
            assert(detail.reason=="Currency units not explicitly verified")
            assert(db.moneyTracking==nil)
        ''')

    def test_verified_lifetime_progress_fills_without_repeated_read_side_effects(self):
        self.h.execute('''
            stats[333]=Coin(6,"Gold")
            local current,goal,label=M.Progress(db,"gold100")
            assert(current==goal and goal==50000 and label=="6g / 5g")
            for i=1,10 do M.Progress(db,"gold100") end
            local value,mode=M.Read(db,"loot")
            assert(value==60000 and mode=="lifetime" and db.moneyTracking==nil)
        ''')

    def test_customized_thresholds_update_clean_descriptions_and_progress_together(self):
        self.h.execute('''
            assert(M.Configure("gold5000",750000))
            assert(M.Description("gold5000")=="Loot 75g.")
            M.Sync(db); M.ObserveLoot(db,"You loot 1 Gold.",20)
            local current,goal,label=M.Progress(db,"gold5000")
            assert(current==10000 and goal==750000 and label=="1g / 75g")
            assert(db.done.gold5000==12345 and db.money==38)
        ''')


class Iteration5DefaultLayoutTests(unittest.TestCase):
    def test_new_and_invalid_preferences_use_large_without_rewriting_saved_choices(self):
        h = Harness(controller=True)
        h.execute('''
            local c=ns.LegacyUIController
            assert(settings.legacyUISize==nil and c:Preset()=="Large")
            settings.legacyUISize="Invalid"
            assert(c:Preset()=="Large" and settings.legacyUISize=="Invalid")
            settings.legacyUISize="Standard"
            local name,size=c:Preset()
            assert(name=="Standard" and size[1]==900 and size[2]==620)
            settings.legacyUISize="Compact"
            assert(c:Preset()=="Compact" and settings.legacyUISize=="Compact")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep")
        ''')

    def test_first_open_uses_large_and_still_fits_a_smaller_screen(self):
        h = Harness(controller=True)
        h.execute('UIParent:SetSize(800,600)')
        h.enable()
        h.execute('''
            local c=ns.LegacyUIController
            assert(c.cover:GetWidth()==1024 and c.cover:GetHeight()==860)
            assert(c.ui.root:GetWidth()==1024 and c.ui.root:GetHeight()==720)
            assert(c.cover:GetScale()<1 and c.cover:IsVisible())
            assert(c.cover:GetWidth()*c.cover:GetScale()<=780)
            assert(c.cover:GetHeight()*c.cover:GetScale()<=580)
            assert(settings.legacyUISize==nil and saved.done.first==1730000000 and #calls==0)
        ''')
