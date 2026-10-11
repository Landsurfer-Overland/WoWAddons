# Legacy Achievements Reforged

A unified Wrath-style achievement interface for **WoW Forever**, maintained by
Landsurfer-Overland. Native Legacy Challenges and character achievements share
one navigation hierarchy while retaining their separate progression and point
calculations. Native Legacy Rewards and Legacy Trees remain available.

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

- `/lar legacyui on|off` — enable the unified interface or restore native Legacy.
- `/lar legacyui size compact|standard|large` — choose a window size.
- `/lar legacyui reset` — reset window position without changing progress.
- `/lar perf on|report|off` — optional timing diagnostics.
- `/lar help` — all commands; `/reforged` and `/legacyachievements` are aliases.
- `/legacyinspect` — the optional read-only native Legacy inspector.

Feats of Strength contains **Legacy Point Achievements**, a searchable view of
confirmed Legacy Point rewards. Original category assignments and totals remain
unchanged. Unverified progress is kept separate from verified completion.

## Development and publishing

Python 3.11 and `pip install -r requirements-dev.txt` provide the Lua 5.1 test
runtime. Run `python -B -m unittest discover -s tests` and
`python tools/validate.py`, then `python tools/package_release.py`.

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
