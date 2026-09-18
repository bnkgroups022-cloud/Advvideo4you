# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-09-19

### Added
- **Real product:** photo + product name + language (Hindi, English, Bangla) + CTA in, a 15-second 1080x1920 MP4 with AI-written script, Piper voice-over, animated captions and background music out.
- `advvideo/` package: launch-file format, script generator (Qwen2.5-1.5B-Instruct with validation and template fallback), Piper voice-over with 15-second timeline fitting, SRT and animated captions (drawtext, or ASS through libass when drawtext lacks HarfBuzz), synthesised CC0 music, FFmpeg render with ducked music and a spec check, Wan2.1 VACE launcher (33 frames, 18 steps, fp16, cached T5 embeddings), and the pipeline that runs the GPU stage alongside the audio work.
- New notebook `colab/Advvideo4you_AI_Ad_Generator.ipynb`: one Run-all cell, one upload prompt, automatic MP4 download.
- Launch flow on the website: a form (photo, name, language, CTA, optional spoken name and key details) that saves `advvideo-launch.json` and opens the notebook, with popup-blocked and notebook-unavailable messages.
- 100+ automated logic tests, LICENSE (MIT) and THIRD_PARTY_LICENSES.md.

### Changed
- The Start Free dialog is now the launch form instead of Colab instructions. Layout, branding, dark theme and the fixed-header scrolling-body dialog are unchanged.
- Site copy, FAQ and README describe the v2 product and its limits.

### Removed
- `colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb` (the v1 notebook, which made a silent 3-second clip).

### Known limitations
- The AI motion is about 2 seconds, looped forward and backward to 15 seconds.
- The Hindi voice is licensed for non-commercial use only.
- The Wan, Piper and LLM stages have not been run end to end on a real Colab T4 by the author; the 6-8 minute target is unmeasured.
## [1.0.0] - 2026-09-18

### Added
- SaaS homepage: hero, 3-step "How it works", feature cards, FAQ and footer with GitHub, Colab, version and copyright.
- "Start Free" dialog with the 5-step Colab flow (open Colab, choose the T4 runtime, Run all, upload a photo, download the MP4). `#start` deep-links to it.
- Light and dark themes (follows the system setting, with a manual toggle).
- SEO: title, meta description, canonical URL, favicon (SVG and ICO), Apple touch icon, OpenGraph and Twitter card tags with a 1200x630 preview image, `robots.txt`, `sitemap.xml`.
- `vercel.json` with security headers, a Content-Security-Policy and cache headers.
- README, changelog, version file and release notes.

### Changed
- The Colab notebook is now `colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb`: Wan2.1 VACE-1.3B through the official Wan-Video/Wan2.1 repository, replacing the earlier Wan 2.2 TI2V-5B notebook, which needed more memory than a free T4 offers.

### Fixed
- The production site returned 404 at `/` because the repository had no page to serve.
- Header overflow on screens narrower than 400 px.

## [0.3.0] - 2026-09-18
- Added the Wan2.1 VACE-1.3B notebook for the free T4 (single Run all, one image upload, automatic MP4 download, out-of-memory fallback).

## [0.2.0] - 2026-09-18
- Rebuilt the notebook around Wan 2.2 TI2V-5B for the free T4 using Diffusers; later discarded in favour of the official Wan2.1 repository.

## [0.1.0] - 2026-09-18
- First Colab notebook for Wan 2.2 image-to-video and the initial repository.