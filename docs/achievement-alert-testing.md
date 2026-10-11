# Achievement alert testing

Current build: `main`, version `0.5.1-alpha`, promoted from
`achievement-alerts-test` (`0.5.1-alpha-alert-test6`). The matching version tag
publishes a GitHub prerelease after checks pass. No CurseForge upload is
performed. Install one version of the addon at a time, using the same
`LegacyAchievementsReforged` folder. This build keeps the current save names.
The checks below remain necessary for live-client verification.

## What to expect

The popup is a classic 300 × 88 logical-unit gold achievement banner: icon frame
on the left, achievement name in the middle, gold shield/points on the right.
It fades in over 0.2 seconds, flashes a gold glow, sweeps a shine across once,
holds for the configured duration, then fades out over 1.5 seconds. Turning off
animation leaves a static banner for the chosen hold duration. Scale and top
offset are adjustable. The preview has a separate visible PREVIEW label below
the banner so it cannot be confused with a real unlock.

**Achievement chime (bundled)** uses the supplied `AchievmentSound1.ogg`, copied
unchanged to `Media/AchievementEarned.ogg`. It plays through `PlaySoundFile`
instead of relying on the client's sound database. The reported client accepted
sound kit **12891** but played nothing; direct file playback avoids that route.
On the first login with this build, only the sound selection is switched to the
recording and a one-time preference marker is stored. Mute and channel settings
are retained. Later deliberate selections are not reset on login. **Use original
achievement chime** selects and tests this file again without awarding progress.

**Classic chime (client kit/WAV/OGG)** remain explicit compatibility probes;
their sources are not verified audible/present on WoW Forever. Each click requests
only the selected source, with no hidden retry or substitution. Status includes
the requested kit/file and read-only client audio enable/volume values.

**Use bundled Reforged chime** selects and tests the project's own bell chime
via `PlaySoundFile`. This is a shipped PCM WAV independent of the client sound
kit database. It is an original sound, not the original Wrath recording. The
selection persists and applies to both previews and normal custom unlocks.
The client's own native award notifications remain under its control.
Other choices are Level up, Quest complete and Ready check. Master/SFX channel selection
controls which client volume affects playback. The explicit sound-test button
plays even if automatic achievement sounds are disabled; the popup follows the
sound checkbox. If a sound is missing or playback is declined, the settings page
reports that result instead of substituting an unrelated sound. Actual audible
volume, client audio mute state and asset availability require in-game checks.

Actual custom completions use this same presentation through the existing
completion function. Recording, hooks, point calculations, history, screenshot
preferences and native Legacy progression remain intact. Native achievement
notifications stay with the game; this module does not register native award
events or create a second popup for those events.

## In-game procedure

1. Install the release ZIP over the current `LegacyAchievementsReforged` folder.
   Retain your WTF/SavedVariables, then `/reload`. A player still on a previous
   addon identity should first use the existing [migration guide](save-migration.md).
   This build also replaces the inherited addon-list/minimap artwork with the
   project's own gold hammer-and-anvil icon. Restart the client if it still shows
   a cached old texture, then check the AddOns list again.
2. Open **Settings → AddOns → Legacy Achievements Reforged**, or `/lar settings`.
   Older clients use their Interface → AddOns category. A standalone owned page
   is available if neither settings API exists.
3. Click **Test popup**. Verify gold artwork, icon/shield alignment, readable
   title, PREVIEW label, fade/glow/shine and one chime. Note any missing textures
   or clipping; the isolated tests do not establish pixel rendering.
4. Click **Play selected sound**; cycle **Sound** and **Channel** to compare.
   Test **Use original achievement chime**, then **Test popup** and a normal custom
   completion. If silent, retain the exact status message with source/channel
   and audio values; check client audio settings. Test client WAV/OGG separately
   to determine whether a legacy asset path resolves. No external download is
   required for the bundled chime. **Use bundled Reforged chime** still selects
   the alternate original project bell. The addon does not change client volume/mute.
   Disable automatic sound and confirm popup preview is silent while the explicit
   sound button still works. Client audio settings still apply.
5. Change hold time, top distance and scale; test again. Disable animation and
   verify static display/expiry. Rapid repeated tests restart the same preview.
   **Stop preview** cancels only previews, not real achievement notifications.
6. Confirm achievement totals/history/completion status did not change after
   previews. Reopen settings and `/reload` to check preferences persist.
7. Use `/lar alert test` in combat. Verify no protected-action errors or Legacy
   appearance changes. Opening settings during combat defers the settings window
   until combat ends; the owned preview itself remains usable.
8. Earn a real custom achievement through normal play. Confirm it is recorded
   once, plays one new popup, has no PREVIEW label, and retains normal tracking/
   chat behavior. Existing achievements at login should still complete quietly.
9. Verify normal achievement navigation, native Rewards/Trees and native alerts
   still work. To roll back, reinstall your previous working ZIP; keep the same
   save files.

## Implementation and verification

`UI/AchievementAlerts.lua` owns a single reused, click-through, unprotected frame.
Its OnUpdate handler is attached only during an active alert, does constant work,
uses snapshotted hold/animation preferences, and is removed on finish/hide. It
does not scan achievement catalogs, refresh providers, inherit native alert
scripts, or schedule preview timers. The FIFO holds at most 32 pending real
alerts; excess notifications are summarized after the queued alerts. Actual
achievement completion remains recorded independently of this display limit.

`UI/AddonSettings.lua` registers one modern canvas/legacy category, with a fallback
owned panel. Registration and native settings opening defer during combat.
On first login, the original recording is selected once; opening/syncing does
not reset existing preferences. Tests
and preview buttons do not invoke completion or EARN_HOOKS. The core's
`Complete`, `PreviewToast` and `ResetToast` only route presentation to the new
module; retained alpha toast code remains available if the module is absent.
No change to the unified Legacy panel's layout, combat controller or fallback.

Classic texture crops and alert geometry were checked against the Blizzard
`AchievementAlertFrameTemplate` in the
[AlertFrameSystems.xml mirror](https://github.com/tekkub/wow-ui-source/blob/master/FrameXML/AlertFrameSystems.xml)
(observed source SHA256 `a70e6633301347f4948e63822dd4aa80b9b284c117f602feccb5560c8c91577a`).
Only client-provided textures are used; its global alert scripts are not loaded.

Validation: all **680 automated tests passed**, including 23 alert/settings
cases using real Lua completion and input callbacks. They cover no preview
progress writes, correct crop/geometry contracts, animation lifecycle, sound
failure/mute/channel behavior, missing sound constants, client sound overrides,
shield-centered points, frame reuse, real-award routing/duplicate safety,
title line/wrapping, explicit file playback, read-only audio diagnostics and
bundled sound routing through a normal completion, supplied OGG routing without
a sound-kit API, one-time selection with mute/channel retention,
bounded bursts, combat deferral and modern/legacy settings APIs. Lua 5.1 syntax
passed for 31 files, all 32 TOC references and four XML dependencies passed,
and the existing 322-definition initialization/14 behavior assertions passed.
Actual visuals, audio and client restrictions remain to be tested in-game.
The supplied OGG decodes successfully as 5.19-second mono Vorbis at 22.05 kHz
and contains non-silent audio. Its upload/runtime hashes match (see CREDITS).
Package checks require the OGG and verify every ZIP entry against runtime source.

This build also includes objective-tracker integration and 12 associated tests;
see [native objective tracker testing](native-objective-tracker.md).
