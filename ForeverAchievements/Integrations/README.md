# Experimental Wrath Legacy interface

Install the complete ForeverAchievements folder in the active Forever
client's Interface/AddOns folder, replacing the previous addon files.
Keep existing WTF/SavedVariables files. Version: 0.4.6-alpha-legacyui.
There is no progress reset or migration. The reference files belong in
the repository, outside the game and native Blizzard addon directories.

## Commands

- /fa legacyui on enables the overlay in the normal native Challenges page.
- /fa legacyui off hides it and restores the native presentation immediately.
- /fa legacyui shows status/help.
- /fach and /qa also accept legacyui on/off through the existing dispatcher.
- /legacyinspect remains the manual read-only inspector.

Disabled by default; the account setting persists. Open the normal Legacy
window and its existing Challenges tab. No additional native tab or separate
Wrath window is created. Native close, Rewards and Legacy Tree remain intact.
The existing standalone /fach window and other addon features are preserved.

The sidebar separates Legacy Challenges and Character Achievements. Click
parents to expand/collapse and cards to show criteria. Linked meta criteria
open referenced achievements within this UI. Search matches names/descriptions;
the filter button cycles All/Complete/Incomplete locally. Achievements and
Statistics buttons are inside the cover. Custom tracking uses the existing
character tracker; native tracking and reward claims are unchanged.

The roof shows character achievement points; a separate label shows native
account Legacy Points. Native shields use actual trait-currency point awards.
Unavailable values are "?" / "Unavailable". The old alpha UI includes native
imports with synthetic addon point values, so its totals can differ.

## Twelve-step manual test in client 1.60.1 / 70338

No actual client testing has been performed. Record failures/screenshots at
your normal UI scale and one different scale.

1. Leave combat; run /fa legacyui on. Check chat status. No new top-level
   window should open.
2. Open the normal Legacy System using its usual game control. Verify its
   native window and close button still work.
3. Select the existing Challenges tab. Confirm no extra native tab was added.
4. Check the Wrath roof, parchment, sidebar, cards, shields and green bars
   fit within the page. Click blank margins and wheel-scroll: hidden native
   controls must not fire. Try the native close button.
5. Browse native and custom categories, including a native parent with its
   own records plus subcategories. Search and cycle each filter.
6. Expand completed/incomplete cards, long descriptions and earned custom
   series tiers. Scroll a large category from top to bottom; verify row clicks
   and scrollbar thumb/viewport stay aligned.
7. Compare Expert Alchemist 62013's numeric 0/225 progress and point reward
   with native values. Expand Explore Azeroth 62053 and follow Eastern
   Kingdoms 62353. Check Explorer uses your native category's ID, not a static
   mirror. Compare completion dates and unknown-data labels. Criteria alone
   must not grant completion. Track a custom card and check the old tracker.
8. Switch to native Rewards, then Legacy Tree. The cover must disappear.
   Check the original points, rewards and tree. This port adds no claim/spend
   buttons; use the native controls as usual.
9. Close/reopen, return to Challenges, change UI scale and verify the cover
   fits and native controls work. Enter/leave combat: the cover should hide
   and resume safely.
10. /reload while enabled and reopen Challenges; the cover should return.
    Check saved dates, history, exploration and tracked custom keys. Try a
    second character: custom completion follows its own data, native scope
    follows the client. Check Statistics and the old /fach window.
11. /fa legacyui off should remove the cover immediately, including after
    a failure or in combat. Reload; the option must stay disabled.
12. Browse, search and expand original native Challenges; switch Rewards/Tree,
    close/reopen and run /legacyinspect. Native filters, rewards/progression,
    standalone features and custom saved progress must match their prior state.

## Fallback and reporting

If attachment waits for a frame, leave combat, open native Challenges and
repeat /fa legacyui on. Protected frames or initialization/render errors
hide the cover and report fallback. After an initialization failure, disable
and reload before retrying.

Report the exact chat status, client build, UI scale, category/challenge ID,
native tab, combat state and Lua error. Disable and run /legacyinspect on
the native page to capture current frame/provider evidence.

Assets, pixel fidelity, actual tab/events, combat taint and disk persistence
still need client validation. Missing backend data is labeled. Bounds:
256 categories / 2500 native challenges / 256 criteria per card; larger results
are visibly partial. Rewards/claims remain in the native page.

Developer provenance, architecture and API notes:
docs/legacy-wrath-compatibility.md in the repository.
