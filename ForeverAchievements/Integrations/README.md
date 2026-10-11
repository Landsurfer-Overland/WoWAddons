# Unified Wrath Legacy interface — iteration 6

Install the complete `ForeverAchievements` folder in the active Forever client's
`Interface/AddOns` directory, replacing the previous addon files. Keep your
existing `WTF/SavedVariables` files. No progress reset is required.
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
- `/fa progressdebug on|off|status|dump` controls progression diagnostics, disabled by default.
- `/fa perf on|off|report|reset` controls bounded session performance diagnostics, off by default.
- `/fa money report` reports observed/lifetime money sources, units and the custom copper thresholds.
- `/fa money threshold KEY COPPER` configures one custom money target; the loot tiers must stay increasing.
- `/fa inspectachievement KEY` reports this character's saved state and current condition evidence.
- `/fa correctachievement KEY` previews a correction and provides a short-lived confirmation token.
- `/fa correctachievement KEY confirm TOKEN` corrects only that key on this character.
- `/fa correctachievement KEY resume`, then `/fa correctachievement KEY resume confirm TOKEN`, explicitly permits future verified earning of that corrected key.

The feature is disabled by default. The account option, selected size, and dragged
position persist across reloads. Standard is the initial size; every valid saved
size preference remains respected. The footer dropdown selects Compact, Standard
or Large. Size presets enlarge
usable content space while retaining fixed decorative corners and classic artwork;
the window fits the available screen. Use the header to drag it and reset if needed
after a resolution or UI-scale change. The original standalone window, its minimap
launcher, welcome popup and comparison menu are quarantined. Bare `/fa`, `/fach`
and `/qa` report this rather than opening the alpha window. Their named commands
still work. Character tracking, toasts, chat-link tooltips, comparison data and
original saved keys remain; the old settings view is retained in source for later
migration. See the [quarantine and recovery notes](../../docs/original-ui-quarantine.md).

| Preset | Logical body dimensions |
| --- | --- |
| Compact | 768 × 500 |
| Standard | 960 × 620 |
| Large | 1024 × 720 |

Roof/footer space is additional; the complete window scales down when needed to
fit UIParent. Presets resize content and border strips; continuous resizing is
not provided for the original artwork.

## Achievements and progression

The bottom tabs remain **Achievements | Legacy Rewards | Legacy Trees | Statistics**.
The complete visible window uses the Wrath roof, borders, parchment, and close button.
Native outer artwork and side tabs are temporarily suppressed.

Achievements has one subject hierarchy. Populated subcategories organize character
progression, quests, geography, individual professions, dungeons/raids, reputation,
PvP, supported classes, and special achievements. Selecting a parent lists only
records assigned directly to it; its completion count can include descendants.
General profession and broad reputation milestones belong in their parent categories.
Clicking a whole parent row selects its directly assigned achievements and toggles
its children. The plus/minus button toggles children without changing selection.
Leaf rows select their own list; the selected row has a green highlight.

Unknown native mappings appear under **Feats of Strength → Other Legacy Challenges**.
That is a navigation location only: the record retains its real type, points, scope,
reward, native ID, and completion. There is no separate Unmapped Challenges root and
no Daily Quests category. Historical unsupported daily keys remain saved but inactive.

Native Legacy completion and rewards come from the game. Custom completion follows
original character SavedVariables. Zone records with verified matching stable IDs
and complete requirements share a presentation card, with independent custom/native
components. Unverified or different requirements remain separate; repeated instances
of the same namespaced identity are removed from a listing. The original 50-point
custom `worldexplorer` record is now displayed as Explore Azeroth, with its existing
ID, criteria and history. Its native 62053 counterpart remains separate in World
Exploration until the complete zone sets and relationships are verified as equivalent.
Gold artwork identifies verified current-character completion; restrained blue
indicators identify native completion. Routine card details omit scope labels and
unknown-state filler. Known previous-character names appear only where linked
Legacy/account completion is relevant. Another character's completion never
changes this character's custom completion, date, points, or completed artwork.
Historical account snapshots without reliable character identity do not establish
who earned an achievement.
Current custom completion uses gold. Native completion alone keeps the card and
central shield gray and colors only its separate laurel layer blue, with a subtle
`Completed via Legacy` label. Character gold takes precedence over Legacy blue.
A merged card retains character completion separately, including when native
progress is complete and this character's custom achievement is incomplete. Reliable
other-character history for Legacy-linked cards names its recorded earner without
granting character points.
The standalone account overview shows verified character snapshots and labels
unreliable totals `Unavailable`. Its old account-union toggle is removed; the stored
preference and historical records remain preserved. Malformed timestamps do not
appear as earned recent achievements or count toward a new meta completion.

The header is the main location for separate **Achievement Points** and
**Legacy Points**. They are never added together. Cards use their actual point system
and achievement type; zero points alone never means Feat of Strength. Point
tooltips distinguish the independent custom and native awards. Unknown shields use
`?`, unknown header totals use `Unavailable`, and point tooltips use a dash rather
than inventing Legacy rewards. A confirmed native zero
award retains numeric 0 with a no-point-reward tooltip and neutral ordinary shield;
it does not advertise a Legacy Point award or imply a Feat. A zone's custom points do
not inherit a native meta-achievement's Legacy award. Cards without real rewards leave
the reward text and decoration blank. The older standalone alpha view retains older
native imports with synthetic addon points, so its totals can differ.

Summary starts with compact source completion bars, then up to six reliable recent
custom/native achievements in one section and category progress. Native partial collections
are labeled; unavailable native dates
are not fabricated. Expand cards for criteria and follow linked meta-achievements.
Click the expanded card again to collapse it; opening another card collapses the
previous one. The icon, card height, surrounding rows, and valid scroll position update
without selecting a native challenge just to collapse a card.
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

The [Iteration 4 audit and manual checks](../../docs/iteration4-regression-plan.md)
describe character attribution, relationship uncertainty, and monetary tuning.

The native root remains a registered UI panel with its original width reservation,
so spacing beside other open panels can retain native dimensions despite smaller
visible artwork. Gamepad mode uses the original native interface because its
SmartNavigation expects the original three pages and controls. Mouse-and-keyboard
mode can resume the replacement.

Missing/incompatible native frames and presentation errors restore native access.
Combat or newly protected frames can defer required restoration; the chat reports
pending work, which retries when legal. Disabling records the option immediately.
No native progression state is changed to force a restoration.

Native catalog reads are bounded at 256 category-information attempts, 2500 challenge
attempts, and 256 criteria per card. Exploration relationship validation has a separate
shared 256-attempt budget per native snapshot; unverified pairs stay separate and are
retried only on a later real data refresh. Larger/unavailable results are labeled.
English subject recognition cannot
reliably classify every localized or new native category; uncertain IDs remain in
Other Legacy Challenges for future review.

Full Questie/Loremaster integration is deferred. Existing guarded completion-ID and
optional quest-database checks remain; missing data does not establish a complete
quest history or a fabricated count. Standalone cards, sorting, the tracker, and social
tooltips show unavailable quest/Loremaster progress without a filled progress bar;
confirmed zero remains zero. Unsupported daily tracked keys stay saved but hidden.
Custom monetary targets now use configurable Forever defaults with explicit copper
normalization. `/fa money report` distinguishes verified lifetime totals from dated
observations and retains the original raw source for diagnosis. Older unverified money
counters remain saved but cannot fabricate a lifetime baseline.
See [classification and data audit](../../docs/iteration3-achievement-audit.md) and
[compatibility/API notes](../../docs/legacy-wrath-compatibility.md).

Pet and collection-mount achievements now require classified items positively observed
in this character's bags; shared/unscoped journal counts and older cached maxima do not
grant custom completion. Learned collections acquired before reliable observation
cannot be reconstructed from an account journal. Existing genuine completion stays saved.
New exploration observations require this character's presence in the named area,
verified current-map identity and a genuine revealed overlay. Where the full discovered
area-at-position API is available, it must also confirm the required area. Hover previews,
remote map reads, zone entry alone, and old unattributed visits do not grant missing
completions. Validated fallback maps retain their actual zone name and overlay dimensions
as proof. Old observations remain saved; uncertain areas may need revisiting.
Meta children require finite positive current-character completion timestamps;
malformed history remains unknown and saved. The reported historical Moonglade
family also requires verified character attribution or owning local discovery
evidence before it supplies completed artwork or points. Unverified history stays
saved; genuine re-verification preserves its original date.
`Going Down?` requires a measured, continuous 65-yard fall and verified survival after
landing; elapsed falling time alone is insufficient. Unavailable evidence cannot award
these achievements. Previously saved completion remains intact.

Inspect `pet1`, `explore855`, or `fall` when investigating a suspect record; inspection
does not award completion. Diagnostic enablement persists across reloads, while its
64-record trace is session-only. A targeted correction requires its explicit confirmation
token within 60 seconds, on the same verified character and unchanged original record.
It archives that key's completion timestamp and identity in character correction history,
clears only that completion, and places that key on a reaward hold. All source evidence,
history, other achievements, and native progression stay intact. Use the separately
confirmed `resume` form to lift only that hold; a later normal check may then earn the
key from verified evidence. Correction is optional and never runs automatically.
The older `/fach reset` directs you to this targeted flow instead of wiping progress.

## Manual in-game test plan

Use the [Iteration 6 checklist](../../docs/iteration6-regression-plan.md#manual-in-game-checklist)
for current sizing, headings, scrollbars, menus and completion artwork. Its texture
limits and `Unavailable` investigation are documented alongside the checks.
The [Iteration 5 checklist](../../docs/iteration5-regression-plan.md#manual-client-checklist)
retains the historical Moonglade and progression checks.

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
   and its geography children. Parent lists contain only direct assignments;
   parent counts can include descendants. Whole parent rows also toggle children,
   while plus/minus buttons toggle without changing the selected list.
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
   Check independent custom/native points and blue/gold completion. Routine scope
   and unknown-state filler stays absent; criteria alone must not grant completion.
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

### Two-character progression regression

Use two characters, A with genuine recorded accomplishments and B without the relevant
custom accomplishment. Back up existing SavedVariables; do not reset them for testing.

1. On A, inspect `pet1`, `explore855`, and `fall` and record genuine completions, dates,
   character points, native Legacy state, and identity. Log out normally to save a snapshot.
2. On B, enable progression diagnostics, reload, and open the panel immediately. Account
   pet ownership, old cached maxima, and A's history must not newly grant B's custom
   achievements. Check the recorded triggering event, character, values, and condition.
3. Compare a custom exploration achievement incomplete on B with its native Legacy
   counterpart completed elsewhere. Native completion must remain visible; the custom
   card must retain B's incomplete state and points. An elsewhere detail needs reliable
   saved identity; account-wide native completion must not invent an earning character.
4. On B, inspect previously visited and unvisited zones, especially Moonglade. Hover
   preview art and entering a zone must not establish its full exploration criteria.
   Verify genuine revealed evidence separately. Do not perform dangerous falls solely
   to test; ordinary movement, flight/taxi transitions, and reloads must not award `fall`.
5. Expand, collapse, and switch cards, including a linked meta entry. Check `+`/`−`, row
   height, surrounding entries, and scrolling. Reload, log out/in, then return to A;
   genuine dates, completions, points, and character evidence must survive.
   Check the standalone account overview: only verified snapshots appear, unavailable
   totals are labeled, and no account-union toggle or malformed recent date appears.
6. If a known false record needs correction, inspect and preview only its intended key.
   Confirm only with the displayed token on that character. Verify the archive, preserved
   source/history/other achievements/native progression, and the corrected key's reaward
   hold. Resume only that key through its separate confirmation when intended. Turn
   diagnostics off after capturing the result.

## Reporting

For intermittent timeouts, run `/fa perf on` before opening the window, then exercise
close/reopen, all four tabs, scrolling, search/filter changes, and size presets. Verify
ordinary earned progress, zone/bag updates, native criteria, and Legacy currency still
refresh live values. Test closing/disabling with pending work and combat/input-mode
fallback. Capture `/fa perf report`, then `/fa perf off`. Reports contain bounded timing
and count aggregates, with explicit unavailable clocks; they do not collect individual
call traces or change saved progression. Collection is off after reload. See
[stability findings and performance test steps](../../docs/legacy-ui-performance.md).

Include chat status, client build, UI scale/resolution, size preset, tab, selected
category/challenge ID, combat/input mode, and Lua error. Preserve SavedVariables;
no reset is part of troubleshooting. Disable/reload and compare original native
behavior before retrying. Backend and native presentation sources are documented in
[compatibility notes](../../docs/legacy-wrath-compatibility.md) and the historical
[70338 native research](../../docs/iteration2-native-research.md).
