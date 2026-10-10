# Iteration 2 native Legacy presentation research

This is source-based compatibility research, not an in-game validation report. The public Blizzard UI mirror was read on October 10, 2026. No GPL or proprietary community implementation was copied into the addon.

## Exact client source

[Gethe/wow-ui-source, `forever`, commit `943764493e6b16d63ded3ab304150d1f05e58b57`](https://github.com/Gethe/wow-ui-source/tree/943764493e6b16d63ded3ab304150d1f05e58b57) reports `1.60.1.70338` in `version.txt`. This matches the client build in the user's inspection reports. The local research checkout is not part of the installed addon.

The MIT-licensed [LegacyNext](https://github.com/lxhwes/LegacyNext) documentation provided the initial source citations. Its latest recorded pin was build 70205; the contracts below were checked again directly against build 70338 rather than assuming that older pin was current.

## Window and page contracts

`Interface/AddOns/Blizzard_LegacySystem/Blizzard_LegacySystem.xml:4-42` defines an unprotected-template `PortraitFrameTemplate` root, `LegacySystemFrame`, with a 920 by 575 logical size. It contains these direct pages, in this order:

| Native page ID | Root field | Native content |
| --- | --- | --- |
| 1 | `RewardTrackPage` | Native renown reward track |
| 2 | `ChallengesPage` | Native challenge browser |
| 3 | `TreePage` | Native trait tree selection and editing |

The pages are retained in `root.Pages`; original side tabs are retained in `root.Tabs`. `LegacySystemFrameMixin:SelectPage(id)` in `Blizzard_LegacySystem.lua:69-79` updates `root.currentPage`, calls `SetShown` on the existing pages, and updates the original checked side tabs.

The verified page-selection entry point is `EventRegistry:TriggerEvent("Legacy.SelectPage", id)`. The root's callback at `Blizzard_LegacySystem.lua:12-15` invokes `SelectPage(id)` followed by `UpdateSmartNavFocus(id)`. No global function replacement or custom native progression implementation is required.

`Blizzard_LegacySystemRegistration.lua:2-11` registers the root as a left-area UI panel, with `xoffset=35`, `pushable=1`, `allowOtherPanels=1`, `checkFit=1`, and `width=1005`. Retaining that registration preserves panel closing and other panel relationships. Its reserved horizontal space remains the native reservation even when the visible replacement is smaller.

`ToggleLegacySystemUI()` in `Blizzard_LegacySystem_Bootstrap.lua:7-21` loads the native addon as necessary and uses the normal panel toggle. It intentionally returns without opening at zero Legacy points. The replacement must preserve that native unlock behavior rather than inventing another opening path.

## Reversible visual replacement

Keep the native root shown for its original lifecycle, but temporarily suppress its presentation. The root's portrait template at `Blizzard_SharedXML/Mainline/SharedUIPanelTemplates.xml:566-662` puts the background textures directly on the root and places the following artwork/control objects in direct children: `NineSlice`, `PortraitContainer`, `FrameGlow`, `TitleContainer`, jump hints, and `CloseButton`. The Legacy XML adds its side tabs, tab indicators, and three pages as direct children.

A bounded snapshot of root region visibility and immediate-child visibility, followed by hiding those objects except the selected mounted native page, suppresses all original outer artwork. Temporarily disabling the root's own mouse handling prevents its invisible 920 by 575 rectangle from consuming clicks. The root alpha, scripts, functions, registration, and page collection can remain unchanged. Restoration must replay the recorded presentation states and geometry; failures must leave the normal native window accessible.

For Rewards and Trees, preserve the original parent and every descendant. Snapshot the selected page's anchors, size, scale, frame level, frame strata, and known decorative visibility. Anchor that existing page to the addon-owned full-width content area while keeping `page:GetParent() == LegacySystemFrame`. Fit its native logical dimensions to the content area's effective scale. Hiding the page's `Background`, and the tree's original `VerticalDivider` where appropriate, removes duplicate decorative presentation while retaining every native interactive control and callback.

Page frame strata must be considered as well as frame level: a native page remaining on MEDIUM strata would be obscured by an addon parchment window on HIGH strata regardless of its numerical frame level. Restore both on release. Native UI panel registration should not be rewritten to force the smaller artwork's width.

Do not reparent the pages indiscriminately. `LegacyRewardTrackPageMixin:OnShow()` at `Blizzard_LegacyRewardTrack.lua:24` and `LegacyTreePageMixin:OnShow()` at `Blizzard_LegacyTree.lua:25` call `self:GetParent():SetTitle(...)`. The tree trait panel additionally accesses `self:GetParent():GetParent().footers[3]` during gamepad updates at `Blizzard_LegacyTree.lua:171`. Preserving the native ancestry satisfies both contracts without proxy objects.

## Native interaction and lifecycle

Root `OnShow` and `OnHide` in `Blizzard_LegacySystem.lua:22-66` update microbuttons, sounds, currency information, and gamepad callbacks. Keep those methods and scripts intact; append guarded hooks for replacement lifecycle observation. Closing the addon artwork should close the registered native panel. Do not leave detached native pages visible after native panel closure.

The native reward page initializes its own actual faction data and reward collection during `Refresh`, reads actual point/renown values, and owns its original scrolling, selection, masking, and tooltip behavior. `RewardTrackTemplates.lua` refers to ancestors within the unchanged reward-page subtree, so retaining that subtree preserves those callbacks. In this build the Legacy reward card's mouse interaction centers a card; the replacement should expose the existing behavior rather than adding independent claim calls.

The native tree trait panel wires its own Apply, Undo, and Reset buttons in `Blizzard_LegacyTree.lua:30-46`. Its `OnShow` selects the currently selected tree through the native `Legacy.SelectTree` event and refreshes conditions. Native `TalentFrameBaseMixin:OnHide()` in `Blizzard_SharedTalentUI/Blizzard_SharedTalentFrame.lua:300-308` unregisters events and clears caches and visuals; it does not purchase, reset, or roll back traits. The replacement should drive native visibility and preserve those scripts, leaving all spending and commit behavior to the original controls.

External native page-selection events can show pages while the replacement is active. The controller observes `Legacy.SelectPage` and defers reading `currentPage` until the native callbacks finish. `Blizzard_SharedXMLBase/CallbackRegistry.lua` stores callbacks by owner and uses `secureexecuterange`, so registration order is not guaranteed. The observer coalesces rapid changes and skips events generated by its own mount. Native current-page state is separate from the addon's fourth Statistics tab.

`Blizzard_LegacySystemUtil.lua:35-75` reads authoritative renown through `C_MajorFactions.GetCurrentRenownLevel` and emits `Legacy.UpdateCurrencyInfo`. The controller observes that event to invalidate cached metadata and refresh the separate header values, without changing the supplied native currency object or calling the native currency updater.

## Combat and gamepad fallback

The root and page templates do not declare secure-frame inheritance. This does not prove that every live object is unprotected: runtime `IsProtected` and `IsForbidden` checks remain necessary before presentation changes, along with out-of-combat attachment and safe restoration.

Native SmartNavigation explicitly binds the three original pages and original Challenges controls. A fourth addon tab and an addon-owned achievement browser cannot claim equivalent gamepad navigation without implementing and testing that integration. Restore the original native presentation in gamepad mode instead.

`Blizzard_SharedXML/InputUtil.lua:75-79` handles `INPUT_DEVICE_INTERFACE_TRANSITION(newInterfaceType, oldInterfaceType)` by executing high-priority transition subscribers **before** ordinary subscribers. The native Legacy root registers an ordinary subscriber. The supported helper sequence is:

1. `InputUtil.RegisterForHighPrioInterfaceTransitions(subscriber, nil)`.
2. `InputUtil.RegisterGamepadInit(subscriber, restoreNativeCallback)`.
3. `InputUtil.RegisterMKBInit(subscriber, scheduleReplacementCallback)`.

The Init registration immediately calls its callback if that style is already current (`InputUtil.lua:100-108`). Register only once and make callbacks harmless when the option is off. Restoration in the high-priority Gamepad callback runs before the native root's gamepad setup or initialization. Reattachment for mouse and keyboard should be queued until ordinary transition callbacks have finished. No unregister helper is provided for these transition subscriptions; persistent callbacks must remain gated by settings and current mode.

Input mode is read through `InputUtil.IsGamepadUIEnabled()` in `Blizzard_SharedXML/Mainline/InputUtil.lua:11-13`. If transition hooks or compatible native objects are unavailable, retain accessible native functionality rather than replacing it with disabled reward/tree placeholders.

## Remaining live-client checks

Source review establishes method names and expected lifecycle, not visual behavior on a real client. In-game verification is still needed for cross-parent anchors, scale ratios at different UI scales, clipping, effective page frame strata, tree tooltips and selection popovers, reward track arrows, taint/protection errors, staged tree changes across tab switching, Escape and normal close behavior, and switching input modes while the native window is open.
