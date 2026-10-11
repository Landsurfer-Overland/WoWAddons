# Codex research brief: Legacy Achievements Reforged

Date: October 11, 2026  
Task: Audit proposed achievements for WoW Forever, with late-install fairness as the primary requirement.

## Objective

Research the current addon and the actual Forever client interfaces to identify genuinely new achievements that can be awarded reliably, including to someone who first installs the addon after reaching level 60.

The target is approximately 200 new achievements spanning General, Quests, Exploration, Professions, Dungeons & Raids, Reputation, PvP, Classes, and Feats of Strength. Quality, distinct criteria, reliable tracking, and historical recovery take priority over reaching 200. Category allocations in the draft are provisional.

This is a research and verification task. Inspect the repository, produce an evidence-backed audit, and create small read-only diagnostics where necessary. Do not add or award achievements in the production addon during this phase. Verified findings will guide later implementation.

## Inputs

Read these supplied files:

- `Legacy_Achievements_Reforged_Backlog.txt`: 200 draft candidates, stable planning IDs ACH-001 through ACH-200, partial duplicate review, and preliminary feasibility tags.
- `Pasted markdown.md`: existing catalog excerpt. It starts midway through PvP and is incomplete.
- The current addon repository and any available Forever client UI/API exports.

The repository's actual definitions and active presentation filters are authoritative for existing addon achievements. Obtain the complete active custom catalog and native Legacy references from source; do not assume the pasted excerpt is complete.

The earlier feasibility labels are hypotheses, not verified support. Do not inherit their conclusions without checking the exact criteria.

## Primary requirement: fairness for late installers

An addon-only lifetime counter cannot recover actions that happened before installation or while it was disabled. Saving new observations does not solve that problem.

Prioritize achievements whose qualifying progress persists in authoritative character data, completed-quest flags, native achievement criteria, collection records, or another durable client-readable record.

For every candidate, answer:

1. Can a fresh installation at level 60 recover the same qualifying progress that an always-installed addon would know?
2. What exact persistent record establishes that progress?
3. Does that record cover the character's lifetime, only current state, only a recent period, or the account?
4. Is the API usable in Forever, on this build, with the data and scope we need?
5. Can the character still earn the achievement after installing late if no backfill exists?
6. Does the design impose extra repetition solely because the addon was absent?

Prefer full historical recovery. Current-state achievements can also be suitable if the description explicitly rewards current state rather than claiming a lifetime history. Explain limitations such as unlearned professions, sold collectibles, reset reputation, and changed faction.

Never reconstruct lifetime activity from level, wealth, skill level, reputation, current currency balance, or a related accomplishment. A completed native record can prove its own criteria, not arbitrary underlying counts.

Newly visiting a scenic location remains possible after level 60, but that is repeatable access, not historical backfill. Mark that distinction.

## Eligibility decisions

Assign exactly one decision per candidate:

| Decision | Meaning |
| --- | --- |
| KEEP — BACKFILL | Exact criteria can be recovered from durable character records after installation. |
| KEEP — CURRENT STATE | Exact criteria intentionally describe queryable current state; do not promise historical completion. |
| REDESIGN | A distinct, fairer achievement can replace the original criteria using reliable data. |
| OPTIONAL — PROSPECTIVE | Only actions observed while installed count; obtainable later but inherently lacks historical credit. |
| HOLD — UNVERIFIED | Required data, mechanics, scope, or availability are unresolved. |
| DROP — DUPLICATE | Existing custom or native achievement already covers the same objective. |
| DROP — UNRELIABLE | Reliable qualification cannot be established. |

Keep OPTIONAL — PROSPECTIVE entries outside the primary proposed point-bearing set unless Matt explicitly approves them later. Do not silently assign them zero points as a policy decision.

Do not count unresolved placeholders or incompatible alternatives as verified additions to meet the target.

## Evidence levels

Keep design decisions separate from evidence:

- SOURCE REVIEWED: Source or documentation identifies a possible interface.
- CLIENT OBSERVED: A controlled action produced the expected data in the actual Forever build.
- VERIFIED: Controlled tests establish exact criteria, attribution, scope, persistence, and recovery behavior.
- BLOCKED: Required access or evidence is missing.

Documentation for Retail, another Classic version, or Season of Discovery is a lead, not proof of Forever support. Function presence alone is not verification. Record build/version and source commit where available.

If no executable Forever client is accessible, complete source research and provide precise client test instructions. Leave findings at SOURCE REVIEWED or BLOCKED. Do not claim tests ran.

## Research workflow

### 1. Establish the actual baseline

- Read applicable repository instructions.
- Identify addon version, target client interface/build, load order, data definitions, active filters, adapters, trackers, and SavedVariables schema.
- Export the complete existing active achievement catalog with criteria, scope, point values, faction/class eligibility, and source locations.
- Separate active custom records, disabled compatibility records, and native Legacy references. Resolve aliases as one record.
- Document existing historical recovery paths and their limitations.

### 2. Build a capability inventory before implementing anything

Investigate durable data first:

- Completed quest IDs and completion flags, including class/faction variants and hidden flags.
- Current reputation and any durable standing/milestone history.
- Current profession skill and learned recipe records.
- Explored-map state and persistent exploration completion.
- Character collections and ownership records, including mounts and companions.
- Native achievement/challenge criteria and completion, where readable.
- Persistent statistics, if exposed in Forever: establish the exact meaning, unit, character/account scope, coverage, and historical retention.
- Boss/instance completion history: distinguish current lockouts from lifetime completion.
- Honor, PvP results and objective statistics: distinguish current totals, seasonal data, scoreboard snapshots and lifetime records.
- Currency data: distinguish held balance, lifetime earned, spent, and recoverable transaction history.

Do not assume any of these interfaces exist. Record absent, inaccessible, restricted, ambiguous, or version-dependent data explicitly.

### 3. Audit all 200 planning IDs

Compare criteria semantically, not just titles. Identify direct duplicates, same-objective threshold variants, composite metas, and internal draft overlaps.

For each ID, produce:

| Field | Required content |
| --- | --- |
| ID / title / category | Preserve the planning ID and original proposal. |
| Exact criteria | Remove vague phrases such as signature quest or qualifying camp until defined. |
| Duplicate check | Existing record IDs/keys and matching criteria, or unresolved missing evidence. |
| Proposed data source | Exact API/event, arguments, payload, IDs and source location. |
| Record semantics | Current/lifetime/seasonal/session; character/account; persistence. |
| Fresh-install recovery | Yes, partial, no or unknown, with explanation. |
| Disabled-addon recovery | Whether missing activity is recovered when re-enabled. |
| Late-install experience | What an already-level-60 player receives or must repeat. |
| Decision | One eligibility decision from the table above. |
| Evidence level | SOURCE REVIEWED, CLIENT OBSERVED, VERIFIED or BLOCKED. |
| Tests / result | Exact procedure and observed output, or clearly labeled pending tests. |
| Replacement | Distinct, fair alternative when needed. |

Research shared tracking families efficiently, then assess each entry's additional conditions separately. A fishing signal does not also prove pool identity or ingredient provenance.

### 4. Focused investigations

**Hearthstones**
- ACH-016 proposes uses; ACH-017 proposes distinct observed bind locations.
- Investigate durable statistics before relying on an addon counter.
- `GetBindLocation()` is a lead for the current bind location, not a lifetime count.
- `HEARTHSTONE_BOUND` is an unverified event lead, not confirmed Forever support.
- Test successful binding, same-location rebinding, different inns sharing a subzone, localization, relog, and installation after previous bindings.
- If history cannot be recovered, redesign or classify prospective; do not infer ten inns from a single current bind.

**Camping**
- Preserve Matt's interest in first campfire, 200 sessions, and 500 sessions.
- First determine whether Forever maintains queryable camping statistics or milestones.
- Ordinary rested state, a sit command, an emote, or proximity is not proof of a qualifying campfire session.
- Shared campfire attendance and minimum duration require separate reliable signals.
- If only live detection exists, retain the ideas in the optional research queue rather than claiming fair historical credit.

**Fishing**
- Preserve ACH-004, The One That Got Away: fish up 2,000 items, with an Ashbringer joke.
- Investigate whether a durable statistic measures exactly items fished, successful catches, fish only, or another unit.
- Validate junk, stacked catches, failed casts, loot attribution, pools and disabled-addon periods.
- If an existing statistic has a different meaning, propose clearly worded criteria matching it.
- Self-caught cooking ingredients require provenance; do not infer it from owning or cooking identical purchased items.

**Merchant's Favor and supply-faction reputation**
- Treat Merchant's Favor currency separately from Azeroth Commerce Authority / Durotar Supply and Logistics reputation.
- Verify the actual Forever faction IDs, currency ID, ranks/caps, character scope and reliable sources.
- Research current supply-faction standing as a promising current-state design.
- Current currency balance does not prove lifetime earnings or spending.
- Lifetime earned/spent proposals require durable records; otherwise redesign toward an exact balance/ownership criterion or classify prospective.
- Do not copy Season of Discovery turn-in reputation rules.

**Dungeons, PvP and classes**
- Completed boss records may be recoverable; lockouts may only prove recent participation.
- Scoreboard totals may not prove a particular player's flag/base action or a timed sequence.
- Completed class quest flags are promising; define exact chains and avoid existing Charger/Dreadsteed records.
- Native class-level and profession-skill milestones are already represented in the catalog excerpt.
- Timed saves, group attendance, summons, recipient delivery, and complex combat conditions need precise attribution.

**Feats of Strength**
- Never infer old beta, launch or event participation from addon installation date.
- Use authoritative durable participation records or hold/drop the entry.
- Do not introduce avoidable installation deadlines.
- Existing rare ownership feats must be checked for duplication and record persistence.

### 5. Verify recovery, not just live tracking

For each supported tracking family, where client access permits:

1. Establish a controlled known qualifying state before enabling the proposed tracker.
2. Enable the addon/diagnostic and query whether that state is recovered.
3. Perform a successful action and a failed/canceled action.
4. Check duplicates, unrelated actions and attribution.
5. Reload, relog and query again.
6. Disable tracking, perform the action, then re-enable and compare recovery.
7. Test applicable faction/class variants and current-state loss.
8. Record build, payload and results.

Use a disposable test profile or backed-up character save for fresh-install simulation. Do not delete real achievement progress. A simulated first install establishes recovery for the tested record only; it does not prove all level-60 history exists.

## Deliverables

Produce reviewable research outputs in the repository's appropriate docs/research location:

1. `achievement-capability-audit.md`: capability inventory, source evidence, client version limits and open questions.
2. `achievement-candidate-audit.csv` or Markdown table: all 200 IDs with the required audit fields.
3. `late-install-safe-achievements.md`: recommended core, separated into backfillable and explicit current-state designs; include verified totals by category.
4. A separate optional/prospective and rejected/replacement section.
5. Minimal read-only diagnostics and concise instructions for any unresolved client tests, if needed.
6. A revised backlog preserving IDs and explaining changes. Only promote entries when the stated evidence level supports it.

In the final research summary, state:
- How many candidates are genuinely new and have verified late-install-safe credit.
- How many are promising but only source-reviewed.
- Which categories still need stronger candidates.
- The highest-impact remaining client tests.
- Whether the level-60 late-installer concern is actually resolved for each proposed family.

Do not report 200 verified achievements unless the evidence supports 200. A smaller defensible core is the correct result if substantial data is unavailable.

## Subsequent implementation gate

Later implementation should begin with small batches of VERIFIED entries that pass duplicate and late-install fairness checks. Keep custom points separate from native Legacy points. Use idempotent awards, safe initialization after data readiness, explicit unknown states, and existing addon conventions. Do not block normal UI interaction or manipulate secure native controls merely to observe progress.

The research phase does not authorize production achievement implementation. Its purpose is to establish which additions we can confidently implement next.

