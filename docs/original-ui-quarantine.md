# Original alpha UI quarantine

Build: `0.4.18-alpha-quarantine1`. Includes the previous combat, logical-fit,
opening-flash and header fixes.

The original minimap/data-broker launcher still called `LAR.Open`, whose alpha
window remained independent of the native Legacy replacement. Removing only
that button would leave slash commands, bindings, tracker clicks, chat links
and received comparison callbacks able to reopen the old presentation.

`UI/OriginalUIPolicy.lua` now loads before the alpha core with `enabled = false`.
The central local `Open` exits before creating or refreshing the old window.
`LAR.OpenSearch` and `LAR.ShowTab` honor that result before touching the absent
window or changing its tab. The minimap module exits before broker registration,
frame creation or writing saved minimap preferences. Welcome entry points and
queued retries cannot create the old popup or mark it seen. The original
comparison menu is not installed; ordinary achievement link tooltips remain.

The original source is retained, including summary, settings, statistics,
comparison and welcome implementations. Shared alpha helpers, tracking, toasts,
progression, social protocol and snapshots remain loaded. No SavedVariables
schema or stored user preferences are changed by the quarantine. Existing
tracking and social operations continue their normal saved-data behavior.

For development research only, change the single `enabled` flag to `true` in
`UI/OriginalUIPolicy.lua`, then `/reload`. This restores the retained entry
points and respects previous minimap preferences. Set it back to `false` and
reload to resume quarantine. There is no player-facing or persisted toggle.

Normal Legacy opening and `/lar legacyui on|off` remain independent of this flag.
This change does not migrate the alpha settings or comparison UI into Legacy.

Changed runtime files: `LegacyAchievementsReforged.lua`, `Minimap.lua`, `Welcome.lua`,
`Social.lua`, `LegacyAchievementsReforged.toc`, and new `UI/OriginalUIPolicy.lua`.
The Legacy controller, bridge, artwork, layout, adapters and tracking evaluators
are unchanged from the header build.

## Client checks

Replace the complete addon folder, keep WTF/SavedVariables, and `/reload`.

1. Verify the old LegacyAchievementsReforged minimap button/data-broker launcher and
   automatic welcome popup are absent, including on login to a new character.
2. Open Legacy normally with `/lar legacyui on`; confirm the unified window,
   Rewards, Trees and Statistics still work, including close/reopen and combat.
3. Try bare `/lar`, the old key binding, tracked-achievement clicks, and shift-click
   an addon chat link. None should create the dark alpha window or raise errors.
   Ordinary link tooltips and right-click untracking should still work.
4. Verify achievement history, points, tracking and saved window preferences
   remain. `/lar legacyui off` should still restore native Legacy normally.

Automated validation: **596 tests passed**, including nine quarantine regressions
and retained alpha consumers, actual core/controller opening, and existing
combat, header, performance and progression tests. Lua 5.1 syntax passed for
28 files; packaging passed for 29 TOC references and four XML files. Isolated
core initialization loaded 322 definitions and passed 14 behavior assertions.
Actual in-game display, login and client restrictions require verification.
