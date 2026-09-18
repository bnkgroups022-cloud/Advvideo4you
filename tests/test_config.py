import base64
import io
import json

from advvideo import config
from advvideo.config import ConfigError


def tiny_png():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (200, 40, 40)).save(buf, "PNG")
    return buf.getvalue()


def raises(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ConfigError:
        return True
    return False


def test_roundtrip_with_image():
    png = tiny_png()
    text = config.build_launch("Aroma Tea", "en", "Order now on our shop", png, details="Loose leaf; Small batch")
    cfg = config.parse_launch(text)
    assert cfg["product_name"] == "Aroma Tea"
    assert cfg["language"] == "en"
    assert cfg["cta"] == "Order now on our shop"
    assert cfg["details"] == ["Loose leaf", "Small batch"]
    assert cfg["image_bytes"] == png and cfg["image_ext"] == "png"


def test_unicode_names_survive():
    name = "स्वाद चाय"
    text = config.build_launch(name, "hi", "अभी खरीदें")
    cfg = config.parse_launch(text.encode("utf-8"))
    assert cfg["product_name"] == name and cfg["language"] == "hi"


def test_default_cta_per_language():
    for lang, cta in config.DEFAULT_CTA.items():
        cfg = config.parse_launch(config.build_launch("X", lang, ""))
        assert cfg["cta"] == cta
        assert config.LANGUAGES[lang]


def test_json_without_image_is_allowed():
    cfg = config.parse_launch(json.dumps({"version": 1, "product_name": "A", "language": "bn", "cta": "c"}))
    assert cfg["image_bytes"] is None and cfg["language"] == "bn"


def test_rejects_bad_input():
    good = {"version": 1, "product_name": "A", "language": "en", "cta": "c"}
    assert raises(config.parse_launch, "not json")
    assert raises(config.parse_launch, "[1, 2]")
    assert raises(config.parse_launch, json.dumps(dict(good, version=2)))
    assert raises(config.parse_launch, json.dumps(dict(good, product_name="")))
    assert raises(config.parse_launch, json.dumps(dict(good, product_name="x" * 61)))
    assert raises(config.parse_launch, json.dumps(dict(good, language="fr")))
    assert raises(config.parse_launch, json.dumps(dict(good, cta="y" * 61)))
    assert raises(config.parse_launch, json.dumps(dict(good, details="a;b;c;d")))
    assert raises(config.parse_launch, b"\xff\xfe\x00")


def test_rejects_bad_images():
    good = {"version": 1, "product_name": "A", "language": "en", "cta": "c"}
    assert raises(config.parse_launch, json.dumps(dict(good, image={"data": "!!!not-base64!!!"})))
    assert raises(config.parse_launch, json.dumps(dict(good, image={"data": base64.b64encode(b"plain text").decode()})))
    assert raises(config.parse_launch, json.dumps(dict(good, image={"data": ""})))
    big = b"\xff\xd8\xff" + b"0" * (config.MAX_IMAGE_BYTES + 1)
    assert raises(config.parse_launch, json.dumps(dict(good, image={"data": base64.b64encode(big).decode()})))
    assert raises(config.parse_launch, json.dumps(dict(good, image="just a string")))


def test_control_characters_and_whitespace_are_cleaned():
    cfg = config.parse_launch(json.dumps({"version": 1, "product_name": "  Tea" + chr(0) + "\n  Co  ", "language": "en", "cta": "Go\tnow"}))
    assert cfg["product_name"] == "Tea Co" and cfg["cta"] == "Go now"


def test_sniff_image_types():
    assert config.sniff_image(b"\xff\xd8\xff\xe0abc") == "jpg"
    assert config.sniff_image(b"\x89PNG\r\n\x1a\n....") == "png"
    assert config.sniff_image(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"
    assert config.sniff_image(b"GIF89a") is None


def test_slugify():
    assert config.slugify("Aroma Tea & Co.") == "aroma-tea-co"
    assert config.slugify("स्वाद") == "product"
    assert len(config.slugify("a" * 100)) == 40
