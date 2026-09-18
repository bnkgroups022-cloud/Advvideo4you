# Advvideo4you 2.0.0

**Released:** 2026-09-19  
**Site:** https://advvideo4you.vercel.app  
**Notebook:** https://colab.research.google.com/github/bnkgroups022-cloud/Advvideo4you/blob/main/colab/Advvideo4you_AI_Ad_Generator.ipynb

Advvideo4you is now a working AI ad generator: one product photo, a name, a language (Hindi, English or Bangla) and a call to action become a 15-second 1080x1920 MP4 with an AI-written script, voice-over, animated captions and background music, made on a free Google Colab T4.

## Highlights

- **Launch flow.** Start Free opens a form (photo, name, language, CTA, optional spoken name and key details), saves one `advvideo-launch.json` and opens the notebook. Colab cannot take URL parameters, so that file is what the notebook's single upload prompt reads.
- **Script.** Qwen2.5-1.5B-Instruct writes the hook and three features; output is validated and replaced by curated templates on any failure. Your CTA is used verbatim.
- **Voice.** Piper TTS in three languages, fitted into 15 seconds.
- **Captions.** SRT plus animated captions via FFmpeg `drawtext`; Hindi/Bangla fall back to the same animation through libass when `drawtext` cannot shape those scripts.
- **Music.** Original synthesised loop (CC0), ducked under the voice.
- **Video.** Wan2.1 VACE-1.3B via the official repository, 33 frames, 18 steps, fp16, cached model and prompt embeddings; automatic fallbacks for out-of-memory and NaN, and a push-in on the photo if no AI clip can be made.

## Known limitations (please read)

- **The AI motion is about 2 seconds**, played forward and backward in a loop with a slow camera drift to fill 15 seconds. Voice, captions and music carry the ad.
- **Not run end to end on a real Colab T4 by the author.** Verified: static analysis, 100+ logic tests, the FFmpeg graphs rendered in ffmpeg 5.1 (captions in English, Hindi and Bangla; the audio mix), and the website flow with real mouse and keyboard input. Unverified: Wan generation, Piper synthesis and the LLM on a real GPU, and the 6-8 minute target (warm cache). The first run downloads about 22 GB.
- **The Hindi voice is non-commercial only** (CC BY-NC-SA 4.0). The Bangla voice needs attribution (CC BY-SA 4.0).
- Hindi/Bangla voices read a product name written in English letters unpredictably; type it in Hindi/Bangla letters in the "Name as spoken" field.
- AI-written lines are not verified facts. Review `script.json` before publishing.

## Upgrade notes

The v1 notebook `Wan2.1_VACE_1.3B_T4_Colab.ipynb` was removed; use `Advvideo4you_AI_Ad_Generator.ipynb`. The notebook clones this repository at run time.