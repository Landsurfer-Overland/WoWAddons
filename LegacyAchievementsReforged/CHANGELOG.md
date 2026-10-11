# Legacy Achievements Reforged

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
