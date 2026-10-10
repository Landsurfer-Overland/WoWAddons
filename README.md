# WoWAddons

ForeverAchievements iteration 4 refines the visible native Forever Legacy
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
Character Achievement Points and Legacy Points stay separate. Gamepad mode
uses the original native interface; unsafe combat changes wait until combat ends.

Iteration 4 adds character-attributed exploration and collection observations,
known other-character names, restrained blue native completion accents, verified
native/custom exploration card relationships, direct parent-category lists,
individual class navigation, and configurable copper-normalized money tracking.
Historical completion records remain saved. Unverifiable progress stays unavailable.
See the [Iteration 4 audit and manual checks](docs/iteration4-regression-plan.md).

The default Standard layout provides more vertical room. Header dragging and
size selection persist; Statistics has its own category navigation. Unsupported
daily-quest definitions are inactive while their historical saved keys remain.

Unmodified supplied Wrath sources live in References/WrathAchievementUI,
outside the runtime addon. Existing saves, tracking, and the standalone addon
window are retained. Actual in-game validation is still required.
