"""Copper normalization, source provenance and event-level money regressions.

These use Lua 5.1 and actual addon code. They do not establish that Forever's
live statistics expose the same IDs, labels or currency texture strings.
"""
import unittest

from test_legacy_wrath_ui import ADDON, LuaRuntime
from test_progression_addendum import CoreHarness


class MoneyHarness:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            ns={}; db={money=38,done={gold5000=12345},history={"keep"}}
            ForeverAchievementsDB={}; clock=123
            time=function() return clock end
            SecretValue={}; issecretvalue=function(v) return v==SecretValue end
            titles={[333]="Gold looted",[326]="Gold from quest rewards"}
            stats={}; reads={}; infoReads={}
            GetAchievementInfo=function(id)
                infoReads[id]=(infoReads[id] or 0)+1
                return id,titles[id],0,false,nil,nil,nil,"",0
            end
            GetStatistic=function(id) reads[id]=(reads[id] or 0)+1; return stats[id] end
            function Coin(n,unit) return n.."|TInterface\\\\MoneyFrame\\\\UI-"..unit.."Icon:0|t" end
        ''')
        self.lua.execute('assert(loadstring(...))("ForeverAchievements",ns)', (ADDON / "MoneyTracking.lua").read_text())
        self.lua.execute('M=ns.MoneyTracking')

    def execute(self, code):
        self.lua.execute(code)
        self.lua.execute('assert(db.money==38 and db.done.gold5000==12345 and db.history[1]=="keep")')


class MoneyTrackingTests(unittest.TestCase):
    def setUp(self):
        self.h = MoneyHarness()

    def check(self, code):
        self.h.execute(code)

    def test_explicit_coin_textures_normalize_gold_silver_and_copper(self):
        self.check('''
            assert(M.ParseCoins(Coin(2,"Gold").." "..Coin(3,"Silver").." "..Coin(4,"Copper"))==20304)
            assert(M.ParseCoins(Coin("1,234","Gold"))==12340000)
            assert(M.ParseCoins(Coin("1.234","Gold"))==12340000)
            assert(M.ParseCoins(Coin("1 234","Gold"))==12340000)
            assert(M.ParseCoins("|cffffffff"..Coin(0,"Copper").."|r")==0)
            assert(M.Format(20304)=="2g 3s 4c" and M.Format(38)=="38c")
            assert(M.Format(0)=="0c" and M.Format(10000)=="1g")
        ''')

    def test_plain_statistics_and_non_currency_icons_remain_unknown(self):
        self.check('''
            for _,v in ipairs({"38","38%","--","1/2",Coin(2,"Honor"),Coin("38.5","Gold"),"-"..Coin(1,"Gold")}) do
                assert(M.ParseCoins(v)==nil)
            end
            assert(M.ParseCoins(38)==nil and M.ParseCoins(SecretValue)==nil)
            assert(M.ParseCoins(Coin(1,"Gold").." 9 victories")==nil)
        ''')

    def test_localized_loot_uses_literal_labels_and_format_strings(self):
        self.check('''
            assert(M.ParseLoot("You loot 1 Gold, 2 Silver, 3 Copper.")==10203)
            GOLD="Or (pièces)"; SILVER="Argent+"; COPPER="Cuivre."
            assert(M.ParseLoot("Vous recevez 2 Or (pièces), 3 Argent+, 4 Cuivre.")==20304)
            GOLD_AMOUNT="%d Or"; SILVER_AMOUNT="%d Argent"; COPPER_AMOUNT="%d Cuivre"
            assert(M.ParseLoot("Votre part: 1 234 Or, 56 Argent, 7 Cuivre")==12345607)
            assert(M.ParseLoot("Your share: "..Coin(1,"Gold").." "..Coin(7,"Copper"))==10007)
            assert(M.ParseLoot("You loot 38 tokens")==nil)
        ''')

    def test_verified_lifetime_requires_correct_statistic_identity_and_units(self):
        self.check('''
            stats[333]=Coin(7,"Gold"); stats[326]=Coin(8,"Gold")
            local value,mode=M.Read(db,"loot"); assert(value==70000 and mode=="lifetime")
            value,mode=M.Read(db,"quest"); assert(value==80000 and mode=="lifetime")
            titles[333]="Victories"; titles[326]="Current money"
            assert(M.Read(db,"loot")==nil and M.Read(db,"quest")==nil)
            titles[333]="Gold looted"; stats[333]="38"
            assert(M.Read(db,"loot")==nil)
        ''')

    def test_unavailable_lifetime_quest_progress_is_nil_with_explicit_units(self):
        self.check('''
            stats[326]="38"
            local cur,need,quantity=M.Progress(db,"breadwinner")
            assert(cur==nil and need==1000000 and quantity=="Unavailable / 100g (tracking unavailable)")
            GetStatistic=function() error("Unavailable") end
            assert(M.Progress(db,"breadwinner")==nil)
            GetAchievementInfo=function() error("Unavailable") end
            assert(M.Progress(db,"breadwinner")==nil)
        ''')

    def test_account_wide_native_statistic_cannot_award_character_money(self):
        self.check('''
            GetAchievementInfo=function(id) return id,titles[id],0,false,nil,nil,nil,"",131072 end
            stats[333]=Coin(1000,"Gold"); stats[326]=Coin(1000,"Gold")
            assert(M.Read(db,"quest")==nil and M.Read(db,"loot")==nil)
            M.Sync(db); assert(M.Read(db,"loot")==0)
            local cur,mode,detail=M.Read(db,"quest")
            assert(cur==nil and mode=="unsupported" and detail.reason:find("Account-wide",1,true))
            GetAchievementInfo=function(id) return id,titles[id],0,false,nil,nil,nil,"",SecretValue end
            assert(M.Read(db,"quest")==nil)
        ''')

    def test_missing_or_malformed_scope_flags_do_not_verify_lifetime_money(self):
        self.check('''
            stats[333]=Coin(1000,"Gold"); stats[326]=Coin(1000,"Gold")
            for _,badFlag in ipairs({false,-1,"0",0/0,SecretValue}) do
                GetAchievementInfo=function(id) return id,titles[id],0,false,nil,nil,nil,"",badFlag end
                assert(M.Read(db,"loot")==nil and M.Read(db,"quest")==nil)
            end
            GetAchievementInfo=function(id) return id,titles[id],0,false,nil,nil,nil,"",nil end
            local cur,mode,detail=M.Read(db,"quest")
            assert(cur==nil and mode=="unsupported" and detail.reason=="Statistic completion scope unavailable")
            GetAchievementInfo=function(id) return id,titles[id],0,false,nil,nil,nil,"",0 end
            assert(M.Read(db,"loot")==10000000 and M.Read(db,"quest")==10000000)
        ''')

    def test_login_sync_ui_reads_and_reload_never_add_earnings(self):
        self.check('''
            stats[333]="38"
            for i=1,5 do assert(M.Sync(db)); M.Progress(db,"gold5000") end
            assert(db.moneyTracking.observedLootCopper==0 and db.moneyTracking.startedAt==123)
            assert(M.ObserveLoot(db,"You loot 2 Silver.",77))
            for i=1,5 do M.Sync(db); M.Progress(db,"gold100") end
            assert(db.moneyTracking.observedLootCopper==200)
        ''')

    def test_observed_loot_and_lifetime_sync_are_not_added_together(self):
        self.check('''
            stats[333]=Coin(10,"Gold"); M.Sync(db)
            assert(M.ObserveLoot(db,"You loot 1 Gold.",100))
            assert(M.Read(db,"loot")==100000)
            stats[333]=Coin(11,"Gold"); M.Sync(db)
            assert(M.Read(db,"loot")==110000 and db.moneyTracking.observedLootCopper==10000)
            M.Sync(db); M.Sync(db); assert(M.Read(db,"loot")==110000)
        ''')

    def test_message_ids_deduplicate_dispatch_without_discarding_identical_loot(self):
        self.check('''
            assert(M.ObserveLoot(db,"You loot 1 Silver.",11))
            assert(not M.ObserveLoot(db,"You loot 1 Silver.",11))
            assert(M.ObserveLoot(db,"You loot 1 Silver.",12))
            assert(M.ObserveLoot(db,"You loot 1 Silver."))
            assert(M.ObserveLoot(db,"You loot 1 Silver."))
            assert(db.moneyTracking.observedLootCopper==400)
            assert(not M.ObserveLoot(db,"No money",13))
        ''')

    def test_corrupt_observation_state_is_preserved_without_becoming_completion(self):
        self.check('''
            local broken={version=1,unit="gold",observedLootCopper=999999999}
            db.moneyTracking=broken
            assert(not M.Sync(db) and not M.ObserveLoot(db,"You loot 1 Gold."))
            assert(M.Read(db,"loot")==nil and db.moneyTracking==broken and broken.unit=="gold")
        ''')

    def test_scope_failure_preserves_all_character_storage(self):
        self.check('''
            ns.FA={CharacterScope=function(d) assert(d==db); return nil,"Identity unavailable" end}
            stats[333]=Coin(100,"Gold")
            assert(not M.Sync(db) and not M.ObserveLoot(db,"You loot 5 Gold."))
            assert(M.Read(db,"loot")==nil and db.moneyTracking==nil)
        ''')

    def test_separate_characters_and_nested_snapshot_are_isolated(self):
        self.check('''
            local other={money=0,done={}}
            M.Sync(db); M.Sync(other); M.ObserveLoot(db,"You loot 2 Gold.")
            M.WithSnapshot(db,function()
                assert(M.Read(db,"loot")==20000)
                M.WithSnapshot(other,function() assert(M.Read(other,"loot")==0) end)
                assert(M.Read(db,"loot")==20000)
            end)
            assert(other.moneyTracking.observedLootCopper==0 and next(other.done)==nil)
        ''')

    def test_one_snapshot_shares_statistic_reads_and_next_pass_refreshes(self):
        self.check('''
            stats[333]=Coin(1,"Gold")
            M.WithSnapshot(db,function()
                M.Progress(db,"gold100"); M.Progress(db,"gold1000"); M.Progress(db,"gold5000")
                assert(reads[333]==1 and infoReads[333]==1)
                stats[333]=Coin(2,"Gold"); assert(M.Read(db,"loot")==10000)
            end)
            assert(M.Read(db,"loot")==20000 and reads[333]==2)
            local a,hole,z=M.WithSnapshot(db,function() return "a",nil,"z" end)
            assert(a=="a" and hole==nil and z=="z")
            assert(not pcall(M.WithSnapshot,db,function() error("Injected") end))
            stats[333]=Coin(3,"Gold"); assert(M.Read(db,"loot")==30000)
        ''')

    def test_unknown_snapshot_can_become_known_without_permanent_failure_cache(self):
        self.check('''
            GetStatistic=function(id) reads[id]=(reads[id] or 0)+1; error("Unavailable") end
            M.WithSnapshot(db,function()
                assert(M.Read(db,"quest")==nil and M.Read(db,"quest")==nil and reads[326]==1)
            end)
            GetStatistic=function() return Coin(9,"Gold") end
            assert(M.Read(db,"quest")==90000)
        ''')

    def test_configured_thresholds_are_copper_and_keep_ordered_tiers(self):
        self.check('''
            assert(M.Threshold("gold100")==50000 and M.Threshold("gold1000")==250000)
            assert(M.Threshold("gold5000")==1000000 and M.Threshold("breadwinner")==1000000)
            assert(M.Configure("gold5000",750000)); assert(M.Threshold("gold5000")==750000)
            assert(not M.Configure("gold5000",100000) and M.Threshold("gold5000")==750000)
            assert(not M.Configure("gold5000",0) and not M.Configure("gold5000",0/0))
            assert(not M.Configure("native:62013",1) and not M.Configure("breadwinner",SecretValue))
            assert(M.Description("gold5000"):find("75g",1,true))
        ''')

    def test_invalid_saved_thresholds_fail_back_without_rewriting_settings(self):
        self.check('''
            local bad={gold100=99999999,gold1000=2,gold5000=1}
            ForeverAchievementsDB.moneyConfig={thresholds=bad}
            assert(M.Threshold("gold100")==50000 and M.Threshold("gold5000")==1000000)
            assert(ForeverAchievementsDB.moneyConfig.thresholds==bad and bad.gold100==99999999)
            ForeverAchievementsDB.moneyConfig=SecretValue
            assert(not M.Configure("gold5000",750000) and ForeverAchievementsDB.moneyConfig==SecretValue)
            ForeverAchievementsDB.moneyConfig={thresholds=SecretValue}
            assert(not M.Configure("gold5000",750000) and ForeverAchievementsDB.moneyConfig.thresholds==SecretValue)
            ForeverAchievementsDB=false
            assert(not M.Configure("gold5000",750000) and ForeverAchievementsDB==false)
        ''')

    def test_localized_statistic_identity_requires_explicit_verified_name(self):
        self.check('''
            titles[326]="Or des récompenses de quête"; stats[326]=Coin(5,"Gold")
            assert(M.Read(db,"quest")==nil)
            ForeverAchievementsDB.moneyConfig={statisticNames={quest="Or des récompenses de quête"}}
            assert(M.Read(db,"quest")==50000)
            stats[326]="5"; assert(M.Read(db,"quest")==nil)
        ''')

    def test_diagnostics_identify_original_raw38_without_claiming_its_units(self):
        self.check('''
            stats[333]="38"; M.Sync(db)
            local lines=M.Report(db); local output=table.concat(lines,"\\n")
            assert(output:find('raw="38"',1,true) and output:find("source=since_tracking",1,true))
            assert(output:find("Currency units not explicitly verified",1,true))
            assert(output:find("Historical alpha money counter preserved: 38",1,true))
            local response,changed=M.Command(db,"threshold gold5000 750000")
            assert(changed and response[1]:find("75g",1,true))
            response,changed=M.Command(db,"report"); assert(not changed and #response>=7)
        ''')

    def test_oversized_secret_and_negative_inputs_do_not_mutate_state(self):
        self.check('''
            assert(not M.ObserveLoot(db,SecretValue))
            assert(not M.ObserveLoot(db,string.rep("1",3000).." Gold"))
            assert(not M.ObserveLoot(db,"You loot 0 Copper"))
            assert(not M.ObserveLoot(db,"You loot -5 Gold"))
            assert(M.ParseCoins(Coin("1000000000001","Copper"))==nil)
            assert(db.moneyTracking==nil)
        ''')


class ProductionMoneyHarness(CoreHarness):
    def load(self, path):
        if path == "ForeverAchievements.lua" and self.lua.eval("ns.MoneyTracking==nil"):
            super().load("MoneyTracking.lua")
        super().load(path)


class ProductionMoneyTests(unittest.TestCase):
    def test_actual_core_definitions_use_rebalanced_copper_and_explicit_unknown_quest(self):
        h = ProductionMoneyHarness()
        h.execute('''
            for key,need in pairs({gold100=50000,gold1000=250000,gold5000=1000000,breadwinner=1000000}) do
                local current,required,quantity=ns.FA.BY_KEY[key].progress()
                assert(required==need and type(quantity)=="string")
                assert(ns.FA.BY_KEY[key].money==true)
            end
            assert(ns.FA.BY_KEY.breadwinner.progress()==nil)
        ''')

    def test_actual_event_awards_only_new_observations_without_rewriting_history(self):
        h = ProductionMoneyHarness()
        h.execute('''
            SelectAchievements("gold100","gold1000","gold5000","breadwinner")
            saved.money=50000000; GetStatistic=function() return "38" end
            CoreEvent("PLAYER_ENTERING_WORLD"); FlushTimers()
            assert(saved.money==50000000 and not saved.done.gold100 and not saved.done.breadwinner)
            CoreEvent("CHAT_MSG_MONEY","You loot 5 Gold.")
            assert(saved.done.gold100 and not saved.done.gold1000 and not saved.done.breadwinner)
            local earned=saved.done.gold100; local observed=saved.moneyTracking.observedLootCopper
            CoreEvent("PLAYER_ENTERING_WORLD"); FlushTimers()
            ns.FA.CheckAll(); ns.FA.CheckAll()
            assert(saved.done.gold100==earned and saved.moneyTracking.observedLootCopper==observed)
            assert(saved.money==50000000 and saved.done.first==1730000000 and saved.history[1]=="keep")
        ''')

    def test_ledger_owner_blocks_known_foreign_or_copied_character_earnings(self):
        h = ProductionMoneyHarness()
        h.execute('''
            SelectAchievements("gold100","gold1000","gold5000")
            saved.money=38
            ns.MoneyTracking.Sync(saved)
            ns.MoneyTracking.ObserveLoot(saved,"You loot 1 Gold.")
            assert(saved.moneyTracking.observedLootCopper==10000 and saved.moneyTracking.ownerIdentity)
            assert(saved.trackingIdentity==nil)
            local ledger=saved.moneyTracking
            currentName="Other"; currentSurname="Different"
            CoreEvent("CHAT_MSG_MONEY","You loot 5 Gold.")
            assert(ledger.observedLootCopper==10000 and saved.moneyTracking==ledger)
            assert(ns.FA.BY_KEY.gold100.progress()==nil and not saved.done.gold100)
            assert(saved.money==38 and saved.done.first==1730000000 and saved.history[1]=="keep")
            saved.trackingIdentity=ledger.ownerIdentity
            CoreEvent("CHAT_MSG_MONEY","You loot 5 Gold.")
            assert(ledger.observedLootCopper==10000 and not saved.done.gold100)
        ''')


if __name__ == "__main__":
    unittest.main()
