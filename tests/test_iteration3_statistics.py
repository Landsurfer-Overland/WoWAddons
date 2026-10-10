#!/usr/bin/env python3
"""Read-only subject statistics, confirmed zeroes and unavailable values."""
import unittest

from test_legacy_wrath_ui import Harness


class StatisticsAdapterTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.load("Integrations/StatisticsAdapter.lua")

    def check(self, code):
        self.h.execute(code)

    def test_native_zero_placeholders_and_errors_are_distinct(self):
        self.check('''
            ns.STATS={{title="COMBAT",list={{197,"Damage"},{198,"Healing"},{193,"Largest hit"},{189,"Largest heal"}}}}
            GetStatistic=function(id)
                if id==197 then return "0" end
                if id==198 then return "--" end
                if id==193 then error("temporarily unavailable") end
                return nil
            end
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:native:197"].value=="0" and m.byKey["statistic:native:197"].available)
            for _,id in ipairs({198,193,189}) do
                local row=m.byKey["statistic:native:"..id]
                assert(row.value=="Unavailable" and not row.available)
            end
            assert(m.byCategory["stats:combat/damage"] and m.byCategory["stats:combat/healing"])
            assert(#ns.StatisticsAdapter.Rows(m,"stats:combat")==6) -- includes tracked pests/rares
            assert(#calls==0)
        ''')

    def test_missing_statistic_function_never_uses_alpha_placeholder(self):
        self.check('''
            GetStatistic=nil
            ns.FA.StatText=function() error("do not substitute an alpha statistic") end
            ns.STATS={{title="QUESTS",list={{98,"Quests completed"}}}}
            local m=ns.StatisticsAdapter.Catalog()
            local row=m.byKey["statistic:native:98"]
            assert(row.value=="Unavailable" and not row.available)
        ''')

    def test_secret_values_and_formatted_placeholders_are_unavailable(self):
        self.check('''
            local hidden={}
            issecretvalue=function(value) return value==hidden end
            ns.STATS={{title="CHARACTER",list={{1,"Hidden"},{2,"Missing"},{3,"Name"},{4,"Amount"}}}}
            GetStatistic=function(id)
                if id==1 then return hidden end
                if id==2 then return " |cffffffff--|r " end
                if id==3 then return "Heavy Runecloth Bandage" end
                return "1|TInterface\\\\MoneyFrame\\\\UI-GoldIcon:0|t"
            end
            local m=ns.StatisticsAdapter.Catalog()
            assert(not m.byKey["statistic:native:1"].available)
            assert(not m.byKey["statistic:native:2"].available)
            assert(m.byKey["statistic:native:3"].value=="Heavy Runecloth Bandage")
            assert(m.byKey["statistic:native:4"].value:find("UI-GoldIcon",1,true))
        ''')

    def test_initialized_collections_zero_but_absent_counters_unknown(self):
        self.check('''
            saved.critters={}; saved.pests={a=true}; saved.books={book=true}
            saved.foods={}; saved.drinks={}; saved.rares={}; saved.bosses={}
            saved.fishedIn={}; saved.rareFish={}; saved.fished=nil; saved.explored=nil
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:tracked:critters"].value=="0")
            assert(m.byKey["statistic:tracked:pests"].value=="1")
            assert(m.byKey["statistic:tracked:books"].value=="1")
            assert(m.byKey["statistic:tracked:fishedIn"].value=="0")
            assert(not m.byKey["statistic:tracked:fished"].available)
            assert(not m.byKey["statistic:tracked:explored"].available)
            saved.fished=0
            assert(ns.StatisticsAdapter.Catalog().byKey["statistic:tracked:fished"].value=="0")
        ''')

    def test_existing_db_is_read_without_accessor_or_account_merge(self):
        self.check('''
            ForeverAchievementsCharDB=saved
            saved.critters={}; saved.fished=4
            ns.FA.DB=function() error("statistics must not initialize state") end
            ns.FA.Account=function() error("statistics must not merge account data") end
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:tracked:fished"].value=="4")
            assert(saved.fished==4 and saved.done.first==1730000000 and saved.history[1]=="keep")
            assert(saved.pests==nil and saved.books==nil)
            assert(#calls==0)
        ''')

    def test_collection_count_failures_do_not_become_zero(self):
        self.check('''
            saved.critters={}
            ns.FA.Count=function() error("counter failed") end
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:tracked:critters"].value=="Unavailable")
            assert(not m.byKey["statistic:tracked:critters"].available)
        ''')

    def test_secondary_professions_use_ids_with_parent_aggregation(self):
        self.check('''
            ns.STATS={{title="SKILLS / SECONDARY SKILLS",list={
                {1519,"Mislabeled Cooking"},{1524,"Mislabeled Fishing"},{281,"First Aid skill"},
                {1745,"Cooking recipes"},{1748,"First Aid manuals"},{1518,"Fish caught"}}}}
            GetStatistic=function() return "0" end
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:native:1519"].category=="stats:professions/fishing")
            assert(m.byKey["statistic:native:1524"].category=="stats:professions/cooking")
            assert(#ns.StatisticsAdapter.Rows(m,"stats:professions/cooking")==2)
            assert(#ns.StatisticsAdapter.Rows(m,"stats:professions/firstaid")==2)
            assert(#ns.StatisticsAdapter.Rows(m,"stats:professions")==9)
            local seen={}
            for _,row in ipairs(ns.StatisticsAdapter.Rows(m,"stats:professions")) do
                assert(not seen[row.key]);seen[row.key]=true
            end
        ''')

    def test_sections_have_precedence_over_ambiguous_titles(self):
        self.check('''
            ns.STATS={{title="CHARACTER / CONSUMABLES",list={{99001,"Fishing Damage"}}},
                {title="KILLS / HONORABLE KILLS",list={{99002,"Healing"}}},
                {title="DUNGEONS & RAIDS / BOSS KILLS",list={{99003,"Character"}}}}
            GetStatistic=function() return "0" end
            local m=ns.StatisticsAdapter.Catalog()
            assert(m.byKey["statistic:native:99001"].category=="stats:character/consumables")
            assert(m.byKey["statistic:native:99002"].category=="stats:pvp")
            assert(m.byKey["statistic:native:99003"].category=="stats:dungeons")
        ''')

    def test_daily_stats_omitted_but_average_ordinary_quests_retained(self):
        self.check('''
            ns.STATS={{title="QUESTS",list={{97,"Daily quests"},{95,"Average quests completed per day"},{98,"Quests completed"}}},
                {title="SKILLS / SECONDARY SKILLS",list={{1525,"Cooking daily quests completed"},
                    {1526,"Fishing daily quests completed"},{1976,"Dalaran Cooking Awards gained"},{1524,"Cooking skill"}}}}
            GetStatistic=function(id)
                assert(id~=97 and id~=1525 and id~=1526 and id~=1976)
                return "0"
            end
            local m=ns.StatisticsAdapter.Catalog()
            for _,id in ipairs({97,1525,1526,1976}) do
                assert(m.byKey["statistic:native:"..id]==nil and m.omitted[id])
            end
            assert(m.byKey["statistic:native:95"] and m.byKey["statistic:native:98"])
            assert(#ns.STATS[1].list==3 and #ns.STATS[2].list==4)
        ''')

    def test_duplicates_are_fetched_once_and_categories_are_populated_only(self):
        self.check('''
            local fetched=0
            ns.STATS={{title="QUESTS",list={{98,"Quests completed"},{98,"Accidental copy"}}}}
            GetStatistic=function() fetched=fetched+1;return "0" end
            local m=ns.StatisticsAdapter.Catalog()
            assert(#ns.StatisticsAdapter.Rows(m,"stats:quests")==1)
            assert(not m.byCategory["stats:professions/firstaid"])
            assert(not m.byCategory["stats:professions/cooking"])
            assert(not m.byCategory["stats:character/general"])
            for _,cat in ipairs(m.categories) do
                assert(cat.key=="stats:summary" or #cat.rows+#cat.children>0)
            end
            assert(fetched==1)
        ''')

    def test_recorded_exploration_deduplicates_old_and_new_zone_keys(self):
        self.check('''
            ns.EXPLORE={{id=777,key="explore777"}}
            saved.explored={[777]={Town=true},explore777={Town=true,Road=true},other={Town=true}}
            local row=ns.StatisticsAdapter.Catalog().byKey["statistic:tracked:explored"]
            assert(row.available and row.value=="3")
            assert(saved.explored[777].Town and saved.explored.explore777.Road)
        ''')

    def test_full_existing_stat_catalog_keeps_supported_definitions(self):
        self.h.load("DataExtra.lua")
        self.check('''
            GetStatistic=function(id) return id==344 and "--" or "0" end
            local original=0
            for _,section in ipairs(ns.STATS) do original=original+#section.list end
            local m=ns.StatisticsAdapter.Catalog()
            local native=0
            for _,row in ipairs(m.rows) do if row.source=="native_statistic" then native=native+1 end end
            assert(native==original-3)
            assert(m.byKey["statistic:native:95"].available)
            assert(not m.byKey["statistic:native:344"].available)
            assert(m.byCategory["stats:character/progression"] and m.byCategory["stats:combat/healing"])
            assert(m.byCategory["stats:professions/fishing"] and m.byCategory["stats:professions/firstaid"])
            assert(ns.StatisticsAdapter==ns.LegacyStatistics)
            assert(ns.StatisticsAdapter.Rows(m,"summary")==m.rows)
            assert(#ns.StatisticsAdapter.Rows(m,"missing")==0 and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
