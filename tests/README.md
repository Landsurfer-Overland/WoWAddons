# Legacy inspector and unified Wrath integration checks

From the repository root, run:

```sh
python -B -m unittest discover -s tests
```

The harness requires `lupa` with its Lua 5.1 runtime. Cloud setup already installs
it under `/workspace/.cloud-tools/forever-achievements/python`; a normally installed
`lupa` package works as well. Run Lua/XML/TOC packaging validation with the existing
cloud validator where available:

```sh
PYTHONPATH=/workspace/.cloud-tools/forever-achievements/python python -B /workspace/.cloud-tools/forever-achievements/validate.py
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
These remain controlled fixtures. The [two-character manual plan](../ForeverAchievements/Integrations/README.md#two-character-progression-regression)
checks login, character switching, reload/logout persistence, real exploration/pet
evidence, and genuine completion preservation in the client.

## Limits

These fixtures do not emulate actual game rendering, asset lookup, native protected
frame behavior, input/gamepad focus, server reward or trait progression, animation
timing, or SavedVariables disk writes. Passing them is not an in-game validation
claim. Follow the [manual test plan](../ForeverAchievements/Integrations/README.md)
for texture fidelity, UI-scale/scroll alignment, native interactions, taint, staged
tree edits, input transitions, and restoration in the actual Forever client.
