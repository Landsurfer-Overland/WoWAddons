# Optional read-only Forever research probe

This is a **separate addon**, outside the production load order and release ZIP.
Copy the `LARResearchProbe` folder into the active Forever client's
`Interface/AddOns`, enable it in the addon list, and reload. It has no
SavedVariables, achievement definitions, event listeners, timers, awards,
native UI hooks, progression calls, settings writes, or automatic queries.
It does not require Legacy Achievements Reforged to be enabled.

Run one command at a time. A small addon-owned window displays a copyable report:
click the text, Ctrl+A, Ctrl+C. Escape or the close button closes it. `copy`
reopens the last report; `chat` prints it in chat. Reports exist only in memory
and disappear on reload/logout. Copy results **before** reloading.

| Command | Read-only query and limits |
| --- | --- |
| `/larprobe build` | Build, character identity, and presence of the explicit APIs below. No data scan. |
| `/larprobe quest 123` | That quest's completion flag, using `C_QuestLog.IsQuestFlaggedCompleted`, or the legacy global if the modern function is absent. No entire completed-quest scan. |
| `/larprobe stat 353` | Raw `GetStatistic(353)` plus that ID's `GetAchievementInfo` metadata. Keeps units, formatting, placeholders and missing fields intact. No criteria scan. |
| `/larprobe achievement 62053` | Metadata, flags, current-character completion field, and at most **20** criteria for that exact ID. Reports truncation; never follows child links. |
| `/larprobe reputation 2586` | Modern `C_Reputation.GetFactionDataByID` and legacy `GetFactionInfoByID` for that exact faction. No expanding/collapsing reputation UI. |
| `/larprobe currency 3402` | Source-reviewed `C_CurrencyInfo.GetCurrencyInfo`. Matching-build documentation describes the interface; runtime support and currency ID/semantics remain unverified. No balance-to-lifetime conversion. |
| `/larprobe bind` | Only `GetBindLocation()`; no history inferred. |
| `/larprobe skills` | Count and first **20** current `GetSkillLineInfo` rows if the list API exists. Otherwise reads the **six** `GetProfessions()` slots and at most six distinct valid `GetProfessionInfo(index)` records, preserving absent/unknown slots. Header rows count toward the list cap. Not a full recipe catalog. |
| `/larprobe totems` | Exactly four current `GetTotemInfo(slot)` reads, slots 1–4; no cast, summon, UI selection or timing counter. Prints `MAX_TOTEMS` and the four elemental slot constants as raw context; no mapping is inferred. |
| `/larprobe recipe 123` | Source-reviewed `C_TradeSkillUI.GetRecipeInfo(recipeSpellID, optional recipeLevel)` for one supplied recipe spell ID, omitting the optional level. Never opens/selects a profession. Use your own already-open profession and record that context. `recipes` is an alias. |
| `/larprobe copy` / `/larprobe chat` | Retrieve the last in-memory report without re-querying. |

Single-ID commands accept one positive numeric ID; no ranges or ID guessing.
Returned tuples retain their indexed fields, including nils. Tables are shallow
and capped at 30 fields; individual strings are capped at 1,000 characters and
reports at 32,000. Truncation is reported. Missing functions, errors, restricted
values, nil, false, and zero remain distinct. A false flag may still need a
data-readiness test. Successful calls are **not** proof of valid IDs, exact
criteria, character attribution, lifetime scope, or historical recovery.

During combat, read requests can collect a report but the tool creates, shows,
or lays out **no** UI. Leave combat and run `copy` yourself. There are no combat
events or automatic retries. Client errors appear in the report; they are not
turned into zero progress. Existing protected/native frames are not modified.

## Source leads, not verified Forever capabilities

The source baseline is `LegacyAchievementsReforged.lua`'s `IsQuestDone`,
`StatText`, skill readers and `Standing`, plus
`Integrations/LegacyAdapter.lua`'s metadata/criteria readers. The adapter uses
`GetAchievementInfo` fields 4 (completion), 9 (flags), and 13 (`wasEarnedByMe`);
completed account records alone do not establish current-character completion.
The probe prints raw fields and the `ACHIEVEMENT_FLAGS_ACCOUNT` constant rather
than inferring proof. Criteria do not override the metadata completion field.

The matching-build API exports reviewed are from
[`Gethe/wow-ui-source`'s Forever commit `943764493e6b16d63ded3ab304150d1f05e58b57`](https://github.com/Gethe/wow-ui-source/tree/943764493e6b16d63ded3ab304150d1f05e58b57),
version **1.60.1.70338**:

- [CurrencyInfoDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/CurrencyInfoDocumentation.lua): `GetCurrencyInfo(type)` returns `CurrencyInfo`, may return nothing; fields include `quantity`, `totalEarned` and `isAccountWide`. Their exact retention/character semantics still need tests.
- [ReputationInfoDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/ReputationInfoDocumentation.lua): `GetFactionDataByID(factionID)` returns nullable `FactionData`, including `currentStanding` and `isAccountWide`.
- [TradeSkillUIDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/TradeSkillUIDocumentation.lua) and [TradeSkillUITypesDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/TradeSkillUITypesDocumentation.lua): `GetRecipeInfo(recipeSpellID, optional recipeLevel)` returns nullable `TradeSkillRecipeInfo`. The probe prints `recipeID`, `name`, `learned`, and `firstCraft` separately so these remain visible if other fields exceed the shallow cap; none establishes lifetime crafting counts.
- [TotemDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/TotemDocumentation.lua): global `GetTotemInfo(slot)` returns active-slot fields and may return nothing or restricted values. Slot-to-element mapping is not guessed.
- [QuestLogDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/QuestLogDocumentation.lua) and [PlayerScriptDocumentation.lua](https://github.com/Gethe/wow-ui-source/blob/943764493e6b16d63ded3ab304150d1f05e58b57/Interface/AddOns/Blizzard_APIDocumentationGenerated/PlayerScriptDocumentation.lua): exact quest completion getter and current bind getter.

These are **SOURCE REVIEWED** interfaces, not executed Forever client tests.
Profession-slot fallback follows the existing production `Skills()` reader
(which notes Forever may not expose the skill-line list); it does not call that
reader or mutate its saved best-skill history.

`DataExtra.lua` lists statistic **349** as “Flight paths taken,” **353** as
“Number of times hearthed,” **1518** as “Fish caught,” and **1456** as “Fish and
other things caught.” These labels differ; none proves an arbitrary fishing
item/catch/provenance condition. It also lists faction **2586** as Azeroth
Commerce Authority and **2587** as Durotar Supply and Logistics. Query both and
confirm actual names, standing and character scope on the Forever build.
Merchant's Favor currency **3402** is a supplied research lead, not verified
by production source or a client test. Namespace presence cannot verify it.

Current standing, balances, learned skills, bind names and recipes cannot
recover lost reputation, spending, forgotten professions, past inns, crafts,
or ingredient provenance. No account collection API is queried. Recipe data
can reflect a linked profession or selected UI context; record the source and
do not treat a metadata row alone as character ownership.

## Controlled client tests — pending, not already run

1. Back up the actual character SavedVariables and use a disposable test profile
   if simulating a fresh install. **Do not delete real achievement progress.**
   Disable this diagnostic and, where needed, the production addon; preserve all
   saves. Establish a known qualifying state/action **before** enabling the
   diagnostic. Record build, character, faction, class, exact ID and action.
2. Enable only the diagnostic as needed and reload. Query `build`, then the
   **same exact ID**. Record first immediate result and a later result after the
   client is ready. Compare against the established state. This tests recovery
   for that one record, not every level-60 player's lifetime history.
3. Query a baseline, perform one successful controlled action, and query again.
   Repeat with a failed/canceled action, a duplicate action and an unrelated
   action. Verify exact unit, increment, attribution and whether display text
   or metadata changes. Copy every report before reload/logout.
4. Reload, relog, and repeat the same query; disable the diagnostic, perform
   another action, re-enable/reload, and compare. Distinguish persistent client
   data from current session values. A retained client value must be shown to
   cover the proposed time period and character, not assumed to do so.
5. Repeat on applicable faction/class variants and a second character. Check
   account-completed versus `wasEarnedByMe` flags. If testing current state,
   test controlled state loss too (without destroying valuable real progress).
6. Record expected result, observed payload, readiness/context, limitations and
   any failure. Keep evidence at **SOURCE REVIEWED** until these client tests
   establish the exact criteria, scope, persistence and disabled-addon recovery.

Family-specific controls:

- **Hearth/bind:** compare stat353 before/after a successful hearth and a canceled
  cast; query `bind` after same-location and different-location rebinding.
  Include different inns sharing the same localized subzone name. A current
  bind name cannot verify distinct historical inns.
- **Fishing:** compare stats1456 and1518 for fish, junk, stacked loot, failed
  casts, pools and another player's loot. Test disable/re-enable recovery.
  Neither generic fishing statistic establishes self-caught ingredient use.
- **Quests/native criteria:** test completed/unfinished exact IDs, hidden and
  faction/class variants, pre-enable completion, reload and other-character
  account completion. Confirm a known true flag before trusting false results.
- **Supply reputation/currency:** verify actual faction/currency names and IDs,
  query before/after a known turn-in, purchase and unrelated transaction. Check
  held balance separately from any explicitly returned earned/spent fields.
  Query a known previous state after re-enabling; current balances/standing do
  not prove history. Do not import Season of Discovery turn-in rules.
- **Skills/recipes:** use your own profession, compare a known learned versus
  unlearned recipe, note UI context and any linked view, and test reload and
  disabled-addon learning. Do not unlearn a valuable profession for research.
- **Held Hunter loyalty proposal (ACH-187):** on an appropriate test character,
  `/dump C_PetInfo and C_PetInfo.GetPetLoyalty and C_PetInfo.GetPetLoyalty()`
  inspects the namespaced getter documented in the matching Forever source.
  A localized loyalty name alone does not establish the maximum tier, character
  attribution, historical loyalty or support for that proposal. This is a manual
  query, outside the probe's command set.
- **Four active totems:** query with zero, one, and four known own-character
  totems; repeat after cancellation/expiration and another shaman's totems.
  Verify slot names/spell IDs, attribution, restricted values and reload.
  This can investigate an explicitly current-state design, not backfill past
  simultaneous summons or historical casts.
- **Camping/complex PvP/boss conditions:** no guessed signal is implemented.
  First establish an exact durable native record/ID from source or the client,
  then query it and design attribution/recovery tests. Rested state, a campfire
  nearby, recent lockouts, or a scoreboard cannot prove lifetime session counts.

The automated fixture tests exercise bounds, unavailable/error handling,
raw values, scope warnings and combat UI safety. They **do not emulate Forever**,
run game actions, establish API availability or prove historical fairness.
