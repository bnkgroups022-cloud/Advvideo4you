import json

from advvideo import render


DRAW = {"mode": "drawtext", "filters": ["drawtext=text='a'", "drawtext=text='b'"]}
ASS = {"mode": "ass", "file": "/content/w/caps.ass", "fontsdir": "/content/fonts"}


def test_final_command_shape():
    cmd = render.final_cmd("pp.mp4", "voice.wav", "music.wav", "out.mp4", DRAW)
    assert cmd[0] == "ffmpeg" and cmd[-1] == "out.mp4"
    assert cmd[cmd.index("-t") + 1] == "15.00" and cmd[cmd.index("-r") + 1] == "30"
    assert cmd[cmd.index("-c:v") + 1] == "libx264" and cmd[cmd.index("-c:a") + 1] == "aac"
    assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p" and "+faststart" in cmd
    assert cmd[cmd.index("-map") + 1] == "[v]" and cmd[cmd.index("-map", cmd.index("-map") + 1) + 1] == "[a]"
    inputs = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-i"]
    assert inputs == ["pp.mp4", "voice.wav", "music.wav"]
    assert cmd.index("-stream_loop") < cmd.index("-i")


def test_video_graph_targets_1080x1920_and_includes_captions():
    g = render.video_graph(DRAW, 15.0)
    assert g.startswith("[0:v]fps=30,scale=") and g.endswith("format=yuv420p[v]")
    assert "crop=1080:1920:" in g and "sin(t/2.6)" in g
    assert "drawtext=text='a',drawtext=text='b'" in g
    assert "fade=t=in:st=0:d=0.5" in g and "fade=t=out:st=14.50:d=0.5" in g


def test_video_graph_ass_and_none():
    g = render.video_graph(ASS, 15.0)
    assert "ass=filename='/content/w/caps.ass':fontsdir='/content/fonts'" in g
    plain = render.video_graph({"mode": "none"}, 15.0)
    assert "drawtext" not in plain and "ass=" not in plain


def test_audio_graph_mixes_voice_and_ducked_music():
    g = render.audio_graph(15.0)
    for part in ("[1:a]", "[2:a]", "asplit=2[vo1][vo2]", "sidechaincompress", "[mus][vo2]", "amix=inputs=2", "loudnorm",
                 "alimiter", "afade=t=in:st=0:d=1.2", "afade=t=out:st=12.80:d=2.2", "atrim=0:15.00", "[a]"):
        assert part in g, part
    assert g.count("[") == g.count("]")


def test_labels_are_consistent_across_the_full_graph():
    graph = render.video_graph(DRAW, 15.0) + ";" + render.audio_graph(15.0)
    for label in ("vo1", "vo2", "mus", "duck", "v", "a"):
        assert graph.count("[%s]" % label) >= 1
    produced = {"v", "a", "vo1", "vo2", "mus", "duck"}
    consumed = {"vo1", "vo2", "mus", "duck"}
    assert consumed <= produced


def test_short_totals_keep_fade_times_valid():
    g = render.audio_graph(4.0)
    assert "afade=t=out:st=1.80:d=2.2" in g
    assert "fade=t=out:st=3.50:d=0.5" in render.video_graph(DRAW, 4.0)


def test_pingpong_and_kenburns_commands():
    pp = render.pingpong_cmd("in.mp4", "out.mp4")
    assert "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]" in pp
    kb = render.kenburns_cmd("photo.jpg", "kb.mp4", seconds=15.0)
    assert "zoompan=" in kb[kb.index("-vf") + 1] and kb[kb.index("-frames:v") + 1] == "450"


def test_check_output():
    good = {"width": 1080, "height": 1920, "vcodec": "h264", "acodec": "aac", "duration": 15.02}
    assert render.check_output(good) == []
    assert render.check_output(dict(good, width=720))
    assert render.check_output(dict(good, duration=12.0))
    assert render.check_output(dict(good, acodec=None))
    assert render.check_output(dict(good, vcodec="vp9"))


def test_probe_parses_ffprobe_json(monkeypatch=None):
    payload = json.dumps({"streams": [{"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920},
                                      {"codec_type": "audio", "codec_name": "aac"}], "format": {"duration": "15.010000"}})
    original = render.run
    render.run = lambda cmd, log=None: payload
    try:
        info = render.probe("x.mp4")
    finally:
        render.run = original
    assert info == {"width": 1080, "height": 1920, "vcodec": "h264", "acodec": "aac", "duration": 15.01}
    assert render.check_output(info) == []
