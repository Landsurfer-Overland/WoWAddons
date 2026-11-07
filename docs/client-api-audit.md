# Achievement API audit — Forever 1.60.1.70862

Reviewed November 7, 2026. Test build: **0.5.2-alpha.3**.

The audit inventories **all 322 production definitions: 263 custom achievements
and 59 legacy native imports**. Seven custom definitions remain explicitly
unsupported/hidden. No achievement, point value, saved completion key, original
completion date, or correction hold was removed or reset.

## Evidence and limits

The newest public `forever` UI-source snapshot available during this review was
[`9dc84f0d3bbae1768ac3405b3716000bd93eda06`](https://github.com/Gethe/wow-ui-source/tree/9dc84f0d3bbae1768ac3405b3716000bd93eda06).
Its `version.txt` reports **1.60.1.70862**, committed November 7, 2026. This is a
public mirror of shipped client UI/API contracts, not a running game client,
character inspection, or the server's achievement/creature/quest database.

- [Source manifest](research/client-70862-source-manifest.json): pinned files,
  immutable blob hashes and source links.
- [Complete achievement inventory](research/client-70862-achievement-audit.json):
  one entry for every definition, including disabled definitions and native
  imports. Each entry identifies its source location, reference IDs, captured
  thresholds/IDs, evidence family and applicable assumption policy.
- Rebuild the inventory with `python tools/audit_achievement_apis.py`.
  `--check` verifies that it still matches the production definitions.

An API declaration establishes the signature, not that every legacy content ID
still has the same meaning. Source review cannot certify every achievement as
obtainable, or every statistic as character-specific lifetime history. In-game
checks below are still required. The combined UI's native catalog is discovered
at runtime; the 59 imported definitions are historical configured records, not a
claim that the current native client contains only 59 achievements.

## Changes implemented

### Permanent automatic path

The confirmation command from alpha.2 is only an optional repair tool. Normal
players should not need to attest to each clear. Alpha.3 adds automatic paths
that remain useful after an account-wide criterion is already complete:

1. **Successful native encounter boss list.** Build 70862 documents the sixth
   `ENCOUNTER_END` payload as `encounterUnitStatus`: engaged creatures with
   `creatureID`, `creatureName` and `remainingHealthPercent`. The previous handler
   ignored this payload. It now credits only recognizable bosses at zero health
   in a successful encounter. It does not require a selected target or equate
   the encounter ID with an NPC ID. Existing exact-name `BOSS_KILL` and encounter
   name handling remain supported.
2. **Automatic historical counter discovery.** Native statistics categories are
   read without changing native selection/search. Exact boss-kill labels are
   matched to authored objectives, explicitly account-wide/unknown-scope rows
   are excluded, and metadata is revalidated before reading a discovered ID.
   Positive personal counts can backfill old clears even if the hard-coded
   statistic ID changed. Unknown values, reused IDs, deaths, and unrelated
   dungeon labels do not prove a kill. The API's availability on the running
   client is capability-checked; a shared UI source declaration is not live
   verification that the server supplies a useful counter.
3. **Corpse-loot evidence.** Up to 32 readable exact creature GUID/name
   observations are remembered for this character/session. Matching a boss's
   actual corpse GUID in loot sources can record its defeat when encounter
   notifications are absent. This is explicitly a loot-eligibility inference.
   Merely targeting, losing a target, or looting a different GUID never counts.

Discovery reads at most 256 categories / 2,500 records per scan, with three
startup attempts and one additional native-addon readiness opportunity. Combat
defers the scan; normal progress refreshes only re-read mapped counters. No
unbounded numeric ID search or repeated catalog scan runs in the regular UI
refresh path. Character switches clear transient unit evidence. Actual observed
boss completion is persisted with its source and retains the original award date.

There is no honest automatic personal backfill from the OR/account checkbox
alone when the server exposes no other history. In that case alpha.3 keeps the
old personal kill unproven while tracking subsequent clears automatically;
it does not silently award both alternatives or every alt. The optional repair
tool is not presented as the permanent solution or suggested by normal diagnostics.

### Live-client correction: shared account criterion

The initial fallback assumed separate named, personally attributable dungeon
criteria. A live build-70862 diagnostic disproved that assumption for Hall:
Novice Spelunker 62031 uses criterion **19213**, named **"Ragefire Chasm or Hall
of Thanes"**, with **account scope** and **no NPC asset ID**. Its 64016 alias uses
criterion **117733**. Statistic **63573** returned `--`. These are three distinct
limits: alternative-objective mapping, character attribution and missing kill
history. The initial tests did not model this combination and missed the bug.

The updated mapping recognizes both alternatives, but a completed OR criterion
does not grant both, even when the whole Spelunker meta is personally earned.
Future native completion events inside a matching instance, or a known
false-to-true transition in that instance, can record character-bound context
evidence. This is a labeled context inference, not a new personal server flag.
Login, visiting the dungeon with an old true account flag, generic updates of an
unchanged flag, and events in an unrelated instance cannot supply that evidence.

For an already-completed run, `/lar recover dungeonThanes` previews the completed
native record. `/lar recover dungeonThanes confirm` explicitly attests that this
character completed Hall. It records **player-confirmed recovery** separately
from native data and uses the normal custom award evaluator. Recovery requires
a matching completed criterion, applies only to the selected single-boss dungeon,
does not change statistic 63573 or award Ragefire, and respects correction holds.
The attestation is bound to character identity/GUID readiness; it is not copied
to other characters. This is necessary because the API output alone cannot
reconstruct which character completed which alternative in the earlier run.

### Native evidence can recover custom achievement credit

The native challenge UI reads objectives through `GetAchievementNumCriteria`
and `GetAchievementCriteriaInfo`. Its current detail pane still reads the
thirteenth `GetAchievementInfo` return, `wasEarnedByMe`, for attribution.

`Integrations/AchievementEvidence.lua` now uses those same read interfaces.
For configured Novice, Experienced and Master Spelunker records it checks the
expected achievement title as well as the ID, then inspects bounded criteria.
Completed creature criteria match an authored NPC ID only when criterion type
is creature-kill type 0; a linked achievement's asset ID is not an NPC ID.

For Hall of Thanes, a personally attributable completed native criterion named
Hall of Thanes can satisfy the custom Durgen Dirgehammer achievement. This is
an **explicit inference that a completed single-boss dungeon implies its final
boss was defeated**. An exact matching boss name is also an objective mapping
inference. Diagnostics label these inferences. Dungeon-name matching never
awards a multi-boss roster wholesale, and total Spelunker progress alone never
proves which dungeon was completed.

Partial native criteria with known character scope can be used before the
whole Spelunker achievement is complete. A finished native achievement requires
personal attribution; account or other-character completion alone does not
award a character's custom achievement. An exact criterion earner matching the
current full character name can also supply attribution. Unknown scope stays
unusable for this fallback. English authored names/aliases remain a mapping
limitation on other locales.

For **196 eligible custom definitions with reference IDs**, an additional
fallback recognizes a completed native record only when **ID, normalized title,
and `wasEarnedByMe=true` all match**. This is eligibility for a lookup, not a
claim that 196 equivalent native records exist. The equivalence assumption is
that the same ID/title still describes the authored objective; changed native
requirements need content checks. Native-backed checklists reflect the same
completion, without inventing a kill count or altering Blizzard progress.

### Progress refreshes reach custom awards

The native pane already refreshes its cards when criteria change. The custom
award evaluator previously lacked the same criteria-update path. It now
rechecks on `CRITERIA_UPDATE`, `CRITERIA_COMPLETE`, `CRITERIA_EARNED`,
`ACHIEVEMENT_EARNED`, and achievement-list updates. Spell, recipe, instance and
additional battleground statistic updates also request checks. Event
registration remains guarded for clients without an event.

A burst schedules one evaluation after 0.5 seconds. Native metadata and criteria
are shared only within one synchronous evaluation snapshot, then discarded.
Criteria enumeration is capped at 256 per source and the dungeon lookup uses
only the six configured Spelunker IDs, not an unbounded ID search. Pending work
for a replaced character database is discarded. The data-version upgrade runs
two quiet history passes so recovered old progress does not trigger a toast storm.

### Current skill and spell APIs

Build 70862 documents `C_SkillInfo.GetSkillLineInfoByID`, returning a nullable
`SkillLineAttributes` table. Riding and profession checks now read its numeric
skill ID and rank, reject headers/invalid/secret ranks, and map skill IDs to the
existing internal names. This avoids depending on localized display names or
expanded skill headers. Legacy skill/profession-slot fallbacks are retained.

Player spell checks can use `C_SpellBook.IsSpellKnown` when `IsPlayerSpell` is
unavailable; the documented default bank is Player. Account mount/pet journals
are not substituted for a character's acquisition history.

### Numeric and kill evidence

- Count statistics accept plain nonnegative integers and unambiguous grouped
  integers. Fractions, decimal counts, negative values, money text and unknown
  placeholders do not become larger counts by stripping punctuation.
- Where native statistic metadata explicitly identifies account scope, it is
  excluded from custom character counts. Missing metadata remains a legacy
  compatibility assumption, not verified character attribution.
- Missing recipe and simple PvP statistics remain unavailable rather than
  displaying a fabricated zero. An explicit native zero remains a known zero.
- Clearing/losing a living target no longer proves a kill. Readable target death,
  native criteria/statistics and successful encounter notifications remain
  available paths. Restricted combat data is not bypassed.

## Coverage by family

The machine-readable inventory contains the complete key-by-key coverage.
The following summarizes the reviewed paths and remaining assumptions.

| Family | Current evidence and API path | Main limitation / live check |
| --- | --- | --- |
| Levels | `UnitLevel`; level-up event | Current state is queryable; native personal fallback is optional. |
| Riding and professions | New `C_SkillInfo` table, player spells, legacy slots | Historical dropped professions need an observed or exact native record. |
| Quest totals and quest lines | Native statistics, completed-ID list and exact quest flags | Flag counts approximate quest totals; legacy quest IDs/hidden flags need checks. |
| Loremaster | Completed quest flags classified through optional QuestieDB | Dependency, authored continent lists and thresholds remain content assumptions. |
| Exploration | Character-bound location/overlay evidence and matching personal native completion | Old overlay rosters and remote/account maps cannot be assumed current-character history. |
| Dungeon and raid bosses | Native Spelunker criteria, statistics and observed successful kills | Single-boss dungeon-name inference is explicit; legacy head-quest shortcuts remain approximate. |
| Reputation | `C_Reputation.GetFactionDataByID` and observed maximum | Faction identity/cap, special scales and account-wide reputation still need live validation. |
| Money | Existing identity/unit-checked native totals and observed ledger | Ledger fallback covers tracking period, not otherwise unavailable lifetime history. |
| Mount/pet collections | Character bag items/equipment, optional personal native completion | Pre-installation items absent from bags can be missed; account journals are not personal history. |
| Ownership feats | Item count/equipment/player spell or personal native completion | A held item/spell can infer acquisition source; it need not prove a specific quest path. |
| Fishing | Native statistics plus existing catch observations | The existing skill-minus-one floor and catch-window/item equivalence remain estimates. |
| Cooking recipes | Statistic 1745 plus recipe/skill refresh events | The statistic's exact lifetime/current-known unit must be tested. Filtered recipe lists are not substituted. |
| QuickFish | Optional dependency log | Seven definitions use dependency-wide/account data; they are not verified native character counters. |
| PvP totals | Native statistics/lifetime HK and match refresh events | IDs/units and delayed scoreboard updates need live checks; account flags are rejected when known. |
| Single-match PvP | Observed scoreboard and target/emote flags | No pre-installation match history; name/surname and timing behavior need checks. |
| Critters, pests, rares and books | Specific emote, confirmed death or book-open observations | Older history and English name lists are not automatically recoverable. |
| Food/drink and loot rolls | Existing bag-change and result-message observations | Consumption/source/name/locale attribution remains inferred. |
| Falling | Existing measured fall with readable position and survival evidence | Old falls and restricted samples cannot be reconstructed. |
| Native imports | Native completion/criteria; current native adapter preserves scope | No synthetic Legacy points, rewards or server-side achievements are granted. |

The six daily-quest definitions and custom For the Alliance remain retained but
unsupported under the existing project policy. Source review did not establish
new mechanics or content evidence justifying re-enabling them.

## In-game diagnostics and acceptance checks

Install the complete **0.5.2-alpha.3** addon folder and keep SavedVariables.
The minimap launcher on this branch enables/opens the combined pane below 25.

1. Run `/lar apicheck` to record the actual client build and API availability.
2. On the character that completed Hall of Thanes, run
   `/lar apicheck dungeonThanes`. It prints progress, evidence source/inference,
   statistic 63573, and matching native criterion IDs/completion/scope.
   Personally attributable completion should reconcile after login. A shared
   account criterion requires recorded personal context or the explicit recovery
   above; it cannot be silently assigned to this character.
3. If no matching native row is found, run `/lar apicheck native`. This prints
   the configured native dungeon criteria so the exact IDs/names can be mapped
   from this character's real data. A missing/ambiguous record is not proof of a
   failed dungeon; it is a diagnostic gap.
4. Use `/lar apicheck dungeons` for all authored bosses and
   `/lar inspectachievement dungeonThanes` for existing progression diagnostics.
   `/lar apicheck all` reads every custom definition without granting awards.
5. Compare a second character that has not completed the dungeon: native account
   completion must not award that character's custom achievement.
6. Test one new skill rank, learned riding spell/recipe and native criterion.
   Confirm custom completion refreshes without reopening/reloading the pane.
7. Clear a living target during combat and then perform an actual supported
   boss kill. Only the confirmed kill/native progress should count.
8. Verify old completion dates, point values, tracking and correction holds;
   compare fishing/native statistic units on real catches before changing estimates.
9. Complete a boss while targeting another unit, with the native account
   criterion already ticked. Confirm normal automatic credit and inspect its
   encounter-unit evidence; no recovery command should be needed.
10. With a readable personal boss statistic, relog and verify quiet historical
    backfill. With no such record, verify the account OR row alone does not
    manufacture personal credit. API diagnostics now report catalog discovery.

Diagnostics query progress and may refresh the evaluator's ordinary observations;
they do not call the award evaluator or mutate native achievements/rewards.
Automated tests cover the contracts and state preservation, not actual game
rendering, protected-frame behavior or server data availability.
