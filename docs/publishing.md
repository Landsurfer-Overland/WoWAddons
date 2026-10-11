# Legacy Achievements Reforged publishing

Addon identity: `LegacyAchievementsReforged`; title: **Legacy Achievements Reforged**.
The current build is `0.5.1-alpha.1` on `main` in
`Landsurfer-Overland/WoWAddons`, promoted from `achievement-alerts-test`.
The repository contains source, documentation, tests and tools; release ZIPs
contain only the addon. Historical branches and commits are retained.

## CurseForge

Create or select the CurseForge project with this title and connect the existing
repository using `main`. The existing GitHub repository
can also be renamed to `LegacyAchievementsReforged` in GitHub repository Settings;
update connected integrations and the local Git remote after that owner action.

The `.pkgmeta` sets `package-as: LegacyAchievementsReforged`, excludes development
files, and moves the isolated runtime folder into the ZIP's addon root. It uses
the maintained addon changelog rather than generating one from historical commit
titles. The Python package tool provides the same single-addon directory layout
without requiring a third-party packager or any upload credentials:

```sh
python tools/validate.py
python -B -m unittest discover -s tests
python tools/package_release.py --output-dir .release
```

Upload `LegacyAchievementsReforged-VERSION.zip` to CurseForge as an alpha while
the addon remains in testing. A GitHub source-download ZIP is a development
checkout, not the installable release archive. Keep bundled library notices and
the project credits in distributed files.

No CurseForge project ID is fabricated and no upload token is committed. Remote
publication is separate from packaging. To add automatic CurseForge uploads
later, configure the actual project ID and a repository secret through the chosen
packager/uploader; this repository does not currently send CurseForge uploads.

## GitHub validation and releases

The workflow runs Lua 5.1 behavior/syntax/packaging checks on pushes and pull
requests. It builds the installable ZIP plus SHA-256 checksum as a workflow
artifact. Pushing a version tag such as `v0.5.1-alpha.1` additionally publishes a
GitHub prerelease using the workflow's built-in token, after checks pass.
The tag version must match the TOC version. Promotion to `main` alone does not
publish a release; the matching tag is required. New releases must be tested
in-game as well.

Older save files need the [migration step](save-migration.md) before the new addon
identity's first login. Include that link in the CurseForge description/release
notes so an identity change is not mistaken for erased progress.
