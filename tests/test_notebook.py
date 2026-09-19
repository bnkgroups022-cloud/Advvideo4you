import ast
import json
import os

PATH = "colab/Advvideo4you_AI_Ad_Generator.ipynb"


def load():
    with open(PATH, encoding="utf-8") as fh:
        return json.load(fh)


def code_cell():
    nb = load()
    return "".join(next(c for c in nb["cells"] if c["cell_type"] == "code")["source"])


def test_notebook_structure():
    nb = load()
    assert nb["nbformat"] == 4 and [c["cell_type"] for c in nb["cells"]] == ["markdown", "code"]
    assert nb["metadata"]["colab"]["gpuType"] == "T4" and nb["metadata"]["accelerator"] == "GPU"
    for cell in nb["cells"]:
        assert isinstance(cell["source"], list) and all(isinstance(s, str) for s in cell["source"])
        assert all(s.endswith("\n") for s in cell["source"][:-1])
    assert nb["cells"][1]["outputs"] == [] and nb["cells"][1]["execution_count"] is None


def test_code_cell_compiles_and_only_calls_main_at_the_end():
    src = code_cell()
    tree = ast.parse(src)
    compile(src, "notebook-cell", "exec")
    assert isinstance(tree.body[-1], ast.Expr) and tree.body[-1].value.func.id == "main"


def test_forms_have_safe_defaults_so_run_all_needs_no_edits():
    src = code_cell()
    for line in ('MUSIC = "upbeat"  #@param ["upbeat", "calm", "none"]', 'SCRIPT_MODE = "auto"  #@param ["auto", "templates"]',
                 "FRAMES = 33  #@param", "STEPS = 18  #@param", "CACHE_TO_DRIVE = False  #@param"):
        assert line in src, line


def test_notebook_uses_the_repo_modules_and_the_one_upload_prompt():
    src = code_cell()
    assert src.count("files.upload()") == 1
    for needle in ("advvideo.pipeline", "config.classify_uploads", "config.prompt_settings", "config.build_launch",
                   "https://github.com/bnkgroups022-cloud/Advvideo4you.git", "files.download(final)"):
        assert needle in src, needle
    assert "os.kill" not in src and "getpid" not in src        # never restarts the runtime
    assert "import torch" not in src.split("CHECK_CODE = r'''")[0] and "def main" in src


def test_every_module_the_notebook_calls_exists():
    for name in ("pipeline", "config", "script", "voice", "captions", "music", "render", "llm_worker", "tts_worker", "wan_launcher"):
        assert os.path.exists("advvideo/%s.py" % name), name
    import advvideo.config as config
    assert callable(config.classify_uploads) and callable(config.prompt_settings) and callable(config.build_launch)


def test_pyflakes_clean_when_available():
    try:
        from pyflakes.checker import Checker
    except ImportError:
        return
    messages = [str(m) for m in Checker(ast.parse(code_cell()), "cell").messages]
    assert messages == [], messages


def test_intro_states_the_licence_limits_and_time_estimates():
    intro = "".join(load()["cells"][0]["source"])
    for needle in ("non-commercial", "33 frames", "loop", "15–25 minutes", "5–8 minutes", "not been measured", "CC BY-NC-SA",
                   "Start Free", "Run all", "Upload the photo", "Download the video", "WhatsApp Today", "480×832"):
        assert needle in intro, needle


def test_model_download_starts_right_after_the_upload_and_before_the_installs():
    code = code_cell()
    upload = code.index("files.upload()")
    prefetch = code.index('"--prefetch"')
    installs = code.index("plans = [")
    pipeline = code.index('"advvideo.pipeline", "--launch"')
    assert upload < prefetch < installs < pipeline
    assert "import threading" in code and "cache = CACHE_DIR" in code and code.index("cache = CACHE_DIR") < prefetch
