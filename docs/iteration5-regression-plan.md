# Iteration 5 presentation changes and client checks

Build: `0.4.12-alpha-iteration5`. Target: Forever 1.60.1, build 70338,
Interface 16001, project 18, Lua 5.1. This extends the Iteration 4 code and retains
the four-tab controller, indexed data model, deferred rendering, bounded frame pools,
performance diagnostics, error fallback, and native completion authority.

Automated tests exercise actual addon Lua and XML callbacks with explicit frame/API
doubles. They cannot establish live asset appearance, click propagation, taint safety,
server progression, client timing, or SavedVariables disk persistence.

## Window and controls

New or invalid size preferences use Large (1024 × 720 logical body). Explicitly
saved Compact/Standard/Large choices remain respected; no settings migration erases
them. Header/footer space adds 140 logical pixels; the outer window still scales
down to fit the screen. `/fa legacyui size large` selects the larger form when an
older explicitly chosen smaller preset remains saved.

The frame restores the original achievement wood-border backdrop with native 64px
edge geometry. A continuous parchment backing supports the sidebar and content,
and a separate footer backing anchors evenly spaced tabs. Decorative roof/corners
retain their native pixel sizes. Header hit/backing space increases, while matching
point plaques surround a neutral shield seal cropped from the existing character
achievement sheet. The labels are Achievement Points and Legacy Points; their
source totals stay independent.

Search, clear button, and the filter share a control row. The filter opens an
addon-owned five-option menu with a down arrow and current-selection check:
All, Completed, Incomplete, Character Achievements, Legacy Challenges. The menu
and its dismissal surface are allocated once. Selecting a filter uses existing
indexed queries; opening/dismissing it does not rebuild a catalog. Closing the
window or leaving Achievements closes the menu.

Sidebar parent/child rows are 29/26 pixels high. Clicking a whole parent row
selects its directly assigned achievements and toggles its children once. The
plus/minus button toggles only, preserving the selected list. A child without
children selects its own list. Statistics retains independent navigation state.
Broad General achievements now occupy General directly, while explicit progression,
collection, and miscellaneous children retain their narrower lists. Broad native
reputation milestones map to Reputation; faction-specific records retain their
subcategories. Parent counts can include descendants without aggregating the list.

## Achievement details

Ordinary cards omit routine scope labels, incomplete-character sentences, and
per-objective unknown-state explanations. Unknown objectives remain unchecked;
their stored fields stay unknown. Criteria use left-aligned labels and adjacent
checkmarks. A completed native record retains restrained blue accents; verified
current-character completion retains gold. Combined cards keep one character-point
shield with separate native status, points, criteria, and completion.

Recorded previous-character names appear only for verified Legacy-linked cards or
relevant native/account completion. Ordinary custom cards suppress that note while
retaining the snapshot data. Point tooltips identify independent awards without
routine scope or incomplete-state filler. Debug commands retain full evidence.

Money descriptions are plain requirements such as `Loot 5g.` or
`Earn 100g from quest rewards.` Progress shows only amount and goal, for example
`2g 3s / 5g`, without repeating the achievement title or exposing tracker provenance.
Unavailable earnings use a dash and goal, with no invented zero or filled bar.
The copper tracker, configured thresholds, source checks, event deduplication and
historical counters are unchanged. `/fa money report` retains the source audit.

## Exploration display corrections and limits

The remaining reproducible Moonglade path was saved-history authority: a positive
`done.explore855` timestamp could still produce completed artwork, recents and
points even after the Iteration 4 trigger stopped accepting remote map textures.
That timestamp alone does not prove the historical award was legitimate.

Moonglade history now requires verified character attribution or matching local
discovery evidence before it supplies current-character completion. Without either,
the card remains present with an unverified state; raw completion history and its
timestamp remain saved. Dependent Kalimdor/world history cannot propagate an
unverified Moonglade award into another gold completion. Fresh local verification
can restore displayed completion with the original saved timestamp. The historical
display gate is limited to this reported family; unrelated older zone completions
retain their existing behavior. All new zone awards retain Iteration 4's generic
geography/overlay/character-proof requirements.

No live SavedVariables or client trace was supplied for this iteration, so the
specific player's original Moonglade award has not been independently reproduced
in the client. `/fa inspectachievement explore855` reports retained history and
verification; `/fa progressdebug on` and `/fa progressdebug dump` retain decision
diagnostics. Optional correction still requires explicit token confirmation.

The existing custom `worldexplorer` key/ID 46 is now named Explore Azeroth. It keeps
its original 50 points, Eastern Kingdoms/Kalimdor criteria and saved history; there
is no additional custom 50-point record. Verified native 62053 can share its card
under the existing exact-criteria relationship rules. Otherwise both sourced records
remain separate in World Exploration. Native Explorer wrappers 62382/64015 retain
their own IDs, criteria and rewards.

Custom individual zones retain 10 points, continents 25 points and the world meta
50 points. Cards use the actual source award; a verified native zero remains zero.
Combined cards never add a second character reward from native completion. No
native point thresholds or rewards are changed. A native/custom point mismatch is
shown as independent source values rather than guessed into an extra point system.

## Native page fit and artwork constraints

Rewards and Trees fit their original aspect ratio uniformly into the content host,
including modest enlargement in Large. The fit accounts for the host and native
root effective scales; native dimensions, ancestry, scripts, data, controls and
original geometry remain preserved. Invalid metrics fail through the existing
fallback before native selection/suppression. Mounting remains idempotent and
restoration uses the existing full geometry snapshot.

Enlargement is capped at 1.5× to limit magnification of original textures. Different
host/native aspect ratios can leave deliberate empty margins; the pages are neither
cropped nor stretched. Original art resolution, native protected frame constraints
and UI scaling still limit cosmetic fidelity. No new artwork or native backend
implementation is bundled. Reference Wrath files remain unmodified; the template
generator reproduces the addon-owned XML.

## Changed functions

| Area | Functions |
| --- | --- |
| Shell and controls | `U.Create`, `U.Fit`, `U.Layout`, `U.TabOnLoad`, filter callbacks, `U.RenderPass` menu visibility; generated window/header XML |
| Navigation | `U.CategoryClick`, `U.CategoryExpand`, `U.RenderCategories`; Presentation `defaultSubject`/native category context |
| Cards | completion/quantity helpers, `U.ShieldEnter`, `U.RenderCard`, `U.MeasureCard` |
| Native fit | Bridge `geometry`, `fitScale`, `B:Mount` |
| Money text | `M.Description`, `M.Progress` |
| Default size | `C:Preset` |
| Moonglade/history | `Proof.CompletionStatus`, `Proof.Completed`, `Earned`, `TotalPoints`, custom `Catalog`, saved-character snapshot handling and inspection diagnostics |

## Manual client checklist

1. Install the complete addon folder while retaining WTF data. Enable
   `/fa legacyui on`. With no explicit size choice, confirm Large opens; check an
   existing saved smaller preference remains respected. Test all three presets,
   screen resolutions/UI scales, dragging and position reset.
2. Inspect frame corners, long borders, backing, parchment transition and footer
   for clipping/seams. Check the roof/crest and both counter labels, numbers,
   shields and spacing. Confirm text does not collide with the decorative art.
3. Verify tabs appear in order: Achievements, Legacy Rewards, Legacy Trees,
   Statistics. Check identical anchoring and footer spacing on every page; the size
   button must remain clear of the tabs at Compact too.
4. Type, clear and escape from search. Open the filter, select every option, check
   its current-selection mark, dismiss outside it, close/reopen and switch tabs.
   Search/filter must preserve the existing source/completion semantics.
5. Click the text/blank portions of General, Professions and Reputation parent rows:
   children toggle and the direct general list appears. Click their plus/minus:
   only expansion changes. Select children, scroll the sidebar, and check thicker
   rows, truncation, selection highlight, counts and independent Statistics navigation.
6. Expand ordinary, native and combined cards. Verify no Scope, Not completed on
   this character, or per-line completion-unavailable filler. Ordinary custom
   achievements must omit another character's note; verified Legacy-linked cards
   may name the actual recorded earner. Check blue/gold states and independent points.
7. Check critter-love objectives and other checklists: completed checkmarks sit
   beside their own left-aligned labels. Check wrapped descriptions, long criteria,
   progress bars, meta navigation, expansion/collapse, tracking and pool reuse.
8. On a fresh character, inspect Moonglade before visiting it: no false custom gold,
   date, recent or earned points may appear. Shared native completion can remain
   blue independently. On an affected old character, verify retained history is
   inspectable and not deleted; genuine local re-verification preserves the old date.
   Do not run correction commands merely to test legitimate progress.
9. Check World Exploration: the original custom world meta is Explore Azeroth/50
   points with no extra World Explorer custom card. Verified relationships share
   one card; uncertain relationships remain clearly sourced. Check zone/continent
   awards and independent native zeros/rewards.
10. Check all money tiers and quest income. Descriptions contain only the actual
    requirement; bars show formatted amounts/goals. Loot normal coins and observe
    one increase, then navigate/reload to confirm no extra earnings. Unknown quest
    income must not display a fabricated zero. Compare `/fa money report` evidence.
11. In Large/Compact/Standard and at different UI scales, use actual native Reward
    controls and Tree interactions. Verify uniform sizing, centering, no distortion,
    no clipped controls, original data/progression, and restoration via
    `/fa legacyui off`. Check Statistics values/navigation remain functional.
12. Enable `/fa perf on`, repeatedly open/close, rapidly navigate, expand cards,
    scroll and search. Check all four tabs and combat/gamepad transitions. Preserve
    any fallback/error text and `/fa perf report`; no script timeout may be claimed
    resolved until these checks run in-game. Turn diagnostics off and reload both
    characters to verify SavedVariables and genuine progress persist.
