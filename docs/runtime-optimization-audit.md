# Runtime optimization audit

Build: `0.4.21-alpha-audit1`.

Reviewed the core/event trackers, money and social code, presentation/data
adapters, UI renderer, and native controller/bridge. The starting build passed
all 609 regression tests. This pass keeps existing progression, point authority,
SavedVariables, appearance and client safety checks intact.

## Changes supported by the review

- **Tracker updates:** use the core's existing synchronous progress snapshot.
  Three tracked quest tiers now share one statistic read instead of three.
  Subsequent updates read fresh values; unknown values and error cleanup retain
  their existing semantics. No new timer or persistent cache.
- **Completed fall tracking:** skip the seven observation APIs while the current
  database already has a completion, matching the existing confirmation rule
  that never overwrites that history. This removes 700 sample API calls per
  100 completed-character frame updates in the fixture. Keep the callback and
  recheck the database each tick so a correction or character change resumes
  tracking, with no inherited grounded/pending observation.
- **Exploration relationship verification:** sort only authored zones with a
  matching native ID. A mixed 304-record fixture sorts three eligible records;
  all unrelated/absent-native records still appear in the catalog. Priority order,
  native read budget, conservative proof, and snapshot lifetime remain unchanged.
- **Other-character completion names:** read snapshot-level validation fields
  and format its character/realm name once per snapshot, rather than for every
  completion. Per-key verification and sorted/deduplicated names are unchanged.
- **Deferred combat close:** a newer native open now cancels both older pending
  close flags, including when the replacement was disabled. Previously an older
  protected close could conceal the reopened cover and close the new native
  window when combat ended. This fix changes pending intent only.

Runtime functions changed: `Tracker.Update` (wrapping its existing renderer),
the fall tracker's `OnUpdate`, `CustomAdapter.otherCharacterCompletions`,
`LegacyPresentation.Build` candidate collection, and the controller's native
`OnShow` hook. The TOC version also changed.

## Existing safeguards retained

The renderer already pools cards/criteria, reuses scroll plans, coalesces search,
discards unchanged reentrant requests, and cancels stale work by generation.
Data/proof/query caches are bounded and scoped to snapshots. Money and social
reads already use their own existing caches. Keep completed-achievement proof
evaluation: it can change whether historical records earn verified points.
Keep both bridge preflight checks: native callbacks run between them and can
change restrictions. Mount passes can repair native presentation drift.
Broader event coalescing and award-hook changes would need a separate behavioral
review; they were unnecessary for the concrete improvements in this pass.

## Verification

All **615 automated tests passed**. Lua 5.1 syntax passed for 28 files;
packaging passed for 29 TOC references and four XML files. Core initialization
loaded 322 definitions and passed 14 isolated behavior assertions.

New regressions measure shared tracker reads and fresh/error/unknown passes,
completed fall idling and resumed observation, relationship filtering/order with
unrelated records preserved, and reopening after a deferred close with the
replacement enabled and disabled. Existing combat, native restoration, point
verification, character identity and performance suites remain active.

Replace the complete addon folder, keep WTF/SavedVariables, and `/reload`.
Check tracked progress refresh, category/search behavior, both point counters,
and close/reopen across combat. Fall observation remains active before completion
and after a supported correction; completed history remains untouched.
Client rendering, secure execution and actual frame timing still require in-game
checks. API counts from fixtures are not a claim about live frame-rate gains.
