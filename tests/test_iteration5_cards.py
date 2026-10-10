"""Player-facing card cleanup with the actual Lua renderer and XML pools.

These fixtures check presentation contracts, ownership and bounded geometry;
they cannot establish WoW rendering quality or in-game progression accuracy.
"""
import unittest

import test_wrath_iteration3_ui as iteration3
import test_iteration4_ui as iteration4


class Iteration5CardTests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check
    combined = iteration4.Iteration4UITests.combined

    def tooltip(self):
        self.check("""
            tooltipLines={}; GameTooltip={SetOwner=function() end,
                SetText=function(_,text) tooltipTitle=text end,
                AddLine=function(_,text) tooltipLines[#tooltipLines+1]=text end,
                Show=function() end}
        """)

    def test_ordinary_unknown_criteria_are_unchecked_without_technical_filler(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            row.completed=nil; row.completionDetail='Completion unavailable'
            local data={available=false,complete=false,items={
                {name='A critter',completed=nil},
                {name='Another objective',current=nil,required=10,completed=nil}}}
            ns.LegacyPresentation.Criteria=function() return data end
            view.selected=row.key
            local advance=view:MeasureCard(row); view:RenderCard(row,1,0)
            local c=view.cards[1]
            assert(c:GetHeight()+4==advance and #c.criteriaPool==2 and #c.progressPool==0)
            assert(not c.scopeText:IsShown() and not c.completionText:IsShown())
            assert(not c.saturated and not c.dateCompleted:IsShown())
            assert(c.criteriaPool[1].label:GetText()=='A critter')
            assert(c.criteriaPool[2].label:GetText()=='Another objective')
            for _,f in ipairs(c.criteriaPool) do assert(not f.check:IsShown()) end
            assert(row.completed==nil and row.completionDetail=='Completion unavailable')
            assert(data.available==false and data.items[1].completed==nil and saved.done.second==nil and #calls==0)
        """)

    def test_ordinary_custom_history_is_retained_without_card_or_tooltip_name(self):
        self.tooltip()
        self.check("""
            local row=view.model.byKey['custom:second']
            row.completedByOtherCharacter=true; row.completedByName='Aldrin Stone'
            row.completionDetail='Completed by Aldrin Stone'
            view.selected=row.key; view:RenderCard(row,1,0)
            ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            local c=view.cards[1]
            assert(not c.otherCompletion:IsShown() and not c.completionText:IsShown() and not c.scopeText:IsShown())
            assert(not c.saturated and c.shield.points:GetText()=='20')
            for _,text in ipairs(tooltipLines) do
                assert(not text:find('Aldrin',1,true) and not text:find('Scope:',1,true))
            end
            assert(row.completedByName=='Aldrin Stone' and row.completedByOtherCharacter==true)
            assert(row.completionDetail=='Completed by Aldrin Stone' and view.model.custom.points==10 and saved.done.second==nil)
        """)

    def test_combined_card_names_verified_earner_and_keeps_native_completion_separate(self):
        self.combined(); self.tooltip()
        self.check("""
            custom.completedByName='Aldrin Stone'
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.completionText:IsShown() and c.completionText:GetText()=='Completed by Aldrin Stone')
            assert(c.completionText.color[1]<c.completionText.color[3])
            assert(not c.scopeText:IsShown() and not c.otherCompletion:IsShown())
            assert(c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(c.shield.points:GetText()=='20' and c.shield.icon.coords[1]==.5)
            assert(c.nativeStatus:GetText()=='Completed via Legacy')
            assert(c.criteriaPool[1].label:GetText()=='Achievement criteria')
            assert(c.criteriaPool[2].label:GetText()=='Legacy criteria')
            ns.WrathAchievementUI.ShieldEnter(c.shield)
            assert(tooltipLines[1]=='Achievement Points: 20' and tooltipLines[2]=='Legacy Points: 1')
            assert(tooltipLines[3]=='Legacy completed' and tooltipLines[4]=='Completed by Aldrin Stone')
            assert(custom.completed==false and native.completed==true and saved.done.second==nil and #calls==0)
        """)

    def test_unknown_native_points_and_completion_do_not_gain_completion_claims(self):
        self.combined(); self.tooltip()
        self.check("""
            custom.completedByOtherCharacter=false; custom.completionDetail='Not completed on this character'
            native.completed=nil; native.pointValue=nil; native.pointType='unknown'
            native.completionDetail='Completion scope unavailable'
            nativeCriteria.available=false; nativeCriteria.complete=false; nativeCriteria.items={}
            local advance=view:MeasureCard(combined); view:RenderCard(combined,1,0)
            local c=view.cards[1]
            assert(c:GetHeight()+4==advance and not c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='')
            assert(not c.nativeCompleted and not c.saturated and not c.completionText:IsShown())
            assert(#c.criteriaPool==2 and #c.progressPool==1)
            ns.WrathAchievementUI.ShieldEnter(c.shield)
            assert(#tooltipLines==2 and tooltipLines[2]=='Legacy Points: —')
            for _,text in ipairs(tooltipLines) do
                assert(not text:find('Scope:',1,true) and not text:find('unavailable',1,true))
                assert(not text:find('completed',1,true))
            end
            assert(native.completed==nil and native.pointValue==nil and nativeCriteria.available==false)
            assert(custom.completed==false and saved.done.second==nil and #calls==0)
        """)

    def test_known_money_progress_is_amount_only_and_bar_updates_without_new_frames(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.money=true; row.achievement.money=true
            local item={name='Got My Mind On My Money',current=20000,required=50000,completed=false,
                quantityText='2g / 5g'}
            ns.LegacyPresentation.Criteria=function() return {available=true,complete=true,items={item}} end
            view.selected=row.key; view:RenderCard(row,1,0)
            local c=view.cards[1]; local count=#frames
            assert(c.progressPool[1].text:GetText()=='2g / 5g' and c.progressPool[1].value==20000)
            item.current=35000; item.quantityText='3g 50s / 5g'
            view:RenderCard(row,1,0)
            assert(c.progressPool[1].text:GetText()=='3g 50s / 5g' and c.progressPool[1].value==35000)
            assert(#frames==count and #c.progressPool==1 and saved.done.second==nil)
            assert(item.name=='Got My Mind On My Money' and item.required==50000 and #calls==0)
        """)

    def test_old_money_tracking_annotation_is_removed_only_from_rendered_text(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.money=true
            local item={name='Money looted',current=38,required=1000000,completed=false,
                quantityText='38c / 100g (since Iteration 4 tracking)'}
            ns.LegacyPresentation.Criteria=function() return {available=true,complete=true,items={item}} end
            view.selected=row.key; view:RenderCard(row,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='38c / 100g')
            assert(item.quantityText=='38c / 100g (since Iteration 4 tracking)' and item.current==38)
            item.quantityText='38c / 100g (lifetime)'; view:RenderCard(row,1,0)
            assert(view.cards[1].progressPool[1].text:GetText()=='38c / 100g')
            assert(item.quantityText=='38c / 100g (lifetime)' and #calls==0)
        """)

    def test_unknown_money_uses_missing_value_marker_without_zero_bar(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.achievement.money=true
            ns.FA.Money=function(v) assert(v==1000000); return '100g' end
            local item={name='Quest earnings',current=nil,required=1000000,completed=nil,
                quantityText='Unavailable / 100g (lifetime quest total unsupported)'}
            ns.LegacyPresentation.Criteria=function() return {available=false,complete=false,items={item}} end
            view.selected=row.key; view:RenderCard(row,1,0); local c=view.cards[1]
            assert(#c.progressPool==0 and #c.criteriaPool==1)
            assert(c.criteriaPool[1].label:GetText()=='— / 100g' and not c.criteriaPool[1].check:IsShown())
            assert(item.current==nil and item.completed==nil and not c.saturated and saved.done.second==nil)
            item.quantityText='— / 100g'; view:RenderCard(row,1,0)
            assert(c.criteriaPool[1].label:GetText()=='— / 100g' and #calls==0)
        """)

    def test_criteria_checkmarks_are_adjacent_to_consistently_left_aligned_labels(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            ns.LegacyPresentation.Criteria=function() return {available=true,complete=true,items={
                {name='Rabbit',completed=true},{name='Squirrel',completed=false},{name='Cat',completed=nil}}} end
            view.selected=row.key; view:RenderCard(row,1,0); local c=view.cards[1]
            local left
            for index,f in ipairs(c.criteriaPool) do
                assert(f.label.justify=='LEFT')
                local point,relative,relativePoint,x,y=f.label:GetPoint()
                assert(point=='LEFT' and relative==f.check and relativePoint=='RIGHT' and x==4 and y==0)
                local checkPoint,checkRelative,checkRelativePoint,checkX,checkY=f.check:GetPoint()
                assert(checkPoint=='LEFT' and checkRelative==f and checkRelativePoint=='LEFT' and checkX==0 and checkY==0)
                if not left then left=f.label:GetLeft() else assert(f.label:GetLeft()==left) end
                assert(f.check:IsShown()==(index==1))
            end
            assert(c.criteriaPool[1].label:GetText()=='Rabbit' and c.criteriaPool[3].label:GetText()=='Cat' and #calls==0)
        """)

    def test_linked_criteria_checkmark_is_between_icon_and_left_aligned_name(self):
        self.check("""
            local row=view.model.byKey['custom:second']
            ns.LegacyPresentation.Criteria=function() return {available=true,complete=true,items={
                {name='First custom',link='custom:first',completed=true}}} end
            view.selected=row.key; view:RenderCard(row,1,0); local f=view.cards[1].metaPool[1]
            assert(f.label.justify=='LEFT' and f.check:IsShown())
            local point,relative,relativePoint,x,y=f.check:GetPoint()
            assert(point=='RIGHT' and relative==f.label and relativePoint=='LEFT' and x==-4 and y==0)
            assert(f.check:GetLeft()>=f:GetLeft() and f.check:GetRight()+4==f.label:GetLeft())
            assert(f.link=='custom:first' and f.label:GetText()=='First custom' and #calls==0)
        """)

    def test_dense_combined_criteria_share_budget_and_measure_exact_render_height(self):
        self.combined()
        self.check("""
            customCriteria.items={}; nativeCriteria.items={}
            for i=1,300 do
                customCriteria.items[i]={name='Critter '..i,completed=i%2==0}
                nativeCriteria.items[i]={name='Legacy objective '..i,completed=nil}
            end
            customCriteria.complete=false; nativeCriteria.available=false
            combined.description=string.rep('A long achievement description. ',30)
            local advance=view:MeasureCard(combined); view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c:GetHeight()+4==advance and #c.criteriaPool==260 and #c.metaPool==0)
            local objectiveCount,moreCount=0,0
            for _,f in ipairs(c.criteriaPool) do if f:IsShown() then
                if f.label:GetText():find('Critter ',1,true)==1 then objectiveCount=objectiveCount+1 end
                if f.label:GetText()=='More objectives…' then moreCount=moreCount+1 end
                assert(not f.label:GetText():find('unavailable',1,true))
            end end
            assert(objectiveCount==256 and moreCount==2)
            local framesCount=#frames; for i=1,15 do view:RenderCard(combined,1,0) end
            assert(#frames==framesCount and #c.criteriaPool==260)
            assert(customCriteria.items[300] and nativeCriteria.items[300] and #calls==0)
        """)

    def test_missing_criteria_do_not_expand_to_a_developer_status_paragraph(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.completed=nil
            ns.LegacyPresentation.Criteria=function() return {available=false,complete=false,items={}} end
            view.selected=row.key
            local advance=view:MeasureCard(row); view:RenderCard(row,1,0); local c=view.cards[1]
            assert(c:GetHeight()+4==advance and c:GetHeight()==110)
            assert(#c.criteriaPool==0 and #c.progressPool==0 and not c.completionText:IsShown())
            assert(not c.scopeText:IsShown() and not c.saturated and row.completed==nil and #calls==0)
        """)

    def test_pool_rebinding_clears_native_accent_earner_and_old_criteria(self):
        self.combined()
        self.check("""
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.completionText:IsShown() and c.nativeStatus:IsShown())
            local row=view.model.byKey['custom:first']; view.selected=nil
            view:RenderCard(row,1,0)
            assert(not c.completionText:IsShown() and not c.otherCompletion:IsShown() and not c.scopeText:IsShown())
            assert(not c.nativeStatus:IsShown() and c.characterCompleted and not c.nativeCompleted)
            assert(c.shield.icon.color[1]==1 and c.shield.icon.color[3]==1 and c:GetHeight()==84)
            for _,entries in ipairs({c.criteriaPool,c.progressPool,c.metaPool}) do
                for _,f in ipairs(entries) do assert(not f:IsShown()) end
            end
            assert(custom.completed==false and native.completed==true and saved.done.first==1730000000 and #calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
