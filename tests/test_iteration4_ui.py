"""Iteration 4 component completion, currency display, and retained UI bounds.

Lua/XML fixtures validate renderer decisions and geometry, not live artwork or
WoW progression, native frame interaction, or real-client timing.
"""
import unittest

import test_wrath_iteration3_ui as iteration3


class Iteration4UITests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check

    def combined(self):
        self.check("""
            function copyRow(row)
                local result={}; for k,v in pairs(row) do result[k]=v end; return result
            end
            custom=copyRow(view.model.byKey['custom:second'])
            custom.completed=false; custom.scopeType='character'; custom.date=nil
            custom.completionDetail='Completed by Aldrin Stone'
            custom.completedByOtherCharacter=true; custom.pointType='character'; custom.pointValue=20
            native=copyRow(view.model.byKey['legacy:62013'])
            native.completed=true; native.scopeType='account'; native.pointType='legacy'; native.pointValue=1
            native.date='10/10/26'; native.completionDetail='Legacy challenge completed account-wide'
            combined=copyRow(custom); combined.source='combined'; combined.character=custom; combined.native=native
            combined.sources={custom=true,legacy=true}; combined.category='general'
            customCriteria={available=true,complete=true,items={{name='Custom objective',current=3,required=10,completed=false}}}
            nativeCriteria={available=true,complete=true,items={{name='Native objective',current=5,required=5,completed=true}}}
            local original=ns.LegacyPresentation.Criteria
            ns.LegacyPresentation.Criteria=function(row)
                if row~=combined then return original(row) end
                return {available=true,complete=true,items=customCriteria.items,sections={
                    {source='custom',record=custom,data=customCriteria},
                    {source='legacy',record=native,data=nativeCriteria}}}
            end
            view.model.records={combined}; view.model.byKey[combined.key]=combined
            view.model.byKey[native.key]=combined; ns.LegacyPresentation.Invalidate(view.model)
            view.category='general'; view.selected=combined.key
        """)

    def verified_zone(self):
        """Use both actual adapters and the real relationship proof."""
        self.check("""
            local a=ns.FA.BY_KEY.second
            a.key='explore802'; a.id=802; a.name='Explore Westfall'
            a.desc='Explore Westfall, revealing the covered areas of the world map.'
            a.list={'Sentinel Hill','Moonbrook'}; a.has=function() return false end
            a.progress=function() return 0,2 end
            ns.EXPLORE={{id=802,map=1436,zone='Westfall',cont='ek',areas={
                {'Sentinel Hill',1,2},{'Moonbrook',3,4}}}}
            ns.FA.CATEGORIES={{key='exploration',label='Exploration'}}
            ns.FA.CATEGORY_ORDER={'exploration'}
            ns.FA.CATEGORY_SECTIONS.exploration={{title='Eastern Kingdoms',list={a}}}
            function GetCategoryList() return {15607} end
            function GetCategoryInfo() return 'Exploration',-1,0 end
            function GetCategoryNumAchievements() return 2,0,2 end
            function GetAchievementInfo(id,index)
                if index then id=index==1 and 802 or 62053 end
                if id==802 then return id,'Explore Westfall',0,true,10,10,2026,
                    a.desc,131072,237388,'Earn 1 Legacy Point.',false,false end
                if id==62053 then return id,'Explore Azeroth',0,false,nil,nil,nil,
                    'Complete the zone map on a single character.',0,237388,'',false,false end
            end
            function GetAchievementNumCriteria(id) return id==802 and 2 or 1 end
            function GetAchievementCriteriaInfo(id,index)
                if id==802 then return a.list[index],43,true,1,1,0,0,1436,'1 / 1',900+index,true end
                return 'Westfall',8,false,0,1,0,0,802,'0 / 1',990,true
            end
            C_Traits.GetTraitCurrencyForAchievement=function(_,id) return id==802 and 1 or 0 end
            realModel=ns.LegacyPresentation.Build()
            zoneCard=realModel.byKey['custom:explore802']
            assert(zoneCard and zoneCard.source=='combined' and realModel.byKey['legacy:802']==zoneCard)
        """)

    def test_native_completion_uses_blue_accents_and_pool_resets_to_character_gold(self):
        self.check("""
            local row=view.model.byKey['legacy:62013']; row.completed=true; row.date='10/10/26'
            view:RenderCard(row,1,0)
            local c=view.cards[1]
            assert(c.nativeCompleted and not c.characterCompleted and c.saturated)
            assert(c.borderColor[1]<c.borderColor[3] and c.glow.color[1]<c.glow.color[3])
            assert(c.shield.icon.color[1]<c.shield.icon.color[3])
            assert(c.shield.points.color[1]<c.shield.points.color[3])
            assert(c.dateCompleted:IsShown() and c.dateCompleted:GetText()=='10/10/26')
            view:RenderCard(view.model.byKey['custom:first'],1,0)
            assert(c.characterCompleted and not c.nativeCompleted and c.saturated)
            assert(c.borderColor[1]>c.borderColor[3] and c.shield.icon.color[1]==1 and c.shield.icon.color[3]==1)
            assert(not c.nativeStatus:IsShown() and not c.otherCompletion:IsShown() and #calls==0)
        """)

    def test_unknown_native_completion_is_not_presented_as_complete(self):
        self.check("""
            local row=view.model.byKey['legacy:62013']; row.completed=nil; row.scopeType='unknown'
            row.completionDetail='Completion scope unavailable'; view.selected=row.key
            view:RenderCard(row,1,0); local c=view.cards[1]
            assert(not c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(not c.dateCompleted:IsShown() and c.scopeText:GetText()=='Scope: Unknown')
            assert(c.completionText:GetText()=='Completion scope unavailable' and #calls==0)
        """)

    def test_recorded_other_character_note_never_awards_current_completion(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            row.completed=false; row.completedByOtherCharacter=true; row.completionDetail='Completed by Aldrin Stone'
            view.selected=nil; view:RenderCard(row,1,0); local c=view.cards[1]
            assert(c.otherCompletion:IsShown() and c.otherCompletion:GetText()=='Completed by Aldrin Stone')
            assert(not c.saturated and c.shield.icon.coords[1]==.5 and not c.dateCompleted:IsShown())
            assert(view.model.custom.points==10 and saved.done.second==nil)
            row.completionDetail=nil; view:RenderCard(row,1,0)
            assert(not c.otherCompletion:IsShown())
            view:RenderCard(view.model.byKey['custom:first'],1,0)
            assert(not c.otherCompletion:IsShown() and #calls==0)
        """)

    def test_combined_native_complete_keeps_character_points_and_gold_unearned(self):
        self.combined()
        self.check("""
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(c.shield.points:GetText()=='20' and c.shield.icon.coords[1]==.5)
            assert(c.shield.icon.color[1]==1 and c.shield.icon.color[3]==1)
            assert(c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='Legacy: 1 point · Complete')
            assert(c.nativeStatus.color[1]<c.nativeStatus.color[3] and c.borderColor[1]<c.borderColor[3])
            assert(not c.dateCompleted:IsShown() and c.completionText:GetText()=='Completed by Aldrin Stone')
            assert(c.scopeText:GetText()=='Scope: Character' and c.tracked:IsShown())
            assert(c.progressPool[1].value==3 and c.progressPool[2].value==5)
            assert(c.progressPool[1].barColor[3]==0 and c.progressPool[2].barColor[3]==.85)
            assert(saved.done.second==nil and custom.completed==false and native.completed==true and #calls==0)
        """)

    def test_combined_character_complete_keeps_native_incomplete(self):
        self.combined()
        self.check("""
            custom.completed=true; custom.date='10/09/26'; custom.completionDetail='Completed on this character'
            combined.completed=true; combined.date=custom.date; combined.completionDetail=custom.completionDetail
            native.completed=false; native.scopeType='unknown'; native.completionDetail='Completion scope unavailable'
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.characterCompleted and not c.nativeCompleted and c.saturated)
            assert(c.shield.points:GetText()=='20' and c.shield.icon.coords[1]==0)
            assert(c.borderColor[1]>c.borderColor[3] and c.dateCompleted:GetText()=='10/09/26')
            assert(c.nativeStatus:GetText()=='Legacy: 1 point · Incomplete')
            local foundScope=false
            for _,f in ipairs(c.criteriaPool) do
                if f:IsShown() and f.label:GetText():find('Scope: Unknown',1,true) then foundScope=true end
            end
            assert(foundScope and native.completed==false and #calls==0)
        """)

    def test_combined_shield_tooltip_reports_both_points_and_verified_scope(self):
        self.combined()
        self.check("""
            tooltipLines={}; GameTooltip={SetOwner=function() end,SetText=function(_,t) tooltipTitle=t end,
                AddLine=function(_,t) tooltipLines[#tooltipLines+1]=t end,Show=function() end}
            view:RenderCard(combined,1,0); ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(tooltipTitle=='Character Achievement + Native Legacy')
            assert(tooltipLines[1]=='Character Achievement Points: 20' and tooltipLines[2]=='Character achievement: Incomplete')
            assert(tooltipLines[3]=='Scope: Character' and tooltipLines[4]=='Completed by Aldrin Stone')
            assert(tooltipLines[5]=='Legacy Points: 1' and tooltipLines[6]=='Native Legacy: Complete')
            assert(tooltipLines[7]=='Scope: Account' and tooltipLines[8]=='Legacy challenge completed account-wide')
            native.scopeType='unknown'; native.scope=nil; native.completionDetail='Completion scope unavailable'
            tooltipLines={}; ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(tooltipLines[7]=='Scope: Unknown')
            for _,text in ipairs(tooltipLines) do assert(not text:find('account-wide',1,true)) end
            assert(#calls==0)
        """)

    def test_combined_track_action_targets_only_underlying_custom_record(self):
        self.combined()
        self.check("""
            local tracked
            ns.CustomAchievementAdapter.Track=function(row) tracked=row end
            view:RenderCard(combined,1,0); ns.WrathAchievementUI.TrackClick(view.cards[1].tracked)
            assert(tracked==custom and tracked~=native and saved.done.second==nil and #calls==0)
        """)

    def test_combined_unknown_points_and_unavailable_native_criteria_remain_independent(self):
        self.combined()
        self.check("""
            native.pointType='unknown'; native.pointValue=nil; native.points=0
            nativeCriteria.available=false; nativeCriteria.complete=false; nativeCriteria.items={}
            combined.completed=nil; custom.completed=nil; combined.completionDetail='Completion unavailable'
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(not c.characterCompleted and not c.saturated and c.nativeCompleted)
            assert(c.shield.points:GetText()=='20' and c.nativeStatus:GetText()=='Legacy: points unavailable · Complete')
            assert(#c.progressPool==1 and c.progressPool[1].text:GetText()=='Custom objective: 3 / 10')
            local unknownPoints,unknownCriteria=false,false
            for _,f in ipairs(c.criteriaPool) do if f:IsShown() then
                if f.label:GetText()=='Native Legacy: Complete — points unavailable' then unknownPoints=true end
                if f.label:GetText()=='Criteria / progress unavailable.' then unknownCriteria=true end
            end end
            assert(unknownPoints and unknownCriteria and saved.done.second==nil and #calls==0)
        """)

    def test_combined_criteria_measure_matches_render_and_reuses_bounded_pool(self):
        self.combined()
        self.check("""
            customCriteria.items={}; nativeCriteria.items={}
            for i=1,300 do
                customCriteria.items[i]={name='Custom '..i,completed=false}
                nativeCriteria.items[i]={name='Native '..i,completed=true}
            end
            local advance=view:MeasureCard(combined)
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c:GetHeight()+4==advance and #c.criteriaPool<=261)
            local count=#c.criteriaPool
            for i=1,10 do view:RenderCard(combined,1,0) end
            assert(#c.criteriaPool==count)
            view.selected=nil; view:RenderCard(combined,1,0)
            assert(c:GetHeight()==84 and not c.scopeText:IsShown() and c.nativeStatus:IsShown())
            for _,f in ipairs(c.criteriaPool) do assert(not f:IsShown()) end
            assert(customCriteria.items[300] and nativeCriteria.items[300] and #calls==0)
        """)

    def test_verified_zone_relationship_renders_once_in_native_recent_summary(self):
        self.verified_zone()
        self.check("""
            view.selected='legacy:802'; view:SetModel(realModel)
            assert(view.selected=='custom:explore802' and view.category=='summary')
            local c=cardFor('custom:explore802')
            assert(c and c.selected and c:GetHeight()>84 and c.record==zoneCard)
            assert(c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(c.nativeStatus:GetText()=='Legacy: 1 point · Complete' and not c.dateCompleted:IsShown())
            local shown=0; for _,card in ipairs(view.cards) do if card:IsShown() then shown=shown+1 end end
            assert(shown==1 and realModel.custom.points==0 and saved.done.explore802==nil)
            assert(c.criteriaPool[1].label:GetText()=='Character Achievement: Incomplete — 20 points')
            assert(not c.criteriaPool[2].check:IsShown() and c.criteriaPool[6].check:IsShown())
            assert(#calls==0)
        """)

    def test_verified_zone_both_recent_source_events_share_one_card_and_alias_navigation(self):
        self.verified_zone()
        self.check("""
            saved.done.explore802=1730000000
            view:SetModel(ns.LegacyPresentation.Build())
            local c=cardFor('custom:explore802'); assert(c and c.characterCompleted and c.nativeCompleted)
            local shown=0; for _,card in ipairs(view.cards) do if card:IsShown() then shown=shown+1 end end
            assert(shown==1 and c.saturated and c.shield.points:GetText()=='20')
            assert(c.dateCompleted:GetText()=='10/27/24' and view.model.custom.points==20)
            view.category='exploration:world'; view.selected='legacy:62053'; view:Render()
            local parent=cardFor('legacy:62053'); assert(parent and parent.metaPool[1].link=='legacy:802')
            ns.WrathAchievementUI.MetaClick(parent.metaPool[1])
            assert(view.focus==view.model.byKey['custom:explore802'] and view.selected=='custom:explore802')
            local linked=cardFor('custom:explore802'); assert(linked and linked.selected and linked:GetHeight()>84)
            linked:Fire('OnClick'); assert(view.selected==nil and view.focus==linked.record)
            assert(cardFor('custom:explore802'):GetHeight()==84 and #calls==0)
        """)

    def test_money_quantity_text_is_authoritative_and_copper_fallback_is_custom_only(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.achievement.money=true
            local data={available=true,complete=true,items={{name='Money looted',current=38,required=50000000,completed=false}}}
            ns.LegacyPresentation.Criteria=function() return data end
            local moneyCalls=0
            ns.FA.Money=function(copper) moneyCalls=moneyCalls+1; return copper..' copper formatted' end
            view.selected=row.key; view:RenderCard(row,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='Money looted: 38 copper formatted / 50000000 copper formatted')
            assert(moneyCalls==2)
            data.items[1].quantityText='38c / 100g (tracked since Iteration 4)'
            view:RenderCard(row,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='Money looted: 38c / 100g (tracked since Iteration 4)' and moneyCalls==2)
            local native=view.model.byKey['legacy:62013']; native.name='Got My Mind on My Money'
            data.items[1].quantityText=nil; view.selected=native.key; view:RenderCard(native,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='Money looted: 38 / 50000000' and moneyCalls==2)
            ns.FA.Money=function() error('Formatter unavailable') end
            view.selected=row.key; view:RenderCard(row,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='Money looted: 38 copper / 50000000 copper')
            assert(#calls==0)
        """)

    def test_unsupported_money_retains_explicit_tracking_explanation(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.achievement.money=true
            ns.LegacyPresentation.Criteria=function() return {available=false,complete=false,items={
                {name='Quest earnings',current=nil,required=1000000,completed=nil,
                 quantityText='Unavailable / 100g (lifetime quest total unsupported)'}}} end
            view.selected=row.key; view:RenderCard(row,1,0); local c=view.cards[1]
            assert(#c.progressPool==0)
            assert(c.criteriaPool[1].label:GetText()=='Quest earnings: Unavailable / 100g (lifetime quest total unsupported)')
            assert(not c.criteriaPool[1].check:IsShown() and c.criteriaPool[2].label:GetText()=='Criteria / progress unavailable.')
            assert(not c.saturated and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
