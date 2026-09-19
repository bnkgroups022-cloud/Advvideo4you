"""Captions: an SRT file, and animated on-screen text burned in by FFmpeg, plus the closing call-to-action card.

The default renderer is an ASS subtitle file drawn by libass: every caption sits on a rounded dark pill with a drop
shadow, fades in while sliding up, and fades out; libass also shapes Hindi and Bangla correctly. If this FFmpeg has no
libass the same layout is produced with ``drawtext`` (one filter per line, rectangular box instead of a rounded one).
Captions stay above the bottom 20% of the frame, where phone apps put their buttons.
"""
import os
import re
import string
import urllib.request

from advvideo.spec import CARD_SECONDS, H, K, W

FONT_BASE = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts/"
FONTS = {  # Noto Sans, SIL Open Font License 1.1
    "en": ("NotoSans-Bold.ttf", FONT_BASE + "NotoSans/hinted/ttf/NotoSans-Bold.ttf", "Noto Sans"),
    "hi": ("NotoSansDevanagari-Bold.ttf", FONT_BASE + "NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Bold.ttf", "Noto Sans Devanagari"),
    "bn": ("NotoSansBengali-Bold.ttf", FONT_BASE + "NotoSansBengali/hinted/ttf/NotoSansBengali-Bold.ttf", "Noto Sans Bengali"),
}
VIDEO_W, VIDEO_H = W, H
FONT_SIZE = int(round(74 * K))         # pixels
MAX_TEXT_WIDTH = int(round(900 * K))
PAD_X, PAD_Y = int(round(40 * K)), int(round(26 * K))
RADIUS = int(round(38 * K))
SLIDE = int(round(40 * K))
LINE_H = 1.28
BOTTOM_SAFE = 0.80                     # a caption pill never extends below 80% of the height
FADE = 0.25
# libass sizes text by the font's full line height, so the same nominal size renders smaller than drawtext's pixel size.
# Calibrated by rendering the same caption both ways (ffmpeg 5.1 + libass) and comparing widths.
ASS_SIZE_FACTOR = {"en": 1.5, "hi": 2.0, "bn": 1.6}
PILL_FILL, PILL_ALPHA = "&H2A1A10&", "&H30&"          # ASS colours are BGR: a dark navy, about 80% opaque
ORDER_FILL, ORDER_TEXT = "&H00B0FF&", "&H141414&"      # amber pill, near-black text
WHATSAPP_FILL = "&H7E8C12&"                            # WhatsApp dark green (#128C7E), white text
WHATSAPP_LINE = {"en": "WhatsApp Today", "hi": "आज ही WhatsApp करें", "bn": "আজই WhatsApp করুন"}


def ensure_font(lang, dest):
    """Path to the Bold Noto font for a language, downloading it once."""
    filename, url, _family = FONTS[lang]
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, filename)
    if not os.path.exists(path) or os.path.getsize(path) < 50000:
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
    return path


def ensure_fonts(lang, dest):
    """The language's font and the Latin font (product names and 'WhatsApp' are Latin in every language)."""
    latin = ensure_font("en", dest)
    return {"native": ensure_font(lang, dest) if lang != "en" else latin, "latin": latin}


def is_native(ch):
    return 0x0900 <= ord(ch) <= 0x09FF          # Devanagari and Bengali blocks


def split_runs(text):
    """[(text, is_native)] runs. Spaces, digits and punctuation join the run before them."""
    kinds = []
    for ch in text:
        kinds.append(True if is_native(ch) else (False if ch.isalpha() else None))
    last = next((k for k in kinds if k is not None), False)
    for i, k in enumerate(kinds):
        if k is None:
            kinds[i] = last
        else:
            last = k
    runs = []
    for ch, k in zip(text, kinds):
        if runs and runs[-1][1] == k:
            runs[-1][0] += ch
        else:
            runs.append([ch, k])
    return [(t, k) for t, k in runs]


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


def burned_events(events, kinds, card_start):
    """The events drawn on the picture: the CTA line is shown by the closing card instead, and no caption runs into it."""
    keep = []
    for ev, kind in zip(events, kinds):
        if kind == "cta":
            continue
        if ev["start"] >= card_start - 0.3:
            continue
        keep.append(dict(ev, end=round(min(ev["end"], card_start - 0.1), 3)))
    return keep


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


def make_measure(font_path, size=FONT_SIZE, latin_path=None):
    """Pixel width function using Pillow (basic layout, so complex scripts are approximate); falls back to characters."""
    try:
        from PIL import ImageFont
        native = ImageFont.truetype(font_path, size)
        latin = ImageFont.truetype(latin_path, size) if latin_path else native
    except Exception:
        return lambda text: len(text) * size * 0.58
    return lambda text: sum((native if is_nat else latin).getlength(part) for part, is_nat in split_runs(text))


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
    """Adds wrapped ``lines``, a ``size`` (shrunk if a caption needs three or more lines) and the text ``width``."""
    laid = []
    for ev in events:
        lines = wrap_lines(ev["text"], measure)
        scale = 1.0
        if len(lines) > 2:
            scale = 0.82
            lines = wrap_lines(ev["text"], lambda t, s=scale: measure(t) * s)
        width = max([measure(line) for line in lines] or [0.0]) * scale
        laid.append(dict(ev, lines=lines, size=int(FONT_SIZE * scale), width=width))
    return laid


def pill_geometry(lines, size, width, cx=None, top=None, bottom=None, center_y=None):
    """(x0, y0, w, h, line_h) of the rounded box around ``lines``; give exactly one of top, bottom or center_y."""
    line_h = int(size * LINE_H)
    h = line_h * len(lines) + 2 * PAD_Y
    w = min(int(width) + 2 * PAD_X, VIDEO_W - 2 * int(round(24 * K)))
    x0 = int(((VIDEO_W if cx is None else 2 * cx) - w) // 2)
    if top is not None:
        y0 = int(top)
    elif bottom is not None:
        y0 = int(bottom) - h
    else:
        y0 = int(center_y) - h // 2
    return x0, y0, w, h, line_h


def _ffq(value):
    """Escape a value for use inside single quotes in an FFmpeg filter option."""
    return str(value).replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")


# ----------------------------------------------------------------------------- drawtext (fallback without libass)
def drawtext_filters(laid, font_path, workdir):
    """One animated drawtext filter per caption line on a translucent box. Text goes through files (no escaping)."""
    os.makedirs(workdir, exist_ok=True)
    filters = []
    for i, ev in enumerate(laid):
        a, b, size = ev["start"], ev["end"], ev["size"]
        _x0, y0, _w, _h, line_h = pill_geometry(ev["lines"], size, ev.get("width", 0), bottom=int(VIDEO_H * BOTTOM_SAFE))
        alpha = "if(lt(t,%.3f),(t-%.3f)/%.3f,if(gt(t,%.3f),(%.3f-t)/%.3f,1))" % (a + FADE, a, FADE, b - FADE, b, FADE)
        for k, line in enumerate(ev["lines"]):
            path = os.path.join(workdir, "cap_%02d_%d.txt" % (i, k))
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(line)
            y = "%d+%d*pow(1-min(1,max(0,(t-%.3f)/0.35)),2)" % (y0 + PAD_Y + k * line_h + (line_h - size) // 2, SLIDE, a)
            filters.append(
                "drawtext=fontfile='%s':textfile='%s':fontsize=%d:fontcolor=white:box=1:boxcolor=0x2A1A10@0.8:boxborderw=%d:"
                "shadowx=0:shadowy=2:shadowcolor=black@0.6:x=(w-text_w)/2:y='%s':alpha='%s':enable='between(t,%.3f,%.3f)'"
                % (_ffq(font_path), _ffq(path), size, PAD_Y // 2 + 2, y, alpha, a, b))
    return filters


# ----------------------------------------------------------------------------- ASS (default: rounded pills, shaped text)
def ass_escape(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def ass_time(seconds):
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return "%d:%02d:%02d.%02d" % (h, m, s, cs)


def rounded_rect(w, h, r):
    """ASS drawing (\\p1) of a rounded rectangle with its top-left corner at 0,0."""
    r = max(1, min(int(r), w // 2, h // 2))
    c = int(round(r * 0.5523))
    path = ["m", r, 0, "l", w - r, 0, "b", w - r + c, 0, w, r - c, w, r,
            "l", w, h - r, "b", w, h - r + c, w - r + c, h, w - r, h,
            "l", r, h, "b", r - c, h, 0, h - r + c, 0, h - r,
            "l", 0, r, "b", 0, r - c, r - c, 0, r, 0]
    return " ".join(str(item) for item in path)


def ass_line(text, lang, latin_family, size):
    """Escaped text; in Hindi/Bangla captions the Latin runs (product names) switch to the Latin font, at its own
    size (libass sizes by line height, which differs between the fonts), and back."""
    if lang == "en":
        return ass_escape(text)
    native = "\\fn%s\\fs%d" % (FONTS[lang][2], int(round(size * ASS_SIZE_FACTOR[lang])))
    latin = "\\fn%s\\fs%d" % (latin_family, int(round(size * ASS_SIZE_FACTOR["en"])))
    out = []
    for part, is_nat in split_runs(text):
        out.append(ass_escape(part) if is_nat else "{%s}%s{%s}" % (latin, ass_escape(part), native))
    return "".join(out)


def _row(layer, start, end, tags, body):
    return "Dialogue: %d,%s,%s,Cap,,0,0,0,,{%s}%s" % (layer, ass_time(start), ass_time(end), tags, body)


def pill_rows(lines, size, width, start, end, lang, latin_family, fill=PILL_FILL, alpha=PILL_ALPHA, text_color="&HFFFFFF&",
              shadow=True, text_shadow=True, fade=(FADE, FADE), delay=0.0, layer=0, **where):
    """Dialogue rows for one animated pill: the rounded box (layer) and one row per text line (layer + 1)."""
    x0, y0, w, h, line_h = pill_geometry(lines, size, width, **where)
    a = start + delay
    fin, fout = int(fade[0] * 1000), int(fade[1] * 1000)
    rows = []
    if fill:
        tags = ("\\an7\\move(%d,%d,%d,%d,0,350)\\fad(%d,%d)\\1c%s\\1a%s\\bord0%s\\p1"
                % (x0, y0 + SLIDE, x0, y0, fin, fout, fill, alpha, "\\shad3\\4c&H000000&\\4a&H70&" if shadow else "\\shad0"))
        rows.append(_row(layer, a, end, tags, rounded_rect(w, h, RADIUS) + "{\\p0}"))
    cx = x0 + w // 2
    fs = int(round(size * ASS_SIZE_FACTOR[lang]))
    for k, line in enumerate(lines):
        cy = y0 + PAD_Y + k * line_h + line_h // 2
        tags = ("\\an5\\move(%d,%d,%d,%d,0,350)\\fad(%d,%d)\\fs%d\\1c%s\\bord0%s\\fscx88\\fscy88\\t(0,350,\\fscx100\\fscy100)"
                % (cx, cy + SLIDE, cx, cy, fin, fout, fs, text_color, "\\shad2\\4c&H000000&\\4a&H60&" if text_shadow else "\\shad0"))
        rows.append(_row(layer + 1, a, end, tags, ass_line(line, lang, latin_family, size)))
    return rows, (x0, y0, w, h)


def make_card(product, cta, lang, total=15.0):
    """The closing call-to-action card: product name, the CTA (default 'Order Now') and 'WhatsApp Today'."""
    return {"start": round(total - CARD_SECONDS, 3), "end": round(total, 3), "title": product,
            "cta": string.capwords(cta) if lang == "en" else cta, "whatsapp": WHATSAPP_LINE[lang]}


def card_rows(card, measure, lang, latin_family):
    """Animated ending: dimmed picture, product name pops in, then the CTA and WhatsApp pills slide up in turn."""
    s, e = card["start"], card["end"]
    rows = ["Dialogue: 0,%s,%s,Cap,,0,0,0,,{\\an7\\pos(0,0)\\fad(400,0)\\1c&H000000&\\1a&H99&\\bord0\\shad0\\p1}m 0 0 l %d 0 %d %d 0 %d{\\p0}"
            % (ass_time(s), ass_time(e), VIDEO_W, VIDEO_W, VIDEO_H, VIDEO_H)]

    def block(text, px, max_w):
        scale = px / float(FONT_SIZE)
        lines = wrap_lines(text, lambda t: measure(t) * scale, max_w) or [text]
        return lines, max(measure(l) for l in lines) * scale

    title_px = int(round(92 * K))
    lines, width = block(card["title"], title_px, int(VIDEO_W * 0.82))
    if len(lines) > 2:
        title_px = int(title_px * 0.8)
        lines, width = block(card["title"], title_px, int(VIDEO_W * 0.82))
    title_h = int(title_px * LINE_H) * len(lines)
    title_top = int(VIDEO_H * 0.36) - title_h // 2
    got, _ = pill_rows(lines, title_px, width, s, e, lang, latin_family, fill=None, fade=(0.3, 0), delay=0.15, top=title_top - PAD_Y, layer=1)
    for row in got:                      # bigger pop for the product name
        rows.append(row.replace("\\fscx88\\fscy88\\t(0,350,\\fscx100\\fscy100)", "\\fscx60\\fscy60\\t(0,260,\\fscx112\\fscy112)\\t(260,420,\\fscx100\\fscy100)"))
    cta_px = int(round(60 * K))
    lines, width = block(card["cta"], cta_px, int(VIDEO_W * 0.74))
    got, _ = pill_rows(lines, cta_px, width, s, e, lang, latin_family, fill=ORDER_FILL, alpha="&H00&", text_color=ORDER_TEXT, text_shadow=False,
                       fade=(0.25, 0), delay=0.6, center_y=int(VIDEO_H * 0.50), layer=1)
    rows += got
    wa_px = int(round(48 * K))
    lines, width = block(card["whatsapp"], wa_px, int(VIDEO_W * 0.74))
    got, _ = pill_rows(lines, wa_px, width, s, e, lang, latin_family, fill=WHATSAPP_FILL, alpha="&H00&",
                       fade=(0.25, 0), delay=1.0, center_y=int(VIDEO_H * 0.50) + int(VIDEO_H * 0.095), layer=1)
    rows += got
    return rows


def to_ass(laid, family, lang="en", card=None, measure=None, latin_family="Noto Sans"):
    """ASS subtitles: rounded caption pills with fade + slide + pop, and (optionally) the closing card."""
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Cap,%s,%d,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,0,2,5,0,0,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        % (VIDEO_W, VIDEO_H, family, int(round(FONT_SIZE * ASS_SIZE_FACTOR[lang]))))
    rows = []
    for ev in laid:
        got, _ = pill_rows(ev["lines"], ev["size"], ev.get("width", 0), ev["start"], ev["end"], lang, latin_family,
                           bottom=int(VIDEO_H * BOTTOM_SAFE))
        rows += got
    if card:
        rows += card_rows(card, measure or (lambda t: len(t) * FONT_SIZE * 0.58), lang, latin_family)
    return header + "\n".join(rows) + "\n"


def drawtext_card_filters(card, fonts, workdir, lang):
    """Fallback ending without libass: three lines on boxes, fading in one after the other."""
    os.makedirs(workdir, exist_ok=True)
    s, e = card["start"], card["end"]
    items = [(card["title"], int(round(92 * K)), 0.36, "0x000000@0.55", 0.15),
             (card["cta"], int(round(60 * K)), 0.50, "0xFFB000@1.0", 0.6),
             (card["whatsapp"], int(round(48 * K)), 0.595, "0x128C7E@1.0", 1.0)]
    filters = []
    for i, (text, size, y_frac, box, delay) in enumerate(items):
        path = os.path.join(workdir, "card_%d.txt" % i)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        font = fonts["native"] if any(is_native(c) for c in text) else fonts["latin"]
        a = s + delay
        color = "0x141414" if i == 1 else "white"
        filters.append(
            "drawtext=fontfile='%s':textfile='%s':fontsize=%d:fontcolor=%s:box=1:boxcolor=%s:boxborderw=%d:x=(w-text_w)/2:"
            "y=h*%.3f-text_h/2+%d*pow(1-min(1,max(0,(t-%.3f)/0.4)),2):alpha='min(1,(t-%.3f)/0.3)':enable='between(t,%.3f,%.3f)'"
            % (_ffq(font), _ffq(path), size, color, box, PAD_Y // 2 + 2, y_frac, SLIDE, a, a, a, e))
    return filters


def parse_ffmpeg_caps(buildconf_text, filters_text):
    """What this FFmpeg build can do for captions, from ``-buildconf`` and ``-filters`` output."""
    return {
        "drawtext": bool(re.search(r"\bdrawtext\b", filters_text)),
        "ass": bool(re.search(r"\bass\b", filters_text)) and "--enable-libass" in buildconf_text,
        "harfbuzz": "--enable-libharfbuzz" in buildconf_text,
        "fribidi": "--enable-libfribidi" in buildconf_text,
    }


def choose_backend(lang, caps):
    """'ass' whenever libass is present (rounded pills, correct Hindi/Bangla shaping); else 'drawtext'; else 'none'."""
    if caps.get("ass"):
        return "ass"
    return "drawtext" if caps.get("drawtext") else "none"
