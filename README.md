# WoWAddons

ForeverAchievements iteration 6 refines the visible native Forever Legacy
System window with an experimental original-Wrath interface, disabled by default.
Native Legacy Challenges and custom achievements share one subject hierarchy;
their points, completion authority, and character/account scopes stay separate.
The four bottom tabs are **Achievements | Legacy Rewards | Legacy Trees | Statistics**.

- Enable: `/fa legacyui on`
- Restore native UI: `/fa legacyui off`
- Size presets: `/fa legacyui size compact|standard|large`
- Reset position: `/fa legacyui reset`

[Installation and manual tests](ForeverAchievements/Integrations/README.md) ·
[Compatibility and API research](docs/legacy-wrath-compatibility.md) ·
[Automated tests](tests/README.md)

Rewards and Trees use the existing native pages, original backgrounds, and interactions.
Achievement Points and Legacy Points stay separate. Gamepad mode
uses the original native interface; unsafe combat changes wait until combat ends.

Iteration 4 adds character-attributed exploration and collection observations,
known other-character names, restrained blue native completion accents, verified
native/custom exploration card relationships, direct parent-category lists,
individual class navigation, and configurable copper-normalized money tracking.
Historical completion records remain saved. Unverifiable progress stays unavailable.
See the [Iteration 4 audit and manual checks](docs/iteration4-regression-plan.md).

Iteration 5 restores the original wood-frame backing, adds a central achievement
seal, aligns header controls and footer tabs, and uses Large by default while
preserving explicitly saved size choices. The filter opens an owned dropdown;
whole parent rows select their direct list and expand/collapse. Card details omit
routine scope/unknown filler and ordinary cross-character notes, with aligned
criteria checks and plain currency progress. Native Rewards/Trees fit uniformly.
The existing 50-point `worldexplorer` key is now named Explore Azeroth; uncertain
native relationships remain separate. Historical Moonglade completion without
verified character evidence remains saved but cannot supply gold artwork or points.
See the [Iteration 5 changes and manual checks](docs/iteration5-regression-plan.md).

Iteration 6 defaults to Standard (960 × 620 body), preserving saved size choices.
It adds ornamental parent/subcategory headings, inset proportional scrollbars and
a size dropdown. Complementary masks separate the original shield and laurels:
Legacy completion alone keeps the card/shield gray with blue laurels; verified
character completion takes gold precedence. Native faction crests use compatible
client textures with a neutral fallback. Tracking, categories and progress are
unchanged. See the [Iteration 6 changes and client checklist](docs/iteration6-regression-plan.md),
including artwork limitations and the investigated `Unavailable` total.

Header dragging and size selection persist; Statistics has its own category navigation. Unsupported
daily-quest definitions are inactive while their historical saved keys remain.

Unmodified supplied Wrath sources live in References/WrathAchievementUI,
outside the runtime addon. Existing saves, tracking, and the standalone addon
window are retained. Actual in-game validation is still required.
