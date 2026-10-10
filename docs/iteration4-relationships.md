# Iteration 4 exploration relationships and category audit

The presentation pairs zone records only after proving that the two definitions
have the same requirements. It never joins SavedVariables, completion events,
points, dates, native IDs, or account and character completion.

For an eligible custom zone, `Presentation.Build` requires all of:

1. An explicit zone identity: the authored numeric zone achievement ID in
   `ns.EXPLORE`, or a captured extra-zone mapping listed below.
2. The expected zone name and full requirement description on both records:
   `Explore <zone>, revealing the covered areas of the world map.`
3. A complete native objective set with exactly the same names and count as the
   authored custom zone's areas. Every native objective must be map-revelation
   criterion type 43 with required quantity 1. Different kinds, thresholds,
   missing fields, duplicate objectives, and unavailable APIs cannot prove parity.

Titles alone, zero native points, and shared reference IDs cannot establish a
relationship. Successful checks cache only the objective definition signature,
keyed by client build, native ID, native name/description, and the full custom
objective-name set. Native completion and progress are always read from the
current native catalog; custom completion remains in the current character DB.

Continent and world metas can also use one card after every underlying zone
requirement is positively verified. The explicit meta ID must have exactly the
expected native type-8 child-ID set, each with required quantity 1. Continent
checks accept matching cached zone-definition proofs; the world check requires
both positively verified continent relationships. An unverified dependency,
different child requirement, or exhausted shared budget leaves the meta separate
and records the reason. The Explorer account wrapper is never folded into a
current-character world meta.

The native definition verification has one shared limit of **256 attempted
criterion/count reads per native catalog snapshot**, including failures. The
reported Westfall, Elwynn Forest, and Moonglade pairs are checked first. Already
loaded complete native criteria are reused. Unknown and failed checks are cached
only for that snapshot and retried when normal native invalidation or reopening
produces another catalog. A partial scan does not schedule extra model builds.
When the budget is exhausted, remaining records stay separate and appear in
`model.relationshipAudit`; a later normal refresh may establish those relationships.

Metrics `relationship.verify` and `relationship.criteria_reads` are available
through `/fa perf on` and `/fa perf report`. No relationship cache is persisted.

## Combined card contract

A normalized zone card has `source = "combined"`, its custom stable key, and
independent `character` and `native` components. Its ordinary completion,
character points, progress, tracking, date, and cross-character attribution come
from the custom component. Its native indicator reads only the native component.

Both source keys resolve to the normalized card through `model.byKey` and
`Presentation.Resolve`. `Presentation.SourceRecord(model, sourceKey)` returns the
corresponding source component when a caller needs its original ID or state.
`Presentation.Criteria` exposes two independently labeled sections. It does not
blend criterion completion or infer either accomplishment from the other.

Source totals, source recents, and source point totals stay independent. Category
lists render one normalized card, and category totals count that card once.
A combined card with current-character incompletion and native completion is
incomplete in the general Completed/Incomplete filter; the explicit `legacy`
source selector evaluates its native state. Both source filters retain the card.

## Ambiguous and separately maintained relationships

The following native IDs are captured runtime/client-reference evidence. Their
existence is not a substitute for live objective verification on build 70338.

| Records | Evidence | Iteration 4 handling |
| --- | --- | --- |
| `custom:explore802` / `legacy:802` — Westfall | Native Eastern Kingdoms criterion references native asset 802. The available community capture does not include its full zone criteria. | Prioritize live exact objective verification. One card only when parity is proven; otherwise retain both and record the reason. |
| `custom:explore776` / `legacy:776` — Elwynn Forest | Native continent asset 776; full captured zone objective set is unavailable. | Same strict live verification. Neither record grants the other's completion. |
| `custom:explore855` / `legacy:855` — Moonglade | Native Kalimdor asset 855; custom definition has one map revelation. A shared asset or one similarly named objective is insufficient. | Same strict live verification, including native type and required quantity. This relation does not repair old character completion history. |
| Zones 760, 761, 765, 766, 775, 777 | Earlier community captures contain full type-43 objective sets matching the authored custom area-name sets: 15, 16, 14, 9, 10, and 3 respectively. | Still verify against the live client before pairing; old captured completion is never imported. |
| `custom:exploreRiverglades` / `legacy:62354` | Native Eastern Kingdoms meta explicitly references Riverglades 62354. | Explicit candidate ID; require the same full live objective proof. |
| `custom:exploreHyjal` / `legacy:62356` | Native Kalimdor meta explicitly references Hyjal 62356. | Explicit candidate ID; differing zone wording or objectives remains separate. |
| `custom:exploreShendralas` / `legacy:63684` | Native Kalimdor meta explicitly references Shen'dralas 63684. | Explicit candidate ID; require the same proof. |
| `custom:exploreEK` / `legacy:62353`; `custom:exploreKal` / `legacy:62355` | Captured continent child sets have 23 and 20 zone references respectively, corresponding to the custom zones with the extra-zone mappings above. Full current-client parity of every zone is not established. | Pair only after all underlying zone requirements and the complete native type-8 child ID/quantity set are verified. Until then, retain separate cards and audit the unverified dependency. Matching child counts alone cannot prove equivalent requirements. |
| `custom:worldexplorer` / `legacy:62053` — Explore Azeroth | Both have two continent children; their children belong to different source definitions. | Pair only after both continent relationships and the complete native type-8 child ID/quantity set are verified. Until then, retain separate cards in **Exploration → World Exploration** and audit why parity is unverified. No redundant copy appears in the parent list. Native completion cannot grant custom completion. |
| `legacy:62382` and `legacy:64015` — Explorer | Native wrappers require having a character with Explore Azeroth. Distinct observed IDs/flags and account/character scope evidence must be preserved. | Keep the real enumerated IDs separate in World Exploration. A wrapper is not the current character's exploration record, and mirrored IDs are not substituted. |

Community captures were inspected as data from the MIT-licensed `LegacyNext`
project. The implementation does not execute or bundle those dumps. Objective
verification uses the current guarded native APIs. The main audit and live
manual tests are in the Iteration 4 project documentation.

## Category selection and classification

`Presentation.Rows` selects direct category assignments. `Presentation.Count`
maintains separately cached subtree totals. Expanding or collapsing navigation
therefore does not change a parent category's list or its selection.

- General profession series and multi-profession milestones are assigned directly
  to Professions. Primary Professions is removed. Authored skill/series metadata
  keeps Fishing, Cooking, First Aid, and the other named professions separate.
  Additional profession subjects require actual native category or authored skill
  metadata.
- Broad exalted-reputation milestones are assigned directly to Reputation.
  Alliance/Horde metadata retains its existing mapping, and individual neutral or
  Forever faction achievements remain under Other Factions.
- Dungeons & Raids, PvP, and Feats retain their subject structure. A navigation
  fallback to Other Legacy Challenges does not change an achievement's type or
  point classification. Actual unmapped native IDs remain in `model.unmappedIDs`.
- Playable class enumeration uses `C_GameRules.IsClassAllowedForGameMode` when
  readable. The ordinary class metadata enumeration and icon tables alone cannot
  establish that a class is playable. If the eligibility API is unavailable,
  actual Forever class references, the current class, and native class category
  evidence provide the fallback. Captured native class record IDs are checked
  against their expected names before mapping them out of mixed categories.
  Additional eligible classes are retained; general class rows stay on Classes.
