"""Wan2.1 VACE-1.3B first-frame video on a free T4, driven through the official generate.py.

Stages (each is a separate process so GPU memory is released between them):
  check     import the official code with the T4 shims installed
  encode    encode the (fixed) motion prompt with the official T5 code; result is cached, so later runs skip it
  generate  run the official generate.py: 33 frames, 18 steps, fp16, photo as frame 0
Patches applied in memory (the official code is not modified): SDPA instead of flash_attn, fp16 instead of bf16,
NaN guard, cached T5 embeddings instead of an 11 GB CPU load, in-memory stand-in for decord.
"""
import argparse
import gc
import os
import runpy
import sys
import time
import traceback
import types

import numpy as np
import torch

EXIT_OOM, EXIT_NAN, EXIT_ENCODER = 3, 4, 7
FPS = 16
SIZE_W, SIZE_H = 480, 832


class NanOutput(RuntimeError):
    pass


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + str(msg), flush=True)


def is_oom(exc):
    return isinstance(exc, torch.cuda.OutOfMemoryError) or "out of memory" in str(exc).lower()


def first_frame(path, width, height):
    """Product photo -> exactly width x height. Keeps the whole product (blurred backdrop) unless the ratio is already ~9:16."""
    from PIL import Image, ImageFilter, ImageOps
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    iw, ih = img.size
    target = width / height
    if abs(iw / ih - target) / target < 0.08:
        return ImageOps.fit(img, (width, height), method=Image.LANCZOS)
    canvas = ImageOps.fit(img, (width, height), method=Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
    scale = min(width / iw, height / ih)
    fg = img.resize((max(1, round(iw * scale)), max(1, round(ih * scale))), Image.LANCZOS)
    canvas.paste(fg, ((width - fg.width) // 2, (height - fg.height) // 2))
    return canvas


def install_import_shims(sources):
    """Stand-ins so the official code imports on Python 3.13 / Colab. `sources` maps mem:// keys to uint8 (F,H,W,3) arrays."""
    class MemReader:
        def __init__(self, key):
            self.frames = sources[key]

        def __len__(self):
            return len(self.frames)

        def get_avg_fps(self):
            return float(FPS)

        def get_frame_timestamp(self, i):
            return np.array([i / FPS, (i + 1) / FPS], dtype=np.float32)

        def next(self):
            return torch.from_numpy(self.frames[0])

        def get_batch(self, ids):
            return torch.from_numpy(self.frames[np.asarray(ids)])

    decord = types.ModuleType("decord")
    decord.VideoReader = MemReader
    decord.bridge = types.SimpleNamespace(set_bridge=lambda name: None)
    sys.modules["decord"] = decord
    try:
        __import__("dashscope")
    except Exception:
        sys.modules["dashscope"] = types.ModuleType("dashscope")


def make_attention(work_dtype):
    import torch.nn.functional as F

    def attention(q, k, v, q_lens=None, k_lens=None, dropout_p=0.0, softmax_scale=None, q_scale=None,
                  causal=False, window_size=(-1, -1), deterministic=False, dtype=None, version=None):
        out_dtype = q.dtype
        if q_scale is not None:
            q = q * q_scale
        q = q.transpose(1, 2).to(work_dtype)
        k = k.transpose(1, 2).to(work_dtype)
        v = v.transpose(1, 2).to(work_dtype)
        mask = None
        if k_lens is not None:
            length = k.size(2)
            lens = k_lens.to(k.device)
            if bool((lens < length).any()):
                mask = (torch.arange(length, device=k.device)[None, :] < lens[:, None])[:, None, None, :]
        if work_dtype == torch.float16:
            out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, is_causal=causal, scale=softmax_scale)
        else:
            heads = [
                F.scaled_dot_product_attention(q[:, h:h + 1], k[:, h:h + 1], v[:, h:h + 1],
                                               attn_mask=mask, is_causal=causal, scale=softmax_scale)
                for h in range(q.size(1))
            ]
            out = torch.cat(heads, dim=1)
        return out.transpose(1, 2).contiguous().to(out_dtype)

    return attention


def apply_t4_patches(work_dtype, embeds_path):
    import wan
    import wan.modules
    import wan.modules.attention as attention_module
    import wan.modules.model as model_module
    import wan.modules.vace_model as vace_module
    from wan.configs import WAN_CONFIGS
    from wan.modules.t5 import T5EncoderModel

    # 1. flash_attn cannot run on a T4: use PyTorch SDPA (memory-efficient kernel in fp16).
    attention = make_attention(work_dtype)
    attention_module.flash_attention = attention
    attention_module.attention = attention
    model_module.flash_attention = attention
    wan.modules.flash_attention = attention

    # 2. T4 has no fast bf16: run the DiT in fp16 (weights cast once, so the GPU holds ~3.6 GB, not 7 GB).
    WAN_CONFIGS["vace-1.3B"].param_dtype = work_dtype
    original_from_pretrained = vace_module.VaceWanModel.from_pretrained.__func__

    def from_pretrained(cls, *args, **kwargs):
        kwargs.setdefault("torch_dtype", work_dtype)
        return original_from_pretrained(cls, *args, **kwargs).to(work_dtype)

    vace_module.VaceWanModel.from_pretrained = classmethod(from_pretrained)

    # 3. Fail fast on NaN/inf instead of finishing a black video.
    original_forward = vace_module.VaceWanModel.forward
    state = {"calls": 0}

    def checked_forward(self, *args, **kwargs):
        out = original_forward(self, *args, **kwargs)
        if not bool(torch.isfinite(out[0]).all()):
            raise NanOutput("DiT output became NaN/inf at call %d" % (state["calls"] + 1))
        state["calls"] += 1
        if state["calls"] == 1:
            log("first DiT pass ok, peak VRAM %.1f GiB" % (torch.cuda.max_memory_allocated() / 2 ** 30))
        return out

    vace_module.VaceWanModel.forward = checked_forward

    # 4. The official T5EncoderModel builds 11 GB on the CPU and loads a second 11 GB copy (~23 GB RAM),
    #    which free Colab cannot hold. Prompts were already encoded by the official T5 code in a separate
    #    process (stage "encode"); serve those embeddings here.
    class NoWeights:
        def to(self, *args, **kwargs):
            return self

        def cpu(self):
            return self

    def cached_init(self, text_len, dtype=None, device=None, checkpoint_path=None, tokenizer_path=None, shard_fn=None):
        self.text_len = text_len
        self.dtype = dtype
        self.device = device
        self.cache = torch.load(embeds_path, map_location="cpu")
        self.model = NoWeights()

    def cached_call(self, texts, device):
        out = []
        for text in texts:
            if text not in self.cache:
                raise KeyError("prompt was not pre-encoded: %r" % text[:60])
            out.append(self.cache[text].to(device=device, dtype=torch.float32))
        return out

    T5EncoderModel.__init__ = cached_init
    T5EncoderModel.__call__ = cached_call


def stage_check(a):
    sys.path.insert(0, a.repo)
    os.chdir(a.repo)
    install_import_shims({})
    import importlib
    for name in ("wan", "wan.configs", "wan.utils.prompt_extend", "wan.utils.utils"):   # what generate.py imports
        importlib.import_module(name)
    assert "480*832" in importlib.import_module("wan.configs").SUPPORTED_SIZES["vace-1.3B"]
    log("official Wan2.1 modules import fine (vace-1.3B supports 480*832)")
    return 0


def stage_encode(a):
    sys.path.insert(0, a.repo)
    os.chdir(a.repo)
    install_import_shims({})
    from wan.configs import WAN_CONFIGS
    from wan.modules.t5 import T5EncoderModel, umt5_xxl
    from wan.modules.tokenizers import HuggingfaceTokenizer

    cfg = WAN_CONFIGS["vace-1.3B"]
    texts = [a.prompt, cfg.sample_neg_prompt]
    if os.path.exists(a.embeds):
        try:
            cached = torch.load(a.embeds, map_location="cpu")
            if all(text in cached for text in texts):
                log("T5: prompt embeddings already cached, skipping the 11 GB encoder")
                return 0
        except Exception as exc:
            log("cached embeddings unreadable (%s); re-encoding" % type(exc).__name__)
    ckpt = os.path.join(a.ckpt, cfg.t5_checkpoint)
    tokenizer_path = os.path.join(a.ckpt, cfg.t5_tokenizer)
    log("T5: building the official umt5-xxl encoder without allocating RAM, then memory-mapping the weights")
    model = umt5_xxl(encoder_only=True, return_tokenizer=False, dtype=cfg.t5_dtype, device="meta").eval().requires_grad_(False)
    try:
        state_dict = torch.load(ckpt, map_location="cpu", mmap=True, weights_only=True)
    except Exception as exc:
        log("mmap load unavailable (%s); loading normally" % type(exc).__name__)
        state_dict = torch.load(ckpt, map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict, assign=True)
    del state_dict
    model.to("cuda")
    log("T5: %.1f GiB on the GPU, encoding the prompts" % (torch.cuda.memory_allocated() / 2 ** 30))

    encoder = T5EncoderModel.__new__(T5EncoderModel)   # official __call__, official weights, no official __init__
    encoder.text_len = cfg.text_len
    encoder.dtype = cfg.t5_dtype
    encoder.device = torch.device("cuda")
    encoder.checkpoint_path = ckpt
    encoder.tokenizer_path = tokenizer_path
    encoder.model = model
    encoder.tokenizer = HuggingfaceTokenizer(name=tokenizer_path, seq_len=cfg.text_len, clean="whitespace")
    with torch.no_grad():
        contexts = encoder(texts, torch.device("cuda"))
    cache = {}
    for text, ctx in zip(texts, contexts):
        if not bool(torch.isfinite(ctx.float()).all()):
            raise RuntimeError("T5 produced non-finite embeddings")
        cache[text] = ctx.detach().cpu()
    torch.save(cache, a.embeds)
    del encoder, model, contexts
    gc.collect()
    torch.cuda.empty_cache()
    log("T5: %d prompt embeddings saved, encoder released" % len(cache))
    return 0


def stage_generate(a):
    work_dtype = torch.float16 if a.dtype == "float16" else torch.bfloat16
    sys.path.insert(0, a.repo)
    os.chdir(a.repo)
    frames = a.frames
    frame0 = np.asarray(first_frame(a.image, SIZE_W, SIZE_H), dtype=np.uint8)
    video = np.full((frames, SIZE_H, SIZE_W, 3), 127, dtype=np.uint8)
    video[0] = frame0
    mask = np.full((frames, SIZE_H, SIZE_W, 3), 255, dtype=np.uint8)
    mask[0] = 0                       # black = keep (the photo), white = generate
    install_import_shims({"mem://video": video, "mem://mask": mask})
    apply_t4_patches(work_dtype, a.embeds)
    log("official generate.py: task vace-1.3B, %s, %d frames, %d steps, %s" % ("480*832", frames, a.steps, a.dtype))
    sys.argv = [
        "generate.py", "--task", "vace-1.3B", "--size", "480*832", "--ckpt_dir", a.ckpt,
        "--src_video", "mem://video", "--src_mask", "mem://mask",
        "--prompt", a.prompt, "--frame_num", str(frames), "--sample_steps", str(a.steps),
        "--sample_guide_scale", str(a.guidance), "--base_seed", str(a.seed),
        "--offload_model", "True", "--save_file", a.out,
    ]
    runpy.run_path("generate.py", run_name="__main__")
    if not os.path.exists(a.out) or os.path.getsize(a.out) < 10000:
        raise RuntimeError("generate.py finished but no MP4 was written")
    log("saved %s (%.1f MB)" % (a.out, os.path.getsize(a.out) / 1e6))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["check", "encode", "generate"], required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--ckpt", default="")
    p.add_argument("--image", default="")
    p.add_argument("--out", default="")
    p.add_argument("--embeds", default="")
    p.add_argument("--prompt", default="")
    p.add_argument("--frames", type=int, default=33)
    p.add_argument("--steps", type=int, default=18)
    p.add_argument("--guidance", type=float, default=5.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dtype", choices=["float16", "bfloat16"], default="float16")
    a = p.parse_args()
    stages = {"check": stage_check, "encode": stage_encode, "generate": stage_generate}
    try:
        return stages[a.stage](a)
    except NanOutput as exc:
        log("NAN: %s" % exc)
        return EXIT_NAN
    except Exception as exc:
        if is_oom(exc):
            log("OOM: %s" % str(exc).splitlines()[0])
            return EXIT_OOM
        traceback.print_exc()
        return EXIT_ENCODER if a.stage == "encode" else 1


if __name__ == "__main__":
    sys.exit(main())
