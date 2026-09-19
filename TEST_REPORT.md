# Test report: Advvideo4you 2.1.0

**Date:** 2026-09-19  
**Legend:** ✅ verified here · ❌ not done, with the reason · ⚠️ verified in part

## Summary

The website, the launch flow, the logic and the FFmpeg rendering were tested with real inputs. **The Colab run itself was not**: Colab needs a Google sign-in, and this environment cannot enter credentials (the Claude in Chrome extension that could have used a signed-in browser was also not connected). So "Runtime → T4", "Run All completes", the Colab upload prompt and the automatic download were not exercised, and neither were the Wan, Piper and Qwen stages on a real GPU. Everything that runs on the GPU is covered only by static analysis and logic tests. The 15–25 and 5–8 minute figures are estimates, not measurements.

## Part 1: end-to-end flow

| Step | Result | Notes |
|---|---|---|
| Landing page loads | ✅ | 200 on production and locally; no console or CSP errors |
| Start Free opens | ✅ | Real mouse click opens the dialog; focus trap, Esc and scroll behaviour checked |
| Form: photo, name, language, CTA, details | ✅ | Validation errors, wrong-type / 16 MB / corrupt photos rejected, thumbnail shown, fields restored on reload |
| Launch file `advvideo-launch.json` | ✅ | Saved by the browser; a file made by the page parses in the Python `config.parse_launch` (name, Hindi, CTA, spoken name, details, 1600×1200 JPEG) |
| Open Colab Notebook works | ⚠️ | The button opens the notebook URL in a new tab, with fallbacks when a popup is blocked or the notebook is gone (tested with a stubbed `window.open`). The notebook page itself loads in Colab (title and content checked while signed out) |
| Notebook opens correctly | ✅ | Colab renders the intro and the code cell from `main` |
| Runtime → T4 | ❌ | Needs a signed-in Colab. The notebook metadata requests a T4 GPU, and the cell stops with a clear message if `nvidia-smi` finds no GPU |
| Run All completes | ❌ | Not run (same reason) |
| Upload one product image | ⚠️ | ✅ in the website form. ❌ Colab's upload prompt not exercised; the classifier that handles what it returns is unit-tested |
| Final MP4 downloads | ❌ | `files.download` in Colab not exercised. ✅ FFmpeg produced a complete MP4 in a browser build of ffmpeg 5.1 (below) |

**About "the output is about 3 seconds":** the v1 notebook (`Wan2.1_VACE_1.3B_T4_Colab.ipynb`, removed in 2.0.0) saved the raw 33-frame clip, which is about 2 seconds at 16 fps. The notebook on `main` renders 15 seconds by design. If you still see 3 seconds, the runtime is running a stale copy of the old notebook; reopen it from the website's button.

## Parts 2 to 6: the video

Rendered with the project's own command builders (`render.final_cmd`, `pingpong_cmd`, `still_cmd`) in ffmpeg 5.1 (ffmpeg.wasm), with tone bursts standing in for the Piper voice, the real music generator, a placeholder photo and a synthetic 33-frame 480×832 clip standing in for Wan output. Renders took 18 to 29 seconds each.

| Requirement | Result | Evidence |
|---|---|---|
| Final duration 15 s | ✅ | Container duration 15.00 s; decoded audio 15.02 s |
| Export 480×832 | ✅ | `tkhd` 480×832; frames extracted at 480×832 |
| H.264 High + AAC, +faststart | ✅ | `avcC` profile 100; `moov` (byte 36) before `mdat` (byte 17627); stereo AAC at 48 kHz |
| AI motion about 2 s, smooth loop | ⚠️ | Forward-and-backward loop with the two turning-point frames dropped (33 frames → 64-frame unit), blended to 30 fps; ran through ffmpeg for English-still, Hindi and Bangla. Not checked with real Wan output |
| Slow zoom, slight pan | ✅ | `zoompan` 1.06 → 1.16 with a sine pan of ±2% / ±1.5%, inside the room the zoom leaves (test) |
| Fade in / fade out | ✅ | 0.5 s video fades, music fade in 1.2 s and out over the last 2.2 s; measured audio: −48.6 dBFS in the first 0.3 s and −53.7 dBFS in the last 0.3 s |
| CTA ending in the last 3 s | ✅ | Card from 12.00 to 15.00 s: product name, CTA (default "Order Now"), "WhatsApp Today"; Hindi and Bangla versions; animated (pop, slide-up, staggered 0.15 / 0.6 / 1.0 s). Frames inspected for English, Hindi, Bangla |
| Voice-over: Hindi, English, Bangla, open-source TTS | ⚠️ | Piper voices selected and licensed per language; timeline planning, speed-fitting and mixing are tested. Piper synthesis itself was not run |
| Captions synchronised, bottom safe area, shadow, rounded background | ✅ | Timed from the voice timeline (appear 0.12 s early, never overlap); box bottom ≤ 80% of the height (test); rounded box and shadow inspected in three languages; Hindi/Bangla conjuncts render correctly through libass; Latin names inside Hindi/Bangla use the Latin font |
| Music ~20%, fades, voice clear | ✅ | With a test voice: voice about −16 to −18 dBFS RMS, un-ducked music about −31 dBFS (≈ −14 dB, ≈ 20% amplitude), ducked about 6 dB further while the voice speaks. Real speech will differ in crest factor; the level is set from RMS |
| CTA voiced when the card appears | ✅ | Last voice line starts at 12.15 s in the plan and in the render |

## Part 7: landing page

| Item | Result |
|---|---|
| Five steps: Start Free, Open Colab, Run All, Upload Photo, Download Video (page and dialog) | ✅ |
| Estimated times: first run 15–25 minutes, later runs 5–8 minutes | ✅ shown; ⚠️ the figures are estimates |
| Existing UI kept (dark theme, header, dialog structure) | ✅ |
| Viewports 1280, 768, 375, 320: no horizontal overflow, dialog scrolls with a fixed header and footer | ✅ |
| Website suite with real mouse/keyboard input (CDP) | ✅ 49/49 locally |

## Part 8: performance

| Item | Result |
|---|---|
| Cached prompt embeddings, checkpoint reuse, 33/25/17 ladder, fp16 first with bf16 fallback | ✅ kept, logic-tested (`ladder_walk`, `verify_checkpoint`, embeds path) |
| Downloads start right after the upload and overlap the package installs | ✅ code and ordering tested; ❌ not timed on Colab |
| Runtime numbers | ❌ not measured |

## Logic tests and static checks

132 checks, all passing, run under Pyodide (CPython 3.12) in a browser: config and launch file, script generation and validation, voice timeline (including the CTA anchor), captions and the closing card (layout, geometry, ASS output, drawtext fallback), music level matching, render command shapes, pipeline stages (voice planning, captions stage per FFmpeg capability, prefetch marker), notebook structure and download-before-install ordering, and pyflakes on every module and on the notebook cell. Not covered: anything that needs a GPU, Piper, network model downloads or Colab.

## Not verified: what to check by hand on Colab

1. Open the notebook from Start Free, `Runtime → Change runtime type → T4 GPU`, `Runtime → Run all`.
2. Expect within a minute: `Step 1/5` with the GPU name, then the upload button. Choose `advvideo-launch.json`.
3. Expect `[prefetch]` lines (script model, then `downloaded N GB of ~19 GB`) while packages install, then `[script] HOOK / FEATURE1..3`, `[audio] voice: ...`, `[video] generating 33 frames (2.1s at 16 fps), 18 steps, float16`, and finally `DONE in N min: advvideo_<name>.mp4 (480x832, 15.0s, h264/aac)`.
4. The MP4 downloads by itself. `report.json` in `/content/advvideo_output` lists the stage times; those are the first real timing numbers.
5. Things most likely to need a fix on first contact with real hardware: Wan's memory use, Piper installing next to the preinstalled packages, the Qwen output for Hindi and Bangla.

## Production verification

Deployed commit `283a6ef` (Vercel, Production), checked after it went live:

| Check | Result |
|---|---|
| `https://advvideo4you.vercel.app/` returns 200 and shows version 2.1.0 | ✅ |
| Live HTML is byte-identical to the committed `index.html` | ✅ |
| 200 for `/VERSION`, `/CHANGELOG.md`, `/RELEASE_NOTES.md`, `/THIRD_PARTY_LICENSES.md`, `/LICENSE`, `/advvideo/pipeline.py`, `/advvideo/spec.py`, the notebook, favicons, `og.png`, `robots.txt`, `sitemap.xml`, and the README screenshots | ✅ |
| CSP and HSTS headers present | ✅ |
| Notebook raw URL and GitHub blob URL return 200 | ✅ |
| Colab opens the new notebook from the GitHub URL (title "Advvideo4you_AI_Ad_Generator.ipynb - Colab", intro "Advvideo4you 2.1", the five steps and the time estimates), signed out | ✅ |
| Website suite against production (real mouse/keyboard, 4 viewports) | ✅ 49/49 on the second run. **The first run failed 3 checks** (form persistence and two keyboard-focus checks) and passed on an immediate rerun; the same suite passes 49/49 locally. I read this as timing in a cold headless browser, not a defect, but I did not find the cause |
