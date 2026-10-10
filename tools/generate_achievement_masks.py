#!/usr/bin/env python3
"""Generate complementary alpha masks for the original Wrath point artwork.

The client retains all artwork. These addon-owned masks divide the 64x64 upper
shield quadrant into its central shield and surrounding laurel; no source image
is copied or modified. Both masks are intentionally binary and complementary.
Geometry was inspected against the public 128x128 UI-Achievement-Shields and
UI-Achievement-Shields-NoPoints reference sheets. Actual Forever rendering still
requires in-game confirmation. This script uses only the Python standard library.
"""
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SIZE = 64
# Keep the complete central shield, including its metallic rim, neutral. The
# laurel mask cannot cover the point-lettering column or the lower shield tip.
SHIELD = ((16, 9), (19, 12), (31, 17), (42, 12), (46, 9),
          (46, 31), (45, 35), (41, 41), (31, 49), (21, 42),
          (17, 36), (16, 31))


def inside(x, y):
    contained = False
    previous = SHIELD[-1]
    for current in SHIELD:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            contained = not contained
        previous = current
    return contained


def generate():
    # Uncompressed, top-origin RGBA TGA: WoW supports this power-of-two format.
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 0x28)
    shield, wreath = bytearray(), bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            alpha = 255 if inside(x + .5, y + .5) else 0
            shield.extend((255, 255, 255, alpha))
            wreath.extend((255, 255, 255, 255 - alpha))
    dest = ROOT / 'ForeverAchievements/Media'
    dest.mkdir(parents=True, exist_ok=True)
    for name, pixels in [('Achievement-Shield-Mask.tga', shield), ('Achievement-Wreath-Mask.tga', wreath)]:
        (dest / name).write_bytes(header + pixels)
        print('Generated', (dest / name).relative_to(ROOT))


if __name__ == '__main__':
    generate()
