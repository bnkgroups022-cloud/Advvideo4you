import math
import os
import tempfile
import wave

import numpy as np

from advvideo import voice


def make_tone(path, seconds, freq=440.0, rate=22050, amp=0.5):
    t = np.arange(int(seconds * rate)) / rate
    voice.write_wav_mono(path, (amp * np.sin(2 * math.pi * freq * t)).astype(np.float32), rate)


def test_voice_catalog():
    assert set(voice.VOICES) == {"en", "hi", "bn"}
    for lang, v in voice.VOICES.items():
        onnx, js = voice.voice_urls(lang)
        assert onnx.startswith("https://huggingface.co/rhasspy/piper-voices/resolve/main/")
        assert onnx.endswith("/%s.onnx" % v["id"]) and js == onnx + ".json"
        assert v["dir"].startswith(lang) and v["license"]
    assert voice.VOICES["hi"]["commercial_ok"] is False
    assert voice.VOICES["en"]["commercial_ok"] is True


def test_voice_urls_match_the_real_catalog_layout():
    onnx, _ = voice.voice_urls("hi")
    assert onnx.endswith("hi/hi_IN/priyamvada/medium/hi_IN-priyamvada-medium.onnx")
    onnx, _ = voice.voice_urls("bn")
    assert onnx.endswith("bn/bn_BD/google/medium/bn_BD-google-medium.onnx")
    onnx, _ = voice.voice_urls("en")
    assert onnx.endswith("en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx")


def test_timeline_when_it_fits():
    plan = voice.plan_timeline([2.0, 2.0, 2.0, 2.0, 2.5])
    assert plan["fits"] and plan["speedup"] == 1.0
    assert plan["starts"][0] == 0.35
    assert all(plan["starts"][i + 1] >= plan["ends"][i] + 0.29 for i in range(4))
    assert plan["ends"][-1] <= 15.0 - 0.9 + 1e-6
    assert 0.3 <= plan["gap"] <= 0.9


def test_timeline_spreads_spare_time_but_caps_the_gap():
    short = voice.plan_timeline([1.0, 1.0, 1.0, 1.0, 1.0])
    assert short["gap"] == 0.9
    assert short["ends"][-1] < 14.1


def test_timeline_speeds_up_when_too_long():
    plan = voice.plan_timeline([3.5, 3.0, 3.0, 3.0, 3.5])
    assert plan["fits"] and 1.0 < plan["speedup"] <= voice.MAX_SPEEDUP
    assert plan["ends"][-1] <= 15.0 - 0.9 + 1e-3
    assert voice.length_scale_for(plan["speedup"]) < 1.0


def test_timeline_reports_when_it_cannot_fit():
    plan = voice.plan_timeline([5.0, 4.0, 4.0, 4.0, 5.0])
    assert not plan["fits"] and plan["speedup"] == voice.MAX_SPEEDUP


def test_length_scale_bounds():
    assert voice.length_scale_for(1.0) == 1.0
    assert voice.length_scale_for(2.0) >= voice.MIN_LENGTH_SCALE
    assert voice.length_scale_for(0.5) == 1.0


def test_drop_order_removes_middle_features_first():
    kinds = ["hook", "feature", "feature", "feature", "cta"]
    assert voice.drop_order(kinds) == [2, 3]
    assert voice.drop_order(["hook", "cta"]) == []


def test_mix_voice_places_segments_at_their_start_times():
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        make_tone(a, 1.0, 440)
        make_tone(b, 1.0, 880)
        out = os.path.join(d, "mix.wav")
        rate = voice.mix_voice([a, b], [0.5, 3.0], 5.0, out)
        samples, sr = voice.read_wav_mono(out)
        assert sr == rate and abs(len(samples) / sr - 5.0) < 0.01
        assert float(np.max(np.abs(samples))) <= 0.93
        def rms(t0, t1):
            return float(np.sqrt(np.mean(samples[int(t0 * sr):int(t1 * sr)] ** 2)))
        assert rms(0.6, 1.4) > 0.2 and rms(3.1, 3.9) > 0.2
        assert rms(1.7, 2.9) < 0.001 and rms(4.2, 4.9) < 0.001 and rms(0.0, 0.4) < 0.001
        with wave.open(out, "rb") as w:
            assert w.getnchannels() == 1 and w.getsampwidth() == 2


def test_wav_helpers_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.wav")
        make_tone(p, 0.5)
        assert abs(voice.wav_duration(p) - 0.5) < 0.001
        samples, rate = voice.read_wav_mono(p)
        assert rate == 22050 and len(samples) == 11025


def test_sequential_plan_is_back_to_back_without_overlap():
    plan = voice.sequential_plan([2.0, 3.0, 4.0])
    assert plan["starts"] == [0.35, 2.65, 5.95] and not plan["fits"] and plan["speedup"] == 1.0
    assert all(plan["starts"][i + 1] >= plan["ends"][i] for i in range(2))

def test_anchor_last_moves_only_the_final_segment_later():
    plain = voice.plan_timeline([1.5, 1.5, 1.5, 1.5, 1.8])
    anchored = voice.plan_timeline([1.5, 1.5, 1.5, 1.5, 1.8], anchor_last=12.15)
    assert anchored["starts"][:-1] == plain["starts"][:-1] and anchored["ends"][:-1] == plain["ends"][:-1]
    assert anchored["starts"][-1] >= plain["starts"][-1]
    assert abs(anchored["ends"][-1] - anchored["starts"][-1] - 1.8) < 1e-2
    assert anchored["ends"][-1] <= 15.0 - 0.9 + 1e-6


def test_anchor_last_never_pushes_a_long_final_segment_past_the_tail():
    anchored = voice.plan_timeline([2.0, 2.0, 2.0, 2.0, 3.4], anchor_last=12.15)
    assert anchored["ends"][-1] <= 15.0 - 0.9 + 1e-6
    assert anchored["starts"][-1] >= anchored["ends"][-2]
