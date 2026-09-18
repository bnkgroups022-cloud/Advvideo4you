import json

from advvideo import config, script

NAMES = ["Aroma Tea", "Nike Air", "स्वाद चाय", "মিষ্টি ঘর", "X", "A very long product name ok"]


def cfg_for(name, lang, details=""):
    return config.validate_fields(name, lang, "", details=details)


def test_templates_are_valid_for_every_language_and_name():
    for lang in ("en", "hi", "bn"):
        for name in NAMES:
            cfg = cfg_for(name, lang)
            s = script.template_script(cfg)
            assert script.validate_script(s, cfg) == [], (lang, name, script.validate_script(s, cfg), s)
            assert s["cta"] == config.DEFAULT_CTA[lang]
            assert name in s["hook"]
            assert len(s["features"]) == 3 and len(set(s["features"])) == 3


def test_every_template_line_fits_the_word_limits():
    for lang in ("en", "hi", "bn"):
        for line in script.FEATURES[lang]:
            assert script.word_count(line) <= script.WORD_LIMITS["feature"], line
        for hook in script.HOOKS[lang]:
            assert script.word_count(hook.format(name="Two Words")) <= script.WORD_LIMITS["hook"], hook
        assert not any(ch.isdigit() for line in script.FEATURES[lang] + script.HOOKS[lang] for ch in line)


def test_templates_are_deterministic_and_vary_by_product():
    a = script.template_script(cfg_for("Aroma Tea", "en"))
    b = script.template_script(cfg_for("Aroma Tea", "en"))
    assert a == b
    hooks = {script.template_script(cfg_for("Product %s" % i, "en"))["hook"].split("Product")[0] for i in range(40)}
    assert len(hooks) >= 3


def test_user_details_replace_generic_features():
    cfg = cfg_for("Aroma Tea", "en", details="Loose leaf tea; Packed in small batches")
    s = script.template_script(cfg)
    assert s["features"][0] == "Loose leaf tea" and s["features"][1] == "Packed in small batches"
    assert len(s["features"]) == 3 and script.validate_script(s, cfg) == []


def test_validate_rejects_bad_scripts():
    cfg = cfg_for("Aroma Tea", "en")
    ok = {"hook": "Meet Aroma Tea.", "features": ["Made for you", "Easy to use", "Looks great"], "cta": "Order now"}
    assert script.validate_script(ok, cfg) == []
    bad = dict(ok, features=["Made for you", "Easy to use"])
    assert script.validate_script(bad, cfg)
    assert script.validate_script(dict(ok, hook="Meet the best tea in town."), cfg)
    assert script.validate_script(dict(ok, features=["Made for you", "Easy to use", "Only 99 rupees"]), cfg)
    assert script.validate_script(dict(ok, features=["Made for you", "Easy to use", "Saves 50% today"]), cfg)
    assert script.validate_script(dict(ok, features=["Made for you", "Made for you", "Looks great"]), cfg)
    assert script.validate_script(dict(ok, hook="one two three four five six seven eight nine ten eleven"), cfg)
    assert script.validate_script(dict(ok, features=["Made for you", "Easy to use", "A guarantee of joy"]), cfg)
    # whole-word matching: 'carefree' and 'wholesale' must not trip the banned list
    assert script.validate_script(dict(ok, features=["Made for you", "Easy to use", "Carefree wholesale style"]), cfg) == []


def test_validate_checks_the_writing_system():
    hi = cfg_for("Aroma Tea", "hi")
    english_in_hindi = {"hook": "Meet Aroma Tea.", "features": ["Made for you", "Easy to use", "Looks great"], "cta": "x"}
    assert script.validate_script(english_in_hindi, hi)
    hindi_in_english = {"hook": "अब आपके लिए Aroma Tea।", "features": ["सरल और आसान", "अच्छा साथी", "एक समझदार चुनाव"], "cta": "x"}
    assert script.validate_script(hindi_in_english, cfg_for("Aroma Tea", "en"))
    bn_text_in_hindi = {"hook": "এসে গেছে Aroma Tea।", "features": ["সহজ এবং সুন্দর", "একটি ভালো সঙ্গী", "একটি বুদ্ধিমানের পছন্দ"], "cta": "x"}
    assert script.validate_script(bn_text_in_hindi, hi)


def test_script_ratio():
    assert script.script_ratio("hello", "en") == 1.0
    assert script.script_ratio("नमस्ते", "hi") == 1.0
    assert script.script_ratio("নমস্কার", "bn") == 1.0
    assert script.script_ratio("नमस्ते", "bn") == 0.0
    assert script.script_ratio("123 !!", "en") == 0.0


def test_parse_llm_json_variants():
    good = '{"hook": "Meet X.", "features": ["a", "b", "c"]}'
    assert script.parse_llm_json(good)["features"] == ["a", "b", "c"]
    assert script.parse_llm_json("Sure! Here you go:\n```json\n" + good + "\n```\nHope that helps")["hook"] == "Meet X."
    assert script.parse_llm_json("no json here") is None
    assert script.parse_llm_json("{broken json") is None
    assert script.parse_llm_json(None) is None
    assert script.parse_llm_json('["not", "an", "object"]') is None


def test_llm_success_uses_the_users_cta():
    cfg = config.validate_fields("Aroma Tea", "en", "Shop today")
    reply = json.dumps({"hook": "Meet Aroma Tea.", "features": ["Warm and calming", "Made for slow mornings", "A cup you will love"]})
    s = script.generate_script(cfg, llm=lambda messages: reply)
    assert s["source"] == "llm" and s["cta"] == "Shop today" and s["features"][0] == "Warm and calming"


def test_llm_garbage_falls_back_to_templates():
    cfg = config.validate_fields("Aroma Tea", "en", "Shop today")
    calls = []

    def bad(messages):
        calls.append(1)
        return "I cannot help with that."

    s = script.generate_script(cfg, llm=bad, attempts=2)
    assert s["source"] == "templates" and len(calls) == 2 and s["notes"]
    assert script.validate_script(s, cfg) == []


def test_llm_rejected_output_and_exceptions_fall_back():
    cfg = config.validate_fields("Aroma Tea", "en", "Shop today")
    risky = json.dumps({"hook": "The best tea ever.", "features": ["a b", "c d", "e f"]})
    s = script.generate_script(cfg, llm=lambda m: risky)
    assert s["source"] == "templates" and any("rejected" in n for n in s["notes"])

    def boom(messages):
        raise RuntimeError("out of memory")

    s = script.generate_script(cfg, llm=boom)
    assert s["source"] == "templates" and any("out of memory" in n for n in s["notes"])


def test_llm_retry_recovers():
    cfg = config.validate_fields("Aroma Tea", "en", "Shop today")
    replies = iter(["nonsense", json.dumps({"hook": "Say hello to Aroma Tea.", "features": ["Warm and calming", "Made for slow mornings", "A cup you will love"]})])
    s = script.generate_script(cfg, llm=lambda m: next(replies))
    assert s["source"] == "llm" and len(s["notes"]) == 1


def test_llm_messages_include_rules_and_a_target_language_example():
    for lang in ("en", "hi", "bn"):
        cfg = cfg_for("Aroma Tea", lang, details="Loose leaf")
        msgs = script.build_llm_messages(cfg)
        assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
        assert "Never invent" in msgs[0]["content"]
        example = json.loads(msgs[2]["content"])
        assert script.script_ratio(example["hook"].replace("Sample", ""), lang) >= 0.7
        assert "Aroma Tea" in msgs[3]["content"] and "Loose leaf" in msgs[3]["content"]


def test_segments_use_spoken_name_only_for_speech():
    cfg = config.validate_fields("Nike Air", "hi", "", spoken_name="नाइकी एयर")
    s = script.template_script(cfg)
    segs = script.segments(s, cfg)
    assert [x["kind"] for x in segs] == ["hook", "feature", "feature", "feature", "cta"]
    assert "Nike Air" in segs[0]["caption"] and "Nike Air" not in segs[0]["speech"] and "नाइकी एयर" in segs[0]["speech"]
    plain = script.segments(script.template_script(cfg_for("Aroma Tea", "en")), cfg_for("Aroma Tea", "en"))
    assert all(x["caption"] == x["speech"] for x in plain)
