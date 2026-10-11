# Legacy inspector and unified Wrath integration checks

From the repository root, run:

```sh
python -B -m unittest discover -s tests
```

The harness requires `lupa` with its Lua 5.1 runtime. Cloud setup already installs
it under `/workspace/.cloud-tools/legacy-achievements-reforged/python`; a normally installed
`lupa` package works as well. Run the repository's Lua/XML/TOC validator:

```sh
PYTHONPATH=/workspace/.cloud-tools/legacy-achievements-reforged/python python -B tools/validate.py
```

## Inspector checks

The isolated diagnostic suite covers unloaded/populated native UI, safe challenge
and reward evidence, manual snapshot comparison, descendant fallback, protected
getter failures, forbidden objects, traversal/output budgets, and absence of
diagnostic hooks, native mutations, unknown API calls, timers, or transmissions.
Copy-window checks cover Run, Clear, Close, keyboard input, widget reuse,
wrapped-text sizing, combat deferral, and TOC registration. Busy fixtures verify
that unrelated children cannot starve requested Legacy pages or their samples.
The inspector itself remains read-only; the optional presentation controller has
its own separately tested, reversible presentation changes.

## Wrath integration checks

The integration suites execute actual Lua adapters, presentation/controller code,
and adapted XML OnLoad callbacks with explicit UI doubles. They check separate
native/custom identifiers and data authority, retained saved progress, opt-in
persistence, errors/missing objects, criteria and point semantics, local filters,
meta navigation, bounded scrolling, original assets/coordinates, and reference hashes.

Iteration 2 adds unified mapping checks for live category metadata, ancestor context,
mixed Adventure exceptions, unmapped fallbacks, duplicate prevention, and separate
source summaries with reliable recent native dates. Presentation checks cover four-tab
order, separate header totals, real/absent reward text, and the single point-shield
texture. Native lifecycle checks cover reversible root presentation suppression,
parent-preserving Rewards/Tree mounting and geometry restoration, native handler
preservation, input-mode fallback, combat deferral, and normal close/reopen behavior.

Iteration 3 extends coverage to independent type/point/source/scope properties,
zero-point standard versus genuine Feat rendering, shared populated subcategories,
parent aggregation, fallback navigation without reclassification, loaded-criteria
search, separate source filters, reliable dates, and retained overlapping progression.
Statistics checks distinguish native zero from absent/error/secret/placeholder data,
preserve money/name formatting, prune empty navigation, exclude unsupported daily IDs,
and count saved observations without adding defaults or merging account history.
Layout/controller checks exercise size presets, screen fitting, saved/clamped position,
reset, original native inner backgrounds, Summary spacing, independent Statistics
navigation, and source/card XML contracts.
Standalone progress checks cover unavailable quest/Loremaster values in sorting,
cards, the tracker, and social tooltips, confirmed zero, and hiding unsupported daily
tracked keys without deleting saved history. Release checks include cleanup failures
and retrying a failed native restoration.

Addendum checks use two isolated character fixtures to distinguish current-character
completion from reliable elsewhere history and native account completion. They cover
unscoped pet ownership and old maxima, hover-only exploration overlays and invalid
map evidence, measured versus time-only falls, character identity/snapshot preservation,
default-off diagnostics with reload-persistent enablement and a session-only trace,
explicitly confirmed targeted correction/reaward holds and separately confirmed resume,
preserved source/history/other keys, rejected native imports, and card
expand/collapse behavior independent of selection. Meta-child checks accept only finite
positive character timestamps, validated dynamic
map proofs preserve zone identity/dimensions, and standalone account/recent views reject
ambiguous snapshots and malformed history without deleting the saved records.
These remain controlled fixtures. The [two-character manual plan](../LegacyAchievementsReforged/Integrations/README.md#two-character-progression-regression)
checks login, character switching, reload/logout persistence, real exploration/pet
evidence, and genuine completion preservation in the client.

## Stability and performance checks

Performance regressions exercise bounded native read attempts across overlapping,
duplicate, failed, and provider-fallback records; indexed category counts and Summary;
query cache limits and loaded-criteria invalidation; fresh progress after model rebuilds;
and cache results that callers cannot mutate. Optional diagnostic checks verify default
off behavior without clock reads, bounded names/outstanding tokens, valid zero duration,
clock conversion/failure/secret handling, one-use tokens, aggregate reports, and preserved
SavedVariables. Controller/UI fixtures cover redundant-refresh prevention, deferred
updates, close/disable lifecycle invalidation, frame reuse, navigation, and live-data
invalidation. These checks establish operation bounds and behavior, not live CPU timing.
See [stability findings and client verification](../docs/legacy-ui-performance.md).

## Iteration 4 checks

Iteration 4 replaces parent list aggregation with direct assignments while retaining
cached descendant totals. Fixtures check general professions/reputation milestones,
eligible class navigation, preserved fallback classification, unique card identities,
and exact native/custom zone and meta relationships. Native requirement verification
shares one 256-read budget per native snapshot and never schedules another build to
finish its work. Missing, changed or partially verified requirements remain separate.

Character fixtures exercise two identities, copied databases, GUID readiness and
later mismatch, unknown historical proofs, actual local geography/current maps plus
revealed overlays, optional discovery-area API failures, positive bag ownership,
preserved historical records, named cross-character indicators, guarded account
snapshots, and confirmed correction archives. The existing measured-fall/fence and
renderer lifecycle regressions remain active. Exact unavailable custom ID 614 stays
defined and saved while absent from the active catalog.

Money checks execute actual core events as well as the copper-normalized tracker:
verified statistic identity/scope/units, unverified plain numeric values, configured
increasing thresholds, copied-ledger ownership, bounded event deduplication, reload
without added earnings, unsupported quest totals, and preservation of old counters.
UI fixtures check independent blue native/gold custom completion, one point shield,
dual criteria within the existing objective cap, named history without character
points, unit formatting, merged recents and canonical linked-card navigation.

Follow the [Iteration 4 client plan](../docs/iteration4-regression-plan.md) for actual
login, disk persistence, progression, source formats, visual and stability verification.

## Iteration 5 checks

UI fixtures cover restored backdrop/header assets, larger defaults with preserved
saved presets, balanced counters/crest, footer geometry, owned filter selection and
bounded reuse, whole-parent versus indicator/leaf interactions, direct broad parent
lists, quiet unknown/card metadata, Legacy-only recorded earner notes, money labels,
and criteria/check alignment. Native fit fixtures cover uniform bounded enlargement,
distinct effective scales, unchanged ancestry/scripts/data, idempotent mounting,
preflight failure, combat guards and exact restoration. Targeted historical Moonglade
fixtures preserve raw history while separating unverified display/points from actual
local evidence and independent native completion; unrelated historical zones remain
compatible. The existing stability, frame-pool and source-authority suites remain active.

Follow the [Iteration 5 client checklist](../docs/iteration5-regression-plan.md) for
actual texture quality, input behavior, native interaction, two-character history
and live timing checks. These remain pending until performed in the Forever client.

## Iteration 6 checks

Actual Lua/XML fixtures cover the Standard default and preserved preferences,
bounded decorative parent/child headings and long names, pooled size/filter menus,
footer geometry and faction/neutral crests. Scroll fixtures exercise proportional
thumbs, wheel/arrows/drag feedback, expansion/collapse, resizing, viewport access and
control reuse without provider reads. Card fixtures cover explicit gray/blue/gold
precedence, complementary shield/laurel masks, capability fallback, actual source
points and completion dates. Header fixtures reproduce the retained-history path
to an unknown custom total without rewriting progress. Existing indexed-query,
native restoration, reentrancy, frame-pool and performance suites remain active.

Follow the [Iteration 6 client checklist](../docs/iteration6-regression-plan.md)
for actual artwork, mask alignment, input, native functionality and timing.

## Original alpha UI quarantine

`test_original_ui_quarantine.py` executes actual retained consumers with the
source policy disabled. It covers central/local slash opening, missing policy,
minimap/broker non-registration with preserved preferences, welcome retries and
seen state, binding/tracker/social entry points, retained tracking and tooltips,
real Legacy controller opening, and explicit developer recovery. The existing
standalone consumer harness enables the policy deliberately to keep testing
the archived implementation rather than silently skipping its regressions.
Follow the [client checks](../docs/original-ui-quarantine.md) after installing.

## Limits

These fixtures do not emulate actual game rendering, asset lookup, native protected
frame behavior, input/gamepad focus, server reward or trait progression, animation
timing, or SavedVariables disk writes. Passing them is not an in-game validation
claim. Follow the [manual test plan](../LegacyAchievementsReforged/Integrations/README.md)
for texture fidelity, UI-scale/scroll alignment, native interactions, taint, staged
tree edits, input transitions, and restoration in the actual Forever client.
