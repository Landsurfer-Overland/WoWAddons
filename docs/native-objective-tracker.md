# Tracked achievements in client objectives

Current build `0.5.1-alpha` on `main`, promoted from `achievement-alerts-test`.
The integration was introduced in `0.5.1-alpha-alert-test5` and is included in
the tagged GitHub prerelease. No CurseForge upload is performed. The manual
checks below remain necessary for live-client verification.

The old `Tracker.lua` only created a separate movable alpha frame. It never
registered watches with the client objective tracker. WoW Forever's in-game
dump confirmed `ObjectiveTrackerFrame.AddModule` is a function and
`ObjectiveTrackerModuleMixin` is a table, including the module layout methods.
The new `Integrations/ObjectiveTracker.lua` uses that module API rather than
inventing native achievement IDs or replacing Blizzard's achievement data.

## Behavior

- Existing tracked custom achievements appear under **Reforged Achievements**
  in the same objective tracker as quests. No separate floating box is shown.
- The client supplies block fonts, objective styling, available height,
  frame pooling and the section collapse button. Moving/hiding/collapsing the
  client tracker controls this section normally; it has no independent position.
- Right-click an entry to stop tracking. Left-click uses the native Legacy
  `ShowChallenges` entry point when available and allowed, then searches the
  owned presentation. If that entry point/presentation is unavailable, the
  addon asks the player to open the Legacy panel rather than force native UI.
- `/lar tracker off` hides the section without forgetting tracked keys.
  `/lar tracker on` shows it again. `/lar tracker status` reports registration,
  display snapshot count and combat state.
- Old tracker size/background/position preferences remain saved. They do not
  resize, recolor or reposition the client's tracker. The retained alpha frame
  is used by archived research tests when the integration module is absent.

Only existing per-character custom watches are presented. Native achievement
tracking, quest watches, Legacy progression, counters and completion conditions
remain unchanged. Missing/unsupported definitions follow existing handling;
unknown progress remains **Unavailable**, and confirmed zero remains zero.

## Performance and combat

The original core watch limit is ten. Progress is sampled only for these watches
within the existing shared snapshot scope. The module stores name/key/progress
text; native layout and collapse callbacks never evaluate progress or scan the
achievement database. Changed snapshots mark the module dirty through the
client scheduler. Repeating an unchanged update does not dirty native layout.
The existing three-second poll runs for registered, nonempty watches outside
combat. It does not poll when there are no watches or the API is unavailable.

Registration/refresh requests and native block layout defer during combat.
The module's combat Update returns its cached height/truncation, retaining the
last rendered rows. Tracking changes and completion still update normal saved
state; the visual section catches up after `PLAYER_REGEN_ENABLED`. A click to
open the Legacy presentation in combat is also deferred. Native tracker frame
protection/forbidden checks prevent forced operations. No native API, frame
script or tracked-ID provider is replaced.

Late initialization retries through coalesced login/world/addon-load events.
If the API is incompatible or protected, watches remain saved and the addon
reports the integration state; it does not silently recreate the floating box.

## Manual client checks

1. Install the release ZIP over the addon folder, retain SavedVariables, `/reload`.
   Existing incomplete watches should appear in the client objective tracker.
2. Track an incomplete quest-count or fishing achievement from the achievement
   window. Verify its name and current/required count beside normal quest entries.
   Confirm the old cyan/black floating frame is absent.
3. Track several entries. Collapse/expand the Reforged Achievements section and
   the full objective tracker. Check that client height limits and positioning
   are respected and quest entries continue to function.
4. Make progress through normal play. Check count updates, then earn an entry;
   verify its watch disappears with normal completion/history/points unchanged.
5. Right-click to untrack. Test `/lar tracker off`, then `on`; selection should
   remain saved across hiding and `/reload`.
6. Click an entry to open/search the Legacy achievement presentation when the
   native entry point is available. Test clicking it in combat and leaving combat.
7. Enter combat, make progress, and track/untrack where the achievement UI allows.
   The last rendered section may remain until combat ends; it must then refresh
   without duplicate entries, protected-action messages or Lua errors.
8. Compare native quest watches and Rewards/Trees before/after. If the section
   does not appear, record `/lar tracker status` and any Lua/protected-action error.

## Verification

Twelve new tests execute the real core watch and completion callbacks against an
explicit modern native-module contract double. They cover pooled native blocks,
unchanged refresh suppression, shared progress reads, unknown/zero/money text,
untracking, natural completion, collapse/height limits, visibility settings,
late initialization, both manager/direct AddModule registration, restricted
frames and combat-deferred opening/refresh. Full suite: **678 tests passed**.
Lua 5.1 syntax: 31 files; 32 TOC references and four XML dependencies passed;
322-definition initialization and 14 core behavior assertions passed.
These checks do not establish live-client font rendering or absence of taint.

The modern method contracts were inspected in the
[Blizzard objective tracker source mirror](https://github.com/Gethe/wow-ui-source/tree/09b9db7948abc9b9648dedaab51eb0cf3ee67b31/Interface/AddOns/Blizzard_ObjectiveTracker).
The client dump confirms API presence, not exact source identity. No upstream
tracker code is bundled or loaded into the addon.
