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


def test_layout_shrinks_three_line_captions_and_reports_the_width():
    ev = [{"text": "one two three four five six seven eight nine ten eleven twelve", "start": 0, "end": 2}]
    laid = captions.layout_events(ev, lambda t: len(t) * 10.0)
    assert laid[0]["size"] < captions.FONT_SIZE or len(laid[0]["lines"]) <= 2
    short = captions.layout_events([{"text": "Order now", "start": 0, "end": 2}], lambda t: len(t) * 10.0)
    assert short[0]["size"] == captions.FONT_SIZE and short[0]["lines"] == ["Order now"] and short[0]["width"] == 90.0


def test_scaled_constants_match_the_480_wide_frame():
    assert (captions.VIDEO_W, captions.VIDEO_H) == (480, 832)
    assert captions.FONT_SIZE == 33 and captions.MAX_TEXT_WIDTH == 400


def test_script_runs():
    assert captions.split_runs("Aroma Tea") == [("Aroma Tea", False)]
    assert captions.split_runs("स्वाद चाय") == [("स्वाद चाय", True)]
    assert captions.split_runs("Try Aroma चाय अभी!") == [("Try Aroma ", False), ("चाय अभी!", True)]
    assert captions.split_runs("123 চা")[-1][1] is True
    assert captions.split_runs("") == []


def test_burned_events_leave_the_cta_to_the_closing_card():
    events = [{"text": "h", "start": 0.5, "end": 2.5}, {"text": "f1", "start": 3.0, "end": 5.0}, {"text": "f2", "start": 8.0, "end": 12.4},
              {"text": "f3", "start": 11.9, "end": 13.0}, {"text": "cta", "start": 12.2, "end": 14.5}]
    kept = captions.burned_events(events, ["hook", "feature", "feature", "feature", "cta"], 12.0)
    assert [e["text"] for e in kept] == ["h", "f1", "f2"]          # f3 starts inside the card lead-in, the CTA is the card
    assert all(e["end"] <= 11.9 + 1e-6 for e in kept)


def test_caption_pills_stay_above_the_bottom_safe_area_on_screen():
    for lines in (["one line"], ["two", "lines"], ["a", "b", "c"]):
        x0, y0, w, h, line_h = captions.pill_geometry(lines, captions.FONT_SIZE, 300, bottom=int(captions.VIDEO_H * captions.BOTTOM_SAFE))
        assert y0 + h <= captions.VIDEO_H * 0.80 + 1 and y0 >= 0
        assert x0 >= 0 and x0 + w <= captions.VIDEO_W and abs(x0 - (captions.VIDEO_W - w) / 2) <= 1
    wide = captions.pill_geometry(["x"], captions.FONT_SIZE, 5000, bottom=600)
    assert wide[2] <= captions.VIDEO_W


def test_drawtext_filters_are_well_formed():
    with tempfile.TemporaryDirectory() as d:
        laid = captions.layout_events([{"text": "Hello world", "start": 1.0, "end": 3.0},
                                       {"text": "Second caption here please", "start": 3.5, "end": 6.0}], lambda t: len(t) * 14.0)
        filters = captions.drawtext_filters(laid, "/fonts/NotoSans-Bold.ttf", d)
        assert len(filters) == sum(len(e["lines"]) for e in laid)
        for f in filters:
            assert f.startswith("drawtext=fontfile='/fonts/NotoSans-Bold.ttf':textfile='")
            assert "alpha='if(lt(t," in f and "enable='between(t," in f and "box=1:boxcolor=" in f and "shadowy=2" in f
            assert f.count("'") % 2 == 0
        files = sorted(os.listdir(d))
        assert files and all(name.endswith(".txt") for name in files)
        with open(os.path.join(d, files[0]), encoding="utf-8") as fh:
            assert fh.read() == "Hello world"


def test_drawtext_text_is_in_files_so_odd_characters_are_safe():
    with tempfile.TemporaryDirectory() as d:
        text = "It's 100%: {50% off} \\ \"quoted\", done"
        laid = [{"text": text, "start": 0.0, "end": 2.0, "lines": [text], "size": 33}]
        filters = captions.drawtext_filters(laid, "/f.ttf", d)
        assert "quoted" not in filters[0] and "100%" not in filters[0]
        with open(os.path.join(d, os.listdir(d)[0]), encoding="utf-8") as fh:
            assert fh.read() == text


def test_ffq_escaping():
    assert captions._ffq("/a/b c/d.ttf") == "/a/b c/d.ttf"
    assert captions._ffq("C:/x") == "C\\:/x"
    assert captions._ffq("it's") == "it'\\''s"


def test_rounded_rect_is_a_closed_path_inside_its_box():
    path = captions.rounded_rect(200, 60, 17)
    nums = [int(t) for t in path.replace("m", " ").replace("l", " ").replace("b", " ").split()]
    xs, ys = nums[0::2], nums[1::2]
    assert min(xs) == 0 and max(xs) == 200 and min(ys) == 0 and max(ys) == 60
    assert path.startswith("m 17 0") and path.count("b ") == 4 and path.count("l ") == 4 and path.endswith("17 0")
    assert captions.rounded_rect(10, 6, 99).startswith("m 3 0")            # radius is limited to half the short side


def test_ass_output_has_pills_text_shadow_and_animation():
    laid = [{"text": "नमस्ते दुनिया", "start": 1.0, "end": 3.25, "lines": ["नमस्ते", "दुनिया"], "size": 33, "width": 120.0},
            {"text": "{x}", "start": 3.5, "end": 5.0, "lines": ["{x}"], "size": 27, "width": 40.0}]
    ass = captions.to_ass(laid, "Noto Sans Devanagari", "hi")
    assert "PlayResX: 480" in ass and "PlayResY: 832" in ass
    assert "Style: Cap,Noto Sans Devanagari,66," in ass
    rows = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    pills = [r for r in rows if "\\p1" in r]
    texts = [r for r in rows if "\\p1" not in r]
    assert len(pills) == 2 and len(texts) == 3                        # a box per caption, a text row per line
    assert all(r.startswith("Dialogue: 0,") for r in pills) and all(r.startswith("Dialogue: 1,") for r in texts)
    assert "0:00:01.00,0:00:03.25" in pills[0] and "\\shad3" in pills[0] and "\\1a&H30&" in pills[0]
    assert "\\fad(250,250)" in texts[0] and "\\move(240," in texts[0] and "\\t(0,350," in texts[0] and "\\shad2" in texts[0]
    assert "नमस्ते" in texts[0] and "दुनिया" in texts[1] and "\\{x\\}" in texts[2]


def test_ass_switches_to_the_latin_font_for_product_names_in_hindi_and_bangla():
    laid = [{"text": "Aroma Tea अभी लें", "start": 1.0, "end": 3.0, "lines": ["Aroma Tea अभी लें"], "size": 33, "width": 200.0}]
    ass = captions.to_ass(laid, "Noto Sans Devanagari", "hi")
    assert "{\\fnNoto Sans\\fs50}Aroma Tea {\\fnNoto Sans Devanagari\\fs66}अभी लें" in ass
    plain = captions.to_ass(laid, "Noto Sans", "en")
    assert "\\fnNoto Sans}" not in plain


def test_closing_card_content_timing_and_placement():
    card = captions.make_card("Aroma Tea", "order now", "en", 15.0)
    assert card == {"start": 12.0, "end": 15.0, "title": "Aroma Tea", "cta": "Order Now", "whatsapp": "WhatsApp Today"}
    assert captions.make_card("X", "अभी ऑर्डर करें", "hi")["whatsapp"] == "आज ही WhatsApp करें"
    assert captions.make_card("X", "এখনই অর্ডার করুন", "bn")["whatsapp"].endswith("WhatsApp করুন")
    ass = captions.to_ass([], "Noto Sans", "en", card=card, measure=lambda t: len(t) * 16.0)
    rows = [line for line in ass.splitlines() if line.startswith("Dialogue:")]
    text = "\n".join(rows)
    for needle in ("Aroma Tea", "Order Now", "WhatsApp Today"):
        assert needle in text
    assert all(",0:00:15.00," in r for r in rows)                     # everything lasts to the end
    starts = {r.split(",")[1] for r in rows}
    assert min(starts) == "0:00:12.00" and all(s >= "0:00:12.00" for s in starts)
    assert len(starts) >= 4                                            # dim layer, then staggered title / CTA / WhatsApp
    assert "\\fscx112" in text and "\\fad(" in text and "\\p1" in text
    assert any("\\1c&H00B0FF&" in r for r in rows) and any("\\1c&H7E8C12&" in r for r in rows)


def test_long_product_names_wrap_inside_the_card():
    card = captions.make_card("A Very Long Product Name For Testing The Wrap Behaviour Well", "Order now", "en")
    ass = captions.to_ass([], "Noto Sans", "en", card=card, measure=lambda t: len(t) * 16.0)
    title_rows = [r for r in ass.splitlines() if r.startswith("Dialogue: 2,") and "\\fscx60" in r]
    assert 2 <= len(title_rows) <= 3


def test_drawtext_card_fallback_has_three_timed_lines():
    with tempfile.TemporaryDirectory() as d:
        card = captions.make_card("Aroma Tea", "Order now", "en")
        filters = captions.drawtext_card_filters(card, {"native": "/n.ttf", "latin": "/l.ttf"}, d, "en")
        assert len(filters) == 3 and all(f.endswith(",15.000)'") for f in filters)
        assert "between(t,12.150," in filters[0] and "between(t,12.600," in filters[1] and "between(t,13.000," in filters[2]
        assert "0xFFB000" in filters[1] and "0x128C7E" in filters[2]


def test_ass_time_and_font_table():
    assert captions.ass_time(3661.5) == "1:01:01.50"
    assert set(captions.FONTS) == {"en", "hi", "bn"}
    for name, url, family in captions.FONTS.values():
        assert url.startswith("https://raw.githubusercontent.com/notofonts/") and name.endswith(".ttf") and family.startswith("Noto Sans")


def test_backend_choice():
    full = {"drawtext": True, "ass": True, "harfbuzz": True}
    no_ass = {"drawtext": True, "ass": False, "harfbuzz": True}
    for lang in ("en", "hi", "bn"):
        assert captions.choose_backend(lang, full) == "ass"
        assert captions.choose_backend(lang, no_ass) == "drawtext"
        assert captions.choose_backend(lang, {}) == "none"


def test_parse_ffmpeg_caps():
    conf = "--enable-gpl --enable-libfreetype --enable-libfribidi --enable-libass --enable-libharfbuzz"
    caps = captions.parse_ffmpeg_caps(conf, " T.. drawtext V->V Draw text\n ... ass V->V Render ASS subtitles\n")
    assert caps == {"drawtext": True, "ass": True, "harfbuzz": True, "fribidi": True}
    caps = captions.parse_ffmpeg_caps("--enable-libfreetype", " ... scale V->V\n")
    assert caps == {"drawtext": False, "ass": False, "harfbuzz": False, "fribidi": False}
