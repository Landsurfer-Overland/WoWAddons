# Existing source baseline

Reviewed repository: `Landsurfer-Overland/WoWAddons`, commit `65d378cc37c164906e8c6346de701075b9805b5a`, testing branch `achievement-alerts-test`. Addon version `0.5.1-alpha-alert-test6`; published main remains unchanged.

## Definition coverage

- 263 custom definitions across all factions/classes: 256 supported definitions and 7 disabled compatibility records.
- 59 retained native imports in the old standalone catalog; the unified custom adapter excludes these imports.
- 68 bundled native reference rows with aliases grouped as one row. Nine are omitted from the old imports. The complete live native catalog is queried from the client, so 68 is not its total size.
- No per-character completion values or live progress evaluator results were exported. All source definitions, including generated tiers, were loaded in the existing isolated Lua5.1 fixture. Fixture reads are not client observations.

## Catalog files and active filters

[existing-custom-catalog.csv](existing-custom-catalog.csv) includes every custom key, authored description/criteria, static checklist, dynamic-criteria flag, default point value, category/section, faction/class, dependency, disabled reason and progress-function source location. Dynamic client criteria and configured money thresholds can differ at runtime. Inspect the cited evaluator/data table for additional conditions; functions were not executed to fabricate missing criteria.

[existing-native-references.csv](existing-native-references.csv) includes every bundled native name, aliases, reference description and retained import key. Native scope, current criteria and Legacy Point rewards remain client-read, not inferred.

The [existing readable catalog](../achievement-catalog.md) remains a convenient category list. The missing pasted excerpt named by the brief is replaced for baseline purposes by this complete source export; the supplied excerpt was explicitly incomplete.

`LegacyAchievementsReforged/LegacyAchievementsReforged.lua:1812–1819` filters unsupported records, required addons, class and faction. `LegacyAchievementsReforged/Integrations/CustomAdapter.lua:130–133` excludes old native imports and duplicate keys and calls that availability rule. Supported definition count therefore differs from the number shown to a particular character. All seven QuickFish definitions require QuickFish; rare mount class restrictions and faction variants are preserved.

The unified presentation maps custom/native categories, validates relationships and merges equivalent rows. A native filtered Legacy Point view is not a separate new achievement. Source equality/aliases alone do not prove that every live native record duplicates a proposal; unresolved comparisons stay pending.

## Load order and storage

TOC interfaces: `16001, 120100`. Load order: libraries and original-UI policy; AlphaUI; Data/DataQuests/ DataProfDungeons/DataExtra; MoneyTracking; core; social/tooltips; ObjectiveTracker/Tracker and retained views; alert/settings; LegacyInspector; read-only adapters/performance/presentation/statistics; owned Wrath UI; native window bridge/controller. The optional research probe is absent from this production load order.

`LegacyAchievementsReforgedDB` is account settings/character snapshots; `LegacyAchievementsReforgedCharDB` is character observations/history. Existing per-character timestamps and identity/provenance safeguards remain unchanged. Saved addon observations are persistent only for previously observed play. This research never reads the player’s real WTF files and does not alter either SavedVariables schema.

## Source provenance

Prior user reports and matching pinned Forever UI mirror identify `1.60.1.70338`, Interface16001. The mirror source is Gethe/wow-ui-source commit `943764493e6b16d63ded3ab304150d1f05e58b57`; nine reviewed generated API files and hashes are listed in [forever-source-manifest.json](forever-source-manifest.json). This proves source identity, not execution or historical record availability on the user’s current client.

The original supplied brief/backlog are retained byte-for-byte in `inputs/`. Their preliminary feasibility labels are input hypotheses; this audit’s fields supersede them. Their hashes are recorded below.

- `Codex_Achievement_Research_Brief.md`: SHA256 `710330d9b94fd4970a554309d6f79d9d502efebc74d31862e8d8784c59e868a1`.
- `Legacy_Achievements_Reforged_Backlog.txt`: SHA256 `01d3d8242ffdf857a44dd07ccb694528d83b7d42ada1ab48c6c28bd98df8511d`.

See [achievement-capability-audit.md](achievement-capability-audit.md) for existing recovery paths and limits.
