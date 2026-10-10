# Unified Wrath Legacy interface — iteration 3

Install the complete `ForeverAchievements` folder in the active Forever client's
`Interface/AddOns` directory, replacing the previous addon files. Keep your
existing `WTF/SavedVariables` files. No progress reset or migration is required.
Original Wrath reference files belong in the repository, outside the installed
addon and the native Blizzard addon directories.

## Commands

- `/fa legacyui on` enables the replacement for normal Legacy System opening.
- `/fa legacyui off` restores the original presentation when safe.
- `/fa legacyui size compact|standard|large` selects a saved size preset.
- `/fa legacyui reset` resets the saved window position.
- `/fa legacyui unmapped` reports observed IDs using the navigation fallback.
- `/fa legacyui` shows status/help.
- `/fach` and `/qa` also accept these `legacyui` commands.
- `/legacyinspect` remains the manual read-only inspector.

The feature is disabled by default. The account option, selected size, and dragged
position persist across reloads. Standard is the initial size. Size presets enlarge
usable content space while retaining fixed decorative corners and classic artwork;
the window fits the available screen. Use the header to drag it and reset if needed
after a resolution or UI-scale change. The existing standalone `/fach` window,
character tracker, settings, social features, and original saved keys remain available.

| Preset | Logical body dimensions |
| --- | --- |
| Compact | 768 × 500 |
| Standard | 900 × 620 |
| Large | 1024 × 720 |

Roof/footer space is additional; the complete window scales down when needed to
fit UIParent. Presets resize content and border strips; continuous resizing is
not provided for the original artwork.

## Achievements and progression

The bottom tabs remain **Achievements | Legacy Rewards | Legacy Trees | Statistics**.
The complete visible window uses the Wrath roof, borders, parchment, and close button.
Native outer artwork and side tabs are temporarily suppressed.

Achievements has one subject hierarchy. Populated subcategories organize character
progression, quests, geography, primary professions, Fishing, Cooking, First Aid,
dungeons/raids, reputation, PvP, class challenges, and special achievements. Select a
parent to see all relevant descendants once; select a child for that narrower subject.
Expansion and selection are independent, and the selected row has a green highlight.

Unknown native mappings appear under **Feats of Strength → Other Legacy Challenges**.
That is a navigation location only: the record retains its real type, points, scope,
reward, native ID, and completion. There is no separate Unmapped Challenges root and
no Daily Quests category. Historical unsupported daily keys remain saved but inactive.

Native Legacy completion and rewards come from the game. Custom completion follows
original character SavedVariables. Similar custom/native accomplishments, zone
achievements, parent meta-achievements, and progression tiers remain distinct; repeated
instances of the same namespaced identity are removed from a listing.

The header is the main location for separate **Character Achievement Points** and
**Legacy Points**. They are never added together. Cards use their actual point system
and achievement type; zero points alone never means Feat of Strength. Point and scope
tooltips distinguish Character, Account, and unknown metadata. Unknown awards show
`?` or `Unavailable`, rather than invented Legacy rewards. A confirmed native zero
award retains numeric 0 with a no-point-reward tooltip and neutral ordinary shield;
it does not advertise a Legacy Point award or imply a Feat. A zone's custom points do
not inherit a native meta-achievement's Legacy award. Cards without real rewards leave
the reward text and decoration blank. The older standalone alpha view retains older
native imports with synthetic addon points, so its totals can differ.

Summary starts with compact source completion bars, then up to six reliable recent
custom/native achievements in one section and category progress. Native partial collections
are labeled; unavailable native dates
are not fabricated. Expand cards for criteria and follow linked meta-achievements.
Custom tracking delegates to the original tracker. Search and completion/source filters
operate locally within the selected subject; they do not change the native search state.
Search includes titles, descriptions, category metadata, and criteria already loaded
by expanding an entry. It does not scan every unloaded objective. The clear button
resets both query and filter. Available filters are All, Completed, Incomplete,
Character Achievements, and Legacy Challenges; one filter is selected at a time.

Legacy Rewards and Legacy Trees retain their **original native backgrounds** within
the shared Wrath outer frame. Existing native page parents, subtrees, and handlers remain
intact. Milestones, icons, tooltips, available-point calculations, tree selection,
Apply/Undo/Reset, and any native reward interactions remain the game's functionality.
The addon performs no independent reward claims or trait spending.

Statistics has its own sidebar and selection. It groups actual client statistics and
addon-recorded character observations by subject, with populated children where useful.
A genuine `0` remains zero; absent/unsupported values show `Unavailable`. Local counters
describe observations since addon installation, not reconstructed lifetime totals.
Statistics and Achievements keep separate navigation state.

## Compatibility and limits

Target: Forever `1.60.1 / 70338`, Interface `16001`, project `18`, Lua `5.1`.
No actual in-game validation has been performed for these changes.

The iteration 3 brief refers to four newer screenshots and a generated mockup, but
those images were not attached to this request. Implementation uses the original
Wrath sources, existing references, and the written brief; no mockup review is claimed.

The native root remains a registered UI panel with its original width reservation,
so spacing beside other open panels can retain native dimensions despite smaller
visible artwork. Gamepad mode uses the original native interface because its
SmartNavigation expects the original three pages and controls. Mouse-and-keyboard
mode can resume the replacement.

Missing/incompatible native frames and presentation errors restore native access.
Combat or newly protected frames can defer required restoration; the chat reports
pending work, which retries when legal. Disabling records the option immediately.
No native progression state is changed to force a restoration.

Native catalog reads are bounded at 256 categories, 2500 challenges, and 256 criteria
per card; larger/unavailable results are labeled. English subject recognition cannot
reliably classify every localized or new native category; uncertain IDs remain in
Other Legacy Challenges for future review.

Full Questie/Loremaster integration is deferred. Existing guarded completion-ID and
optional quest-database checks remain; missing data does not establish a complete
quest history or a fabricated count. Standalone cards, sorting, the tracker, and social
tooltips show unavailable quest/Loremaster progress without a filled progress bar;
confirmed zero remains zero. Unsupported daily tracked keys stay saved but hidden.
Complex money/progression chains remain unchanged.
See [classification and data audit](../../docs/iteration3-achievement-audit.md) and
[compatibility/API notes](../../docs/legacy-wrath-compatibility.md).

## Manual in-game test plan

Automated/static checks cannot validate game assets, protected UI, real native
progression, or SavedVariables disk writes. Keep your existing saves and record errors
at normal and smaller UI scales. Avoid irreversible claims or trait commits solely
for testing.

1. Leave combat, enable, and open Legacy using its usual control. Check one complete
   Wrath window, all four bottom tabs, and no old black outer rectangle/portrait/side tabs.
   Close/reopen repeatedly with the close button, Escape, and normal game toggle.
2. Drag the header, close/reopen, and `/reload`. Confirm saved position and enable state.
   Select Compact, Standard, and Large; compare visible cards, Summary height, sidebar,
   scrollbars, native-page viewports, and bottom tabs. Larger presets must increase space.
3. Change screen resolution/UI scale and verify the window stays reachable. Run reset.
   Open another normal UI panel and check its layout/closing alongside Legacy.
4. Expand/collapse parent and child categories. Select Professions and compare its list
   with Fishing, Cooking, First Aid, and primary-profession children. Select Exploration
   and its geography children. Parents must include all descendants without repeated IDs.
5. Check root/child indentation, backgrounds, text prominence, and green selection.
   Refresh progress or switch tabs and return: the selected category and expansion
   should remain stable, with only the selected row highlighted.
6. Inspect Other Legacy Challenges under Feats. Confirm fallback entries retain their
   actual achievement type and point-system tooltip. Record ambiguous IDs/categories
    for future mapping using `/fa legacyui unmapped` after opening the enabled window.
    The report shows at most 30 IDs; the full observed list remains in the view model.
    No Daily Quests category or active daily achievements should appear.
7. Inspect native Explore Azeroth `62053`: actual Legacy award or unavailable state,
   native completion/progress, correct Exploration location, and no Feat icon merely
   because the award is zero/missing. Follow Eastern Kingdoms `62353` where available.
8. Inspect Desolace, Darkshore, Elwynn Forest, and Westfall custom zone achievements.
   Verify valid character points, geography, saved dates, and independent native/meta
   entries. Distinct accomplishments may coexist; the same identity must not repeat.
9. Compare Expert Alchemist `62013`'s progress/award against the native interface.
   Expand completed/incomplete cards, long criteria, series tiers, and linked metas.
   Check Character/Account/unknown scope. Criteria alone must not grant completion.
10. Check ordinary character, Legacy, and genuine Feat shields: one correctly positioned
    icon/value, completed/incomplete styling, and appropriate tooltips. Zero-point
    standard records must not acquire Feat artwork. Absent rewards leave no text/decoration.
11. Search custom/native titles, descriptions, and available category metadata. Combine
    completion/source filters with parent/child selection, clear/reset, and switch
    categories with a query active. Results must stay relevant and identity-unique.
12. Check separate live header totals, compact Summary completion bars, partial/unknown
    labels, actual recent dates, and category bars. Scroll to the last entry; verify no
    clipped cards, overlapping header art, or redundant large point-total headings.
13. Track/untrack a custom card and check the original tracker and standalone `/fach`
    window. Compare saved history, dates, explored areas, point values, and tracked keys.
    Check unavailable quest/Loremaster progress in cards, sorting, the tracker, and social
    tooltips: no Lua error or fabricated zero/fill. Confirm real zero remains visible
    and old daily tracked keys remain saved without appearing as active objectives.
14. Open Legacy Rewards: original native inner background, milestones, points, icons,
    native state/tooltips, and scrolling interactions. Do not claim rewards just to test.
15. Open Legacy Trees: original native background, centered nodes/connections, usable
    selection/search, available-point indicator, and accessible Apply/Undo/Reset.
    Inspect tooltips; compare staged edits across tab switching/closing to native behavior.
    Do not commit/reset progression solely to test.
16. Open Statistics and browse parents/children. Verify right-panel values and alignment,
    genuine zero versus unavailable, money/name formatting, and recorded-counter labels.
    Switch back to Achievements and confirm its independent category selection returns.
17. Enter/leave combat while open; disable in combat and check any pending-restoration
    message. Native presentation must return when legal and the option stay off. Enable
    after combat. Switch to gamepad and test native navigation, then return to keyboard.
18. Reload while enabled and repeat tab checks. Try another character: custom completion
    remains character-specific and native scope follows client metadata. Disable/reload
    and verify original Challenges, Rewards, Trees, search/filters, normal closing, and
    standalone features. Use `/legacyinspect` with native Challenges open for evidence.

## Reporting

Include chat status, client build, UI scale/resolution, size preset, tab, selected
category/challenge ID, combat/input mode, and Lua error. Preserve SavedVariables;
no reset is part of troubleshooting. Disable/reload and compare original native
behavior before retrying. Backend and native presentation sources are documented in
[compatibility notes](../../docs/legacy-wrath-compatibility.md) and the historical
[70338 native research](../../docs/iteration2-native-research.md).
