# Unified Wrath Legacy System — iteration 2

Target: Forever Beta 1.60.1 / build 70338 / Interface 16001 / Lua 5.1 /
project 18. Experimental, disabled by default. The actual game client
has not been used to test this implementation. Iteration 1 embedded the Wrath
browser inside native Challenges; iteration 2 replaces the complete visible
Legacy System presentation while retaining its registered native root and data.

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
The only new setting is account settings.legacyUI. Explicit custom tracking
clicks delegate to the existing ToggleTrack service.

This view uses this character's completion timestamps even with standalone
account view enabled; the existing tracking service still honors its own
account-view rules. Native scope uses the runtime account-flag constant.
Character achievement points and native Legacy Points remain separate.
Old native imports keep their saved keys/behavior in the alpha UI; the new
custom adapter excludes them to avoid duplicates and synthetic addon points.

The integration loads LegacyAdapter, CustomAdapter, Presentation, Wrath Lua
callbacks, adapted virtual XML templates, the native presentation bridge, and
LegacyController. No new libraries or original Wrath backend are required.

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

The 768 by 500 body retains its proportions. A 768 by 640 logical footprint
reserves roof/body/tab artwork and scales uniformly as the complete visible
replacement. The addon close button closes the native registered panel; its
header supports dragging. The original Blizzard AchievementFrame global is
not created or overwritten. Header totals are intentionally separated into
Character Achievement Points and Legacy Points. Summary shows separate source
counts, reliable recent custom/native completions, and unified overview bars.
Cards expand descriptions/criteria and earned custom series link to previous
tiers. Cards use one original point-shield region and hide both reward text and
reward decoration when no genuine reward exists.

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
| Unmapped Challenges | New, localized, or mixed metadata without a verified mapping; preserved and browsable |

Native subcategory ancestry is retained where it helps navigation. A parent with
its own challenges and its child categories both contributes its original records.
Mappings never enumerate fabricated challenges or choose a substitute mirrored ID.
The few record-level Adventure exceptions require both a verified ID and matching
live title; they do not classify all Adventure content as Exploration. Current
name recognition and interface labels use English, so unrecognized localized names
can appear under Unmapped Challenges rather than receive a guessed category.

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
decorative visibility. It does not recreate claim/spend controls or assign a new
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
