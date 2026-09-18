import os
import re
import tempfile

from advvideo import captions


def measure(text):
    return len(text) * 40.0


def test_srt_time_format():
    assert captions.srt_time(0) == "00:00:00,000"
    assert captions.srt_time(1.5) == "00:00:01,500"
    assert captions.srt_time(61.234) == "00:01:01,234"
    assert captions.srt_time(3600.0) == "01:00:00,000"


def test_srt_structure_and_unicode():
    events = [{"text": "नमस्ते", "start": 0.5, "end": 2.0}, {"text": "Second line", "start": 2.2, "end": 4.0}]
    srt = captions.to_srt(events)
    blocks = srt.strip().split("\n\n")
    assert len(blocks) == 2
    assert blocks[0].splitlines() == ["1", "00:00:00,500 --> 00:00:02,000", "नमस्ते"]
    assert blocks[1].splitlines()[0] == "2"
    assert re.fullmatch(r"\d\d:\d\d:\d\d,\d{3} --> \d\d:\d\d:\d\d,\d{3}", blocks[1].splitlines()[1])


def test_caption_events_never_overlap_and_stay_inside_the_video():
    starts, ends = [0.35, 2.9, 5.4, 7.9, 11.0], [2.6, 5.1, 7.6, 10.1, 13.4]
    ev = captions.caption_events(list("abcde"), starts, ends, total=15.0)
    assert len(ev) == 5
    for i, e in enumerate(ev):
        assert 0 <= e["start"] < e["end"] <= 15.0
        assert e["start"] <= starts[i] and e["end"] >= ends[i] - 1e-6
        if i + 1 < len(ev):
            assert e["end"] <= ev[i + 1]["start"] + 1e-6


def test_wrap_lines():
    assert captions.wrap_lines("a b c", measure, 10000) == ["a b c"]
    assert captions.wrap_lines("aaaa bbbb cccc dddd", measure, 400) == ["aaaa bbbb", "cccc dddd"]
    assert captions.wrap_lines("unbreakable" * 5, measure, 100) == ["unbreakable" * 5]
    assert captions.wrap_lines("", measure) == []


def test_layout_shrinks_three_line_captions():
    ev = [{"text": "one two three four five six seven eight nine ten eleven twelve", "start": 0, "end": 2}]
    laid = captions.layout_events(ev, lambda t: len(t) * 30.0)
    assert laid[0]["size"] < captions.FONT_SIZE or len(laid[0]["lines"]) <= 2
    short = captions.layout_events([{"text": "Order now", "start": 0, "end": 2}], measure)
    assert short[0]["size"] == captions.FONT_SIZE and short[0]["lines"] == ["Order now"]


def test_drawtext_filters_are_well_formed():
    with tempfile.TemporaryDirectory() as d:
        laid = captions.layout_events([{"text": "Hello world", "start": 1.0, "end": 3.0},
                                       {"text": "Second caption here please", "start": 3.5, "end": 6.0}], lambda t: len(t) * 60.0)
        filters = captions.drawtext_filters(laid, "/fonts/NotoSans-Bold.ttf", d)
        assert len(filters) == sum(len(e["lines"]) for e in laid)
        for f in filters:
            assert f.startswith("drawtext=fontfile='/fonts/NotoSans-Bold.ttf':textfile='")
            assert "alpha='if(lt(t," in f and "enable='between(t," in f and "y='h*0.640" in f
            assert f.count("'") % 2 == 0
        files = sorted(os.listdir(d))
        assert files and all(name.endswith(".txt") for name in files)
        with open(os.path.join(d, files[0]), encoding="utf-8") as fh:
            assert fh.read() == "Hello world"


def test_drawtext_text_is_in_files_so_odd_characters_are_safe():
    with tempfile.TemporaryDirectory() as d:
        text = "It's 100%: {50% off} \\ \"quoted\", done"
        laid = [{"text": text, "start": 0.0, "end": 2.0, "lines": [text], "size": 74}]
        filters = captions.drawtext_filters(laid, "/f.ttf", d)
        assert "quoted" not in filters[0] and "100%" not in filters[0]
        with open(os.path.join(d, os.listdir(d)[0]), encoding="utf-8") as fh:
            assert fh.read() == text


def test_ffq_escaping():
    assert captions._ffq("/a/b c/d.ttf") == "/a/b c/d.ttf"
    assert captions._ffq("C:/x") == "C\\:/x"
    assert captions._ffq("it's") == "it'\\''s"


def test_ass_output():
    laid = [{"text": "नमस्ते दुनिया", "start": 1.0, "end": 3.25, "lines": ["नमस्ते", "दुनिया"], "size": 74},
            {"text": "{x}", "start": 3.5, "end": 5.0, "lines": ["{x}"], "size": 60}]
    ass = captions.to_ass(laid, "Noto Sans Devanagari", "hi")
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass
    assert "Style: Cap,Noto Sans Devanagari,148" in ass
    rows = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    assert len(rows) == 2
    assert "0:00:01.00,0:00:03.25" in rows[0] and "नमस्ते\\Nदुनिया" in rows[0]
    assert "\\fad(250,250)" in rows[0] and "\\move(540," in rows[0] and "\\t(0,350," in rows[0]
    assert "\\{x\\}" in rows[1]


def test_ass_time_and_font_table():
    assert captions.ass_time(3661.5) == "1:01:01.50"
    assert set(captions.FONTS) == {"en", "hi", "bn"}
    for name, url, family in captions.FONTS.values():
        assert url.startswith("https://raw.githubusercontent.com/notofonts/") and name.endswith(".ttf") and family.startswith("Noto Sans")


def test_backend_choice():
    full = {"drawtext": True, "ass": True, "harfbuzz": True}
    no_hb = {"drawtext": True, "ass": True, "harfbuzz": False}
    only_dt = {"drawtext": True, "ass": False, "harfbuzz": False}
    assert captions.choose_backend("en", no_hb) == "drawtext"
    assert captions.choose_backend("hi", full) == "drawtext"
    assert captions.choose_backend("hi", no_hb) == "ass"
    assert captions.choose_backend("bn", no_hb) == "ass"
    assert captions.choose_backend("hi", only_dt) == "drawtext"
    assert captions.choose_backend("en", {}) == "none"


def test_parse_ffmpeg_caps():
    conf = "--enable-gpl --enable-libfreetype --enable-libfribidi --enable-libass --enable-libharfbuzz"
    caps = captions.parse_ffmpeg_caps(conf, " T.. drawtext V->V Draw text\n ... ass V->V Render ASS subtitles\n")
    assert caps == {"drawtext": True, "ass": True, "harfbuzz": True, "fribidi": True}
    caps = captions.parse_ffmpeg_caps("--enable-libfreetype", " ... scale V->V\n")
    assert caps == {"drawtext": False, "ass": False, "harfbuzz": False, "fribidi": False}
