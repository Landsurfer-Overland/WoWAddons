# Tab labels and child category insets

Build: `0.4.24-alpha-align1`.

The main footer labels move up four pixels while retaining their horizontal
center, tab dimensions and attached anchors. The smaller size tab also moves its
label and arrow up four pixels. The label is centered in a 62-pixel region inset
18 pixels from the left; the dropdown arrow moves six pixels inward from its
previous position. This brings the visible preset text and arrow together without
overlap. Dropdown behavior and pooled options remain unchanged.

Category expand controls move four pixels inward. Labels reserve the matching
space so they do not overlap the expand controls. Child categories inset the whole
button by 12 pixels per level, capped at three levels, with correspondingly reduced
width to keep their right edges aligned. This includes the backing, hover/selection
art and click bounds. The former decorative dash texture is no longer created.
The existing 24-pixel row height and one-pixel gap remain; expansion still inserts
rows and pushes subsequent entries down.

Runtime changes: `WrathAchievementUI.TabOnLoad`, size-label/arrow anchors in
`Create`, and child-row geometry in `RenderCategories`, plus the TOC version.
No XML, artwork, calculations, SavedVariables, tracking, native Rewards/Trees,
combat handling or new refresh/timer changes. Existing sidebar caching and frame
reuse remain.

## Client checks

Replace the complete addon folder, retain WTF/SavedVariables, then `/reload`.
Check that all four footer labels sit higher in their tabs. Verify that Compact,
Standard and Large fit beside the arrow and that selecting a preset still works.
Expand General, Quests and other parents: child button left edges should step
inward with no dash before the title, while right edges remain aligned. Check
parent/child selection, the separate expand controls, scrolling and Statistics.

Automated fixtures cover all presets, compact stacking, selection blending,
expansion displacement, navigation, bounded reuse and dropdown behavior. Actual
perceived alignment still requires the client.

Validation: all 618 automated tests passed. The setup check passed Lua 5.1 syntax
for 28 files, 29 TOC references and 4 XML files, initialization with 322
achievement definitions, and 14 isolated behavior assertions.
