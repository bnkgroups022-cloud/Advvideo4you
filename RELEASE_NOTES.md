# Advvideo4you 1.0.0

**Released:** 2026-09-18  
**Site:** https://advvideo4you.vercel.app

First public release: a website and a Google Colab notebook that turn one product photo into a 9:16 vertical ad video on the free T4 GPU.

## Highlights

- **Homepage** with hero, how-it-works, features, FAQ and footer. Responsive from 320 px up, light and dark themes.
- **Start Free** opens a guided 5-step dialog so nobody is left wondering what to click in Colab.
- **Notebook**: Wan2.1 VACE-1.3B via the official Wan-Video/Wan2.1 repository. One Run all, one image upload, automatic `output.mp4` download, automatic fallback to shorter clips when memory runs out.
- **Production hygiene**: OpenGraph and Twitter tags, favicon set, robots and sitemap, security headers and a CSP, no external requests, no build step.

## Known limitations

- The notebook has been validated statically (syntax, logic tests, JSON) and against the pinned official sources, but it has not been executed end to end on a live Colab GPU by the release tooling. Please report the first real run's log if anything fails.
- Free Colab availability (GPU allocation, session length) is controlled by Google.
- The model is Wan2.1 VACE-1.3B in first-frame mode, which is not the same as a dedicated image-to-video model; motion quality will vary by photo.
- Check the model's license before commercial use.

## Upgrade notes

None. This is the first tagged release.