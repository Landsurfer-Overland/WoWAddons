# Legacy Achievements Reforged Inspector

This manual diagnostic discovers accessible Legacy frames, namespaces, challenge
records, and reward fields. It does not implement native Legacy integration or
change the existing achievement interface or tracker.

## Run it in Forever

1. Install the updated `LegacyAchievementsReforged` folder in the active client's
   `Interface/AddOns` directory. The TOC loads `Diagnostics/LegacyInspector.lua`.
2. Log in or use `/reload`, and leave combat.
3. Open the native Legacy **Challenges** page so its data can populate.
4. Type `/legacyinspect`, then click **Run Inspection**.
5. Click inside the report, press **Ctrl+A**, then **Ctrl+C**. Paste the result
   into a text file or this chat. Copying uses the game's EditBox; the diagnostic
   neither accesses the clipboard directly nor writes files or transmits results.
6. Change the native category yourself and run the inspector again. The report
   compares provider identity and sampled IDs with the previous manual run.
7. Open the native **Reward Track** yourself and run another inspection. Copy
   this report separately because hidden pages may have no populated data.

**Clear Results** empties the text area. **Close** hides the diagnostic window.
Reports and the previous comparison snapshot are held only in memory and are
discarded on reload. There is no continuous polling or automatic inspection.

## What the report establishes

- `CLIENT` records the actual build, interface number, project constant, and
  `_VERSION` when readable. The supplied client screenshot reports Forever
  1.60.1, build 70338, interface 16001. Runtime support must still be tested there.
- `FRAMES` inspects `LegacySystemFrame` and its bounded descendants, recording
  names, types, parents, immediate child counts, named regions, direct Lua
  fields, function fields, and supported event scripts without executing them.
  Candidate page properties are checked against their native parent relationships.
  Named descendants provide a fallback when direct properties are absent.
- `NAMESPACES` scans a bounded number of raw global keys for Legacy, Challenge,
  Achievement, and RewardTrack names. Matching tables receive only a direct-key
  sample; unrelated frames and arbitrary global tables are never traversed.
  Function identity matches can suggest a source mixin, but do not prove its
  original attachment.
- `CHALLENGE DATA` checks supported `GetDataProvider`, `GetSize`, and
  `GetCollection` getters, with passive `dataProvider` / `collection` fallbacks.
  It samples records and reports actual candidate fields for IDs, names,
  descriptions, categories, progress, completion, points, and scope. Supported
  row `GetElementData` getters and passive row fields can expose visible data.
- `REWARD TRACK` reports accessible populated candidate fields for Legacy
  points, milestones, thresholds, rewards, descriptions, and claim status.

The standard provider getters were checked against Blizzard's public shared UI
source: `DataProviderMixin:GetCollection` returns its collection,
`DataProviderMixin:GetSize` reads its length, and
`ScrollBoxListViewMixin:GetDataProvider` returns its provider. The standard
`GetElementData` mixin getter returns stored row data. Unknown Legacy namespace
functions, iterators, and other methods are listed but never invoked.

The `CONFIRMED` findings describe what was readable in this run. `HYPOTHESIS`
recommendations require checking the actual field meanings and native state
before building an adapter. A method or namespace name alone proves no API
contract.

## Bounds and limitations

`ns.LegacyInspector.Config` defines the limits; edit the configuration at the
beginning of `LegacyInspector.lua` before installing if needed:

| Setting | Default | Hard ceiling |
| --- | ---: | ---: |
| `maxDepth` | 4 | 4 |
| `maxObjects` | 80 | 160 |
| `maxOutputChars` | 60000 | 120000 |
| `maxFields` | 24 | 64 |
| `maxEntries` | 20 | 100 |
| `maxGlobalMatches` | 100 | 200 |
| `maxGlobalScan` | 30000 | 50000 |

Frame hierarchy traversal and relevant passive table samples each have a depth
limit. Expanded frames, checked regions, and sampled tables share the object
budget; global classification uses its separate match/scan budgets. Requested
property paths and challenge provider samples are prioritized before generic
descendant expansion. Direct-key sampling examines at most 256 keys per table
and emits at most `maxFields`. Numeric records also respect `maxEntries`.
Each frame expansion considers at most 256 immediate child references.
Detailed output has a separate allowance to leave room for summary sections.
Any reached limit makes the snapshot partial.

- Open the native interface first; the inspector never force-loads it.
- Category changes are manual. A snapshot difference does not prove its cause.
- Providers can contain only the selected category, and rows may be recycled.
  Rows below the depth limit and unpopulated hidden pages can be unavailable.
- Restricted values are redacted. Forbidden frames and failed/unsupported
  getters are skipped. Function-valued table metamethods are not executed for
  arbitrary tables, so inherited custom data may remain inaccessible.
- Registered event enumeration is unavailable until a verified safe client
  mechanism is established. The inspector never registers events to probe it.
- Original mixin names and account/character scope cannot be inferred reliably
  from object types or field names.
- Inspection and window creation are deferred during combat.
- The diagnostic makes no native frame changes, script hooks, category
  selections, scroll changes, provider replacements, or reward claims. Only
  its own window is changed.
- Normal `LegacyAchievementsReforged` behavior remains active, including its existing
  social addon messages. The diagnostic does not call or use that system.

## Existing project findings

The alpha's TOC declares interfaces 16001 and 120100. Its code uses Lua 5.1
syntax, but the live client Lua version was not previously recorded.
`DataExtra.lua` identifies its generated datasets as Wrath Classic 3.4.3.58936
and Forever 1.60.1.70205, older than the supplied build 70338.

There was no Legacy frame or ScrollBox integration. Existing guarded
`GetAchievementInfo`, `GetAchievementNumCriteria`, and
`GetAchievementCriteriaInfo` calls import configured native achievement IDs.
Those records receive addon achievement points, and duplicate native Explorer
and reputation records are omitted. The inspector neither uses the addon's
progress helpers nor changes those rules.

Existing API families include `C_Container`, `C_Item`, `C_QuestLog`, `C_Map`,
`C_MapExplorationInfo`, `C_MountJournal`, `C_PetJournal`, `C_Reputation`, `C_PvP`,
`C_AddOns`, `C_ChatInfo`, and `C_Timer`, with various older-global fallbacks.
These are existing addon assumptions, not a requirement that all are available
to the isolated diagnostic.

## Validation outside the game

From `/workspace/WoWAddons`, run:

```sh
python3 -B -m unittest discover -s tests -v
python3 /workspace/.cloud-tools/legacy-achievements-reforged/validate.py
```

The tests use Lua 5.1 with explicit frame/data-provider mocks to exercise
read-only behavior, unsupported access, bounds, and the addon-owned copy window.
They do not verify live native API support, real rendering, clipboard behavior,
or the Legacy data schema. Those require the in-game reports above.
