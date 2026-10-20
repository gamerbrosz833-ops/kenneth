"""Sound for the 12 s reel "Signal over noise". Everything is synthesized here
(no third-party samples) and written to assets/score.wav, aligned to the
timeline beats in index.html (T1 3.4, T2 6.0, T3 7.6, T4 9.9).

    python -I tools/score.py        (from reel/)
"""
import os

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
END = 12.0
N = int(END * SR)
rng = np.random.default_rng(521)
T1, T2, T3, T4 = 3.4, 6.0, 7.6, 9.9

dry = np.zeros((2, N))
wet = np.zeros((2, N))


def tt(d):
    return np.arange(int(d * SR)) / SR


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, min(fc, SR * 0.45), 'low', fs=SR, output='sos'), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR * 0.45)], 'band', fs=SR, output='sos'), x)


def env(n, a, r):
    e = np.ones(n)
    a, r = int(a * SR), int(r * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def add(x, start, gain=1.0, pan=0.0, rev=0.0):
    i = int(start * SR)
    if i >= N:
        return
    x = x[: N - i]
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    dry[0, i:i + len(x)] += x * gain * l
    dry[1, i:i + len(x)] += x * gain * r
    wet[0, i:i + len(x)] += x * gain * rev * l
    wet[1, i:i + len(x)] += x * gain * rev * r


def tick(freq=3200, d=0.04):
    t = tt(d)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 140)
    x += bp(rng.standard_normal(len(t)), freq * 0.7, freq * 1.4) * np.exp(-t * 220) * 0.4
    return x


def bell(m, d=3.5):
    t = tt(d)
    f = mtof(m)
    x = np.zeros_like(t)
    for ratio, amp, dec in [(1, 1.0, 1.6), (2.76, 0.35, 3.2), (5.4, 0.16, 5.0), (8.93, 0.06, 7.0)]:
        x += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec)
    return x * env(len(t), 0.004, 0.4)


def swell(d, lo, hi, curve=2.0):
    t = tt(d)
    n = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = int(0.05 * SR)
    for s in range(0, len(t), seg):
        k = (s / len(t)) ** curve
        fc = lo + (hi - lo) * k
        out[s:s + seg] = bp(n[max(0, s - 2000):s + seg], fc * 0.6, fc * 1.5)[-len(out[s:s + seg]):]
    return out * (t / d) ** 1.6 * env(len(t), 0.0, 0.06)


def pad(notes, d, cutoff=900):
    t = tt(d)
    x = np.zeros_like(t)
    for m in notes:
        f = mtof(m)
        for det in (-0.12, 0.0, 0.11):
            ph = rng.uniform(0, 2 * np.pi)
            x += signal.sawtooth(2 * np.pi * f * (1 + det / 100) * t + ph) * 0.33
    return lp(x, cutoff, 2) / len(notes)


# 01 Noise: low bed + scattered soft ticks as dots appear
add(pad([45, 52, 57], 6.2, 500) * env(int(6.2 * SR), 1.2, 1.4), 0.0, 0.16, rev=0.3)
for i in range(26):
    tstart = 0.25 + rng.uniform(0, 2.9)
    add(tick(rng.uniform(2200, 4200)), tstart, rng.uniform(0.05, 0.12), pan=rng.uniform(-0.8, 0.8), rev=0.5)

# 02 System: rush into the lanes, a soft landing thump, then a pulse running down each lane
add(swell(0.9, 300, 4000), T1 - 0.6, 0.18, rev=0.4)
t = tt(0.6)
add(np.sin(2 * np.pi * (70 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 9), T1 + 0.55, 0.5)
for k in range(20):
    add(tick(1800 + k * 70, 0.05), T1 + 1.35 + k * 0.048, 0.07, pan=-0.9 + k * 0.09, rev=0.3)
add(pad([45, 52, 57, 64], 2.8, 1200) * env(int(2.8 * SR), 0.6, 1.0), T1 + 0.3, 0.1, rev=0.4)

# 03 Signal: rising air into the line, then the headline bell
add(swell(1.5, 200, 6000, 1.4), T3 - 1.5, 0.16, rev=0.5)
add(bell(81), T3, 0.20, pan=-0.1, rev=0.7)
add(bell(88, 3.0), T3 + 0.16, 0.08, pan=0.25, rev=0.8)
add(pad([45, 52, 61, 64], 2.6, 1400) * env(int(2.6 * SR), 0.3, 1.2), T3 - 0.1, 0.12, rev=0.5)

# Name: a resolved chord (A major) and a low anchor
for j, m in enumerate([69, 73, 76, 81]):
    add(bell(m, 2.6), T4 + j * 0.05, 0.10, pan=-0.3 + j * 0.2, rev=0.8)
t = tt(2.0)
add(np.sin(2 * np.pi * mtof(33) * t) * env(len(t), 0.05, 1.6), T4, 0.22)
add(pad([45, 52, 57, 61, 64], 2.1, 1000) * env(int(2.1 * SR), 0.4, 1.2), T4, 0.12, rev=0.5)

# simple feedback-delay reverb on the wet bus
rev = np.zeros_like(wet)
for d_ms, g in [(41, 0.5), (67, 0.42), (113, 0.35), (173, 0.28), (241, 0.2), (337, 0.14)]:
    d = int(d_ms * SR / 1000)
    for ch in (0, 1):
        dd = d + (ch * 37)
        rev[ch, dd:] += wet[ch, :-dd] * g
rev = np.vstack([lp(rev[0], 5000), lp(rev[1], 5000)])
mix = dry + rev * 0.8
mix = hp(mix[0], 30)[None, :], hp(mix[1], 30)[None, :]
mix = np.vstack(mix)

# fade tail for a clean loop and normalize to -1 dBFS
f = int(0.5 * SR)
mix[:, -f:] *= np.linspace(1, 0, f)
mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))

os.makedirs('assets', exist_ok=True)
wavfile.write('assets/score.wav', SR, (mix.T * 32767).astype(np.int16))
print('assets/score.wav', mix.shape[1] / SR, 's')
