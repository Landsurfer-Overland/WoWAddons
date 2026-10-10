# Iteration 6 UI refinements and client checks

Build: `0.4.13-alpha-iteration6`. Target: Forever 1.60.1, build 70338,
Interface 16001, project 18, Lua 5.1. This iteration changes presentation only.
Achievement definitions, categories, progression, SavedVariables schema, native
completion authority, indexed providers, performance diagnostics and error fallback
retain the previous implementation.

## Window and controls

Standard is the default for new or invalid size preferences: a **960 × 620** logical
body, **960 × 760** including the header and footer. Compact remains 768 × 500;
Large remains 1024 × 720. Valid existing choices remain respected. The movable
outer window still scales down to fit the screen without scaling its contents
individually. No migration rewrites a saved preference or position.

The size selector is an owned three-option dropdown with an arrow and current-choice
check. It fits beside the four existing footer tabs, including at Compact. Its
frames are allocated once. Opening or dismissing it does not render the model;
selecting the current preset does nothing. Selecting another uses the existing
controller resize path. Size and filter menus dismiss each other and close on
Escape, tab changes, full render or window hiding.

Header plaques preserve the original 18px ends and 39px height; only their plain
centers widen. The roof, wood border, metal corners and parchment slices retain
their original geometry. Recognized Alliance/Horde characters use the native
`Interface/Timer/Alliance-Logo` or `Horde-Logo` crest. Unknown/unavailable faction
information retains the neutral original shield emblem. The two independently
bound totals and the crest remain centered around the original header.

## Headings and scrolling

A fixed heading sits above the selected-category viewport. It shows the actual
parent and subcategory names, or the selected main-category name. The gold dividers
use three slices of the original Wrath `UI-Achievement-Stat-Buttons` texture,
retaining 23px decorative caps. Two reusable font strings wrap long names within
48px/36px limits; a tooltip exposes the full names. Heading height is bounded at
94px. Search remains above it and the viewport bottom remains inset by 29px.
Summary, linked-achievement focus and native pages retain their existing behavior.

The list scrollbar uses an owned Slider, two arrow buttons and the original
`UI-ScrollBar-*` textures. It occupies a 22px gutter inside the content panel,
outside the clipped card viewport. Its thumb is proportional to viewport/content
height with an 18px minimum. Wheel, arrow and Slider input share bounded scroll
limits. A synchronization guard prevents value-change callback recursion; range
updates reuse controls and do not query providers or rebuild card data. The sidebar
uses the same bounded scrolling helper. Existing measured lists and viewport card
pools remain active.

## Completion artwork

`U.CardVisualState` determines one state from the source components. It does not
write completion, points, dates or progress.

| Source state | Card and central shield | Wreath | Completion detail |
| --- | --- | --- | --- |
| Custom and Legacy incomplete | Gray | Gray | No Legacy completion claim |
| Verified Legacy complete; custom incomplete or unverified | Gray | Blue | `Completed via Legacy`; no character date or earned points |
| Verified current-character completion | Original gold | Original gold | Actual character date; native completion remains in the point tooltip/details |
| Native-only complete | Gray native presentation; actual native point value | Blue | `Completed via Legacy` and actual native date when supplied |

Custom completion takes precedence even when its native component is complete.
The point shield always uses its actual source value; a combined card retains its
custom award value without treating native completion as earned character points.
Native-only cards retain actual Legacy points, including verified zero, and have
no fabricated character requirement. Unknown values remain unknown. The blue label
sits at bottom-right within the description column, outside the shield/date column.
It does not repeat `Legacy: 0 points` or imply a named earner. Expanded criteria and
point tooltips preserve independent source information.

### Texture implementation and limits

The original 128 × 128 `UI-Achievement-Shields` sheet combines central shield and
laurels; it has gold/gray normal variants above progressive variants. The matching
NoPoints sheet has the same geometry. Two addon-owned, complementary 64 × 64 alpha
masks divide the displayed quadrant into a central shield and the original laurels.
Both texture layers reuse client artwork; their visible pixels complement each
other instead of stacking duplicate shields. Only the laurel layer is tinted blue.
Gold and gray reconstruct the original sheet. Two masks and one extra texture are
created once per pooled shield, with no per-refresh mask creation.

`tools/generate_achievement_masks.py` regenerates the uncompressed 32-bit,
power-of-two TGA masks using the standard library. Original raster artwork is not
bundled or edited. Geometry was inspected against the public
[normal sheet](https://github.com/Gethe/wow-ui-textures/blob/live/ACHIEVEMENTFRAME/UI-ACHIEVEMENT-SHIELDS.PNG)
and matching NoPoints sheet. Actual Forever atlas alignment and alpha-mask
rendering still need in-game verification. Native Forever Legacy source uses
`AddMaskTexture`/`RemoveMaskTexture`; mask creation and attachment are checked at
runtime. Unsupported or failed mask setup retains the original composite
gray/gold shield and the meaningful blue label. The existing UI fallback remains
active for other rendering failures.

The original statistic-header decoration, simpler native faction shield and
scrollbar bevels differ from the generated mockup. Binary mask edges can reveal
seams when resampled at different UI scales. A proportional thumb vertically resizes the
original knob texture; arrow artwork retains its fixed dimensions. Original native
page aspect-ratio margins and source-art resolution remain constraints. Supplied
Wrath reference sources remain unmodified; `tools/adapt_wrath_templates.py`
reproduces the addon-owned XML.

## Why Achievement Points can show Unavailable

The reproducible path is `C:Refresh` → `P.Build` → `CustomAchievementAdapter.Catalog`
→ `U.SetModel`. Catalog deliberately returns an unknown total when a custom
completion state is unknown. One such case is retained Moonglade completion history
without verified current-character attribution or local evidence. Its positive
saved timestamp alone cannot prove completion under the previous history gate;
dependent Kalimdor/world records can likewise remain unverified. The saved history
is preserved. A fresh unknown progress reading without a saved completion does not
by itself poison the total: it remains incomplete and contributes zero.

Unavailable character identity and malformed saved timestamps can also make
completion unknown. The specific player's cause cannot be established without
their current diagnostics/SavedVariables. This iteration preserves that distinction
and does not substitute mockup totals or remove history. Use
`/fa inspectachievement explore855`, related meta inspection and
`/fa progressdebug on` / `/fa progressdebug dump` to identify the live evidence.
Correction commands are optional and are not needed for this UI update.

## Changed functions and files

| Area | Functions/files |
| --- | --- |
| Default and selection | Controller `C:Preset`, `C:Attach`; UI `U.Create`, `U.DismissMenus`, `U.Layout`, `U.SetTab` |
| Shell | `U.TabOnLoad`, generated `UI/WrathAchievementUI.xml`, `tools/adapt_wrath_templates.py` |
| Heading | `U.CreateCategoryHeading`, `U.CategoryHeading`, `U.RenderPass` |
| Scrollbar | `scroll`, `syncScrollbar`, `clampScroll`, `U.LayoutContentScrollbar` |
| Cards | `U.ShieldOnLoad`, `U.CardVisualState`, `saturate`, `U.RenderCard`, `U.MeasureCard`, `U.ShieldEnter` |
| Masks | `Media/Achievement-{Shield,Wreath}-Mask.tga`, `tools/generate_achievement_masks.py` |
| Validation/docs | Iteration 6 UI/header tests, updated historical visual expectations, TOC version and current READMEs |

## Automated validation

The complete Lua 5.1 regression suite passes **548 tests**, including **59 new
Iteration 6 tests**. Setup validation passes syntax checks for 27 Lua files,
28 TOC references, four XML files, initialization of 322 definitions and 14
isolated behavior assertions. The template and mask generators reproduce their
committed output. Supplied reference files and progression/provider/native bridge
sources remain unchanged.

```sh
PYTHONPATH=/workspace/.cloud-tools/forever-achievements/python python -B -m unittest discover -s tests
sh /workspace/.cloud-tools/forever-achievements/install.sh
```

These commands use the environment's existing pinned Lupa 2.6/Lua 5.1 setup.
For another environment, follow the [test setup](../tests/README.md).

## Manual in-game checklist

Automated checks execute actual addon Lua/XML with explicit client doubles. They
cannot validate rendering, real input, taint, live timing, server progression or
SavedVariables disk persistence. These client checks remain pending.

1. Replace the complete addon folder, keep existing WTF data, leave combat and
   enable `/fa legacyui on`. A fresh preference opens Standard; an existing saved
   preference remains selected. Test all three sizes and several UI scales and
   resolutions. Move, close/reopen and reload; confirm position persistence.
2. Inspect roof, wood/metal borders, corners, parchment seam and footer. Check
   centered faction/neutral crest, separate counter labels/values/shields and
   undistorted art. Verify tab order: Achievements, Legacy Rewards, Legacy Trees,
   Statistics. The size dropdown must not collide with tabs at any preset.
3. Open both dropdowns, select each size, reselect the current size, click outside,
   Escape, hide/reopen and switch tabs. Menus must dismiss cleanly and changing size
   must preserve progress, category/selection and native-page functionality.
4. Select main and child categories, including Exploration → Eastern Kingdoms.
   Check centered parent/child titles, decorative caps, search spacing and long-name
   wrapping/tooltips. Summary and linked meta navigation must still work. Category
   assignments and source ordering must match the real data.
5. Scroll by wheel, drag and both arrows through a long list and long sidebar.
   Check proportional thumb and limits. Expand/collapse entries near the bottom,
   resize and navigate while scrolled. Content must remain accessible, controls
   aligned inside the panel, and shield/text clear of the scrollbar.
6. Find real examples of all four completion states in the table above. Verify
   gray/blue/gold precedence, independent central shield/laurels, actual points,
   dates and label placement. Check ordinary and NoPoints art at several UI scales;
   look for mask seams or accidental blue shield edges. A combined character
   completion must remain gold when the native version also completes.
7. Check search/clear/filter combinations, criteria, tracking, expansion, long
   descriptions, source point tooltips and Statistics navigation. Confirm native
   zeros, unknown values and unverified history retain their meanings. Compare
   both independent header totals with their actual source data.
8. Use real native Reward and Tree controls in all presets; check aspect ratio,
   centering and original progression. Restore `/fa legacyui off` and verify native
   geometry, inputs and tabs return. Check combat and gamepad transitions.
9. Enable `/fa perf on`; repeatedly open/close, switch tabs/categories, scroll,
   expand and search. Keep any error/fallback text and `/fa perf report`. Confirm
   no script timeout in the client; automated tests alone cannot establish this.
10. Turn diagnostics off and reload two characters. Verify SavedVariables and genuine
    character/native progression persist. Do not reset or correct valid progress
    merely to manufacture a visual test state.
