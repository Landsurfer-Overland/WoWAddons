# Wrath Summary layout

Build: `0.4.25-alpha-summary1`.

The Summary follows the reference's content hierarchy: Recent Achievements
first, up to four compact dated rows, then Progress Overview with a full-width
Achievements Earned bar and paired category bars. Existing roof counters, search
controls, navigation, tabs and size presets remain.

Collapsed recent rows use a 48-pixel height, smaller versions of the existing
icon/shield artwork, centered titles, descriptions and upper-right dates. The
title reserves space for the date. Clicking a recent row expands its normal
description and criteria; clicking again restores the compact row. Reusing that
frame for a category list restores its original scales, anchors and regular
84-pixel collapsed geometry. The active expanded record retains the existing
dedicated first card slot and bounded objective pools.

The unified earned count comes from the existing `Presentation.Count(model,
"summary")` aggregate. It counts canonical records rather than adding overlapping
Custom and Legacy source totals. Points, completion logic, source counts and
recent-event deduplication are unchanged. Undated native completions are not
fabricated into recent rows, and fewer than four reliable events do not produce
fake placeholder achievements.

The two-column overview pairs General/Quests, Exploration/PvP and Dungeons &
Raids/Professions, followed by the remaining available root categories. Existing
Classes and Feats of Strength remain visible; unsupported reference categories
are not invented. This ordering applies only to the copied Summary category list,
with no navigation/category mapping change. All category bars remain clickable.

Counts show the existing observed data. The overall bar keeps explicit partial
and unknown text. In narrow category bars, `*` marks available-record counts and
`(?N)` identifies N unknown completions; a small legend appears only when needed.
Labels/counts receive separate widths to prevent overlap. Known normal counts
retain the familiar earned/total form. Unknown records never increase completion.

Runtime changes are confined to `UI/WrathAchievementUI.lua` and the TOC version:
Summary rendering in `RenderPass`, compact mode in `RenderCard`, a mode-change
geometry helper, responsive `SummaryBar` text and one reusable legend. No XML,
artwork files, tracking, SavedVariables, verified point calculations, native
Rewards/Trees, combat/fallback handling or provider changes.

Frame pooling, aggregate caches and the Summary scroll shortcut remain. Compact
rows do not fetch criteria; only a selected expanded row does. The renderer orders
at most eight existing source-recent events and the small root-category list,
without achievement database scans or extra refresh timers.

## Validation

All 624 automated tests passed. Coverage includes reference hierarchy at every
preset, four most recent dated records, unified counts, category navigation,
partial/unknown markers, expanded criteria, restoring pooled list geometry and
repeated-render/scroll reuse. Existing relationship tests also verify that recent
Custom and Legacy events for one unified record share one card.

The UI double was corrected to keep frame anchors separate from the shield's
public `points` FontString, and now models the standard `GetStringWidth` API.
Neither change alters runtime addon behavior. The setup check passed Lua 5.1
syntax for 28 files, 29 TOC references and 4 XML files, initialization with 322
achievement definitions, and 14 isolated behavior assertions.

## Client checks

Replace the complete addon folder, retain WTF/SavedVariables, then `/reload`.
Open Summary and compare its recent rows and paired progress overview with the
reference. Check Compact, Standard and Large, including long titles and dates.
Open/collapse a recent achievement, then select a category and confirm regular
cards retain their previous size. Click category progress bars and check scrolling
when expanded or using Compact. Verify unknown indicators if present, counters,
Rewards/Trees, close/reopen and normal combat behavior.

Automated geometry checks do not verify actual textures or in-game rendering.
