"""A-weighted level timeline of a WAV recording, in dBFS.

Used to measure the Efficienado Reference Box: record the box and a known
reference source (an appliance with a published dB figure) at the same
distance and gain, then anchor the dBFS readings to the published level.
The measured levels live in params.json under noise.reference_box_measured_2026-09-07.

Usage:
    python3 sound_level.py recording.wav [more.wav ...]

Prints, for every 5 s block, the mean, minimum and maximum one-second A-weighted
level in dBFS.  Requires numpy and scipy.  Input must be 16-bit PCM WAV; stereo
files are averaged to mono.
"""
import sys
import wave

import numpy as np
from scipy.signal import bilinear, lfilter


def a_weighting(fs):
    """Digital A-weighting filter (b, a) for sample rate fs, from the IEC 61672 analog prototype."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    A1000 = 1.9997
    num = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20)), 0, 0, 0, 0]
    den = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2], [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    den = np.polymul(np.polymul(den, [1, 2 * np.pi * f3]), [1, 2 * np.pi * f2])
    return bilinear(num, den, fs)


def load(path):
    """Return (sample rate, mono float samples in -1..1) for a 16-bit PCM WAV file."""
    w = wave.open(path)
    fs, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
    x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return fs, x


def levels(path, win=1.0):
    """Per-window RMS levels in dBFS: (A-weighted, unweighted)."""
    fs, x = load(path)
    b, a = a_weighting(fs)
    xa = lfilter(b, a, x)
    n = int(fs * win)
    m = len(x) // n
    z = xa[:m * n].reshape(m, n)
    zz = x[:m * n].reshape(m, n)
    la = 20 * np.log10(np.sqrt((z ** 2).mean(axis=1)) + 1e-12)
    lz = 20 * np.log10(np.sqrt((zz ** 2).mean(axis=1)) + 1e-12)
    return la, lz


def main(paths):
    for p in paths:
        la, lz = levels(p)
        print(p.replace("\\", "/").split("/")[-1], "seconds:", len(la))
        for i in range(0, len(la), 5):
            seg = la[i:i + 5]
            print(f"{i:4d}s  A {seg.mean():6.1f} dBFS (min {seg.min():6.1f} max {seg.max():6.1f})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
