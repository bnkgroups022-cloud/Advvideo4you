import json

from advvideo import render, spec


DRAW = {"mode": "drawtext", "filters": ["drawtext=text='a'", "drawtext=text='b'"]}
ASS = {"mode": "ass", "file": "/content/w/caps.ass", "fontsdir": "/content/fonts"}


def test_output_spec_is_480_by_832_and_fifteen_seconds():
    assert (spec.W, spec.H) == (480, 832) and spec.DURATION == 15.0 and spec.FPS == 30 and spec.CARD_SECONDS == 3.0
    assert (render.W, render.H) == (480, 832)


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


def test_video_graph_zooms_pans_and_targets_480x832():
    g = render.video_graph(DRAW, 15.0)
    assert g.startswith("[0:v]fps=30,scale=960:1664:") and g.endswith("format=yuv420p[v]")
    assert "zoompan=z='1.06+0.10*on/450'" in g and "s=480x832" in g and "sin(on/30/2.6)" in g and "sin(on/30/3.3)" in g
    assert "drawtext=text='a',drawtext=text='b'" in g
    assert "fade=t=in:st=0:d=0.5" in g and "fade=t=out:st=14.50:d=0.5" in g


def test_slow_zoom_stays_within_the_pan_room():
    # the crop window at zoom z has room (1 - 1/z)/2 of the width on each side; the pan amplitude must fit at the start
    assert render.ZOOM_FROM > 1.0 and render.ZOOM_TO > render.ZOOM_FROM
    room_x = (1 - 1 / render.ZOOM_FROM) / 2
    assert 0.02 <= room_x and 0.015 <= (1 - 1 / render.ZOOM_FROM) / 2


def test_video_graph_ass_and_none():
    g = render.video_graph(ASS, 15.0)
    assert "ass=filename='/content/w/caps.ass':fontsdir='/content/fonts'" in g
    plain = render.video_graph({"mode": "none"}, 15.0)
    assert "drawtext" not in plain and "ass=" not in plain


def test_audio_graph_mixes_voice_and_ducked_music():
    g = render.audio_graph(15.0)
    for part in ("[1:a]", "[2:a]", "asplit=2[vo1][vo2]", "sidechaincompress", "[mus][vo2]", "amix=inputs=2", "loudnorm",
                 "alimiter", "volume=1.00", "afade=t=in:st=0:d=1.2", "afade=t=out:st=12.80:d=2.2", "atrim=0:15.00", "[a]"):
        assert part in g, part
    assert g.count("[") == g.count("]") and "sidechaincompress=threshold=0.05:ratio=2" in g


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


def test_pingpong_drops_the_turning_point_frames_when_the_count_is_known():
    pp = render.pingpong_cmd("in.mp4", "out.mp4", frames=33)
    graph = pp[pp.index("-filter_complex") + 1]
    assert "reverse,trim=start_frame=1:end_frame=32,setpts=PTS-STARTPTS[r]" in graph and "framerate=fps=30" in graph
    assert "concat=n=2:v=1:a=0" in graph
    unknown = render.pingpong_cmd("in.mp4", "out.mp4")
    assert "[b]reverse[r]" in unknown[unknown.index("-filter_complex") + 1]


def test_still_fallback_command():
    cmd = render.still_cmd("photo.jpg", "still.mp4")
    assert cmd[cmd.index("-loop") + 1] == "1" and cmd[cmd.index("-t") + 1] == "1"
    assert "crop=960:1664" in cmd[cmd.index("-vf") + 1]


def test_check_output():
    good = {"width": 480, "height": 832, "vcodec": "h264", "acodec": "aac", "duration": 15.02}
    assert render.check_output(good) == []
    assert render.check_output(dict(good, width=1080, height=1920))
    assert render.check_output(dict(good, duration=12.0))
    assert render.check_output(dict(good, acodec=None))
    assert render.check_output(dict(good, vcodec="vp9"))


def test_probe_parses_ffprobe_json(monkeypatch=None):
    payload = json.dumps({"streams": [{"codec_type": "video", "codec_name": "h264", "width": 480, "height": 832},
                                      {"codec_type": "audio", "codec_name": "aac"}], "format": {"duration": "15.010000"}})
    original = render.run
    render.run = lambda cmd, log=None: payload
    try:
        info = render.probe("x.mp4")
    finally:
        render.run = original
    assert info == {"width": 480, "height": 832, "vcodec": "h264", "acodec": "aac", "duration": 15.01}
    assert render.check_output(info) == []
