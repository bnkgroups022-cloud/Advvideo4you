import json
import os
import tempfile
import types

from advvideo import captions, config, music, pipeline, render, script, voice


def fake_synth(seconds_per_word=0.5):
    calls = []

    def synth(items, length_scale):
        calls.append(length_scale)
        return {i["id"]: len(i["text"].split()) * seconds_per_word * length_scale for i in items}

    synth.calls = calls
    return synth


def items(words=(4, 5, 5, 5, 4)):
    kinds = ["hook", "feature", "feature", "feature", "cta"]
    return [{"id": "seg%d" % i, "kind": k, "text": " ".join(["w"] * n), "caption": "cap%d" % i} for i, (k, n) in enumerate(zip(kinds, words))]


def test_plan_voice_fits_at_normal_speed():
    synth = fake_synth(0.4)
    r = pipeline.plan_voice(items(), synth)
    assert r["plan"]["fits"] and r["length_scale"] == 1.0 and not r["dropped"] and synth.calls == [1.0]
    assert len(r["items"]) == 5


def test_plan_voice_speeds_up_and_resynthesises():
    synth = fake_synth(0.75)     # 23 words * 0.75 = 17s: too long at normal speed
    r = pipeline.plan_voice(items(), synth)
    assert r["plan"]["fits"] and r["length_scale"] < 1.0 and not r["dropped"]
    assert synth.calls[0] == 1.0 and len(synth.calls) >= 2
    assert r["plan"]["ends"][-1] <= pipeline.TOTAL - 0.9 + 1e-3
    assert r["plan"]["speedup"] <= 1.02


def test_plan_voice_drops_a_middle_feature_when_speed_alone_is_not_enough():
    synth = fake_synth(0.95)     # 23 words * 0.95 = 21.9 s: too long even at the fastest allowed speech rate
    r = pipeline.plan_voice(items(), synth)
    assert len(r["dropped"]) == 1 and r["items"][0]["kind"] == "hook" and r["items"][-1]["kind"] == "cta"
    assert sum(1 for i in r["items"] if i["kind"] == "feature") == 2
    assert r["plan"]["fits"] and r["plan"]["speedup"] <= 1.02
    assert r["plan"]["ends"][-1] <= pipeline.TOTAL - 0.9 + 1e-3
    assert r["length_scale"] >= voice.MIN_LENGTH_SCALE


def test_plan_voice_last_resort_is_sequential_and_never_overlaps():
    synth = fake_synth(2.0)      # hopeless: even four segments cannot fit
    r = pipeline.plan_voice(items(), synth)
    plan = r["plan"]
    assert not plan["fits"] and plan["speedup"] == 1.0
    ends = plan["ends"]
    assert all(plan["starts"][i + 1] >= ends[i] for i in range(len(ends) - 1))

def test_ladder_walk():
    def walk(codes, ladder=(33, 25, 17)):
        calls, it = [], iter(codes)

        def rung(n, dtype):
            calls.append((n, dtype))
            return next(it, 3)

        return pipeline.ladder_walk(list(ladder), rung), calls

    assert walk([0])[0] == (33, "float16")
    assert walk([3, 0])[0] == (25, "float16")
    res, calls = walk([4, 0])
    assert res == (33, "bfloat16") and calls[0] == (33, "float16")
    assert walk([4, 4])[0] is None
    res, calls = walk([3, 3, 3])
    assert res is None and len(calls) == 3
    assert walk([1])[0] is None and len(walk([1])[1]) == 1


def test_paths_create_their_folders():
    with tempfile.TemporaryDirectory() as d:
        p = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        for folder in (p.input, p.audio, p.caps, p.fonts, p.voices, p.out):
            assert os.path.isdir(folder)
        assert p.embeds.endswith(".pt") and "prompt_embeds_" in p.embeds


def make_args(**kw):
    base = dict(launch=None, image=None, name=None, language="en", cta="", spoken_name="", details="")
    base.update(kw)
    return types.SimpleNamespace(**base)


def png_bytes():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), (1, 2, 3)).save(buf, "PNG")
    return buf.getvalue()


def test_load_inputs_from_a_launch_file():
    with tempfile.TemporaryDirectory() as d:
        paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        launch = os.path.join(d, "launch.json")
        with open(launch, "w", encoding="utf-8") as fh:
            fh.write(config.build_launch("Aroma Tea", "hi", "", png_bytes()))
        cfg, image = pipeline.load_inputs(make_args(launch=launch), paths)
        assert cfg["product_name"] == "Aroma Tea" and cfg["language"] == "hi" and cfg["cta"] == config.DEFAULT_CTA["hi"]
        assert image.endswith("product.png") and os.path.getsize(image) > 50


def test_load_inputs_from_arguments_and_uploaded_image():
    with tempfile.TemporaryDirectory() as d:
        paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        img = os.path.join(d, "photo.png")
        open(img, "wb").write(png_bytes())
        cfg, image = pipeline.load_inputs(make_args(name="Nike Air", language="en", cta="Shop now", image=img), paths)
        assert cfg["cta"] == "Shop now" and image.endswith("product.png")


def test_load_inputs_rejects_missing_pieces():
    with tempfile.TemporaryDirectory() as d:
        paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        for args in (make_args(), make_args(name="X")):
            try:
                pipeline.load_inputs(args, paths)
            except config.ConfigError:
                continue
            raise AssertionError("expected ConfigError")
        bad = os.path.join(d, "bad.txt")
        open(bad, "wb").write(b"not an image")
        try:
            pipeline.load_inputs(make_args(name="X", image=bad), paths)
        except config.ConfigError:
            return
        raise AssertionError("expected ConfigError for a non-image")


def test_script_stage_with_templates_writes_script_json():
    with tempfile.TemporaryDirectory() as d:
        paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        cfg = config.validate_fields("Aroma Tea", "bn", "")
        result = pipeline.script_stage(cfg, paths, "templates")
        assert result["source"] == "templates" and len(result["features"]) == 3
        saved = json.load(open(os.path.join(paths.work, "script.json"), encoding="utf-8"))
        assert saved["hook"] == result["hook"]


def stub_render_environment(harfbuzz):
    render.buildconf_and_filters = lambda ffmpeg="ffmpeg": (
        "--enable-libfreetype --enable-libfribidi --enable-libass" + (" --enable-libharfbuzz" if harfbuzz else ""),
        " T. drawtext V->V x\n T. ass V->V y\n")
    captions.ensure_font = lambda lang, dest: os.path.join(dest, "missing-font.ttf")   # measure falls back to estimates


def test_captions_stage_picks_the_backend_by_language_and_ffmpeg():
    original = (render.buildconf_and_filters, captions.ensure_font)
    try:
        with tempfile.TemporaryDirectory() as d:
            paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
            for lang, harfbuzz, expected in (("en", False, "drawtext"), ("hi", False, "ass"), ("bn", True, "drawtext")):
                stub_render_environment(harfbuzz)
                cfg = config.validate_fields("Aroma Tea", lang, "")
                segs = script.segments(script.template_script(cfg), cfg)
                items_ = [{"id": "seg%d" % i, "kind": s["kind"], "caption": s["caption"]} for i, s in enumerate(segs)]
                plan = voice.plan_timeline([2.0] * 5)
                voiced = {"items": items_, "plan": plan}
                caps, srt = pipeline.captions_stage(cfg, voiced, paths)
                assert caps["mode"] == expected, (lang, harfbuzz, caps["mode"])
                assert os.path.exists(srt) and open(srt, encoding="utf-8").read().count("-->") == 5
                if expected == "ass":
                    assert os.path.exists(caps["file"]) and "Dialogue:" in open(caps["file"], encoding="utf-8").read()
                else:
                    assert len(caps["filters"]) >= 5
    finally:
        render.buildconf_and_filters, captions.ensure_font = original


def test_music_stage_writes_audio_for_every_style():
    import wave
    with tempfile.TemporaryDirectory() as d:
        paths = pipeline.Paths(os.path.join(d, "w"), os.path.join(d, "c"), os.path.join(d, "o"))
        for style in ("none", "calm"):
            wav = pipeline.music_stage(style, paths)
            with wave.open(wav, "rb") as w:
                assert w.getnchannels() == 2 and w.getnframes() >= int(pipeline.TOTAL * music.SR)


def test_verify_checkpoint_and_constants():
    with tempfile.TemporaryDirectory() as d:
        assert pipeline.verify_checkpoint(d)
        original = dict(pipeline.WAN_REQUIRED)
        pipeline.WAN_REQUIRED.clear()
        pipeline.WAN_REQUIRED.update({"a.bin": 3, "sub/b.bin": 2})
        try:
            os.makedirs(os.path.join(d, "sub"))
            open(os.path.join(d, "a.bin"), "wb").write(b"123")
            open(os.path.join(d, "sub", "b.bin"), "wb").write(b"1")
            assert any("only" in p for p in pipeline.verify_checkpoint(d))
            open(os.path.join(d, "sub", "b.bin"), "wb").write(b"12")
            assert pipeline.verify_checkpoint(d) == []
        finally:
            pipeline.WAN_REQUIRED.clear()
            pipeline.WAN_REQUIRED.update(original)
    assert pipeline.FRAME_LADDER[0] == 33 and all((n - 1) % 4 == 0 for n in pipeline.FRAME_LADDER)
    assert len(pipeline.WAN_REPO_COMMIT) == 40 and pipeline.TOTAL == 15.0
    assert "product from the photo" in pipeline.MOTION_PROMPT
