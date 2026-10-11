#!/usr/bin/env python3
"""Export the project's original rising bell chime as client-compatible PCM WAV.

No sampled audio or Blizzard sound assets. Standard library only; run from any
directory. Runtime playback reads the exported file, never synthesizes audio.
"""
from array import array
import math
from pathlib import Path
import wave

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'LegacyAchievementsReforged/Media/ReforgedChime.wav'
RATE = 22050
DURATION = 1.8


def generate(output=OUTPUT):
    # Original four-note rising C-major arpeggio with fading bell harmonics.
    notes = [(0, 523.251), (.10, 659.255), (.20, 783.991), (.30, 1046.502)]
    samples = []
    for i in range(round(RATE * DURATION)):
        time = i / RATE
        value = 0.0
        for start, frequency in notes:
            elapsed = time - start
            if elapsed < 0:
                continue
            attack = min(1.0, elapsed / .006)
            envelope = attack * math.exp(-elapsed * 3.8)
            phase = 2 * math.pi * frequency * elapsed
            value += envelope * (math.sin(phase) + .25 * math.sin(2.01 * phase)
                                 + .09 * math.sin(4.02 * phase))
        # Smooth tail to exact silence rather than cutting the last waveform.
        value *= min(1.0, max(0.0, (DURATION - time) / .18))
        samples.append(value)
    gain = .8 * 32767 / max(abs(value) for value in samples)
    pcm = array('h', (round(value * gain) for value in samples))
    import sys
    if sys.byteorder != 'little':
        pcm.byteswap()
    with wave.open(str(output), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(RATE)
        audio.writeframes(pcm.tobytes())
    return output


if __name__ == '__main__':
    print(generate())
