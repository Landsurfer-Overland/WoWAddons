"""Owned notification animation and accessible preview settings; no game awards."""
import unittest

from test_progression_addendum import CoreHarness


class AlertHarness(CoreHarness):
    def __init__(self, modern=True):
        super().__init__()
        self.execute('''
            soundCalls={}; SOUNDKIT={UI_ACHIEVEMENT_AWARDED=12891,LEVELUP=888,IG_QUEST_LIST_COMPLETE=878,READY_CHECK=8960}
            function PlaySound(id,channel) soundCalls[#soundCalls+1]={id,channel}; return true end
            registrationCalls=0; settingsOpenCalls=0
            function IsLoggedIn() return false end
            function StepAlert(elapsed)
                local frame=ns.AchievementAlerts.frame
                if frame and frame:GetScript('OnUpdate') then frame:Fire('OnUpdate',elapsed) end
            end
            function Fingerprint(value)
                if type(value)~='table' then return type(value)..':'..tostring(value) end
                local keys,out={},{}
                for key in pairs(value) do keys[#keys+1]=key end
                table.sort(keys,function(a,b) return tostring(a)<tostring(b) end)
                for _,key in ipairs(keys) do out[#out+1]=Fingerprint(key)..'='..Fingerprint(value[key]) end
                return '{'..table.concat(out,';')..'}'
            end
        ''')
        if modern:
            self.execute('''
                Settings={
                    RegisterCanvasLayoutCategory=function(panel,name)
                        assert(not InCombatLockdown()); registrationCalls=registrationCalls+1
                        return {GetID=function() return 91 end,panel=panel,name=name}
                    end,
                    RegisterAddonCategory=function(category)
                        assert(category.name=='Legacy Achievements Reforged' and not InCombatLockdown())
                    end,
                    OpenToCategory=function(id)
                        assert(id==91 and not InCombatLockdown()); settingsOpenCalls=settingsOpenCalls+1
                    end,
                }
            ''')
        self.load("UI/AchievementAlerts.lua")
        self.load("UI/AddonSettings.lua")
        self.execute('ns.LAR.Settings().sound=true; ns.LAR.Settings().toasts=true')

    def create(self, kind, name=None, parent=None, template=None):
        # The client provides these two standard button templates. Their input
        # callbacks are real addon code; their native artwork is not emulated.
        if template in ("UIPanelButtonTemplate", "UICheckButtonTemplate"):
            return self.g.UIObject(kind, name, parent)
        return super().create(kind, name, parent, template)


class AchievementAlertTests(unittest.TestCase):
    def setUp(self):
        self.h = AlertHarness()

    def check(self, code):
        self.h.execute(code)

    def test_preview_does_not_award_points_change_history_or_run_hooks(self):
        self.check('''
            local L,A=ns.LAR,ns.AchievementAlerts
            local db,account=Fingerprint(L.DB()),Fingerprint(L.Account())
            local earned=0; L.EARN_HOOKS[#L.EARN_HOOKS+1]=function() earned=earned+1 end
            local points=L.TotalPoints()
            assert(A.Preview()); StepAlert(.3); StepAlert(2); StepAlert(20)
            assert(not A.active and not A.frame:IsShown() and not A.frame:GetScript('OnUpdate'))
            assert(Fingerprint(L.DB())==db and Fingerprint(L.Account())==account)
            assert(L.TotalPoints()==points and earned==0 and #calls==0)
            assert(#soundCalls==1 and soundCalls[1][1]==12891 and soundCalls[1][2]=='Master')
        ''')

    def test_uses_classic_crops_gold_frame_and_distinct_preview_marker(self):
        self.check('''
            local A=ns.AchievementAlerts; A.Preview(); local f=A.frame
            assert(f:GetWidth()==300 and f:GetHeight()==88)
            assert(f.background.textureValue=='Interface\\\\AchievementFrame\\\\UI-Achievement-Alert-Background')
            assert(f.background.coords[2]==.605 and f.background.coords[4]==.703)
            assert(f.icon:GetWidth()==50 and f.iconFrame:GetWidth()==72)
            assert(f.shield.coords[2]==.5 and f.shield.coords[4]==.5)
            assert(f.preview:IsShown() and f.points:GetText()=='10')
            assert(f.name:GetText()=='Reforged Test Achievement' and not f:IsMouseEnabled())
            assert(f.glow:GetBlendMode()=='ADD' and f.shine:GetBlendMode()=='ADD')
        ''')

    def test_fade_glow_shine_hold_and_exit_stop_updating_when_finished(self):
        self.check('''
            local A=ns.AchievementAlerts; A.Preview(); local f=A.frame
            assert(f:GetAlpha()==0 and f:IsShown())
            StepAlert(.1); assert(f:GetAlpha()==.5 and f.glow.alpha==.5)
            StepAlert(.3); assert(f:GetAlpha()==1 and f.shine:IsShown())
            StepAlert(.8); assert(not f.glow:IsShown() and not f.shine:IsShown())
            StepAlert(3.5); assert(f:GetAlpha()>0 and f:GetAlpha()<1)
            StepAlert(2); assert(not f:IsShown() and not f:GetScript('OnUpdate'))
        ''')

    def test_animation_disabled_is_static_but_still_expires(self):
        self.check('''
            ns.LAR.Settings().animations=false; ns.LAR.Settings().toastTime=2
            local A=ns.AchievementAlerts; A.Preview(); local f=A.frame
            assert(f:GetAlpha()==1 and not f.glow:IsShown() and not f.shine:IsShown())
            StepAlert(1); assert(f:GetAlpha()==1 and f:IsShown())
            StepAlert(2); assert(not A.active and not f:GetScript('OnUpdate'))
        ''')

    def test_preview_replays_and_stop_reuse_one_frame_without_timers(self):
        self.check('''
            local A=ns.AchievementAlerts; A.Preview(); local f,count,timerCount=A.frame,#frames,#timers
            for i=1,30 do assert(A.Preview()); StepAlert(.1); assert(#A.queue==0) end
            assert(A.frame==f and #frames==count and #timers==timerCount)
            assert(A.StopPreview()); assert(not f:IsShown() and not f:GetScript('OnUpdate'))
            assert(not A.StopPreview() and #calls==0)
        ''')

    def test_sound_choice_mute_channel_and_unavailable_sound_are_explicit(self):
        self.check('''
            local L,A=ns.LAR,ns.AchievementAlerts
            L.Settings().sound=false; A.Preview(); assert(#soundCalls==0)
            assert(A.PlaySelectedSound() and #soundCalls==1) -- explicit sound test ignores preference
            L.Settings().soundName='LEVELUP'; L.Settings().alertSoundChannel='SFX'
            assert(A.PlaySelectedSound() and soundCalls[2][1]==888 and soundCalls[2][2]=='SFX')
            SOUNDKIT.LEVELUP=nil
            local ok,reason=A.PlaySelectedSound(); assert(not ok and reason:find('unavailable',1,true))
            assert(#soundCalls==2) -- no unrelated fallback chime
            PlaySound=function() return false end; L.Settings().soundName='UI_ACHIEVEMENT_AWARDED'
            ok,reason=A.PlaySelectedSound(); assert(not ok and reason:find('declined',1,true))
            PlaySound=function() error('Playback error') end
            ok,reason=A.PlaySelectedSound(); assert(not ok and reason:find('Playback error',1,true))
        ''')

    def test_real_unlock_preempts_preview_queues_once_and_cannot_be_stopped_by_preview(self):
        self.check('''
            local A=ns.AchievementAlerts; A.Preview()
            A.Enqueue({name='Actual one',id=1,pts=10}); A.Enqueue({name='Actual two',pts=20})
            assert(A.active.record.name=='Actual one' and not A.frame.preview:IsShown())
            assert(not A.Preview() and not A.StopPreview())
            assert(#A.queue==1 and A.frame.points:GetText()=='10')
            StepAlert(20); assert(A.active.record.name=='Actual two' and #A.queue==0)
            StepAlert(20); assert(not A.active and not A.frame:GetScript('OnUpdate'))
            ns.LAR.Settings().toasts=false
            assert(not A.Enqueue({name='Muted',pts=10}) and not A.active)
            assert(A.Preview()) -- explicit test remains usable while normal notifications disabled
        ''')

    def test_real_completion_uses_new_presenter_and_keeps_saved_progress_and_hooks(self):
        self.check('''
            SelectAchievements('lvl10'); CoreEvent('PLAYER_LOGIN'); FlushTimers()
            local L,A=ns.LAR,ns.AchievementAlerts
            assert(L.DB().done.lvl10==nil)
            local earned=0; L.EARN_HOOKS[#L.EARN_HOOKS+1]=function(a) assert(a.key=='lvl10'); earned=earned+1 end
            function UnitLevel() return 10 end
            CoreEvent('PLAYER_LEVEL_UP'); FlushTimers()
            assert(L.DB().done.lvl10 and earned==1 and A.active)
            assert(A.active.record.name==L.BY_KEY.lvl10.name and not A.active.record.preview)
            assert(not A.frame.preview:IsShown() and #A.queue==0)
            local count=#soundCalls
            CoreEvent('PLAYER_LEVEL_UP'); FlushTimers()
            assert(earned==1 and #soundCalls==count)
        ''')

    def test_burst_queue_is_bounded_and_overflow_remains_visible_as_summary(self):
        self.check('''
            local A=ns.AchievementAlerts
            for i=1,50 do A.Enqueue({name='Unlock '..i,pts=10}) end
            assert(#A.queue==32 and A.overflow==17)
            for i=1,33 do StepAlert(20) end
            assert(#A.queue==0 and A.overflow==0 and A.active.record.name=='17 additional achievements earned')
            StepAlert(20); assert(not A.active and not A.frame:GetScript('OnUpdate'))
        ''')

    def test_combat_preview_touches_only_owned_frames_and_malformed_settings_are_bounded(self):
        self.check('''
            inCombat=true
            local L,A=ns.LAR,ns.AchievementAlerts
            L.Settings().toastTime=math.huge; L.Settings().toastY=-900; L.Settings().alertScale=9
            assert(A.Preview()); StepAlert(.1)
            assert(A.active.hold==4 and A.frame:GetScale()==1.5)
            local _,_,_,_,y=A.frame:GetPoint(1); assert(y==-60 and #calls==0)
            StepAlert(20); assert(not A.active and #calls==0)
        ''')


class AlertSettingsTests(unittest.TestCase):
    def setUp(self):
        self.h = AlertHarness()

    def check(self, code):
        self.h.execute(code)

    def test_modern_settings_register_once_and_open_exact_category(self):
        self.check('''
            local U=ns.AddonSettings; U.events:Fire('OnEvent','PLAYER_LOGIN')
            assert(registrationCalls==1 and U.mode=='modern')
            local count=#frames
            for i=1,20 do U.Register(); U.Open() end
            assert(registrationCalls==1 and settingsOpenCalls==20 and #frames==count)
            assert(#calls==0)
        ''')

    def test_panel_buttons_preview_sound_and_stop_without_progress_writes(self):
        self.check('''
            local L,U,A=ns.LAR,ns.AddonSettings,ns.AchievementAlerts
            U.Register(); local before=Fingerprint(L.DB())
            U.panel.test:Fire('OnClick'); assert(A.active.record.preview)
            assert(U.panel.status:GetText():find('No progress or points',1,true))
            U.panel.soundTest:Fire('OnClick'); assert(#soundCalls==2)
            U.panel.stop:Fire('OnClick'); assert(not A.active)
            assert(Fingerprint(L.DB())==before and #calls==0)
        ''')

    def test_settings_change_only_preferences_and_reopen_does_not_write_defaults(self):
        self.check('''
            local L,U=ns.LAR,ns.AddonSettings; U.Register()
            local before=Fingerprint(L.Account())
            U.Sync(); U.Sync(); assert(Fingerprint(L.Account())==before)
            U.panel.checks.animations:SetChecked(false); U.panel.checks.animations:Fire('OnClick')
            U.panel.sliders.toastTime:SetValue(6); U.panel.sliders.toastY:SetValue(220)
            U.panel.sliders.alertScale:SetValue(1.25); U.panel.sound:Fire('OnClick'); U.panel.channel:Fire('OnClick')
            local s=L.Settings()
            assert(s.animations==false and s.toastTime==6 and s.toastY==220 and s.alertScale==1.25)
            assert(s.soundName=='LEVELUP' and s.alertSoundChannel=='SFX')
            U.Sync(); assert(not U.panel.checks.animations:GetChecked())
            assert(U.panel.sliders.toastTime:GetValue()==6 and U.panel.channel:GetText()=='Channel: SFX')
        ''')

    def test_registration_and_settings_open_defer_once_until_combat_ends(self):
        self.check('''
            inCombat=true; local U=ns.AddonSettings
            U.events:Fire('OnEvent','PLAYER_LOGIN'); U.Open(); U.Open()
            assert(not U.panel and U.registerPending and U.openPending and registrationCalls==0)
            inCombat=false; U.events:Fire('OnEvent','PLAYER_REGEN_ENABLED')
            assert(registrationCalls==1 and settingsOpenCalls==1 and not U.openPending and not U.registerPending)
            U.events:Fire('OnEvent','PLAYER_REGEN_ENABLED')
            assert(registrationCalls==1 and settingsOpenCalls==1 and #calls==0)
        ''')

    def test_classic_category_api_and_standalone_fallback_are_usable(self):
        for legacy in (True, False):
            h = AlertHarness(modern=False)
            if legacy:
                h.execute('''
                    function InterfaceOptions_AddCategory(panel) registrationCalls=registrationCalls+1 end
                    function InterfaceOptionsFrame_OpenToCategory(panel)
                        assert(panel==ns.AddonSettings.panel); settingsOpenCalls=settingsOpenCalls+1
                    end
                ''')
            h.execute('''
                local U=ns.AddonSettings; U.Open(); local count=#frames; U.Open()
                assert(#frames==count and #calls==0)
                U.panel.test:Fire('OnClick'); assert(ns.AchievementAlerts.active.record.preview)
            ''')
            if legacy:
                h.execute("assert(ns.AddonSettings.mode=='legacy' and registrationCalls==1 and settingsOpenCalls==2)")
            else:
                h.execute("assert(ns.AddonSettings.mode=='standalone' and ns.AddonSettings.panel:IsShown())")


if __name__ == '__main__':
    unittest.main()
