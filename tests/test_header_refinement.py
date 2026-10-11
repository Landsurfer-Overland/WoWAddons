"""Header geometry and verified-subtotal presentation using production Lua/XML."""
import unittest

from test_iteration6_header_binding import SETUP
from test_iteration6_shell import CrestHarness
from test_progression_addendum import CoreHarness


TOOLTIP = '''
    tooltipLines={}
    GameTooltip={
        SetOwner=function(self,owner,anchor) self.owner=owner end,
        SetText=function(self,text) tooltipLines={text} end,
        AddLine=function(self,text,...) tooltipLines[#tooltipLines+1]=text end,
        Show=function(self) self.visible=true end,
        Hide=function(self) self.visible=false end,
    }
'''


class HeaderPointRefinementTests(unittest.TestCase):
    def setUp(self):
        self.h=CoreHarness()
        self.h.execute(SETUP)
        self.h.load('Integrations/CustomAdapter.lua')
        self.h.execute(TOOLTIP)

    def test_unverified_history_does_not_hide_other_verified_character_points(self):
        self.h.execute('''
            saved.done.explore855=123456; saved.done.explore802=123400
            local done,history=saved.done,saved.history
            local model=BindHeader()
            assert(model.custom.points==nil and model.custom.confirmedPoints==10)
            assert(model.custom.unverifiedPointRecords==1)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='10+')
            assert(LARWrathAchievementFrameHeaderLegacyPoints:GetText()=='16')
            LARWrathAchievementFrameHeader:Fire('OnEnter')
            assert(#tooltipLines==0 and not GameTooltip.visible)
            local lowerBound,_,_,_,known=ns.LAR.TotalPoints()
            assert(lowerBound==10 and known==false)
            assert(saved.done==done and saved.history==history and saved.done.explore855==123456 and #calls==0)
        ''')

    def test_subtotal_becomes_exact_when_real_character_evidence_is_available(self):
        self.h.execute('''
            saved.done.explore855=123456; saved.done.explore802=123400
            local before=BindHeader(); assert(before.custom.confirmedPoints==10 and before.custom.points==nil)
            testZone='Moonglade'; testSubzone='Nighthaven'
            local model=BindHeader()
            assert(model.custom.points==20 and model.custom.confirmedPoints==20 and model.custom.unverifiedPointRecords==0)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='20')
            LARWrathAchievementFrameHeader:Fire('OnEnter')
            assert(#tooltipLines==0 and not GameTooltip.visible)
            assert(saved.done.explore855==123456 and saved.done.explore802==123400 and #calls==0)
        ''')

    def test_foreign_or_unknown_character_scope_does_not_fabricate_zero_or_a_subtotal(self):
        self.h.execute('''
            saved.done.explore802=123400
            ns.LAR.CharacterScope=function() return nil end
            local model=BindHeader()
            assert(model.custom.points==nil and model.custom.confirmedPoints==nil)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='—')
            LARWrathAchievementFrameHeader:Fire('OnEnter')
            assert(#tooltipLines==0 and not GameTooltip.visible)
            assert(saved.done.explore802==123400 and saved.history[1]=='keep' and #calls==0)
        ''')

    def test_missing_earned_point_value_does_not_inflate_verified_subtotal(self):
        self.h.execute('''
            saved.done.explore802=123400
            ns.LAR.BY_KEY.explore802.pts=nil
            local model=BindHeader()
            assert(model.custom.points==nil and model.custom.confirmedPoints==0 and model.custom.unverifiedPointRecords==1)
            assert(model.custom.byKey['custom:explore802'].completed==true)
            assert(model.custom.byKey['custom:explore802'].pointValue==nil)
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='0+' and saved.done.explore802==123400 and #calls==0)
        ''')

    def test_hover_without_tooltip_and_repeated_render_do_not_do_catalog_work(self):
        self.h.execute('''
            saved.done.explore855=123456; saved.done.explore802=123400
            local model=BindHeader(); local frameCount=#frames
            ns.LegacyPresentation.Build=function() error('Hover rebuilt achievements') end
            ns.CustomAchievementAdapter.Catalog=function() error('Hover rescanned achievements') end
            for i=1,20 do
                LARWrathAchievementFrameHeader:Fire('OnEnter')
                assert(not GameTooltip.visible and #tooltipLines==0)
                LARWrathAchievementFrameHeader:Fire('OnLeave'); assert(not GameTooltip.visible)
                view:Render()
                assert(view.model==model and LARWrathAchievementFrameHeaderPoints:GetText()=='10+')
            end
            assert(#frames==frameCount and saved.done.explore855==123456 and #calls==0)
        ''')

    def test_native_zero_is_distinct_from_unavailable_and_never_added_to_character_points(self):
        self.h.execute('''
            saved.done.explore802=123400
            nativeCatalog.points=0; BindHeader()
            assert(LARWrathAchievementFrameHeaderLegacyPoints:GetText()=='0')
            nativeCatalog.points=nil; BindHeader()
            assert(LARWrathAchievementFrameHeaderLegacyPoints:GetText()=='—')
            assert(LARWrathAchievementFrameHeaderPoints:GetText()=='10')
            LARWrathAchievementFrameHeader:Fire('OnEnter')
            assert(#tooltipLines==0 and not GameTooltip.visible and #calls==0)
        ''')

    def test_header_hover_has_no_handlers_and_leaves_unrelated_tooltips_alone(self):
        self.h.execute('''
            BindHeader()
            local header=LARWrathAchievementFrameHeader
            assert(header:GetScript('OnEnter')==nil and header:GetScript('OnLeave')==nil)
            assert(view.PointsTooltip==nil)
            GameTooltip.visible=true
            GameTooltip.owner=UIParent
            tooltipLines={'Unrelated tooltip'}
            header:Fire('OnEnter'); header:Fire('OnLeave')
            assert(GameTooltip.visible and GameTooltip.owner==UIParent)
            assert(#tooltipLines==1 and tooltipLines[1]=='Unrelated tooltip')
            assert(#calls==0)
        ''')


class HeaderGeometryRefinementTests(unittest.TestCase):
    def test_roof_crest_and_seated_plaques_share_window_center_on_every_preset(self):
        h=CrestHarness(controller=True)
        h.execute("function UnitFactionGroup() return 'Alliance' end")
        h.enable()
        h.execute('''
            local c=ns.LegacyUIController; local frameCount=#frames; local model=c.ui.model
            for _,name in ipairs({'Compact','Standard','Large','Compact'}) do
                c:SetSizePreset(name); FlushTimers()
                local header=LARWrathAchievementFrameHeader
                local x=header:GetCenter(); local rootX=c.ui.root:GetCenter()
                assert(x==rootX and c.ui.model==model)
                local crest=LARWrathAchievementFrameHeaderCrest
                local surround=LARWrathAchievementFrameHeaderCrestSurround
                local cx,cy=crest:GetCenter(); local sx,sy=surround:GetCenter()
                assert(cx==x and sx==x and cy==sy and surround:IsShown())
                assert(crest:GetWidth()<surround:GetWidth() and crest:GetHeight()<surround:GetHeight())
                local a,b=LARWrathAchievementFrameHeaderRoofLeft,LARWrathAchievementFrameHeaderRoofRight
                assert(a:GetRight()==x and b:GetLeft()==x and a:GetTop()==b:GetTop())
                local l,r=LARWrathAchievementFrameHeaderPointBorder,LARWrathAchievementFrameHeaderLegacyPointBorder
                local lx,ly=l:GetCenter(); local rx,ry=r:GetCenter()
                assert(x-lx==rx-x and ly==ry)
                assert(LARWrathAchievementFrameHeaderPointBorderLeft:GetLeft()>=a:GetLeft())
                assert(LARWrathAchievementFrameHeaderLegacyPointBorderRight:GetRight()<=b:GetRight())
                assert(l:GetRight()<surround:GetLeft() and r:GetLeft()>surround:GetRight())
                assert(#frames==frameCount and c.cover:IsVisible() and c.lastError==nil and #calls==0)
            end
        ''')

    def test_header_hover_does_not_intercept_normal_window_drag(self):
        h=CrestHarness(controller=True)
        h.enable()
        h.execute(TOOLTIP)
        h.execute('''
            local c=ns.LegacyUIController; local model=c.ui.model
            LARWrathAchievementFrameHeader:Fire('OnEnter')
            LARWrathAchievementFrameHeader:Fire('OnDragStart')
            assert(c.cover.moving and c.dragging)
            LARWrathAchievementFrameHeader:Fire('OnDragStop')
            assert(not c.cover.moving and not c.dragging and c.ui.model==model)
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        ''')


if __name__=='__main__':
    unittest.main()
