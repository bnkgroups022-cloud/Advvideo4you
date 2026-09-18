import ast
import os
import tempfile

import numpy as np
from PIL import Image

SRC = open(os.path.join(os.path.dirname(__file__), "..", "advvideo", "wan_launcher.py"), encoding="utf-8").read() \
    if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "advvideo", "wan_launcher.py")) else open("advvideo/wan_launcher.py", encoding="utf-8").read()
TREE = ast.parse(SRC)


def function_source(name):
    node = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(SRC, node)


def load_first_frame():
    ns = {}
    exec(function_source("first_frame"), ns)
    return ns["first_frame"]


def make(path, size, color):
    Image.new("RGB", size, color).save(path)


def test_first_frame_shapes():
    ff = load_first_frame()
    with tempfile.TemporaryDirectory() as d:
        sq, tall, wide = (os.path.join(d, n) for n in ("sq.png", "tall.png", "wide.png"))
        make(sq, (1000, 1000), (200, 30, 30))
        make(tall, (540, 960), (10, 200, 10))
        make(wide, (1600, 900), (20, 20, 220))
        a = ff(sq, 480, 832)
        assert a.size == (480, 832) and a.getpixel((240, 416)) == (200, 30, 30)
        b = ff(tall, 480, 832)
        assert b.size == (480, 832) and b.getpixel((5, 5)) == (10, 200, 10)
        c = ff(wide, 480, 832)
        assert c.size == (480, 832) and c.getpixel((240, 416)) == (20, 20, 220)


def test_defaults_match_the_v2_speed_targets():
    text = SRC
    assert 'p.add_argument("--frames", type=int, default=33)' in text
    assert 'p.add_argument("--steps", type=int, default=18)' in text
    assert (33 - 1) % 4 == 0   # the model needs 4n+1 frames


def test_frame_selection_math_for_33_frames():
    # the official VaceVideoProcessor picks frames from a 16 fps in-memory clip; 33 frames must map 1:1
    frames, fps = 33, 16
    of_latent = (frames - 1) // 4 + 1
    assert of_latent == 9 and (of_latent - 1) * 4 + 1 == frames
    timestamps = np.array([[i / fps, (i + 1) / fps] for i in range(frames)], dtype=np.float32)
    duration = timestamps[-1].mean()
    linspace = np.linspace(0.0, duration, frames)
    ids = np.argmax(np.logical_and(linspace[:, None] >= timestamps[None, :, 0], linspace[:, None] <= timestamps[None, :, 1]), axis=1)
    assert ids.tolist() == list(range(frames))


def test_launcher_keeps_the_t4_patches_and_the_embedding_cache():
    for needle in ("flash_attention = attention", "param_dtype = work_dtype", "VaceWanModel.forward = checked_forward",
                   "T5EncoderModel.__init__ = cached_init", "mmap=True", 'runpy.run_path("generate.py"',
                   "prompt embeddings already cached"):
        assert needle in SRC, needle


def test_stage_and_exit_code_contract():
    assert "EXIT_OOM, EXIT_NAN, EXIT_ENCODER = 3, 4, 7" in SRC
    for stage in ("check", "encode", "generate"):
        assert '"%s"' % stage in SRC
