# Iteration 4: character and exploration proof audit

Target: Forever 1.60.1, Interface 16001, Project 18, Lua 5.1. Automated checks
execute the production core in Lua 5.1; no live-client tests have been run.

## Findings

The TOC already declares `LegacyAchievementsReforgedCharDB` as
`SavedVariablesPerCharacter`. `Earned`, custom zone definitions and custom
point totals read that loaded character file. Account `chars` snapshots do not
feed custom completion, and zone definitions do not call native Legacy
achievement completion. The audit did not establish native account completion
being copied into custom SavedVariables.

The previous exploration path nevertheless accepted a verified-name map and a
matching non-hover texture while checking **every zone at startup**, without
requiring this character to be at the criterion's location. Texture metadata
does not identify its owning character. Moonglade has one authored criterion,
so a globally revealed/base texture can satisfy its whole requirement in that
path. Its actual mapping is ID **855**, map **1450**, offset **244, 89**;
it is not a zero-offset special case. Elwynn and Westfall IDs are **776** and
**802**, maps **1429** and **1436**.

Saved revealed-overlay proofs and companion-item booleans also had no recorded
character identity. The prior map cache checked the loaded database table but
not character identity. A second `PLAYER_ENTERING_WORLD` registration overwrote
the earlier cache-clearing callback in the single-handler registry; clearing is
now consolidated with the money/battleground handler. Existing false completion timestamps intentionally
survived every earlier update, so installing a safer trigger alone could not
change those historical display states.

These are confirmed code-path weaknesses. The precise source of a reported
live Moonglade award still requires the client's progression diagnostic output.

## Corrected proof boundaries

| Evidence | New custom completion behavior | Existing data |
|---|---|---|
| Remote zone's revealed texture | Unknown; cannot grant the criterion | Retained |
| Zone visit without a revealed matching overlay | Cannot grant | Retained |
| Matching current player zone/subzone, verified current unit map or bounded child-map ancestry, genuine matching non-hover overlay | Record versioned proof for this character | Older sample retained as `previousEvidence` when replaced |
| Complete explored-area-at-position API set is exposed | Also requires positively discovered area IDs at the current player position; unknown/error/empty results cannot grant | No historical inference |
| Existing versioned proof with recorded local observation and matching current character | May prove an earlier discovery without revisiting it | Retained |
| Unattributed old overlay proof | Requires fresh local proof before granting an unearned achievement | Retained; no timestamp revoked |
| Companion or mount item positively classified in current character bags | Add to a versioned per-character item ledger | Original item booleans and best/journal counters retained |
| Unattributed old companion-item booleans | Unknown if no independently verified item exists | Retained; never assigned a newly invented acquisition owner |
| Native Legacy account completion | Native completion only | Native records and APIs unchanged |
| Account mount journal or unattributed rare-item ownership | Cannot create a character Feat of Strength | Historical earned timestamps and `owned` retained |

The map location check uses `C_Map.GetBestMapForUnit("player")`, not the map
currently displayed or hovered. It validates map IDs and names, with a maximum
32-parent walk. For a criterion naming a separately mapped city, its exact
actual unit-zone/map name can prove location without guessing a parent map.
This keeps Elwynn's explicitly authored Stormwind City criterion usable.

When the client exposes `GetExploredAreaIDsAtPosition`,
`GetPlayerMapPosition` and `GetAreaInfo` together, their independent positive
discovery observation is required too. If these APIs are absent, the documented
fallback proof is exact current player geography plus a genuine revealed
overlay. This fallback's behavior on Forever still needs in-game verification.

Unattributed historical discoveries may require revisiting the named areas.
They appear unknown while the client cannot supply trustworthy character proof;
existing earned timestamps continue to be preserved. No special rule hides
Moonglade or turns native Legacy completion into character completion.

## SavedVariables compatibility

New `trackingIdentity` records describe the owner of observations made from
Iteration 4 onward. They do not retroactively attribute existing `done` entries.
New custom awards store `completionAttribution[key]` with the actual recorded
identity and timestamp. Older completion timestamps stay unattributed.

Known ownership mismatches and unreadable identity metadata return unavailable
scope, suppress custom completion/points and prevent new awards. Nothing is
erased. GUID availability changes can use an exact recorded complete Forever
name plus realm alias; two different known GUIDs cannot be joined by name.
If an observation was initially bound by name, its first subsequently observed
GUID is stored additively as `observedGUID` while preserving the original key.
A later recreated namesake with a different known GUID is unavailable.

Companion history now uses `characterCollectionEvidence[field]` with version,
character key and verified unique items. The old `characterPetItems`,
`characterMountItems`, `petsBest` and `mountsBest` fields remain saved. A verified
lower bound can prove an acquisition even when unrelated bag slots are unknown.

Rare-item Feats use `featOwnershipEvidence`, with actual current-character
bank/bag counts, equipped items or known player spells as proof. Account mount
journals and unattributed legacy `owned` flags cannot create a new completion.
Missing or malformed ownership reads remain unknown. The exact custom Charger
and Dreadsteed definitions now require PALADIN and WARLOCK respectively for
availability and new awarding; historical timestamps and the Feats layout/type
remain unchanged.

`/lar correctachievement <key>` remains a preview followed by the generated
explicit confirmation token. It affects one achievement on the verified current
character, archives its timestamp and attribution, then holds automatic reaward.
`/lar correctachievement <key> resume` requires a separate confirmation. A known
other-character database cannot be corrected through the current character.
Account snapshots and source evidence remain saved.

Custom **For The Alliance!**, key `forAlliance`, exact ID **614**, is unavailable
in the active catalog and cannot be newly awarded. Its definition, 20-point
metadata and historical `done.forAlliance` entries remain saved. Custom ID 619
`forHorde`, native records and similarly named achievements are unaffected.
Removing the definition's `unsupported` flags restores this exclusion if the
required mechanics are later introduced.

## Changed functions and performance

Core `CharacterIdentity`, `CharacterScope`, `BindCharacter`,
`CompletionAttribution`, `RecordCompletion`, `CharacterCollection`,
`AreaLocation`, `AreaExplored`, `ClearExplorationCache`, `ZoneMap`,
`ExploredOffsets`, `Earned`, `Complete`, `CheckAll`, `TotalPoints`,
`Owns`, `Feat`, `Available`,
`inspectachievement` evidence and `correctachievement` implement these changes.
The core also forwards copper-normalized money operations to `MoneyTracking`.

Identity, geographic APIs, map metadata and explored-area API observations share
the existing synchronous `WithEvaluation` cache. Results never survive an
independent pass or database switch. The persistent revealed-overlay cache now
checks both database and character identity. Existing overlay coordinate
buckets, native enumeration budgets, criteria bounds and performance diagnostics
remain intact. This introduces no new ticker, delayed batch loop or UI callback.

## Client checks

1. Back up both account and per-character SavedVariables.
2. On Character A, inspect `explore802`, `explore776`, `explore855` and `pet1`
   with `/lar inspectachievement <key>`. Enable `/lar progressdebug on` before a
   new observation. The report includes current player zone/subzone/map,
   confirmed/unknown areas, character key, required local proof and preserved
   historical completion status.
3. On Character B, stay outside Westfall/Elwynn/Moonglade. Open the world map,
   hover those zones, reload and reopen achievements. Remote textures and
   account Legacy completion must not grant custom character points.
4. Enter a genuinely undiscovered named area on B. Confirm its real zone/map
   and non-preview discovery appear in the report; confirm other remote areas
   stay unknown. For Moonglade's zone-wide criterion, a valid current Moonglade
   location must be required even if its map was already visible remotely.
5. Verify Elwynn's Stormwind criterion while actually in Stormwind. If map or
   position/discovery APIs cannot verify the location, capture the diagnostic
   output rather than granting by map visibility alone.
6. Confirm a companion item in B's own bags can award `pet1`; an account pet
   journal or A's item history must not. Reload and remove the observed item:
   B's versioned acquisition proof should persist.
7. Historical false timestamps must remain until a targeted preview and token
   confirmation. Verify the correction hold, archived timestamp/attribution,
   separately confirmed resume and unaffected other characters/native Legacy.
8. Repeat rapid navigation/open/close/search/expansion with `/lar perf on` and
   capture `/lar perf report`. Re-run the Going Down? terrain/fence regression.

Automated tests include two isolated characters progressing through all authored
Elwynn and Westfall criteria, globally revealed remote maps, Moonglade's single
criterion, current-map mismatches, exposed empty versus positive explored-area
results, copied proof/collection ledgers, GUID readiness, correction scope and
history, exact ID 614 exclusion, and per-pass geographic/identity operation
counts. They do not establish live rendering, progression authority or stability.
