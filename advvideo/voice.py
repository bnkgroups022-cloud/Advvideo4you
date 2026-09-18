"""Voice-over with Piper TTS (Hindi, English, Bangla), plus the timeline maths that keeps it inside 15 seconds.

Voices come from the ``rhasspy/piper-voices`` repository on Hugging Face. Licences differ per voice and are surfaced
in ``VOICES`` so the pipeline and the docs can tell the user (the Hindi voices are non-commercial).
"""
import json
import os
import time
import urllib.request
import wave

HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

VOICES = {
    "en": {"id": "en_US-ljspeech-medium", "dir": "en/en_US/ljspeech/medium", "speaker": None,
           "license": "Public domain (LJ Speech dataset)", "commercial_ok": True},
    "hi": {"id": "hi_IN-priyamvada-medium", "dir": "hi/hi_IN/priyamvada/medium", "speaker": None,
           "license": "CC BY-NC-SA 4.0 - non-commercial use only", "commercial_ok": False},
    "bn": {"id": "bn_BD-google-medium", "dir": "bn/bn_BD/google/medium", "speaker": 0,
           "license": "CC BY-SA 4.0 (OpenSLR 37) with CMU permissive terms; attribution required", "commercial_ok": True},
}

MAX_SPEEDUP = 1.35
MIN_LENGTH_SCALE = 0.72


def voice_urls(lang):
    """(onnx_url, json_url) of the Piper voice used for a language."""
    v = VOICES[lang]
    base = HF_BASE + v["dir"] + "/" + v["id"]
    return base + ".onnx", base + ".onnx.json"


def voice_paths(lang, dest):
    v = VOICES[lang]
    return os.path.join(dest, v["id"] + ".onnx"), os.path.join(dest, v["id"] + ".onnx.json")


def download_voice(lang, dest, retries=3):
    """Download the voice model and its config once; returns the .onnx path."""
    os.makedirs(dest, exist_ok=True)
    onnx_path, json_path = voice_paths(lang, dest)
    onnx_url, json_url = voice_urls(lang)
    for url, path, min_bytes in ((json_url, json_path, 500), (onnx_url, onnx_path, 10 * 2 ** 20)):
        if os.path.exists(path) and os.path.getsize(path) >= min_bytes:
            continue
        for attempt in range(1, retries + 1):
            try:
                urllib.request.urlretrieve(url, path + ".part")
                if os.path.getsize(path + ".part") < min_bytes:
                    raise IOError("download too small")
                os.replace(path + ".part", path)
                break
            except Exception as exc:  # network hiccup: retry, then give up loudly
                if attempt == retries:
                    raise RuntimeError("could not download %s: %s" % (url, exc))
                time.sleep(3 * attempt)
    with open(json_path, "r", encoding="utf-8") as fh:
        json.load(fh)
    return onnx_path


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def read_wav_mono(path):
    """(float32 samples in [-1, 1], sample rate) from a 16-bit PCM WAV."""
    import numpy as np
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError("expected 16-bit PCM WAV")
        rate, channels = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def write_wav_mono(path, samples, rate):
    import numpy as np
    pcm = (np.clip(samples, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())


def plan_timeline(durations, total=15.0, lead=0.35, tail=0.9, min_gap=0.30, max_gap=0.90):
    """Where each spoken segment starts inside the video.

    Returns starts/ends (seconds), the gap used, the speed-up factor needed to fit (1.0 = none) and whether it fits
    without exceeding MAX_SPEEDUP. Spare time is spread evenly between segments (up to max_gap).
    """
    n = len(durations)
    speech = float(sum(durations))
    room = total - tail - lead
    speedup = 1.0
    if speech + (n - 1) * min_gap > room:
        speedup = (speech) / max(room - (n - 1) * min_gap, 0.1)
    fits = speedup <= MAX_SPEEDUP
    speedup = min(speedup, MAX_SPEEDUP) if not fits else max(speedup, 1.0)
    scaled = [d / speedup for d in durations]
    spare = room - sum(scaled)
    gap = min_gap if n < 2 else min(max_gap, max(min_gap, spare / (n - 1)))
    starts, ends, t = [], [], lead
    for d in scaled:
        starts.append(round(t, 3))
        ends.append(round(t + d, 3))
        t += d + gap
    return {"starts": starts, "ends": ends, "gap": round(gap, 3), "speedup": round(speedup, 3), "fits": fits,
            "speech_seconds": round(sum(scaled), 3)}


def sequential_plan(durations, total=15.0, lead=0.35, gap=0.30):
    """Last resort when nothing fits: play everything back to back at normal speed (the end may be cut off)."""
    starts, ends, t = [], [], lead
    for d in durations:
        starts.append(round(t, 3))
        ends.append(round(t + d, 3))
        t += d + gap
    return {"starts": starts, "ends": ends, "gap": gap, "speedup": 1.0, "fits": False, "speech_seconds": round(sum(durations), 3)}

def length_scale_for(speedup):
    """Piper length_scale for a wanted speed-up (< 1 is faster), never absurdly fast."""
    return max(MIN_LENGTH_SCALE, round(1.0 / max(speedup, 1.0), 3))


def drop_order(kinds):
    """Indices of segments to drop, in order, when the script cannot fit even at maximum speed: middle features first."""
    features = [i for i, k in enumerate(kinds) if k == "feature"]
    return features[1:2] + features[2:3] if len(features) >= 3 else []


def mix_voice(wav_paths, starts, total, out_path, fade=0.008, peak=0.92):
    """Place each segment at its start time on a silent mono track of ``total`` seconds and write it."""
    import numpy as np
    rate = None
    chunks = []
    for path in wav_paths:
        samples, sr = read_wav_mono(path)
        if rate is None:
            rate = sr
        elif sr != rate:
            raise ValueError("segments have different sample rates")
        chunks.append(samples)
    track = np.zeros(int(round(total * rate)), dtype=np.float32)
    ramp = max(1, int(fade * rate))
    for samples, start in zip(chunks, starts):
        seg = samples.copy()
        if len(seg) > 2 * ramp:
            seg[:ramp] *= np.linspace(0, 1, ramp, dtype=np.float32)
            seg[-ramp:] *= np.linspace(1, 0, ramp, dtype=np.float32)
        i = int(round(start * rate))
        j = min(len(track), i + len(seg))
        if i < len(track):
            track[i:j] += seg[:j - i]
    top = float(np.max(np.abs(track))) if len(track) else 0.0
    if top > 0:
        track *= peak / top
    write_wav_mono(out_path, track, rate)
    return rate
