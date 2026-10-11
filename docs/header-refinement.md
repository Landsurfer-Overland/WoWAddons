# Header refinement

Build: `0.4.17-alpha-header1`. Includes the combat, Compact fit and opening-flash fixes.

## Character points

The custom catalog previously withheld the entire definitive point total if any
completion or earned point value was unverified. This could display
"Unavailable" even when other character achievements had verified earned points.
The existing exploration-history review is one possible source of that state;
the supplied screenshot alone does not identify the affected character's records.

The adapter now also exposes `confirmedPoints`, the sum already accumulated
from verified current-character completions, and `unverifiedPointRecords`. The
original `points`/`pointsAvailable` contract remains strict. The header shows:

- `120` when the total is verified.
- `120+` when 120 points are verified and other records remain uncertain.
- `0+` when the verified subtotal is zero and other records remain uncertain.
- `—` when current-character attribution is unavailable; no foreign saved
  database is turned into a zero or credited to the current character.

Hovering the header explains the subtotal and unresolved record count. A real
zero remains distinct from an unavailable value. Legacy points still come from
the native authoritative total, remain separate from character points, and use
`—` with an explanatory tooltip when unavailable. Hover uses cached model data,
without another catalog build or point scan. The existing completion validation,
SavedVariables, awards, dates and point weights are unchanged.

## Artwork and alignment

The old native roof was asymmetric around its original single counter. Native
pixel-sized artwork crops now form a mirrored roof and shoulders, centered on
the owned window. Two matching 152-pixel plaques (including their original
18-pixel end caps) sit beneath the raised roof at equal offsets of ±140 pixels.
Smaller gold title labels remain inside the roof rather than sitting on its edge.

The Alliance/Horde logo sits within an 80-pixel native gold shield and laurel
surround. Its smaller 50-pixel square maintains the faction logo's proportions.
The empty regular shield avoids showing another symbol through Horde's
transparent logo. A centered neutral achievement seal remains the unavailable
faction/texture fallback. Crest, surround, roof midpoint and window share the
same horizontal center on Compact, Standard and Large.

No artwork files were replaced or generated. Preset sizes, page layout, tabs,
native progression and the controller lifecycle fixes are unchanged. The XML
generator was updated alongside its generated header so regeneration preserves
the new composition. A local browser layout preview used existing textures and
approximate fonts; it is not an in-game rendering check.

Changed addon functions: `CustomAchievementAdapter.Catalog` aggregation,
`WrathAchievementUI.Create`, `SetModel`, and new `PointsTooltip`. Header XML and
the TOC version also changed. Supporting files are the template generator,
header-refinement regressions, updated header assertions in earlier UI tests,
and this document. `LegacyController.lua` and the progression core are unchanged.

## Client verification

Replace the complete addon folder and `/reload`, retaining WTF/SavedVariables.
Open Legacy with the custom replacement enabled.

1. Verify the character total is numeric, or a clearly marked verified subtotal.
   Hover the header for its explanation; Legacy points should remain independent.
2. Check the crest is centered and framed, with both point plaques seated within
   the same roof. Check Compact, Standard and Large, plus your normal UI scale.
3. Verify header dragging, close/reopen, Rewards and Trees, and entering/leaving
   combat still work without stock-window flashes, timeouts or fallback messages.
4. Where practical, test Horde and unavailable-faction fallback as well as Alliance.

In-game appearance and the specific live character subtotal require confirmation.

Validation: all **587 tests passed**, including eight new header regressions
and the existing combat, opening, sizing, progress and performance checks.
Lua 5.1 syntax checks passed for 27 files; packaging checks passed for 28 TOC
references and four XML files. Core initialization loaded 322 definitions;
the isolated behavior check passed 14 assertions.
