"""Standalone account presentation executes Views.lua with explicit widgets.

Fixtures inspect rendered labels and controls, never mutate account progression.
"""
import unittest

from test_legacy_wrath_ui import Harness


class StandaloneViewTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute("""
            account={chars={}}; renderedFonts={}; renderedHeaders={}; controls={}
            settings.accountView=true
            local FA=ns.FA
            FA.secret=function(value) return value==HiddenSnapshotValue end
            FA.Account=function() return account end
            FA.VIEWS={}; FA.THEMES={{key='teal',label='Teal'}}
            FA.EarnedTitles=function() return {} end; FA.CurrentTitle=function() return nil end
            FA.ZONE_ACH={}; FA.CRITTERS={}; FA.PESTS={}
            function GetRealZoneText() return nil end
            function IsInInstance() return false end
            local W={}
            FA.Kit={W=W,COLORS={card={0,0,0,1},cardHover={.1,.1,.1,1},edge={.2,.2,.2,1},
                dim={.7,.7,.7},text={1,1,1}},Accent=function() return 1,.82,0 end,
                MakeBorder=function(frame) assert(frame:GetObjectType()=='Frame' or frame:GetObjectType()=='Button') end,
                MakeFont=function(parent)
                    local text=parent:CreateFontString(nil,'OVERLAY','GameFontNormal')
                    renderedFonts[#renderedFonts+1]=text; return text
                end}
            function W:SectionHeader(parent,label,y)
                renderedHeaders[#renderedHeaders+1]=label; return CreateFrame('Frame',nil,parent),24
            end
            function W:Dropdown(parent,label,y,values,get,set)
                controls[label]={get=get,set=set}; return CreateFrame('Frame',nil,parent),34
            end
            function W:Toggle(parent,label,y,get,set)
                controls[label]={get=get,set=set}; return CreateFrame('Frame',nil,parent),30
            end
            function W:Slider(parent,label,y,min,max,step,get,set)
                controls[label]={get=get,set=set}; return CreateFrame('Frame',nil,parent),34
            end
            function W:WideDualButton(parent,left,right,y)
                controls[left]={}; controls[right]={}; return CreateFrame('Frame',nil,parent),34
            end
            child=CreateFrame('Frame','StandaloneViewHost'); child:SetSize(1000,1000)
            function verifiedSnapshot(key,name,surname,realm,guid,points,last)
                return {name=name,surname=surname,realm=realm,class='WARRIOR',level=1,count=0,
                    pts=points,last=last,done={},identityVersion=1,characterKey=key,
                    completionScope='character',pointType='character',pointsAvailable=points~=nil,countAvailable=true,
                    identity={verified=true,key=key,name=name,surname=surname,realm=realm,guid=guid}}
            end
            function renderedContains(text)
                for _,font in ipairs(renderedFonts) do if font:GetText():find(text,1,true) then return true end end
                return false
            end
            function renderedCount(text)
                local n=0
                for _,font in ipairs(renderedFonts) do if font:GetText():find(text,1,true) then n=n+1 end end
                return n
            end
        """)
        self.h.load("Views.lua")

    def check(self, code):
        self.h.execute(code)

    def test_summary_shows_verified_zero_unknown_and_keeps_unverified_history_without_total(self):
        self.check("""
            local old={name='Old',realm='Forever',pts=900,count=90,done={first=100}}
            account.chars['Old-Forever']=old
            account.chars.Main=verifiedSnapshot('Main','Main','One','Forever','Player-Main',10,100)
            account.chars.Alt=verifiedSnapshot('Alt','Alt','One','Forever','Player-Alt',0,90)
            account.chars.Unknown=verifiedSnapshot('Unknown','Unknown','One','Forever','Player-Unknown',nil,80)
            ns.FA.VIEWS.summary(child,1000)
            assert(renderedContains('Main One') and renderedContains('Alt One') and renderedContains('Unknown One'))
            assert(renderedContains('10 character points') and renderedContains('0 character points'))
            assert(renderedContains('Unavailable character points') and not renderedContains('900'))
            assert(renderedContains('Older or unverified character snapshots are preserved'))
            assert(not renderedContains('Account:') and account.chars['Old-Forever']==old and old.done.first==100)
            assert(settings.accountView==true and #calls==0)
        """)

    def test_verified_identity_aliases_display_once_without_coercing_new_unknown_points(self):
        self.check("""
            account.chars.NameAlias=verifiedSnapshot('NameAlias','Main','One','Forever',nil,30,10)
            account.chars.GuidKey=verifiedSnapshot('GuidKey','Main','One','Forever','Player-Main',nil,20)
            account.chars.OtherRealm=verifiedSnapshot('OtherRealm','Main','One','Elsewhere','Player-Other',5,15)
            ns.FA.VIEWS.summary(child,1000)
            assert(renderedCount('Main One')==2)
            assert(renderedContains('Unavailable character points') and renderedContains('5 character points'))
            assert(not renderedContains('30 character points'))
            assert(account.chars.NameAlias.pts==30 and account.chars.GuidKey.pts==nil)
            assert(#calls==0)
        """)

    def test_snapshot_scope_key_and_availability_are_checked_before_display(self):
        self.check("""
            account.chars.Flagged=verifiedSnapshot('Flagged','Flagged','One','Forever','Player-Flagged',99,10)
            account.chars.Flagged.pointsAvailable=false; account.chars.Flagged.count=12; account.chars.Flagged.countAvailable=false
            account.chars.Mixed=verifiedSnapshot('Mixed','Mixed','One','Forever','Player-Mixed',5,10)
            account.chars.Mixed.pointType='legacy'
            account.chars.WrongKey=verifiedSnapshot('ActualKey','Mismatched','One','Forever','Player-Wrong',5,10)
            account.chars.AccountScope=verifiedSnapshot('AccountScope','AccountScoped','One','Forever','Player-Account',5,10)
            account.chars.AccountScope.completionScope='account'
            ns.FA.VIEWS.summary(child,1000)
            assert(renderedContains('Flagged One') and renderedContains('Unavailable earned'))
            assert(renderedContains('Unavailable character points') and not renderedContains('99 character points'))
            assert(not renderedContains('Mixed One') and not renderedContains('Mismatched One') and not renderedContains('AccountScoped One'))
            assert(account.chars.Mixed.pointType=='legacy' and account.chars.WrongKey.characterKey=='ActualKey')
            assert(#calls==0)
        """)

    def test_settings_no_longer_promises_account_union_and_preserves_saved_preference(self):
        self.check("""
            ns.FA.VIEWS.settings(child,1000)
            assert(controls['Account-wide view']==nil)
            assert(renderedContains("Achievements and points use this character's progress"))
            assert(not renderedContains('Show an achievement as earned when any'))
            assert(settings.accountView==true)
            controls['Show keys and IDs in tooltips'].set(true)
            assert(settings.showIDs==true and settings.accountView==true and #calls==0)
        """)

    def test_malformed_completion_records_remain_saved_without_recent_completion_claims(self):
        self.check("""
            saved.done.first=false; saved.done.second='unverified'
            ns.FA.VIEWS.summary(child,1000)
            assert(not renderedContains('First custom') and not renderedContains('Second custom'))
            for _,header in ipairs(renderedHeaders) do assert(header~='RECENTLY EARNED') end
            assert(saved.done.first==false and saved.done.second=='unverified' and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
