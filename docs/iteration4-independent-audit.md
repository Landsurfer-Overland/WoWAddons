# Iteration 4 independent evidence audit

This is source and captured-data research, not a new live-client inspection.
Build-specific observations remain evidence candidates; the running client's
readable IDs, criteria, flags and currency getters remain authoritative.

The client UI reference is [Gethe/wow-ui-source build 70338](https://github.com/Gethe/wow-ui-source/tree/943764493e6b16d63ded3ab304150d1f05e58b57).
Additional captured data was read from the MIT-licensed [LegacyNext](https://github.com/lxhwes/LegacyNext/tree/f6bba488215a06d0c0d26899a4399269878ee5b0)
fixtures `dump_challenges_page1_fresh.lua`, `dump_criteria_types.lua` and
`categories_full.lua`. Those fixtures explicitly identify **build 69913**, not
70338. No community implementation was copied into this addon.

## Exploration relationship evidence

The native continent records use type-8 achievement criteria. Their asset IDs
establish these candidates independently of matching titles:

| Native parent | Native child IDs from the captured criteria |
| --- | --- |
| `62353` — Eastern Kingdoms | `760`, `761`, `765`, `766`, `775`, `777`, `627`, `778`, `771`, `776`, `772`, `773`, `779`, `780`, `62354`, `774`, `769`, `781`, `782`, `768`, `770`, `802`, `841` |
| `62355` — Kalimdor | `845`, `852`, `750`, `844`, `848`, `728`, `850`, `853`, `849`, `855`, `62356`, `736`, `63684`, `856`, `847`, `851`, `842`, `846`, `854`, `857` |

The standard custom candidate saved key is `explore<ID>`. The explicit new-zone
candidates are `exploreRiverglades` → `62354`, `exploreHyjal` → `62356`, and
`exploreShendralas` → `63684`. Zephras Isle is outside both continent chains.
These candidates do not establish that the actual map-discovery requirements
are equal in a later build.

An isolated Lua 5.1 comparison of the complete captured zone criteria against
the addon's real `ns.EXPLORE` definitions found exact required-name sets and
counts for the following six records. Every captured native criterion is type 43
(area discovery), requires one discovery, and has a distinct asset ID.

| Native ID | Custom saved key | Zone | Native/custom required areas |
| ---: | --- | --- | ---: |
| `760` | `explore760` | Alterac Mountains | 15 / 15 |
| `761` | `explore761` | Arathi Highlands | 16 / 16 |
| `765` | `explore765` | Badlands | 14 / 14 |
| `766` | `explore766` | Blasted Lands | 9 / 9 |
| `775` | `explore775` | Burning Steppes | 10 / 10 |
| `777` | `explore777` | Deadwind Pass | 3 / 3 |

The captures do not include full Westfall, Elwynn Forest or Moonglade zone
criteria. Their continent links establish candidate native IDs `802`, `776` and
`855`, respectively. A matching title, numeric ID or generic "reveal the covered
areas" description by itself cannot rule out different required subareas.
Unavailable or differing criteria should retain independent cards or an explicit
uncertain relationship; they must never establish custom completion.

| Ambiguous relationship | Verified evidence | Safe interpretation |
| --- | --- | --- |
| Explore Azeroth `62053` / custom World Explorer | Native children are `62353` and `62355`; custom children are `exploreEK` and `exploreKal`. Both authored continent candidate sets contain 23 Eastern Kingdoms and 20 Kalimdor zones. | The chain shapes correspond. Equivalence still depends on the actual zone requirements, including the new zones. Validate the child relationships before folding the world cards. |
| Explorer `62382` / Explore Azeroth `62053` | The captured Explorer requires having a character with achievement `62053`; the fixture records account-wide flags and one native point. | Keep the point-bearing account wrapper independently identifiable. It is not a second character zone-discovery achievement. Live flags and trait-currency rewards remain authoritative. |
| Explorer `64015` / Explorer `62382` | The user's reports show different flags; native selection exposed `62382`. | Do not substitute or merge mirrored IDs using the shared title. |
| Zephras Isle | A custom definition exists; no corresponding native ID is established by these captures. | Preserve the independent custom record. |

## Moonglade and character attribution

The authored Moonglade definition is `explore855`, UI map `1450`, with one
required named area and offset `(244, 89)`. The captured native Kalimdor chain
references achievement `855`. Neither fact establishes who earned a saved
completion, whether a texture is actually revealed for this character, or whether
the authored Wrath offset remains valid for every Forever overlay.

The stability build already rejects hover-preview textures, validates map
identity, limits scans, and isolates its temporary evaluation caches by CharDB.
Its persistent overlay cache clears on CharDB changes, map events and expiry.
The remaining source-level risk is older saved revealed-overlay evidence: its
prior shape has no earning-character identity and can be accepted before a fresh
map read. Historical timestamps and evidence must remain saved, but absent
ownership evidence must not be promoted into newly verified character progress.
Native account completion never supplies that ownership evidence.

The exact 70338 `MapExplorationDocumentation.lua` describes dimensions,
offsets, hover previews, draw-layer placement, file IDs and hit rectangles. It
does **not** declare a character-ownership flag for an overlay. The native map
provider shows every non-hover texture and supplies no additional discovery
ownership test. Thus a readable non-hover texture, particularly a permanently
visible base layer, is insufficient on its own to demonstrate that this
character newly discovered the named area. `GetExploredAreaIDsAtPosition` and
`C_Map.GetAreaInfo` offer explicit discovered-area IDs and names, while native
type-43 criteria can provide a readable earning-character name. Each requires
guarded runtime verification and must not substitute account-wide completion.

Iteration 4 therefore requires the current character to be physically located
in the verified map and the exact required subzone (or the zone itself for a
zone-named criterion), together with a matching genuinely revealed overlay.
Available discovered-area APIs must also return readable discovery evidence.
The character-bound observation is retained for later checks. A remote startup
scan, a hover preview, an account map, an old visit flag or an unattributed old
proof cannot grant a missing completion. This conservative policy can leave
historical incomplete area progress unknown until the character revisits it;
existing completion timestamps are not revoked.

## Supported classes

The complete captured native category list contains the nine vanilla class
subjects under native Classes `15568`: Druid `15577`, Hunter `15578`, Mage
`15579`, Paladin `15580`, Priest `15581`, Rogue `15582`, Shaman `15583`, Warlock
`15584`, and Warrior `15585`. This establishes historical native content, not an
unchanging hardcoded class roster.

Build 70338's shared `CLASS_ICON_TCOORDS` also contains Death Knight, Monk,
Demon Hunter, Evoker and Traveler. That shared artwork table is not evidence that
those classes are playable in Forever. Runtime class metadata alone can have the
same limitation. Where available, guarded
`C_GameRules.IsClassAllowedForGameMode(classID)` combined with readable
`C_CreatureInfo.GetClassInfo(classID)` provides a stronger bounded discovery path.
Actual native class categories and the current player's readable `UnitClass`
remain useful conservative fallback evidence when the game-mode getter is absent.

## Money progress trace

The stability build contains four monetary custom definitions:

| Saved key / reference ID | Metric | Prior threshold in copper |
| --- | --- | ---: |
| `gold100` / `1176` | Money looted | `1,000,000` = 100 gold |
| `gold1000` / `1177` | Money looted | `10,000,000` = 1,000 gold |
| `gold5000` / `1178` | Money looted | `50,000,000` = 5,000 gold |
| `breadwinner` / `1182` | Quest reward money | `100,000,000` = 10,000 gold |

The old third tier renders `min(CharDB.money, 50000000)` against `50000000`.
The custom adapter retained these raw numbers; the Wrath presentation used them
as a raw numeric fraction. Thus `38 / 50,000,000` is consistent with a saved raw
counter of 38, but **the report does not prove what originally produced 38**.

`CHAT_MSG_MONEY` parsed localized gold/silver/copper tokens into copper and added
the result to the character's counter. `SyncMoney` read statistic `333`, decoded
coin textures where present, otherwise stripped nondigits and treated the number
as copper. `StatCopper(326)` used the same ambiguous plain-number fallback for
quest rewards. No uploaded trace establishes the client's actual plain statistic
units or lifetime-statistic scope for those IDs. Repeated login used a maximum,
not direct addition, but the plain-string interpretation and presentation remained
unsafe. A format containing explicit units can be normalized; a plain `38`
cannot be relabeled as verified lifetime copper or gold without evidence.

No native Legacy monetary threshold should change in response to this custom
economy rebalance. Completed historical timestamps and legacy counter values
must survive, while uncertain counters remain identifiable as uncertain.
