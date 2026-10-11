# Targeted bug fix 1: combat presentation lifecycle

Build: `0.4.14-alpha-combatfix1`, based on Iteration 6. Target: Forever 1.60.1,
build 70338, Interface 16001, Lua 5.1. This changes only controller combat behavior.

## Reproduced cause

The addon explicitly tore down its presentation on `PLAYER_REGEN_DISABLED`:
`OnEvent` → `C:Release("Waiting for combat to end")` → `bridge:Restore()` →
native regions/tabs restored and custom cover hidden. `C:Refresh` repeated that
same teardown whenever `InCombatLockdown()` returned true. The replacement option
remained enabled, but the mounted bridge was discarded.

This was reproduced using the actual addon Lua with unprotected frame doubles:
before the event, custom cover visible / stock background hidden; afterwards,
custom cover hidden / stock background visible / bridge absent. No Lua error or
protected-action rejection was needed. It was an intentional combat release,
not an error-handler fallback. The inspected native build's Legacy root
`OnShow`/`OnHide` and page-selection callbacks contain no matching combat release.

Two adjacent controller paths also needed combat handling: blocked close requests
called `C:Fail`, treating an ordinary restriction as a presentation error, and the
native root's hide hook could replay restoration while the client was locked.

## Correction

- Combat entry retains the existing cover, UI, bridge, model, selected tab,
  category, expansion and scroll state. It invalidates queued controller/UI work
  and retains dirty flags for one subsequent safe refresh. A pending search/render
  is retained as a render request. The event never requests native restoration.
- Refresh, attach, native selection coordination and scheduling defer during
  lockdown. They do not repeatedly queue retries, scan providers, create frames,
  change native geometry or reinitialize native pages. Native selection callbacks
  recheck lockdown after their queued delay and retain the custom tab.
- `PLAYER_REGEN_ENABLED` consumes deferred work through the existing controller
  path and remounts the retained view. An unchanged model needs no rebuild or
  render. Native Rewards/Trees still use their original handlers and controls.
- A legal close still invokes the native close path. A protected/forbidden root
  defers the close request until combat ends, without calling the fallback handler.
  If the client hides its root, the ordinary custom cover follows it; the bridge
  and navigation remain retained. An existing cover can reappear when the client
  permits reopening, without native mounting during combat. Restricted cover
  visibility changes wait until after combat. A closed root is not automatically
  reopened when combat ends.
- Actual errors still reach `C:Guard`/`C:Fail` and report their original cause.
  A genuine disable, input-mode restoration or fallback request defers native
  restoration while combat is active. It does not force protected changes or
  discard the saved bridge snapshot. Existing restoration failure handling remains.
- Initial replacement activation during combat remains deferred. The disabled
  replacement leaves the normal native combat lifecycle alone.

All deferred flags are session state. There is no SavedVariables migration or new
saved field. Tracking, completion, point calculations, category mapping, artwork,
templates, presets, window geometry, native progression and backend APIs are unchanged.

## Changed files and functions

| File | Change |
| --- | --- |
| `LegacyAchievementsReforged/Integrations/LegacyController.lua` | New `C:DeferCombat`; combat handling in `Release`, `Refresh`, `QueueRefresh`, `QueueAttach`, `Close`, `NativeSelection`, `Attach`, root visibility hooks and event callback |
| `LegacyAchievementsReforged/LegacyAchievementsReforged.toc` | Version only |
| `tests/test_legacy_combat.py` | Combat lifecycle regression tests using actual controller, bridge and UI Lua/XML |
| `docs/combat-ui-regression-fix.md` | Cause, behavior, validation and client procedure |

## Automated validation and limits

All **14 new combat tests** and the complete **562-test** Lua 5.1 regression suite
pass. Setup validation passes 27 Lua syntax checks, 28 TOC references, four XML
files, initialization of 322 definitions and 14 isolated behavior assertions.

The dedicated tests cover all four tabs, valid scroll/expansion preservation,
queued work cancellation, coalesced data events, delayed selection callbacks,
protected close and native/cover visibility restrictions, initial activation,
disabled operation, deferred disable and genuine error recovery. They reject
native mounting/restoration during lockdown and check that no new frames or
unnecessary model builds occur across a plain combat transition.

These are Lua 5.1 fixtures with explicit client doubles. They do not establish
live aggro behavior, taint safety, client-specific panel restrictions, server
progression or absence of real script timeouts. In-game validation is pending.

## Manual in-game procedure

1. Replace the complete addon folder while keeping existing WTF/SavedVariables.
   Leave combat, enable `/lar legacyui on`, and enable `/lar perf on` if timing
   evidence is wanted. Open the custom Achievements tab through the usual Legacy
   control. Select a category, expand an achievement and scroll to a recognizable
   position. Record the selected tab and both point totals.
2. Gain aggro from a hostile NPC with the panel open. Confirm the Wrath presentation
   remains visible where the client permits it, with the same tab, category,
   expanded card and scroll position. No stock borders/tabs should appear merely
   because combat began. There must be no new fallback or protected-action error.
3. Leave combat. Confirm the same presentation and navigation remain correct;
   any real progress updates may now appear. Check that no unexpected native page
   selection, duplicate initialization or extra points occurred.
4. Close and reopen after combat using the close button, Escape and normal Legacy
   toggle. Then repeat a permitted close during combat. If close is restricted,
   it should wait until combat ends without a fallback message. If the game closes
   the panel itself, the custom cover should follow safely and the panel must not
   reopen automatically on combat exit. Reopen normally when permitted.
5. Repeat steps 1–4 with **Legacy Rewards** selected, then **Legacy Trees**. Use
   their existing controls where the client permits them. Their original native
   behavior, staged changes and progression must remain intact. Also check
   Statistics retains its tab/navigation across combat.
6. Repeat several combat cycles, including queued search/data refreshes and
   opening/closing around combat entry. Check for script timeouts, protected-action
   errors or unexpected fallback messages. Preserve any error text and
   `/lar perf report`; confirm queued work settles after combat.
7. Outside combat, run `/lar legacyui off` and repeat opening, gaining aggro,
   leaving combat and closing with the native interface. Confirm normal native
   behavior. If disabling during combat, restoration should wait until combat
   ends. Re-enable outside combat if desired.
8. Turn diagnostics off, reload and verify existing achievement history, current
   progress and native points remain intact. Do not reset valid progress or make
   irreversible tree/reward changes just to test this presentation fix.
