# Native window flash during custom opening

Build: `0.4.16-alpha-openfix1`, including the combat and Compact fit fixes.

The native `ShowChallenges` implementation calls `ShowUIPanel` before sending
`Legacy.SelectPage`. Closing the replacement intentionally restores the native
window. On the next open, our `OnShow` observer queues an attach so the native
handlers and final page selection can finish before building/rendering our view.
That left the restored stock screen drawable during the handoff, consistent with
the reported brief flash. The test fixture now checks this interval before any
deferred timers run, rather than only the final mounted state.

The controller temporarily sets the ordinary native root's opacity to zero
during that handoff. Its visibility, scripts, providers and page-selection
callbacks continue normally. The original opacity is restored after mounting
the replacement and showing its independent cover. This also restores normal
opacity for the native Rewards/Trees pages, whose parent remains the native root.
No synchronous database rebuild was added to `OnShow`; deferred initialization,
coalescing and the existing performance guards remain intact.

The temporary opacity snapshot belongs to the controller, independently of the
page bridge, so failures before bridge creation still restore the stock screen.
Close, disable and genuine fallback all restore it. Combat interruptions restore
it only when the native root is unprotected; protected restoration waits until
permitted. Gamepad mode bypasses concealment and restores native presentation
before ordinary-priority native input initialization. Lua errors still use the
existing fallback and are reported.

Changed files:

- `LegacyAchievementsReforged/Integrations/LegacyController.lua`: new `BeginOpening` and
  `RestoreOpening`; integrates them into `Attach`/`OnShow`, `Refresh`, `Release`
  and the interrupted-opening path in `DeferCombat`.
- `LegacyAchievementsReforged/LegacyAchievementsReforged.toc`: version only.
- `tests/test_legacy_wrath_ui.py`: permits the reversible native root opacity setter.
- `tests/test_legacy_opening.py`: handoff visibility, final selection, repeated
  opening on all native pages, frame reuse, early close/disable, build/mount/
  opacity failures, combat interruption, protected restoration and gamepad mode.
- `docs/opening-flash-fix.md`: cause and verification.

Achievement progress, SavedVariables, points, artwork, categories, window size,
layout and native progression are unchanged. Client rendering and protected
action behavior must still be verified in-game.

Validation: **579 tests passed**, including 11 new opening regressions and the
existing combat, sizing and performance checks. Lua 5.1 syntax checks passed for
27 files; packaging checks passed for 28 TOC references and four XML files. Core
initialization loaded 322 definitions and the isolated behavior check passed
14 assertions. The fixture verifies state before/after deferred work; it does
not measure live client rendering or prove the reported flash is gone in-game.

## Manual client checks

Install the complete addon folder, preserve WTF/SavedVariables, then `/reload`.
Enable replacement with `/lar legacyui on` outside combat.

1. Open Legacy normally: the stock screen should not briefly appear. Close and
   reopen several times, including the first open after another `/reload`.
2. Repeat after selecting Achievements, Legacy Rewards and Legacy Trees. Native
   content should become visible normally inside the custom presentation.
3. Repeat on Compact, Standard and Large; verify the sizing hotfix remains intact.
4. Gain aggro with the custom panel open, leave combat, then close/reopen. Check
   for protected-action errors, fallback messages and unexpected stock appearance.
5. Close immediately after opening; verify deferred work does not reopen it.
6. Use `/lar legacyui off`: native opening and closing should work normally with
   the original opacity. Re-enable and repeat. If gamepad input is available,
   verify native gamepad mode and the return to mouse/keyboard input.

In-game confirmation of this build remains pending.
