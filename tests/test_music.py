import os
import tempfile
import wave

import numpy as np

from advvideo import music

SR = 22050   # smaller rate keeps the test fast; the code is rate-independent


def test_shape_dtype_and_level():
    for style in music.STYLES:
        x = music.make_music(style, seconds=6.0, sr=SR)
        assert x.dtype == np.float32 and x.shape == (int(6.0 * SR), 2)
        assert np.all(np.isfinite(x))
        peak = float(np.max(np.abs(x)))
        assert 0.55 <= peak <= 0.62, peak
        rms = float(np.sqrt(np.mean(x ** 2)))
        assert 0.04 <= rms <= 0.35, rms


def test_never_silent_in_any_second():
    for style in music.STYLES:
        x = music.make_music(style, seconds=8.0, sr=SR)
        for s in range(8):
            window = x[s * SR:(s + 1) * SR]
            assert float(np.sqrt(np.mean(window ** 2))) > 0.02, (style, s)


def test_pitch_content_is_in_c_major():
    x = music.make_music("calm", seconds=8.0, sr=SR)
    mono = x.mean(axis=1)
    spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
    freqs = np.fft.rfftfreq(len(mono), 1.0 / SR)
    band = (freqs > 60) & (freqs < 1500)
    top = freqs[band][np.argsort(spec[band])[-12:]]
    c_major = {0, 2, 4, 5, 7, 9, 11}
    def pitch_class(f):
        return int(round(12 * np.log2(f / 440.0) + 69)) % 12
    inside = sum(1 for f in top if pitch_class(f) in c_major)
    assert inside >= 10, sorted(top)


def test_stereo_is_not_dual_mono():
    x = music.make_music("upbeat", seconds=4.0, sr=SR)
    assert float(np.mean(np.abs(x[:, 0] - x[:, 1]))) > 0.003


def test_upbeat_has_more_energy_movement_than_calm():
    up = music.make_music("upbeat", seconds=8.0, sr=SR).mean(axis=1)
    calm = music.make_music("calm", seconds=8.0, sr=SR).mean(axis=1)
    def flux(x):
        win = SR // 10
        env = np.array([np.sqrt(np.mean(x[i:i + win] ** 2)) for i in range(0, len(x) - win, win)])
        return float(np.mean(np.abs(np.diff(env))))
    assert flux(up) > flux(calm)


def test_deterministic_and_seed_changes_the_hats():
    a = music.make_music("upbeat", seconds=3.0, sr=SR, seed=1)
    b = music.make_music("upbeat", seconds=3.0, sr=SR, seed=1)
    c = music.make_music("upbeat", seconds=3.0, sr=SR, seed=2)
    assert np.array_equal(a, b) and not np.array_equal(a, c)


def test_unknown_style_is_rejected():
    try:
        music.make_music("polka")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_wav_writer():
    x = music.make_music("calm", seconds=1.0, sr=SR)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.wav")
        music.write_wav_stereo(p, x, SR)
        with wave.open(p, "rb") as w:
            assert w.getnchannels() == 2 and w.getsampwidth() == 2 and w.getframerate() == SR and w.getnframes() == len(x)


def test_music_is_scaled_to_a_fraction_of_the_voice_level():
    rng = np.random.default_rng(3)
    voice = np.zeros(SR * 6, dtype=np.float32)
    voice[SR:3 * SR] = 0.4 * rng.standard_normal(2 * SR).astype(np.float32).clip(-1, 1)      # speech burst, silence around it
    track = 0.6 * music.make_music("calm", seconds=6.0, sr=SR)
    scaled = music.match_to_voice(track, voice)
    ratio = music.rms(scaled) / music.speech_rms(voice)
    assert abs(ratio - music.MUSIC_TO_VOICE) < 0.01
    assert scaled.dtype == np.float32 and np.max(np.abs(scaled)) <= 1.0
    assert music.speech_rms(voice) > music.rms(voice)               # silence between lines does not lower the reference
    assert 0.05 <= music.MUSIC_TO_VOICE <= 0.25


def test_music_left_alone_when_there_is_no_voice():
    track = music.make_music("calm", seconds=2.0, sr=SR)
    assert np.array_equal(music.match_to_voice(track, np.zeros(1000, dtype=np.float32)), track)
    assert np.array_equal(music.match_to_voice(track, np.zeros(0, dtype=np.float32)), track)
