# Compact category stack

Build: `0.4.22-alpha-stack1`.

The persistent selected-row texture used the original Wrath category highlight
with normal blending. The supplied XML uses additive blending for that artwork;
normal blending rendered its black pixels as the rectangle visible behind Summary.
The persistent texture now uses `ADD` and the same anchors as the original hover
highlight. Selection and mouse hover remain independent, with the existing art.

Category rows now use the original 24-pixel logical height, separated by just
one pixel, at every size preset. The original backing retains its 32-pixel height
and top-left/top-right anchors rather than stretching across oversized hit rows.
Parent and child edges retain equal widths and four-pixel viewport margins;
the existing scrollbar gutter stays available. Fonts, colors and internal hierarchy
indentation remain. Spare panel height is not distributed between buttons.

Expansion inserts child rows directly after their parent, pushing the rest of
the stack down by one row pitch per child. Collapse closes that space again.
Long expanded stacks scroll using the existing controls. Achievement and Statistics
navigation share this behavior; signatures, row reuse and render guards remain.

Runtime changes: `WrathAchievementUI.Layout` category metrics and
`RenderCategories` selection blending/backing anchors, plus the TOC version.
No XML, artwork, calculations, SavedVariables, combat or tracking changes.

## Client checks

Replace the complete addon folder, retain WTF/SavedVariables, then `/reload`.

1. Check Summary and other selected rows: no opaque black rectangle should
   appear behind the green selection. Check mouse hover as well.
2. Verify main and child buttons form a compact, aligned stack in Compact,
   Standard and Large. Expand Dungeons & Raids, Reputation and other parents;
   later rows should move down and return upward when collapsed.
3. Check selecting parents/children, separate expand controls, Statistics,
   scrolling to the last expanded row, combat and close/reopen.

Automated fixtures cover additive selection settings, original backing geometry,
uniform compact rows on every preset, expansion/collapse displacement and frame
reuse. Actual texture blending and perceived spacing still require the client.

Validation: all 617 automated tests passed. The setup check also passed Lua 5.1
syntax for 28 files, all 29 TOC references and 4 XML files, core initialization
with 322 achievement definitions, and 14 isolated behavior assertions.
