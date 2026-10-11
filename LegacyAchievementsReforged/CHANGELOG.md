# Legacy Achievements Reforged

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
