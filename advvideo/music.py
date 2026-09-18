"""Royalty-free background music, synthesised at run time.

The tracks are original (a simple I-V-vi-IV progression rendered with soft pads, a bass line, plucked arpeggios and, for
the upbeat style, kick and hi-hat), generated from code in this repository and released under CC0. Nothing is downloaded
and no third-party recording is used, so there is no licence to carry into the finished ad.
"""
import wave

import numpy as np

SR = 44100
STYLES = {
    "upbeat": {"bpm": 118, "bars_per_chord": 1, "drums": True, "bass_pulse": 2, "arp_gain": 0.10, "pad_gain": 0.085},
    "calm": {"bpm": 84, "bars_per_chord": 2, "drums": False, "bass_pulse": 0.5, "arp_gain": 0.075, "pad_gain": 0.11},
}
# I - V - vi - IV in C major (MIDI note numbers, close voicings)
CHORDS = [[60, 64, 67], [59, 62, 67], [57, 60, 64], [60, 65, 69]]
ROOTS = [36, 43, 45, 41]


def midi_hz(note):
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def _env(n, sr, attack, release, length=None):
    """Attack/release envelope over n samples."""
    e = np.ones(n, dtype=np.float32)
    a, r = max(1, int(attack * sr)), max(1, int(release * sr))
    a, r = min(a, n), min(r, n)
    e[:a] = np.linspace(0.0, 1.0, a, dtype=np.float32)
    e[n - r:] *= np.linspace(1.0, 0.0, r, dtype=np.float32)
    return e


def _tone(freq, n, sr, harmonics=(1.0, 0.3, 0.12)):
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, dtype=np.float32)
    for k, amp in enumerate(harmonics, 1):
        out += amp * np.sin(2 * np.pi * freq * k * t).astype(np.float32)
    return out


def _add(track, signal, start, gain=1.0, pan=0.0):
    """Mix a mono signal into a stereo track (pan -1 left .. +1 right)."""
    i = int(start)
    if i >= len(track):
        return
    j = min(len(track), i + len(signal))
    seg = signal[: j - i] * gain
    track[i:j, 0] += seg * (1.0 - max(0.0, pan))
    track[i:j, 1] += seg * (1.0 + min(0.0, pan))


def make_music(style="upbeat", seconds=16.5, sr=SR, seed=7):
    """Stereo float32 array (samples, 2), peak-normalised to about 0.6."""
    if style not in STYLES:
        raise ValueError("unknown music style: %r" % (style,))
    cfg = STYLES[style]
    rng = np.random.default_rng(seed)
    n = int(seconds * sr)
    track = np.zeros((n, 2), dtype=np.float32)
    beat = 60.0 / cfg["bpm"] * sr                      # samples per beat
    chord_len = beat * 4 * cfg["bars_per_chord"]
    total_chords = int(np.ceil(n / chord_len)) + 1

    for c in range(total_chords):
        start = c * chord_len
        chord, root = CHORDS[c % 4], ROOTS[c % 4]
        seg = int(chord_len + 0.6 * sr)
        for k, note in enumerate(chord):
            for detune, pan in ((0.998, -0.4), (1.002, 0.4)):
                voice = _tone(midi_hz(note) * detune, seg, sr) * _env(seg, sr, 0.35, 0.6)
                _add(track, voice, start, cfg["pad_gain"] / 2.0, pan)
        # bass: pulses per beat (or slower for calm)
        pulse = beat / cfg["bass_pulse"] if cfg["bass_pulse"] >= 1 else beat / cfg["bass_pulse"]
        p = 0
        while p * pulse < chord_len:
            length = int(min(pulse, 0.6 * sr))
            note = _tone(midi_hz(root), length, sr, (1.0, 0.25)) * np.exp(-np.arange(length) / (0.28 * sr)).astype(np.float32)
            note *= _env(length, sr, 0.005, 0.02)
            _add(track, note, start + p * pulse, 0.20)
            p += 1
        # arpeggio: eighth notes cycling through the chord an octave up
        step = beat / 2.0
        idx = 0
        while idx * step < chord_len:
            note_num = chord[idx % 3] + 12 + (12 if idx % 6 >= 3 else 0)
            length = int(0.42 * sr)
            pluck = _tone(midi_hz(note_num), length, sr, (1.0, 0.4, 0.2)) * np.exp(-np.arange(length) / (0.16 * sr)).astype(np.float32)
            pluck *= _env(length, sr, 0.003, 0.05)
            _add(track, pluck, start + idx * step, cfg["arp_gain"], -0.5 if idx % 2 == 0 else 0.5)
            idx += 1

    if cfg["drums"]:
        b = 0
        while b * beat < n:
            length = int(0.16 * sr)
            t = np.arange(length, dtype=np.float32) / sr
            sweep = 45.0 + 85.0 * np.exp(-t / 0.035)
            kick = np.sin(2 * np.pi * np.cumsum(sweep) / sr).astype(np.float32) * np.exp(-t / 0.07).astype(np.float32)
            _add(track, kick, b * beat, 0.30)
            hat_len = int(0.05 * sr)
            noise = rng.standard_normal(hat_len).astype(np.float32)
            hat = np.diff(noise, prepend=0.0) * np.exp(-np.arange(hat_len) / (0.012 * sr)).astype(np.float32)
            _add(track, hat, b * beat + beat / 2.0, 0.05, 0.3)
            b += 1

    track = np.tanh(1.25 * track) / 1.25
    peak = float(np.max(np.abs(track)))
    if peak > 0:
        track *= 0.6 / peak
    return track.astype(np.float32)


def write_wav_stereo(path, track, sr=SR):
    pcm = (np.clip(track, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
