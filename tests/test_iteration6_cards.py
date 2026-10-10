"""Explicit card states, complementary client-art masks and pooled reuse.

These tests exercise actual Lua/XML code and binary mask assets. They establish
state/data/geometry contracts, not native client rendering or texture alignment.
"""
import struct
import unittest
import xml.etree.ElementTree as ET

import test_wrath_iteration3_ui as iteration3
import test_iteration4_ui as iteration4
from test_legacy_wrath_ui import ADDON, URI


class Iteration6CardTests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check
    combined = iteration4.Iteration4UITests.combined

    def tooltip(self):
        self.check("""
            tooltipLines={}; GameTooltip={SetOwner=function() end,
                SetText=function(_,text) tooltipTitle=text end,
                AddLine=function(_,text) tooltipLines[#tooltipLines+1]=text end,Show=function() end}
        """)

    def test_explicit_state_precedence_uses_character_component_and_verified_booleans(self):
        self.combined()
        self.check("""
            local visual=ns.WrathAchievementUI.CardVisualState
            assert(visual(combined)=='legacy-complete')
            native.completed=nil; assert(visual(combined)=='incomplete')
            native.completed=false; custom.completed=nil; assert(visual(combined)=='incomplete')
            native.completed=true; assert(visual(combined)=='legacy-complete')
            custom.completed=true; combined.completed=false; assert(visual(combined)=='character-complete')
            native.completed=false; assert(visual(combined)=='character-complete')
            combined.completed=true; custom.completed=false; assert(visual(combined)=='incomplete')
            assert(visual(native)=='native-incomplete')
            native.completed=true; assert(visual(native)=='native-complete')
            assert(saved.done.second==nil and view.model.custom.points==10 and view.model.native.points==16)
        """)

    def test_incomplete_card_keeps_original_gray_card_shield_and_laurel(self):
        self.combined()
        self.check("""
            native.completed=false; view.selected=nil; view:RenderCard(combined,1,0)
            local c=view.cards[1]
            assert(c.visualState=='incomplete' and not c.saturated and not c.characterCompleted and not c.nativeCompleted)
            assert(c.background.textureValue:find('Desaturated',1,true))
            assert(c.shield.icon.coords[1]==.5 and c.shield.wreath.coords[1]==.5)
            assert(c.shield.icon.color[1]==1 and c.shield.wreath.color[1]==1)
            assert(c.shield.points.color[1]==.65 and c.borderColor[1]==c.borderColor[3])
            assert(not c.nativeStatus:IsShown() and not c.dateCompleted:IsShown())
            assert(c.shield.points:GetText()=='20' and saved.done.second==nil and #calls==0)
        """)

    def test_legacy_completion_colors_only_separate_laurel_and_never_custom_points(self):
        self.combined()
        self.check("""
            view.selected=nil; view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.visualState=='legacy-complete' and not c.saturated and not c.characterCompleted)
            assert(c.background.textureValue:find('Desaturated',1,true) and c.shield.icon.coords[1]==.5)
            assert(c.shield.points:GetText()=='20' and c.shield.points.color[1]==.65)
            assert(c.shield.icon.color[1]==1 and c.shield.icon.color[2]==1 and c.shield.icon.color[3]==1)
            assert(c.shield.wreath.color[1]==.35 and c.shield.wreath.color[3]==.95)
            assert(c.shield.wreath:IsShown() and c.shield.separateWreath)
            assert(c.nativeStatus:GetText()=='Completed via Legacy' and c.nativeStatus:IsShown())
            -- This fixture does not import XML anchors, and ShieldOnLoad's
            -- actual points FontString occupies its double's anchor-table key.
            -- Verify the real production anchors directly; XML below verifies
            -- the shield's top-right inset and dimensions.
            local point,relative,relativePoint,x,y=c.nativeStatus:GetPoint()
            assert(point=='BOTTOMRIGHT' and relative==c and relativePoint=='BOTTOMRIGHT' and x==-90 and y==6)
            local datePoint,dateRelative,dateRelativePoint,dateX=c.dateCompleted:GetPoint()
            assert(datePoint=='TOP' and dateRelative==c.shield and dateRelativePoint=='BOTTOM' and dateX==-3)
            assert(c.dateCompleted:GetWidth()==78 and c.nativeStatus:GetWidth()==c.description:GetWidth())
            assert(not c.dateCompleted:IsShown() and c.dateCompleted:GetText()=='')
            assert(c.borderColor[1]==c.borderColor[3] and c.glow.color[1]==.22)
            assert(custom.completed==false and native.completed==true and saved.done.second==nil)
            assert(view.model.custom.points==10 and view.model.native.points==16 and #calls==0)
        """)

    def test_current_character_completion_selects_gold_and_actual_custom_date(self):
        self.combined()
        self.check("""
            custom.completed=true; custom.date='10/09/26'; combined.date='Stale outer date'; combined.completed=false
            native.completed=false; view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.visualState=='character-complete' and c.saturated and c.characterCompleted and not c.nativeCompleted)
            assert(not c.background.textureValue:find('Desaturated',1,true))
            assert(c.shield.icon.coords[1]==0 and c.shield.wreath.coords[1]==0)
            assert(c.shield.icon.color[1]==1 and c.shield.wreath.color[1]==1 and c.shield.wreath.color[3]==1)
            assert(c.shield.points.color[1]==1 and c.shield.points:GetText()=='20')
            assert(c.dateCompleted:IsShown() and c.dateCompleted:GetText()=='10/09/26')
            assert(not c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='' and c.borderColor[1]>c.borderColor[3])
            assert(combined.date=='Stale outer date' and combined.completed==false and saved.done.second==nil)
        """)

    def test_both_completions_keep_gold_precedence_and_legacy_information_in_tooltip(self):
        self.combined(); self.tooltip()
        self.check("""
            custom.completed=true; custom.date='10/08/26'; combined.completed=true; combined.date=custom.date
            native.completed=true; view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.visualState=='character-complete' and c.saturated and c.nativeCompleted and c.characterCompleted)
            assert(c.shield.wreath.color[1]==1 and c.shield.wreath.color[3]==1)
            assert(c.shield.icon.coords[1]==0 and c.shield.wreath.coords[1]==0)
            assert(not c.nativeStatus:IsShown() and not c.completionText:IsShown())
            assert(c.dateCompleted:GetText()=='10/08/26' and native.date=='10/10/26')
            ns.WrathAchievementUI.ShieldEnter(c.shield)
            assert(tooltipTitle=='Achievement and Legacy Points')
            assert(tooltipLines[1]=='Achievement Points: 20' and tooltipLines[2]=='Achievement completed')
            assert(tooltipLines[3]=='Legacy Points: 1' and tooltipLines[4]=='Legacy completed')
            assert(saved.done.second==nil and view.model.custom.points==10 and #calls==0)
        """)

    def test_native_only_completion_has_actual_native_points_date_and_no_character_requirement(self):
        self.tooltip()
        self.check("""
            local row=view.model.byKey['legacy:62013']; row.completed=true; row.date='10/10/26'
            row.pointType='legacy'; row.pointValue=7; view.selected=nil; view:RenderCard(row,1,0)
            local c=view.cards[1]
            assert(c.visualState=='native-complete' and c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(c.shield.points:GetText()=='7' and c.shield.points.color[1]<c.shield.points.color[3])
            assert(c.shield.icon.coords[1]==.5 and c.shield.icon.color[1]==1)
            assert(c.shield.wreath.color[1]<c.shield.wreath.color[3] and c.nativeStatus:GetText()=='Completed via Legacy')
            assert(c.dateCompleted:IsShown() and c.dateCompleted:GetText()=='10/10/26')
            assert(not c.tracked:IsShown() and row.character==nil and row.source=='legacy')
            ns.WrathAchievementUI.ShieldEnter(c.shield)
            assert(tooltipTitle=='Legacy Points' and tooltipLines[1]=='7' and tooltipLines[2]=='Legacy completed')
            assert(view.model.custom.points==10 and saved.done.second==nil and #calls==0)
        """)

    def test_unknown_completion_never_creates_blue_gold_or_date_claims(self):
        self.combined()
        self.check("""
            custom.completed=nil; native.completed=nil; native.date='Historical native date'; combined.completed=true
            view:RenderCard(combined,1,0); local c=view.cards[1]
            assert(c.visualState=='incomplete' and not c.nativeCompleted and not c.characterCompleted and not c.saturated)
            assert(not c.nativeStatus:IsShown() and not c.dateCompleted:IsShown() and c.dateCompleted:GetText()=='')
            assert(c.shield.wreath.color[1]==1 and c.shield.wreath.coords[1]==.5)
            assert(custom.completed==nil and native.completed==nil and native.date=='Historical native date')
            assert(combined.completed==true and saved.done.second==nil and #calls==0)
        """)

    def test_zero_native_points_do_not_produce_filler_but_tooltip_preserves_zero(self):
        self.combined(); self.tooltip()
        self.check("""
            native.pointType='none'; native.pointValue=0; view:RenderCard(combined,1,0)
            local c=view.cards[1]; assert(c.nativeStatus:GetText()=='Completed via Legacy')
            assert(not c.nativeStatus:GetText():find('0',1,true) and c.shield.points:GetText()=='20')
            ns.WrathAchievementUI.ShieldEnter(c.shield); assert(tooltipLines[2]=='Legacy Points: 0')
            native.completed=false; view:RenderCard(combined,1,0)
            assert(not c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='' and native.pointValue==0)
        """)

    def test_pooled_reuse_resets_colors_coordinates_dates_footer_and_reuses_masks(self):
        self.combined()
        self.check("""
            view.selected=nil; view:RenderCard(combined,1,0); local c=view.cards[1]
            local shieldMask,wreathMask=c.shield.shieldMask,c.shield.wreathMask
            local count=#frames
            for i=1,12 do
                custom.completed=true; custom.date='10/09/26'; native.completed=true; view:RenderCard(combined,1,0)
                assert(c.saturated and c.shield.wreath.color[1]==1 and c.shield.wreath.coords[1]==0)
                assert(not c.nativeStatus:IsShown() and c.dateCompleted:GetText()=='10/09/26')
                custom.completed=false; native.completed=false; view:RenderCard(combined,1,0)
                assert(not c.saturated and c.shield.wreath.color[1]==1 and c.shield.wreath.coords[1]==.5)
                assert(not c.nativeStatus:IsShown() and c.dateCompleted:GetText()=='' and not c.dateCompleted:IsShown())
                native.completed=true; view:RenderCard(combined,1,0)
                assert(c.shield.wreath.color[1]==.35 and c.shield.wreath.coords[1]==.5)
                assert(c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='Completed via Legacy')
                assert(c.shield.icon.color[1]==1 and c.shield.points.color[1]==.65)
            end
            assert(c.shield.shieldMask==shieldMask and c.shield.wreathMask==wreathMask and #frames==count)
            assert(#c.shield.icon.masks==1 and #c.shield.wreath.masks==1)
            assert(saved.done.second==nil and #calls==0)
        """)

    def test_masks_are_attached_to_distinct_regions_at_matching_geometry(self):
        self.combined()
        self.check("""
            view:RenderCard(combined,1,0); local s=view.cards[1].shield
            assert(s.separateWreath and s.shieldMask~=s.wreathMask)
            assert(s.icon.masks[1]==s.shieldMask and s.wreath.masks[1]==s.wreathMask)
            assert(s.shieldMask.allPoints==s.icon and s.wreathMask.allPoints==s.wreath)
            assert(s.shieldMask.textureValue:find('Achievement-Shield-Mask',1,true))
            assert(s.wreathMask.textureValue:find('Achievement-Wreath-Mask',1,true))
            assert(s.icon.textureValue==s.wreath.textureValue and s.icon.coords[1]==s.wreath.coords[1])
        """)

    def test_missing_mask_creation_keeps_single_original_gray_composite_and_blue_label(self):
        self.combined()
        self.check("""
            local original=UIObject
            UIObject=function(...) local f=original(...); f.CreateMaskTexture=nil; return f end
            view:RenderCard(combined,9,0); UIObject=original
            local c=view.cards[9]
            assert(not c.shield.separateWreath and not c.shield.wreath:IsShown())
            assert(not c.shield.icon.masks and c.shield.icon.coords[1]==.5 and c.shield.icon.color[1]==1)
            assert(c.nativeStatus:GetText()=='Completed via Legacy' and c.nativeStatus:IsShown())
            assert(c.visualState=='legacy-complete' and not c.saturated and saved.done.second==nil and #calls==0)
        """)

    def test_missing_mask_attachment_or_rollback_capability_skips_optional_masks(self):
        self.combined()
        self.check("""
            local original=UIObject
            UIObject=function(...) local f=original(...); f.AddMaskTexture=nil; return f end
            view:RenderCard(combined,8,0)
            UIObject=function(...) local f=original(...); f.RemoveMaskTexture=nil; return f end
            view:RenderCard(combined,9,0); UIObject=original
            for _,index in ipairs({8,9}) do
                local c=view.cards[index]
                assert(not c.shield.separateWreath and not c.shield.wreath:IsShown() and not c.shield.icon.masks)
                assert(c.nativeStatus:GetText()=='Completed via Legacy' and c.shield.icon.color[1]==1)
                assert(c.shield.shieldMask==nil and c.shield.wreathMask==nil)
            end
        """)

    def test_mid_attachment_failure_rolls_back_both_regions_once_and_preserves_ui(self):
        self.combined()
        self.check("""
            local original=UIObject; maskAttempts=0
            UIObject=function(...)
                local f=original(...); local add=f.AddMaskTexture
                f.AddMaskTexture=function(self,mask)
                    maskAttempts=maskAttempts+1; add(self,mask)
                    if self:GetName() and self:GetName():find('Wreath',1,true) then error('Unsupported optional mask') end
                end
                return f
            end
            view:RenderCard(combined,9,0); UIObject=original
            local c=view.cards[9]
            assert(not c.shield.separateWreath and not c.shield.wreath:IsShown())
            assert(#c.shield.icon.masks==0 and #c.shield.wreath.masks==0)
            assert(c.shield.maskSetupFailure:find('Unsupported optional mask',1,true))
            assert(c.shield.icon.color[1]==1 and c.shield.icon.coords[1]==.5)
            assert(c.nativeStatus:GetText()=='Completed via Legacy' and c:IsShown() and not c.saturated)
            local count=#frames
            for i=1,8 do view:RenderCard(combined,9,0) end
            assert(maskAttempts==2 and #frames==count and saved.done.second==nil and #calls==0)
        """)

    def test_mask_creation_failure_is_bounded_and_does_not_replace_progress_or_record(self):
        self.combined()
        self.check("""
            local original=UIObject; creations=0
            UIObject=function(...)
                local f=original(...)
                f.CreateMaskTexture=function() creations=creations+1; error('Mask unavailable at runtime') end
                return f
            end
            view:RenderCard(combined,9,0); UIObject=original
            local c=view.cards[9]; assert(creations==1 and c.record==combined)
            assert(not c.shield.separateWreath and c.shield.icon.masks==nil and not c.shield.wreath:IsShown())
            assert(c.shield.maskSetupFailure:find('Mask unavailable at runtime',1,true))
            assert(c.progressPool[1].value==3 and c.progressPool[2].value==5)
            assert(c.nativeStatus:IsShown() and custom.completed==false and native.completed==true)
            assert(saved.done.second==nil and #calls==0)
        """)

    def test_feat_no_points_sheet_is_identical_in_both_complementary_regions(self):
        self.check("""
            local row=view.model.byKey['custom:first']; row.achievementType='feat_of_strength'; row.pointType='none'; row.pointValue=0
            view:RenderCard(row,1,0); local c=view.cards[1]
            assert(c.shield.icon.textureValue:find('NoPoints',1,true) and c.shield.wreath.textureValue==c.shield.icon.textureValue)
            assert(c.shield.icon.coords[1]==0 and c.shield.wreath.coords[1]==0)
            assert(c.shield.points:GetText()=='' and c.saturated and c.shield.wreath.color[1]==1)
            row.source='legacy'; row.completed=true; row.pointType='legacy'; row.pointValue=3
            view:RenderCard(row,1,0)
            assert(c.shield.points:GetText()=='3' and c.visualState=='native-complete' and not c.characterCompleted)
            assert(c.shield.icon.coords[1]==.5 and c.shield.wreath.coords[1]==.5)
            assert(c.shield.icon.color[1]==1 and c.shield.wreath.color[1]<c.shield.wreath.color[3])
            assert(#calls==0)
        """)

    def test_unavailable_mask_texture_keeps_composite_and_does_not_retry_on_refresh(self):
        self.combined()
        self.check("""
            local original=UIObject; lookups=0
            UIObject=function(...)
                local f=original(...)
                if f.kind=='MaskTexture' then
                    f.SetTexture=function() lookups=lookups+1; return false end
                end
                return f
            end
            view:RenderCard(combined,9,0); UIObject=original
            local c=view.cards[9]
            assert(lookups==2 and not c.shield.separateWreath and not c.shield.wreath:IsShown())
            assert(c.shield.icon.masks==nil and c.shield.wreath.masks==nil)
            assert(c.shield.maskSetupFailure:find('Achievement mask texture unavailable',1,true))
            assert(c.shield.icon.coords[1]==.5 and c.shield.icon.color[1]==1 and c.shield.points:GetText()=='20')
            assert(c.nativeStatus:IsShown() and c.nativeStatus:GetText()=='Completed via Legacy')
            for i=1,6 do view:RenderCard(combined,9,0) end
            assert(lookups==2 and custom.completed==false and saved.done.second==nil and #calls==0)
        """)

    def test_scroll_reuse_checks_explicit_state_before_reusing_artwork(self):
        self.combined()
        self.check("""
            view:RenderCard(combined,1,0); local c=view.cards[1]; local count=#frames
            view.scrollPass=true; custom.completed=true; custom.date='10/09/26'; combined.completed=false
            view:RenderCard(combined,1,20)
            assert(c.visualState=='character-complete' and c.saturated and c.shield.wreath.color[1]==1)
            assert(c.dateCompleted:GetText()=='10/09/26' and not c.nativeStatus:IsShown())
            custom.completed=false; native.completed=false; view:RenderCard(combined,1,40)
            assert(c.visualState=='incomplete' and not c.saturated and not c.nativeStatus:IsShown())
            assert(#frames==count and combined.completed==false and saved.done.second==nil)
        """)


class Iteration6MaskAssetsTests(unittest.TestCase):
    def test_mask_assets_are_binary_complements_and_keep_point_column_neutral(self):
        shield = (ADDON / 'Media/Achievement-Shield-Mask.tga').read_bytes()
        wreath = (ADDON / 'Media/Achievement-Wreath-Mask.tga').read_bytes()
        for raw in (shield, wreath):
            header = struct.unpack('<BBBHHBHHHHBB', raw[:18])
            self.assertEqual(header[2], 2)
            self.assertEqual(header[8:12], (64, 64, 32, 0x28))
            self.assertEqual(len(raw), 18 + 64 * 64 * 4)
            self.assertTrue(all(raw[n:n + 3] == b'\xff\xff\xff' for n in range(18, len(raw), 4)))
        a, b = shield[21::4], wreath[21::4]
        self.assertEqual(set(a), {0, 255})
        self.assertTrue(all(x + y == 255 for x, y in zip(a, b)))
        # Points and the entire central shield rim cannot receive Legacy blue.
        for x, y in ((18, 17), (20, 30), (31, 28), (43, 17), (42, 33), (31, 46)):
            self.assertEqual(a[y * 64 + x], 255, (x, y))
            self.assertEqual(b[y * 64 + x], 0, (x, y))
        for x, y in ((8, 12), (53, 12), (14, 43), (49, 43)):
            self.assertEqual(a[y * 64 + x], 0, (x, y))
            self.assertEqual(b[y * 64 + x], 255, (x, y))

    def test_shield_template_has_one_point_text_and_complementary_artwork_layers(self):
        root = ET.parse(ADDON / 'UI/WrathAchievementUI.xml').getroot()
        card = next(n for n in root if n.get('name') == 'FAWrathCardTemplate')
        shield = next(n for n in card.iter(URI + 'Frame') if n.get('name') == '$parentShield')
        textures = list(shield.iter(URI + 'Texture'))
        points = list(shield.iter(URI + 'FontString'))
        self.assertEqual([n.get('name') for n in textures], ['$parentIcon', '$parentWreath'])
        self.assertEqual([n.get('name') for n in points], ['$parentPoints'])
        layers = list(shield.find(URI + 'Layers'))
        self.assertEqual([n.get('level') for n in layers], ['BACKGROUND', 'ARTWORK', 'OVERLAY'])
        for texture in textures:
            self.assertEqual(texture.get('file'), 'Interface\\AchievementFrame\\UI-Achievement-Shields')
            self.assertEqual(texture.find(URI + 'TexCoords').get('bottom'), '.5')
        self.assertEqual(textures[1].get('hidden'), 'true')
        size = shield.find(URI + 'Size').find(URI + 'AbsDimension')
        self.assertEqual((size.get('x'), size.get('y')), ('64', '64'))
        anchor = shield.find(URI + 'Anchors').find(URI + 'Anchor')
        self.assertEqual(anchor.get('point'), 'TOPRIGHT')
        inset = anchor.find(URI + 'Offset').find(URI + 'AbsDimension')
        self.assertEqual((inset.get('x'), inset.get('y')), ('-6', '0'))


if __name__ == '__main__':
    unittest.main()
