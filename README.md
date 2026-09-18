# Advvideo4you

Turn one product photo into a **9:16 vertical ad video** on the **free Google Colab T4 GPU**.

**Website:** https://advvideo4you.vercel.app  
**Notebook:** [`colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb`](colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bnkgroups022-cloud/Advvideo4you/blob/main/colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb)

## Quick start

1. Open the notebook in Colab (button above).
2. `Runtime -> Change runtime type -> T4 GPU -> Save`.
3. `Runtime -> Run all` (Ctrl+F9).
4. When the **Choose Files** button appears, upload one product photo (JPG or PNG).
5. `output.mp4` downloads automatically when generation finishes.

The first run also downloads about 19 GB of model files. Later runs in the same session are faster.

## What it does

- Model: **Wan2.1 VACE-1.3B**, run through the official [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) `generate.py` (task `vace-1.3B`), pinned to commit `9737cba`.
- Your photo becomes frame 0 (fitted to 9:16 with a blurred backdrop so the whole product stays visible); the model generates the rest.
- Output: 480x832 MP4 at 16 fps. Default length is 49 frames (about 3 s); raise it with the `FRAMES` form field at the top of the cell.
- Fits a free T4: the prompt is encoded once by the official T5 code in its own process, attention uses PyTorch SDPA (no `flash_attn`), the DiT runs in fp16, and each attempt is a fresh process that falls back from 49 to 33 to 17 frames on out-of-memory.
- One code cell, one upload prompt, no runtime restart.

There is no Wan 2.2 "I2V-1.3B" model: the Wan 2.2 repository only ships 14B and 5B models, so the 1.3B option that accepts an input image is Wan2.1 VACE-1.3B.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The website (single static file, no build step) |
| `colab/Wan2.1_VACE_1.3B_T4_Colab.ipynb` | The Colab notebook |
| `vercel.json` | Security and cache headers for Vercel |
| `favicon.*`, `apple-touch-icon.png`, `og.png` | Icons and social preview |
| `robots.txt`, `sitemap.xml` | SEO |
| `VERSION`, `CHANGELOG.md`, `RELEASE_NOTES.md` | Versioning and release info |

## Deployment

Pushing to `main` deploys the static site to Vercel automatically. There is no `package.json` and no build command.

## Limitations

- Colab decides GPU availability and session limits on free accounts; you may have to wait or retry.
- Check the Wan2.1 model license in its official repository before using the videos commercially.

## Version

See [`VERSION`](VERSION), [`CHANGELOG.md`](CHANGELOG.md) and [`RELEASE_NOTES.md`](RELEASE_NOTES.md).