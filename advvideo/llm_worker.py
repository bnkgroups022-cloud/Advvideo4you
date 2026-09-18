"""Runs the script-writing LLM in its own process so its GPU memory is freed before Wan starts.

Usage: python -m advvideo.llm_worker --messages in.json --out out.json [--n 3]
Writes a JSON list of raw model replies. Exit code 0 on success; the caller falls back to templates otherwise.
"""
import argparse
import json
import sys
import time

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"   # Apache-2.0


def log(msg):
    print(time.strftime("[%H:%M:%S] ") + str(msg), flush=True)


def dtype_kw(dtype):
    import transformers
    from packaging.version import Version
    key = "dtype" if Version(transformers.__version__) >= Version("4.56.0") else "torch_dtype"
    return {key: dtype}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--messages", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--model", default=MODEL_ID)
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    with open(args.messages, "r", encoding="utf-8") as fh:
        messages = json.load(fh)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log("script LLM: loading %s on %s" % (args.model, device))
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, **dtype_kw(torch.float16 if device == "cuda" else torch.float32))
    model.to(device).eval()
    inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    prompt_len = inputs["input_ids"].shape[1]
    replies = []
    for i in range(args.n):
        torch.manual_seed(1234 + i)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=220, do_sample=True, temperature=0.7, top_p=0.9,
                                 pad_token_id=tokenizer.eos_token_id)
        replies.append(tokenizer.decode(out[0][prompt_len:], skip_special_tokens=True))
        log("script LLM: reply %d/%d generated" % (i + 1, args.n))
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(replies, fh, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
