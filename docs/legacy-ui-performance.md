# Legacy UI stability and performance

The reported `script ran too long` failures occurred during synchronous presentation
work. Different reported lines in `Presentation.lua` do not establish separate bugs:
the former line 329 was part of `P.Rows` category membership filtering. The error
identifies where the client exhausted its execution budget, not necessarily where the
excess work began. Native fallback remains available after presentation errors.
The controller catches these errors to restore native access and reports them in chat,
so BugSack/BugGrabber may not receive an uncaught error. Preserve the fallback text
alongside the optional performance report.

## Findings from code and controlled fixtures

The previous opening path could rebuild the presentation during fitting, initial model
assignment, native-page coordination, and rendering. An instrumented opening fixture
recorded **three model builds and seven renders**. This demonstrates redundant work;
it does not reproduce or prove the exact live-client timeout sequence.

Native enumeration previously bounded unique records, while repeated category entries
and unavailable reads did not necessarily consume that bound. With 256 categories and
2500 entries per category, an overlapping collection could attempt **640,000 native
achievement reads** before presentation completed. These are potential read counts,
not measured game timing. The corrected catalog shares a single 2500-attempt budget
across categories and passive provider fallback. Duplicates and failed reads consume
that budget; exhausted or unavailable results remain explicitly partial.
Category-information reads share a separate 256-attempt budget, including failed
metadata, ancestry recovery, and achievement-type inspection; repeated reads reuse
the catalog's metadata snapshot.

Custom progress also repeated expensive observations. A baseline catalog fixture
observed **620 map-information reads for 576 area checks across 44 zones**. Missing map
metadata could repeat the failed fallback path for additional criteria. Repeated builds
multiplied this work, while category counts, Summary, filters, and scrolling repeatedly
visited the same record collection.

The same production-definition fixture (243 available character records) was rerun
after the changes with controlled API doubles:

| Observations per custom catalog | Before | After |
| --- | ---: | ---: |
| Bag item reads, five full 200-slot bags | 3,000 | 1,000 |
| Skill-line reads, 50 lines | 1,400 | 100 |
| Faction standing reads | 421 | 54 |
| Statistic reads | 92 | 46 |
| Completed-quest list retrievals | 8 | 1 |
| Map-information reads with valid authored maps | 620 | 44 |
| Best-map / child-list reads with unresolved maps | 620 each | 1 each |
| Map-information reads in that unresolved one-parent case | 1,240 | 45 |

The next independent catalog made fresh reads and detected a changed bag item.
These counts demonstrate reuse within a pass; they are not client timing results.

The changes remove those confirmed work multipliers and bound remaining reads.
Actual client performance and recurrence of the reported timeout still need manual
verification; automated fixtures measure operation counts rather than game CPU time.
Focused actual-core fixtures verify that reputation tiers share one read per faction
within a catalog pass, failed map fallback observations are shared, and a 256-criterion
native condition shares one count read and 256 detail reads across repeated progress
and detail requests. An oversized condition stays unknown instead of scanning more.

## Refresh and cache boundaries

`Presentation.lua` creates subject membership indexes, completion counts, and category
ancestry once per model snapshot. Parent aggregation stays identity-unique. Summary
and recent lists reuse snapshot results; callers receive separate arrays rather than
mutable cached arrays. Search scans only the selected category's membership, retains
at most 32 queries, and invalidates those queries when newly loaded criteria change.
Search still uses loaded criteria only; it never fetches every unloaded objective.

The controller separates data, layout, tab, and native-mount changes. Fitting and pure
tab transitions reuse the current model. Custom progress checks rebuild character
values while retaining the native catalog; native challenge/criteria/list events,
Legacy challenge refresh callbacks, relevant currency changes, and reopening invalidate
native data. Native partial snapshots remain reusable until such a change, avoiding
repeated full scans merely because the collection is partial. Existing data-refresh
requests also refresh a native snapshot older than 30 seconds; this adds no polling
ticker and leaves pure navigation free to reuse unchanged data. Without a reliable
clock, at most eight actual data refreshes reuse that native snapshot before rereading.

Closely spaced refresh requests coalesce into one deferred pass. Busy-state guards
defer a real pending update rather than discarding it. Lifecycle generations invalidate
queued work after closing, disabling, changing input mode, or restoring native access.
Native callbacks observe the final page selection; addon mounting does not recursively
select the same tab again. Existing hooks are installed once, and the native frame
parents, providers, progression, rewards, and tree handlers remain authoritative.

Custom catalog generation and `CheckAll` share expensive observations only within one
synchronous evaluation pass. Collection, skill, riding, statistic, completed-quest,
reputation, native-criteria, and zone-map reads can reuse values, including nil/error
results. The pass restores its prior context on success or error and never supplies
one character's reads to another character's database. The next pass reads live values
again. This is not an indefinitely cached completion state.

Validated exploration overlays use offset buckets to find nearby candidates, followed
by the same exact two-pixel tolerance and existing map/preview/dimension checks.
Missing evidence stays unknown. Native criterion reads are capped at 256; oversized
custom conditions backed by native criteria stay unknown and cannot prove completion.
The native card adapter continues labeling partial or unavailable criterion sets.

The UI reuses frame pools and finds visible card/statistic ranges in a retained row
plan instead of walking every record on each scroll. Selection, expansion, filtering,
dimensions, model replacement, and loaded criteria invalidate the corresponding plan;
scrolling reuses unchanged data. Sidebar updates follow its own navigation/layout
changes. Summary scrolls its existing content without rebuilding. Real model/size changes
also invalidate the Statistics catalog and criterion-height cache.
Typed search requests coalesce the latest query after 0.12 seconds; programmatic queries
and clearing stay immediate. Callback tokens prevent an old request consuming a new
typing session. Summary retains separate totals, recorded dates, and expandable cards.

## Optional performance diagnostics

Enable diagnostics only when collecting a report:

```text
/fa perf on
/fa perf report
/fa perf off
/fa perf reset
```

Diagnostics default **off each session** and do not write SavedVariables. `on` starts
a fresh collection; `off` stops measurements and retains aggregates for reporting;
`reset` clears aggregates without changing whether collection is enabled. Disabled
instrumentation never reads the profiling or game clock.

`Integrations/Performance.lua` records operation counts, measured samples, total,
average, maximum, and last duration in milliseconds, plus named counters. It uses
guarded `debugprofilestop` when available, otherwise `GetTime` converted to milliseconds.
A missing, restricted, invalid, or reset clock leaves timing unavailable while the
operation count remains known. Clock domains are never mixed within a measurement.

Storage is limited to **64 metric names and 128 outstanding tokens**, with no per-call
trace. Reports contain at most one aggregate line per metric name plus their heading;
the dropped/unavailable counters explain collection limits. Timing totals can include
nested operations, so adding all reported totals does not measure total window time.

Useful report entries include `controller.attach`, `controller.refresh`,
`presentation.build`, `native.enumerate`, `native.info_attempts`, `native.category_attempts`, `custom.catalog`,
`category.generate`, `search.filter`, and `summary.refresh`. UI timings include
`UI.Render`, `UI.ScrollRender`, `UI.CategoryRender`, `UI.SummaryRender`, `UI.ListRender`,
`UI.Search`, `UI.StatisticsRender`, `UI.Resize`, and `UI.TabSwitch`. Counters such as
`search.cache_hits`, `controller.refresh.coalesced`, `UI.RenderRedundant`, and
`UI.PooledFramesCreated` show reused work and frame-pool growth.

## Manual client verification

1. Enable `/fa perf on`, then enable the replacement and open the normal Legacy window.
   Close and reopen it several times. Report metrics after the first opening and after
   reopening; save any fallback/error text together with the report.
2. Switch through Achievements, Rewards, Trees, and Statistics. Browse categories,
   expand/collapse cards, scroll to the final entries, type and clear searches, combine
   supported filters, and change size presets/UI scale. Pure navigation should not
   repeatedly enumerate the native catalog or rebuild unchanged character data.
3. Verify genuine progress updates: ordinary zone/map changes, bag changes, an earned
   custom achievement, native challenge/criteria changes, and authoritative Legacy
   currency changes. Completion, counts, points, and loaded search results must update
   after the deferred refresh. Reopening must recover newly available native records.
4. Close or disable while a refresh/search is queued. Reopen and confirm stale work does
   not alter the new session. Test combat and gamepad transitions, then restore with
   `/fa legacyui off`; original native presentation and interactions must remain usable.
5. Run `/fa perf report`, record the relevant metric counts/durations, then `/fa perf off`.
   Reload and confirm performance collection returns to off. Keep genuine progression
   and SavedVariables intact; do not claim rewards or commit traits solely for testing.

Use the full [integration manual plan](../ForeverAchievements/Integrations/README.md)
for visual fidelity and progression checks. Automated operation-count fixtures do not
emulate client rendering, protected frames, native timing, or server progression.
