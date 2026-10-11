"""Iteration 6 shell geometry and reusable size selector behavior.

The real owned Lua/XML callbacks run against the explicit WoW UI double.
These checks do not establish client texture rendering or in-game timing.
"""
import unittest
import xml.etree.ElementTree as ET

from test_legacy_wrath_ui import ADDON, Harness, URI


class CrestHarness(Harness):
    """Load header texture/font geometry omitted by the general client double."""
    def child(self, parent, element):
        child = super().child(parent, element)
        if parent.GetName(parent) == 'LARWrathAchievementFrameHeader':
            if element.get('file'): child.SetTexture(child, element.get('file'))
            size = element.find(URI + 'Size')
            if size is not None:
                size = size.find(URI + 'AbsDimension') if size.find(URI + 'AbsDimension') is not None else size
                child.SetSize(child, float(size.get('x', '0')), float(size.get('y', '0')))
            coordinates = element.find(URI + 'TexCoords')
            if coordinates is not None:
                child.SetTexCoord(child, *(float(coordinates.get(key)) for key in ['left', 'right', 'top', 'bottom']))
            child.SetShown(child, element.get('hidden') != 'true')
            anchor = element.find('.//' + URI + 'Anchor')
            if anchor is not None:
                offset = anchor.find(URI + 'Offset')
                if offset is not None and offset.find(URI + 'AbsDimension') is not None: offset = offset.find(URI + 'AbsDimension')
                target = anchor.get('relativeTo')
                relative = self.g[target.replace('$parent', parent.GetName(parent))] if target else parent
                child.SetPoint(child, anchor.get('point'), relative, anchor.get('relativePoint', anchor.get('point')),
                               float(offset.get('x', '0')) if offset is not None else 0,
                               float(offset.get('y', '0')) if offset is not None else 0)
        return child


class Iteration6ShellTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()
        self.h.execute("""
            GameFontNormal={name='normal'}; GameFontNormalSmall={name='small'}
            local originalObject=UIObject
            function UIObject(...)
                local object=originalObject(...)
                function object:EnableKeyboard(value) self.keyboard=value end
                function object:SetPropagateKeyboardInput(value) self.propagateKeys=value end
                return object
            end
            shellHost=CreateFrame('Frame','Iteration6ShellHost'); shellHost:SetSize(960,760)
            refreshes,resizes,chosen=0,0,{}
            function shellGuard(fn) fn() end
            shell=ns.WrathAchievementUI.Create(shellHost,shellGuard,function() refreshes=refreshes+1 end,{
                onSizePreset=function(name)
                    resizes=resizes+1; chosen[#chosen+1]=name
                    local preset=ns.WrathAchievementUI.PRESETS[name]
                    shellHost:SetSize(preset[1],preset[2]+140); shell:Fit(shellHost)
                end,
            })
            shell:SetModel(ns.LegacyPresentation.Build())
        """)

    def check(self, code):
        self.h.execute(code)

    def test_standard_is_modestly_wider_than_original_and_initializes_without_scale(self):
        self.check("""
            local u=ns.WrathAchievementUI
            assert(u.PRESETS.Compact[1]==768 and u.PRESETS.Compact[2]==500)
            assert(u.PRESETS.Standard[1]==960 and u.PRESETS.Standard[2]==620)
            assert(u.PRESETS.Large[1]==1024 and u.PRESETS.Large[2]==720)
            assert(shell.width==960 and shell.height==620 and shell.root:GetScale()==1)
            assert(shell.layoutName=='Standard' and shell.sizeButton.label:GetText()=='Standard')
            assert(#shell.sizeChoices==3 and shell.sizeChoices[2].check:IsShown())
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and refreshes==0 and #calls==0)
        """)

    def test_size_dropdown_has_arrow_upward_owned_popup_and_attached_tab_alignment(self):
        self.check("""
            assert(shell.sizeArrow.textureValue=='Interface\\\\ChatFrame\\\\UI-ChatIcon-ScrollDown-Up')
            assert(shell.sizeArrow:GetLeft()>shell.sizeButton.label:GetRight())
            assert(shell.sizeMenu:GetBottom()>shell.sizeButton:GetTop())
            assert(shell.sizeMenu:GetRight()==shell.sizeButton:GetRight())
            local _,labelY=shell.sizeButton.label:GetCenter()
            local _,arrowY=shell.sizeArrow:GetCenter()
            assert(labelY==arrowY)
            assert(shell.sizeButton:GetTop()==shell.tabs[1]:GetTop())
            assert(shell.sizeButton:GetRight()==shell.root:GetRight()-20)
            assert(shell.sizeMenu.backdrop.edgeFile==shell.filterMenu.backdrop.edgeFile)
            assert(shell.sizeMenu.backdrop.bgFile==shell.filterMenu.backdrop.bgFile)
        """)

    def test_size_popup_reopens_without_allocation_catalog_build_or_refresh(self):
        self.check("""
            local originalFrames,model=#frames,shell.model
            ns.LegacyPresentation.Build=function() error('Popup rebuilt catalog') end
            local originalRender=shell.Render
            shell.Render=function() error('Opening popup rendered content') end
            for i=1,150 do
                shell.sizeButton:Fire('OnClick')
                assert(shell.sizeMenu:IsShown() and shell.sizeDismiss:IsShown())
                assert(shell.sizeMenu.keyboard and shell.sizeMenu.propagateKeys)
                shell.sizeButton:Fire('OnClick')
                assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
            end
            shell.Render=originalRender
            assert(#frames==originalFrames and shell.model==model and resizes==0 and refreshes==0 and #calls==0)
        """)

    def test_every_size_choice_uses_direct_callback_and_current_choice_is_noop(self):
        self.check("""
            for i,name in ipairs({'Compact','Standard','Large'}) do
                shell.sizeButton:Fire('OnClick'); shell.sizeChoices[i]:Fire('OnClick')
                assert(chosen[#chosen]==name and shell.layoutName==name)
                assert(shell.sizeButton.label:GetText()==name)
                assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
                local before=resizes
                shell.sizeButton:Fire('OnClick'); shell.sizeChoices[i]:Fire('OnClick')
                assert(resizes==before and not shell.sizeMenu:IsShown())
                for j,option in ipairs(shell.sizeChoices) do assert(option.check:IsShown()==(i==j)) end
            end
            assert(resizes==3 and refreshes==0 and #calls==0)
            assert(saved.done.first==1730000000 and saved.history[1]=='keep')
        """)

    def test_filter_and_size_popups_are_mutually_exclusive(self):
        self.check("""
            shell.filterButton:Fire('OnClick'); assert(shell.filterMenu:IsShown())
            shell.sizeButton:Fire('OnClick')
            assert(shell.sizeMenu:IsShown() and not shell.filterMenu:IsShown() and not shell.filterDismiss:IsShown())
            shell.filterButton:Fire('OnClick')
            assert(shell.filterMenu:IsShown() and not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
            shell.sizeButton:Fire('OnClick'); shell.sizeDismiss:Fire('OnClick')
            assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
            assert(refreshes==0 and resizes==0 and #calls==0)
        """)

    def test_escape_closes_size_menu_and_keyboard_continues_propagating(self):
        self.check("""
            shell.sizeButton:Fire('OnClick'); shell.sizeMenu:Fire('OnKeyDown','SPACE')
            assert(shell.sizeMenu:IsShown() and shell.sizeMenu.propagateKeys)
            shell.sizeMenu:Fire('OnKeyDown','ESCAPE')
            assert(not shell.sizeMenu:IsShown() and not shell.sizeMenu.keyboard and not shell.sizeMenu.propagateKeys)
            shell.sizeButton:Fire('OnClick'); shell.searchBox:Fire('OnEscapePressed')
            assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
            assert(shell.layoutName=='Standard' and shell.filter=='All' and resizes==0)
        """)

    def test_popup_dismisses_on_tabs_render_and_root_hide_without_losing_selection(self):
        self.check("""
            for _,tab in ipairs({'rewards','trees','statistics','achievements'}) do
                shell.sizeButton:Fire('OnClick'); shell:SetTab(tab)
                assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
                assert(shell.sizeButton.label:GetText()=='Standard')
            end
            shell.sizeButton:Fire('OnClick'); shell:Render()
            assert(not shell.sizeMenu:IsShown())
            shell.sizeButton:Fire('OnClick'); shell.root:Hide(); shell.root:Show()
            assert(not shell.sizeMenu:IsShown() and not shell.sizeDismiss:IsShown())
            assert(shell.layoutName=='Standard' and refreshes==0 and resizes==0 and #calls==0)
        """)

    def test_all_presets_keep_footer_controls_and_content_gutter_inside_body(self):
        self.check("""
            for _,name in ipairs({'Compact','Standard','Large'}) do
                local preset=ns.WrathAchievementUI.PRESETS[name]
                shellHost:SetSize(preset[1],preset[2]+140); shell:Fit(shellHost)
                assert(shell.sizeButton:GetLeft()>=shell.tabs[4]:GetRight()+16)
                assert(shell.filterButton:GetRight()==shell.root:GetLeft()+shell.contentLeft+shell.contentPanelWidth)
                assert(shell.contentPanelWidth-shell.contentWidth==22)
                assert(shell.contentScroll:GetRight()+22<=shell.root:GetRight()-38)
                assert(shell.root:GetScale()==1 and shell.nativeHost:GetWidth()==preset[1]-50)
                assert(shell.nativeHost:GetHeight()==preset[2]-46)
                assert(shell.searchBox:GetWidth()>100 and shell.sizeArrow:GetWidth()==16)
            end
            assert(refreshes==0 and resizes==0 and #calls==0)
        """)

    def test_roof_and_plaque_ornaments_keep_native_dimensions_and_neutral_crest(self):
        xml = ET.parse(ADDON / 'UI/WrathAchievementUI.xml').getroot()
        window = next(element for element in xml if element.get('name') == 'LARWrathWindowTemplate')
        header = window.find('.//' + URI + 'Frame[@name="$parentHeader"]')
        for suffix, width, height in [('Left', '147', '106'), ('Right', '147', '106'), ('RoofLeft', '216', '106'), ('RoofRight', '216', '106')]:
            roof = header.find('.//' + URI + f'Texture[@name="$parent{suffix}"]')
            self.assertEqual(roof.find(URI + 'Size/' + URI + 'AbsDimension').attrib, {'x': width, 'y': height})
        for prefix, offset in [('PointBorder', '-140'), ('LegacyPointBorder', '140')]:
            center = header.find('.//' + URI + f'Texture[@name="$parent{prefix}"]')
            self.assertEqual(center.find(URI + 'Size/' + URI + 'AbsDimension').attrib, {'x': '116', 'y': '39'})
            self.assertEqual(center.find('.//' + URI + 'Offset').get('x'), offset)
            self.assertEqual(center.find(URI + 'TexCoords').get('left'), '.455078125')
            self.assertEqual(center.find(URI + 'TexCoords').get('right'), '.64453125')
            for suffix in ['Left', 'Right']:
                end = header.find('.//' + URI + f'Texture[@name="$parent{prefix}{suffix}"]')
                self.assertEqual(end.find(URI + 'Size/' + URI + 'AbsDimension').attrib, {'x': '18', 'y': '39'})
                self.assertEqual(end.find('.//' + URI + 'Anchor').get('relativeTo'), '$parent' + prefix)
        crest = header.find('.//' + URI + 'Texture[@name="$parentCrest"]')
        self.assertEqual(crest.get('file'), r'Interface\AchievementFrame\UI-Achievement-Shields-NoPoints')
        self.assertEqual(crest.find(URI + 'Size').attrib, {'x': '80', 'y': '80'})


class Iteration6PresetControllerTests(unittest.TestCase):
    def test_existing_named_preferences_survive_enable_reopen_and_layout_refresh(self):
        for preference in ['Compact', 'Standard', 'Large']:
            with self.subTest(preference=preference):
                h = Harness(controller=True)
                h.execute("settings.legacyUISize='" + preference + "'")
                h.enable()
                h.execute("""
                    local c=ns.LegacyUIController
                    local name,preset=c:Preset()
                    assert(name==settings.legacyUISize and c.ui.layoutName==name)
                    assert(c.ui.root:GetWidth()==preset[1] and c.ui.root:GetHeight()==preset[2])
                    LegacySystemFrame:Hide(); LegacySystemFrame:Show(); FlushTimers()
                    c:Refresh('layout'); FlushTimers()
                    assert(settings.legacyUISize==name and c.ui.layoutName==name)
                    assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
                """)

    def test_controller_size_choices_resize_without_catalog_rebuild_or_progress_writes(self):
        h = Harness(controller=True)
        h.enable()
        h.execute("""
            local c=ns.LegacyUIController
            assert(c:Preset()=='Standard' and c.ui.layoutName=='Standard')
            local model,done,history,explored=c.ui.model,saved.done,saved.history,saved.explored
            ns.LegacyPresentation.Build=function() error('Size selector rebuilt achievement catalog') end
            for i,name in ipairs({'Compact','Standard','Large'}) do
                c.ui.sizeButton:Fire('OnClick'); c.ui.sizeChoices[i]:Fire('OnClick'); FlushTimers()
                assert(c.state=='Enabled' and c.ui.layoutName==name and settings.legacyUISize==name)
                assert(c.ui.model==model and not c.ui.sizeMenu:IsShown())
                assert(saved.done==done and saved.history==history and saved.explored==explored)
            end
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        """)


class Iteration6FactionCrestTests(unittest.TestCase):
    def make(self, api):
        h = CrestHarness()
        h.execute(api + """
            crestHost=CreateFrame('Frame','Iteration6CrestHost'); crestHost:SetSize(960,760)
            crestView=ns.WrathAchievementUI.Create(crestHost,function(fn) fn() end,function() error('Unexpected refresh') end,{})
            crest=LARWrathAchievementFrameHeaderCrest
        """)
        return h

    def test_recognized_factions_select_native_compatible_square_logos_without_scans(self):
        for faction in ['Alliance', 'Horde']:
            with self.subTest(faction=faction):
                h = self.make("factionReads=0; function UnitFactionGroup(unit) assert(unit=='player'); factionReads=factionReads+1; return '" + faction + "' end;")
                h.execute("""
                    assert(factionReads==1)
                    assert(crest:GetWidth()==50 and crest:GetHeight()==50)
                    assert(crest.coords[1]==.0625 and crest.coords[2]==.9375)
                    assert(crest.coords[3]==.0625 and crest.coords[4]==.9375)
                    local point,parent,relative,x,y=crest:GetPoint(1)
                    assert(point=='CENTER' and parent==LARWrathAchievementFrameHeaderCrestSurround and relative=='CENTER' and x==0 and y==0)
                    assert(parent:IsShown())
                    local frameCount=#frames
                    crestView:Layout(1024,720); crestView:Layout(768,500)
                    assert(factionReads==1 and #frames==frameCount and #calls==0)
                    assert(saved.done.first==1730000000 and saved.history[1]=='keep')
                """)
                self.assertEqual(h.lua.eval('crest.textureValue'), 'Interface\\Timer\\' + faction + '-Logo')

    def test_missing_unknown_nil_failing_and_secret_faction_keep_original_neutral_xml_seal(self):
        for api in [
            'UnitFactionGroup=nil;',
            'function UnitFactionGroup() return nil end;',
            "function UnitFactionGroup() return 'Neutral' end;",
            "function UnitFactionGroup() error('Unavailable') end;",
            "function UnitFactionGroup() return 'Alliance' end; function issecretvalue(value) return value=='Alliance' end;",
        ]:
            with self.subTest(api=api):
                h = self.make(api)
                h.execute("""
                    assert(crest.textureValue=='Interface\\\\AchievementFrame\\\\UI-Achievement-Shields-NoPoints')
                    assert(crest:GetWidth()==80 and crest:GetHeight()==80)
                    assert(crest.coords[1]==0 and crest.coords[2]==.5 and crest.coords[3]==0 and crest.coords[4]==.5)
                    local point,parent,relative,x,y=crest:GetPoint(1)
                    assert(point=='CENTER' and parent==LARWrathAchievementFrameHeaderCrestSurround and x==0 and y==0)
                    assert(not parent:IsShown())
                    assert(#calls==0 and saved.done.first==1730000000)
                """)

    def test_unavailable_faction_texture_restores_neutral_without_changing_its_geometry(self):
        h = self.make("""
            function UnitFactionGroup() return 'Horde' end
            local originalObject=UIObject
            function UIObject(...)
                local object=originalObject(...)
                local originalTexture=object.SetTexture
                function object:SetTexture(value)
                    if value=='Interface\\\\Timer\\\\Horde-Logo' then self.textureValue=nil; return false end
                    return originalTexture(self,value)
                end
                return object
            end
        """)
        h.execute("""
            assert(crest.textureValue=='Interface\\\\AchievementFrame\\\\UI-Achievement-Shields-NoPoints')
            assert(crest:GetWidth()==80 and crest:GetHeight()==80)
            assert(crest.coords[1]==0 and crest.coords[2]==.5 and crest.coords[4]==.5)
            assert(#calls==0 and saved.done.first==1730000000)
        """)


if __name__ == '__main__':
    unittest.main()
