# Achievement expansion research

The supplied brief is treated as research scope, and the backlog as unverified design input. This audit implements no production achievements and makes no visual, progression or point changes.

Start with [late-install-safe-achievements.md](late-install-safe-achievements.md). **All 200 IDs audited; 0 VERIFIED additions.**

- [Capability inventory and pending family tests](achievement-capability-audit.md).
- [All 200 candidate audits (CSV)](achievement-candidate-audit.csv): original/clarified criteria, exact duplicates/overlaps, source calls, scope, both recovery paths, late experience, decision, evidence, tests and replacements.
- [Revised backlog preserving all IDs](revised-achievement-backlog.md).
- [Existing source baseline](existing-source-baseline.md), [custom catalog CSV](existing-custom-catalog.csv), [native references CSV](existing-native-references.csv), [source manifest](forever-source-manifest.json).
- [Optional standalone read-only probe and client procedure](../../tools/research/LARResearchProbe/README.md).
- [Original research brief](inputs/Codex_Achievement_Research_Brief.md) and [original backlog](inputs/Legacy_Achievements_Reforged_Backlog.txt).

Design decisions are separate from evidence levels. KEEP/REDESIGN means a proposed design path, not Ready or permission to ship it. Implementation should start only with a small batch that has passed exact client qualification, attribution, persistence, recovery and duplicate tests. Prospective-only entries require explicit later approval; point values remain proposals.

No client gameplay was performed. The probe fixture tests establish diagnostic boundaries and error handling, not game APIs. Use disposable/backed-up test profiles without deleting real progress.

Validation: all 692 automated tests passed, including 12 read-only probe cases.
Production validation remains 31 Lua files, 32 TOC references, four XML files,
322 initialized definitions and 14 core assertions. Coverage checks confirmed
all 200 IDs and original criteria, 263 custom records (seven disabled), 68 native
references (59 retained imports), unchanged input uploads, matching source
hashes and valid local document links. No executable client tests ran.
