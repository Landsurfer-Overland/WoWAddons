# Experimental unified Wrath Legacy interface — iteration 2

Install the complete `ForeverAchievements` folder in the active Forever client's
`Interface/AddOns` folder, replacing the previous addon files. Keep the existing
`WTF/SavedVariables` files. No achievement progress reset or data migration is
required. Addon version: `0.4.7-alpha-legacyui`. Original Wrath reference files
remain in the repository, outside the
installed addon and the native Blizzard addon directories.

## Commands and normal use

- `/fa legacyui on` enables the replacement when the normal Legacy System opens.
- `/fa legacyui off` restores the original native presentation when it is safe to do so.
- `/fa legacyui` shows status/help.
- `/fach` and `/qa` also accept `legacyui on/off` through the existing dispatcher.
- `/legacyinspect` remains the manual read-only inspector.

The feature is disabled by default; its account setting persists across reloads.
Open the normal Legacy System using the game's usual control. The complete visible
window uses the original Wrath roof, borders, parchment, and proportions, with a
close button and draggable header. The original native outer art and side tabs are
suppressed while the replacement is active. There is no second outer window border.
The existing standalone `/fach` window and other addon features remain available.

The bottom tabs are **Achievements | Legacy Rewards | Legacy Trees | Statistics**.
Achievements contains one hierarchy: General, Quests, Exploration, Professions,
Dungeons & Raids, Reputation, PvP, Classes, and Feats of Strength. Recognized native
subcategories retain their names beneath an appropriate category. Tradeskills and
custom professions share Professions. Mixed Adventure records are mapped individually
where verified; uncertain or new metadata remains browsable under Unmapped Challenges.
The addon does not put every Adventure challenge into Exploration or invent missing
challenge records.

Click category parents to expand/collapse and cards to show criteria. Meta criteria
open referenced achievements within this interface. Search matches names/descriptions;
the filter button cycles All/Complete/Incomplete locally. Custom tracking uses the
existing character tracker. Native completion and progression stay authoritative to
the game; the presentation does not import them into custom SavedVariables.

The header and Summary display **Character Achievement Points** and **Legacy Points**
separately. Native card shields show actual trait-currency point awards. Shield
tooltips identify the point system. Unknown points show `?` or `Unavailable`.
Achievements without real rewards leave the reward area blank. Recent native
completions appear only when the game supplies a reliable completion date; unavailable
or partial native counts are labeled. The old alpha UI includes older native imports
with synthetic addon points, so its totals can differ from this character-only view.

Legacy Rewards and Legacy Trees display the original native pages within the Wrath
body. Their original parents, subtrees, and handlers remain intact. Native reward
icons, milestones, tooltips, scrolling, and tree editing/Apply/Undo/Reset controls
remain the game's functionality. The addon implements no independent reward claims
or talent spending. Statistics preserves the existing read-only statistics view.

## Compatibility and fallback

Target source and inspection evidence: Forever `1.60.1 / 70338`, Interface `16001`,
Lua `5.1`, project `18`. The implementation has not been tested inside the actual
game client.

The native root remains a registered UI panel; only its visible presentation is
temporarily suppressed. Its original panel-width reservation remains in place to
preserve normal panel behavior. A smaller visible Wrath window can therefore retain
native spacing relative to other open UI panels.

Gamepad mode uses the original native Legacy interface because its SmartNavigation
expects the original three pages and controls. Switching back to mouse and keyboard
can resume the replacement. Native functionality is also restored if required objects
are unavailable, forbidden/protected, or presentation initialization fails. A missing
Rewards or Trees page must preserve access to the native interface rather than display
a fabricated substitute.

Combat defers unsafe presentation changes. Disabling in combat records the disabled
setting and completes any required native restoration after combat; check the chat
status. Do not interpret a pending restoration as permission to change protected
frames during combat. Leaving combat retries pending attachment/restoration.

Native data reads are bounded: 256 categories, 2500 challenges, and 256 criteria per
card. Larger or unavailable results are labeled partial/unavailable. No native points,
dates, completion, rewards, or progress are inferred from missing data.

## Manual in-game test plan

No actual client validation has been performed. Record screenshots and Lua errors at
your normal UI scale, a second UI scale, and a smaller screen resolution if available.
Compare native progression before and after testing; retain existing saved files.

1. Leave combat, run `/fa legacyui on`, and check the chat status. Open the normal
   Legacy System through its usual game control. There should be one complete Wrath
   window with no native black rectangle, portrait, outer border, title bar, or side tabs.
2. Check header alignment and the separate live Character Achievement Points and
   Legacy Points. Drag the header, close with its button, reopen normally, and press
   Escape. The replacement and any native mounted content must close together.
3. Open another normal UI panel alongside Legacy. Verify ordinary panel closing and
   layout still work; note that the native panel's original space reservation is retained.
4. Switch through all four bottom tabs in order. Check selected-tab artwork and that
   Statistics is rightmost. No old native side controls should remain clickable outside
   the Wrath body. Blank margins and mouse-wheel input should affect only visible content.
5. In Achievements, browse Professions: native Tradeskills and custom profession cards
   should coexist. Check Classes, native subcategories, and any Unmapped Challenges.
   Verify Explorer belongs to Exploration and unrelated Adventure content is not forced
   there. A record must appear only once within its category listing.
6. Search by native/custom title and description, then cycle all three filters. Unknown
   completion must not appear as completed or incomplete. Clearing the search/filter
   should restore all available records without changing native filters.
7. Expand completed and incomplete native/custom cards, long descriptions, and earned
   custom series tiers. Scroll a large category from top to bottom. Check card positions,
   scrollbar alignment, criteria wrapping, and that no entries are clipped.
8. Inspect point shields on both completed and incomplete cards. Each card should have
   one original Wrath shield, with a readable value and point-system tooltip. Custom
   cards without genuine rewards must have no "Character Achievement" reward label or
   empty reward decoration. Native real reward descriptions must remain visible.
9. Compare Expert Alchemist `62013`'s actual numeric progress and point award with the
   native interface. Expand Explore Azeroth `62053` and follow Eastern Kingdoms `62353`.
   Verify Explorer uses the live catalog's ID rather than substituting a static mirror.
   Criteria completion alone must not grant achievement completion.
10. Check Summary's separate point totals and source completion counts. Verify recent
    custom dates against saved history. Native recent entries must have actual native
    dates; unknown/partial data must be labeled, omitted, or unavailable. Click category
    summary bars and confirm they open the intended unified category.
11. Track and untrack a custom card, then check the existing tracker and standalone
    `/fach` window. Compare saved dates, history, explored areas, and tracked keys.
    Statistics and existing standalone settings/social features should still work.
12. Open Legacy Rewards. Verify actual points, milestones, icons, reward descriptions,
    collected/available states, scrolling arrows, and tooltips against the original page.
    Use only native interactions already provided by the game; no addon claim logic exists.
13. Open Legacy Trees. Switch available trees, inspect node tooltips and selection
    popovers, and verify native unlocks, staged changes, Apply/Undo/Reset behavior.
    If testing progression changes, choose changes you actually intend to make. Switch
    tabs/close/reopen with staged changes and compare native behavior; the addon must
    not independently commit, spend, reset, or roll back progress.
14. Change UI scale and repeat Rewards/Trees and scroll checks. Enter/leave combat with
    the window open; run `/fa legacyui off` during combat and verify the chat reports any
    pending restoration, the native presentation returns when legal, and the option stays
    off. Enable again after combat.
15. Switch to gamepad mode with the window open. The original native interface and its
    normal navigation must be restored before native gamepad initialization. Close,
    reopen, and use native Rewards/Trees. Switch back to mouse and keyboard and verify
    the replacement resumes safely when enabled.
16. `/reload` while enabled, reopen normally, and verify persistence and all four tabs.
    Try another character: custom completion follows its own saved data and native scope
    follows the client. Run `/fa legacyui off`, reload, and check original native categories,
    search, Rewards, Trees, closing, and standalone features. Run `/legacyinspect` with
    native Challenges open to compare frame/provider evidence.

## Reporting problems

Report the exact chat status, client build, UI scale/resolution, category/challenge ID,
selected tab, combat/input mode, and Lua error. If a failure restores the native window,
check that Rewards and Trees remain accessible before retrying. Disable and reload,
then use `/legacyinspect` on the original Challenges page for current frame/provider
evidence. Preserve SavedVariables; no progress reset is part of troubleshooting.

Developer architecture and data/API notes:
[compatibility research](../../docs/legacy-wrath-compatibility.md) and
[build 70338 native presentation research](../../docs/iteration2-native-research.md).
