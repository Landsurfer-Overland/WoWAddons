# Legacy Point Achievements

Build: `0.4.27-alpha-legacy-points1`.

Expand Feats of Strength and select Legacy Point Achievements to browse and
search existing achievements with a confirmed positive Legacy Point reward.
Completed and incomplete achievements are both eligible. Existing search,
completion/source filters, scrolling, expansion and tracking remain available.

The only runtime function changed is `LegacyPresentation.Build` in
`Integrations/Presentation.lua`. It creates the stable `feats:legacy-points`
child selector and fills its membership during the existing canonical-record
indexing pass. It uses the native component's finite positive `pointValue` with
`pointType == "legacy"`, already verified by `LegacyAdapter.Points` through
`C_Traits.GetTraitCurrencyForAchievement`. It does not infer rewards from the
achievement's title, reward text, native achievement points or character points.
Unknown and zero rewards are excluded. A partial native catalog still carries
its existing notice; only its available verified records enter this selector.
The section remains available when no eligible records are known.

This is an additional selector, not a new classification or achievement source.
Records retain their original categories, artwork, progress and point values.
Combined character/native achievements appear once when the native component
has a confirmed reward. Their cards and completion filters use the same
canonical completion as their normal category; the native completion detail
remains visible in the existing card. No completion is granted by the selector.

Its indexed count is independent of the Feats parent and Summary totals, so
cross-category records are not counted twice. The existing alias membership
also supports explicit snapshot invalidation. Search uses the existing bounded
query cache, and navigation uses the existing pooled frames and callbacks.
No extra API enumeration, reward calls, timer, provider rebuild or refresh loop.
No changes to SavedVariables, progression, point calculations, native Rewards
or Trees, combat handling, fallback, layout or header rendering. The TOC version
is updated; tests and this document are the other changed files.

## Checks

Automated cases cover reward API classification rather than text, positive and
zero rewards, missing API, partial-catalog refresh, ordinary and combined rows,
duplicate suppression, original category/source/parent totals, SavedVariables,
search and filters with and without indexes, bounded cached queries without API
reads, and actual sidebar navigation with repeated frame reuse.

Validation: all 633 automated tests passed. The setup check also passed Lua 5.1
syntax for 28 files, 29 TOC references and 4 XML files, initialization with 322
achievement definitions, and 14 isolated behavior assertions.

Install the complete addon folder while retaining WTF/SavedVariables, then
`/reload`. Expand Feats of Strength and select Legacy Point Achievements. Check
that positive-reward challenges appear, zero-reward and unverified challenges do
not, and search and completion filters work. Open an achievement in both its
original category and this selector and verify identical progress and artwork.
Confirm point counters and Summary totals stay unchanged, navigation survives
reopening, and Rewards/Trees and combat behavior remain normal. Rendering and
actual game API behavior still require in-game testing.
