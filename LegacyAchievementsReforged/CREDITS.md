# Credits

Legacy Achievements Reforged is maintained by Landsurfer-Overland.
Piotr contributed the initial achievement-tracking foundation.

The addon-list/minimap icon is original AI-generated artwork created for
Legacy Achievements Reforged: a gold hammer and anvil on a navy background.
The editable-size PNG is retained at
`docs/assets/legacy-achievements-reforged-icon.png` in the development repository;
`Media/icon.tga` is its uncompressed 128 × 128 RGBA client export.

`Media/ReforgedChime.wav` is an original synthesized rising bell chime created
for this project. It contains no third-party samples or Blizzard recording.
Its reproducible source is `tools/generate_reforged_chime.py`; the runtime file
is 1.8 seconds of 16-bit mono PCM at 22.05 kHz. It is labeled Reforged chime
in settings and is an explicit alternative to the client's achievement sound.

`Media/AchievementEarned.ogg` is the user-supplied `AchievmentSound1.ogg`,
associated with Blizzard's [UI_ALERT_ACHIEVEMENTGAINED sound, kit 12891](https://www.wowhead.com/sound=12891/ui-alert-achievementgained).
It is retained byte-for-byte and is not original project audio. The recording
is 5.19 seconds of mono Vorbis audio at 22.05 kHz; SHA256:
`8494d51c69bfc1eadd1774a9be89d2a0600122e5bd2a7fff2a08c58184bb6d7d`.

Bundled LibStub, CallbackHandler-1.0, LibDataBroker-1.1 and LibDBIcon-1.0 retain
their authorship and license notices in their source files.

The achievement interface adapts supplied Blizzard Wrath UI templates and uses
client-provided textures. Reference source files and their original hashes are
retained separately in the development repository. No ownership of Blizzard
artwork or third-party libraries is claimed by this project name change.
