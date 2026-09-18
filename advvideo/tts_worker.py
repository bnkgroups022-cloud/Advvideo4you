"""Synthesises voice-over lines with Piper (one process, the voice model is loaded once).

Usage: python -m advvideo.tts_worker --onnx voice.onnx --lines lines.json --outdir dir [--length-scale 1.0] [--speaker N]
lines.json is a list of {"id": "hook", "text": "..."}; writes <outdir>/<id>.wav and prints one JSON summary line.
"""
import argparse
import json
import os
import sys
import time
import wave


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx", required=True)
    parser.add_argument("--lines", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--length-scale", type=float, default=1.0)
    parser.add_argument("--speaker", type=int, default=None)
    args = parser.parse_args()

    from piper import PiperVoice, SynthesisConfig

    with open(args.lines, "r", encoding="utf-8") as fh:
        lines = json.load(fh)
    os.makedirs(args.outdir, exist_ok=True)
    print(time.strftime("[%H:%M:%S] ") + "Piper: loading " + os.path.basename(args.onnx), flush=True)
    voice = PiperVoice.load(args.onnx)
    config = SynthesisConfig(length_scale=args.length_scale, speaker_id=args.speaker)
    result = {}
    for item in lines:
        path = os.path.join(args.outdir, item["id"] + ".wav")
        with wave.open(path, "wb") as wav_file:
            voice.synthesize_wav(item["text"], wav_file, syn_config=config)
        with wave.open(path, "rb") as check:
            result[item["id"]] = {"path": path, "seconds": check.getnframes() / float(check.getframerate())}
        print(time.strftime("[%H:%M:%S] ") + "Piper: %s %.2fs" % (item["id"], result[item["id"]]["seconds"]), flush=True)
    print("RESULT " + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
