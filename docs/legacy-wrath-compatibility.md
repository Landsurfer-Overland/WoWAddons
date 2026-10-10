# Unified Wrath Legacy System — iteration 3

Target: Forever Beta 1.60.1 / build 70338 / Interface 16001 / Lua 5.1 /
project 18. Experimental, disabled by default. The actual game client
has not been used to test this implementation. Iteration 1 embedded the Wrath
browser inside native Challenges; iteration 2 replaced the complete visible
Legacy System presentation while retaining its registered native root and data.
Iteration 3 refines classification, subject subcategories, window layout and
statistics while preserving that foundation.

The original Wrath Lua/XML and earlier attached references remain the primary
artwork sources. The iteration 3 brief refers to four newer screenshots and a
generated mockup, but those images were not attached to this iteration's request.
No review of those missing images or pixel-for-pixel match is claimed.

## Existing project and persistence

The current core contains 322 definitions, including older native imports.
AlphaUI supplies the existing standalone interface. Data, DataQuests,
DataProfDungeons and DataExtra load before ForeverAchievements, which exports
ns.FA. Social, Tooltips, Tracker, Views, Minimap, Themes and Welcome build
on it; Diagnostics/LegacyInspector loads afterwards and remains unchanged.

Existing categories are General, Quests, Exploration, Professions, Dungeons
& Raids, Reputation, PvP and Feats of Strength. The core owns character
counters, exploration/collection sets, quests, profession/boss/reputation
checks, series, history, completion timestamps, notifications and tracking.
The standalone UI, account view, social comparison, chat links, titles,
tracker, minimap, themes, settings and diagnostic remain available.

ForeverAchievementsDB stores account settings and character snapshots.
ForeverAchievementsCharDB stores done[key] timestamps, tracked keys, history
and existing counters/sets. The new interface reads their original keys,
without migration, completion writes, deletion or native progress import.
Account settings.legacyUI controls the optional replacement. `legacyUISize`
and `legacyUIPosition` are additive, account-scoped presentation preferences; they do not
migrate character progression. Explicit custom tracking clicks delegate to the
existing ToggleTrack service.

This view uses this character's completion timestamps even with standalone
account view enabled; the existing tracking service still honors its own
account-view rules. Native scope uses the runtime account-flag constant.
Character achievement points and native Legacy Points remain separate.
Old native imports keep their saved keys/behavior in the alpha UI; the new
custom adapter excludes them to avoid duplicates and synthetic addon points.
Unsupported daily-quest definitions retain their saved keys and historical data
but are inactive in this Forever project. No daily category or replacement
daily achievement is added.

The integration loads LegacyAdapter, CustomAdapter, Presentation, Wrath Lua
callbacks, adapted virtual XML templates, the native presentation bridge, and
LegacyController. StatisticsAdapter supplies the independent Statistics model.
The existing LibStub, CallbackHandler, LibDataBroker and LibDBIcon load before
core services and remain unchanged. No new libraries or original Wrath backend
are required.

## Original UI port

All five uploads remain unchanged in References/WrathAchievementUI. Their
complete window, category, entry, criteria, summary, statistics, comparison,
filtering, localization, scrolling and tracking implementation was reviewed.

| Original component | Adaptation |
| --- | --- |
| AchievementFrame layers and Header | Actual original wood, metal, parchment, watermark, joints, roof, point border and tiny shield in FAWrathWindowTemplate |
| AchievementCategoryTemplate | Original art/label anchors with one native/custom category hierarchy |
| AchievementTemplate | Original parchment/title/glow/reward textures, icon, shield, date, highlight and plus/minus; adapter records |
| AchievementIconFrameTemplate / shield | Original borders, texture coordinates and saturation colors |
| AchievementCriteriaTemplate | Original checkmark/label with native or character criteria |
| MetaCriteriaTemplate | Original icon/check/border; read-only linked-record navigation |
| AchievementProgressBarTemplate | Original green bar, border and quantity text |
| AchievementFrameSummaryCategoryTemplate | Original overview ornamentation and two-column category bars |
| AchievementFrameTabButtonTemplate / StatTemplate | Original wooden tabs for Achievements, Legacy Rewards, Legacy Trees, Statistics; original statistics row art |
| AchievementButton_Saturate / Desaturate | Original colored/gray parchment, title slices, icon/description colors and shield slices |
| AchievementButton_Collapse / Expand / OnLoad | Original 84-pixel collapsed height, parchment/glow calculations, region bindings and date-under-shield placement |

The original 768 by 500 body remains the Compact preset. Standard is 900 by
620, and Large is 1024 by 720; each adds 140 logical pixels for roof/footer
space. The default Standard layout increases useful card/sidebar/native-pane
space. Corners and the ornate roof remain fixed-size; center backgrounds and
plain border strips resize with content. Continuous resizing is replaced by
these saved presets. Whole-window scaling is used only to fit the available
UIParent dimensions. The addon close button closes the native registered panel;
its header supports dragging with saved, clamped position and a reset command.
The original Blizzard AchievementFrame global is
not created or overwritten. Header totals are intentionally separated into
Character Achievement Points and Legacy Points. Summary shows separate source
completion bars, up to six reliable dated custom/native records in one Recent
Achievements section, then unified overview bars without repeated point headings.
Cards expand descriptions/criteria and earned custom series link to previous
tiers. Cards use one original point-shield region and hide both reward text and
reward decoration when no genuine reward exists.

## Independent classification fields

Presentation identity, source, scope, navigation, achievement type, points,
completion and rewards are separate fields. Namespaced identity remains stable
through refreshes and parent-category aggregation. Native completion/reward data
stays native; custom completion follows original character saved keys. Neither
account scope nor native source determines an achievement's type or point system.
Zero points do not imply Feat of Strength. Missing authoritative point values
remain unavailable rather than defaulting to one Legacy Point or ten custom points.

| Presentation property | Authority / semantics |
| --- | --- |
| `uniqueID`, `key` | Stable `legacy:<nativeID>` or `custom:<savedKey>`; deduplicated by identity |
| `sourceType` | `native_legacy` or `custom_character`; original `source` aliases retain existing adapter compatibility |
| `scopeType`, `scope` | Native verified flags or the existing character-specific custom storage model; unavailable metadata stays unknown |
| `category`, `subcategory` | Subject navigation; does not grant points or determine the native achievement's type |
| `achievementType` | Independent standard/feat/special classification with evidence; unavailable native metadata stays unknown |
| `pointType`, `pointValue` | Actual custom definition value or native trait-currency getter; native positive awards are Legacy, confirmed native zero awards are none with value 0, missing awards remain unknown |
| `completionState`, `completionDate` | Original saved custom completion or authoritative native completion/date, not inferred from criteria |
| `criteria`, `progress` | Read-only actual objectives/quantities; missing data is explicitly unavailable |
| `reward` | Actual description only; no generic source label or invented reward |

The point shield renderer uses actual achievement type independently of point
value. Positive Legacy awards use the original shield with a distinct blue-bronze
tint and gold number; ordinary confirmed zero awards use a neutral ordinary
shield. Only actual Feats use the original NoPoints artwork. Character and
Legacy points remain distinguishable; native Explore Azeroth
does not acquire Feat artwork merely because its point award is zero or missing.
Its displayed numeric award still requires the live trait-currency getter.
Individual custom zone achievements
retain their own valid character points; they do not inherit a native parent
meta-achievement's Legacy reward. Similar custom/native descriptions are not
grounds for merging independently earned records.

Scope is shown subtly in details/tooltips from explicit custom metadata or
verified native flags. Missing flags stay unknown. The Feats → Other Legacy
Challenges navigation fallback does not change the record's real achievement
type, scope, point value, reward or completion. Exact duplicate identities are
removed from a displayed list; separate sources, native meta milestones and
custom progression tiers remain distinct.

## Unified category mapping

Mapping changes only the view model. The native runtime catalog is still the
source of native IDs, names, ancestry, completion and reward metadata. Custom
definitions and both progression databases retain their original identifiers.

| Unified category | Recognized runtime metadata / handling |
| --- | --- |
| General | General plus custom General |
| Quests | Quest/questing metadata plus custom Quests; verified quest-specific Adventure exceptions |
| Exploration | Exploration/Explorer metadata and Eastern Kingdoms/Kalimdor under exploration or Adventure ancestry; verified exploration-specific Adventure exceptions |
| Professions | Tradeskills, named profession subcategories, plus custom Professions |
| Dungeons & Raids | Dungeons/Raids ancestry plus custom Dungeons & Raids |
| Reputation | Reputation metadata plus custom Reputation; PvP/class context takes precedence where appropriate |
| PvP | Player vs. Player/PvP ancestry plus custom PvP |
| Classes | Classes and recognized class-name metadata; applicable custom definitions if present |
| Feats of Strength | Recognized Feats metadata plus custom Feats of Strength |
| Feats of Strength → Other Legacy Challenges | New, localized, or mixed native metadata without a verified subject mapping; navigation fallback only |

Native subcategory ancestry is retained where it helps navigation. A parent with
its own challenges and its child categories both contributes its original records.
Mappings never enumerate fabricated challenges or choose a substitute mirrored ID.
The few record-level Adventure exceptions require both a verified ID and matching
live title; they do not classify all Adventure content as Exploration. Shared
subcategories are created from available content rather than filling an empty
proposed hierarchy. Main categories aggregate every relevant descendant without
duplicating records. Fishing, Cooking and First Aid have separate profession
subcategories, with primary professions organized independently. Geography and
actual profession/class/category metadata take precedence over title guesses.
Native achievement type follows the verified original `AchievementUtil`
Feats-of-Strength categories 81 and 15093, with bounded ancestry inspection;
unknown or cyclic ancestry does not prove a standard type or a Feat. No invented
native Feat flag is used. Custom Feats follow explicit type or their authored
Feats category rather than a zero-point heuristic. Scope separately uses the
validated runtime `ACHIEVEMENT_FLAGS_ACCOUNT` bit, without deriving it from source.

Current name recognition and interface labels use English, so unrecognized
localized names remain in Other Legacy Challenges rather than receive a guessed
subject category. There is no standalone Unmapped Challenges navigation root.

The view model retains unknown mappings as `model.unmapped`, recording ID, name,
original category and reason for later classification work. The original native
challenge ID is retained even when its displayed navigation location changes.
`/fa legacyui unmapped` reports the current observed list in chat, bounded to 30
entries with a truncation notice; it does not enumerate unavailable native data.
The full current list remains in the view model. See the
[classification/overlap audit](iteration3-achievement-audit.md) for static records
and unresolved relationships.

Native and custom rows share the same card renderer but keep `legacy:<id>` and
`custom:<original-key>` identifiers and distinct point-system tooltips. Unknown
completion, partial catalogs, missing points, and missing dates remain explicit.

Unsupported original dependencies are adapted:

- Global AchievementFrame/selection and UI panel registration become
  addon-owned callbacks/state. Original secure/load-on-demand TOC is excluded.
- HybridScrollFrame becomes UIPanelScrollFrameTemplate with visible-card
  pooling; its standard scrollbar scripts remain intact.
- TooltipBorderBackdropTemplate/gold-border mixin dependencies become
  BackdropTemplate with local colors; original body/card art is retained.
- Achievement font objects become namespaced standard-game-font equivalents:
  12-pixel criteria/description/date, 20-pixel points, gold dates.
  Alignment-only font styles use standard font objects and explicit alignment.
- The supplied fork's WowStyle1FilterDropdownTemplate/SetupMenu is replaced
  by a cycling original-category-art filter button. Search and filters are local.
- Original native tracking/completion setters, comparison queries, WatchFrame,
  progressive-chain getters, backend event handlers and localization setup
  entry points are not run. Existing alpha social comparison remains available.

The alpha interface was modern-looking and had no reusable original Wrath
template port. Its appearance and functionality stay independent.

## Native evidence and API contracts

Later user snapshots supersede the older task statement that records had
not been enumerated. They establish LegacySystemFrame, ChallengesPage,
CategoryList, DetailPane.ScrollBox, provider changes and concrete records.
RewardTrackPage.majorFactionData showed faction 2802, Legacy Track,
renownLevel 16 and maxLevel 90. This does not establish claim state.

Native selected examples were Alchemy 15587 / Expert Alchemist 62013,
Exploration 15607 / Explore Azeroth 62053, and Adventure 15596 / Explorer
62382. Expert Alchemist returned achievement points 0, incomplete, reward
"Earn 1 Legacy Point.", and criterion 225 Alchemy Skill: current 0, required
225, asset 2937, criteria ID 111540. Explore Azeroth has two criteria;
Eastern Kingdoms is type 8 and references achievement 62353. Mirrored
Explorer 64015 has different flags from native-selected 62382; no static
alias is chosen.

| Read-only getter | Purpose |
| --- | --- |
| GetCategoryList() / GetCategoryInfo(id) | Runtime category IDs, names, parent IDs (-1 is a root), flags |
| GetCategoryNumAchievements(id) | Walk 1..total, retaining parent-owned records and descendants |
| GetAchievementInfo(categoryID,index) / GetAchievementInfo(id) | Identity, name, authoritative completion/date, description, flags, icon and reward text |
| GetAchievementNumCriteria(id) / GetAchievementCriteriaInfo(id,index) | Actual criteria completion, current/required quantities, asset IDs and criteria IDs |
| C_Traits.GetTraitCurrencyForAchievement(currencyID,achievementID) | Documented actual Legacy point award |
| C_MajorFactions.GetCurrentRenownLevel(factionID) | Native account Legacy Points as renown |
| ScrollBox:GetDataProvider() / provider:GetCollection() | Read-only current-category fallback; passive dataProvider/collection fields also supported |

Runtime LegacyConsts IDs are preferred; documented currency 4225 and observed
faction 2802 are fallbacks. Achievement-info points are never repurposed as
Legacy Points. Missing getters display "?" or "Unavailable"; reward text is
never parsed into points. Renown is the native account total, distinct from
spent/unspent points and sums of mirrored records.

Native completion always comes from GetAchievementInfo, never criteria
counts/quantities. Zero criteria differ from unavailable criteria. Unknown
completion stays unknown and is excluded from Complete/Incomplete filters.
Actual numeric criteria drive bars; omissions are labeled. Keys are
legacy:<id> and custom:<original-key>.

Full category APIs are preferred. A provider fallback supplies IDs whose
metadata is queried read-only; its partial status is visible. Providers are
re-read rather than retained across category changes. Bounds are 256
categories, 2500 records and 256 criteria per card; limits produce notices.

Observed GenerateDataProvider, SelectChallenge, UpdateCategoryList,
RefreshChallenges, SelectCategory and UpdateChallenge methods are never called:
the inspector did not establish their signatures/side effects. Presence of
C_AchievementInfo does not imply an API contract; C_Legacy is not required.

GetMajorFactionData, GetRenownLevels and GetRenownRewardsForLevel were also
investigated. Threshold arrays may be sparse and collection flags do not
prove claims. Iteration 2 displays the original Rewards and Tree pages and
retains their original claim/progression behavior. No independently calculated
reward-claim state or native talent-spending implementation is added.

The latest public Blizzard source was checked directly at
[943764493e6b16d63ded3ab304150d1f05e58b57](https://github.com/Gethe/wow-ui-source/tree/943764493e6b16d63ded3ab304150d1f05e58b57),
whose version.txt reports build 1.60.1.70338. It verifies root.Pages as
RewardTrackPage (1), ChallengesPage (2), TreePage (3), and
`EventRegistry:TriggerEvent("Legacy.SelectPage", id)` as the native selection
entry point. Page OnShow calls the original parent's SetTitle; tree gamepad
logic additionally relies on that native ancestry. The integration therefore
keeps the original parents and page handlers. Full citations and input-mode
ordering are in [iteration2-native-research.md](iteration2-native-research.md).

## Community research and licensing

All resources were reachable and inspected on 2026-10-10 at these revisions.
Only API/integration facts were used; no implementation was copied, translated
or vendored from GPL/proprietary projects.

| Resource | Revision / license | Findings |
| --- | --- | --- |
| [LegacyNext](https://github.com/lxhwes/LegacyNext) | f6bba488215a06d0c0d26899a4399269878ee5b0 / MIT | docs/legacy-internals.md: runtime catalog, completed-first order, account flag, trait currency, renown, sparse thresholds and page lifecycle |
| [Legacy Forever](https://github.com/cjber/legacy-forever) | 57da66d4ddcdd9d3ccfaa84c06a85f3d7fff19a0 / GPL-3.0 | Native IDs, criteria and tracking/extraction API facts; no source copied |
| [ClassicUI Forever](https://github.com/wowaddonmaker/classicuiforever) | d9f25cf9af939d418e763e70b50c02f576164269 / proprietary | Replacement lifecycle/native integration concerns; no source copied |
| [Forever API docs](https://github.com/Atraeau/WoW-Addons) ([site](https://atraeau.github.io/WoW-Addons/)) | d8c9be3635e756fd90284e02b5a800c796b337a0 | Standard category/achievement contracts; docs/api/Spells-Auras-Talents/C_Traits.md and Achievements-Progression/C_MajorFactions.md |

Community live/source evidence includes earlier 1.60.1 builds. The current
root/page contracts were checked directly against the exact 70338 public
source, but source review does not prove in-game rendering or interaction.
Supplied live evidence, documented contracts and guarded calls are used together.

## Reversibility and limits

### Quest tracking and deferred work

No full Questie/Loremaster integration is introduced. Existing quest helpers
prefer the native completed-quest statistic and guarded completed-ID getters:
`C_QuestLog.GetAllCompletedQuestIDs`, then `GetQuestsCompleted` where available.
Existing Loremaster counting recognizes the optional `QuestDB.Exists` and
`QuestDB.Get(id, "zoneOrSort")` contract and the authored continent-area lists.
Missing or failing completion/database data must remain unavailable rather than
become a fabricated zero or completed Loremaster achievement. This narrow
optional contract is not proof that an arbitrary Questie version is compatible.
The standalone card/sort paths, tracker, and social tooltips also guard unavailable
quest/Loremaster progress and leave its progress bar empty. A confirmed zero is
still a known value. Retained daily tracked keys are hidden without deleting history.

Future integration needs a Forever-compatible licensed quest database, reliable
completed-ID coverage, zone/faction mapping, and agreement on which quests count
toward each authored requirement. Existing quest keys, history, and currently
working checks remain intact. Historical daily keys are retained but disabled;
daily completion checks/categories are not added. Complex multi-stage money
chains are preserved for later work rather than redesigned here.

### Statistics authority

`Integrations/StatisticsAdapter.lua` supplies an independent Statistics hierarchy
and does not reuse the achievement category selection. Populated categories
cover Character, Combat, Quests, Exploration, Professions, Dungeons & Raids, PvP,
and Miscellaneous; Character, Combat and secondary professions have relevant
subcategories. Parent selection aggregates each stable statistic identity once.
Definitions alone do not establish that the client can return a valid value.

Native rows call guarded `GetStatistic(id)` and preserve actual formatted text,
including genuine `0`, grouped values, names and coin textures. Missing getters,
exceptions, secret values and placeholder results display `Unavailable`.
Local rows read original character counters/collections without adding defaults:
an initialized empty collection confirms zero recorded observations, while an
absent counter remains unavailable. These observations reflect addon tracking
since installation, not a reconstructed lifetime total. Exploration is labeled
as recorded areas, not a claim of full historical zone completion.

The unified Statistics view omits unsupported daily statistics (97, 1525, 1526)
and Dalaran Cooking Awards (1976), while preserving historical `ns.STATS` data
and standalone behavior. Average quests per day is an ordinary statistic and
does not imply that daily quests exist. No account histories or statistic values
are merged or migrated.

### Saved layout and local search

`legacyUISize` records Compact, Standard or Large; absent/invalid preferences
use Standard. `legacyUIPosition` contains `point`, `relativePoint`, `x` and `y`
relative to UIParent. The controller validates values, fits the complete window
to the current screen and clamps restored positions. `/fa legacyui reset`
clears only that presentation preference; `/fa legacyui size ...` never changes
achievement tracking or native progression. Size commands issued in combat
save the preference and wait for safe layout work.

Achievement and Statistics sidebar selections, expansion and scroll state are
independent runtime navigation preferences. Search uses title, description and
available category metadata plus already-loaded criterion text. It performs no
native criterion queries on each keystroke and does not pretend to search every
unloaded objective. The loaded-criteria index is bounded to 64 names of 256
characters. The clear control resets the query and filter; completion/source
filters are selected one at a time and respect the current subject category.

### Native presentation restoration

Disabled by default, the account option is controlled by `/fa legacyui on`
and `/fa legacyui off`. The native registered root remains intact and owns
normal open/close and panel lifecycle. The addon temporarily hides its original
regions and immediate presentation children, disables its invisible mouse
rectangle, and displays the complete Wrath artwork at the replacement's own
proportions. These presentation states are recorded for restoration. Native
root alpha, functions, scripts, providers and progression collections remain
unchanged; this supersedes iteration 1's narrower Challenges-only cover.

Rewards and Trees mount their actual existing native page into the Wrath body
using temporary cross-parent anchors, preserving each original parent and every
descendant. Original native selection events drive those pages; their original
callbacks own points, rewards, talent editing and progression. The bridge
records/restores page anchors, dimensions, scale, strata, frame level and known
decorative visibility. Iteration 3 preserves original Rewards/Tree backgrounds
and the native tree divider inside the shared Wrath frame; only native root
presentation is suppressed. This supersedes iteration 2's inner-background
suppression. It does not recreate claim/spend controls or assign a new
page parent. The native panel's original width reservation remains unchanged to
preserve relationships with other panels, even though the visible artwork is
smaller. Rewards/Trees selection must preserve native access if mounting fails.

Append-only root hooks and native selection callbacks observe normal lifecycle
and coordinate external selection with addon tabs without replacing original scripts. Hooks
cannot be removed through a standard WoW API; their inactive paths remain gated
when the feature is disabled. A reload while disabled starts without native hooks.

Combat defers unsafe initialization and restoration. Disabling records the option
immediately; necessary presentation restoration can remain pending until combat
ends. Runtime protected/forbidden checks supplement source contracts. Missing
frames wait for native loading; incompatible objects and rendering errors restore
native access. No force-load, native search setter, global function replacement,
transmission, CVar write, completion grant, trait purchase or reward claim is added.
Drag-stop and saved-position cleanup errors cannot prevent an attempted native
restoration or clearing the controller's busy state. Bridge restoration failures
remain pending for a later legal retry.

Gamepad mode uses the original native presentation. Its SmartNavigation maps the
original three pages and original challenge controls, so the addon does not claim
untested four-tab gamepad support. InputUtil's high-priority transition subscriber
restores native geometry/presentation before ordinary native gamepad setup; return
to mouse and keyboard schedules reattachment after normal transition handling.
Settings and current mode gate those persistent callbacks.

Native events invalidate metadata; visible updates are coalesced. Existing
custom checking/earning hooks refresh character data. Complete native catalogs
are cached between native events/reopening; criteria are read on expansion.
No polling ticker is added.

Tests run actual adapter/controller Lua and template OnLoad callbacks with
explicit UI doubles. They verify data separation, unified mapping, retained
saves/scripts/parents, commands/persistence, restoration and mode/combat fallback,
points/criteria, reliable native summaries, meta links, visible-card scrolling,
four-tab order, reward/shield rendering contracts, XML, original assets and hashes.
They cannot establish texture availability, pixel fidelity, native timing,
combat taint or SavedVariables disk writes. Own labels currently use English;
native text follows client localization. Native tracking/comparison setters
are excluded; the standalone alpha features remain.

Use the [manual plan](../ForeverAchievements/Integrations/README.md) for normal
opening/closing/dragging, all four tabs, mixed categories, search/filtering,
criteria, native reward/tree interactions, UI scale, input transitions, reloads,
character saves and complete restoration after disabling.
