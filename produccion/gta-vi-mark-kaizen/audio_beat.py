"""Beat sintetizado (128 BPM, 32 beats). Sin muestras ni música con copyright."""
import numpy as np, wave, sys
SR, BPM, BEATS = 44100, 128, 32
beat = 60 / BPM
n = int(SR * (beat * BEATS + 0.6))
out = np.zeros(n)
rng = np.random.default_rng(7)

def add(sig, t):
    i = int(t * SR); j = min(n, i + len(sig))
    if i < n: out[i:j] += sig[: j - i]

def kick():
    t = np.arange(int(.28 * SR)) / SR
    f = 50 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 1.0

def hat():
    t = np.arange(int(.05 * SR)) / SR
    x = rng.standard_normal(len(t)); x = np.diff(x, prepend=0)
    return x * np.exp(-t * 90) * .18

def clap():
    t = np.arange(int(.18 * SR)) / SR
    x = rng.standard_normal(len(t)) * np.exp(-t * 28)
    return np.diff(x, prepend=0) * .5

def bass(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 3) * .38

notes = [55, 55, 65.4, 73.4]  # A1 A1 C2 D2
for b in range(BEATS):
    t = b * beat
    add(kick(), t)
    add(hat(), t + beat / 2)
    if b % 2 == 1: add(clap(), t)
    add(bass(notes[(b // 2) % 4], beat * .9), t)
    if b == BEATS - 1:  # remate final
        add(kick() * 1.2, t + beat)
out = np.tanh(out * 1.3)
out /= np.max(np.abs(out)) / 0.9
fade = np.linspace(1, 0, int(.35 * SR)); out[-len(fade):] *= fade
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
