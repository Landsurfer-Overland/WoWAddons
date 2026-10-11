# Legacy Achievements Reforged identity change

Release: `0.5.0-alpha`; branch: `legacy-achievements-reforged`.

The runtime folder, TOC and core file are `LegacyAchievementsReforged`. Visible
titles, status messages, links, broker registration, asset paths, binding names,
diagnostic windows, XML templates and owned frame names use the new identity.
The internal module namespace is `ns.LAR`; owned Wrath frames use `LARWrath`.
Addon chat messages use the short `LAR` prefix, within the client's prefix limit.
Commands are `/lar`, `/reforged` and `/legacyachievements`; the generic
`/legacyinspect` diagnostic command remains. Old identity aliases are not retained.

The two saved tables are renamed too. The separate generic migration tool copies
account and character files, changes only their top-level declarations, refuses
conflicting destination saves, and leaves sources/backups unchanged. See
[save migration](save-migration.md) before the first renamed-addon login.
No achievement keys, native IDs, category mappings, completion checks, point
formulas, copper units, timestamp data, frame geometry or combat protections
were changed by this identity migration. The quarantined presentation remains
available as retained source with the new identity.

README, audit documents, tests and generators use the renamed paths and commands.
Credits and bundled library notices remain. Supplied Blizzard source files still
match every original source hash. A manual addon changelog, `.pkgmeta`, portable
validator/ZIP builder and GitHub validation/prerelease workflow prepare publishing.
No remote tag, GitHub release or CurseForge upload is created by this change.

Validation: all **645 tests passed**, including 12 new identity, package and
migration cases. Lua 5.1 syntax passed for 28 files; all 29 TOC references and four
XML files passed dependency checks. Core initialization retained 322 definitions
and passed 14 isolated behavior assertions. Both the Python ZIP builder and a
local no-upload run of the authoritative BigWigs packager verified a single
correctly named addon root, with no development/reference source files included.
The current files were also scanned for stale project names and identifiers.

Native rendering and actual saved-file loading still require in-game testing.
Migrate before first login, verify progress/settings on multiple characters,
enable `/lar legacyui on`, and check open/close, combat, Legacy Rewards/Trees,
search and the Legacy Point Achievements selector.
