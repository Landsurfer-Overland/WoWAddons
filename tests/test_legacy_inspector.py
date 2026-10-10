#!/usr/bin/env python3
"""Focused safety and behavior checks for the manual Legacy diagnostic.

Run with Python 3 and Lupa's Lua 5.1 runtime. These mocks exercise diagnostic
behavior; they do not emulate WoW rendering or establish native API support.
"""

from pathlib import Path
import re
import sys
import unittest

try:
    from lupa.lua51 import LuaRuntime
except ImportError:
    sys.path.insert(0, "/workspace/.cloud-tools/forever-achievements/python")
    from lupa.lua51 import LuaRuntime


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "ForeverAchievements" / "Diagnostics" / "LegacyInspector.lua"


BASE = r'''
ns = {}
SlashCmdList = {}
UISpecialFrames = {}
WOW_PROJECT_ID = 99
function GetBuildInfo() return "1.60.1", "70338", "Oct 9 2026", 16001 end
function InCombatLockdown() return false end
function geterrorhandler() return function() end end
function GetTime() return 1 end
function date() return "2026-10-10" end
unpack = unpack or table.unpack
tinsert = table.insert

forbiddenCalls = {}
getterCalls = {}
uiFrames = {}
local function forbidden(name)
    return function(...)
        forbiddenCalls[#forbiddenCalls + 1] = name
        error("Forbidden diagnostic operation: " .. name)
    end
end
Forbidden = forbidden
hooksecurefunc = forbidden("hooksecurefunc")
SendAddonMessage = forbidden("SendAddonMessage")
SetCVar = forbidden("SetCVar")
LoadAddOn = forbidden("LoadAddOn")
C_AddOns = { LoadAddOn = forbidden("C_AddOns.LoadAddOn") }
C_ChatInfo = { SendAddonMessage = forbidden("C_ChatInfo.SendAddonMessage") }
C_Timer = {
    After = forbidden("C_Timer.After"),
    NewTicker = forbidden("C_Timer.NewTicker"),
}
GetAchievementInfo = forbidden("GetAchievementInfo")
C_Legacy = {
    GetChallenges = forbidden("C_Legacy.GetChallenges"),
    ClaimReward = forbidden("C_Legacy.ClaimReward"),
}
LegacyUnknownFunction = forbidden("LegacyUnknownFunction")
UIParent = {
    GetName = function() return "UIParent" end,
    GetObjectType = function() return "Frame" end,
    IsForbidden = function() return false end,
}

-- Native objects have explicit read-only methods and poisoned mutators.
function NativeFrame(name, parent)
    local f = { children = {}, regions = {}, scripts = {}, parent = parent }
    local function record(method)
        getterCalls[name .. ":" .. method] = true
    end
    function f:GetName() record("GetName"); return name end
    function f:GetObjectType() record("GetObjectType"); return "Frame" end
    function f:IsObjectType(kind) return kind == "Frame" end
    function f:GetParent() record("GetParent"); return self.parent end
    function f:GetChildren() record("GetChildren"); return unpack(self.children) end
    function f:GetRegions() record("GetRegions"); return unpack(self.regions) end
    function f:GetScript(script) record("GetScript"); return self.scripts[script] end
    function f:IsForbidden() return false end
    function f:IsProtected() return false end
    for _, method in ipairs({
        "Show", "Hide", "SetScript", "HookScript", "SetParent", "SetPoint",
        "RegisterEvent", "UnregisterAllEvents", "SetDataProvider",
        "SelectCategory", "ScrollToElementDataIndex", "ClaimReward",
    }) do
        f[method] = forbidden(name .. ":" .. method)
    end
    return f
end

-- A small UI mock permits an addon-owned copy window, if created lazily or
-- eagerly. It deliberately does not grant mutation methods to native frames.
local function UIObject(kind, name, parent)
    local f = { kind = kind, name = name, parent = parent, scripts = {}, text = "" }
    function f:GetName() return self.name end
    function f:GetObjectType() return self.kind end
    function f:GetParent() return self.parent end
    function f:SetScript(event, callback) self.scripts[event] = callback end
    function f:GetScript(event) return self.scripts[event] end
    function f:SetText(value) self.text = value end
    function f:GetText() return self.text end
    function f:SetMultiLine(value) self.multiline = value end
    function f:SetAutoFocus(value) self.autofocus = value end
    function f:SetMaxLetters(value) self.maxletters = value end
    function f:SetFocus() self.focused = true end
    function f:ClearFocus() self.focused = false end
    function f:Show() self.shown = true end
    function f:Hide() self.shown = false end
    function f:IsShown() return self.shown == true end
    function f:SetSize(width, height) self.width = width; self.height = height end
    function f:SetWidth(width) self.width = width end
    function f:SetHeight(height) self.height = height end
    function f:GetWidth() return self.width or 640 end
    function f:GetHeight() return self.height or 420 end
    function f:GetStringHeight() return 120 end
    function f:GetStringWidth() return 300 end
    function f:GetFont() return "font", 12, "" end
    function f:CreateFontString(childName) return UIObject("FontString", childName, self) end
    function f:CreateTexture(childName) return UIObject("Texture", childName, self) end
    for _, method in ipairs({
        "SetPoint", "SetAllPoints",
        "ClearAllPoints", "SetBackdrop", "SetBackdropColor", "SetBackdropBorderColor",
        "SetFrameStrata", "SetFrameLevel", "SetToplevel", "SetMovable",
        "EnableMouse", "RegisterForDrag", "StartMoving", "StopMovingOrSizing",
        "SetClampedToScreen", "SetResizable", "SetMinResize", "SetMaxResize",
        "SetScrollChild", "SetVerticalScroll", "UpdateScrollChildRect",
        "SetFontObject", "SetFont", "SetTextInsets", "SetCursorPosition", "HighlightText",
        "EnableKeyboard", "SetJustifyH", "SetJustifyV",
        "SetNormalFontObject", "SetHighlightFontObject", "SetDisabledFontObject",
        "SetNormalTexture", "SetHighlightTexture", "SetPushedTexture",
        "SetTextColor", "SetColorTexture", "SetTexture", "SetAlpha",
        "Enable", "Disable", "SetEnabled", "SetPropagateKeyboardInput",
    }) do
        f[method] = function() end
    end
    uiFrames[#uiFrames + 1] = f
    if name then _G[name] = f end
    return f
end
function CreateFrame(kind, name, parent) return UIObject(kind, name, parent) end
GameFontNormal = {}; GameFontHighlight = {}; GameFontHighlightSmall = {}
ChatFontNormal = {}; GameFontNormalSmall = {}
DEFAULT_CHAT_FRAME = { AddMessage = function() end }
'''


POPULATED = r'''
LegacySystemFrame = NativeFrame("LegacySystemFrame", UIParent)
local root = LegacySystemFrame
root.ChallengesPage = NativeFrame("LegacySystemFrame.ChallengesPage", root)
root.RewardTrackPage = NativeFrame("LegacySystemFrame.RewardTrackPage", root)
root.children = { root.ChallengesPage, root.RewardTrackPage }
local page = root.ChallengesPage
page.DetailPane = NativeFrame("LegacySystemFrame.ChallengesPage.DetailPane", page)
page.children = { page.DetailPane }
page.DetailPane.ScrollBox = NativeFrame("LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox", page.DetailPane)
page.DetailPane.children = { page.DetailPane.ScrollBox }
local box = page.DetailPane.ScrollBox
local entries = {
    {
        challengeID = 481, name = "Explore Mock Kingdom", categoryID = 7,
        description = "Explore mock locations", completed = false,
        progress = 3, progressMax = 12, legacyPoints = 10, accountWide = true,
    },
    {
        challengeID = 482, name = "Complete Mock Journey", categoryID = 7,
        completed = true, progress = 12, progressMax = 12,
    },
}
provider = { collection = entries }
function provider:GetSize() return #self.collection end
provider.Enumerate = Forbidden("unknown provider iterator")
function box:GetDataProvider() return provider end
box.dataProvider = provider
box.categoryID = 7
local row = NativeFrame("LegacyMockChallengeRow", box)
row.elementData = entries[1]
function row:GetElementData() return self.elementData end
box.children = { row }
root.RewardTrackPage.currentLegacyPoints = 160
root.RewardTrackPage.nextMilestone = 200
root.RewardTrackPage.rewards = {
    { rewardID = 9001, threshold = 200, description = "Mock Spectral Tabard", claimed = false },
    { rewardID = 9002, threshold = 100, description = "Mock Mount", claimed = true },
}
root.scripts.OnShow = Forbidden("native OnShow callback")
row.Refresh = Forbidden("unknown native Refresh")
root.UnknownMixin = { Apply = Forbidden("unknown mixin Apply") }
'''


class InspectorTests(unittest.TestCase):
    def make_runtime(self, fixture=""):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(BASE)
        if fixture:
            lua.execute(fixture)
        chunk = lua.execute("return assert(loadstring(...))", MODULE.read_text(), "@LegacyInspector.lua")
        chunk("ForeverAchievements", lua.globals().ns)
        self.assertIsNotNone(lua.globals().ns.LegacyInspector)
        self.assertIsNotNone(lua.globals().ns.LegacyInspector.Inspect)
        return lua

    def inspect(self, lua):
        report = lua.globals().ns.LegacyInspector.Inspect()
        self.assertIsInstance(report, str)
        self.assertTrue(report.strip())
        self.assertEqual(list(lua.globals().forbiddenCalls.values()), [], "Inspector invoked a forbidden native/unknown operation")
        return report

    def slash_handler(self, lua):
        handler = lua.execute('''
            for key, value in pairs(_G) do
                if type(key) == "string" and key:match("^SLASH_") and value == "/legacyinspect" then
                    local name = key:match("^SLASH_(.-)%d+$")
                    return name and SlashCmdList[name]
                end
            end
        ''')
        self.assertIsNotNone(handler, "The manual /legacyinspect command is missing")
        return handler

    def test_unloaded_ui_reports_guidance_and_registers_manual_command(self):
        lua = self.make_runtime()
        report = self.inspect(lua)
        for heading in (
            "FOREVER LEGACY INSPECTOR", "CLIENT", "FRAMES", "NAMESPACES",
            "CHALLENGE DATA", "REWARD TRACK", "LIMITATIONS", "RECOMMENDED INTEGRATION POINTS",
        ):
            self.assertIn(heading, report)
        self.assertIn("70338", report)
        self.assertIn("16001", report)
        self.assertIn("LegacySystemFrame", report)
        self.assertIn("open", report.lower())
        self.assertRegex(report.lower(), r"not found|unavailable|not loaded")
        self.assertTrue(lua.execute('''
            for key, value in pairs(_G) do
                if type(key) == "string" and key:match("^SLASH_") and value == "/legacyinspect" then
                    local handler = key:match("^SLASH_(.-)%d+$")
                    return handler and type(SlashCmdList[handler]) == "function"
                end
            end
            return false
        '''), "The manual /legacyinspect command is missing")

    def test_populated_frames_passively_expose_challenge_and_reward_evidence(self):
        lua = self.make_runtime(POPULATED)
        report = self.inspect(lua)
        for evidence in (
            "ChallengesPage", "DetailPane", "ScrollBox", "RewardTrackPage",
            "481", "Explore Mock Kingdom", "progress", "legacyPoints",
            "currentLegacyPoints", "160", "9001", "Mock Spectral Tabard", "claimed",
        ):
            self.assertIn(evidence.lower(), report.lower())
        self.assertIn("C_Legacy", report)
        self.assertIn("OnShow", report)
        self.assertIn("Refresh", report)
        self.assertRegex(report.lower(), r"recycl|visible|materializ")

    def test_native_state_is_unchanged_across_inspections(self):
        lua = self.make_runtime(POPULATED)
        snapshot = lua.eval('''function()
            local r = LegacySystemFrame
            local box = r.ChallengesPage.DetailPane.ScrollBox
            return tostring(box:GetDataProvider()) .. ":" .. box.categoryID .. ":"
                .. r.RewardTrackPage.currentLegacyPoints .. ":"
                .. tostring(r.RewardTrackPage.rewards[1].claimed) .. ":"
                .. tostring(r.scripts.OnShow) .. ":" .. provider.collection[1].progress
        end''')
        before = snapshot()
        self.inspect(lua)
        self.inspect(lua)
        self.assertEqual(snapshot(), before)

    def test_category_inference_requires_observed_changes_and_never_changes_category(self):
        lua = self.make_runtime(POPULATED)
        first = self.inspect(lua)
        self.assertRegex(first.lower(), r"unknown|unavailable|not (?:yet )?established|not confirmed|hypothes|cannot|manual")
        lua.execute('''
            LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.categoryID = 8
            provider = { collection = {{ challengeID = 777, name = "A Different Observed Category" }} }
            function provider:GetSize() return #self.collection end
        ''')
        second = self.inspect(lua)
        self.assertIn("777", second)
        self.assertIn("A Different Observed Category", second)
        self.assertRegex(second.lower(), r"chang|differ|snapshot|observ")
        self.assertEqual(lua.globals().LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.categoryID, 8)

    def test_snapshots_without_readable_ids_report_unavailable_comparison(self):
        lua = self.make_runtime(POPULATED + '''
            provider.collection = {{ name = "No stable identifiers", progress = 3 }}
            LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox.children = {}
        ''')
        self.inspect(lua)
        lua.execute('provider.collection[1].progress = 4')
        second = self.inspect(lua)
        comparison = next(line for line in second.splitlines() if "Manual snapshot comparison:" in line)
        self.assertRegex(comparison.lower(), r"ids.*unavailable")
        self.assertNotRegex(comparison.lower(), r"ids\s+unchanged")
        # A newly readable ID cannot establish a change against an earlier
        # snapshot that had no IDs to compare.
        lua.execute('provider.collection[1].challengeID = 953')
        third = self.inspect(lua)
        comparison = next(line for line in third.splitlines() if "Manual snapshot comparison:" in line)
        self.assertRegex(comparison.lower(), r"ids.*unavailable")

    def test_missing_property_paths_can_be_resolved_from_named_descendants(self):
        lua = self.make_runtime(POPULATED + '''
            LegacySystemFrame.ChallengesPage = nil
            LegacySystemFrame.RewardTrackPage = nil
        ''')
        report = self.inspect(lua)
        self.assertIn("Explore Mock Kingdom", report)
        self.assertIn("Mock Spectral Tabard", report)

    def test_stale_properties_cannot_escape_native_descendant_boundary(self):
        lua = self.make_runtime(POPULATED + '''
            local outside = NativeFrame("DetachedLegacyChallengesPage", UIParent)
            outside.DetailPane = NativeFrame("DetachedLegacyDetailPane", UIParent)
            outside.DetailPane.ScrollBox = NativeFrame("DetachedLegacyScrollBox", UIParent)
            outside.DetailPane.ScrollBox.GetDataProvider = Forbidden("detached provider lookup")
            outside.DetailPane.ScrollBox.payload = "DETACHED_FRAME_SENTINEL"
            LegacySystemFrame.ChallengesPage = outside
            LegacySystemFrame.children = { LegacySystemFrame.RewardTrackPage }
        ''')
        report = self.inspect(lua)
        self.assertNotIn("DETACHED_FRAME_SENTINEL", report)
        self.assertRegex(report, r"ScrollBox: NOT FOUND")

    def test_named_regions_are_reported_without_frame_traversal(self):
        lua = self.make_runtime(POPULATED + '''
            local region = NativeFrame("LegacyNamedChallengeLabel", LegacySystemFrame)
            function region:GetObjectType() return "FontString" end
            region.GetChildren = Forbidden("region child traversal")
            region.GetScript = Forbidden("region script traversal")
            LegacySystemFrame.regions = { region }
        ''')
        report = self.inspect(lua)
        self.assertIn("LegacyNamedChallengeLabel", report)
        self.assertIn("FontString", report)

    def test_verified_provider_getters_support_table_inheritance(self):
        lua = self.make_runtime(POPULATED + '''
            local collection = provider.collection
            provider.collection = nil
            provider.GetSize = nil
            setmetatable(provider, { __index = {
                GetSize = function() return #collection end,
                GetCollection = function() return collection end,
            } })
        ''')
        report = self.inspect(lua)
        self.assertIn("Explore Mock Kingdom", report)
        self.assertIn("481", report)

    def test_busy_root_preserves_requested_pages_and_core_challenge_samples(self):
        lua = self.make_runtime(POPULATED + '''
            local root = LegacySystemFrame
            root.children = {}
            for index = 1, 90 do
                root.children[index] = NativeFrame("OrdinaryLegacyChild" .. index, root)
            end
            root.children[91] = root.ChallengesPage
            root.children[92] = root.RewardTrackPage
        ''')
        report = self.inspect(lua)
        self.assertIn("ScrollBox: FOUND", report)
        self.assertIn("RewardTrackPage: FOUND", report)
        self.assertIn("Explore Mock Kingdom", report)
        self.assertIn("Mock Spectral Tabard", report)

    def test_reward_collection_records_are_visible_within_entry_budget(self):
        lua = self.make_runtime(POPULATED + '''
            local rewards = LegacySystemFrame.RewardTrackPage
            rewards.rewards = nil
            rewards.collection = {}
            for index = 1, 100 do
                rewards.collection[index] = {
                    rewardID = 6000 + index,
                    threshold = index * 100,
                    description = "CollectionReward" .. index,
                    claimed = index == 1,
                }
            end
        ''')
        lua.globals().ns.LegacyInspector.Config.maxEntries = 2
        report = self.inspect(lua)
        self.assertIn("CollectionReward1", report)
        self.assertNotIn("CollectionReward100", report)
        self.assertNotIn("6100", report)
        lua.execute('''
            local rewards = LegacySystemFrame.RewardTrackPage
            rewards.dataProvider = { collection = rewards.collection }
            rewards.collection = nil
        ''')
        nested = self.inspect(lua)
        self.assertIn("CollectionReward1", nested)
        self.assertNotIn("CollectionReward100", nested)
        self.assertNotIn("6100", nested)

    def test_exhausted_object_budget_skips_global_namespace_table_keys(self):
        lua = self.make_runtime('''
            LegacySystemFrame = NativeFrame("LegacySystemFrame", UIParent)
            watchedNamespaceTables = {}
            namespaceKeyReads = {}
            for index = 1, 80 do
                local namespace = { payload = "NAMESPACE_BUDGET_SENTINEL" .. index }
                _G["LegacyNamespaceBudgetTable" .. index] = namespace
                watchedNamespaceTables[namespace] = true
            end
            local originalNext = next
            function next(object, key)
                if watchedNamespaceTables[object] then namespaceKeyReads[object] = true end
                return originalNext(object, key)
            end
        ''')
        lua.globals().ns.LegacyInspector.Config.maxObjects = 1
        report = self.inspect(lua)
        self.assertNotIn("NAMESPACE_BUDGET_SENTINEL", report)
        self.assertEqual(len(list(lua.globals().namespaceKeyReads.keys())), 0)

    def test_getter_failures_are_contained_and_reported(self):
        lua = self.make_runtime(POPULATED + '''
            local box = LegacySystemFrame.ChallengesPage.DetailPane.ScrollBox
            function box:GetDataProvider() error("protected provider unavailable") end
            function LegacySystemFrame:GetChildren() error("protected children unavailable") end
            function LegacySystemFrame:GetScript() error("protected scripts unavailable") end
            function LegacySystemFrame.RewardTrackPage:GetRegions() error("protected regions unavailable") end
        ''')
        report = self.inspect(lua)
        self.assertRegex(report.lower(), r"protected|failed|unavailable|error")
        self.assertIn("RECOMMENDED INTEGRATION POINTS", report)

    def test_forbidden_objects_are_not_inspected(self):
        lua = self.make_runtime(POPULATED + '''
            local reward = LegacySystemFrame.RewardTrackPage
            function reward:IsForbidden() return true end
            reward.GetChildren = Forbidden("forbidden GetChildren")
            reward.GetRegions = Forbidden("forbidden GetRegions")
            reward.GetScript = Forbidden("forbidden GetScript")
        ''')
        report = self.inspect(lua)
        self.assertRegex(report.lower(), r"forbidden|restricted|unavailable|skip")

    def test_combat_defers_native_inspection(self):
        lua = self.make_runtime(POPULATED + '''
            function InCombatLockdown() return true end
        ''')
        report = self.inspect(lua)
        self.assertIn("combat", report.lower())
        self.assertFalse(any(key.endswith(":GetChildren") for key in lua.globals().getterCalls.keys()))

    def test_secret_values_are_redacted_without_conversion(self):
        lua = self.make_runtime(POPULATED + '''
            local secret = setmetatable({}, {
                __tostring = Forbidden("secret value conversion"),
                __index = Forbidden("secret value indexing"),
            })
            function issecretvalue(value) return value == secret end
            provider.collection[1].progress = secret
            LegacySystemFrame.RewardTrackPage.currentLegacyPoints = secret
        ''')
        report = self.inspect(lua)
        self.assertRegex(report.lower(), r"secret|restricted|unavailable|redact")

    def test_cycles_and_depth_are_bounded(self):
        lua = self.make_runtime(POPULATED + '''
            local r = LegacySystemFrame
            r.cycle = r
            provider.collection[1].cycle = provider.collection[1]
            local current = r
            for depth = 1, 9 do
                local child = NativeFrame("InspectorDepth" .. depth, current)
                current.children[#current.children + 1] = child
                current = child
            end
            current.secret = "DEEP_DATA_SENTINEL"
        ''')
        report = self.inspect(lua)
        self.assertNotIn("DEEP_DATA_SENTINEL", report)
        self.assertFalse(lua.globals().getterCalls["InspectorDepth9:GetChildren"])
        self.assertLess(len(report), 60001)

    def test_object_budget_limits_inspection_work(self):
        lua = self.make_runtime('''
            LegacySystemFrame = NativeFrame("LegacySystemFrame", UIParent)
            for index = 1, 200 do
                local f = NativeFrame("BudgetChild" .. index, LegacySystemFrame)
                LegacySystemFrame.children[index] = f
            end
        ''')
        lua.globals().ns.LegacyInspector.Config.maxObjects = 3
        self.inspect(lua)
        inspected = {key.split(":")[0] for key in lua.globals().getterCalls.keys() if key.endswith(":GetChildren")}
        self.assertLessEqual(len(inspected), 3)

    def test_output_size_cap_applies_to_large_native_strings(self):
        lua = self.make_runtime(POPULATED + '''
            provider.collection[1].description = string.rep("long-description ", 20000)
        ''')
        lua.globals().ns.LegacyInspector.Config.maxOutputChars = 1200
        report = self.inspect(lua)
        self.assertLessEqual(len(report), 1200)

    def test_entry_budget_limits_native_provider_records(self):
        lua = self.make_runtime(POPULATED + '''
            provider.collection = {}
            for index = 1, 100 do
                provider.collection[index] = {
                    challengeID = 10000 + index,
                    name = "BoundedEntry" .. index,
                    progress = index,
                }
            end
        ''')
        lua.globals().ns.LegacyInspector.Config.maxEntries = 2
        report = self.inspect(lua)
        self.assertIn("BoundedEntry1", report)
        self.assertNotIn("BoundedEntry100", report)
        self.assertNotIn("10100", report)

    def test_missing_property_path_sparse_provider_is_sampled_only_once(self):
        lua = self.make_runtime(POPULATED + '''
            LegacySystemFrame.ChallengesPage = nil
            provider.collection = {
                [100] = { challengeID = 100, name = "SparseBudgetRecordA" },
                [10001] = { challengeID = 10001, name = "SparseBudgetRecordB" },
                [5] = { challengeID = 5, name = "SparseBudgetRecordC" },
            }
        ''')
        lua.globals().ns.LegacyInspector.Config.maxEntries = 1
        report = self.inspect(lua)
        self.assertIn("ScrollBox: FOUND", report)
        records = set(re.findall(r"SparseBudgetRecord[ABC]", report))
        self.assertEqual(len(records), 1, "General frame dumps must not bypass the provider's single sampling budget")

    def test_namespace_budget_limits_global_frame_introspection(self):
        lua = self.make_runtime('''
            C_Legacy = nil
            GetAchievementInfo = nil
            LegacyUnknownFunction = nil
            for index = 1, 100 do
                local name = "LegacyBudgetNamespace" .. index
                _G[name] = NativeFrame(name, UIParent)
            end
        ''')
        lua.globals().ns.LegacyInspector.Config.maxGlobalMatches = 3
        self.inspect(lua)
        visited = {
            key.split(":")[0]
            for key in lua.globals().getterCalls.keys()
            if key.startswith("LegacyBudgetNamespace")
        }
        self.assertLessEqual(len(visited), 3)

    def test_unrelated_ui_and_metatables_are_not_walked(self):
        lua = self.make_runtime(POPULATED + '''
            local outside = NativeFrame("UnrelatedChatWindow", UIParent)
            outside.GetChildren = Forbidden("unrelated UI traversal")
            outside.GetRegions = Forbidden("unrelated UI regions")
            outside.payload = "UNRELATED_UI_SENTINEL"
            LegacySystemFrame.unrelatedFrame = outside
            local traps = {}
            setmetatable(traps, {
                __index = Forbidden("unknown table __index"),
                __tostring = Forbidden("unknown table __tostring"),
                __pairs = Forbidden("unknown table __pairs"),
            })
            LegacyChallengeOpaqueTable = traps
        ''')
        report = self.inspect(lua)
        self.assertNotIn("UNRELATED_UI_SENTINEL", report)

    def test_copy_window_runs_clears_closes_and_reuses_owned_widgets(self):
        lua = self.make_runtime(POPULATED)
        command = self.slash_handler(lua)
        command()
        widgets = list(lua.globals().uiFrames.values())
        edits = [widget for widget in widgets if widget.kind == "EditBox"]
        self.assertEqual(len(edits), 1)
        edit = edits[0]
        self.assertTrue(edit.multiline)
        self.assertFalse(edit.autofocus)
        self.assertGreaterEqual(edit.maxletters, 60000)
        # Copy/select shortcuts are handled by the native EditBox. The addon
        # must leave those keys available instead of replacing keyboard input.
        self.assertIsNone(edit.scripts.OnKeyDown)
        self.assertIsNone(edit.scripts.OnChar)
        buttons = {widget.text: widget for widget in widgets if widget.kind == "Button"}
        for label in ("Run Inspection", "Clear Results", "Close"):
            self.assertIn(label, buttons)
        window = buttons["Close"].parent
        self.assertTrue(window.shown)
        self.assertIsNotNone(window.name)
        self.assertIn(window.name, list(lua.globals().UISpecialFrames.values()))
        buttons["Run Inspection"].scripts.OnClick(buttons["Run Inspection"])
        self.assertIn("FOREVER LEGACY INSPECTOR", edit.text)
        self.assertIn("Explore Mock Kingdom", edit.text)
        self.assertLessEqual(len(edit.text), 60000)
        buttons["Clear Results"].scripts.OnClick(buttons["Clear Results"])
        self.assertEqual(edit.text, "")
        edit.SetFocus(edit)
        self.assertTrue(edit.focused)
        buttons["Close"].scripts.OnClick(buttons["Close"])
        self.assertFalse(window.shown)
        self.assertFalse(edit.focused)
        previous_count = len(widgets)
        command()
        self.assertTrue(window.shown)
        self.assertEqual(len(list(lua.globals().uiFrames.values())), previous_count)
        self.assertEqual(list(lua.globals().UISpecialFrames.values()).count(window.name), 1)
        self.assertEqual(list(lua.globals().forbiddenCalls.values()), [])

    def test_combat_blocks_copy_window_creation(self):
        lua = self.make_runtime(POPULATED + '''
            function InCombatLockdown() return true end
        ''')
        before = len(list(lua.globals().uiFrames.values()))
        self.slash_handler(lua)()
        self.assertEqual(len(list(lua.globals().uiFrames.values())), before)
        self.assertEqual(list(lua.globals().forbiddenCalls.values()), [])

    def test_long_wrapped_report_has_scrollable_copy_height(self):
        lua = self.make_runtime()
        self.slash_handler(lua)()
        widgets = list(lua.globals().uiFrames.values())
        edit = next(widget for widget in widgets if widget.kind == "EditBox")
        run = next(widget for widget in widgets if widget.kind == "Button" and widget.text == "Run Inspection")
        lua.globals().ns.LegacyInspector.Inspect = lua.eval('function() return string.rep("W", 10000) end')
        run.scripts.OnClick(run)
        self.assertEqual(len(edit.text), 10000)
        self.assertGreater(edit.height, 1000, "Wrapped text must expand the scroll child beyond newline-only height")

    def test_native_text_height_is_respected_when_available(self):
        lua = self.make_runtime()
        self.slash_handler(lua)()
        widgets = list(lua.globals().uiFrames.values())
        edit = next(widget for widget in widgets if widget.kind == "EditBox")
        run = next(widget for widget in widgets if widget.kind == "Button" and widget.text == "Run Inspection")
        edit.GetTextHeight = lua.eval('function() return 5000 end')
        lua.globals().ns.LegacyInspector.Inspect = lua.eval('function() return "A short mock report" end')
        run.scripts.OnClick(run)
        self.assertGreater(edit.height, 5000)

    def test_toc_loads_diagnostic_once(self):
        references = [
            line.strip().replace("\\", "/")
            for line in (ROOT / "ForeverAchievements" / "ForeverAchievements.toc").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(references.count("Diagnostics/LegacyInspector.lua"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
