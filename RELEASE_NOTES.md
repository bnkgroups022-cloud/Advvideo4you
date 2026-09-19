# Advvideo4you 2.1.0

**Released:** 2026-09-19  
**Site:** https://advvideo4you.vercel.app  
**Notebook:** https://colab.research.google.com/github/bnkgroups022-cloud/Advvideo4you/blob/main/colab/Advvideo4you_AI_Ad_Generator.ipynb

One product photo, a name, a language (Hindi, English or Bangla) and a call to action become a **15-second 480×832 vertical MP4** with AI motion, an AI-written script, voice-over, captions, background music and a closing call-to-action card, made on a free Google Colab T4.

![Captions and closing card in English, Hindi and Bangla](docs/screenshots/sample-frames.png)

*Layout preview rendered by this project's FFmpeg commands over a placeholder photo. Your video uses your photo and the AI clip.*

## What is new in 2.1.0

- **Closing card.** The last 3 seconds show the product name, your CTA (default "Order Now") and "WhatsApp Today", animated. The CTA is spoken as the card appears.
- **Captions.** Rounded dark boxes with a shadow, timed to the voice, kept above the bottom 20% of the screen. Hindi and Bangla shape correctly, and English product names inside them use the Latin font.
- **Motion.** The ~2-second AI clip loops forward and backward with no repeated turning frames, under a slow zoom and a slight pan, with a fade in and a fade out.
- **Music.** Scaled to about 20% of the voice level and ducked a little more while the voice speaks.
- **Size.** 480×832, the model's native size, instead of an upscale to 1080×1920.
- **Waiting less.** The 22 GB of models start downloading as soon as you upload your file and run while the packages install. Cached prompt embeddings, checkpoint reuse, the 33/25/17 frame ladder and fp16-then-bf16 are unchanged.
- **Website.** "How it works" and the Start Free dialog show the five steps (Start Free, Open Colab, Run All, Upload Photo, Download Video) with the estimated times: first run 15–25 minutes, later runs 5–8 minutes.

![How it works](docs/screenshots/how-it-works-1280.png)

## Known limitations (please read)

- **Not run end to end on a real Colab T4 by the author.** Colab needs a Google sign-in that this environment cannot perform. What was verified, and what was not, is in [`TEST_REPORT.md`](TEST_REPORT.md). The 15–25 and 5–8 minute figures are estimates.
- **The AI motion is about 2 seconds**, looped. The voice, captions, music and closing card carry the ad.
- **The Hindi voice is non-commercial only** (CC BY-NC-SA 4.0). The Bangla voice needs attribution (CC BY-SA 4.0).
- Hindi/Bangla voices read a product name written in English letters unpredictably; type it in Hindi/Bangla letters in the "Name as spoken" field.
- The closing card has no phone number: "WhatsApp Today" is text only.
- AI-written lines are not verified facts. Review `script.json` before publishing.

## Upgrade notes

Nothing to do: the notebook clones this repository at run time. Older runtimes keep their cached models.

## Earlier releases

See [`CHANGELOG.md`](CHANGELOG.md). 2.0.0 (2026-09-19) introduced the real product: launch file, script, voice, captions, music and the new notebook, replacing the v1 notebook that made a silent ~3-second clip.
