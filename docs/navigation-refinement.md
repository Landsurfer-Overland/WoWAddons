# Achievement navigation refinement

Build: `0.4.19-alpha-navigation1`.

The Achievement Points tooltip was attached to the entire draggable roof.
Its `OnEnter`/`OnLeave` handlers and `PointsTooltip` method are removed. Header
dragging and all displayed counters remain unchanged. Verified points,
unverified-record exclusions, `+` subtotals, unavailable values and independent
native Legacy points use exactly the previous calculations and display binding.

Category rows now have equal widths, heights and gaps for parents and children.
Their edges align with four-pixel horizontal margins inside the scroll viewport.
Compact uses 36-pixel rows with six-pixel gaps; Standard uses 40-pixel rows with
ten-pixel gaps; Large uses 40-pixel rows with twelve-pixel gaps. Expanded lists
scroll normally rather than shrinking or redistributing buttons when opened.
Hierarchy indentation moves inside the button, on the existing label, connector
and expand control. Existing textures, fonts, colors and selection/expand
callbacks remain. Achievement and Statistics navigation share this geometry.

Dimensions are calculated only during an existing size change. The sidebar's
existing signature cache, frame pool and catalog remain intact; no extra refresh
callbacks, timers, scans or new frames are introduced. Current selected categories,
expanded state and scroll behavior retain their existing lifecycle.

Runtime changes are limited to `WrathAchievementUI.lua` (`Create`, `Layout`,
`RenderCategories`, removed `PointsTooltip`) and the TOC version. The original
alpha quarantine and previous combat, opening and header fixes remain.

## Client checks

Install the complete addon folder, retain WTF/SavedVariables, then `/reload`.

1. Hover both point counters and the roof: no achievement-point tooltip should
   appear. Check displayed totals/subtotals and header dragging remain correct.
2. Check category alignment, row size and gaps in Compact, Standard and Large.
   Expand several parents and verify child labels remain visibly indented.
3. Select parent rows, child rows and expand controls. Check selection, scrolling
   to the last category, collapse/reopen, and Statistics navigation.
4. Confirm Rewards, Trees, combat transitions and open/close behavior remain
   correct, without Lua errors, unexpected fallback or script timeouts.

All **599 automated tests passed**. Lua 5.1 syntax passed for 28 files;
packaging passed for 29 TOC references and four XML files. Core initialization
loaded 322 definitions and passed 14 isolated behavior assertions.

Automated checks cover counter attribution, absent tooltip handlers, unrelated
tooltip preservation, dragging, geometry on every preset, unchanged row caching,
expansion/navigation and existing performance/lifecycle regressions. Actual
client rendering and appearance require in-game verification. No additional
reference screenshot accompanied this request; proportions use the existing
Wrath references in the conversation.
