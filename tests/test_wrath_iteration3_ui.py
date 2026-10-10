"""Iteration 3 UI contracts exercised with Lua 5.1 and original XML templates.

These checks cover data meaning, navigation and logical geometry. They cannot
verify rendering, client texture appearance or native game interaction.
"""
import unittest
import xml.etree.ElementTree as ET

from test_legacy_wrath_ui import ADDON, Harness, URI


class Iteration3UITests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute("""
            GameFontNormal={name='normal'}; GameFontNormalSmall={name='small'}
            GameFontHighlight={name='highlight'}
            host=CreateFrame('Frame','Iteration3Host'); host:SetSize(900,760)
            function guard(fn) fn() end
            dragStarts,positionSaves,sizeCycles=0,0,0
            view=ns.WrathAchievementUI.Create(host,guard,function() end,{
                onDragStart=function() dragStarts=dragStarts+1 end,
                onPositionSave=function(frame) assert(frame==host); positionSaves=positionSaves+1 end,
                onSizePresetCycle=function() sizeCycles=sizeCycles+1 end,
            })
            view:Fit(host); view:SetModel(ns.LegacyPresentation.Build())
            function categoryButton(key)
                for _,button in ipairs(view.categories) do
                    if button:IsShown() and button.category.key==key then return button end
                end
            end
            function cardFor(key)
                for _,card in ipairs(view.cards) do
                    if card:IsShown() and card.record.key==key then return card end
                end
            end
        """)

    def check(self, code):
        self.h.execute(code)

    def test_preset_enlargement_increases_content_without_scaling_art_or_text(self):
        self.check("""
            view:Layout(768,500)
            local compactWidth,compactHeight=view.contentScroll:GetWidth(),view.contentScroll:GetHeight()
            view:RenderCard(view.model.byKey['custom:first'],1,0)
            local compactCard,compactDescription=view.cards[1]:GetWidth(),view.cards[1].description:GetWidth()
            local roofWidth,cornerWidth=FAWrathAchievementFrameHeader:GetWidth(),FAWrathAchievementFrameMetalBorderTopLeft:GetWidth()
            host:SetSize(1024,860); view:Fit(host)
            view:RenderCard(view.model.byKey['custom:first'],1,0)
            assert(view.root:GetWidth()==1024 and view.root:GetHeight()==720 and view.root:GetScale()==1)
            assert(view.contentScroll:GetWidth()>compactWidth and view.contentScroll:GetHeight()>compactHeight)
            assert(view.cards[1]:GetWidth()>compactCard and view.cards[1].description:GetWidth()>compactDescription)
            assert(FAWrathAchievementFrameHeader:GetWidth()==roofWidth and FAWrathAchievementFrameMetalBorderTopLeft:GetWidth()==cornerWidth)
            assert(view.nativeHost:GetWidth()==974 and view.nativeHost:GetHeight()==674)
            assert(view.sizeButton.label:GetText()=='Large')
            for _,preset in pairs(ns.WrathAchievementUI.PRESETS) do
                view:Layout(preset[1],preset[2])
                assert(view.searchClear:GetRight()<view.filterButton:GetLeft())
                assert(view.searchIcon:GetLeft()>=view.root:GetLeft()+view.contentLeft)
            end
        """)

    def test_sidebar_expansion_and_parent_selection_have_separate_actions(self):
        self.check("""
            local parent=categoryButton('professions')
            assert(parent and parent.expandButton:IsShown())
            parent.expandButton:Fire('OnClick')
            assert(view.expanded.professions and view.category=='summary')
            local child=categoryButton('professions:alchemy')
            assert(child and child.depth==1 and child.points[1][4]==14)
            assert(child.label:GetFontObject()==GameFontNormalSmall and parent.label:GetFontObject()==GameFontNormal)
            assert(child.connector:IsShown() and not parent.connector:IsShown())
            child:Fire('OnClick')
            assert(view.category=='professions:alchemy' and view.expanded.professions)
            assert(categoryButton('professions:alchemy').selection:IsShown())
            assert(not categoryButton('professions').selection:IsShown())
            categoryButton('professions'):Fire('OnClick')
            assert(view.category=='professions' and view.expanded.professions)
            assert(categoryButton('professions').selection:IsShown())
            assert(not categoryButton('professions:alchemy').selection:IsShown())
            assert(#ns.LegacyPresentation.Rows(view.model,'professions')==0)
            assert(#ns.LegacyPresentation.Rows(view.model,'professions:alchemy')>0)
            local parentDone,parentTotal=ns.LegacyPresentation.Count(view.model,'professions')
            local childDone,childTotal=ns.LegacyPresentation.Count(view.model,'professions:alchemy')
            assert(parentTotal>=childTotal and parentDone>=childDone)
        """)

    def test_standard_zero_unknown_and_actual_fos_use_independent_badges(self):
        self.check("""
            local row=view.model.byKey['legacy:62053']
            row.achievementType='standard'; row.pointType='none'; row.pointValue=0
            view:RenderCard(row,1,0)
            local shield=view.cards[1].shield
            assert(shield.points:GetText()=='0' and not shield.icon.textureValue:find('NoPoints',1,true))
            assert(shield.icon.color[1]==1 and shield.icon.color[3]==1)
            row.pointType='unknown'; row.pointValue=nil; row.points=0; row.achievementType='unknown'
            view:RenderCard(row,1,0)
            assert(shield.points:GetText()=='?' and not shield.icon.textureValue:find('NoPoints',1,true))
            row.achievementType='feat_of_strength'; row.pointType='none'; row.pointValue=0
            view:RenderCard(row,1,0)
            assert(shield.icon.textureValue:find('NoPoints',1,true) and shield.points:GetText()=='')
            row.pointType='legacy'; row.pointValue=3
            view:RenderCard(row,1,0)
            assert(shield.icon.textureValue:find('NoPoints',1,true) and shield.points:GetText()=='3')
        """)

    def test_awarded_legacy_shield_is_distinct_and_pool_returns_to_character_colors(self):
        self.check("""
            view:RenderCard(view.model.byKey['legacy:62013'],1,0)
            local shield=view.cards[1].shield
            assert(shield.icon.color[1]<shield.icon.color[3])
            assert(shield.points.color[1]==1 and shield.points.color[2]==.82)
            view:RenderCard(view.model.byKey['custom:first'],1,0)
            assert(shield.icon.color[1]==1 and shield.icon.color[2]==1 and shield.icon.color[3]==1)
            assert(shield.points.color[1]==1 and shield.points.color[2]==1)
            assert(shield.points:GetText()=='10')
        """)

    def test_shield_tooltip_reports_source_scope_type_and_exact_point_system(self):
        self.check("""
            tooltipLines={}
            GameTooltip={SetOwner=function() end,SetText=function(_,text) tooltipTitle=text end,
                AddLine=function(_,text) tooltipLines[#tooltipLines+1]=text end,Show=function() end}
            local row=view.model.byKey['legacy:62053']
            row.achievementType='standard'; row.pointType='none'; row.pointValue=0; row.scopeType='account'
            view:RenderCard(row,1,0); ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(tooltipTitle=='No point reward' and tooltipLines[1]=='0')
            assert(tooltipLines[2]=='Source: Native Legacy Challenge' and tooltipLines[3]=='Scope: Account')
            for _,line in ipairs(tooltipLines) do assert(line~='Feat of Strength') end
            row.pointType='legacy'; row.pointValue=5; row.achievementType='feat_of_strength'
            tooltipLines={}; view:RenderCard(row,1,0); ns.WrathAchievementUI.ShieldEnter(view.cards[1].shield)
            assert(tooltipTitle=='Legacy Points' and tooltipLines[1]=='5' and tooltipLines[4]=='Feat of Strength')
            assert(#calls==0)
        """)

    def test_expanded_scope_is_subtle_and_criterion_width_grows(self):
        self.check("""
            local row=view.model.byKey['custom:second']; row.scopeType='account'
            view.selected=row.key; view:Layout(768,500); view:RenderCard(row,1,0)
            local card=view.cards[1]
            assert(card.scopeText:IsShown() and card.scopeText:GetText()=='Scope: Account')
            local narrow=card.progressPool[1]:GetWidth()
            view:Layout(1024,720); view:RenderCard(row,1,0)
            assert(card.progressPool[1]:GetWidth()>narrow)
            assert(card.scopeText:GetWidth()==card.description:GetWidth())
            view.selected=nil; view:RenderCard(row,1,0)
            assert(not card.scopeText:IsShown())
        """)

    def test_summary_merges_reliable_recents_once_and_keeps_points_in_roof(self):
        self.check("""
            local native=view.model.byKey['legacy:62013']
            native.completed=true; native.date='10/28/24'; native.dateSort=20241028
            local undated=view.model.byKey['legacy:62382']; undated.completed=true; undated.date=nil; undated.dateSort=nil
            -- This fixture intentionally edits the existing presentation snapshot.
            ns.LegacyPresentation.Invalidate(view.model)
            view:Render()
            local recentHeadings=0
            for _,heading in ipairs(view.headings) do
                if heading:IsShown() then
                    if heading:GetText()=='Recent Achievements' then recentHeadings=recentHeadings+1 end
                    assert(not heading:GetText():find('Character Achievement Points:',1,true))
                    assert(not heading:GetText():find('Legacy Points:',1,true))
                    assert(not heading:GetText():find('Recent Character',1,true))
                    assert(not heading:GetText():find('Recent Legacy',1,true))
                end
            end
            assert(recentHeadings==1 and view.cards[1].record.key==native.key)
            assert(cardFor('custom:first') and not cardFor(undated.key))
            assert(view.bars[1].text:GetText()=='1/2' and view.bars[2].text:GetText()=='2/3')
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=='10')
        """)

    def test_search_placeholder_clear_and_source_filters_keep_native_state_read_only(self):
        self.check("""
            assert(view.searchHint:IsShown() and view.searchHint:GetText()=='Search achievements...')
            assert(view.searchIcon:IsShown() and not view.searchClear:IsShown())
            view.searchBox:SetText('Alchemy'); view.searchBox:Fire('OnTextChanged')
            assert(not view.searchHint:IsShown() and view.searchClear:IsShown())
            local found=false
            for _,card in ipairs(view.cards) do if card:IsShown() and card.record.key=='legacy:62013' then found=true end end
            assert(found)
            for i=1,3 do view.filterButton:Fire('OnClick') end
            assert(view.filter=='Character Achievements')
            view.searchClear:Fire('OnClick')
            assert(view.search=='' and view.filter=='All' and view.searchBox:GetText()=='' and view.searchHint:IsShown())
            assert(not view.searchClear:IsShown() and #calls==0)
        """)

    def test_statistics_has_actual_headers_zero_unknown_and_original_zebra(self):
        self.check("""
            saved.critters={}; saved.books=nil
            view:SetTab('statistics',false)
            assert(view.categoryScroll:IsShown() and not view.searchBox:IsShown())
            assert(categoryButton('stats:misc'))
            categoryButton('stats:misc'):Fire('OnClick')
            local zero,unknown,header,odd,even
            for _,row in ipairs(view.stats) do
                if row:IsShown() then
                    if row.isHeader then header=row
                    elseif row.record.key=='statistic:tracked:critters' then zero=row
                    elseif row.record.key=='statistic:tracked:books' then unknown=row end
                    if not row.isHeader then if not odd then odd=row else even=row end end
                end
            end
            assert(header and header.title:GetText()=='Miscellaneous' and header.headerLeft:IsShown())
            assert(zero and zero.value:GetText()=='0' and unknown and unknown.value:GetText()=='Unavailable')
            assert(odd.bG:IsShown() and odd.bG.coords[3]==.1875 and odd.bG:GetBlendMode()=='BLEND' and odd.bG:GetAlpha()==1)
            assert(even.bG.coords[3]==.375 and even.bG:GetBlendMode()=='ADD' and even.bG:GetAlpha()==.5)
            assert(#calls==0)
        """)

    def test_achievement_and_statistics_navigation_survive_switch_and_refresh_independently(self):
        self.check("""
            view.expanded.professions=true; view.category='professions:alchemy'
            view.search='Alchemy'; view.filter='Legacy Challenges'; view:Render()
            view:SetTab('statistics',false)
            view.statisticsExpanded['stats:character']=true
            view.statisticsCategory='stats:character/consumables'; view:Render()
            view:SetModel(ns.LegacyPresentation.Build())
            assert(view.statisticsCategory=='stats:character/consumables' and view.statisticsExpanded['stats:character'])
            view:SetTab('achievements',false)
            assert(view.category=='professions:alchemy' and view.expanded.professions)
            assert(view.search=='Alchemy' and view.filter=='Legacy Challenges')
            view:SetTab('statistics',false)
            assert(view.statisticsCategory=='stats:character/consumables' and view.statisticsExpanded['stats:character'])
        """)

    def test_resizing_and_filtering_clamp_scroll_before_rendering_visible_pool(self):
        self.check("""
            local m=view.model; m.records={}
            for i=1,100 do m.records[i]={key='custom:wide'..i,source='custom',category='general',
                name='Wide '..i,description='',completed=false,pointValue=10,pointType='character',achievementType='standard'} end
            view.category='general'; view:Render(); view.contentScroll:SetVerticalScroll(8700)
            view:Layout(1024,720)
            assert(view.contentScroll:GetVerticalScroll()<=view.contentChild:GetHeight()-view.contentScroll:GetHeight())
            local shown=0
            for _,card in ipairs(view.cards) do if card:IsShown() then shown=shown+1 end end
            assert(shown>0 and #view.cards<15)
            view.search='No such achievement'; view:Render()
            assert(view.contentScroll:GetVerticalScroll()==0 and view.contentChild:GetHeight()==view.contentScroll:GetHeight())
        """)

    def test_tab_scroll_offsets_restore_independently_with_bounded_statistics_pool(self):
        self.check("""
            view.model.records={}
            for i=1,100 do view.model.records[i]={key='custom:long'..i,source='custom',category='general',
                name='Long '..i,description='',completed=false,pointValue=10,pointType='character'} end
            view.category='general'; view:Render(); view.contentScroll:SetVerticalScroll(1500)
            ns.STATS={{title='SOCIAL',list={}}}
            for i=1,100 do ns.STATS[1].list[i]={900000+i,'Observed stat '..i} end
            function GetStatistic() return '0' end
            view:SetTab('statistics',false); view.statisticsCategory='stats:misc'; view:Render()
            view.contentScroll:SetVerticalScroll(600)
            assert(#view.stats<28)
            view:SetTab('achievements',false)
            assert(view.category=='general' and view.contentScroll:GetVerticalScroll()==1500)
            view:SetTab('statistics',false)
            assert(view.statisticsCategory=='stats:misc' and view.contentScroll:GetVerticalScroll()==600)
            assert(#calls==0)
        """)

    def test_owner_drag_and_preset_control_report_callbacks(self):
        self.check("""
            FAWrathAchievementFrameHeader:Fire('OnDragStart')
            assert(host.moving and dragStarts==1)
            FAWrathAchievementFrameHeader:Fire('OnDragStop')
            assert(not host.moving and positionSaves==1)
            view.sizeButton:Fire('OnClick'); assert(sizeCycles==1)
        """)

    def test_native_views_use_only_native_page_backgrounds(self):
        self.check("""
            for _,tab in ipairs({'rewards','trees'}) do
                view:SetTab(tab,false)
                assert(view.nativeHost:IsShown() and not view.nativeBackground:IsShown() and not view.contentBackground:IsShown())
                assert(not FAWrathAchievementFrameCategoriesBG:IsShown() and not view.contentScroll:IsShown())
            end
        """)

    def test_matched_roof_counters_are_balanced_and_do_not_share_regions(self):
        root = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        window = next(e for e in root if e.get("name") == "FAWrathWindowTemplate")
        borders = [e for e in window.iter(URI + "Texture") if e.get("name") in ("$parentPointBorder", "$parentLegacyPointBorder")]
        offsets = [e.find(".//" + URI + "Offset").get("x") for e in borders]
        self.assertEqual(offsets, ["-115", "115"])
        self.assertEqual(borders[0].find(URI + "Size/" + URI + "AbsDimension").attrib,
                         borders[1].find(URI + "Size/" + URI + "AbsDimension").attrib)
        self.check("""
            view.model.custom.points=nil; view.model.native.points=nil; view:SetModel(view.model)
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=='Unavailable')
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText()=='Unavailable')
        """)


if __name__ == "__main__":
    unittest.main()
