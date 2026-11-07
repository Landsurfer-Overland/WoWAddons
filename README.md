# Legacy Achievements Reforged

A unified Wrath-style achievement interface for **WoW Forever**, maintained by
Landsurfer-Overland. Native Legacy Challenges and character achievements share
one navigation hierarchy while retaining their separate progression and point
calculations. Native Legacy Rewards and Legacy Trees remain available.

The minimap button opens achievements even before the native menu unlocks at
level 25. Left-click to open or close the screen, right-click for addon settings,
and drag to reposition. Clicking the button enables and opens the combined
Reforged interface, including on a fresh installation or when native Legacy is
already open. Existing hidden-button and
position preferences are preserved. Use `/lar minimap show` to restore the button.

[CurseForge project](https://www.curseforge.com/wow/addons/legacy-achivements-reforged)

## Installation

Download the installable ZIP from a tagged release or build it with
`python tools/package_release.py`. Extract **LegacyAchievementsReforged** into
your client's `Interface/AddOns` directory. Keep its folder and TOC basename
unchanged. Enable the addon and run `/lar legacyui on`.

**Updating from an earlier addon identity:** close WoW and follow the
[save migration guide](docs/save-migration.md) before the first login. The new
addon uses new SavedVariables names; simply renaming its folder does not import
earlier progress. Disable the previous addon after migration to avoid running
two achievement controllers. Source saves and their backups remain intact.

## Commands

- `/lar settings` — addon settings, including achievement popup/sound previews.
- `/lar minimap show|hide` — show or hide the minimap launcher.
- `/lar apicheck [key|dungeons|native|all]` — inspect client API availability and achievement evidence.
- `/lar recover <dungeon key> [confirm]` — preview or record personally confirmed completion backed by a native criterion.
- `/lar alert test|sound|stop` — test notifications without awarding progress.
- `/lar legacyui on|off` — enable the unified interface or restore native Legacy.
- `/lar legacyui size compact|standard|large` — choose a window size.
- `/lar legacyui reset` — reset window position without changing progress.
- `/lar perf on|report|off` — optional timing diagnostics.
- `/lar tracker on|off|status` — show, hide or inspect tracked achievements.
- `/lar help` — all commands; `/reforged` and `/legacyachievements` are aliases.
- `/legacyinspect` — the optional read-only native Legacy inspector.

Feats of Strength contains **Legacy Point Achievements**, a searchable view of
confirmed Legacy Point rewards. Original category assignments and totals remain
unchanged. Unverified progress is kept separate from verified completion.

The current `main` build is **0.5.1-alpha.1**, promoted from `achievement-alerts-test`.
Its popup uses the classic gold banner, short fade-in, gold glow, sweeping shine,
timed fade-out and the supplied achievement chime played from a bundled OGG.
Other sounds remain selectable. The settings page is available through
the client's AddOns settings or `/lar settings`; the quarantined alpha window
is not needed. See the [alert testing guide](docs/achievement-alert-testing.md).
Tracked custom achievements use the client's objective tracker under **Reforged
Achievements**, alongside quests. The former floating tracker stays hidden.
See the [tracker testing guide](docs/native-objective-tracker.md) for client checks
and combat deferral behavior.
The matching `v0.5.1-alpha.1` release tag publishes an installable GitHub prerelease
after the automated checks pass. The root `.pkgmeta` prepares this repository for
CurseForge packaging. Automatic packaging requires a project-side repository connection.
See the [automatic-packaging checklist](docs/publishing.md#automatic-packaging-checklist).
Research reports and the optional read-only probe remain outside
the installable addon; no research proposals are implemented by this release.

## Development and publishing

The **0.5.2-alpha.2 API-audit testing branch** targets Forever **1.60.1.70862**.
It adds personal native-evidence recovery for custom achievements, current skill
API support, coalesced criteria updates and `/lar apicheck` diagnostics.
See the [full audit and in-game checks](docs/client-api-audit.md) and the
[complete 322-definition inventory](docs/research/client-70862-achievement-audit.json).
This is a source-reviewed test build; content IDs and live character results
still require the documented in-game checks.
Account-wide criteria can combine alternatives: Novice Spelunker's "Ragefire
Chasm or Hall of Thanes" does not identify the dungeon or character. Future
completion events can be attributed using instance context. For an old run you
personally completed, `/lar recover dungeonThanes` previews the available native
record; adding `confirm` records your report for this character. This is labeled
player-confirmed recovery, not a server-verified personal boss statistic.

Python 3.11 and `pip install -r requirements-dev.txt` provide the Lua 5.1 test
runtime. Run `python -B -m unittest discover -s tests` and
`python tools/validate.py`, then `python tools/package_release.py`.
Run `python tools/audit_achievement_apis.py --check` to check audit coverage;
regenerate the inventory after changing authored achievement definitions.

[CurseForge/release setup](docs/publishing.md) ·
[Installation and in-game checks](LegacyAchievementsReforged/Integrations/README.md) ·
[Automated tests](tests/README.md) ·
[Credits](LegacyAchievementsReforged/CREDITS.md)

Runtime source is isolated in `LegacyAchievementsReforged/`. Development tests,
reference sources, documentation and tools remain outside the release addon.
The quarantined alpha presentation is retained for future feature migration;
it does not register its old window or launcher in normal use. Supplied Blizzard
reference sources retain their original hashes. Rendering, client protections,
and actual game API behavior still require in-game verification.

