"""Captions: SRT file, and animated on-screen text burned in by FFmpeg.

English (and Hindi/Bangla when FFmpeg has HarfBuzz) uses the ``drawtext`` filter: one filter per caption line, each
fading in while sliding up and fading out. Hindi and Bangla need complex-script shaping; if this FFmpeg build's
drawtext cannot do it, the same animation is produced as an ASS subtitle file rendered by libass, which always shapes.
"""
import os
import re
import urllib.request

FONT_BASE = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/"
FONTS = {  # Noto Sans, SIL Open Font License 1.1
    "en": ("NotoSans-Bold.ttf", FONT_BASE + "NotoSans/hinted/ttf/NotoSans-Bold.ttf", "Noto Sans"),
    "hi": ("NotoSansDevanagari-Bold.ttf", FONT_BASE + "NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Bold.ttf", "Noto Sans Devanagari"),
    "bn": ("NotoSansBengali-Bold.ttf", FONT_BASE + "NotoSansBengali/hinted/ttf/NotoSansBengali-Bold.ttf", "Noto Sans Bengali"),
}
VIDEO_W, VIDEO_H = 1080, 1920
FONT_SIZE = 74
MAX_TEXT_WIDTH = 900          # pixels; leaves a 90 px margin each side
FADE = 0.25
# libass sizes text by the font's full line height, so the same nominal size renders smaller than drawtext's pixel size.
# Calibrated by rendering the same caption both ways (ffmpeg 5.1 + libass) and comparing widths.
ASS_SIZE_FACTOR = {"en": 1.5, "hi": 2.0, "bn": 1.6}


def ensure_font(lang, dest):
    """Path to the Bold Noto font for a language, downloading it once."""
    filename, url, _family = FONTS[lang]
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, filename)
    if not os.path.exists(path) or os.path.getsize(path) < 50000:
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
    return path


def caption_events(texts, starts, ends, total=15.0, lead_in=0.12, linger=0.45):
    """Caption timing: appears slightly before the voice, lingers after it, never overlaps the next caption."""
    events = []
    for i, text in enumerate(texts):
        start = max(0.0, starts[i] - lead_in)
        end = ends[i] + linger
        if i + 1 < len(texts):
            end = min(end, max(starts[i + 1] - lead_in - 0.05, ends[i] + 0.1))
        end = min(end, total - 0.05)
        events.append({"text": text, "start": round(start, 3), "end": round(max(end, start + 0.4), 3)})
    return events


def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def to_srt(events):
    blocks = []
    for i, ev in enumerate(events, 1):
        blocks.append("%d\n%s --> %s\n%s\n" % (i, srt_time(ev["start"]), srt_time(ev["end"]), ev["text"]))
    return "\n".join(blocks)


def make_measure(font_path, size=FONT_SIZE):
    """Pixel width function using Pillow (basic layout, so complex scripts are approximate); falls back to characters."""
    try:
        from PIL import ImageFont
        font = ImageFont.truetype(font_path, size)
        return lambda text: font.getlength(text)
    except Exception:
        return lambda text: len(text) * size * 0.58


def wrap_lines(text, measure, max_width=MAX_TEXT_WIDTH):
    """Greedy word wrap. A single word wider than max_width stays on its own line."""
    lines, current = [], ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if current and measure(trial) > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def layout_events(events, measure):
    """Adds wrapped ``lines`` and a ``size`` (shrunk if a caption needs three or more lines)."""
    laid = []
    for ev in events:
        lines = wrap_lines(ev["text"], measure)
        size = FONT_SIZE
        if len(lines) > 2:
            scale = 0.82
            shrunk = lambda t, s=scale: measure(t) * s
            lines = wrap_lines(ev["text"], shrunk)
            size = int(FONT_SIZE * scale)
        laid.append(dict(ev, lines=lines, size=size))
    return laid


def _ffq(value):
    """Escape a value for use inside single quotes in an FFmpeg filter option."""
    return str(value).replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")


def drawtext_filters(laid, font_path, workdir, y_frac=0.64):
    """One animated drawtext filter per caption line. Text goes through files, so no filter-escaping of the words."""
    os.makedirs(workdir, exist_ok=True)
    filters = []
    for i, ev in enumerate(laid):
        a, b, size = ev["start"], ev["end"], ev["size"]
        line_h = int(size * 1.28)
        block_h = line_h * len(ev["lines"])
        alpha = "if(lt(t,%.3f),(t-%.3f)/%.3f,if(gt(t,%.3f),(%.3f-t)/%.3f,1))" % (a + FADE, a, FADE, b - FADE, b, FADE)
        for k, line in enumerate(ev["lines"]):
            path = os.path.join(workdir, "cap_%02d_%d.txt" % (i, k))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(line)
            y = "h*%.3f-%d+%d+40*pow(1-min(1,max(0,(t-%.3f)/0.35)),2)" % (y_frac, block_h // 2, k * line_h, a)
            filters.append(
                "drawtext=fontfile='%s':textfile='%s':fontsize=%d:fontcolor=white:borderw=6:bordercolor=black@0.9:"
                "shadowx=0:shadowy=5:shadowcolor=black@0.45:x=(w-text_w)/2:y='%s':alpha='%s':enable='between(t,%.3f,%.3f)'"
                % (_ffq(font_path), _ffq(path), size, y, alpha, a, b))
    return filters


def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def ass_time(seconds):
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return "%d:%02d:%02d.%02d" % (h, m, s, cs)


def to_ass(laid, family, lang="en", y_frac=0.64):
    """ASS subtitles with the same fade + slide + pop animation, rendered (and shaped) by libass."""
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Cap,%s,%d,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,5,90,90,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        % (VIDEO_W, VIDEO_H, family, int(round(FONT_SIZE * ASS_SIZE_FACTOR[lang]))))
    rows = []
    for ev in laid:
        x, y = VIDEO_W // 2, int(VIDEO_H * y_frac)
        text = "\\N".join(ass_escape(line) for line in ev["lines"])
        scale = int(round(100.0 * ev["size"] / FONT_SIZE))
        tags = "{\\an5\\move(%d,%d,%d,%d,0,350)\\fad(%d,%d)\\fscx%d\\fscy%d\\t(0,350,\\fscx%d\\fscy%d)}" % (
            x, y + 40, x, y, int(FADE * 1000), int(FADE * 1000), scale * 88 // 100, scale * 88 // 100, scale, scale)
        rows.append("Dialogue: 0,%s,%s,Cap,,0,0,0,,%s%s" % (ass_time(ev["start"]), ass_time(ev["end"]), tags, text))
    return header + "\n".join(rows) + "\n"


def parse_ffmpeg_caps(buildconf_text, filters_text):
    """What this FFmpeg build can do for captions, from ``-buildconf`` and ``-filters`` output."""
    return {
        "drawtext": bool(re.search(r"\bdrawtext\b", filters_text)),
        "ass": bool(re.search(r"\bass\b", filters_text)) and "--enable-libass" in buildconf_text,
        "harfbuzz": "--enable-libharfbuzz" in buildconf_text,
        "fribidi": "--enable-libfribidi" in buildconf_text,
    }


def choose_backend(lang, caps):
    """'drawtext' when it can render the script correctly, else 'ass' (libass shapes Devanagari/Bengali)."""
    if lang == "en":
        return "drawtext" if caps.get("drawtext") else ("ass" if caps.get("ass") else "none")
    if caps.get("drawtext") and caps.get("harfbuzz"):
        return "drawtext"
    if caps.get("ass"):
        return "ass"
    return "drawtext" if caps.get("drawtext") else "none"
