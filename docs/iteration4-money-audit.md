# Iteration 4 money audit

The four active custom monetary achievements now compare **copper with copper**. Display text converts only at the boundary: 100 copper = 1 silver; 10,000 copper = 1 gold. Native Legacy requirements, currencies and rewards are unchanged.

## Definitions and proposed Forever thresholds

| Saved key / reference ID | What it measures | Previous requirement | Iteration 4 default | Source and unit evidence |
| --- | --- | --- | --- | --- |
| `gold100` / 1176 | Money looted, first tier | 100g / 1,000,000c | **5g / 50,000c** | Verified character lifetime statistic 333, or explicitly dated `CHAT_MSG_MONEY` observations |
| `gold1000` / 1177 | Money looted, middle tier | 1,000g / 10,000,000c | **25g / 250,000c** | Same independent loot metric, not money currently held |
| `gold5000` / 1178 | Money looted, major tier | 5,000g / 50,000,000c | **100g / 1,000,000c** | Same independent loot metric, not quest rewards or account Legacy points |
| `breadwinner` / 1182 | Lifetime money from quest rewards | 10,000g / 100,000,000c | **100g / 1,000,000c** | Verified character lifetime statistic 326; unavailable totals remain unknown |

These are initial lower-economy tuning values, not measured Forever economy statistics. The 5/25/100g loot tiers keep a substantial separation between an introductory milestone and the major achievement; the 100g quest milestone requires cumulative quest rewards. Client testing and actual income rates should guide further tuning. No custom achievement in this catalog measures current holdings; `GetMoney`, auction/vendor income, `PLAYER_MONEY`, or native Legacy currency balances are not used to award these records.

Configure a custom threshold with `/fa money threshold <saved-key> <integer-copper>`, for example `/fa money threshold gold5000 750000` sets the major loot tier to 75g. Loot tiers must remain strictly increasing. Thresholds are saved under `ForeverAchievementsDB.moneyConfig.thresholds`; malformed values fail back to defaults without overwriting the settings. Achievement keys, reference IDs, points and existing completion timestamps remain the same. Tuning a threshold does not revoke historical completion.

## The reported `38 / 50,000,000`

The previous `gold5000.progress` returned `math.min(DB().money, 50000000), 50000000`. The adapter carried those raw numbers into the Wrath progress card, so its requirement was the original **5,000g expressed in copper**. The value 38 came from the character's `money` field at evaluation time.

The previous field had two possible writers:

- `CHAT_MSG_MONEY` parsed gold/silver/copper labels and added the resulting copper.
- `SyncMoney` read `GetStatistic(333)`, parsed known coin textures, or stripped every non-digit character and treated the result as copper. It then retained the larger of the statistic and the saved counter.

The captured report does not include the live original statistic or its title. Therefore, **38's original units and source are not established**. It could have been 38 copper from an event, an ambiguous plain statistic, or a preexisting counter; it must not be described as verified gold, silver, or a particular wrong statistic. Statistic 333/326 names in the supplied Wrath data are “Gold looted”/“Gold from quest rewards”; that identifies their intended meanings, not proof that Forever exposes compatible lifetime data.

`/fa money report` now shows the statistic ID, client title, exact readable raw string, accepted source, formatted progress and copper threshold. This is the evidence needed to diagnose the live 38 case. The optional performance commands remain available separately.

## Accepted observations and unsupported data

`MoneyTracking.Read` accepts a lifetime statistic only when `GetAchievementInfo` identifies the expected statistic, exposes readable nonnegative integer flags that do not include the account-wide flag, and its value explicitly includes recognized gold/silver/copper coin textures. Missing, hidden or malformed scope flags cannot prove character scope; an account-wide statistic is rejected as character earnings. API failures, hidden values, `--`, a plain `38`, percentages, numeric strings without currency units, negative amounts and non-currency icons stay unknown. No digit-stripping fallback converts these into money. Raw text is bounded, and all API reads are protected.

For a localized client, automatic English identity matching may be unavailable. After verifying the exact statistic title in-game, `ForeverAchievementsDB.moneyConfig.statisticNames.loot` or `.quest` may contain that exact localized title. Coin-unit validation remains required. A title override alone never makes a plain number into copper. Different Forever statistic identities or formats require additional confirmed evidence and code support.

Loot messages use the client's localized `GOLD_AMOUNT`, `SILVER_AMOUNT`, `COPPER_AMOUNT`, or literal localized currency labels. Labels are escaped as literal text rather than Lua patterns. Recognized coin textures also work. Grouped integers support comma, period and space (including nonbreaking spaces); ambiguous decimal values without explicit subunits are rejected. Quest reward chat and generic changes in player money are deliberately not added to looted money.

When a verified lifetime loot total is unavailable, the addon can still count **observed loot since Iteration 4 tracking began**. It says so beside the progress bar and in the description. That is an observed total, not a reconstructed lifetime history. The lifetime method remains unsupported in the diagnostic evidence. The quest-money achievement has no unverified event substitute and displays unavailable progress when its lifetime statistic cannot be verified.

The observed loot counter is never added to a lifetime statistic. If both are available, the larger independently observed total is used. Synchronizing, logging in, reloading, opening the UI, changing a category and reevaluating progress never add earnings. An available numeric chat line ID suppresses duplicate dispatch of that same event using a bounded session cache. Identical messages with different IDs, or separate events without IDs, remain separate legitimate loot events; text or elapsed-time guesses do not discard them.

## SavedVariables and performance

`ForeverAchievementsCharDB.money` and every existing `done`/history entry are preserved unchanged. The previous counter mixed event copper with a potentially ambiguous statistic and had no provenance marker, so it is **retained for audit without silently using it as a verified baseline**. This can leave uncompleted historical monetary progress unavailable until reliable lifetime evidence exists. It is not erased, converted, attributed to another character or fabricated. A confirmed historical completion remains completed.

New event observations use the separate character field `moneyTracking = { version=1, unit="copper", observedLootCopper=..., startedAt=..., ownerIdentity=... }`. A first safe synchronization starts it at zero; that means zero observed since the new dated tracking period, not zero lifetime earnings. The owner tags only the new observations, not historical achievements. An existing malformed or unbound ledger is left untouched and is unavailable for event writes. Both the core's character-scope guard and the new ledger's verified owner reject ambiguous or different-character storage, preventing a copied ledger from awarding a new character even if its enclosing legacy DB was previously unbound. Account configuration contains thresholds only, not shared character earnings.

`MoneyTracking.WithSnapshot` shares source observations only within one synchronous progress evaluation. Nested calls preserve the outer snapshot, character DB changes use a separate snapshot, and the snapshot is restored on errors. A later evaluation rereads the client data. There is no new ticker, frame, window callback, whole-database scan or permanent statistic cache.

## Regression checks

Automated Lua 5.1 tests in `tests/test_iteration4_money.py` cover source identity, explicit coin units, localized labels and formats, unsupported lifetime data, malformed/hidden values, threshold ordering, observed/lifetime reconciliation, duplicate event IDs, fresh/nested snapshots, character separation, history preservation and actual core event awards. These are API-double tests, not client verification.

Manual client checks:

1. Enable `/fa perf on`, run `/fa money report`, and retain the full output before earning money. Confirm the four requirements and the original raw 333/326 values.
2. Loot a known amount of coins solo and in a party. Confirm exactly one corresponding observed increment per actual message. Distinguish loot from quest, auction, vendor and current-holdings changes.
3. Reload, relog and repeatedly open/search/scroll the unified window. Confirm neither observed money nor completion timestamps increment from those actions.
4. When a statistic is available, verify its title, lifetime meaning and coin units against the native Statistics display. Confirm an updated lifetime total is selected independently instead of added to the observed counter.
5. On a second character, confirm the observed ledger and custom points are separate while account-wide native Legacy data remains visible.
6. Check the formatted card and tracker text: `38c / 100g`, or an explicit unavailable/tracking-period label, never an unexplained raw `38 / 50000000`.
7. Change one custom threshold, verify description and bar agree, then restore the desired tuning. Confirm native Legacy requirements and historical completions do not change.
8. Run `/fa perf report`, then `/fa perf off`. Live client source formats, actual economy balance and absence of a timeout remain to be verified in-game.
