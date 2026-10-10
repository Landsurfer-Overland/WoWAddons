# Original Wrath achievement UI reference

These five files are the user's supplied Classic/Wrath UI sources, stored
byte-for-byte with canonical filenames. The upload suffix "(1)" was removed
from filenames only. SOURCE_HASHES.json records their byte counts and SHA-256
digests. Neither the original sources nor native Blizzard game files are modified.

They are outside the runtime addon. Their TOC (Interface 30001, Secure,
load-on-demand) is never loaded. The adapted runtime is in ForeverAchievements/UI.
Its XML is generated from this XML by tools/adapt_wrath_templates.py; the
generated result is committed and needs no Python at runtime. The runtime
Lua ports selected presentation behavior with an addon-owned namespace.
See docs/legacy-wrath-compatibility.md for the mapping and dependency changes.

These are supplied Blizzard sources, not code authored by this repository.
No new license or permission to redistribute Blizzard's sources is asserted.
No GPL or proprietary community implementation is included.
