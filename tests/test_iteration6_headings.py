"""Iteration 6 ornamental headings exercised through the real Lua renderer.

These assert category ancestry, bounded layout/allocation and read-only data.
They cannot validate the original texture's appearance in a live WoW client.
"""
import unittest

import test_wrath_iteration3_ui as iteration3


class Iteration6HeadingTests(unittest.TestCase):
    setUp = iteration3.Iteration3UITests.setUp
    check = iteration3.Iteration3UITests.check

    def test_main_category_has_centered_original_texture_heading_outside_viewport(self):
        self.check("""
            view.category='professions'; view:Render()
            local h=view.categoryHeading
            assert(h:IsShown() and h.title:GetText()=='Professions' and not h.subtitle:IsShown())
            assert(h:GetParent()==view.root and h:GetWidth()==view.contentPanelWidth)
            assert(h:GetLeft()==view.root:GetLeft()+view.contentLeft)
            assert(h.left.textureValue=='Interface\\\\AchievementFrame\\\\UI-Achievement-Stat-Buttons')
            assert(h.right.textureValue==h.left.textureValue and h.middle.textureValue==h.left.textureValue)
            assert(h.left:GetWidth()==23 and h.left:GetHeight()==23 and h.right:GetWidth()==23)
            assert(h.left.coords[1]==0 and h.left.coords[2]==.08984375)
            assert(h.right.coords[1]==.91015625 and h.right.coords[2]==1)
            assert(h:GetTop()<view.notice:GetBottom())
            assert(view.contentScroll:GetTop()==h:GetBottom()-8)
            assert(view.contentScroll:GetBottom()==view.root:GetBottom()+29)
            for _,heading in ipairs(view.headings) do
                assert(not heading:IsShown() or heading:GetText()~='Professions')
            end
            assert(#calls==0)
        """)

    def test_subcategory_uses_actual_parent_and_selected_names_without_changing_membership(self):
        self.check("""
            local parent=view.model.byCategory.professions
            local child=view.model.byCategory['professions:alchemy']
            local originalParent,originalChild=parent.name,child.name
            parent.name='Artisan Professions'; child.name='Alchemy and Elixirs'
            local memberships=#child.records
            view.expanded.professions=true; view.category=child.key; view:Render()
            local h=view.categoryHeading
            assert(h.title:GetText()=='Artisan Professions' and h.subtitle:GetText()=='Alchemy and Elixirs')
            assert(h.subtitle:IsShown() and h.subtitle:GetTop()<h.title:GetBottom())
            assert(child.parent=='professions' and #child.records==memberships)
            assert(view.category==child.key and view.expanded.professions)
            parent.name=originalParent; child.name=originalChild
            view:Render(); assert(h.title:GetText()==originalParent and h.subtitle:GetText()==originalChild)
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        """)

    def test_heading_tracks_resolved_category_after_model_refresh(self):
        self.check("""
            view.category='professions:alchemy'; view:Render()
            local h=view.categoryHeading
            local refreshed=ns.LegacyPresentation.Build()
            refreshed.byCategory.professions.name='Craft Professions'
            refreshed.byCategory['professions:alchemy'].name='Potions'
            view:SetModel(refreshed)
            assert(h==view.categoryHeading and h.title:GetText()=='Craft Professions' and h.subtitle:GetText()=='Potions')
            view.category='general'; view:Render()
            assert(h.title:GetText()=='General' and not h.subtitle:IsShown())
            assert(view.headingIndex==0 and #calls==0)
        """)

    def test_every_preset_has_spacing_fixed_end_caps_and_usable_list_viewport(self):
        self.check("""
            view.category='professions:alchemy'
            for name,preset in pairs(ns.WrathAchievementUI.PRESETS) do
                view:Layout(preset[1],preset[2])
                local h=view.categoryHeading
                local center=h:GetCenter()
                assert(center==view.root:GetLeft()+view.contentLeft+view.contentPanelWidth/2)
                assert(h.title:GetWidth()==view.contentPanelWidth-46)
                assert(h:GetTop()<view.searchBox:GetBottom() and h:GetTop()<view.notice:GetBottom())
                assert(h.left:GetWidth()==23 and h.right:GetHeight()==23 and h.middle:GetHeight()==23)
                assert(view.contentScroll:GetTop()<=h:GetBottom()-8)
                assert(view.contentScroll:GetHeight()>300 and view.root:GetScale()==1)
            end
            assert(#calls==0)
        """)

    def test_long_names_wrap_with_bounded_header_height_and_full_name_tooltip(self):
        self.check("""
            local parent=view.model.byCategory.professions
            local child=view.model.byCategory['professions:alchemy']
            parent.name=string.rep('Long parent category ',12)
            child.name=string.rep('Long subcategory name ',14)
            view.category=child.key; view:Layout(768,500); view:Render()
            local h=view.categoryHeading
            assert(h.title:GetText()==parent.name and h.subtitle:GetText()==child.name)
            assert(h.title:GetHeight()<=48 and h.subtitle:GetHeight()<=36 and h:GetHeight()<=94)
            assert(h.title:GetLeft()>=h:GetLeft() and h.title:GetRight()<=h:GetRight())
            assert(h.subtitle:GetLeft()>=h:GetLeft() and h.subtitle:GetRight()<=h:GetRight())
            assert(view.contentScroll:GetHeight()>=300 and view.contentScroll:GetTop()<h:GetBottom())
            tooltipLines={}
            GameTooltip={SetOwner=function(_,owner) tooltipOwner=owner end,
                SetText=function(_,text) tooltipTitle=text end,
                AddLine=function(_,text) tooltipLines[#tooltipLines+1]=text end,
                Show=function() tooltipShown=true end,Hide=function() tooltipShown=false end}
            h:Fire('OnEnter')
            assert(tooltipOwner==h and tooltipTitle==parent.name and tooltipLines[1]==child.name and tooltipShown)
            h:Fire('OnLeave'); assert(not tooltipShown and #calls==0)
        """)

    def test_summary_native_statistics_and_linked_pages_keep_original_headings(self):
        self.check("""
            view.category='general'; view:Render(); assert(view.categoryHeading:IsShown())
            view.category='summary'; view:Render()
            assert(not view.categoryHeading:IsShown() and view.renderMode=='summary')
            local recent=false
            for _,h in ipairs(view.headings) do if h:IsShown() and h:GetText()=='Recent Achievements' then recent=true end end
            assert(recent and view.contentScroll.points[1][5]==-69)
            for _,tab in ipairs({'rewards','trees','statistics'}) do
                view:SetTab(tab)
                assert(not view.categoryHeading:IsShown())
            end
            view:SetTab('achievements'); view.focus=view.model.byKey['custom:first']; view:Render()
            assert(not view.categoryHeading:IsShown() and view.renderMode=='focus')
            assert(view.headings[1]:GetText()=='Linked Achievement' and #calls==0)
        """)

    def test_search_filters_scroll_and_ordinary_refresh_allocate_no_new_heading_regions(self):
        self.check("""
            view.category='general'; view:Render()
            local h=view.categoryHeading
            local regions={h.title,h.subtitle,h.left,h.middle,h.right}
            local frameCount=#frames
            local model=view.model
            ns.LegacyPresentation.Build=function() error('Unexpected model rebuild') end
            for i=1,50 do
                view:Render()
                view.contentScroll:SetVerticalScroll(i)
                view.search='No result'; view:Render('search')
                view.filter='Completed'; view:Render('filter')
                view.search=''; view.filter='All'; view:Render()
                assert(view.categoryHeading==h and view.model==model)
            end
            assert(#frames==frameCount and #h.regions==5)
            assert(h.title==regions[1] and h.subtitle==regions[2] and h.left==regions[3])
            assert(h.middle==regions[4] and h.right==regions[5])
            assert(saved.done.first==1730000000 and saved.history[1]=='keep' and #calls==0)
        """)

    def test_decorative_creation_is_idempotent_and_missing_parent_falls_back_to_main(self):
        self.check("""
            local h=view.categoryHeading
            local count=#frames
            ns.WrathAchievementUI.CreateCategoryHeading(view)
            assert(view.categoryHeading==h and #frames==count)
            local category=view.model.byCategory.general
            category.parent='not-present'
            view.category='general'; view:Render()
            assert(h.title:GetText()==category.name and not h.subtitle:IsShown())
            category.parent=nil
            assert(#calls==0)
        """)


if __name__ == '__main__':
    unittest.main()
