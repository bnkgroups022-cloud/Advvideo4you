# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

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