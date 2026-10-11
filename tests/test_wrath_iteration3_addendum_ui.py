"""Visual expansion and completion provenance remain separate from progression.

These Lua/XML fixtures do not represent in-client rendering or native gameplay.
"""
import unittest

import test_wrath_iteration3_ui as iteration3


class AddendumUITests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check
    def test_card_toggle_collapses_and_moves_following_entries_back(self):
        self.check("""
            view.category=view.model.byKey['custom:first'].category; view:Render()
            local first,second=cardFor('custom:first'),cardFor('custom:second')
            local initialSecondY=second.points[1][5]
            assert(first:GetHeight()==84 and second:GetHeight()==84)
            first:Fire('OnClick')
            first,second=cardFor('custom:first'),cardFor('custom:second')
            assert(view.selected=='custom:first' and first:GetHeight()>84)
            assert(first.plusMinus.coords[3]==.25 and second.points[1][5]<initialSecondY)
            first:Fire('OnClick')
            first,second=cardFor('custom:first'),cardFor('custom:second')
            assert(view.selected==nil and first:GetHeight()==84 and first.plusMinus.coords[3]==0)
            assert(second.points[1][5]==initialSecondY)
            first:Fire('OnClick'); cardFor('custom:second'):Fire('OnClick')
            assert(view.selected=='custom:second')
            assert(cardFor('custom:first'):GetHeight()==84 and cardFor('custom:second'):GetHeight()>84)
            assert(#calls==0)
        """)

    def test_linked_card_collapse_keeps_its_navigation_route(self):
        self.check("""
            view.category=view.model.byKey['legacy:62053'].category; view.selected='legacy:62053'; view:Render()
            ns.WrathAchievementUI.MetaClick(cardFor('legacy:62053').metaPool[1])
            local target=view.focus.key
            local card=cardFor(target)
            assert(card and card:GetHeight()>84 and view.selected==target)
            card:Fire('OnClick')
            assert(view.focus.key==target and view.selected==nil)
            assert(cardFor(target) and cardFor(target):GetHeight()==84)
            assert(cardFor(target).plusMinus.coords[3]==0)
            cardFor(target):Fire('OnClick')
            assert(view.focus.key==target and view.selected==target and cardFor(target):GetHeight()>84)
            assert(#calls==0)
        """)

    def test_collapse_at_end_clamps_scroll_and_retains_last_card(self):
        self.check("""
            view.model.records={}
            for i=1,100 do
                view.model.records[i]={key='custom:entry'..i,source='custom',category='general',name='Entry '..i,
                    description='',achievement={},completed=false,scopeType='character',pointType='character',pointValue=10,
                    current=3,required=10}
            end
            view.category='general'; view:Render()
            view.contentScroll:SetVerticalScroll(view.contentChild:GetHeight()-view.contentScroll:GetHeight())
            cardFor('custom:entry100'):Fire('OnClick')
            view.contentScroll:SetVerticalScroll(view.contentChild:GetHeight()-view.contentScroll:GetHeight())
            local expandedHeight=view.contentChild:GetHeight()
            cardFor('custom:entry100'):Fire('OnClick')
            assert(view.selected==nil and view.contentChild:GetHeight()<expandedHeight)
            assert(view.contentScroll:GetVerticalScroll()==view.contentChild:GetHeight()-view.contentScroll:GetHeight())
            assert(cardFor('custom:entry100') and cardFor('custom:entry100'):GetHeight()==84)
            assert(#calls==0)
        """)

    def test_ordinary_custom_hides_cross_character_detail_and_keeps_current_art_incomplete(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            row.completed=false; row.completedOnCurrentCharacter=false; row.completedByOtherCharacter=true
            row.completionScope='other_character'; row.completionDetail='Completed by another character'
            view.selected=row.key; view:RenderCard(row,1,0)
            local card=view.cards[1]
            assert(not card.saturated and card.shield.icon.coords[1]==.5 and card.shield.points:GetText()=='20')
            assert(not card.completionText:IsShown() and not card.otherCompletion:IsShown())
            assert(not card.scopeText:IsShown() and row.completionDetail=='Completed by another character')
            assert(view.model.custom.points==10 and saved.done.second==nil)
            view.selected=nil; view:RenderCard(row,1,0)
            assert(not card.completionText:IsShown() and card:GetHeight()==84 and not card.saturated)
            assert(#calls==0)
        """)

    def test_current_character_completion_and_native_account_completion_remain_distinct(self):
        self.check("""
            local custom=view.model.byKey['custom:first']
            custom.completionDetail='Completed on this character'; custom.completionScope='current_character'
            view.selected=custom.key; view:RenderCard(custom,1,0)
            local card=view.cards[1]
            assert(card.saturated and not card.completionText:IsShown())
            assert(custom.completionDetail=='Completed on this character')
            local native=view.model.byKey['legacy:62013']
            native.completed=true; native.scopeType='account'; native.completionScope='native_account'
            native.completionDetail='Legacy challenge completed account-wide'
            view.selected=native.key; view:RenderCard(native,1,0)
            assert(not card.saturated and card.nativeCompleted and not card.characterCompleted)
            assert(card.visualState=='native-complete' and card.shield.wreath.color[1]<card.shield.wreath.color[3])
            assert(not card.completionText:IsShown() and not card.scopeText:IsShown() and saved.done.second==nil)
            native.completionScope='unknown'; native.completionDetail='Completion scope unavailable'
            view:RenderCard(native,1,0)
            assert(not card.saturated and card.visualState=='native-complete' and not card.completionText:IsShown())
            assert(native.completionDetail=='Completion scope unavailable')
            assert(#calls==0)
        """)

    def test_provenance_tooltip_uses_verified_detail_without_guessing_other_character(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            tooltipLines={}; GameTooltip={SetOwner=function() end,SetText=function() end,
                AddLine=function(_,text) tooltipLines[#tooltipLines+1]=text end,Show=function() end}
            row.completionDetail='Completed by another character'; row.completionScope='other_character'
            view:RenderCard(row,1,0); ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            for _,line in ipairs(tooltipLines) do assert(line~='Completed by another character') end
            assert(row.completionDetail=='Completed by another character')
            row.completionDetail=nil; row.completionScope=nil; row.completedByOtherCharacter=true
            tooltipLines={}; view.selected=row.key; view:RenderCard(row,1,0)
            ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(not view.cards[1].completionText:IsShown())
            for _,line in ipairs(tooltipLines) do assert(line~='Completed by another character') end
            row.completed=nil; tooltipLines={}; view:RenderCard(row,1,0)
            ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(not view.cards[1].saturated and not view.cards[1].completionText:IsShown())
            for _,line in ipairs(tooltipLines) do assert(line~='Completion unavailable') end
            assert(row.completed==nil and #calls==0)
        """)

    def test_adapter_verified_other_character_and_native_account_states_render_independently(self):
        self.check("""
            local current={verified=true,key='AltKey',name='Alt',surname='One',realm='Forever',guid='Player-Alt'}
            local other={verified=true,key='MainKey',name='Main',surname='One',realm='Forever',guid='Player-Main'}
            ns.LAR.CharacterIdentity=function() return current end
            ns.LAR.Account=function() return {chars={MainKey={identity=other,identityVersion=1,
                characterKey='MainKey',completionScope='character',done={second=200}}}} end
            local nativeInfo=GetAchievementInfo
            function GetAchievementInfo(id,index)
                local values={nativeInfo(id,index)}
                if values[1]==62013 then values[4]=true; values[9]=131072; values[13]=nil end
                return unpack(values,1,15)
            end
            view:SetModel(ns.LegacyPresentation.Build())
            local custom=view.model.byKey['custom:second']
            assert(custom.completed==false and custom.completionScope=='other_character')
            view.selected=custom.key; view:RenderCard(custom,1,0)
            assert(not view.cards[1].saturated and not view.cards[1].completionText:IsShown())
            assert(custom.completionDetail=='Completed by Main One' and custom.completedByName=='Main One')
            local native=view.model.byKey['legacy:62013']
            assert(native.completed==true and native.completionScope=='native_account')
            view.selected=native.key; view:RenderCard(native,1,0)
            assert(not view.cards[1].saturated and view.cards[1].nativeCompleted and not view.cards[1].completionText:IsShown())
            assert(view.cards[1].visualState=='native-complete' and view.cards[1].nativeStatus:GetText()=='Completed via Legacy')
            assert(native.completionDetail=='Legacy challenge completed account-wide')
            assert(custom.completed==false and saved.done.second==nil and view.model.custom.points==10)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='10' and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
