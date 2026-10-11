# Combat lockdown follow-up

Build: `0.4.20-alpha-combat2`.

## Confirmed code defects and limits

`LegacyUIController:Close` checked the native root's protection flag, then called
`HideUIPanel` even in combat. That API also operates on Blizzard's protected panel
manager; an ordinary target frame does not make the entire operation safe. The
existing fixture defined `HideUIPanel` as only `frame:Hide()`, missing this path.
A new fixture models a blocked manager call returning without a Lua exception:
the old close implementation would leave the window open without fallback or
a Lua tracker entry. The corrected path avoids the manager call during combat.

Header dragging started movement before consulting the controller. Position
saving/resetting could also write cover anchors or stop movement in combat.
Native pages retain their parents but anchor to our host, so moving the cover
affects that native dependency chain. Scroll, menu visibility and keyboard
callbacks also had direct writes outside the controller guard. These are code
paths that required correction; fixtures cannot establish the exact operation
blocked on the user's live client or prove actual client taint has disappeared.

There is no explicit combat handler that hides the Legacy Points font string.
Currency callbacks did still read the native total in combat and could overwrite
the controller's observed currency with an unavailable read, invalidate its native
catalog and schedule later work. They now retain the current counter/model and
observed currency during combat, marking one native refresh for after regen.
Neither Legacy nor verified character point calculations changed. Counter
visibility is recorded by optional diagnostics to investigate any remaining live
disappearance; its exact live cause remains unconfirmed.

## Targeted corrections

- `Close`: during combat, directly hide the native root only if permitted.
  Reconcile panel-manager bookkeeping once after `PLAYER_REGEN_ENABLED`.
  If the native root is protected, hide the independent owned cover where
  permitted and record a deferred native close. A protected owned cover also
  defers. Repeated clicks queue no timers. A new native open supersedes pending
  bookkeeping for an already closed ordinary root.
- `PresentationAllowed` and the UI guard: defer callbacks when the owned cover,
  root or host becomes protected/forbidden during combat. Close uses its separate
  guard so its pending request is preserved even when content is restricted.
- `StartDrag`, `FinishDrag`, `RestorePosition`, `SavePosition`, `ResetPosition`:
  no combat movement/anchor writes; interrupted drag cleanup and explicit reset
  finish after regen. Current navigation/model/expansion remain intact.
- Scroll arrow/wheel/slider and menu show/hide/key callbacks: use the same
  presentation guard before writes. No frame hierarchy or artwork changes.
- `CurrencyChanged`: combat updates coalesce into the existing native dirty flag;
  the next permitted build reads the authoritative total normally.
- Bridge `Select`, `Suppress`, `Mount` and `Restore`: explicit final lockdown
  checks prevent native mutations even if called outside the controller path.

Genuine presentation errors still use the existing error recovery and native
fallback. No Blizzard callbacks, globals, panel attributes, progression controls
or protected frame ancestry are replaced. No secure templates, new presentation
frames, refresh tickers, catalog scans or additional event refresh loops are added.

Runtime files changed: `Integrations/LegacyController.lua`,
`Integrations/LegacyWindowBridge.lua`, `UI/WrathAchievementUI.lua`, and the TOC
version. Tracking, data definitions, adapters/calculations, SavedVariables schema,
XML/artwork/layout and the original alpha quarantine are unchanged.

## Optional diagnostics

Use `/lar combatdebug on` before reproducing; `/lar combatdebug report` afterward.
The bounded session-only log retains at most 16 observations, including combat
transitions, close requests and `ADDON_ACTION_BLOCKED`/`ADDON_ACTION_FORBIDDEN`
notifications. It records root/cover visibility, cover restrictions, pending close,
Legacy counter visibility, and the addon/operation names supplied by those events.
It does not write SavedVariables or emit per-event chat spam. `/lar combatdebug off`
stops collection; `reset` clears it. Native blocked-action reporting remains intact;
these notifications alone do not activate fallback or refresh the catalog.

## Client verification required

Replace the full addon folder, keep WTF/SavedVariables, and `/reload`.

1. Enable `/lar legacyui on` and diagnostics. Open outside combat. Note both point
   counters, selected category/tab, expanded achievement and scroll positions.
2. Gain aggro. Verify the displayed totals and custom presentation stay consistent.
   Try closing; it should close immediately where permitted, otherwise after regen.
3. Reopen through the normal Legacy control during combat where the client permits.
   An initialized presentation is reused; initial attachment waits for regen.
4. Leave combat. Confirm no unexpected reopen, stock fallback, lost navigation,
   duplicate refreshes or point changes except actual authoritative progression.
5. Repeat on Rewards, Trees and Statistics. Test entering combat during a header
   drag, releasing the mouse and then leaving combat. New drags wait for regen.
6. Reopen/close outside combat and check size presets, categories and scrolling.
   Repeat with `/lar legacyui off` to confirm normal native behavior.
7. Check the built-in action-failed notification, Lua tracker, fallback messages
   and `/lar combatdebug report`. If the counter still disappears, capture a report
   while it is missing and another after combat, before disabling diagnostics.

Tests simulate protected flags, restricted setters and a silent panel-manager
denial; they do not emulate the actual WoW secure execution engine or prove
in-game taint safety. Do not consider the live issue resolved before these checks.

Validation: **609 automated tests passed**, including ten new lockdown checks
and existing combat, opening, navigation, counters, performance and progression
regressions. Lua 5.1 syntax passed for 28 files; packaging passed for 29 TOC
references and four XML files. Core initialization loaded 322 definitions and
the isolated behavior check passed 14 assertions.
