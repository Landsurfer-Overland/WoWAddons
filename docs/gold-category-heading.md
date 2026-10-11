# Gold category heading

Build: `0.4.26-alpha-heading1`.

Category titles/subtitles now follow the second reference: a centered gold title,
thin horizontal gold rules with small mirrored diamond knots beside it, and a
smaller centered subtitle directly below. The wide red subtitle panel is removed.
Its source was the statistic-row atlas sampled as a stretched header strip.
The new decoration uses transparent owned line primitives and one-pixel rules,
with no filled background or dependency on that atlas's client-specific colors.

The duplicate boxed heading above the content was the hover tooltip. Ordinary
readable headings no longer open it. The full-name tooltip remains when a long
title or subtitle exceeds the existing bounded wrapping heights.

Titles retain the selected category's actual parent name; subtitles retain the
selected child name. The title stays centered across the content panel. Rules
adapt to measured title width and knots retain their fixed size; when a long title
leaves insufficient space, knots hide instead of crossing the text. Clients without
the optional `CreateLine` API retain thin rules and centered text without knots.
Subtitle-free root categories no longer reserve an empty decorative subtitle row.
Lists remain below the heading with their existing eight-pixel clearance.

Runtime changes are limited to `CreateCategoryHeading`, `CategoryHeading`, a
small one-time ornament helper in `UI/WrathAchievementUI.lua`, and the TOC version.
The heading frame/regions are reused; the layout cache still skips unchanged
categories, names and widths. No achievement/provider scans, new timers or refresh
callbacks. No XML, image files, category mappings, Summary, navigation, tracking,
point calculations, SavedVariables, native Rewards/Trees or combat/fallback changes.

## Client checks

Replace the complete addon folder, retain WTF/SavedVariables, then `/reload`.
Check General/Character and Exploration/Eastern Kingdoms against the reference.
Verify centered gold text, thin rules and knots beside the title, a subtitle below
with no red panel, and no duplicate box on ordinary hover. Check root categories
with no subtitle, long names, all three size presets, search/filter and scrolling.
Verify Summary and native Rewards/Trees retain their existing appearance.

Automated checks validate hierarchy, spacing, title clearance, bounded long-name
layout/tooltips, no ordinary tooltip, region reuse and list viewport bounds.
Actual line rendering and perceived proportions still require the WoW client.

Validation: all 624 automated tests passed. An isolated compatibility check also
passed with `CreateLine` unavailable. The setup check passed Lua 5.1 syntax for
28 files, 29 TOC references and 4 XML files, initialization with 322 achievement
definitions, and 14 isolated behavior assertions.
