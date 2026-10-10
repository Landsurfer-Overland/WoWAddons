# Iteration 3 achievement data audit

This audit inspects the actual addon definitions and the available native-client
source and reports. It is not a new in-game inspection. Runtime reward amounts,
account flags, completion dates, and the complete native catalog must still come
from the client rather than screenshots or this document.

## Definition and persistence inventory

An isolated Lua 5.1 load of the real AlphaUI/data/core files found **322
definitions and 322 distinct saved keys**. There were no exact duplicate core
definitions. The inventory consists of **263 custom definitions** and **59 older
native imports**. These are definition counts before faction, optional-addon,
and unsupported-content filtering; they are not a player's completion totals.

The custom definitions preserve these authored point values:

| Character points | Number of definitions |
| --- | ---: |
| 0 | 13 |
| 10 | 235 |
| 15 | 2 |
| 20 | 6 |
| 25 | 4 |
| 50 | 3 |

The 13 zero-point custom records are authored in the Feats of Strength category.
The adapter classifies them using that authored category, not their zero value.
A standard custom record with zero points would remain standard and use the
character point system. No blanket ten-point or one-point default is introduced.

`ForeverAchievementsCharDB.done[originalKey]` remains the character's completion
timestamp source. Its tracked keys, explored subzones, boss records, counters,
daily history, and all other existing progression fields are retained.
`ForeverAchievementsDB.chars` remains a separate account snapshot collection.
Both browsers read valid current-character `done` timestamps. The standalone
account-union toggle has been removed while its stored preference and old histories
remain preserved. Its account overview lists verified character snapshots and labels
unreliable totals `Unavailable`; malformed timestamps do not appear as earned recent
records. Account snapshots never grant the current character completion.
The addendum records new account snapshots with verified character identity, including
Forever surname/realm handling, while retaining older snapshot keys. Ambiguous older
snapshots do not supply a confident other-character indicator.

The 59 old `native=true` imports retain their definitions and saved keys in the
core. The unified custom adapter excludes them, and the native adapter reads
actual native catalog records instead. This prevents an additional synthetic
ten-character-point presentation of an already native challenge. It does not
delete historical imported completion or select a substitute mirrored native ID.

## Independent presentation properties

| Field | Custom records | Native records |
| --- | --- | --- |
| `uniqueID` / `key` | `custom:<original saved key>` | `legacy:<actual API ID>` |
| `sourceType` | `custom_character` | `native_legacy` |
| `source` compatibility alias | `custom` | `legacy` |
| `scopeType` | `character`, from the existing per-character tracker | `character`, `account`, or `unknown`, from readable flags and the runtime account-mask constant |
| `scope` compatibility label | `Character` | `Character`, `Account`, or `Scope unavailable` |
| `achievementType` | Explicit supported authored type, otherwise authored category | Actual native Feats category ancestry, otherwise standard only when ancestry is known; unknown if unavailable/cyclic |
| `pointType` | `character`, or `none` for an authored zero-point Feat; `unknown` if its value is unavailable | `legacy` for a positive readable trait-currency award, `none` for a confirmed zero award, `unknown` if unavailable |
| `pointValue` / `points` / `pts` | Original authored `a.pts` | Exact `C_Traits.GetTraitCurrencyForAchievement` return value |
| `completionState` | `complete`, `incomplete`, or `unknown` for malformed/unreadable saved data | `complete`, `incomplete`, or `unknown`, from `GetAchievementInfo` |
| `completionDate` / `date` | Readable original timestamp formatted for presentation | Valid completed month/day/year, validated for leap years and calendar days |
| `completionScope` / `completionDetail` | Current character, reliably recorded other character, incomplete, or unknown; snapshot detail never changes current completion | Current character, other character, native account completion, incomplete, or unknown, from independent native evidence |
| `progress` / `criteria` | Existing progress evaluators and criteria, with unavailable values left unavailable | Read-only criteria loaded for expansion; never used to grant completion |
| `reward` | Explicit reward text only | Actual native reward text only |

Numeric native achievement points returned in the third `GetAchievementInfo`
slot are retained as `nativeAchievementPoints` for evidence. They are not Legacy
currency and never replace a missing trait-currency getter. Reward text is not
parsed to manufacture a numeric award. Header Legacy Points use authoritative
renown rather than summing possibly mirrored challenge rewards or treating
available talent currency as the account total.

A confirmed zero native award retains numeric zero but uses `pointType = none`.
It does not advertise Legacy Points for an individual zone or another milestone
that awards no native currency. This does not make the record a Feat: ordinary
zero-award native records keep ordinary shield artwork and a no-point-award
tooltip. A missing getter remains unknown and is not treated as zero.

Unknown custom point values or completion states also make the affected earned
aggregate unavailable rather than silently reporting a smaller fabricated total. Existing real custom
definitions all have numeric authored points.

The exact build 70338 source's `Blizzard_FrameXMLUtil/AchievementUtil.lua`
identifies native Feats of Strength through categories **81** and **15093** and
their ancestors. The adapter checks this native contract with visited-category
tracking and a maximum depth of 32. It does not invoke an unbounded recursive
helper. Account flags, zero values, Legacy provenance, an unfamiliar title, and
the navigation fallback under Feats are not Feat classifications. Unknown types
receive ordinary artwork rather than speculative Feat artwork.

The criteria adapter also respects the native return positions: character name
is slot six and criteria flags are slot seven. Achievement-link criteria use
type 8 and the actual slot-eight asset ID.

## Exploration records and relationships

There are **44 individual custom zone achievements**: 23 Eastern Kingdoms, 20
Kalimdor, and one Zephras Isle. Each retains **10 character achievement points**.
Their underlying custom progress now requires verified map identity and genuinely
revealed world-map overlay evidence. Historical visit sets remain saved but do not
grant missing completions merely from zone/subzone presence. They do not independently
award Legacy Points.

| Region | Saved key | Data/reference ID | Achievement |
| --- | --- | --- | --- |
| Eastern Kingdoms | `explore776` | 776 | Explore Elwynn Forest |
| Eastern Kingdoms | `explore627` | 627 | Explore Dun Morogh |
| Eastern Kingdoms | `explore768` | 768 | Explore Tirisfal Glades |
| Eastern Kingdoms | `explore779` | 779 | Explore Loch Modan |
| Eastern Kingdoms | `explore802` | 802 | Explore Westfall |
| Eastern Kingdoms | `explore841` | 841 | Explore Wetlands |
| Eastern Kingdoms | `explore769` | 769 | Explore Silverpine Forest |
| Eastern Kingdoms | `explore780` | 780 | Explore Redridge Mountains |
| Eastern Kingdoms | `explore778` | 778 | Explore Duskwood |
| Eastern Kingdoms | `explore772` | 772 | Explore Hillsbrad Foothills |
| Eastern Kingdoms | `explore782` | 782 | Explore Swamp of Sorrows |
| Eastern Kingdoms | `explore765` | 765 | Explore Badlands |
| Eastern Kingdoms | `explore781` | 781 | Explore Stranglethorn Vale |
| Eastern Kingdoms | `explore760` | 760 | Explore Alterac Mountains |
| Eastern Kingdoms | `explore761` | 761 | Explore Arathi Highlands |
| Eastern Kingdoms | `explore773` | 773 | Explore The Hinterlands |
| Eastern Kingdoms | `explore774` | 774 | Explore Searing Gorge |
| Eastern Kingdoms | `explore766` | 766 | Explore Blasted Lands |
| Eastern Kingdoms | `explore775` | 775 | Explore Burning Steppes |
| Eastern Kingdoms | `explore777` | 777 | Explore Deadwind Pass |
| Eastern Kingdoms | `explore770` | 770 | Explore Western Plaguelands |
| Eastern Kingdoms | `explore771` | 771 | Explore Eastern Plaguelands |
| Eastern Kingdoms | `exploreRiverglades` | No numeric achievement ID authored | Explore Riverglades |
| Kalimdor | `explore728` | 728 | Explore Durotar |
| Kalimdor | `explore736` | 736 | Explore Mulgore |
| Kalimdor | `explore842` | 842 | Explore Teldrassil |
| Kalimdor | `explore750` | 750 | Explore The Barrens |
| Kalimdor | `explore844` | 844 | Explore Darkshore |
| Kalimdor | `explore845` | 845 | Explore Ashenvale |
| Kalimdor | `explore846` | 846 | Explore Thousand Needles |
| Kalimdor | `explore847` | 847 | Explore Stonetalon Mountains |
| Kalimdor | `explore848` | 848 | Explore Desolace |
| Kalimdor | `explore850` | 850 | Explore Dustwallow Marsh |
| Kalimdor | `explore849` | 849 | Explore Feralas |
| Kalimdor | `explore851` | 851 | Explore Tanaris Desert |
| Kalimdor | `explore852` | 852 | Explore Azshara |
| Kalimdor | `explore853` | 853 | Explore Felwood |
| Kalimdor | `explore854` | 854 | Explore Un'Goro Crater |
| Kalimdor | `explore855` | 855 | Explore Moonglade |
| Kalimdor | `explore856` | 856 | Explore Silithus |
| Kalimdor | `explore857` | 857 | Explore Winterspring |
| Kalimdor | `exploreShendralas` | No numeric achievement ID authored | Explore Shen'dralas |
| Kalimdor | `exploreHyjal` | No numeric achievement ID authored | Explore Mount Hyjal |
| Zephras Isle | `exploreZephras` | No numeric achievement ID authored | Explore Zephras Isle |

These numeric IDs are definition/reference metadata, not a claim that each
custom zone is an independent native Legacy award. Stable custom identity is the
saved key, so a similarly numbered native record cannot overwrite it.

| Custom meta | Reference ID | Character points | Existing children |
| --- | ---: | ---: | --- |
| `custom:exploreEK` | 42 | 25 | The 23 custom Eastern Kingdoms zones |
| `custom:exploreKal` | 43 | 25 | The 20 custom Kalimdor zones |
| `custom:worldexplorer` | 46 | 50 | `custom:exploreEK`, `custom:exploreKal` |

Zephras Isle is a separate zone and is not added to the two-continent world meta.
These relationships retain the existing definitions and separate native/custom
achievements. The addendum accepts a meta child only through a finite positive
current-character completion timestamp. Malformed child history stays saved and
unknown; it cannot establish a missing parent completion through truthiness.

Available native evidence establishes these distinct records:

| Native record | Evidence and handling |
| --- | --- |
| `legacy:62053` — Explore Azeroth | Selected-category provider 15607 includes this ID. Its native criteria link Eastern Kingdoms 62353 and Kalimdor 62355. Map to World Exploration. Its actual Legacy point value is the live trait-currency result; zero is valid and does not imply a Feat. |
| `legacy:62353` — Explore Eastern Kingdoms | Selected provider 15607 includes this ID. Native continent/meta criteria are independent of the custom saved-zone sets. Map to Eastern Kingdoms. |
| `legacy:62355` — Explore Kalimdor | Selected provider 15607 includes this ID. Map to Kalimdor and retain native progress. |
| `legacy:62382` — Explorer | Selected Adventure provider 15596 includes this wrapper. It remains distinct from custom World Explorer and native Explore Azeroth. “Have a character” in dataset wording does not establish account scope. |
| 64015 — mirrored Explorer ID | Appears in the alpha's static candidate ID list and has different observed flags from 62382. Do not substitute it for the actual native-selected ID or collapse both IDs without stronger evidence. |

The in-game screenshot's apparent award is not an authoritative replacement for
the getter. The automated zero-award fixture verifies preservation of an API
return of zero; it does not claim that the real client currently returns zero
for every Explorer record.

## Cross-character false-unlock audit

The alternate-character report identifies unexpected completions for `pet1` and
`explore855`, and retains the earlier `fall` report. No diagnostic trace from those
particular awards is available. The following are demonstrated unsafe source paths;
they are not a claim that a specific historical incident has been reproduced in-game.

| Record | Previous condition and verified risk | Corrected evidence policy |
| --- | --- | --- |
| `pet1` — Can I Keep Him?; reference ID 1017; 10 character points | `PetCount` took the maximum of journal ownership, legacy companion counts, and bag items, then permanently copied it into per-character `petsBest`. The pinned collection UI exposes ownership totals without an earning-character identity; those totals and old maxima cannot prove this character obtained a pet. | Count distinct companion items positively observed in this character's bags (Miscellaneous class 15, Companion Pets subclass 2) and new character-scoped observed-item evidence. Ignore journal totals, unproven companion-count scope, and the old cached maximum as grant evidence. Keep original completed records and saved values. |
| `mount10` — Stable Keeper; reference ID 2141; 10 character points | Adjacent audit found the same journal/legacy-count promotion into `mountsBest`; this was not one of the user's reported false awards. | Apply the same current-character observed-item policy to Mount subclass 5. Preserve old maxima and completed records without using unproven account collection counts to grant this character completion. |
| `explore855` — Explore Moonglade; 10 character points | The authored Wrath dataset has one criterion named `Moonglade`, UI map 1450, and overlay pixel offset (244, 89). The old overlay reader counted matching textures even when `isShownByMouseOver` marked them as hover previews. It also accepted saved subzone visits as completion evidence. | Verify runtime map name/ID, readable actual overlay dimensions/offsets, and `isShownByMouseOver == false`. Only revealed overlay evidence can establish a missing completion. Retain old visit history without promoting it. Invalidate/recheck on `MAP_EXPLORATION_UPDATED`. |
| `fall` — Going Down?; reference ID 964; 10 character points | An `IsFalling` interval of at least 2.6 seconds followed by an alive check substituted elapsed time for the authored 65-yard requirement. There was no measured vertical distance or guarded continuous landing/world state. | Require a measured vertical drop of at least 65 yards from grounded state through one continuous fall and landing in the same instance, with readable state and survival after landing. Flight, taxi, swimming, death, loading/world transitions, or unknown evidence cannot establish completion. |

The build 70338 `MapExplorationDocumentation.lua` declares the overlay's
`isShownByMouseOver` flag and `MAP_EXPLORATION_UPDATED` event. Its actual
`MapExplorationDataProvider.lua` hides those flagged textures and reveals them on
mouseover, confirming why preview art cannot prove earned exploration. The custom
Moonglade UI map/offset were authored from Wrath build 3.4.3.58936; they still require
runtime Forever validation. A validated dynamic map fallback retains its actual map ID,
zone name, positive overlay dimensions, and readable nonnegative offsets as evidence, rather than importing
historical proximity flags. The MIT LegacyNext captured Explore Kalimdor fixture
independently lists Moonglade as type-8 achievement criterion asset ID 855, but does
not establish its scope or a current player's completion.

`SavedVariablesPerCharacter` already isolates `CharDB.done`; the old standalone
`accountView` used an account union for display rather than writing that union into
the character database. Separately, the old Social snapshot key omitted surname
and could collide for characters sharing a first name and realm. Build 70338's
Camelot `NameUtil.lua` confirms surname is part of character identity. New snapshots
prefer verified GUID plus realm, with guarded full-name/surname/realm fallback.
Older ambiguous entries remain preserved and untrusted for elsewhere attribution.
Unexpected collisions in the new canonical snapshot namespace are archived in
`ForeverAchievementsDB.characterSnapshotArchives` before replacement. New snapshot
point/count availability is explicit when malformed history prevents a reliable total.

Current-character completion, completion reliably recorded on another character,
native account completion, incomplete progress, and unknown provenance are separate
`completionScope` states (`current_character`, `other_character`, `native_account`,
`incomplete`, `unknown`). `completionDetail` supplies the displayed explanation.
Native `GetAchievementInfo` slot 13 (`wasEarnedByMe`) is explicitly
used by the pinned native Legacy detail pane. Its readable value can distinguish
native character accomplishment from a shared completion; missing values do not
identify an earning character. These details never write custom completion, merge
dates, or inflate current-character custom point totals.

No correction automatically revokes a completion. `/fa progressdebug on|off|status|dump`
controls diagnostics, disabled by default; enablement persists across reloads while
the 64-record ring is session-only. `/fa inspectachievement KEY` reports
the current character, triggering/evaluated evidence, and saved condition state.
Inspection does not grant completion.
`/fa correctachievement KEY` previews a narrowly scoped correction. Its
`KEY confirm TOKEN` form requires explicit confirmation within 60 seconds, verified
current-character identity, and the unchanged original timestamp. It archives only
that key's old completion timestamp and identity in `CharDB.correctionHistory`, clears
only `done[key]`, and adds a `completionCorrections[key]` reaward hold. Source evidence,
all history, other keys, and native Legacy state remain untouched. `KEY resume`, then
`KEY resume confirm TOKEN`, separately confirms removal of only that hold; the next
normal verified check may award the key again. Native imports are rejected, and the
older `/fach reset` no longer performs an unconfirmed bulk wipe. Preserved historical
completions therefore require player review if they may have been falsely awarded.

## Exact duplicates, overlaps, and deferred chains

| Case | Classification | Result |
| --- | --- | --- |
| 322 core saved keys | No confirmed exact duplicates | Preserve every definition and key. |
| Same custom saved key repeated in multiple sections | Exact presentation duplicate if encountered | Custom catalog's seen-key guard retains one row and one point contribution. |
| Same actual native achievement ID encountered in multiple categories | Exact presentation duplicate if encountered | Native catalog's seen-key guard retains one row; `duplicates` and `duplicateIDs` record skipped occurrences for investigation. |
| Unified parent/child aggregation, repeated refresh, and search | Potential duplicate paths | View model uses stable namespaced keys and displays one occurrence per underlying record. |
| Old native imports versus the new native catalog | Redundant view of the native system | Keep imported saved definitions/history; omit their synthetic custom rows from the unified browser. |
| Custom zone → custom continent → custom world | Distinct achievements and meta relationships | Keep all levels and original point values. |
| Native continent/world and Adventure Explorer wrapper | Distinct IDs and progression relationships | Retain separately and use each native record's actual scope/reward/completion. |
| Custom versus native continent/world exploration | Similar activity, independent completion stores | Keep both; no shared completion or combined point value. |
| General profession rank versus native profession-specific rank | Related accomplishments with different criteria/scope | Keep each in its subject category; do not merge by title or required rank. |
| Custom dungeon completions versus native Spelunker stages | Individual achievements versus native stage/meta | Keep existing dungeon and Spelunker records. |
| `gold100`, `gold1000`, `gold5000` | Three stages titled Got My Mind On My Money | Keep the authored chain, saved keys, and values. Richer chain presentation is deferred. |
| Native class progression versus custom level tiers | Class-specific native versus generic character progression | Keep both, with their real categories and scope. |

The money series is the only repeated title in the real core inventory. Repeated
titles alone are not evidence of exact duplicates. Distinct IDs with similar
descriptions are not automatically merged or treated as aliases.

## Unmapped native records

The navigation fallback is **Feats of Strength → Other Legacy Challenges**,
internally `feats:other-legacy`. It does not change an entry's `achievementType`,
`pointType`, numeric value, scope, reward, or completion.

Each current presentation model exposes `unmappedIDs` containing actual native
IDs, plus `unmappedRecords` / `unmapped` records with `id`, `key`, `name`,
`nativeCategory`, and `reason`. A fresh catalog replaces this audit snapshot; no
unmapped ID list is persisted into the player's progression database.

The supplied Adventure snapshot also includes **64283** in category 15596, but
that provider-only excerpt does not establish its title, reward, or subject.
If stronger live category/record metadata does not classify it, it belongs in
the fallback until investigated. New or localized categories may similarly
require mapping. The complete current native catalog and a confirmed complete
unmapped-ID list have not been captured in this cloud environment.

## Quest and daily limitations

Forever daily quests are unsupported for this project. The old five daily-count
definitions (`d5`, `d50`, `d200`, `d500`, `d1000`) and `request` remain in the
322-definition inventory solely to preserve their original keys/history.
They are marked unsupported and excluded from available achievements, counters,
search, navigation, and completion checks. Daily sampling no longer runs on
login or quest turn-in. Existing `dailyDays` and `dailyLast` saved data are not
reset. No daily category or new daily achievement is introduced.

Working quest counts continue using native statistic 98 and available completed
quest IDs. A native zero remains zero; missing completed-ID/statistic APIs leave
progress unavailable rather than inventing zero. Storyline checks retain their
existing quest IDs and supported native completion flags.

Loremaster currently needs a compatible `QuestDB` exposing `Exists` and `Get`
with `zoneOrSort`, plus readable completed quest IDs. Missing or failing
prerequisites leave continent Loremaster counts unavailable. The old area lists
and faction-specific thresholds do not prove coverage of every Forever quest.
Even when the available database produces a count, its completeness and custom
Forever quest coverage still require validation. The addon does not import
Questie code, claim full Loremaster coverage, or create a new database adapter in
this iteration. A future adapter needs version/license review, Forever quest
IDs and zone classification, complete character quest history, and explicit
coverage reporting before a count can be described as complete.

## Validation and remaining checks

`tests/test_iteration3_achievement_classification.py` executes both API-double
classification scenarios and the actual core initialization under Lua 5.1. It
checks independent source/scope/type/points, zero versus unavailable awards,
native category ancestry bounds, exact criteria return positions, unknown
completion, 322 distinct saved keys, original point distributions, character
history isolation, and real zone/meta metadata. The tests use controlled values
and are separate from in-game rendering or server validation.

The [manual plan](../ForeverAchievements/Integrations/README.md) covers actual
Explorer values, individual-zone character shields, genuine Feat artwork,
scope tooltips, subject hierarchy, unmapped IDs, completion dates, category
aggregation, and native progression preservation. No new live client results
are asserted here.

Source contracts and prior observations are detailed in
[iteration2-native-research.md](iteration2-native-research.md) and
[legacy-wrath-compatibility.md](legacy-wrath-compatibility.md). The pinned native
reference is [Gethe/wow-ui-source build 70338](https://github.com/Gethe/wow-ui-source/tree/943764493e6b16d63ded3ab304150d1f05e58b57).
Only API contracts were used; no third-party progression implementation was
copied into the adapters.
