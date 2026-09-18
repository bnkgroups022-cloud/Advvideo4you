"""Launch configuration: what the website hands to the notebook.

The website cannot pass parameters through a Colab URL, so it produces one JSON file
(``advvideo-launch.json``) containing the settings and the product photo. The notebook
accepts that file in its single upload prompt. Pure Python, no third-party imports.
"""
import base64
import binascii
import json
import re
import unicodedata

LAUNCH_VERSION = 1
LANGUAGES = {"en": "English", "hi": "Hindi", "bn": "Bangla"}
DEFAULT_CTA = {
    "en": "Order now",
    "hi": "अभी ऑर्डर करें",
    "bn": "এখনই অর্ডার করুন",
}
MAX_NAME = 60
MAX_CTA = 60
MAX_DETAILS = 200
MAX_DETAIL_LINES = 3
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class ConfigError(ValueError):
    """The launch file or a field in it is not usable."""


def clean_text(value, limit, field, required=False):
    """One-line text: control characters dropped, whitespace collapsed, length checked."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ConfigError("%s must be text" % field)
    value = "".join(" " if ch in "\r\n\t" else ch for ch in value if ch in "\r\n\t" or unicodedata.category(ch)[0] != "C")
    value = re.sub(r"\s+", " ", value).strip()
    if required and not value:
        raise ConfigError("%s is required" % field)
    if len(value) > limit:
        raise ConfigError("%s is longer than %d characters" % (field, limit))
    return value


def clean_details(value):
    """Optional 'what should the ad mention' text: up to three short lines."""
    if value is None or value == "":
        return []
    if not isinstance(value, str):
        raise ConfigError("details must be text")
    if len(value) > MAX_DETAILS * 2:
        raise ConfigError("details are longer than %d characters" % MAX_DETAILS)
    lines = [clean_text(part, 80, "details line") for part in re.split(r"[\r\n;]+", value)]
    lines = [line for line in lines if line]
    if len(lines) > MAX_DETAIL_LINES:
        raise ConfigError("details can have at most %d lines" % MAX_DETAIL_LINES)
    return lines


def sniff_image(data):
    """File extension from the leading bytes, or None if it is not JPEG/PNG/WebP."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def validate_fields(product_name, language, cta, spoken_name="", details=""):
    """Return a cleaned settings dict or raise ConfigError."""
    language = (language or "").strip().lower()
    if language not in LANGUAGES:
        raise ConfigError("language must be one of: " + ", ".join(sorted(LANGUAGES)))
    cta = clean_text(cta, MAX_CTA, "CTA")
    return {
        "product_name": clean_text(product_name, MAX_NAME, "product name", required=True),
        "language": language,
        "cta": cta or DEFAULT_CTA[language],
        "spoken_name": clean_text(spoken_name, MAX_NAME, "spoken name"),
        "details": clean_details(details),
    }


def parse_launch(raw):
    """Parse the JSON produced by the website. Returns settings plus image_bytes/image_ext (or None)."""
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = bytes(raw).decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ConfigError("launch file is not UTF-8 text") from exc
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise ConfigError("launch file is not valid JSON") from exc
    if not isinstance(data, dict):
        raise ConfigError("launch file must contain a JSON object")
    if data.get("version") != LAUNCH_VERSION:
        raise ConfigError("unsupported launch file version: %r" % (data.get("version"),))
    cfg = validate_fields(data.get("product_name"), data.get("language"), data.get("cta"),
                          data.get("spoken_name", ""), data.get("details", ""))
    cfg["image_bytes"] = None
    cfg["image_ext"] = None
    image = data.get("image")
    if image is not None:
        if not isinstance(image, dict) or not isinstance(image.get("data"), str):
            raise ConfigError("image must be an object with base64 data")
        try:
            blob = base64.b64decode(image["data"], validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ConfigError("image data is not valid base64") from exc
        if not blob or len(blob) > MAX_IMAGE_BYTES:
            raise ConfigError("image must be between 1 byte and %d MB" % (MAX_IMAGE_BYTES // 2 ** 20))
        ext = sniff_image(blob)
        if ext is None:
            raise ConfigError("image must be a JPEG, PNG or WebP file")
        cfg["image_bytes"], cfg["image_ext"] = blob, ext
    return cfg


def build_launch(product_name, language, cta, image_bytes=None, spoken_name="", details=""):
    """Python twin of what the website's JavaScript writes (used by tests and the notebook fallback)."""
    cfg = validate_fields(product_name, language, cta, spoken_name, details)
    out = {
        "version": LAUNCH_VERSION,
        "product_name": cfg["product_name"],
        "language": cfg["language"],
        "cta": cfg["cta"],
        "spoken_name": cfg["spoken_name"],
        "details": "\n".join(cfg["details"]),
    }
    if image_bytes is not None:
        ext = sniff_image(image_bytes)
        if ext is None:
            raise ConfigError("image must be a JPEG, PNG or WebP file")
        out["image"] = {"mime": {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[ext],
                        "data": base64.b64encode(image_bytes).decode("ascii")}
    return json.dumps(out, ensure_ascii=False)


def slugify(name):
    """ASCII file-name stem for the output; never empty."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:40] or "product"


def classify_uploads(files):
    """Sort what the user uploaded in Colab: the launch file (JSON) and/or a product photo. ``files``: {name: bytes}."""
    launch, image, ignored = None, None, []
    for name, blob in files.items():
        if launch is None and (name.lower().endswith(".json") or blob.lstrip()[:1] == b"{"):
            launch = blob
        elif image is None and sniff_image(blob) is not None:
            image = (name, blob)
        else:
            ignored.append(name)
    return {"launch": launch, "image": image, "ignored": ignored}


def prompt_settings(ask=input, say=print):
    """Fallback when no launch file was uploaded: ask the three questions in the notebook (Enter accepts the default)."""
    name = ""
    for _ in range(3):
        name = (ask("Product name: ") or "").strip()
        if name:
            break
        say("A product name is needed.")
    language = ""
    for _ in range(3):
        language = ((ask("Language - en, hi or bn [en]: ") or "en").strip().lower())
        if language in LANGUAGES:
            break
        say("Please type en, hi or bn.")
    cta = (ask("Call to action [%s]: " % DEFAULT_CTA.get(language, "Order now")) or "").strip()
    return validate_fields(name, language, cta)