"""AI script generator: a hook, three feature lines and a call to action.

A small local LLM (Qwen2.5-1.5B-Instruct, Apache-2.0) writes the hook and features. Everything it returns is
validated (structure, length, target script, no digits or risky claims); if the model is unavailable or its output
fails validation, curated templates are used, so the pipeline never stops here. The CTA is always the user's own.
Pure Python, no third-party imports.
"""
import hashlib
import json
import re
import unicodedata

WORD_LIMITS = {"hook": 10, "feature": 8, "cta": 12}
SCRIPT_BLOCKS = {"hi": (0x0900, 0x097F), "bn": (0x0980, 0x09FF)}
LANGUAGE_NAMES = {"en": "English", "hi": "Hindi (Devanagari script)", "bn": "Bangla (Bengali script)"}

BANNED = {
    "en": ("best", "guarantee", "guaranteed", "cure", "cures", "cheapest", "miracle", "clinically", "doctor", "number one",
           "lowest price", "free", "discount", "sale"),
    "hi": ("गारंटी", "सबसे", "बेस्ट", "मुफ़्त", "मुफ्त", "इलाज"),
    "bn": ("গ্যারান্টি", "সেরা", "সবচেয়ে", "বিনামূল্যে", "চিকিৎসা"),
}

HOOKS = {
    "en": ["Meet {name}.", "Say hello to {name}.", "Introducing {name}.", "{name}: something new for you.", "Have you seen {name}?"],
    "hi": ["{name} से मिलिए।", "आ गया है {name}।", "अब आपके लिए {name}।",
           "{name} — कुछ नया, कुछ खास।", "क्या आपने देखा {name}?"],
    "bn": ["{name}-এর সাথে পরিচিত হোন।", "এসে গেছে {name}।", "এখন আপনার জন্য {name}।",
           "{name} — নতুন কিছু, বিশেষ কিছু।", "আপনি কি {name} দেখেছেন?"],
}

FEATURES = {
    "en": ["Made for your everyday life", "Simple, stylish and easy to use", "Quality you can feel", "Designed with you in mind",
           "A great companion for every moment", "Brings out your style", "A smart choice", "Made with care, made for you"],
    "hi": ["रोज़मर्रा की ज़िंदगी के लिए बनाया गया", "सरल, स्टाइलिश और इस्तेमाल में आसान",
           "क्वालिटी जो आप महसूस करेंगे", "आपको ध्यान में रखकर बनाया गया",
           "हर पल के लिए एक अच्छा साथी", "आपके अंदाज़ को और निखारे", "एक समझदार चुनाव",
           "प्यार से बनाया, आपके लिए"],
    "bn": ["প্রতিদিনের জীবনের জন্য তৈরি", "সহজ, স্টাইলিশ এবং ব্যবহারে আরামদায়ক",
           "মানের অনুভূতিই আলাদা", "আপনার প্রয়োজনের কথা ভেবে তৈরি",
           "প্রতিটি মুহূর্তের জন্য একটি ভালো সঙ্গী", "আপনার স্টাইলকে আরও উজ্জ্বল করে",
           "একটি বুদ্ধিমানের পছন্দ", "যত্ন নিয়ে বানানো, আপনার জন্য"],
}


def word_count(text):
    return len(text.split())


def _seed(cfg):
    digest = hashlib.sha256((cfg["product_name"] + "|" + cfg["language"]).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _trim_words(text, limit):
    words = text.split()
    return " ".join(words[:limit])


def template_script(cfg, variant=0):
    """Deterministic curated script; the user's own detail lines replace generic features when given."""
    lang = cfg["language"]
    seed = _seed(cfg) + variant
    hook = HOOKS[lang][seed % len(HOOKS[lang])].format(name=cfg["product_name"])
    bank = FEATURES[lang]
    start = seed % len(bank)
    features = [_trim_words(line, WORD_LIMITS["feature"]) for line in cfg.get("details", [])][:3]
    for i in range(len(bank)):
        if len(features) == 3:
            break
        candidate = bank[(start + i * 3) % len(bank)]
        if candidate not in features:
            features.append(candidate)
    return {"hook": hook, "features": features[:3], "cta": cfg["cta"], "source": "templates", "notes": []}


def _is_wordchar(ch):
    return unicodedata.category(ch)[0] in ("L", "M")


def script_ratio(text, lang):
    """Share of letters/marks that belong to the expected writing system (Latin/ASCII for English)."""
    chars = [ch for ch in text if _is_wordchar(ch)]
    if not chars:
        return 0.0
    if lang == "en":
        good = sum(1 for ch in chars if ord(ch) < 128)
    else:
        lo, hi = SCRIPT_BLOCKS[lang]
        good = sum(1 for ch in chars if lo <= ord(ch) <= hi)
    return good / len(chars)


def validate_script(script, cfg):
    """List of human-readable problems; empty means the script is safe to record."""
    lang = cfg["language"]
    problems = []
    features = script.get("features")
    if not isinstance(script.get("hook"), str) or not script["hook"].strip():
        problems.append("hook is missing")
    if not isinstance(features, list) or len(features) != 3 or not all(isinstance(f, str) and f.strip() for f in features):
        problems.append("need exactly three feature lines")
    if problems:
        return problems
    lines = [("hook", script["hook"], WORD_LIMITS["hook"])] + [("feature", f, WORD_LIMITS["feature"]) for f in features]
    for kind, text, limit in lines:
        if word_count(text) > limit:
            problems.append("%s has more than %d words: %r" % (kind, limit, text))
        if re.search(r"[0-9०-९০-৯%$₹€#@]", text):
            problems.append("%s contains digits or symbols: %r" % (kind, text))
        lowered = text.lower()
        for word in BANNED[lang]:
            hit = re.search(r"\b%s\b" % re.escape(word), lowered) if lang == "en" else word in lowered
            if hit:
                problems.append("%s contains a risky claim (%s)" % (kind, word))
        scrubbed = text.replace(cfg["product_name"], " ")
        if script_ratio(scrubbed, lang) < (0.98 if lang == "en" else 0.7):
            problems.append("%s is not written in %s: %r" % (kind, LANGUAGE_NAMES[lang], text))
    if len(set(f.strip().lower() for f in features)) < 3:
        problems.append("feature lines repeat")
    return problems


def build_llm_messages(cfg):
    """Chat messages for the LLM: rules, one worked example in the target language, then the real request."""
    lang = cfg["language"]
    example_cfg = {"product_name": "Sample", "language": lang, "cta": "", "details": []}
    example = template_script(example_cfg)
    system = (
        "You write short voice-over scripts for 15-second vertical product ads. Reply with JSON only, in exactly this shape: "
        '{"hook": "...", "features": ["...", "...", "..."]}. Write in %s. '
        "The hook has at most %d words and includes the product name exactly as given. Each feature has at most %d words. "
        "Use only the details the user gives. If there are none, write general benefit lines about everyday use, style, comfort "
        "or quality. Never invent specifications, numbers, prices, awards, ingredients, health claims or comparisons. "
        "No digits, no emojis, no hashtags, no quotation marks inside the lines."
        % (LANGUAGE_NAMES[lang], WORD_LIMITS["hook"], WORD_LIMITS["feature"])
    )
    example_user = "Product name: Sample\nDetails: none\nLanguage: %s" % LANGUAGE_NAMES[lang]
    example_reply = json.dumps({"hook": example["hook"], "features": example["features"]}, ensure_ascii=False)
    details = "; ".join(cfg.get("details", [])) or "none"
    user = "Product name: %s\nDetails: %s\nLanguage: %s" % (cfg["product_name"], details, LANGUAGE_NAMES[lang])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": example_user},
        {"role": "assistant", "content": example_reply},
        {"role": "user", "content": user},
    ]


def parse_llm_json(text):
    """First JSON object found in the model's reply (tolerates code fences and chatter), or None."""
    if not isinstance(text, str):
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    features = data.get("features")
    if isinstance(features, list):
        features = [str(f).strip().strip('"').strip() for f in features]
    return {"hook": str(data.get("hook", "")).strip().strip('"').strip(), "features": features}


def generate_script(cfg, llm=None, attempts=2):
    """Script for the ad. ``llm(messages) -> str`` may be None; any failure falls back to the templates."""
    notes = []
    if llm is not None:
        messages = build_llm_messages(cfg)
        for attempt in range(1, attempts + 1):
            try:
                reply = llm(messages)
            except Exception as exc:  # the model is best-effort by design
                notes.append("LLM attempt %d failed: %s" % (attempt, exc))
                break
            parsed = parse_llm_json(reply)
            if parsed is None:
                notes.append("LLM attempt %d: no JSON in the reply" % attempt)
                continue
            parsed["cta"] = cfg["cta"]
            problems = validate_script(parsed, cfg)
            if not problems:
                parsed.update(source="llm", notes=notes)
                return parsed
            notes.append("LLM attempt %d rejected: %s" % (attempt, "; ".join(problems)))
    script = template_script(cfg)
    script["notes"] = notes
    return script


def segments(script, cfg):
    """Ordered ad segments with caption text (as typed) and speech text (spoken name substituted)."""
    spoken = cfg.get("spoken_name") or ""
    name = cfg["product_name"]
    out = []
    for kind, text in [("hook", script["hook"])] + [("feature", f) for f in script["features"]] + [("cta", script["cta"])]:
        speech = text.replace(name, spoken) if spoken else text
        out.append({"kind": kind, "caption": text, "speech": speech})
    return out
