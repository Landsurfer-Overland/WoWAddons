# WoWAddons

ForeverAchievements iteration 2 replaces the visible native Forever Legacy
System window with an experimental original-Wrath interface, disabled by default.
Native Legacy Challenges and custom achievements share one category hierarchy.
The four bottom tabs are **Achievements | Legacy Rewards | Legacy Trees | Statistics**.

- Enable: `/fa legacyui on`
- Restore native UI: `/fa legacyui off`

[Installation and manual tests](ForeverAchievements/Integrations/README.md) ·
[Compatibility and API research](docs/legacy-wrath-compatibility.md) ·
[Automated tests](tests/README.md)

Rewards and Trees use the existing native pages and their original interactions.
Character Achievement Points and Legacy Points stay separate. Gamepad mode
uses the original native interface; unsafe combat changes wait until combat ends.

Unmodified supplied Wrath sources live in References/WrathAchievementUI,
outside the runtime addon. Existing saves, tracking, and the standalone addon
window are retained. Actual in-game validation is still required.
