# Legacy Achievements Reforged publishing

Addon identity: `LegacyAchievementsReforged`; title: **Legacy Achievements Reforged**.
The current build is `0.5.1-alpha.1` on `main` in
`Landsurfer-Overland/WoWAddons`, promoted from `achievement-alerts-test`.
The repository contains source, documentation, tests and tools; release ZIPs
contain only the addon. Historical branches and commits are retained.

## CurseForge

Use the existing [Legacy Achievements Reforged CurseForge project](https://www.curseforge.com/wow/addons/legacy-achivements-reforged)
and connect `https://github.com/Landsurfer-Overland/WoWAddons` using `main` in its repository /
automatic-packaging configuration. The repository does not need to be renamed
to match the addon folder.

The `.pkgmeta` sets `package-as: LegacyAchievementsReforged`, excludes development
files, and moves the isolated runtime folder into the ZIP's addon root. The
changelog explicitly declares Markdown formatting. Vendored libraries are copied
verbatim without keyword or line-ending transformations. No-library packages are
disabled because this addon ships the libraries it needs. The Python package
tool provides the same single-addon directory layout
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

### Automatic packaging checklist

- Use the repository root containing `.pkgmeta`, not the addon subdirectory.
  The `move-folders` entry accounts for the nested source layout and places
  `LegacyAchievementsReforged.toc` directly inside the installed addon folder.
- Keep `main` as the current-build branch. Preserve existing release tags;
  packaging settings added later do not change those historical snapshots.
- For each future release, update the TOC version and changelog, validate, then
  create a matching annotated tag such as `v0.5.2-alpha`. Tags containing
  `alpha` identify alpha packages; do not remove that marker while testing.
- Verify the downloaded package contains a single `LegacyAchievementsReforged/`
  addon root, its TOC, all vendored libraries, textures and both audio files.
  Research reports, the separate research probe, references and tests are excluded.
- Check CurseForge's packaging status and generated file after connecting the
  project. A successful local package does not establish that the project is
  connected or that a CurseForge upload has been accepted.

See [CurseForge's automatic-packaging guide](https://support.curseforge.com/support/solutions/articles/9000197281-automatic-packaging)
for the current project-side connection process. The repository configuration
was exercised with the maintained [BigWigs addon packager](https://github.com/BigWigsMods/packager/tree/0f24d2169de3ceb3b79a981311b2ebab4c6160c7),
with uploading disabled; that is a local compatibility check, not a test of
CurseForge's hosted service.

Project-side repository packaging and GitHub Actions API uploads are separate
options. This repository's GitHub workflow publishes GitHub downloads only.
An API uploader would require the actual CurseForge project ID and a GitHub
repository secret such as `CF_API_TOKEN`; do not put a token in source files.
Use one upload path for each release to avoid duplicate files.

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
