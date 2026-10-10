# Wrath UI inside Forever Legacy Challenges

Target: Forever Beta 1.60.1 / build 70338 / Interface 16001 / Lua 5.1 /
project 18. Experimental, disabled by default. The actual game client
has not been used to test this implementation.

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

The TOC appends LegacyAdapter, CustomAdapter, Presentation, Wrath Lua
callbacks, adapted virtual XML templates, and LegacyController. No new
libraries or original Wrath backend are required.

## Original UI port

All five uploads remain unchanged in References/WrathAchievementUI. Their
complete window, category, entry, criteria, summary, statistics, comparison,
filtering, localization, scrolling and tracking implementation was reviewed.

| Original component | Adaptation |
| --- | --- |
| AchievementFrame layers and Header | Actual original wood, metal, parchment, watermark, joints, roof, point border and tiny shield in FAWrathWindowTemplate |
| AchievementCategoryTemplate | Original art/label anchors with local hierarchy and source navigation |
| AchievementTemplate | Original parchment/title/glow/reward textures, icon, shield, date, highlight and plus/minus; adapter records |
| AchievementIconFrameTemplate / shield | Original borders, texture coordinates and saturation colors |
| AchievementCriteriaTemplate | Original checkmark/label with native or character criteria |
| MetaCriteriaTemplate | Original icon/check/border; read-only linked-record navigation |
| AchievementProgressBarTemplate | Original green bar, border and quantity text |
| AchievementFrameSummaryCategoryTemplate | Original overview ornamentation and two-column category bars |
| AchievementFrameTabButtonTemplate / StatTemplate | Original wooden Achievements/Statistics tabs and statistics row art |
| AchievementButton_Saturate / Desaturate | Original colored/gray parchment, title slices, icon/description colors and shield slices |
| AchievementButton_Collapse / Expand / OnLoad | Original 84-pixel collapsed height, parchment/glow calculations, region bindings and date-under-shield placement |

The 768 by 500 body retains its proportions. A 768 by 640 logical footprint
reserves roof/body/tab artwork and scales uniformly inside ChallengesPage.
The original global window and close button are omitted; Forever owns
opening/closing and its native tabs. The Summary shows four recorded recent
completions and overview bars. Cards expand descriptions/criteria and earned
custom series link to previous tiers.

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
prove claims. No reward presentation/claim calculation is added. Forever's
Rewards and Tree pages retain all claims and progression.

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

Community live/source evidence includes earlier 1.60.1 builds and does not
prove every behavior on 70338. Supplied live evidence, documented contracts
and guarded calls are used together.

## Reversibility and limits

The addon cover is parented only to ChallengesPage, with opaque background,
mouse/wheel interception, descendant clipping when supported and a frame
level above native page children. Native visibility, anchors, alpha, mouse
settings, functions and providers are untouched. Append-only native page
show/hide/size hooks preserve existing scripts and become inert on disable.
WoW does not expose hook removal; a reload while disabled starts without hooks.

Combat defers initialization and hides an existing cover; leaving combat
retries. Missing frames wait for native addon loading or another enable
command. Protected/forbidden roots/pages and failed initialization/rendering
leave the native presentation exposed. No force-load, native selection,
native search setter, function replacement, transmission, CVar write,
completion grant, trait purchase or reward claim is added.

Native events invalidate metadata; visible updates are coalesced. Existing
custom checking/earning hooks refresh character data. Complete native catalogs
are cached between native events/reopening; criteria are read on expansion.
No polling ticker is added.

Tests run actual adapter/controller Lua and template OnLoad callbacks with
explicit UI doubles. They verify data separation, retained saves/scripts,
commands/persistence, fallback, points/criteria, meta links, visible-card
scrolling, XML contracts, asset coordinates and original hashes.
They cannot establish texture availability, pixel fidelity, native timing,
combat taint or SavedVariables disk writes. Own labels currently use English;
native text follows client localization. Native tracking/comparison setters
are excluded; the standalone alpha features remain.

Use the twelve-step manual plan in ForeverAchievements/Integrations/README.md.
