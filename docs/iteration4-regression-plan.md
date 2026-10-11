# Iteration 4 accuracy audit and client regression plan

Target: Forever 1.60.1, build 70338, Interface 16001, project 18, Lua 5.1.
These changes extend the stability build. Automated fixtures exercise actual addon
Lua with explicit API/UI doubles; they do not validate live rendering, server
progression, taint, client timings, or SavedVariables disk writes.

## Storage and independent completion

`LegacyAchievementsReforgedCharDB` remains SavedVariablesPerCharacter. Its original `done`
keys and timestamps remain the completion history. `LegacyAchievementsReforgedDB.chars`
contains separate account snapshots used for historical indicators, never to award
this character's custom achievements. Existing snapshot identities include realm,
Forever surname where available, and a valid player GUID where available.

New observations record a verified tracking identity; newly earned custom completions
also record attribution alongside the existing timestamp. A known foreign or malformed
identity makes current-character progression unavailable rather than copying, erasing,
or reassigning history. Older per-character completion timestamps stay saved without
retroactively manufacturing new attribution entries. Old account snapshots without
verified attribution cannot name a previous earner.

Current custom completion retains the Wrath gold treatment. An incomplete current
custom record can name another verified character without receiving their points or
date. Native completion uses a restrained blue accent, with scope derived from the
actual native flags and earning metadata. Unknown native scope is not described as
account-wide merely because the record comes from Legacy.
Rare-mount Feats also require actual character item/equipment/spell evidence rather
than the account mount journal. Charger and Dreadsteed use their explicit Paladin
and Warlock requirements; Feat artwork and the existing navigation stay intact.

For a verified combined card, the custom and native records remain independent
components. One shield represents the custom character-point value; blue native status
and the point tooltip expose native completion and its actual point award. Criteria,
dates, source identities, rewards and completion authority stay independent. Source
summary totals count the components separately; category navigation uses normalized
cards. No native challenge IDs, SavedVariables, completion events, or rewards are merged.

## Exploration and historical evidence

The real Moonglade definition is `explore855`, map 1450, with one required area at
overlay offset `(244, 89)`. Westfall is `explore802`/map 1436; Elwynn Forest is
`explore776`/map 1429. The API describing revealed textures does not document a
character-ownership flag. Previously, a remote texture read or saved overlay proof
without identity could satisfy a startup check without establishing this character's
presence in the required area.

The generic area evaluator now requires current-player geographic evidence plus a
matching, non-preview revealed overlay on a verified current map. A zone-wide named
criterion requires presence in that zone; other criteria require the named subzone.
When the full explored-area-at-position API is available, it must provide positive
matching area evidence too. New proofs retain character identity and local observation
evidence; map caches cannot cross characters. This applies to all zones and does not
hide or special-case Moonglade.

Unattributed older observations remain saved and cannot establish a new verified
completion. Areas or learned collection items that cannot be reconstructed safely may
show unavailable progress until positively observed. Genuine existing completions are
not automatically revoked. An optional token-confirmed correction archives and clears
only the chosen current-character completion, adds a reaward hold, and leaves source
evidence, other characters, other keys and native progression intact.

Use `/lar progressdebug on` while investigating, `/lar inspectachievement explore855`
for the current condition, and `/lar progressdebug dump` for award decisions. Repeat
with `explore802`, `explore776`, `pet1` or `fall` as appropriate. Disable with
`/lar progressdebug off` when finished.

## Relationship and classification audit

Stable native candidates come from native type-8 continent links and the existing
authored custom definitions, including Forever's additional mainland zones. A candidate
is combined only after the live requirements are verified: exact identifiers, canonical
zone requirement, and the complete matching type-43 area-discovery criteria. Native
completion never supplies custom completion. Names alone are not a merge key.

Verification shares a fixed budget and prioritizes Westfall, Elwynn Forest and
Moonglade. Cached requirement signatures contain no completion values. If native reads
are unavailable, different, or outside the budget, the records stay separate. A later
native catalog refresh or reopening can verify more candidates; no extra refresh loop
is started to exhaust the catalog. Thus an initially unverified pair can still have
two clearly identified cards until its requirements are established.

| Ambiguous records | Evidence | Handling |
| --- | --- | --- |
| Westfall 802, Elwynn 776, Moonglade 855 versus their custom keys | Captured native continent links identify candidates; full current requirements need runtime verification. | Combine only when the complete required-area sets match; unavailable or different requirements stay separate. |
| World Explorer versus Explore Azeroth 62053 | Corresponding continent chains exist, including Forever zones; complete child equivalence still needs verification. | Preserve independent states in World Exploration until the full relationship is proven. |
| Explorer 62382 versus Explore Azeroth | Explorer is a separate “have a character with” wrapper with its own native reward. | Keep the wrapper independent; use live flags/rewards. |
| Explorer 64015 versus 62382 | Different observed flags and native selection evidence. | Preserve actual IDs; no title-based substitution. |
| Zephras Isle | Custom zone exists, corresponding native ID not established. | Keep the custom record independent. |

See [relationship implementation](iteration4-relationships.md) and
[independent captured-data audit](iteration4-independent-audit.md). The community
capture is build 69913, not proof of build 70338's complete requirements.

Parent achievement lists now contain only directly assigned records; parent counts
can include descendants. General profession milestones live directly in Professions,
with individual professions retaining their children. Broad reputation milestones
live in Reputation, while faction-specific records remain in their faction groups.
Dungeons/Raids, PvP and Feats retain their structure. Only the exact custom
`forAlliance` reference ID 614 is inactive for unavailable mechanics; its definition
and saved history remain preserved. Similar titles and native IDs are not guessed.

Class navigation uses readable runtime game-mode availability and class metadata,
actual native class categories, observed current class and captured Forever class
content where appropriate. Modern class icon tables do not establish playability.
Native class completion remains authoritative and unrelated classes are not awarded
custom class achievements.

## Money audit and tuning

All monetary comparisons use integer copper; only displayed text converts units.
Current holdings do not stand in for cumulative loot or quest income. The four custom
keys and their point values stay unchanged:

| Key | Old target | Iteration 4 default |
| --- | ---: | ---: |
| `gold100` | 100g | 5g / 50,000c |
| `gold1000` | 1,000g | 25g / 250,000c |
| `gold5000` | 5,000g | 100g / 1,000,000c |
| `breadwinner` | 10,000g quest rewards | 100g / 1,000,000c |

These are configurable initial lower-economy values, not measured income rates.
Use `/lar money threshold KEY COPPER`; loot tiers must stay increasing. Native
Legacy thresholds and currency rewards are unchanged.

The old `38 / 50,000,000` display was the raw character money counter compared
with 5,000g in copper. That counter accepted event loot and a statistic parser that
could interpret plain digits without currency evidence. The report does not establish
38's original source or unit. `/lar money report` now prints the actual raw statistic,
its title, verification result and threshold. Statistics 333/326 are accepted only
with verified metric identity, readable non-account scope flags and explicit coin units.
Otherwise loot uses explicitly
dated observations since the new tracker began, and unavailable lifetime quest income
stays unavailable. Login and UI refreshes do not create earnings; the observed and
lifetime totals are not added together. The old money counter remains preserved and
cannot fabricate a trustworthy baseline. See [the full money audit](iteration4-money-audit.md).

## Manual client checks

1. Install the full new addon folder while retaining `WTF` data. Enable
   `/lar legacyui on`, `/lar perf on`, and optional `/lar progressdebug on`.
   Record a first-open timing report before navigating.
2. On character A, verify genuine Westfall/Elwynn/Moonglade completion, point totals,
   dates, criteria, and native Legacy completion. Observe new area evidence only through
   genuine gameplay; inspect its recorded map, local geography and character identity.
3. Log into distinct character B, who has not explored those areas. Current custom
   records and points must remain unearned; verified A history can name A. Shared native
   completion may be blue and must never turn B's custom achievement gold. Inspect
   `pet1`: an account pet journal or old shared maximum must not grant Can I Keep Him?.
4. Inspect suspected historical false records before any correction. Only if explicitly
   testing a false award, run `/lar correctachievement explore855`, review the preview,
   and enter its confirmation token. Check the archive and hold. To permit reearning,
   separately preview and confirm `resume`; genuine new evidence must then be required.
   Never run correction commands merely to test a legitimate achievement.
5. Browse Eastern Kingdoms and Kalimdor after the native data loads. Verified equivalent
   zones must have one card with independent custom/native details. Unverified pairs
   should retain distinct source identities. Reopen to allow bounded verification of
   further candidates. Check World Exploration and its independent Explorer wrapper.
6. Check direct lists: Professions contains general milestones; Fishing/Cooking/Alchemy
   contain their own records. Reputation contains broad milestones; Other Factions has
   individual factions. Check each supported class, unavailable For the Alliance!,
   Spelunker/dungeon groups, PvP and Feats. Expand/collapse navigation independently
   from selecting it, and check that counts can include children without listing them.
7. Run `/lar money report`. Verify 100c = 1s, 10,000c = 1g, and the configured targets.
   Loot known coins through ordinary gameplay and verify one increase. Opening/searching
   the UI and reloading must not add that loot again. A plain unverified statistic such
   as “38” must not masquerade as verified lifetime money. Quest income remains unavailable
   if its source cannot be verified; current holdings must not substitute for it.
8. Open/close repeatedly, switch categories rapidly, expand/collapse cards, scroll long
   lists, search/type/clear, drag and change size presets/UI scale. Visit all four tabs;
   verify native Rewards/Trees behavior and restore with `/lar legacyui off`. Check queued
   work while closing, combat/gamepad transitions, and original fallback behavior.
   `Going Down?` must not award for a fence collision or merely becoming stuck.
9. Save `/lar perf report`, progression evidence and any fallback/error text. Pure
   navigation must not repeatedly enumerate the catalog. Turn diagnostics off, reload
   both characters and check genuine saved progression, histories and attribution.
   Client testing remains pending until these checks are actually performed.
