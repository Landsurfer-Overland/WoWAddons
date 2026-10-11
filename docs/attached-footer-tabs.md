# Attached footer tabs

Build: `0.4.23-alpha-footer1`.

The black rectangle was the explicitly added full-width `FooterBacking` texture
using `TutorialFrameBackground`. It is removed from the owned window template
and its generator. Individual tabs retain the original Wrath artwork.

The four navigation tabs now have equal 150-pixel widths, 32-pixel logical
heights and 49-pixel artwork heights for both selected and inactive states.
Their edges touch rather than leaving gaps; the initial left inset stays 20 pixels.
The Compact preset still leaves at least 16 pixels between these tabs and the
size selector.

The size selector now uses the same tab template at a smaller 112 by 24 logical
size with 36-pixel artwork. Its top aligns with the other tabs, and its right edge
stays 20 pixels inside the window edge on every preset. The preset label and
dropdown arrow remain inside that smaller tab. The existing pooled menu,
Compact/Standard/Large choices, outside-click and Escape dismissal, and guarded
controller resize callbacks are unchanged.

Changes are limited to footer construction in `WrathAchievementUI.Create`, a
local tab-sizing helper, removal of the XML footer backing and matching generator
output, and the TOC version. No tracking, SavedVariables, calculations, combat
handling, native Rewards/Trees behavior, sidebar or window-body layout changes.
No additional timers, data refreshes or frame creation on dropdown use.

## Client checks

Replace the complete addon folder, retain WTF/SavedVariables, then `/reload`.
Check that the black rectangle is gone and all four navigation tabs share the
same outline and touch horizontally. Switch through Achievements, Legacy Rewards,
Legacy Trees and Statistics. Check the smaller right-side tab and its dropdown in
Compact, Standard and Large, including outside-click/Escape dismissal and
close/reopen. Check normal combat behavior as well.

Automated fixtures check geometry, selection-state artwork sizes, menu behavior,
frame reuse and template reproducibility. Actual rendering still needs an in-game
check.

Validation: all 618 automated tests passed, including the 150-cycle dropdown
reuse check and template reproducibility. The setup check passed Lua 5.1 syntax
for 28 files, 29 TOC references and 4 XML files, core initialization with 322
achievement definitions, and 14 isolated behavior assertions.
