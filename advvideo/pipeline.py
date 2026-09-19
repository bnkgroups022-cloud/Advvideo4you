"""End-to-end pipeline (runs inside Colab): product photo + name + language + CTA -> 15-second 9:16 MP4.

    launch file -> script (LLM, templates as fallback) -> Piper voice-over -> captions -> music
                                        \\-> Wan2.1 VACE clip (GPU, runs alongside the audio work) -> FFmpeg render

Heavy stages run as child processes so their memory is released. If the AI clip cannot be produced the ad still renders,
using a slow push-in on the photo instead (and the report says so).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time

from advvideo import __version__, captions, config, music, render, script, spec, voice

HERE = os.path.dirname(os.path.abspath(__file__))
WAN_REPO_URL = "https://github.com/Wan-Video/Wan2.1"
WAN_REPO_COMMIT = "9737cba9c1c3c4d04b33fcad41c111989865d315"
WAN_MODEL_REPO = "Wan-AI/Wan2.1-VACE-1.3B"
WAN_ALLOW = ["*.safetensors", "*.pth", "config.json", "google/*"]
WAN_REQUIRED = {
    "diffusion_pytorch_model.safetensors": 7.0e9,
    "models_t5_umt5-xxl-enc-bf16.pth": 11.3e9,
    "Wan2.1_VAE.pth": 5.0e8,
    "config.json": 100,
    "google/umt5-xxl/spiece.model": 1e6,
    "google/umt5-xxl/tokenizer.json": 1e6,
    "google/umt5-xxl/tokenizer_config.json": 1000,
}
# Fixed on purpose: the product comes from the photo (frame 0), and a fixed prompt lets the T5 embeddings be cached.
MOTION_PROMPT = ("Cinematic vertical product advertisement. The product from the photo stays sharp, centered and unchanged "
                 "in shape and color. Slow smooth camera push-in with subtle parallax, soft studio key light with a gentle "
                 "rim highlight, clean background with light bokeh, realistic reflections, natural subtle motion, "
                 "premium commercial look, high detail.")
FRAME_LADDER = [33, 25, 17]
EXIT_OK, EXIT_OOM, EXIT_NAN = 0, 3, 4
TOTAL = render.DURATION

_LOCK = threading.Lock()


def log(tag, message):
    with _LOCK:
        print(time.strftime("[%H:%M:%S] ") + "[" + tag + "] " + str(message), flush=True)


def stream(cmd, tag, env=None, cwd=None, timeout=None, keep=40):
    """Run a command, echoing its output live under ``tag``. Returns (exit code, last lines)."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, cwd=cwd)
    timer = None
    if timeout:
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
    tail = []
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.strip():
            log(tag, line)
            tail = (tail + [line])[-keep:]
    code = proc.wait()
    if timer:
        timer.cancel()
    return code, tail


class Paths:
    def __init__(self, work, cache, out):
        self.work, self.cache, self.out = work, cache, out
        self.input = os.path.join(work, "input")
        self.audio = os.path.join(work, "audio")
        self.caps = os.path.join(work, "captions")
        self.fonts = os.path.join(cache, "fonts")
        self.voices = os.path.join(cache, "voices")
        self.wan_repo = os.path.join(cache, "Wan2.1")
        self.wan_ckpt = os.path.join(cache, "Wan2.1-VACE-1.3B")
        digest = hashlib.sha256(MOTION_PROMPT.encode("utf-8")).hexdigest()[:12]
        self.embeds = os.path.join(cache, "prompt_embeds_%s.pt" % digest)
        for d in (self.input, self.audio, self.caps, self.fonts, self.voices, out):
            os.makedirs(d, exist_ok=True)


# ----------------------------------------------------------------------------- inputs
def load_inputs(args, paths):
    """Settings and the product photo from the launch file and/or the uploaded image."""
    cfg = None
    if args.launch:
        with open(args.launch, "rb") as fh:
            cfg = config.parse_launch(fh.read())
    elif args.name:
        cfg = config.validate_fields(args.name, args.language, args.cta, args.spoken_name or "", args.details or "")
        cfg["image_bytes"], cfg["image_ext"] = None, None
    if cfg is None:
        raise config.ConfigError("no launch file and no --name: nothing to make an ad about")
    if args.image:
        with open(args.image, "rb") as fh:
            blob = fh.read()
        ext = config.sniff_image(blob)
        if ext is None:
            raise config.ConfigError("the uploaded photo must be a JPEG, PNG or WebP image")
        cfg["image_bytes"], cfg["image_ext"] = blob, ext
    if cfg["image_bytes"] is None:
        raise config.ConfigError("no product photo: choose one in the website form or upload an image next to the launch file")
    image_path = os.path.join(paths.input, "product." + cfg["image_ext"])
    with open(image_path, "wb") as fh:
        fh.write(cfg["image_bytes"])
    return cfg, image_path


# ----------------------------------------------------------------------------- script
def script_stage(cfg, paths, mode, timeout=420):
    """Hook + three features + CTA. LLM first (unless mode says otherwise), templates as the safety net."""
    llm = None
    notes = []
    if mode in ("auto", "llm"):
        messages_path = os.path.join(paths.work, "llm_messages.json")
        replies_path = os.path.join(paths.work, "llm_replies.json")
        with open(messages_path, "w", encoding="utf-8") as fh:
            json.dump(script.build_llm_messages(cfg), fh, ensure_ascii=False)
        if os.path.exists(replies_path):
            os.remove(replies_path)
        code, _tail = stream([sys.executable, "-m", "advvideo.llm_worker", "--messages", messages_path, "--out", replies_path, "--n", "3"],
                             "script", cwd=os.path.dirname(HERE), timeout=timeout)
        if code == 0 and os.path.exists(replies_path):
            with open(replies_path, "r", encoding="utf-8") as fh:
                replies = iter(json.load(fh))
            llm = lambda messages: next(replies)
        else:
            notes.append("LLM worker exited with code %s" % code)
    result = script.generate_script(cfg, llm=llm, attempts=3)
    result["notes"] = notes + result.get("notes", [])
    with open(os.path.join(paths.work, "script.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    log("script", "source: %s" % result["source"])
    for note in result["notes"]:
        log("script", "note: " + note)
    log("script", "HOOK    : " + result["hook"])
    for i, line in enumerate(result["features"], 1):
        log("script", "FEATURE%d: %s" % (i, line))
    log("script", "CTA     : " + result["cta"])
    return result


# ----------------------------------------------------------------------------- voice
def timeline(durations, items, total):
    """Voice timeline; the CTA is anchored to start just after the closing card appears."""
    return voice.plan_timeline([durations[i["id"]] for i in items], total=total, anchor_last=total - spec.CARD_SECONDS + 0.15)


def plan_voice(items, synth, total=TOTAL, max_rounds=3):
    """Choose speaking speed (and drop a middle feature if needed) so the speech fits the video.

    ``items`` is a list of {"id", "kind", "text"}; ``synth(items, length_scale) -> {id: seconds}``. The returned plan
    always describes audio that really exists: speed changes are made by re-synthesising, never assumed.
    """
    items = list(items)
    scale = 1.0
    dropped = []
    durations = synth(items, scale)
    while True:
        plan = timeline(durations, items, total)
        rounds = 0
        while plan["speedup"] > 1.02 and scale > voice.MIN_LENGTH_SCALE + 1e-6 and rounds < max_rounds:
            scale = max(voice.MIN_LENGTH_SCALE, round(scale / plan["speedup"], 3))
            durations = synth(items, scale)
            plan = timeline(durations, items, total)
            rounds += 1
        if plan["speedup"] <= 1.02:
            break
        order = voice.drop_order([i["kind"] for i in items])
        if not order:
            plan = voice.sequential_plan([durations[i["id"]] for i in items], total=total)
            break
        victim = items[order[0]]
        dropped.append(victim["id"])
        items = [i for i in items if i["id"] != victim["id"]]
    return {"items": items, "durations": durations, "plan": plan, "length_scale": scale, "dropped": dropped}

def ensure_piper():
    probe = subprocess.run([sys.executable, "-c", "import piper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if probe.returncode != 0:
        log("audio", "installing piper-tts")
        code, tail = stream([sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", "piper-tts"], "audio")
        if code != 0:
            raise RuntimeError("could not install piper-tts: " + " | ".join(tail[-3:]))


def voice_stage(cfg, scr, paths):
    lang = cfg["language"]
    info = voice.VOICES[lang]
    log("audio", "voice: %s (%s)" % (info["id"], info["license"]))
    if not info["commercial_ok"]:
        log("audio", "NOTICE: this voice is licensed for non-commercial use only")
    ensure_piper()
    onnx = voice.download_voice(lang, paths.voices)
    segs = script.segments(scr, cfg)
    items = [{"id": "seg%d" % i, "kind": s["kind"], "text": s["speech"], "caption": s["caption"]} for i, s in enumerate(segs)]

    def synth(current, length_scale):
        lines_path = os.path.join(paths.audio, "lines.json")
        with open(lines_path, "w", encoding="utf-8") as fh:
            json.dump([{"id": i["id"], "text": i["text"]} for i in current], fh, ensure_ascii=False)
        cmd = [sys.executable, "-m", "advvideo.tts_worker", "--onnx", onnx, "--lines", lines_path, "--outdir", paths.audio,
               "--length-scale", str(length_scale)]
        if info["speaker"] is not None:
            cmd += ["--speaker", str(info["speaker"])]
        code, tail = stream(cmd, "audio", cwd=os.path.dirname(HERE), timeout=600)
        result = next((json.loads(l[7:]) for l in reversed(tail) if l.startswith("RESULT ")), None)
        if code != 0 or result is None:
            raise RuntimeError("Piper failed (exit %s): %s" % (code, " | ".join(tail[-3:])))
        return {k: v["seconds"] for k, v in result.items()}

    planned = plan_voice(items, synth)
    plan, kept = planned["plan"], planned["items"]
    log("audio", "speech %.1fs at length_scale %.2f%s; starts %s" % (plan["speech_seconds"], planned["length_scale"],
        (", dropped " + ",".join(planned["dropped"])) if planned["dropped"] else "", plan["starts"]))
    if not plan["fits"]:
        log("audio", "WARNING: speech still longer than the video allows; it will be cut at the end")
    wav = os.path.join(paths.audio, "voice.wav")
    voice.mix_voice([os.path.join(paths.audio, i["id"] + ".wav") for i in kept], plan["starts"], TOTAL, wav)
    return {"wav": wav, "plan": plan, "items": kept, "length_scale": planned["length_scale"], "dropped": planned["dropped"]}


# ----------------------------------------------------------------------------- captions + music
def captions_stage(cfg, voiced, paths, ffmpeg="ffmpeg"):
    """SRT (every spoken line) plus the on-screen captions and the closing card. Returns (caps dict for render, srt path)."""
    lang = cfg["language"]
    fonts = captions.ensure_fonts(lang, paths.fonts)
    texts = [i["caption"] for i in voiced["items"]]
    events = captions.caption_events(texts, voiced["plan"]["starts"], voiced["plan"]["ends"], total=TOTAL)
    card = captions.make_card(cfg["product_name"], cfg["cta"], lang, TOTAL)
    on_screen = captions.burned_events(events, [i["kind"] for i in voiced["items"]], card["start"])
    measure = captions.make_measure(fonts["native"], latin_path=fonts["latin"])
    laid = captions.layout_events(on_screen, measure)
    srt_path = os.path.join(paths.out, "captions.srt")
    with open(srt_path, "w", encoding="utf-8") as fh:
        fh.write(captions.to_srt(events))
    conf, filters = render.buildconf_and_filters(ffmpeg)
    caps = captions.parse_ffmpeg_caps(conf, filters)
    backend = captions.choose_backend(lang, caps)
    log("render", "FFmpeg captions: ass=%s drawtext=%s harfbuzz=%s -> using %s" % (caps["ass"], caps["drawtext"], caps["harfbuzz"], backend))
    if backend == "ass":
        ass_path = os.path.join(paths.caps, "captions.ass")
        latin_family = captions.FONTS["en"][2]
        with open(ass_path, "w", encoding="utf-8") as fh:
            fh.write(captions.to_ass(laid, captions.FONTS[lang][2], lang, card=card, measure=measure, latin_family=latin_family))
        return {"mode": "ass", "file": ass_path, "fontsdir": paths.fonts, "card": card}, srt_path
    if backend == "drawtext":
        filters = captions.drawtext_filters(laid, fonts["native"], paths.caps) + captions.drawtext_card_filters(card, fonts, paths.caps, lang)
        return {"mode": "drawtext", "filters": filters, "card": card}, srt_path
    log("render", "WARNING: this FFmpeg has neither libass nor drawtext; the video will have no on-screen text (SRT still written)")
    return {"mode": "none", "card": card}, srt_path


def music_stage(style, paths, voice_wav=None):
    """Background track, scaled so it sits at about 20% of the voice-over's loudness."""
    import numpy as np
    wav = os.path.join(paths.audio, "music.wav")
    seconds = TOTAL + 1.5
    if style == "none":
        music.write_wav_stereo(wav, np.zeros((int(seconds * music.SR), 2), dtype=np.float32), music.SR)
    else:
        track = music.make_music(style, seconds=seconds)
        if voice_wav:
            samples, _rate = voice.read_wav_mono(voice_wav)
            track = music.match_to_voice(track, samples)
        music.write_wav_stereo(wav, track, music.SR)
    log("audio", "music: %s (original synthesised track, CC0), level about 20%% of the voice" % style)
    return wav


# ----------------------------------------------------------------------------- Wan video
def verify_checkpoint(ckpt_dir):
    problems = []
    for name, minimum in WAN_REQUIRED.items():
        path = os.path.join(ckpt_dir, name)
        if not os.path.exists(path):
            problems.append("missing " + name)
        elif os.path.getsize(path) < minimum:
            problems.append("%s is only %.2f GB" % (name, os.path.getsize(path) / 1e9))
    return problems


def dir_size(path):
    total = 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


PREFETCH_STALE = 120          # seconds without a heartbeat before a prefetch marker is ignored
SCRIPT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def prefetch_marker(paths):
    return os.path.join(paths.cache, "prefetch.running")


def prefetch_running(paths, now=None):
    """True while a ``--prefetch`` process is alive (it refreshes its marker file every 30 seconds)."""
    try:
        return ((now or time.time()) - os.path.getmtime(prefetch_marker(paths))) < PREFETCH_STALE
    except OSError:
        return False


def wait_for_prefetch(paths, poll=5.0, sleep=time.sleep):
    if not prefetch_running(paths):
        return
    log("video", "the model download started earlier is still running; waiting for it")
    while prefetch_running(paths):
        sleep(poll)


def prefetch(paths):
    """Download everything heavy while the user is still busy (upload, package installs): script model, Wan repo and weights."""
    marker = prefetch_marker(paths)
    stop = threading.Event()

    def beat():
        while not stop.is_set():
            try:
                with open(marker, "w") as fh:
                    fh.write(str(os.getpid()))
            except OSError:
                pass
            stop.wait(30)

    threading.Thread(target=beat, daemon=True).start()
    try:
        code_text = ("import os\nos.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'\nfrom huggingface_hub import snapshot_download\n"
                     "snapshot_download(repo_id=%r, allow_patterns=['*.json', '*.safetensors', '*.txt', 'merges.txt', 'vocab.json'])\n" % SCRIPT_MODEL)
        code, _ = stream([sys.executable, "-c", code_text], "prefetch")
        log("prefetch", "script model %s" % ("ready" if code == 0 else "not fetched (the script step will fetch it)"))
        wan_prepare(paths, wait=False)
    finally:
        stop.set()
        try:
            os.remove(marker)
        except OSError:
            pass


def wan_prepare(paths, wait=True):
    """Clone the pinned official repo and download the model (network and disk only, no GPU)."""
    if wait:
        wait_for_prefetch(paths)
    repo_ok = os.path.exists(os.path.join(paths.wan_repo, "generate.py")) and os.path.exists(os.path.join(paths.wan_repo, "wan", "vace.py"))
    if not repo_ok:
        shutil.rmtree(paths.wan_repo, ignore_errors=True)
        os.makedirs(paths.wan_repo)
        steps = [["git", "init", "-q"], ["git", "remote", "add", "origin", WAN_REPO_URL + ".git"],
                 ["git", "fetch", "-q", "--depth", "1", "origin", WAN_REPO_COMMIT], ["git", "checkout", "-q", "--detach", "FETCH_HEAD"]]
        if any(stream(cmd, "video", cwd=paths.wan_repo)[0] != 0 for cmd in steps):
            log("video", "pinned commit not fetchable; cloning the default branch")
            shutil.rmtree(paths.wan_repo, ignore_errors=True)
            if stream(["git", "clone", "-q", "--depth", "1", WAN_REPO_URL + ".git", paths.wan_repo], "video")[0] != 0:
                raise RuntimeError("could not clone " + WAN_REPO_URL)
    log("video", "official repo ready: " + WAN_REPO_URL)
    for attempt in (1, 2):
        problems = verify_checkpoint(paths.wan_ckpt) if os.path.isdir(paths.wan_ckpt) else ["not downloaded"]
        if not problems:
            log("video", "model files cached (%.1f GB)" % (dir_size(paths.wan_ckpt) / 1e9))
            return
        if attempt == 2:
            raise RuntimeError("model download incomplete: " + "; ".join(problems))
        log("video", "downloading the Wan2.1 VACE-1.3B model (~19 GB, first run only)")
        stop = threading.Event()

        def monitor():
            while not stop.wait(30):
                log("video", "downloaded %.1f GB of ~19 GB" % (dir_size(paths.wan_ckpt) / 1e9))

        threading.Thread(target=monitor, daemon=True).start()
        code_text = (
            "import os, sys, time\n"
            "os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'\n"
            "from huggingface_hub import snapshot_download\n"
            "for n in (1, 2, 3):\n"
            "    try:\n"
            "        snapshot_download(repo_id=%r, local_dir=%r, allow_patterns=%r, max_workers=8)\n"
            "        sys.exit(0)\n"
            "    except Exception as exc:\n"
            "        print('download attempt', n, 'failed:', type(exc).__name__, exc, flush=True)\n"
            "        time.sleep(5)\n"
            "sys.exit(1)\n") % (WAN_MODEL_REPO, paths.wan_ckpt, WAN_ALLOW)
        stream([sys.executable, "-c", code_text], "video")
        stop.set()


def ladder_walk(ladder, run_rung, bf16_max=33):
    """Try frame counts longest-first. run_rung(frames, dtype) -> exit code. Returns (frames, dtype) or None."""
    dtype = "float16"
    i = 0
    while i < len(ladder):
        frames = ladder[i]
        if dtype == "bfloat16" and frames > bf16_max:
            i += 1
            continue
        code = run_rung(frames, dtype)
        if code == EXIT_OK:
            return frames, dtype
        if code == EXIT_OOM:
            log("video", "out of GPU memory at %d frames -> trying a shorter clip" % frames)
            i += 1
        elif code == EXIT_NAN and dtype == "float16":
            log("video", "fp16 overflowed -> retrying in bf16")
            dtype = "bfloat16"
        else:
            log("video", "generation failed with exit code %s" % code)
            return None
    return None


def wan_generate(paths, image_path, out_clip, frames, steps, seed):
    launcher = os.path.join(HERE, "wan_launcher.py")
    env = dict(os.environ, PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True", PYTHONUNBUFFERED="1", TOKENIZERS_PARALLELISM="false")
    common = [sys.executable, launcher, "--repo", paths.wan_repo, "--ckpt", paths.wan_ckpt, "--embeds", paths.embeds]
    if stream(common[:2] + ["--stage", "check"] + common[2:6], "video", env=env)[0] != 0:
        raise RuntimeError("the official Wan2.1 code does not import in this environment")
    code, _ = stream(common + ["--stage", "encode", "--prompt=" + MOTION_PROMPT], "video", env=env)
    if code != 0 or not os.path.exists(paths.embeds):
        raise RuntimeError("prompt encoding failed (exit %s)" % code)
    ladder = [f for f in FRAME_LADDER if f <= frames] or [frames]

    def run_rung(n, dtype):
        log("video", "generating %d frames (%.1fs at 16 fps), %d steps, %s" % (n, n / 16.0, steps, dtype))
        cmd = common + ["--stage", "generate", "--image", image_path, "--out", out_clip, "--prompt=" + MOTION_PROMPT,
                        "--frames", str(n), "--steps", str(steps), "--guidance", "5.0", "--seed", str(seed), "--dtype", dtype]
        return stream(cmd, "video", env=env)[0]

    outcome = ladder_walk(ladder, run_rung)
    if outcome is None or not os.path.exists(out_clip):
        raise RuntimeError("no setting produced a video clip")
    return outcome


# ----------------------------------------------------------------------------- main
def main(argv=None):
    p = argparse.ArgumentParser(description="Advvideo4you: photo -> 15-second 9:16 AI ad video")
    p.add_argument("--launch", help="advvideo-launch.json from the website")
    p.add_argument("--image", help="product photo (overrides the one inside the launch file)")
    p.add_argument("--name")
    p.add_argument("--language", default="en")
    p.add_argument("--cta", default="")
    p.add_argument("--spoken-name", default="")
    p.add_argument("--details", default="")
    p.add_argument("--work", default="/content/advvideo_work")
    p.add_argument("--cache", default="/content/advvideo_cache")
    p.add_argument("--out", default="/content/advvideo_output")
    p.add_argument("--music", choices=["upbeat", "calm", "none"], default="upbeat")
    p.add_argument("--script-mode", choices=["auto", "llm", "templates"], default="auto")
    p.add_argument("--frames", type=int, default=33)
    p.add_argument("--steps", type=int, default=18)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-wan", action="store_true", help="skip the AI clip and use a slow zoom on the photo (CPU test)")
    p.add_argument("--prefetch", action="store_true", help="only download the models into --cache (run in the background while waiting)")
    args = p.parse_args(argv)

    started = time.time()
    stamps = {}
    log("pipeline", "Advvideo4you %s" % __version__)
    paths = Paths(args.work, args.cache, args.out)
    if args.prefetch:
        prefetch(paths)
        log("prefetch", "done")
        return 0
    cfg, image_path = load_inputs(args, paths)
    log("pipeline", "product=%r language=%s cta=%r" % (cfg["product_name"], cfg["language"], cfg["cta"]))
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("ffmpeg/ffprobe not found (in Colab: apt-get install -y ffmpeg)")

    clip_path = os.path.join(paths.work, "wan_clip.mp4")
    if os.path.exists(clip_path):
        os.remove(clip_path)
    script_done = threading.Event()
    video = {"ok": False, "error": None, "frames": None, "dtype": None, "seconds": None}

    def video_thread():
        t0 = time.time()
        try:
            if args.no_wan:
                raise RuntimeError("--no-wan given")
            wan_prepare(paths)
            script_done.wait()          # the script LLM uses the GPU first
            frames, dtype = wan_generate(paths, image_path, clip_path, args.frames, args.steps, args.seed)
            video.update(ok=True, frames=frames, dtype=dtype)
        except Exception as exc:
            video["error"] = str(exc)
            log("video", "AI clip unavailable: %s" % exc)
        finally:
            video["seconds"] = round(time.time() - t0, 1)
            script_done.set()

    thread = threading.Thread(target=video_thread, name="video", daemon=True)
    thread.start()

    t0 = time.time()
    try:
        scr = script_stage(cfg, paths, "templates" if args.no_wan and args.script_mode == "auto" else args.script_mode)
    finally:
        script_done.set()
    stamps["script"] = round(time.time() - t0, 1)

    t0 = time.time()
    voiced = voice_stage(cfg, scr, paths)
    stamps["voice"] = round(time.time() - t0, 1)
    t0 = time.time()
    caps, srt_path = captions_stage(cfg, voiced, paths)
    music_wav = music_stage(args.music, paths, voiced["wav"])
    stamps["captions+music"] = round(time.time() - t0, 1)

    log("pipeline", "audio and captions ready; waiting for the video clip")
    thread.join()
    stamps["video (ran alongside audio)"] = video["seconds"]

    t0 = time.time()
    if video["ok"]:
        loop_src = os.path.join(paths.work, "wan_pingpong.mp4")
        render.run(render.pingpong_cmd(clip_path, loop_src, frames=video["frames"]))
        motion = "AI clip: %d frames (%.1fs), %s, looped forward and backward with a slow zoom and pan" % (
            video["frames"], video["frames"] / 16.0, video["dtype"])
    else:
        loop_src = os.path.join(paths.work, "still.mp4")
        render.run(render.still_cmd(image_path, loop_src))
        motion = "FALLBACK: slow zoom and pan on the photo (no AI motion) because: %s" % video["error"]
    log("render", motion)
    log("render", "rendering the final %dx%d MP4 (zoom, captions, closing card, voice, music)" % (spec.W, spec.H))
    final_name = "advvideo_%s.mp4" % config.slugify(cfg["product_name"])
    final_path = os.path.join(paths.out, final_name)
    render.run(render.final_cmd(loop_src, voiced["wav"], music_wav, final_path, caps))
    info = render.probe(final_path)
    problems = render.check_output(info)
    stamps["final render"] = round(time.time() - t0, 1)

    report = {"version": __version__, "output": final_path, "info": info, "problems": problems, "motion": motion,
              "script_source": scr["source"], "voice": voice.VOICES[cfg["language"]]["id"],
              "voice_license": voice.VOICES[cfg["language"]]["license"], "captions": caps["mode"], "end_card": caps.get("card"),
              "stage_seconds": stamps, "total_minutes": round((time.time() - started) / 60.0, 1)}
    with open(os.path.join(paths.out, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    shutil.copy(os.path.join(paths.work, "script.json"), os.path.join(paths.out, "script.json"))
    log("pipeline", "DONE in %.1f min: %s (%sx%s, %.1fs, %s/%s)" % (report["total_minutes"], final_name, info["width"], info["height"],
        info["duration"], info["vcodec"], info["acodec"]))
    for name, seconds in stamps.items():
        log("pipeline", "  %-30s %6.1fs" % (name, seconds or 0))
    if problems:
        log("pipeline", "CHECK FAILED: " + "; ".join(problems))
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except config.ConfigError as exc:
        print("Input problem: %s" % exc, file=sys.stderr)
        sys.exit(64)
