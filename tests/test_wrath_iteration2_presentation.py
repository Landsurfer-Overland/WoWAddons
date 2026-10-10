"""Iteration 2 presentation contracts; no claim of native client rendering."""
import unittest
import xml.etree.ElementTree as ET

from test_legacy_wrath_ui import ADDON, Harness, URI


class PresentationHarness(Harness):
    def create(self, kind, name=None, parent=None, template=None):
        # These are native presentation primitives, not addon templates. Keep
        # their scripts explicit so the addon close handler is still tested.
        if template == "UIPanelCloseButton":
            template = None
        f = super().create(kind, name, parent, template)
        self.lua.execute("""
            local f = ...
            function f:RegisterForDrag(button) self.dragButton = button end
            function f:StartMoving() self.moving = true end
            function f:StopMovingOrSizing() self.moving = false end
            function f:SetFontObject(object) self.fontObject = object end
        """, f)
        return f

    def build(self, f, element):
        if element.get("inherits") == "UIPanelCloseButton":
            element = ET.fromstring(ET.tostring(element))
            element.attrib.pop("inherits")
        super().build(f, element)


class Iteration2PresentationTests(unittest.TestCase):
    def setUp(self):
        self.h = PresentationHarness()
        self.h.execute("""
            host = CreateFrame("Frame", "PresentationHost")
            host:SetSize(768, 640)
            function guard(fn) fn() end
            selectedTabs, closeCount = {}, 0
            view = ns.WrathAchievementUI.Create(host, guard, function() end, {
                onTab = function(tab) selectedTabs[#selectedTabs + 1] = tab end,
                onClose = function() closeCount = closeCount + 1 end,
            })
            view:Fit(host)
            view:SetModel(ns.LegacyPresentation.Build())
        """)

    def check(self, code):
        self.h.execute(code)

    def test_player_sheet_contains_one_shield_for_each_completion_state(self):
        self.check("""
            local row = view.model.byKey["custom:second"]
            view:RenderCard(row, 1, 0)
            local shield = view.cards[1].shield
            assert(shield.icon.coords[1] == .5 and shield.icon.coords[2] == 1)
            assert(shield.icon.coords[3] == 0 and shield.icon.coords[4] == .5)
            assert(shield.points:GetText() == "20" and shield:IsShown())
            view:RenderCard(view.model.byKey["custom:first"], 1, 0)
            assert(shield.icon.coords[1] == 0 and shield.icon.coords[2] == .5)
            assert(shield.icon.coords[4] == .5 and shield.points:GetText() == "10")
        """)
        xml = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        card = next(e for e in xml if e.get("name") == "FAWrathCardTemplate")
        shields = [e for e in card.iter(URI + "Texture") if "UI-Achievement-Shields" in e.get("file", "")]
        self.assertEqual(len(shields), 1)
        self.assertEqual(shields[0].find(URI + "TexCoords").get("bottom"), ".5")

    def test_pooled_card_removes_reward_after_genuine_native_reward(self):
        self.check("""
            view:RenderCard(view.model.byKey["legacy:62013"], 1, 0)
            local card = view.cards[1]
            assert(card.reward:GetText() == "Earn 1 Legacy Point.")
            assert(card.reward:IsShown() and card.rewardBackground:IsShown())
            view:RenderCard(view.model.byKey["custom:second"], 1, 0)
            assert(card.reward:GetText() == "")
            assert(not card.reward:IsShown() and not card.rewardBackground:IsShown())
            assert(card.shield:IsShown() and card.shield.points:GetText() == "20")
        """)

    def test_header_keeps_two_live_counters_in_matching_wrath_artwork(self):
        self.check("""
            assert(FAWrathAchievementFrameHeaderPoints:GetText() == "10")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText() == "16")
            view.model.custom.points, view.model.native.points = 345, nil
            view:SetModel(view.model)
            assert(FAWrathAchievementFrameHeaderPoints:GetText() == "345")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText() == "Unavailable")
        """)
        xml = ET.parse(ADDON / "UI/WrathAchievementUI.xml").getroot()
        window = next(e for e in xml if e.get("name") == "FAWrathWindowTemplate")
        borders = [e for e in window.iter(URI + "Texture") if e.get("name") in ("$parentPointBorder", "$parentLegacyPointBorder")]
        self.assertEqual(len(borders), 2)
        self.assertEqual(borders[0].get("file"), borders[1].get("file"))
        self.assertEqual(borders[0].find(URI + "TexCoords").attrib, borders[1].find(URI + "TexCoords").attrib)

    def test_four_tabs_select_one_view_without_native_behavior_in_renderer(self):
        self.check("""
            assert(#view.tabs == 4)
            local titles = {"Achievements", "Legacy Rewards", "Legacy Trees", "Statistics"}
            for i, title in ipairs(titles) do assert(view.tabs[i]:GetText() == title) end
            view.tabs[2]:Fire("OnClick")
            assert(view.tab == "rewards" and selectedTabs[1] == "rewards")
            assert(view.nativeHost:IsShown() and not view.categoryScroll:IsShown())
            assert(not view.contentBackground:IsShown() and not view.nativeBackground:IsVisible())
            assert(not view.searchBox:IsShown() and not view.contentScroll:IsShown())
            assert(FAWrathTab2LeftDisabled:IsShown() and not FAWrathTab2Left:IsShown())
            view:SetTab("trees", false)
            assert(#selectedTabs == 1 and view.tab == "trees")
            view.tabs[4]:Fire("OnClick")
            assert(view.tab == "statistics" and selectedTabs[2] == "statistics")
            assert(view.contentScroll:IsShown() and not view.nativeHost:IsShown())
            assert(view.contentBackground:IsShown() and not view.nativeBackground:IsVisible())
            assert(#calls == 0)
        """)

    def test_summary_keeps_source_counts_and_reports_unknown_partial_data(self):
        self.check("""
            view.model.byKey["legacy:62013"].completed = nil
            view.model.native.partial = true
            -- This fixture edits an already-built snapshot in place.
            ns.LegacyPresentation.Invalidate(view.model)
            view:Render()
            assert(view.bars[1].label:GetText() == "Custom Achievements Earned")
            assert(view.bars[1].text:GetText() == "1/2")
            assert(view.bars[2].label:GetText() == "Native Legacy Challenges Earned")
            assert(view.bars[2].text:GetText() == "0/3 shown (1 unknown)")
            for _, heading in ipairs(view.headings) do
                assert(heading:GetText()~="Character Achievement Points: 10")
                assert(heading:GetText()~="Legacy Points: 16")
            end
            assert(FAWrathAchievementFrameHeaderPoints:GetText()=="10")
            assert(FAWrathAchievementFrameHeaderLegacyPoints:GetText()=="16" and #calls==0)
        """)

    def test_undated_native_completion_is_not_fabricated_as_recent(self):
        self.check("""
            view.model.byKey["legacy:62013"].completed = true
            view.model.byKey["legacy:62013"].date = nil
            view.model.byKey["legacy:62013"].dateSort = nil
            -- Runtime data refreshes build a new model; invalidate this edited fixture.
            ns.LegacyPresentation.Invalidate(view.model)
            view:Render()
            assert(#ns.LegacyPresentation.Recent(view.model, "legacy", 4) == 0)
            assert(view.bars[2].text:GetText() == "1/3")
            for _, card in ipairs(view.cards) do
                assert(not card:IsShown() or card.record.source == "custom")
            end
        """)

    def test_original_close_and_roof_drag_target_only_owner_host(self):
        self.check("""
            FAWrathAchievementFrameCloseButton:Fire("OnClick")
            assert(closeCount == 1)
            assert(FAWrathAchievementFrameCloseButton:GetFrameLevel()>view.nativeHost:GetFrameLevel()+10)
            FAWrathAchievementFrameHeader:Fire("OnDragStart")
            assert(host.moving)
            FAWrathAchievementFrameHeader:Fire("OnDragStop")
            assert(not host.moving and #calls == 0)
        """)

    def test_scrolling_expansion_and_custom_tracking_survive_mixed_categories(self):
        self.check("""
            view.category = "general"
            view.selected = "custom:second"
            view:Render()
            local card
            for _, f in ipairs(view.cards) do if f:IsShown() and f.record.key == "custom:second" then card = f end end
            assert(card and card:GetHeight() > 84 and card.tracked:IsShown())
            assert(card.progressPool[1].value == 7 and card.progressPool[1].maximum == 10)
            card.tracked:Fire("OnClick")
            assert(saved.tracked.second and saved.done.first == 1730000000 and #calls == 0)
            view.searchBox:SetText("alchemist"); view.searchBox:Fire("OnTextChanged")
            view.category = "professions:alchemy"; view:Render()
            assert(view.cards[1].record.key == "legacy:62013")
        """)


if __name__ == "__main__":
    unittest.main()
