# Legacy Achievements Reforged

## 0.5.1-alpha.1 — current build

- Correct GitHub artifact uploading to include the hidden `.release` directory,
  allowing the installable ZIP and checksum to reach the prerelease job.
- Retain the promoted addon behavior from `0.5.1-alpha` unchanged. The initial
  tag remains in history; its upload failed before any installable assets were
  published.

## 0.5.1-alpha — promotion

- Promote the achievement-alert test build to the current alpha release.
- Classic gold achievement popup with fade, glow and shine, centered title and
  shield points, plus addon settings and manual popup/sound previews.
- Play the supplied achievement chime directly from bundled OGG audio; retain
  selectable sound alternatives, mute/channel preferences and preview controls.
- Use the project's original hammer-and-anvil addon-list/minimap icon.
- Show tracked custom achievements in the client's objective tracker, with
  cached watch snapshots and combat-deferred registration/layout operations.
- Preserve achievement progress, point calculations, SavedVariables names,
  unified Legacy navigation, Rewards/Trees and existing stability safeguards.
- Retain the research reports and optional read-only probe in the repository;
  they are excluded from the installable addon and add no new achievements.
- Automated Lua and packaging checks pass. Audible playback, rendering and
  protected-frame behavior still require verification in the Forever client.

## 0.5.1-alpha-alert-test6 — testing branch

- Bundle the supplied achievement-earned OGG unchanged and play it directly
  with PlaySoundFile for previews and normal custom achievement unlocks.
  This avoids the client's accepted but silent sound kit 12891 request.
- Select the recording once on upgrade; retain mute, channel and volume settings.
  Later sound selections persist. Settings can reselect/test the original chime.
- Keep the original Reforged bell and client sound probes as selectable options.
  Package OGG audio in installable ZIPs. Popup animation and progress are unchanged.
  Audible playback on WoW Forever still requires an in-game check.

## 0.5.1-alpha-alert-test5 — testing branch

- Tracked custom achievements use a Reforged Achievements section inside the
  client objective tracker, instead of the separate floating alpha box.
- Native blocks supply formatting, height limits, pooling and section collapse.
  Track/untrack, progress labels, unknown values and saved watch keys are retained.
- Register/layout changes defer in combat. Refresh only changed watch snapshots;
  native layouts do not rescan custom progress or rebuild achievement catalogs.
- `/lar tracker on|off|status` controls visibility and reports integration state.
  In-game appearance and taint behavior still require client verification.

## 0.5.1-alpha-alert-test4 — testing branch

- Center title in the classic line area; align its heading horizontally and
  retain bounded space for wrapped titles. Alert animation is unchanged.
- Add explicit client WAV/OGG sound probes and an original bundled Reforged
  bell chime, with a one-click selection/test button. The bundled chime is
  independent artwork, not Blizzard's recording or an automatic substitution.
- Selected file playback applies to previews and normal custom completions.
  Sound status distinguishes kit/file requests and reports read-only audio
  enable/volume values; accepted requests do not prove audible playback.

## 0.5.1-alpha-alert-test3 — testing branch

- Anchor popup points to the shield center and restore the classic shield crop.
- Achievement chime can request the standard client sound kit 12891 even when
  the client does not export the expected SOUNDKIT constant. Report playback
  rejection with the kit number; audible playback still needs in-game testing.
- No external sound downloads, native sound changes or progress changes.

## 0.5.1-alpha-alert-test2 — testing branch

- Replace the inherited addon-list/minimap icon with an original gold hammer
  and anvil emblem for Legacy Achievements Reforged.
- Artwork-only change; achievement behavior and alert settings are unchanged.

## 0.5.1-alpha-alert-test1 — testing branch

- Classic gold achievement popup with icon, shield, fade, glow and shine.
- Addon settings page with Test popup, Play selected sound and Stop preview.
- Configure notification/sound/animation toggles, sound selection/channel,
  hold time, position and scale. `/lar settings` opens the page.
- `/lar alert test|sound|stop` previews without awarding progress or points.
- Actual custom unlocks use the new popup; native game notifications remain
  under the client's control. One reused frame, bounded queue, no idle updates.
- Experimental build for in-game testing; not promoted to the published build.

## 0.5.0-alpha

- New project identity, addon folder, commands and internal identifiers.
- Use `/lar`, `/reforged` or `/legacyachievements` for addon commands.
- Feats of Strength includes Legacy Point Achievements for browsing confirmed
  Legacy Point rewards with the existing search and filters.
- Retains the unified Wrath-style interface, achievement progress checks,
  separate point counters, native Rewards/Trees, and combat/performance fixes.
- Includes a separate non-destructive save migration tool in the repository;
  existing players should follow the migration guide before the first login.
