# Advvideo4you

Turn **one product photo** into a **15-second 9:16 AI ad video** — AI-written script, voice-over (Hindi, English or Bangla), animated captions and background music — on the **free Google Colab T4 GPU**.

**Website:** https://advvideo4you.vercel.app  
**Notebook:** [`colab/Advvideo4you_AI_Ad_Generator.ipynb`](colab/Advvideo4you_AI_Ad_Generator.ipynb)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bnkgroups022-cloud/Advvideo4you/blob/main/colab/Advvideo4you_AI_Ad_Generator.ipynb)

## How to use it

1. On the website press **Start Free**. Choose your photo, type the product name, pick the language and a call to action.
2. The page saves everything (settings plus your photo, resized in your browser) into one file, `advvideo-launch.json`, and opens the notebook in Colab. Nothing is uploaded to a server.
3. In Colab press `Runtime -> Run all` (T4 GPU; if it is not selected: `Runtime -> Change runtime type -> T4 GPU`).
4. When the upload button appears, choose `advvideo-launch.json`. That is the only click. (You can upload just a photo instead; the notebook then asks for the name, language and CTA.)
5. The finished MP4 downloads automatically.

Colab cannot receive parameters through a link, which is why settings travel in the launch file.

## What you get

- **1080×1920 MP4**, H.264 + AAC, exactly 15 seconds, `+faststart`.
- **Script:** hook, three feature lines and your CTA. A small LLM (Qwen2.5-1.5B-Instruct) writes it; the output is validated (length, correct script, no digits or risky claims) and replaced by curated templates if it fails. If you fill in "What should the ad mention?", only that is stated.
- **Voice-over:** Piper TTS, fitted into the 15 seconds (re-synthesised faster, up to 1.35x, if needed).
- **Captions:** an SRT file plus animated on-screen text (fade in, slide up, fade out) burned in with FFmpeg `drawtext`. Hindi and Bangla need text shaping; when the local FFmpeg's `drawtext` lacks HarfBuzz, the identical animation is rendered as ASS through libass (verified: `drawtext` without HarfBuzz visibly breaks conjuncts and vowel signs).
- **Music:** an original synthesised loop (CC0), faded in and out and ducked under the voice.
- **Video:** Wan2.1 VACE-1.3B through the official Wan-Video/Wan2.1 repository, your photo as frame 0.

## Read this before you rely on it

- **The AI motion is about 2 seconds.** 33 frames at 16 fps, 18 steps, fp16. It plays forward and backward in a loop with a slow camera drift to fill 15 seconds, so the motion repeats; the voice, captions and music carry the ad. If the AI clip cannot be made, the ad is rendered with a slow push-in on your photo and the report says so.
- **Not yet measured on a real T4.** The pipeline was checked by static analysis, 100+ automated tests of the logic, and by running the FFmpeg graphs (video, captions in three languages, audio mix) in ffmpeg 5.1. The Wan, Piper and LLM stages have not been run end to end on a Colab GPU by the author. The 6–8 minute target is for a warm cache; the first run also downloads about 22 GB (Wan 19 GB, script model 3 GB, voices).
- **Licences:** the Hindi voice is CC BY-NC-SA 4.0 (**non-commercial only**). See [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
- AI-written lines are not verified facts. Review the script (`script.json` is saved next to the video) before publishing.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The website: single static file, no build step |
| `colab/Advvideo4you_AI_Ad_Generator.ipynb` | One Run-all cell: upload, install, run the pipeline, download |
| `advvideo/config.py` | Launch-file format, validation, upload classification |
| `advvideo/script.py`, `llm_worker.py` | Script generator (LLM + validation + templates) |
| `advvideo/voice.py`, `tts_worker.py` | Piper voices, licences, 15-second timeline, voice mixing |
| `advvideo/captions.py` | SRT, wrapping, animated drawtext / ASS |
| `advvideo/music.py` | Synthesised background music |
| `advvideo/render.py` | FFmpeg commands and output checks |
| `advvideo/wan_launcher.py` | Wan2.1 VACE on a T4 (patches applied in memory) |
| `advvideo/pipeline.py` | Orchestration; the GPU stage runs alongside the audio work |
| `tests/` | Logic tests (pytest style, plain `assert`) |
| `vercel.json`, `favicon.*`, `og.png`, `robots.txt`, `sitemap.xml` | Static-site config and SEO |

## Development

```bash
pip install numpy pillow pytest
python -m pytest tests
```

The site deploys to Vercel from `main` with no build step. The notebook clones this repository at run time, so pushing to `main` updates it.

## Version

See [`VERSION`](VERSION), [`CHANGELOG.md`](CHANGELOG.md) and [`RELEASE_NOTES.md`](RELEASE_NOTES.md).

## Licence

Code: MIT (see `LICENSE`). Models, voices, fonts and music carry their own licences, listed in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
