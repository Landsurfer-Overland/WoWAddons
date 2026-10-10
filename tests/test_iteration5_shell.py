"""Iteration 5 owned shell/dropdown behavior with the real Lua/XML callbacks.

Geometry, read-only APIs and bounded allocation are checked here. These tests
cannot establish client texture availability, screenshot appearance or taint.
"""
import subprocess
import unittest
import xml.etree.ElementTree as ET

from test_legacy_wrath_ui import ADDON, Harness, ROOT, URI


class Iteration5ShellTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute("""
            GameFontNormal={name='normal'}; GameFontNormalSmall={name='small'}
            GameFontHighlight={name='highlight'}
            local originalObject=UIObject
            function UIObject(...)
                local object=originalObject(...)
                function object:EnableKeyboard(enabled) self.keyboard=enabled end
                function object:SetPropagateKeyboardInput(enabled) self.propagateKeys=enabled end
                return object
            end
            host=CreateFrame('Frame','Iteration5ShellHost'); host:SetSize(1024,860)
            refreshCalls,resizeCalls=0,0
            function guard(fn) fn() end
            view=ns.WrathAchievementUI.Create(host,guard,function() refreshCalls=refreshCalls+1 end,{
                onSizePresetCycle=function() resizeCalls=resizeCalls+1 end,
            })
            view:SetModel(ns.LegacyPresentation.Build())
        """)

    def check(self, code):
        self.h.execute(code)

    def test_large_initial_layout_restores_original_connecting_wood_backdrop(self):
        self.check("""
            assert(view.root:GetWidth()==1024 and view.root:GetHeight()==720)
            assert(view.layoutName=='Large' and view.sizeButton.label:GetText()=='Large')
            assert(view.root:GetScale()==1 and view.root.backdrop.edgeSize==64 and view.root.backdrop.tileEdge)
            assert(view.root.backdrop.edgeFile=='Interface\\\\AchievementFrame\\\\UI-Achievement-WoodBorder')
            assert(#view.tabs==4 and view.tabs[1].view=='achievements' and view.tabs[2].view=='rewards')
            assert(view.tabs[3].view=='trees' and view.tabs[4].view=='statistics')
            assert(view.tabs[1]:GetText()=='Achievements' and view.tabs[2]:GetText()=='Legacy Rewards')
            assert(view.tabs[3]:GetText()=='Legacy Trees' and view.tabs[4]:GetText()=='Statistics')
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        """)

    def test_controls_and_footer_remain_aligned_without_overlapping_at_each_preset(self):
        self.check("""
            for name,preset in pairs(ns.WrathAchievementUI.PRESETS) do
                host:SetSize(preset[1],preset[2]+140); view:Fit(host)
                local rootLeft=view.root:GetLeft()
                assert(view.root:GetHeight()==preset[2] and view.root:GetScale()==1)
                assert(view.searchBox:GetLeft()==rootLeft+view.contentLeft)
                assert(view.searchIcon:GetLeft()>view.searchBox:GetLeft())
                assert(view.searchClear:GetRight()<view.searchBox:GetRight())
                assert(view.filterButton:GetLeft()-view.searchBox:GetRight()==12)
                assert(view.filterButton:GetRight()==rootLeft+view.contentLeft+view.contentWidth)
                local _, searchCenter=view.searchBox:GetCenter()
                local _, filterCenter=view.filterButton:GetCenter()
                assert(searchCenter==filterCenter)
                assert(view.searchHint:GetWidth()>0 and view.notice:GetHeight()==14)
                assert(view.tabs[1]:GetLeft()==rootLeft+20)
                for i=2,#view.tabs do
                    assert(view.tabs[i]:GetLeft()-view.tabs[i-1]:GetRight()==3)
                    assert(view.tabs[i]:GetTop()==view.tabs[1]:GetTop())
                end
                assert(view.sizeButton:GetLeft()>view.tabs[4]:GetRight()+20)
                local _,_,_,_,offset=view.root:GetPoint(1)
                assert(offset==-82 and view.sizeButton.label:GetText()==name)
                assert(view.nativeHost:GetWidth()==preset[1]-50 and view.nativeHost:GetHeight()==preset[2]-46)
                assert(FAWrathAchievementFrameCategoriesBG.coords[2]==view.contentBackground.coords[1])
                assert(FAWrathAchievementFrameCategoriesBG.coords[1]==0 and view.contentBackground.coords[2]==1)
            end
            assert(#calls==0 and refreshCalls==0)
        """)

    def test_open_close_reuses_five_owned_options_without_refresh_or_model_rebuild(self):
        self.check("""
            local frameCount,model=#frames,view.model
            local providerReads,renderCalls=0,0
            ns.LegacyPresentation.Build=function() providerReads=providerReads+1; error('Unexpected catalog build') end
            local originalRender=view.Render
            view.Render=function(...) renderCalls=renderCalls+1; return originalRender(...) end
            for i=1,200 do
                view.filterButton:Fire('OnClick')
                assert(view.filterMenu:IsShown() and view.filterDismiss:IsShown() and view.filter=='All')
                assert(view.filterMenu.keyboard and view.filterMenu.propagateKeys)
                view.filterDismiss:Fire('OnClick')
                assert(not view.filterMenu:IsShown() and not view.filterDismiss:IsShown() and not view.filterMenu.keyboard)
            end
            assert(#view.filterChoices==5 and #frames==frameCount and view.model==model)
            assert(renderCalls==0 and providerReads==0 and refreshCalls==0 and #calls==0)
        """)

    def test_each_dropdown_choice_keeps_existing_filter_semantics_and_renders_once(self):
        self.check("""
            local expected={'All','Completed','Incomplete','Character Achievements','Legacy Challenges'}
            local renders,original=0,view.Render
            view.Render=function(...) renders=renders+1; return original(...) end
            for i,filter in ipairs(expected) do
                local before=renders
                view.filterButton:Fire('OnClick'); assert(view.filterMenu:IsShown())
                view.filterChoices[i]:Fire('OnClick')
                assert(view.filter==filter and view.filterButton.label:GetText()==filter)
                assert(renders==before+1 and not view.filterMenu:IsShown() and not view.filterDismiss:IsShown())
                for j,choice in ipairs(view.filterChoices) do assert(choice.check:IsShown()==(i==j)) end
            end
            assert(refreshCalls==0 and #calls==0)
        """)

    def test_clear_resets_search_choice_and_closes_popup_without_extra_refresh(self):
        self.check("""
            view.filterChoices[4]:Fire('OnClick')
            view.searchBox:SetText('First'); view.searchBox:Fire('OnTextChanged',false)
            view.filterButton:Fire('OnClick'); assert(view.filterMenu:IsShown())
            view.searchClear:Fire('OnClick')
            assert(view.search=='' and view.searchBox:GetText()=='' and view.filter=='All')
            assert(view.filterButton.label:GetText()=='All' and view.filterChoices[1].check:IsShown())
            for i=2,5 do assert(not view.filterChoices[i].check:IsShown()) end
            assert(not view.filterMenu:IsShown() and not view.filterDismiss:IsShown())
            assert(not view.searchClear:IsShown() and view.searchHint:IsShown())
            assert(refreshCalls==0 and #calls==0)
        """)

    def test_escape_dismisses_menu_and_other_keyboard_input_still_propagates(self):
        self.check("""
            view.filterButton:Fire('OnClick')
            view.filterMenu:Fire('OnKeyDown','A')
            assert(view.filterMenu:IsShown() and view.filterMenu.propagateKeys)
            view.filterMenu:Fire('OnKeyDown','ESCAPE')
            assert(not view.filterMenu:IsShown() and not view.filterMenu.propagateKeys)
            assert(not view.filterMenu.keyboard and not view.filterDismiss:IsShown())
            view.filterButton:Fire('OnClick'); assert(view.filterMenu.propagateKeys)
            view.searchBox:Fire('OnEscapePressed')
            assert(not view.filterMenu:IsShown() and not view.filterDismiss:IsShown())
            assert(view.filter=='All' and refreshCalls==0 and #calls==0)
        """)

    def test_switching_to_each_other_tab_and_hiding_shell_dismisses_popup(self):
        self.check("""
            for _,target in ipairs({'rewards','trees','statistics'}) do
                view:SetTab('achievements'); view.filterButton:Fire('OnClick')
                assert(view.filterMenu:IsShown())
                view:SetTab(target)
                assert(not view.filterMenu:IsShown() and not view.filterDismiss:IsShown())
                assert(not view.filterButton:IsShown())
            end
            view:SetTab('achievements'); view.filterButton:Fire('OnClick'); view.root:Hide()
            assert(not view.filterMenu:IsShown() and not view.filterDismiss:IsShown())
            view.root:Show(); assert(not view.filterMenu:IsShown())
            assert(refreshCalls==0 and #calls==0)
        """)

    def test_header_has_balanced_titles_crest_and_original_unscaled_art_regions(self):
        xml = ET.parse(ADDON / 'UI/WrathAchievementUI.xml').getroot()
        window = next(element for element in xml if element.get('name') == 'FAWrathWindowTemplate')
        self.assertEqual(window.get('inherits'), 'BackdropTemplate')
        header = window.find('.//' + URI + 'Frame[@name="$parentHeader"]')
        self.assertEqual(header.find(URI + 'Size/' + URI + 'AbsDimension').get('y'), '118')
        for suffix, width, height in [('Left', '512', '106'), ('Right', '215', '100')]:
            region = header.find('.//' + URI + f'Texture[@name="$parent{suffix}"]')
            size = region.find(URI + 'Size/' + URI + 'AbsDimension')
            self.assertEqual((size.get('x'), size.get('y')), (width, height))
        for suffix, x in [('PointBorder', '-174'), ('LegacyPointBorder', '174')]:
            plaque = header.find('.//' + URI + f'Texture[@name="$parent{suffix}"]')
            self.assertEqual(plaque.find('.//' + URI + 'Offset').get('x'), x)
        titles = [header.find('.//' + URI + f'FontString[@name="$parent{suffix}"]')
                  for suffix in ['Title', 'LegacyTitle']]
        self.assertEqual([title.get('text') for title in titles], ['Achievement Points', 'Legacy Points'])
        self.assertEqual([title.get('inherits') for title in titles], ['GameFontNormalLarge'] * 2)
        crest = header.find('.//' + URI + 'Texture[@name="$parentCrest"]')
        self.assertEqual(crest.get('file'), r'Interface\AchievementFrame\UI-Achievement-Shields-NoPoints')
        self.assertEqual(crest.find(URI + 'Size').attrib, {'x': '66', 'y': '64'})
        self.assertEqual(crest.find(URI + 'TexCoords').attrib,
                         {'left': '0', 'right': '.5', 'top': '0', 'bottom': '.5'})

    def test_page_backgrounds_share_a_parchment_source_and_footer_has_real_backing(self):
        xml = ET.parse(ADDON / 'UI/WrathAchievementUI.xml').getroot()
        window = next(element for element in xml if element.get('name') == 'FAWrathWindowTemplate')
        page = window.find('.//' + URI + 'Texture[@name="$parentPageParchment"]')
        categories = window.find('.//' + URI + 'Texture[@name="$parentCategoriesBG"]')
        self.assertEqual(page.get('file'), categories.get('file'))
        self.assertEqual(page.find(URI + 'TexCoords').attrib, categories.find(URI + 'TexCoords').attrib)
        self.assertEqual(page.get('file'), r'Interface\AchievementFrame\UI-Achievement-AchievementBackground')
        footer = window.find('.//' + URI + 'Texture[@name="$parentFooterBacking"]')
        anchors = footer.find(URI + 'Anchors')
        self.assertEqual(anchors[0].get('relativePoint'), 'BOTTOMLEFT')
        self.assertEqual(anchors[1].find(URI + 'Offset').get('y'), '-57')

    def test_template_generator_reproduces_committed_xml_and_leaves_reference_unchanged(self):
        output = ADDON / 'UI/WrathAchievementUI.xml'
        reference = ROOT / 'References/WrathAchievementUI/Blizzard_AchievementUI.xml'
        before, original = output.read_bytes(), reference.read_bytes()
        subprocess.run(['python', '-B', str(ROOT / 'tools/adapt_wrath_templates.py')],
                       cwd=ROOT, check=True, capture_output=True)
        self.assertEqual(output.read_bytes(), before)
        self.assertEqual(reference.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
