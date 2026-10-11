"""Optional bounded aggregates cannot change behavior or require a valid clock."""
import unittest

from test_legacy_wrath_ui import Harness


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.load("Integrations/Performance.lua")

    def check(self, code):
        self.h.execute(code)

    def test_default_off_paths_never_read_clocks_or_modify_progress(self):
        self.check('''
            local clockCalls=0
            debugprofilestop=function() clockCalls=clockCalls+1;error("must stay cold") end
            GetTime=function() clockCalls=clockCalls+1;error("must stay cold") end
            assert(not ns.LegacyPerf.IsEnabled())
            assert(ns.LegacyPerf.Begin("Open")==nil)
            assert(not ns.LegacyPerf.Count("Rows",200))
            assert(not ns.LegacyPerf.Finish({}))
            local s=ns.LegacyPerf.Report()
            assert(not s.enabled and s.names==0 and next(s.timings)==nil and next(s.counters)==nil)
            assert(clockCalls==0 and saved.done.first==1730000000 and saved.history[1]=="keep")
            assert(next(settings)==nil and #calls==0)
        ''')

    def test_profile_clock_aggregates_milliseconds_and_tokens_are_single_use(self):
        self.check('''
            local profile=100
            debugprofilestop=function() return profile end
            GetTime=function() error("profile available") end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Open")
            assert(type(token)=="table" and next(token)==nil)
            profile=112.5
            assert(ns.LegacyPerf.Finish(token))
            assert(not ns.LegacyPerf.Finish(token))
            token=ns.LegacyPerf.Begin("Open");profile=120
            ns.LegacyPerf.Finish(token)
            local row=ns.LegacyPerf.Snapshot().timings.Open
            assert(row.calls==2 and row.measured==2 and row.total==20 and row.max==12.5 and row.last==7.5)
            assert(ns.LegacyPerf.Count("Rows",3) and ns.LegacyPerf.Count("Rows"))
            assert(ns.LegacyPerf.Snapshot().counters.Rows==4)
        ''')

    def test_fallback_game_clock_converts_seconds_to_milliseconds(self):
        self.check('''
            debugprofilestop=nil
            local clock=5
            GetTime=function() return clock end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Render")
            clock=5.125;ns.LegacyPerf.Finish(token)
            local row=ns.LegacyPerf.Snapshot().timings.Render
            assert(row.last==125 and row.total==125 and row.measured==1)
        ''')

    def test_broken_profile_clock_falls_back_and_missing_clocks_leave_count_known(self):
        self.check('''
            local clock=10
            debugprofilestop=function() error("unavailable profiling") end
            GetTime=function() return clock end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Summary")
            clock=10.25;assert(ns.LegacyPerf.Finish(token))
            assert(ns.LegacyPerf.Snapshot().timings.Summary.last==250)
            GetTime=nil
            token=ns.LegacyPerf.Begin("NoClock")
            assert(token and ns.LegacyPerf.Finish(token))
            local s=ns.LegacyPerf.Snapshot()
            assert(s.timings.NoClock.calls==1 and s.timings.NoClock.measured==0 and s.timings.NoClock.last==nil)
            assert(s.clockUnavailable==1)
            ns.LegacyPerf.Report()
            assert(#messages>0 and #calls==0)
        ''')

    def test_clock_failures_mid_operation_do_not_mix_clock_domains(self):
        self.check('''
            local clock=100
            debugprofilestop=function() return clock end
            GetTime=function() return 9000 end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Tab")
            debugprofilestop=nil
            assert(ns.LegacyPerf.Finish(token))
            local s=ns.LegacyPerf.Snapshot()
            assert(s.timings.Tab.calls==1 and s.timings.Tab.measured==0 and s.timings.Tab.last==nil)
            assert(s.clockUnavailable==1)
        ''')

    def test_secret_and_nonfinite_clock_samples_cannot_fail_the_caller(self):
        self.check('''
            local hidden={}
            issecretvalue=function(v) return v==hidden end
            debugprofilestop=function() return hidden end
            GetTime=function() return 0/0 end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Unknown")
            assert(ns.LegacyPerf.Finish(token))
            assert(ns.LegacyPerf.Snapshot().timings.Unknown.measured==0)
            debugprofilestop=function() return math.huge end
            GetTime=function() return -1 end
            token=ns.LegacyPerf.Begin("Invalid")
            assert(ns.LegacyPerf.Finish(token))
            assert(ns.LegacyPerf.Snapshot().timings.Invalid.measured==0)
            assert(not ns.LegacyPerf.Count("Unsafe",hidden))
            assert(ns.LegacyPerf.Begin(hidden)==nil)
            assert(not ns.LegacyPerf.Finish(hidden))
            assert(#calls==0)
        ''')

    def test_reversed_clock_is_unavailable_while_real_zero_duration_is_valid(self):
        self.check('''
            local clock=100
            debugprofilestop=function() return clock end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Zero")
            ns.LegacyPerf.Finish(token)
            local row=ns.LegacyPerf.Snapshot().timings.Zero
            assert(row.measured==1 and row.last==0 and row.total==0)
            token=ns.LegacyPerf.Begin("ResetClock");clock=99
            ns.LegacyPerf.Finish(token)
            row=ns.LegacyPerf.Snapshot().timings.ResetClock
            assert(row.calls==1 and row.measured==0 and row.last==nil)
        ''')

    def test_named_metrics_and_unfinished_tokens_have_fixed_bounds(self):
        self.check('''
            debugprofilestop=function() return 100 end
            ns.LegacyPerf.Enable(true)
            local cap=ns.LegacyPerf.Snapshot().limits.names
            for i=1,cap+25 do ns.LegacyPerf.Count("Rows"..i) end
            local s=ns.LegacyPerf.Snapshot()
            local count=0;for _ in pairs(s.counters) do count=count+1 end
            assert(count==cap and s.names==cap and s.droppedNames==25)
            ns.LegacyPerf.Reset()
            local retained={}
            cap=ns.LegacyPerf.Snapshot().limits.tokens
            for i=1,cap+20 do retained[i]=ns.LegacyPerf.Begin("Outstanding") end
            for i=1,20 do assert(not ns.LegacyPerf.Finish(retained[i])) end
            for i=21,#retained do assert(ns.LegacyPerf.Finish(retained[i])) end
            s=ns.LegacyPerf.Snapshot()
            assert(s.droppedTokens==20 and s.timings.Outstanding.calls==cap)
            assert(s.names==1 and #calls==0)
        ''')

    def test_invalid_names_amounts_and_saturation_remain_bounded(self):
        self.check('''
            ns.LegacyPerf.Enable(true)
            for _,value in ipairs({{},false,12,"",string.rep("x",65),"bad\\nname"}) do
                assert(ns.LegacyPerf.Begin(value)==nil)
            end
            for _,amount in ipairs({{},false,"1",-1,math.huge,0/0}) do assert(not ns.LegacyPerf.Count("Rows",amount)) end
            local cap=ns.LegacyPerf.Snapshot().limits.value
            assert(ns.LegacyPerf.Count("Rows",cap) and ns.LegacyPerf.Count("Rows",cap))
            assert(ns.LegacyPerf.Snapshot().counters.Rows==cap)
            assert(ns.LegacyPerf.Snapshot().names==1)
        ''')

    def test_reset_disable_and_reenable_invalidate_pending_tokens(self):
        self.check('''
            local clockReads=0
            debugprofilestop=function() clockReads=clockReads+1;return 100 end
            ns.LegacyPerf.Enable(true)
            local token=ns.LegacyPerf.Begin("Old")
            ns.LegacyPerf.Reset()
            assert(not ns.LegacyPerf.Finish(token))
            assert(ns.LegacyPerf.Count("Rows",5))
            token=ns.LegacyPerf.Begin("BeforeOff")
            ns.LegacyPerf.Enable(false)
            local before=clockReads
            assert(not ns.LegacyPerf.Finish(token) and ns.LegacyPerf.Begin("Disabled")==nil)
            assert(not ns.LegacyPerf.Count("Disabled") and clockReads==before)
            assert(ns.LegacyPerf.Snapshot().counters.Rows==5)
            ns.LegacyPerf.Enable(true)
            assert(ns.LegacyPerf.Snapshot().names==0 and not ns.LegacyPerf.Finish(token))
        ''')

    def test_report_returns_copy_and_prints_only_aggregate_lines(self):
        self.check('''
            debugprofilestop=function() return 10 end
            ns.LegacyPerf.Enable(true)
            for i=1,100 do
                local token=ns.LegacyPerf.Begin("Render");ns.LegacyPerf.Finish(token)
                ns.LegacyPerf.Count("Render")
            end
            local before=#messages
            local report=ns.LegacyPerf.Report()
            assert(#messages-before==2)
            report.timings.Render.calls=999;report.counters.Render=999
            assert(ns.LegacyPerf.Snapshot().timings.Render.calls==100)
            assert(ns.LegacyPerf.Snapshot().counters.Render==100)
            print=function() error("chat unavailable") end
            assert(ns.LegacyPerf.Report().timings.Render.calls==100)
        ''')

    def test_slash_registry_changes_session_diagnostics_only(self):
        self.check('''
            assert(type(ns.LAR.SLASH.perf)=="function")
            ns.LAR.SLASH.perf("ON")
            assert(ns.LegacyPerf.IsEnabled())
            ns.LegacyPerf.Count("Rows",5)
            ns.LAR.SLASH.perf("report")
            ns.LAR.SLASH.perf("off")
            assert(not ns.LegacyPerf.IsEnabled() and ns.LegacyPerf.Snapshot().counters.Rows==5)
            ns.LAR.SLASH.perf("reset")
            assert(ns.LegacyPerf.Snapshot().names==0)
            ns.LAR.SLASH.perf("unsupported")
            assert(saved.done.first==1730000000 and saved.history[1]=="keep")
            assert(next(settings)==nil and #calls==0)
            assert(#messages<10)
        ''')


if __name__ == "__main__":
    unittest.main()
