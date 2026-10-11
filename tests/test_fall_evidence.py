"""Going Down? requires measured, character-local, safely survived fall evidence."""
import unittest

from test_progression_addendum import CoreHarness


class MeasuredFallTests(unittest.TestCase):
    def setUp(self):
        self.h = CoreHarness()
        self.h.execute('''
            SelectAchievements("fall")
            fallFrame=ForeverAchievementsFallTracker
            assert(fallFrame)
            testZ=120; testInstance=1; fallingValue=false; deadValue=false
            flyingValue=false; taxiValue=false; swimmingValue=false
            function UnitPosition() return 1,2,testZ,testInstance end
            function IsFalling() return fallingValue end
            function UnitIsDeadOrGhost() return deadValue end
            function IsFlying() return flyingValue end
            function UnitOnTaxi() return taxiValue end
            function IsSwimming() return swimmingValue end
            function TickFall(t,z,falling)
                testClock=t;testZ=z;fallingValue=falling
                fallFrame:Fire("OnUpdate",.1)
            end
            function LandMeasuredFall(z)
                TickFall(10,120,false)
                TickFall(10.1,119,true)
                TickFall(10.2,80,true)
                TickFall(10.3,z,false)
            end
        ''')

    def test_measured_sixty_five_yards_requires_delayed_safe_confirmation(self):
        self.h.execute('''
            local originalAfter=C_Timer.After
            C_Timer.After=function(delay,fn) assert(delay==.5);originalAfter(delay,fn) end
            LandMeasuredFall(55)
            C_Timer.After=originalAfter
            assert(saved.done.fall==nil and saved.fallEvidence==nil)
            assert(#timers==1)
            testClock=10.8;FlushTimers()
            assert(saved.done.fall and saved.fall==true)
            local proof=saved.fallEvidence
            assert(proof.kind=="measured-fall" and proof.verified==true and proof.drop==65)
            assert(proof.startZ==120 and proof.landingZ==55 and proof.confirmedZ==55 and proof.instanceID==1)
            assert(proof.survived and proof.dead==false and proof.falling==false)
            assert(proof.flying==false and proof.taxi==false and proof.swimming==false)
            assert(saved.done.first==1730000000 and saved.history[1]=="keep" and #calls==0)
        ''')

    def test_less_than_sixty_five_yards_does_not_award(self):
        self.h.execute('''
            LandMeasuredFall(55.1);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
        ''')

    def test_airborne_login_without_grounded_baseline_does_not_award(self):
        self.h.execute('''
            TickFall(10,120,true);TickFall(10.1,80,true);TickFall(10.2,0,false)
            FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
        ''')

    def test_delayed_confirmation_rejects_death_unknown_and_new_fall(self):
        for change in ("deadValue=true", "deadValue=nil", "fallingValue=true", "fallingValue=nil",
                       "flyingValue=true", "taxiValue=true", "swimmingValue=true", "testInstance=2"):
            with self.subTest(change=change):
                self.setUp()
                self.h.execute('''
                    LandMeasuredFall(40)
                    assert(#timers==1)
                ''' + change + '''
                    testClock=10.8;FlushTimers()
                    assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
                ''')

    def test_status_interruptions_invalidate_the_whole_fall(self):
        for change in ("deadValue=true", "flyingValue=true", "taxiValue=true", "swimmingValue=true",
                       "deadValue=nil", "flyingValue=nil", "taxiValue=nil", "swimmingValue=nil"):
            with self.subTest(change=change):
                self.setUp()
                self.h.execute('''
                    TickFall(10,120,false);TickFall(10.1,119,true)
                ''' + change + '''
                    TickFall(10.2,80,true)
                    deadValue=false;flyingValue=false;taxiValue=false;swimmingValue=false
                    TickFall(10.3,0,false);FlushTimers()
                    assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
                ''')

    def test_missing_apis_cannot_produce_an_award(self):
        for api in ("UnitPosition", "GetTime", "IsFalling", "UnitIsDeadOrGhost", "IsFlying", "UnitOnTaxi", "IsSwimming"):
            with self.subTest(api=api):
                self.setUp()
                self.h.execute(api + '''=nil
                    LandMeasuredFall(0);FlushTimers()
                    assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
                ''')

    def test_invalid_coordinates_and_instance_identifiers_invalidate_measurement(self):
        for change in ("testZ=nil", "testZ=math.huge", "testZ=0/0", "testInstance=nil", "testInstance=1.5",
                       "UnitPosition=function() error('Restricted coordinate') end"):
            with self.subTest(change=change):
                self.setUp()
                self.h.execute('''
                    TickFall(10,120,false);TickFall(10.1,119,true)
                ''' + change + '''
                    testClock=10.2;fallingValue=true;fallFrame:Fire("OnUpdate",.1)
                    testZ=0;testInstance=1;fallingValue=false;testClock=10.3
                    fallFrame:Fire("OnUpdate",.1);FlushTimers()
                    assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
                ''')

    def test_secret_coordinates_and_status_values_are_unknown(self):
        self.h.execute('''
            SecretTestValue=setmetatable({}, {__tostring=function() error("Secret coordinate conversion") end})
            TickFall(10,120,false)
            TickFall(10.1,SecretTestValue,true)
            TickFall(10.2,0,false);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
            TickFall(20,120,false);TickFall(20.1,119,true)
            deadValue=SecretTestValue
            TickFall(20.2,80,true)
            deadValue=false
            TickFall(20.3,0,false);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
        ''')

    def test_instance_change_and_world_transition_reset_pending_evidence(self):
        for event in ("PLAYER_ENTERING_WORLD", "PLAYER_LEAVING_WORLD", "LOADING_SCREEN_ENABLED", "PLAYER_DEAD"):
            with self.subTest(event=event):
                self.setUp()
                self.h.execute('''
                    LandMeasuredFall(0)
                    assert(#timers==1)
                    CoreEvent("''' + event + '''")
                    testClock=10.8;FlushTimers()
                    assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
                ''')
        self.setUp()
        self.h.execute('''
            TickFall(10,120,false);TickFall(10.1,119,true)
            testInstance=2;TickFall(10.2,80,true);TickFall(10.3,0,false);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
        ''')

    def test_character_state_switch_invalidates_a_pending_fall(self):
        self.h.execute('''
            LandMeasuredFall(40)
            local old=ForeverAchievementsCharDB
            ForeverAchievementsCharDB={done={},tracked={},history={"other character"}}
            testClock=10.8;FlushTimers()
            assert(ForeverAchievementsCharDB.done.fall==nil and ForeverAchievementsCharDB.fallEvidence==nil)
            assert(old.done.fall==nil and old.fallEvidence==nil)
            assert(old.done.first==1730000000 and old.history[1]=="keep" and #calls==0)
        ''')

    def test_clock_reversal_and_overflow_are_not_trusted_evidence(self):
        self.h.execute('''
            TickFall(10,120,false);TickFall(10.1,119,true)
            TickFall(9,80,true);TickFall(11,0,false);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
            TickFall(20,1e308,false);TickFall(21,1e308,true)
            TickFall(22,-1e308,false);FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and not saved.fall)
        ''')

    def test_existing_genuine_completion_is_never_overwritten(self):
        self.h.execute('''
            saved.done.fall=444444;saved.fall=true
            saved.fallEvidence={kind="previous evidence",note="preserve"}
            local existing=saved.fallEvidence
            LandMeasuredFall(40);testClock=10.8;FlushTimers()
            assert(saved.done.fall==444444 and saved.fall and saved.fallEvidence==existing)
            assert(saved.history[1]=="keep" and #calls==0)
        ''')

    def test_completed_ticks_skip_sample_apis_and_resume_with_fresh_baseline(self):
        self.h.execute('''
            saved.done.fall=444444; saved.fall=true
            local evidence={kind="existing evidence"}; saved.fallEvidence=evidence
            local reads=0
            for _,name in ipairs({"UnitPosition","GetTime","IsFalling","UnitIsDeadOrGhost","IsFlying","UnitOnTaxi","IsSwimming"}) do
                local original=_G[name]
                _G[name]=function(...) reads=reads+1; return original(...) end
            end
            for i=1,100 do TickFall(10+i*.001,120,false) end
            assert(reads==0 and saved.done.fall==444444 and saved.fallEvidence==evidence and #timers==0)
            -- Resume observation after a targeted correction; no inherited baseline.
            saved.done.fall=nil; saved.fall=nil; saved.fallEvidence=nil
            TickFall(11,119,true); TickFall(11.1,40,false); FlushTimers()
            assert(saved.done.fall==nil and saved.fallEvidence==nil and reads>0)
            TickFall(20,120,false); TickFall(20.1,119,true)
            TickFall(20.2,80,true); TickFall(20.3,55,false)
            testClock=20.8; FlushTimers()
            assert(saved.done.fall and saved.fallEvidence.drop==65 and saved.history[1]=="keep")
        ''')

    def test_completed_guard_clears_pending_confirmation_and_new_character_baseline(self):
        self.h.execute('''
            LandMeasuredFall(40); assert(#timers==1)
            saved.done.fall=444444; local old=saved
            TickFall(10.4,40,false)
            ForeverAchievementsCharDB={done={},tracked={},history={"new character"}}
            testClock=10.8; FlushTimers()
            assert(old.done.fall==444444 and old.fallEvidence==nil)
            TickFall(11,120,true); TickFall(11.1,40,false); FlushTimers()
            assert(ForeverAchievementsCharDB.done.fall==nil and ForeverAchievementsCharDB.fallEvidence==nil)
            assert(old.history[1]=="keep" and #calls==0)
        ''')


if __name__ == "__main__":
    unittest.main()
