# Late-install-safe achievement recommendations

Research date: October 11, 2026. Source build: `0.5.1-alpha-alert-test6` on `achievement-alerts-test`.

**Verified, genuinely new, late-install-safe additions: 0.** No executable Forever client was available. Source review is complete for all 200 planning IDs; every runtime/scope/recovery test remains pending. No production achievement is added, awarded, removed or retuned by this research.

## Decision totals

| Design decision | Candidates |
| --- | ---: |
| KEEP — BACKFILL | 0 |
| KEEP — CURRENT STATE | 1 |
| REDESIGN | 18 |
| OPTIONAL — PROSPECTIVE | 0 |
| HOLD — UNVERIFIED | 123 |
| DROP — DUPLICATE | 58 |
| DROP — UNRELIABLE | 0 |

Evidence levels: **117 SOURCE REVIEWED**, **83 BLOCKED**, **0 CLIENT OBSERVED candidate qualifications**, **0 VERIFIED candidates**. Prior client screenshots establish some native API return shapes, not the new proposals’ recovery or attribution.

DROP — DUPLICATE includes disclosed same-objective threshold retierings and narrower/wider checklist overlaps, as well as exact duplicates. Read the per-ID duplicate field before treating any entry as an identical predicate.

## Recommended core

The implementation-ready core is empty. **Backfillable, VERIFIED: 0. Explicit current-state, VERIFIED: 0.** No original proposal can yet be labeled KEEP — BACKFILL on the available evidence. ACH-193 is one conditional KEEP — CURRENT STATE design, not permission to implement it before testing.

The shortlist contains **14 source-reviewed proposals or replacement designs worth focused tests**. They are research priorities, not a verified new-achievement count. Multiple thresholds or factions share a family. Novelty against the complete live native catalog still needs a client comparison.

### Potential backfill designs: confirm the authoritative counter’s exact wording

| ID | Original title | Candidate/replacement and remaining gate |
| --- | --- | --- |
| ACH-016 | Homeward Bound | Describe the confirmed persistent native unit exactly, e.g. "Have 25 returns recorded by your character’s hearth statistic" only if its meaning is established. Do not infer historical uses from GetBindLocation(). |
| ACH-020 | Frequent Flyer | Match wording to the confirmed native unit, e.g. "Take 50 flight paths" if this means departures; retain completed-arrival wording only if statistic proves arrivals. |
| ACH-021 | Azeroth From Above | Match wording to the confirmed native unit, e.g. "Take 250 flight paths" if this means departures; retain completed-arrival wording only if statistic proves arrivals. |
| ACH-134 | Dungeon Regular | Dungeon Visitor: Have 25 recorded five-player dungeon entries, conditional on client verification of statistic 932. This is a replacement design, not verification of the original 25-completion proposal. |

These are native statistic leads: 353 (times hearthed), 349 (flight paths taken), and 932 (five-player dungeon entries). They must not be renamed hearthstone-only uses, completed arrivals, or dungeon completions without exact unit/persistence/attribution tests. Entry counts are not final-boss completion counts.

### Explicit current-state designs: make the limited promise visible

| ID | Original title | Candidate/replacement and remaining gate |
| --- | --- | --- |
| ACH-104 | A Favor Earned | Proposed exact current-state design: Currently hold at least 100 Merchant's Favor (currency 3402), never infer cumulative earned/spent. SOURCE REVIEWED recommendation only; require cap, name, scope and raw quantity tests before promotion. Retain earned-transaction idea in optional queue only after verified attribution/approval. |
| ACH-143 | For the Lion | Proposed exact current-state replacement: As an Alliance character, currently hold Exalted reputation with Stormwind (factionID 72, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-144 | Among the Ancients | Proposed exact current-state replacement: As an Alliance character, currently hold Exalted reputation with Darnassus (factionID 69, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-145 | Heart of the Mountain | Proposed exact current-state replacement: As an Alliance character, currently hold Exalted reputation with Ironforge (factionID 47, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-146 | Small Friends, Big Ideas | Proposed exact current-state replacement: As an Alliance character, currently hold Exalted reputation with Gnomeregan Exiles (factionID 54, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-147 | For the Warchief | Proposed exact current-state replacement: As a Horde character, currently hold Exalted reputation with Orgrimmar (factionID 76, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-148 | Spirit of the Plains | Proposed exact current-state replacement: As a Horde character, currently hold Exalted reputation with Thunder Bluff (factionID 81, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-149 | A Place Among the Forsaken | Proposed exact current-state replacement: As a Horde character, currently hold Exalted reputation with Undercity (factionID 68, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-150 | Troll Toll Paid | Proposed exact current-state replacement: As a Horde character, currently hold Exalted reputation with Darkspear Trolls (factionID 530, expected classic standing 42000/reaction 8, pending Forever threshold/API/scope tests). A source-reviewed design recommendation, not client-verified or implemented. |
| ACH-193 | Totemic Company | As a Shaman, simultaneously maintain one totem from each of four elements, if supported. PENDING, not run: query UnitClass("player"), the four slot constants, all GetTotemInfo returns and secret status with0/1/3/4 active totems. Verify each element maps correctly and a second same-element totem does not satisfy another slot. Test expiration, recall, death, reload/relog and non-Shaman. Disable diagnostics, summon four, re-enable while all active; repeat using a backed-up fresh level60 profile. Check in/out-of-combat restrictions without forcing protected actions. Do not award until exact Forever build passes. |

Current-state designs can be recovered when the qualifying state is present. They cannot credit standing lost before installation, currency already spent, expired totems, sold items or forgotten professions. The eight capital-standing proposals are narrower predicates than the existing all-city Ambassador metas, with component overlap explicitly disclosed. Their descriptions must say current standing rather than best-ever standing.

## Verified totals by category

| Category | Original candidates | Source-reviewed shortlist | Verified backfill | Verified current state |
| --- | ---: | ---: | ---: | ---: |
| General | 25 | 3 | 0 | 0 |
| Quests | 30 | 0 | 0 | 0 |
| Exploration | 25 | 0 | 0 | 0 |
| Professions | 25 | 1 | 0 | 0 |
| Dungeons & Raids | 30 | 1 | 0 | 0 |
| Reputation | 20 | 8 | 0 | 0 |
| PvP | 20 | 0 | 0 | 0 |
| Classes | 20 | 1 | 0 | 0 |
| Feats of Strength | 5 | 0 | 0 | 0 |

Every category needs stronger tested criteria before implementation. Quests and class chains are promising families but lack exact eligible Forever quest-ID lists. Exploration lacks exact landmark/area/node checklists and recovery evidence. Professions need recipe/craft units and ownership semantics. Dungeons/PvP have heavy overlap with existing records and unresolved native rosters. Historical event feats lack authoritative participation IDs.

## Optional/prospective research queue

No prospective-only candidate is promoted to the primary point-bearing set. Most live-action ideas remain HOLD because even the qualifying signal is unverified; this is not a decision to assign them zero points. The original draft’s point fields are preserved separately in the CSV and revised backlog.

- Keep ACH-001/002/003: first qualifying campfire, 200 sessions and 500 sessions. Neither sitting/rested state nor nearby players proves server-qualified camping. Test durable native statistics first; if only live detection exists, keep the ideas optional and obtain explicit approval before later implementation.
- ACH-004 remains The One That Got Away, 2,000 items, with “Still no Ashbringer.” It is a held threshold extension of the current fishing family. Do not infer catches from skill or turn loot-window counts into items.
- ACH-017 observed binds, scenic revisits, transport journeys, camp duration/attendance, crafting/gathering counters, personal PvP sequences and class actions may remain achievable after level 60. That means future access, not historical credit.
- Earned/spent Merchant’s Favor after tracking starts (ACH-104/105 original designs) needs actual attributed transaction signals. Held balance is a separate replacement; `totalEarned` needs its own retention/unit/scope tests. No spending history is established.
- Ingredient provenance, causal “save” claims, exact recipient delivery and timed carrier/interrupt chains are held or redesigned rather than inferred from ownership, attempts, team totals or related accomplishments.

## Rejected and replacement proposals

**58 candidates** repeat existing objectives or retier them. The full reasons and existing keys/IDs are in [the candidate audit](achievement-candidate-audit.csv). They remain in the revised backlog with stable IDs. Replace them with genuinely distinct exact predicates after the live native duplicate check. No replacement automatically inherits Ready status or counts toward the target.

## Highest-impact pending client tests

1. **Fishing units/recovery:** `/larprobe stat 1456` and `1518` before/after fish, junk, stacked catches, unlooted loot, failed casts and pools. Compare first-enable and disabled-addon periods and another character. This determines whether ACH-004 can retain its exact items criterion.
2. **Durable history leads:** query stats `353`, `349`, and `932`; test successful/canceled/unrelated actions, exact increments, relog and disabled-addon recovery. Counter presence or a positive value is insufficient.
3. **Supply/currency:** `/larprobe reputation 2586`, `2587` and `/larprobe currency 3402`. Verify names, caps, current standing/balance and account scope. Test a known turn-in and an intended purchase, then compare any `totalEarned` field with actual known history. Do not borrow Season of Discovery rules.
4. **Exact quest/native criteria:** define eligible quest IDs and native Spelunker/raid rosters, then query those exact records. Check known-completed true flags before interpreting false flags; include class/faction alternatives and account attribution.
5. **Current-state shortlist:** verify capital reaction/standing, Merchant’s Favor current quantity, and all four totem slots (`/larprobe totems`) including state loss, another character, relog and data readiness.
6. **Recipe/collection history:** test own-character learned flags versus linked profession views; exclude account collections. Forgotten professions/sold items remain uncredited unless an exact durable character record exists.

Use the separate [read-only probe](../../tools/research/LARResearchProbe/README.md). No new achievement implementation or unsafe native UI action is needed for these tests.

## Is the level-60 late-installer concern resolved?

**No, not for any new family yet.** Exact quest flags and correctly identified persistent native counters could resolve it for their own criteria after tests. Current-state predicates resolve only present-state credit and must disclose that boundary. Addon-only history, lost/currently absent state, unspecified checklists and complex provenance remain unresolved. The next step is collecting controlled client evidence, not implementing 200 awards.
