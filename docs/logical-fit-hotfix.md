# Compact opening regression: logical fit hotfix

Build: `0.4.15-alpha-fitfix1`. This includes the previous combat fix.

The client reported an exact reproduction: the Compact cover's `GetWidth()`
returned **767.99981689453**, `GetHeight()` returned **640.00006103516**, and scale
was **1**. The requested size was 768 × 640, including header/footer space.

`C:Fit` set the selected preset, then `U.Fit` read the frame geometry back to
derive the body dimensions. `U.Layout` correctly rejected a body width below 768.
The small readback rounding difference therefore triggered `C:Fail`, restored
the stock Legacy appearance, and prevented Compact from reopening. Re-selecting
Compact repeated the same readback and rejection. This was a dimension-validation
failure; no combat restriction was needed. The earlier fixtures returned exact
integer geometry and missed it.

The controller now passes its exact selected logical body dimensions into
`U.Fit`. Scaling and positioning remain on the outer cover. Existing callers
without explicit dimensions retain measured-host fitting and the minimum-size
check; genuinely invalid supplied logical dimensions still fail. There is no
broad size clamp, weakened minimum, guessed preset or disabled fallback.

Changed files:

- `ForeverAchievements/Integrations/LegacyController.lua`: `C:Fit` passes the exact preset dimensions.
- `ForeverAchievements/UI/WrathAchievementUI.lua`: `U.Fit` accepts a validated pair of logical dimensions.
- `ForeverAchievements/ForeverAchievements.toc`: version only.
- `tests/test_legacy_logical_fit.py`: six regressions, including the reported client readback.
- `docs/logical-fit-hotfix.md`: cause, correction and validation.

Preset dimensions, artwork, categories, progress, SavedVariables and the combat
lifecycle correction are unchanged. Six focused tests cover Compact opening,
repeated preset changes/reopening, a scaled-down screen, combat state retention,
and rejection of genuinely invalid dimensions. They execute the actual Lua/XML
with explicit client doubles; in-game confirmation of this build is still pending.

Validation: all **568 tests passed**, including the six new regressions. Lua 5.1
syntax checks passed for 27 files; packaging checks passed for 28 TOC references
and four XML files. Core initialization loaded 322 definitions and the isolated
behavior check passed 14 assertions. These checks do not replace client testing.

To install, replace the complete `ForeverAchievements` addon folder with this
build, retaining your existing WTF/SavedVariables. Run `/reload`, leave combat,
then `/fa legacyui size compact` and `/fa legacyui on`. Open Legacy normally.
Confirm the custom interface opens without the minimum-dimensions fallback.
Check Standard and Large, close/reopen, then gain aggro while the custom panel
is open and verify the combat fix still retains the custom presentation.
Repeat on native Rewards and Trees. Keep any further fallback text if a distinct
client failure occurs; do not delete saved progress or change UI scale to work
around this rounding error.
