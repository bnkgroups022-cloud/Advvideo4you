[package.json](https://github.com/user-attachments/files/32349456/package.json)# Advvideo4you
This is my ad video project

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# env files
.env
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Cloudinary will host uploaded product images from Phase 2 onward.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com", // Google account profile photos
      },
    ],
  },
};

export default nextConfig;

{
  "name": "offer-for-you",
  "version": "0.1.0",
  "private": true,
  "description": "Offer For You - BNK AI Ad Studio. AI-powered affiliate advertisement asset generator.",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "firebase": "^11.1.0",
    "clsx": "^2.1.1",
    "cloudinary": "^2.5.1",
    "openai": "^4.77.0",
    "zod": "^3.24.1"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.2",
    "@types/react-dom": "^19.0.2",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.5.0",
    "@eslint/eslintrc": "^3.2.0"
  },
  "engines": {
    "node": ">=18.18.0"
  }
}

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

# Offer For You — BNK AI Ad Studio (V1.0)

A SaaS platform where a user uploads a product image and AI generates a
full affiliate ad kit: prompts, video scripts, captions, WhatsApp copy,
hashtags, and downloadable assets.

This repo is being built **phase by phase**. Each phase is fully working
and testable on its own before the next one starts.

## Phase 1 — Auth & Dashboard (this delivery)

**Included:**
- Next.js 15 (App Router) + TypeScript + Tailwind CSS project scaffold
- Dark theme, mobile-first responsive UI, brand colors wired into Tailwind
- Premium marketing landing page at `/` — Hero, Features, How It Works,
  Pricing (Coming Soon), FAQ, Footer, with Login / Start Free CTAs
- Google Sign-In via Firebase Authentication
- Client-side protected `/dashboard` route (redirects to `/login` if signed out)
- Dashboard shell: sidebar (desktop) / drawer + bottom nav (mobile), topbar
  with profile menu and sign-out
- Dashboard widgets, as responsive cards: **Upload Product** (now live —
  see Phase 2 below), **Recent Projects** (honest empty state — no fake
  sample data — ready to list real projects once Supabase persistence
  exists), **AI Credits** (shows the true `0` used; live *usage tracking*
  still needs Supabase — the generator itself is live, see Phase 3),
  **Download History** (empty state until Phase 5), **Profile** (real:
  avatar, name, email, Google badge, join date, sign out)

**Not included yet** (later phases): Supabase persistence (saving
uploads/projects against a user), OpenAI-powered generators, and asset
downloads. Their env vars are already reserved in `.env.local.example`
so nothing has to be restructured later.

## Phase 2 — Image Upload (Cloudinary)

**Included:**
- Drag-and-drop **and** click-to-browse upload in the "Upload Product"
  dashboard widget
- Live **preview** thumbnail for every file, generated locally before
  upload even starts
- Real **progress bar** per file, driven by actual upload progress events
  (not a fake timer)
- **File validation** — type (JPG/PNG/WebP only) and size (8MB max),
  checked before upload, with the specific reason shown inline on
  rejected files
- **Delete** that actually works: removing a file that's still uploading
  cancels the request; removing one that's already on Cloudinary calls a
  server route (`/api/uploads/delete`) that signs a real delete request
  with the Cloudinary Admin SDK
- Files upload directly from the browser to Cloudinary via an **unsigned
  upload preset** — no file ever passes through our own server, so
  uploads aren't bottlenecked by it

**Not included yet:** uploaded photos aren't saved anywhere durable yet
(no Supabase table exists), so they won't appear in "Recent Projects"
and are **not** tied to your account — refreshing the page clears the
list from view (though the files remain on Cloudinary until deleted).
Wiring uploads to a real "projects" record is part of the Supabase work
still to come.

**Security note:** the delete route currently has no ownership check —
anyone who knows a `publicId` could ask the API to delete it, since
there's no database yet linking uploads to users. This is fine for this
single-tenant testing phase; the code has a `TODO` marking exactly where
to add an ownership check once Supabase exists.

## Phase 3 — AI Generator (OpenAI)

A single new page, **AI Generator** (`/dashboard/generate`), that takes a
product photo plus a few details and returns a complete ad kit in one
OpenAI call.

**Note on navigation:** Phase 1 originally sketched five separate
placeholder nav items — Prompt Generator, Script Generator, Caption
Generator, WhatsApp Copy, Hashtag Generator — on the assumption each
would be its own tool. Since the product always generates the whole kit
in a single pass (matching the landing page's "upload once, get
everything" pitch), those five have been consolidated into one **AI
Generator** nav item. The "Upload Product" nav placeholder was also
removed, since upload lives as a Dashboard widget, not a separate route.
The sidebar now has three real items: Dashboard, AI Generator, Download
Assets (still coming soon).

**Inputs:** Product Image (its own drag-and-drop upload, reusing the
Phase 2 Cloudinary pipeline), Product Name, Category (a select, with an
"Other" free-text option), Language (English, Hindi, Hinglish, Tamil,
Telugu, Bengali, Marathi).

**Outputs, generated together in one pass:**
- **Product Analysis** — 2-3 sentences on what the product is and who it appeals to
- **3 Hooks** — short scroll-stopping opening lines, each individually copyable
- **15-Second Script** — a time-coded short-form video script (0-3s / 3-10s / 10-15s beats)
- **Kling Prompt** — a cinematic prompt (always in English) ready to paste into Kling AI
- **WhatsApp Message** — a casual, friend-to-friend recommendation
- **Instagram Caption** — a ready-to-post caption (hashtags kept separate)
- **10 Hashtags** — shown as chips, copyable individually or all at once

Every output field (except the Kling prompt, which is intentionally
always English) is written in the language you selected — not machine-translated
English, but generated natively in that language.

**How it's wired:**
- `/api/generate` is a server route — this is the only place
  `OPENAI_API_KEY` is read, so it never reaches the browser
- Uses OpenAI's **Structured Outputs** (a JSON Schema passed as
  `response_format`) so the model is constrained to return exactly the
  7 fields above — no fragile regex-parsing of free-text output
- The parsed JSON is validated again with a `zod` schema server-side
  before it's ever sent to the browser, as defense-in-depth on top of
  Structured Outputs
- The product photo is sent to OpenAI as an image URL (the Cloudinary
  `secure_url` from the upload), not re-uploaded as base64

**Not included yet:** generated ad kits aren't saved anywhere — closing
or refreshing the page loses the result (copy anything you want to keep
before navigating away). Persisting kits as "projects" tied to your
account is Supabase work still to come, at which point they'll start
appearing in the Dashboard's "Recent Projects" widget.

**Security note:** like the Phase 2 delete route, `/api/generate` has no
per-user rate limiting or ownership check yet — anyone who can reach
your deployed app's `/api/generate` endpoint can trigger an OpenAI call
on your API key. Fine for local testing; before a public launch, add
rate limiting and tie requests to a signed-in user.

## Tech stack

- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Firebase Authentication (Google provider)
- Cloudinary (image upload, Phase 2 — live)
- OpenAI API (AI Generator, Phase 3 — live), validated with `zod`
- Supabase (persistence — not yet), Kling API (future, prompts are ready for it now)

## Prerequisites

- Node.js 18.18+ (Node 20 LTS recommended)
- A Firebase project with the **Google** sign-in provider enabled
- A Cloudinary account with an **unsigned upload preset** (free tier is fine)
- An OpenAI API key with access to a vision-capable model (e.g. `gpt-4o`)

> Note: this project was authored in a sandboxed environment without
> package-registry access, so `npm install` / `npm run build` have not
> been run here. Please run them locally as the first test — see
> "Phase 1 Test" below.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Set up Firebase — see the **Firebase Console Setup** walkthrough below
   if this is your first time; short version:
   - Build → Authentication → Sign-in method → enable **Google**
   - Project settings → General → "Your apps" → add a **Web app** →
     copy the `firebaseConfig` values
3. Set up Cloudinary — see the **Cloudinary Console Setup** walkthrough
   below; short version: grab your cloud name from the dashboard, create
   an unsigned upload preset, and grab your API key/secret.
4. Set up OpenAI — see the **OpenAI Setup** walkthrough below; short
   version: create an API key at platform.openai.com and add billing
   (the API isn't covered by a ChatGPT subscription).
5. Copy the env template and fill it in:
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in the six `NEXT_PUBLIC_FIREBASE_*` values, the four
   `CLOUDINARY_*` / `NEXT_PUBLIC_CLOUDINARY_*` values, and
   `OPENAI_API_KEY`. Leave Supabase / Kling blank — reserved for later.
6. Run the dev server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000
7. Click **Get started free** → **Continue with Google** → you should
   land on `/dashboard` signed in, and refreshing should keep you signed
   in (and redirect straight to `/dashboard` from `/`).

## Firebase Console Setup (step by step)

Everything here happens at https://console.firebase.google.com — no
billing account or credit card needed for Authentication.

**1. Create the project**
1. Click **Add project** (or **Create a project**).
2. Enter a project name, e.g. `offer-for-you`. Firebase suggests a unique
   project ID underneath — you can leave it as-is.
3. You'll be asked about Google Analytics — you can toggle it **off** for
   this project; it isn't needed for Authentication.
4. Click **Create project** and wait for it to finish provisioning.

**2. Enable the Google sign-in provider**
1. In the left sidebar, open **Build → Authentication**.
2. Click **Get started** (first time only).
3. Go to the **Sign-in method** tab.
4. Click **Google** in the provider list.
5. Toggle **Enable**.
6. Set a **Project public-facing name** (shown on the Google consent
   screen, e.g. "Offer For You") and a **Project support email** (pick
   your own email from the dropdown).
7. Click **Save**.

**3. Register a Web app and get your config**
1. Click the **gear icon → Project settings** in the left sidebar.
2. Scroll to **Your apps** and click the **`</>`** (Web) icon to add a
   web app.
3. Give it a nickname, e.g. `offer-for-you-web`. You do **not** need to
   check "Also set up Firebase Hosting."
4. Click **Register app**. Firebase shows a `firebaseConfig` object —
   copy the six values (`apiKey`, `authDomain`, `projectId`,
   `storageBucket`, `messagingSenderId`, `appId`) into your `.env.local`
   as the matching `NEXT_PUBLIC_FIREBASE_*` variables.
5. Click **Continue to console** — you can skip the SDK install
   instructions Firebase shows, since the `firebase` npm package is
   already in this project's `package.json`.

**4. Authorize the domains that will run this app**
1. Still in **Authentication**, go to the **Settings** tab → **Authorized
   domains**.
2. `localhost` is included by default, so local development works
   immediately.
3. When you deploy, add your deployed domain here too (e.g.
   `your-app.vercel.app`, and later your custom domain) — otherwise
   Google sign-in fails on that domain with `auth/unauthorized-domain`.

**5. Confirm it's wired up correctly**
1. In this project, copy `.env.local.example` to `.env.local` and paste
   in the six values from step 3.
2. Run `npm run dev`, open the app, and click **Start Free** or
   **Login → Continue with Google**.
3. A Google account-picker popup should appear. After choosing an
   account, you should land on `/dashboard` with your name, email and
   photo showing in the top-right menu.

**Common issues**
- **`auth/unauthorized-domain`** — the domain you're testing from isn't
  in Authorized domains (step 4).
- **Popup closes immediately / `auth/popup-blocked`** — your browser
  blocked the sign-in popup; allow popups for `localhost` and retry.
- **Sign-in button is disabled** — `.env.local` is missing or one of the
  six `NEXT_PUBLIC_FIREBASE_*` values is empty; check the browser
  console for the exact missing-key warning this project logs.

## Cloudinary Console Setup (step by step)

Everything here happens at https://console.cloudinary.com — the free
tier is enough for development.

**1. Create an account and find your cloud name**
1. Sign up (or log in) at https://cloudinary.com.
2. On the **Dashboard**, copy the **Cloud name** shown near the top —
   this goes in `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`.

**2. Create an unsigned upload preset**
Uploads happen directly from the browser, so they use an *unsigned*
preset rather than your secret API key.
1. Go to the **gear icon → Settings → Upload**.
2. Scroll to **Upload presets** → click **Add upload preset**.
3. Set **Signing Mode** to **Unsigned**.
4. (Recommended) Set **Folder** to `offer-for-you/products` so every
   upload from this app is organized under one folder automatically.
5. (Recommended, defense-in-depth) Under the preset's restrictions, set
   **Allowed formats** to `jpg, png, webp` and a max file size — this
   backs up the client-side validation this project already does.
6. Click **Save**, then copy the preset's **name** into
   `NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET`.

**3. Get your API key and secret (for deleting files)**
1. Back on the **Dashboard**, find **API Key** and **API Secret** (click
   "reveal" for the secret).
2. Copy them into `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET` — no
   `NEXT_PUBLIC_` prefix on these two; they must stay server-only.

**4. Confirm it's wired up correctly**
1. Fill in all four Cloudinary values in `.env.local`.
2. Run `npm run dev`, sign in, and on the dashboard's Upload Product
   card, drag in a JPG or PNG.
3. You should see a thumbnail preview immediately, a progress bar while
   it uploads, then a green "Uploaded" badge and a "View on Cloudinary"
   link — click it to confirm the file really is on Cloudinary.
4. Click the trash icon to delete it — the item should disappear from
   the list. To fully confirm, check Cloudinary's **Media Library** in
   the console; the file (and folder, if you set one) should be gone.

**Common issues**
- **Upload silently fails / network error** — double check
  `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` and
  `NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET` are both set and the preset is
  actually **Unsigned** (a signed preset will reject browser uploads
  that don't include a signature).
- **"Upload preset not found"** — the preset name in `.env.local`
  doesn't match one in Console > Settings > Upload exactly (case-sensitive).
- **Delete button shows an error** — `CLOUDINARY_API_KEY` /
  `CLOUDINARY_API_SECRET` are missing from `.env.local`, or the dev
  server needs a restart after adding them (Next.js only reads
  `.env.local` at startup).

## OpenAI Setup (step by step)

Everything here happens at https://platform.openai.com — note that this
is separate from a ChatGPT Plus subscription; API usage is billed
separately (pay-as-you-go), typically a few cents per generation.

**1. Create an API key**
1. Log in (or sign up) at https://platform.openai.com.
2. Go to **Dashboard → API keys** (or platform.openai.com/api-keys).
3. Click **Create new secret key**, give it a name like
   `offer-for-you-dev`, and copy the key immediately — it's only shown once.
4. Paste it into `OPENAI_API_KEY` in `.env.local`. Leave `OPENAI_MODEL`
   blank unless you want to override the default (`gpt-4o`).

**2. Add billing**
1. Go to **Settings → Billing** and add a payment method plus a small
   initial credit balance. Without this, API calls fail even with a
   valid key.
2. (Recommended) Set a monthly budget/usage limit under Billing so a bug
   or unexpected traffic can't run up a large bill.

**3. Confirm it's wired up correctly**
1. Fill in `OPENAI_API_KEY` (and Cloudinary's four values, if not
   already done) in `.env.local`, then restart `npm run dev`.
2. Sign in, go to the sidebar's **AI Generator**, upload a product photo,
   fill in a name and category, and click **Generate Ad Kit**.
3. After 10-30 seconds you should see all 7 output sections filled in —
   Product Analysis, 3 Hooks, 15-Second Script, Kling Prompt, WhatsApp
   Message, Instagram Caption, 10 Hashtags — each with a working Copy button.

**Common issues**
- **"OpenAI isn't configured" / 500 error immediately** —
  `OPENAI_API_KEY` is missing from `.env.local`, or the dev server
  wasn't restarted after adding it.
- **401 Unauthorized** — the key is invalid, revoked, or pasted with
  extra whitespace.
- **429 / quota errors** — no billing/credit added yet (see step 2), or
  you've hit your usage limit.
- **Generation times out** — vision + structured-output responses can
  take 15-30s; locally this is fine, but on Vercel's free tier, function
  duration is capped lower than the `maxDuration = 60` this route
  requests. If you see timeouts in production, check your Vercel plan's
  function duration limit.
- **Response doesn't match the expected format** — very rare with
  Structured Outputs, but if your `OPENAI_MODEL` override points at a
  model that doesn't support `response_format: json_schema`, generation
  will fail with a clear error; switch back to a model that does (e.g. `gpt-4o`).

## Folder structure

```
src/
  app/
    layout.tsx          Root layout (fonts, dark theme, AuthProvider)
    page.tsx             Public landing page
    login/page.tsx        Google sign-in screen
    dashboard/
      layout.tsx          AuthGuard + DashboardShell wrapper
      page.tsx            Dashboard home (widget grid)
      generate/page.tsx    AI Generator: form + results, two-column layout
    api/
      uploads/delete/route.ts  Server route: signed Cloudinary destroy
      generate/route.ts        Server route: OpenAI call (has the API key)
  components/
    ui/                  Button, Card, Icon — generic building blocks
    landing/             Navbar, Hero, Features, HowItWorks, Pricing, FAQ,
                          Footer, LandingPage (composes all of the above),
                          content.ts (all landing page copy)
    layout/              Sidebar, Topbar, MobileNav, DashboardShell
    auth/                GoogleSignInButton, AuthGuard, UserAvatar
    dashboard/           UploadProductWidget, RecentProjectsWidget,
                          AICreditsWidget, DownloadHistoryWidget,
                          ProfileWidget, EmptyState (shared empty-state UI)
    upload/              Dropzone (supports single or multi-file),
                          UploadItemCard, ProgressBar
    generator/           GeneratorForm, GeneratorResults, ProductImagePicker,
                          OutputSection, CopyButton
  context/AuthContext.tsx Firebase auth state, exposed via useAuth()
  hooks/useAuth.ts
  hooks/useImageUpload.ts       Upload list state (dashboard widget)
  hooks/useSingleImageUpload.ts One-image variant (AI Generator form)
  hooks/useAdGenerator.ts       Calls /api/generate, tracks status/result
  lib/firebase/          client.ts (init) + auth.ts (sign-in/out helpers)
  lib/cloudinary/        validate.ts, upload.ts, delete.ts (client-safe),
                          server.ts (Admin SDK — server-only, has the secret)
  lib/openai/            server.ts (client — server-only, has the API key),
                          prompt.ts (system/user prompt builders),
                          schema.ts (zod validation + the JSON Schema
                          passed to OpenAI's Structured Outputs)
  config/brand.ts        Brand colors + the nav map
  config/generator.ts    Category and language options for the form
  types/user.ts, types/upload.ts, types/generator.ts
```

## Deploy to Vercel

1. Push this project to a GitHub repo (Vercel deploys from git).
2. Go to https://vercel.com/new and import that repo.
3. Framework preset: Vercel auto-detects **Next.js** — leave build command
   as `next build` and output as default.
4. Before the first deploy, add environment variables under
   **Project Settings → Environment Variables** (copy every key from
   `.env.local.example` that you've filled in — at minimum the six
   `NEXT_PUBLIC_FIREBASE_*` values, the four Cloudinary values, and
   `OPENAI_API_KEY`). Add them to all three environments (Production,
   Preview, Development). `/api/uploads/delete` and `/api/generate` both
   run as Vercel serverless functions automatically — no extra config
   needed, though `/api/generate` requests up to 60s of execution time
   (`maxDuration` in the route file); check your plan's function-duration
   limit if generation times out in production.
5. Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL.
6. Back in the Firebase console → Authentication → Settings →
   **Authorized domains** → add your `*.vercel.app` domain (and your
   custom domain later) or Google sign-in will fail on the deployed site
   with an `auth/unauthorized-domain` error.
7. For later phases: once Cloudinary/Supabase/OpenAI keys exist, add them
   the same way before redeploying — no code changes needed, the env
   vars are already wired to be read from `process.env`.

Redeploying after future phases is automatic: every push to your main
branch triggers a new Vercel deployment.

## Phase 1 Test

Run through this after `npm install`:

1. `npm install` completes with no errors
2. `npm run build` completes with no type/lint errors
3. `npm run dev` → open `http://localhost:3000` and check the landing
   page: Navbar (Login / Start Free), Hero, Features, How It Works,
   Pricing (Coming Soon), FAQ accordion, Footer all render
4. Click each Navbar anchor link (Features / How it works / Pricing /
   FAQ) — page smooth-scrolls to that section
5. On Pricing, submit an email in "Notify me" — it shows a confirmation
   message (UI only for now; not yet wired to a real waitlist backend)
6. Click **Start Free** or **Login** → **Continue with Google** → lands
   on `/dashboard` signed in
7. Refresh `/dashboard` — session persists (no bounce to `/login`)
8. On `/dashboard`, check all 5 widgets render as cards: Upload Product
   (drop-zone + disabled button), Recent Projects (empty state), AI
   Credits (shows "0 credits used"), Download History (empty state),
   Profile (your avatar, name, email, "Google account" badge, join date)
9. Resize to phone width — Navbar collapses to a hamburger menu, the
   dashboard sidebar becomes a drawer + bottom nav bar, and the widget
   grid stacks to a single column
10. Sign out from the profile menu (top right) or the Profile widget's
    Sign out button → redirected to `/login`
11. Visit `/dashboard` directly while signed out → redirected to `/login`
    (route protection works)

Report back what breaks, if anything, and I'll fix it before moving on.

## Phase 2 Test

Run through this after filling in the four Cloudinary env vars:

1. On the dashboard's **Upload Product** card, drag a JPG/PNG/WebP onto
   the drop zone — a thumbnail preview and a progress bar appear
   immediately, then a green "Uploaded" badge
2. Click "View on Cloudinary" on an uploaded file — it opens the real
   image at a `res.cloudinary.com` URL
3. Click to browse instead of dragging — same result
4. Try uploading a `.pdf` or `.gif` — it's rejected inline with "Unsupported
   file type," no network request is made
5. Try uploading a file larger than 8MB — rejected inline with a
   "File is too large" message
6. Drag in 2–3 valid files at once — each gets its own row with its own
   progress bar, uploading independently
7. Click delete (trash icon) on a file **while it's still uploading** —
   the upload stops and the row disappears
8. Click delete on a file that finished uploading — it briefly shows
   "Deleting," then disappears; check Cloudinary's Media Library to
   confirm it's actually gone, not just hidden in the UI
9. Refresh the page — the upload list is empty again (expected: nothing
   is persisted yet, see "Not included yet" under Phase 2 above)
10. Resize to phone width — the widget and its file rows stay readable
    and don't overflow horizontally

Report back what breaks, and I'll fix it before moving on.

## Phase 3 Test

Run through this after filling in `OPENAI_API_KEY`:

1. Sidebar → **AI Generator** loads a two-column form + results layout
2. Try clicking **Generate Ad Kit** with the form incomplete — it's
   disabled until an image is uploaded, a name is entered, and a category
   is chosen
3. Upload a product photo in the form's own image picker — same
   preview/progress behavior as the dashboard's Upload Product widget
4. Fill in a name (e.g. "Wireless Neckband Earphones"), pick a category,
   pick a language, click **Generate Ad Kit**
5. A loading state appears ("Generating your ad kit…"); after ~10-30s,
   all 7 sections render: Product Analysis, 3 Hooks, 15-Second Script,
   Kling Prompt, WhatsApp Message, Instagram Caption, 10 Hashtags
6. Everything reads in the language you picked (except the Kling prompt,
   which should always be English)
7. Click a few **Copy** buttons — paste somewhere to confirm the right
   text copied, and the button briefly shows "Copied ✓"
8. Click **Copy all** on Hooks and on Hashtags — confirm all 3 / all 10
   come through in one paste
9. Click **Start over** — the form and results both reset
10. Try selecting **Category → Other** — a free-text field appears and
    is required before Generate becomes enabled
11. Turn off your network (or use an invalid `OPENAI_API_KEY` temporarily)
    and try generating — a clear error message appears with a "Try again"
    button, not a silent failure or a stuck spinner
12. Resize to phone width — the form and results stack into a single
    column and stay readable

Report back what breaks, and I'll fix it before we tackle Supabase
persistence (saving generated kits as real projects).

## Roadmap (next phases)

- **Phase 2 (upload):** done — Supabase schema so uploads persist as
  real projects tied to a user is still outstanding
- **Phase 3 (AI Generator):** done — Product Analysis, 3 Hooks,
  15-Second Script, Kling Prompt, WhatsApp Message, Instagram Caption,
  10 Hashtags, all from one OpenAI call
- **Phase 4:** Supabase — persist generated ad kits as "projects,"
  populate Recent Projects and AI Credits with real data, add ownership
  checks to `/api/uploads/delete` and `/api/generate`
- **Phase 5:** Download Assets (zip/export of a generated kit), polish,
  Kling API groundwork (the Kling prompt output is already
  Kling-ready — wiring the actual Kling API call is what's left)

## Brand colors

| Token | Hex |
|---|---|
| Primary | `#344CB7` |
| Secondary | `#577BC1` |
| Accent | `#0EA5E9` |
| Dark | `#000957` |

{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# ------------------------------------------------------------------
# Offer For You - BNK AI Ad Studio
# Copy this file to .env.local and fill in real values.
# .env.local is git-ignored and must never be committed.
# ------------------------------------------------------------------

# --- Firebase Authentication (Phase 1 - required now) --------------
# Get these from Firebase Console > Project Settings > General > Your apps > Web app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# --- Supabase Database (Phase 2+ - reserved, not used yet) ---------
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# --- Cloudinary Storage (Phase 2 - required now for image upload) --
# Cloud name is not secret - it's used both in the browser (to upload
# directly to Cloudinary) and on the server (to delete assets).
# Get it from Cloudinary Console > Dashboard > "Cloud name".
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=
# An UNSIGNED upload preset - create it in Console > Settings > Upload >
# Upload presets. See the README's "Cloudinary Console Setup" section.
NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET=
# Server-only - used by the /api/uploads/delete route to remove assets.
# Never expose these with a NEXT_PUBLIC_ prefix.
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# --- OpenAI API (Phase 3 - required now for the AI Generator) ------
# Server-only - never expose this with a NEXT_PUBLIC_ prefix.
OPENAI_API_KEY=
# Optional: override the model used for generation. Must be a
# vision-capable model that supports Structured Outputs (JSON schema).
# Defaults to gpt-4o if left blank.
OPENAI_MODEL=

# --- Kling API (future integration - reserved, not used yet) -------
KLING_API_KEY=

import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
];

export default eslintConfig;

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#344CB7",
          secondary: "#577BC1",
          accent: "#0EA5E9",
          dark: "#000957",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #000957 0%, #344CB7 55%, #0EA5E9 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "fade-in-up": "fadeInUp 0.6s ease-out both",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Cloudinary will host uploaded product images from Phase 2 onward.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com", // Google account profile photos
      },
    ],
  },
};

export default nextConfig;

{
  "name": "offer-for-you",
  "version": "0.1.0",
  "private": true,
  "description": "Offer For You - BNK AI Ad Studio. AI-powered affiliate advertisement asset generator.",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "firebase": "^11.1.0",
    "clsx": "^2.1.1",
    "cloudinary": "^2.5.1"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.2",
    "@types/react-dom": "^19.0.2",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.5.0",
    "@eslint/eslintrc": "^3.2.0"
  },
  "engines": {
    "node": ">=18.18.0"
  }
}

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

# Offer For You — BNK AI Ad Studio (V1.0)

A SaaS platform where a user uploads a product image and AI generates a
full affiliate ad kit: prompts, video scripts, captions, WhatsApp copy,
hashtags, and downloadable assets.

This repo is being built **phase by phase**. Each phase is fully working
and testable on its own before the next one starts.

## Phase 1 — Auth & Dashboard (this delivery)

**Included:**
- Next.js 15 (App Router) + TypeScript + Tailwind CSS project scaffold
- Dark theme, mobile-first responsive UI, brand colors wired into Tailwind
- Premium marketing landing page at `/` — Hero, Features, How It Works,
  Pricing (Coming Soon), FAQ, Footer, with Login / Start Free CTAs
- Google Sign-In via Firebase Authentication
- Client-side protected `/dashboard` route (redirects to `/login` if signed out)
- Dashboard shell: sidebar (desktop) / drawer + bottom nav (mobile), topbar
  with profile menu and sign-out
- Dashboard widgets, as responsive cards: **Upload Product** (now live —
  see Phase 2 below), **Recent Projects** (honest empty state — no fake
  sample data — ready to list real projects once Supabase persistence
  exists), **AI Credits** (shows the true `0` used; live tracking arrives
  with Phase 3's generators), **Download History** (empty state until
  Phase 5), **Profile** (real: avatar, name, email, Google badge, join
  date, sign out)
- Placeholder cards for every V1.0 feature (Prompt Generator, Script
  Generator, Caption Generator, WhatsApp Copy, Hashtag Generator, Downloads)
  so the full product shape is visible from day one

**Not included yet** (later phases): Supabase persistence (saving
uploads/projects against a user), OpenAI-powered generators, and asset
downloads. Their env vars are already reserved in `.env.local.example`
so nothing has to be restructured later.

## Phase 2 — Image Upload (Cloudinary)

**Included:**
- Drag-and-drop **and** click-to-browse upload in the "Upload Product"
  dashboard widget
- Live **preview** thumbnail for every file, generated locally before
  upload even starts
- Real **progress bar** per file, driven by actual upload progress events
  (not a fake timer)
- **File validation** — type (JPG/PNG/WebP only) and size (8MB max),
  checked before upload, with the specific reason shown inline on
  rejected files
- **Delete** that actually works: removing a file that's still uploading
  cancels the request; removing one that's already on Cloudinary calls a
  server route (`/api/uploads/delete`) that signs a real delete request
  with the Cloudinary Admin SDK
- Files upload directly from the browser to Cloudinary via an **unsigned
  upload preset** — no file ever passes through our own server, so
  uploads aren't bottlenecked by it

**Not included yet:** uploaded photos aren't saved anywhere durable yet
(no Supabase table exists), so they won't appear in "Recent Projects"
and are **not** tied to your account — refreshing the page clears the
list from view (though the files remain on Cloudinary until deleted).
Wiring uploads to a real "projects" record is part of the Supabase work
still to come.

**Security note:** the delete route currently has no ownership check —
anyone who knows a `publicId` could ask the API to delete it, since
there's no database yet linking uploads to users. This is fine for this
single-tenant testing phase; the code has a `TODO` marking exactly where
to add an ownership check once Supabase exists.

## Tech stack

- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Firebase Authentication (Google provider)
- Cloudinary (image upload, Phase 2 — live)
- Supabase (Phase 2+, persistence — not yet), OpenAI API (Phase 3+), Kling API (future)

## Prerequisites

- Node.js 18.18+ (Node 20 LTS recommended)
- A Firebase project with the **Google** sign-in provider enabled
- A Cloudinary account with an **unsigned upload preset** (free tier is fine)

> Note: this project was authored in a sandboxed environment without
> package-registry access, so `npm install` / `npm run build` have not
> been run here. Please run them locally as the first test — see
> "Phase 1 Test" below.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Set up Firebase — see the **Firebase Console Setup** walkthrough below
   if this is your first time; short version:
   - Build → Authentication → Sign-in method → enable **Google**
   - Project settings → General → "Your apps" → add a **Web app** →
     copy the `firebaseConfig` values
3. Set up Cloudinary — see the **Cloudinary Console Setup** walkthrough
   below; short version: grab your cloud name from the dashboard, create
   an unsigned upload preset, and grab your API key/secret.
4. Copy the env template and fill it in:
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in the six `NEXT_PUBLIC_FIREBASE_*` values and the four
   `CLOUDINARY_*` / `NEXT_PUBLIC_CLOUDINARY_*` values. Leave Supabase /
   OpenAI / Kling blank — they're reserved for later phases.
5. Run the dev server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000
6. Click **Get started free** → **Continue with Google** → you should
   land on `/dashboard` signed in, and refreshing should keep you signed
   in (and redirect straight to `/dashboard` from `/`).

## Firebase Console Setup (step by step)

Everything here happens at https://console.firebase.google.com — no
billing account or credit card needed for Authentication.

**1. Create the project**
1. Click **Add project** (or **Create a project**).
2. Enter a project name, e.g. `offer-for-you`. Firebase suggests a unique
   project ID underneath — you can leave it as-is.
3. You'll be asked about Google Analytics — you can toggle it **off** for
   this project; it isn't needed for Authentication.
4. Click **Create project** and wait for it to finish provisioning.

**2. Enable the Google sign-in provider**
1. In the left sidebar, open **Build → Authentication**.
2. Click **Get started** (first time only).
3. Go to the **Sign-in method** tab.
4. Click **Google** in the provider list.
5. Toggle **Enable**.
6. Set a **Project public-facing name** (shown on the Google consent
   screen, e.g. "Offer For You") and a **Project support email** (pick
   your own email from the dropdown).
7. Click **Save**.

**3. Register a Web app and get your config**
1. Click the **gear icon → Project settings** in the left sidebar.
2. Scroll to **Your apps** and click the **`</>`** (Web) icon to add a
   web app.
3. Give it a nickname, e.g. `offer-for-you-web`. You do **not** need to
   check "Also set up Firebase Hosting."
4. Click **Register app**. Firebase shows a `firebaseConfig` object —
   copy the six values (`apiKey`, `authDomain`, `projectId`,
   `storageBucket`, `messagingSenderId`, `appId`) into your `.env.local`
   as the matching `NEXT_PUBLIC_FIREBASE_*` variables.
5. Click **Continue to console** — you can skip the SDK install
   instructions Firebase shows, since the `firebase` npm package is
   already in this project's `package.json`.

**4. Authorize the domains that will run this app**
1. Still in **Authentication**, go to the **Settings** tab → **Authorized
   domains**.
2. `localhost` is included by default, so local development works
   immediately.
3. When you deploy, add your deployed domain here too (e.g.
   `your-app.vercel.app`, and later your custom domain) — otherwise
   Google sign-in fails on that domain with `auth/unauthorized-domain`.

**5. Confirm it's wired up correctly**
1. In this project, copy `.env.local.example` to `.env.local` and paste
   in the six values from step 3.
2. Run `npm run dev`, open the app, and click **Start Free** or
   **Login → Continue with Google**.
3. A Google account-picker popup should appear. After choosing an
   account, you should land on `/dashboard` with your name, email and
   photo showing in the top-right menu.

**Common issues**
- **`auth/unauthorized-domain`** — the domain you're testing from isn't
  in Authorized domains (step 4).
- **Popup closes immediately / `auth/popup-blocked`** — your browser
  blocked the sign-in popup; allow popups for `localhost` and retry.
- **Sign-in button is disabled** — `.env.local` is missing or one of the
  six `NEXT_PUBLIC_FIREBASE_*` values is empty; check the browser
  console for the exact missing-key warning this project logs.

## Cloudinary Console Setup (step by step)

Everything here happens at https://console.cloudinary.com — the free
tier is enough for development.

**1. Create an account and find your cloud name**
1. Sign up (or log in) at https://cloudinary.com.
2. On the **Dashboard**, copy the **Cloud name** shown near the top —
   this goes in `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME`.

**2. Create an unsigned upload preset**
Uploads happen directly from the browser, so they use an *unsigned*
preset rather than your secret API key.
1. Go to the **gear icon → Settings → Upload**.
2. Scroll to **Upload presets** → click **Add upload preset**.
3. Set **Signing Mode** to **Unsigned**.
4. (Recommended) Set **Folder** to `offer-for-you/products` so every
   upload from this app is organized under one folder automatically.
5. (Recommended, defense-in-depth) Under the preset's restrictions, set
   **Allowed formats** to `jpg, png, webp` and a max file size — this
   backs up the client-side validation this project already does.
6. Click **Save**, then copy the preset's **name** into
   `NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET`.

**3. Get your API key and secret (for deleting files)**
1. Back on the **Dashboard**, find **API Key** and **API Secret** (click
   "reveal" for the secret).
2. Copy them into `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET` — no
   `NEXT_PUBLIC_` prefix on these two; they must stay server-only.

**4. Confirm it's wired up correctly**
1. Fill in all four Cloudinary values in `.env.local`.
2. Run `npm run dev`, sign in, and on the dashboard's Upload Product
   card, drag in a JPG or PNG.
3. You should see a thumbnail preview immediately, a progress bar while
   it uploads, then a green "Uploaded" badge and a "View on Cloudinary"
   link — click it to confirm the file really is on Cloudinary.
4. Click the trash icon to delete it — the item should disappear from
   the list. To fully confirm, check Cloudinary's **Media Library** in
   the console; the file (and folder, if you set one) should be gone.

**Common issues**
- **Upload silently fails / network error** — double check
  `NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME` and
  `NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET` are both set and the preset is
  actually **Unsigned** (a signed preset will reject browser uploads
  that don't include a signature).
- **"Upload preset not found"** — the preset name in `.env.local`
  doesn't match one in Console > Settings > Upload exactly (case-sensitive).
- **Delete button shows an error** — `CLOUDINARY_API_KEY` /
  `CLOUDINARY_API_SECRET` are missing from `.env.local`, or the dev
  server needs a restart after adding them (Next.js only reads
  `.env.local` at startup).

## Folder structure

```
src/
  app/
    layout.tsx          Root layout (fonts, dark theme, AuthProvider)
    page.tsx             Public landing page
    login/page.tsx        Google sign-in screen
    dashboard/
      layout.tsx          AuthGuard + DashboardShell wrapper
      page.tsx            Dashboard home (widget grid)
    api/uploads/delete/route.ts  Server route: signed Cloudinary destroy
  components/
    ui/                  Button, Card, Icon — generic building blocks
    landing/             Navbar, Hero, Features, HowItWorks, Pricing, FAQ,
                          Footer, LandingPage (composes all of the above),
                          content.ts (all landing page copy)
    layout/              Sidebar, Topbar, MobileNav, DashboardShell
    auth/                GoogleSignInButton, AuthGuard, UserAvatar
    dashboard/           UploadProductWidget, RecentProjectsWidget,
                          AICreditsWidget, DownloadHistoryWidget,
                          ProfileWidget, EmptyState (shared empty-state UI)
    upload/              Dropzone, UploadItemCard, ProgressBar
  context/AuthContext.tsx Firebase auth state, exposed via useAuth()
  hooks/useAuth.ts
  hooks/useImageUpload.ts  Upload list state: add/validate/upload/delete
  lib/firebase/          client.ts (init) + auth.ts (sign-in/out helpers)
  lib/cloudinary/        validate.ts, upload.ts, delete.ts (client-safe),
                          server.ts (Admin SDK — server-only, has the secret)
  config/brand.ts        Brand colors + the full V1.0 nav/feature map
  types/user.ts, types/upload.ts
```

## Deploy to Vercel

1. Push this project to a GitHub repo (Vercel deploys from git).
2. Go to https://vercel.com/new and import that repo.
3. Framework preset: Vercel auto-detects **Next.js** — leave build command
   as `next build` and output as default.
4. Before the first deploy, add environment variables under
   **Project Settings → Environment Variables** (copy every key from
   `.env.local.example` that you've filled in — at minimum the six
   `NEXT_PUBLIC_FIREBASE_*` values and the four Cloudinary values).
   Add them to all three environments (Production, Preview, Development).
   `/api/uploads/delete` runs as a Vercel serverless function
   automatically — no extra config needed.
5. Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL.
6. Back in the Firebase console → Authentication → Settings →
   **Authorized domains** → add your `*.vercel.app` domain (and your
   custom domain later) or Google sign-in will fail on the deployed site
   with an `auth/unauthorized-domain` error.
7. For later phases: once Cloudinary/Supabase/OpenAI keys exist, add them
   the same way before redeploying — no code changes needed, the env
   vars are already wired to be read from `process.env`.

Redeploying after future phases is automatic: every push to your main
branch triggers a new Vercel deployment.

## Phase 1 Test

Run through this after `npm install`:

1. `npm install` completes with no errors
2. `npm run build` completes with no type/lint errors
3. `npm run dev` → open `http://localhost:3000` and check the landing
   page: Navbar (Login / Start Free), Hero, Features, How It Works,
   Pricing (Coming Soon), FAQ accordion, Footer all render
4. Click each Navbar anchor link (Features / How it works / Pricing /
   FAQ) — page smooth-scrolls to that section
5. On Pricing, submit an email in "Notify me" — it shows a confirmation
   message (UI only for now; not yet wired to a real waitlist backend)
6. Click **Start Free** or **Login** → **Continue with Google** → lands
   on `/dashboard` signed in
7. Refresh `/dashboard` — session persists (no bounce to `/login`)
8. On `/dashboard`, check all 5 widgets render as cards: Upload Product
   (drop-zone + disabled button), Recent Projects (empty state), AI
   Credits (shows "0 credits used"), Download History (empty state),
   Profile (your avatar, name, email, "Google account" badge, join date)
9. Resize to phone width — Navbar collapses to a hamburger menu, the
   dashboard sidebar becomes a drawer + bottom nav bar, and the widget
   grid stacks to a single column
10. Sign out from the profile menu (top right) or the Profile widget's
    Sign out button → redirected to `/login`
11. Visit `/dashboard` directly while signed out → redirected to `/login`
    (route protection works)

Report back what breaks, if anything, and I'll fix it before moving on.

## Phase 2 Test

Run through this after filling in the four Cloudinary env vars:

1. On the dashboard's **Upload Product** card, drag a JPG/PNG/WebP onto
   the drop zone — a thumbnail preview and a progress bar appear
   immediately, then a green "Uploaded" badge
2. Click "View on Cloudinary" on an uploaded file — it opens the real
   image at a `res.cloudinary.com` URL
3. Click to browse instead of dragging — same result
4. Try uploading a `.pdf` or `.gif` — it's rejected inline with "Unsupported
   file type," no network request is made
5. Try uploading a file larger than 8MB — rejected inline with a
   "File is too large" message
6. Drag in 2–3 valid files at once — each gets its own row with its own
   progress bar, uploading independently
7. Click delete (trash icon) on a file **while it's still uploading** —
   the upload stops and the row disappears
8. Click delete on a file that finished uploading — it briefly shows
   "Deleting," then disappears; check Cloudinary's Media Library to
   confirm it's actually gone, not just hidden in the UI
9. Refresh the page — the upload list is empty again (expected: nothing
   is persisted yet, see "Not included yet" under Phase 2 above)
10. Resize to phone width — the widget and its file rows stay readable
    and don't overflow horizontally

Report back what breaks, and I'll fix it before we wire up Supabase
persistence and move on to Phase 3.

## Roadmap (next phases)

- **Phase 2 (in progress):** ~~Product image upload → Cloudinary~~ done;
  still to do: Supabase schema so uploads persist as real projects tied
  to a user
- **Phase 3:** AI Prompt Generator + Script Generator (OpenAI)
- **Phase 4:** Caption Generator + WhatsApp Copy + Hashtag Generator
- **Phase 5:** Download Assets (zip/export), polish, Kling API groundwork

## Brand colors

| Token | Hex |
|---|---|
| Primary | `#344CB7` |
| Secondary | `#577BC1` |
| Accent | `#0EA5E9` |
| Dark | `#000957` |

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#344CB7",
          secondary: "#577BC1",
          accent: "#0EA5E9",
          dark: "#000957",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #000957 0%, #344CB7 55%, #0EA5E9 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "fade-in-up": "fadeInUp 0.6s ease-out both",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# ------------------------------------------------------------------
# Offer For You - BNK AI Ad Studio
# Copy this file to .env.local and fill in real values.
# .env.local is git-ignored and must never be committed.
# ------------------------------------------------------------------

# --- Firebase Authentication (Phase 1 - required now) --------------
# Get these from Firebase Console > Project Settings > General > Your apps > Web app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# --- Supabase Database (Phase 2+ - reserved, not used yet) ---------
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# --- Cloudinary Storage (Phase 2 - required now for image upload) --
# Cloud name is not secret - it's used both in the browser (to upload
# directly to Cloudinary) and on the server (to delete assets).
# Get it from Cloudinary Console > Dashboard > "Cloud name".
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=
# An UNSIGNED upload preset - create it in Console > Settings > Upload >
# Upload presets. See the README's "Cloudinary Console Setup" section.
NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET=
# Server-only - used by the /api/uploads/delete route to remove assets.
# Never expose these with a NEXT_PUBLIC_ prefix.
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# --- OpenAI API (Phase 3+ - reserved, not used yet) -----------------
OPENAI_API_KEY=

# --- Kling API (future integration - reserved, not used yet) -------
KLING_API_KEY=

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# env files
.env
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
];

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#344CB7",
          secondary: "#577BC1",
          accent: "#0EA5E9",
          dark: "#000957",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #000957 0%, #344CB7 55%, #0EA5E9 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "fade-in-up": "fadeInUp 0.6s ease-out both",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# ------------------------------------------------------------------
# Offer For You - BNK AI Ad Studio
# Copy this file to .env.local and fill in real values.
# .env.local is git-ignored and must never be committed.
# ------------------------------------------------------------------

# --- Firebase Authentication (Phase 1 - required now) --------------
# Get these from Firebase Console > Project Settings > General > Your apps > Web app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# --- Supabase Database (Phase 2+ - reserved, not used yet) ---------
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# --- Cloudinary Storage (Phase 2+ - reserved, not used yet) --------
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# --- OpenAI API (Phase 3+ - reserved, not used yet) -----------------
OPENAI_API_KEY=

# --- Kling API (future integration - reserved, not used yet) -------
KLING_API_KEY=

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# env files
.env
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
];

export default eslintConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Cloudinary will host uploaded product images from Phase 2 onward.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com", // Google account profile photos
      },
    ],
  },
};

export default nextConfig;

{
  "name": "offer-for-you",
  "version": "0.1.0",
  "private": true,
  "description": "Offer For You - BNK AI Ad Studio. AI-powered affiliate advertisement asset generator.",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "firebase": "^11.1.0",
    "clsx": "^2.1.1"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.2",
    "@types/react-dom": "^19.0.2",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.5.0",
    "@eslint/eslintrc": "^3.2.0"
  },
  "engines": {
    "node": ">=18.18.0"
  }
}

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

# Offer For You — BNK AI Ad Studio (V1.0)

A SaaS platform where a user uploads a product image and AI generates a
full affiliate ad kit: prompts, video scripts, captions, WhatsApp copy,
hashtags, and downloadable assets.

This repo is being built **phase by phase**. Each phase is fully working
and testable on its own before the next one starts.

## Phase 1 — Auth & Dashboard (this delivery)

**Included:**
- Next.js 15 (App Router) + TypeScript + Tailwind CSS project scaffold
- Dark theme, mobile-first responsive UI, brand colors wired into Tailwind
- Premium marketing landing page at `/` — Hero, Features, How It Works,
  Pricing (Coming Soon), FAQ, Footer, with Login / Start Free CTAs
- Google Sign-In via Firebase Authentication
- Client-side protected `/dashboard` route (redirects to `/login` if signed out)
- Dashboard shell: sidebar (desktop) / drawer + bottom nav (mobile), topbar
  with profile menu and sign-out
- Placeholder cards for every V1.0 feature (Upload, Prompt Generator, Script
  Generator, Caption Generator, WhatsApp Copy, Hashtag Generator, Downloads)
  so the full product shape is visible from day one

**Not included yet** (later phases): image upload to Cloudinary, Supabase
persistence, OpenAI-powered generators, and asset downloads. Their env
vars are already reserved in `.env.local.example` so nothing has to be
restructured later.

## Tech stack

- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Firebase Authentication (Google provider)
- Supabase (Phase 2+), Cloudinary (Phase 2+), OpenAI API (Phase 3+), Kling API (future)

## Prerequisites

- Node.js 18.18+ (Node 20 LTS recommended)
- A Firebase project with the **Google** sign-in provider enabled

> Note: this project was authored in a sandboxed environment without
> package-registry access, so `npm install` / `npm run build` have not
> been run here. Please run them locally as the first test — see
> "Phase 1 Test" below.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Set up Firebase — see the full **Firebase Console Setup** walkthrough
   below if this is your first time; short version:
   - Build → Authentication → Sign-in method → enable **Google**
   - Project settings → General → "Your apps" → add a **Web app** →
     copy the `firebaseConfig` values
3. Copy the env template and fill it in:
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in the six `NEXT_PUBLIC_FIREBASE_*` values. Leave the Supabase /
   Cloudinary / OpenAI / Kling lines blank — they're reserved for later
   phases and unused right now.
4. Run the dev server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000
5. Click **Get started free** → **Continue with Google** → you should
   land on `/dashboard` signed in, and refreshing should keep you signed
   in (and redirect straight to `/dashboard` from `/`).

## Firebase Console Setup (step by step)

Everything here happens at https://console.firebase.google.com — no
billing account or credit card needed for Authentication.

**1. Create the project**
1. Click **Add project** (or **Create a project**).
2. Enter a project name, e.g. `offer-for-you`. Firebase suggests a unique
   project ID underneath — you can leave it as-is.
3. You'll be asked about Google Analytics — you can toggle it **off** for
   this project; it isn't needed for Authentication.
4. Click **Create project** and wait for it to finish provisioning.

**2. Enable the Google sign-in provider**
1. In the left sidebar, open **Build → Authentication**.
2. Click **Get started** (first time only).
3. Go to the **Sign-in method** tab.
4. Click **Google** in the provider list.
5. Toggle **Enable**.
6. Set a **Project public-facing name** (shown on the Google consent
   screen, e.g. "Offer For You") and a **Project support email** (pick
   your own email from the dropdown).
7. Click **Save**.

**3. Register a Web app and get your config**
1. Click the **gear icon → Project settings** in the left sidebar.
2. Scroll to **Your apps** and click the **`</>`** (Web) icon to add a
   web app.
3. Give it a nickname, e.g. `offer-for-you-web`. You do **not** need to
   check "Also set up Firebase Hosting."
4. Click **Register app**. Firebase shows a `firebaseConfig` object —
   copy the six values (`apiKey`, `authDomain`, `projectId`,
   `storageBucket`, `messagingSenderId`, `appId`) into your `.env.local`
   as the matching `NEXT_PUBLIC_FIREBASE_*` variables.
5. Click **Continue to console** — you can skip the SDK install
   instructions Firebase shows, since the `firebase` npm package is
   already in this project's `package.json`.

**4. Authorize the domains that will run this app**
1. Still in **Authentication**, go to the **Settings** tab → **Authorized
   domains**.
2. `localhost` is included by default, so local development works
   immediately.
3. When you deploy, add your deployed domain here too (e.g.
   `your-app.vercel.app`, and later your custom domain) — otherwise
   Google sign-in fails on that domain with `auth/unauthorized-domain`.

**5. Confirm it's wired up correctly**
1. In this project, copy `.env.local.example` to `.env.local` and paste
   in the six values from step 3.
2. Run `npm run dev`, open the app, and click **Start Free** or
   **Login → Continue with Google**.
3. A Google account-picker popup should appear. After choosing an
   account, you should land on `/dashboard` with your name, email and
   photo showing in the top-right menu.

**Common issues**
- **`auth/unauthorized-domain`** — the domain you're testing from isn't
  in Authorized domains (step 4).
- **Popup closes immediately / `auth/popup-blocked`** — your browser
  blocked the sign-in popup; allow popups for `localhost` and retry.
- **Sign-in button is disabled** — `.env.local` is missing or one of the
  six `NEXT_PUBLIC_FIREBASE_*` values is empty; check the browser
  console for the exact missing-key warning this project logs.

## Folder structure

```
src/
  app/
    layout.tsx          Root layout (fonts, dark theme, AuthProvider)
    page.tsx             Public landing page
    login/page.tsx        Google sign-in screen
    dashboard/
      layout.tsx          AuthGuard + DashboardShell wrapper
      page.tsx            Dashboard home (feature roadmap cards)
  components/
    ui/                  Button, Card, Icon — generic building blocks
    landing/             Navbar, Hero, Features, HowItWorks, Pricing, FAQ,
                          Footer, LandingPage (composes all of the above),
                          content.ts (all landing page copy)
    layout/              Sidebar, Topbar, MobileNav, DashboardShell
    auth/                GoogleSignInButton, AuthGuard, UserAvatar
  context/AuthContext.tsx Firebase auth state, exposed via useAuth()
  hooks/useAuth.ts
  lib/firebase/          client.ts (init) + auth.ts (sign-in/out helpers)
  config/brand.ts        Brand colors + the full V1.0 nav/feature map
  types/user.ts
```

## Deploy to Vercel

1. Push this project to a GitHub repo (Vercel deploys from git).
2. Go to https://vercel.com/new and import that repo.
3. Framework preset: Vercel auto-detects **Next.js** — leave build command
   as `next build` and output as default.
4. Before the first deploy, add environment variables under
   **Project Settings → Environment Variables** (copy every key from
   `.env.local.example` that you've filled in — at minimum the six
   `NEXT_PUBLIC_FIREBASE_*` values). Add them to all three environments
   (Production, Preview, Development).
5. Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL.
6. Back in the Firebase console → Authentication → Settings →
   **Authorized domains** → add your `*.vercel.app` domain (and your
   custom domain later) or Google sign-in will fail on the deployed site
   with an `auth/unauthorized-domain` error.
7. For later phases: once Cloudinary/Supabase/OpenAI keys exist, add them
   the same way before redeploying — no code changes needed, the env
   vars are already wired to be read from `process.env`.

Redeploying after future phases is automatic: every push to your main
branch triggers a new Vercel deployment.

## Phase 1 Test

Run through this after `npm install`:

1. `npm install` completes with no errors
2. `npm run build` completes with no type/lint errors
3. `npm run dev` → open `http://localhost:3000` and check the landing
   page: Navbar (Login / Start Free), Hero, Features, How It Works,
   Pricing (Coming Soon), FAQ accordion, Footer all render
4. Click each Navbar anchor link (Features / How it works / Pricing /
   FAQ) — page smooth-scrolls to that section
5. On Pricing, submit an email in "Notify me" — it shows a confirmation
   message (UI only for now; not yet wired to a real waitlist backend)
6. Click **Start Free** or **Login** → **Continue with Google** → lands
   on `/dashboard` signed in
7. Refresh `/dashboard` — session persists (no bounce to `/login`)
8. Resize to phone width — Navbar collapses to a hamburger menu, and once
   in the dashboard the sidebar becomes a drawer + bottom nav bar
9. Sign out from the profile menu (top right) → redirected to `/login`
10. Visit `/dashboard` directly while signed out → redirected to `/login`
    (route protection works)

Report back what breaks, if anything, and I'll fix it before Phase 2.

## Roadmap (next phases)

- **Phase 2:** Product image upload → Cloudinary storage, Supabase schema
  for users/products
- **Phase 3:** AI Prompt Generator + Script Generator (OpenAI)
- **Phase 4:** Caption Generator + WhatsApp Copy + Hashtag Generator
- **Phase 5:** Download Assets (zip/export), polish, Kling API groundwork

## Brand colors

| Token | Hex |
|---|---|
| Primary | `#344CB7` |
| Secondary | `#577BC1` |
| Accent | `#0EA5E9` |
| Dark | `#000957` |
[package.json](https://github.com/user-attachments/files/32349525/package.json)

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# env files
.env
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
];

export default eslintConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Cloudinary will host uploaded product images from Phase 2 onward.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com", // Google account profile photos
      },
    ],
  },
};

export default nextConfig;

{
  "name": "offer-for-you",
  "version": "0.1.0",
  "private": true,
  "description": "Offer For You - BNK AI Ad Studio. AI-powered affiliate advertisement asset generator.",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "firebase": "^11.1.0",
    "clsx": "^2.1.1"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.2",
    "@types/react-dom": "^19.0.2",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.5.0",
    "@eslint/eslintrc": "^3.2.0"
  },
  "engines": {
    "node": ">=18.18.0"
  }
}

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

# Offer For You — BNK AI Ad Studio (V1.0)

A SaaS platform where a user uploads a product image and AI generates a
full affiliate ad kit: prompts, video scripts, captions, WhatsApp copy,
hashtags, and downloadable assets.

This repo is being built **phase by phase**. Each phase is fully working
and testable on its own before the next one starts.

## Phase 1 — Auth & Dashboard (this delivery)

**Included:**
- Next.js 15 (App Router) + TypeScript + Tailwind CSS project scaffold
- Dark theme, mobile-first responsive UI, brand colors wired into Tailwind
- Google Sign-In via Firebase Authentication
- Client-side protected `/dashboard` route (redirects to `/login` if signed out)
- Dashboard shell: sidebar (desktop) / drawer + bottom nav (mobile), topbar
  with profile menu and sign-out
- Placeholder cards for every V1.0 feature (Upload, Prompt Generator, Script
  Generator, Caption Generator, WhatsApp Copy, Hashtag Generator, Downloads)
  so the full product shape is visible from day one

**Not included yet** (later phases): image upload to Cloudinary, Supabase
persistence, OpenAI-powered generators, and asset downloads. Their env
vars are already reserved in `.env.local.example` so nothing has to be
restructured later.

## Tech stack

- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Firebase Authentication (Google provider)
- Supabase (Phase 2+), Cloudinary (Phase 2+), OpenAI API (Phase 3+), Kling API (future)

## Prerequisites

- Node.js 18.18+ (Node 20 LTS recommended)
- A Firebase project with the **Google** sign-in provider enabled

> Note: this project was authored in a sandboxed environment without
> package-registry access, so `npm install` / `npm run build` have not
> been run here. Please run them locally as the first test — see
> "Phase 1 Test" below.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Create a Firebase project at https://console.firebase.google.com
   - Build → Authentication → Sign-in method → enable **Google**
   - Project settings → General → "Your apps" → add a **Web app** →
     copy the `firebaseConfig` values
3. Copy the env template and fill it in:
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in the six `NEXT_PUBLIC_FIREBASE_*` values. Leave the Supabase /
   Cloudinary / OpenAI / Kling lines blank — they're reserved for later
   phases and unused right now.
4. Run the dev server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000
5. Click **Get started free** → **Continue with Google** → you should
   land on `/dashboard` signed in, and refreshing should keep you signed
   in (and redirect straight to `/dashboard` from `/`).

## Folder structure

```
src/
  app/
    layout.tsx          Root layout (fonts, dark theme, AuthProvider)
    page.tsx             Public landing page
    login/page.tsx        Google sign-in screen
    dashboard/
      layout.tsx          AuthGuard + DashboardShell wrapper
      page.tsx            Dashboard home (feature roadmap cards)
  components/
    ui/                  Button, Card, Icon — generic building blocks
    layout/              Sidebar, Topbar, MobileNav, DashboardShell
    auth/                GoogleSignInButton, AuthGuard
  context/AuthContext.tsx Firebase auth state, exposed via useAuth()
  hooks/useAuth.ts
  lib/firebase/          client.ts (init) + auth.ts (sign-in/out helpers)
  config/brand.ts        Brand colors + the full V1.0 nav/feature map
  types/user.ts
```

## Deploy to Vercel

1. Push this project to a GitHub repo (Vercel deploys from git).
2. Go to https://vercel.com/new and import that repo.
3. Framework preset: Vercel auto-detects **Next.js** — leave build command
   as `next build` and output as default.
4. Before the first deploy, add environment variables under
   **Project Settings → Environment Variables** (copy every key from
   `.env.local.example` that you've filled in — at minimum the six
   `NEXT_PUBLIC_FIREBASE_*` values). Add them to all three environments
   (Production, Preview, Development).
5. Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL.
6. Back in the Firebase console → Authentication → Settings →
   **Authorized domains** → add your `*.vercel.app` domain (and your
   custom domain later) or Google sign-in will fail on the deployed site
   with an `auth/unauthorized-domain` error.
7. For later phases: once Cloudinary/Supabase/OpenAI keys exist, add them
   the same way before redeploying — no code changes needed, the env
   vars are already wired to be read from `process.env`.

Redeploying after future phases is automatic: every push to your main
branch triggers a new Vercel deployment.

## Phase 1 Test

Run through this after `npm install`:

1. `npm install` completes with no errors
2. `npm run build` completes with no type/lint errors
3. `npm run dev` → open `http://localhost:3000`, click **Get started
   free** → **Continue with Google** → lands on `/dashboard` signed in
4. Refresh `/dashboard` — session persists (no bounce to `/login`)
5. Resize to phone width — sidebar becomes a hamburger drawer + bottom
   nav bar; drawer opens/closes correctly
6. Sign out from the profile menu (top right) → redirected to `/login`
7. Visit `/dashboard` directly while signed out → redirected to `/login`
   (route protection works)

Report back what breaks, if anything, and I'll fix it before Phase 2.

## Roadmap (next phases)

- **Phase 2:** Product image upload → Cloudinary storage, Supabase schema
  for users/products
- **Phase 3:** AI Prompt Generator + Script Generator (OpenAI)
- **Phase 4:** Caption Generator + WhatsApp Copy + Hashtag Generator
- **Phase 5:** Download Assets (zip/export), polish, Kling API groundwork

## Brand colors

| Token | Hex |
|---|---|
| Primary | `#344CB7` |
| Secondary | `#577BC1` |
| Accent | `#0EA5E9` |
| Dark | `#000957` |

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#344CB7",
          secondary: "#577BC1",
          accent: "#0EA5E9",
          dark: "#000957",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #000957 0%, #344CB7 55%, #0EA5E9 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# ------------------------------------------------------------------
# Offer For You - BNK AI Ad Studio
# Copy this file to .env.local and fill in real values.
# .env.local is git-ignored and must never be committed.
# ------------------------------------------------------------------

# --- Firebase Authentication (Phase 1 - required now) --------------
# Get these from Firebase Console > Project Settings > General > Your apps > Web app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# --- Supabase Database (Phase 2+ - reserved, not used yet) ---------
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# --- Cloudinary Storage (Phase 2+ - reserved, not used yet) --------
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# --- OpenAI API (Phase 3+ - reserved, not used yet) -----------------
OPENAI_API_KEY=

# --- Kling API (future integration - reserved, not used yet) -------
KLING_API_KEY=

# ------------------------------------------------------------------
# Offer For You - BNK AI Ad Studio
# Copy this file to .env.local and fill in real values.
# .env.local is git-ignored and must never be committed.
# ------------------------------------------------------------------

# --- Firebase Authentication (Phase 1 - required now) --------------
# Get these from Firebase Console > Project Settings > General > Your apps > Web app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=

# --- Supabase Database (Phase 2+ - reserved, not used yet) ---------
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# --- Cloudinary Storage (Phase 2+ - reserved, not used yet) --------
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# --- OpenAI API (Phase 3+ - reserved, not used yet) -----------------
OPENAI_API_KEY=

# --- Kling API (future integration - reserved, not used yet) -------
KLING_API_KEY=

# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# env files
.env
.env*.local

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts

import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "out/**"],
  },
];

export default eslintConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    // Cloudinary will host uploaded product images from Phase 2 onward.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com", // Google account profile photos
      },
    ],
  },
};

export default nextConfig;

{
  "name": "offer-for-you",
  "version": "0.1.0",
  "private": true,
  "description": "Offer For You - BNK AI Ad Studio. AI-powered affiliate advertisement asset generator.",
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint ."
  },
  "dependencies": {
    "next": "^15.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "firebase": "^11.1.0",
    "clsx": "^2.1.1"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^22.10.2",
    "@types/react": "^19.0.2",
    "@types/react-dom": "^19.0.2",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.17.0",
    "eslint-config-next": "^15.5.0",
    "@eslint/eslintrc": "^3.2.0"
  },
  "engines": {
    "node": ">=18.18.0"
  }
}

/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

export default config;

# Offer For You — BNK AI Ad Studio (V1.0)

A SaaS platform where a user uploads a product image and AI generates a
full affiliate ad kit: prompts, video scripts, captions, WhatsApp copy,
hashtags, and downloadable assets.

This repo is being built **phase by phase**. Each phase is fully working
and testable on its own before the next one starts.

## Phase 1 — Auth & Dashboard (this delivery)

**Included:**
- Next.js 15 (App Router) + TypeScript + Tailwind CSS project scaffold
- Dark theme, mobile-first responsive UI, brand colors wired into Tailwind
- Premium marketing landing page at `/` — Hero, Features, How It Works,
  Pricing (Coming Soon), FAQ, Footer, with Login / Start Free CTAs
- Google Sign-In via Firebase Authentication
- Client-side protected `/dashboard` route (redirects to `/login` if signed out)
- Dashboard shell: sidebar (desktop) / drawer + bottom nav (mobile), topbar
  with profile menu and sign-out
- Placeholder cards for every V1.0 feature (Upload, Prompt Generator, Script
  Generator, Caption Generator, WhatsApp Copy, Hashtag Generator, Downloads)
  so the full product shape is visible from day one

**Not included yet** (later phases): image upload to Cloudinary, Supabase
persistence, OpenAI-powered generators, and asset downloads. Their env
vars are already reserved in `.env.local.example` so nothing has to be
restructured later.

## Tech stack

- Next.js 15 (App Router), TypeScript, Tailwind CSS
- Firebase Authentication (Google provider)
- Supabase (Phase 2+), Cloudinary (Phase 2+), OpenAI API (Phase 3+), Kling API (future)

## Prerequisites

- Node.js 18.18+ (Node 20 LTS recommended)
- A Firebase project with the **Google** sign-in provider enabled

> Note: this project was authored in a sandboxed environment without
> package-registry access, so `npm install` / `npm run build` have not
> been run here. Please run them locally as the first test — see
> "Phase 1 Test" below.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Create a Firebase project at https://console.firebase.google.com
   - Build → Authentication → Sign-in method → enable **Google**
   - Project settings → General → "Your apps" → add a **Web app** →
     copy the `firebaseConfig` values
3. Copy the env template and fill it in:
   ```bash
   cp .env.local.example .env.local
   ```
   Fill in the six `NEXT_PUBLIC_FIREBASE_*` values. Leave the Supabase /
   Cloudinary / OpenAI / Kling lines blank — they're reserved for later
   phases and unused right now.
4. Run the dev server:
   ```bash
   npm run dev
   ```
   Open http://localhost:3000
5. Click **Get started free** → **Continue with Google** → you should
   land on `/dashboard` signed in, and refreshing should keep you signed
   in (and redirect straight to `/dashboard` from `/`).

## Folder structure

```
src/
  app/
    layout.tsx          Root layout (fonts, dark theme, AuthProvider)
    page.tsx             Public landing page
    login/page.tsx        Google sign-in screen
    dashboard/
      layout.tsx          AuthGuard + DashboardShell wrapper
      page.tsx            Dashboard home (feature roadmap cards)
  components/
    ui/                  Button, Card, Icon — generic building blocks
    landing/             Navbar, Hero, Features, HowItWorks, Pricing, FAQ,
                          Footer, LandingPage (composes all of the above),
                          content.ts (all landing page copy)
    layout/              Sidebar, Topbar, MobileNav, DashboardShell
    auth/                GoogleSignInButton, AuthGuard
  context/AuthContext.tsx Firebase auth state, exposed via useAuth()
  hooks/useAuth.ts
  lib/firebase/          client.ts (init) + auth.ts (sign-in/out helpers)
  config/brand.ts        Brand colors + the full V1.0 nav/feature map
  types/user.ts
```

## Deploy to Vercel

1. Push this project to a GitHub repo (Vercel deploys from git).
2. Go to https://vercel.com/new and import that repo.
3. Framework preset: Vercel auto-detects **Next.js** — leave build command
   as `next build` and output as default.
4. Before the first deploy, add environment variables under
   **Project Settings → Environment Variables** (copy every key from
   `.env.local.example` that you've filled in — at minimum the six
   `NEXT_PUBLIC_FIREBASE_*` values). Add them to all three environments
   (Production, Preview, Development).
5. Click **Deploy**. Vercel builds and gives you a `*.vercel.app` URL.
6. Back in the Firebase console → Authentication → Settings →
   **Authorized domains** → add your `*.vercel.app` domain (and your
   custom domain later) or Google sign-in will fail on the deployed site
   with an `auth/unauthorized-domain` error.
7. For later phases: once Cloudinary/Supabase/OpenAI keys exist, add them
   the same way before redeploying — no code changes needed, the env
   vars are already wired to be read from `process.env`.

Redeploying after future phases is automatic: every push to your main
branch triggers a new Vercel deployment.

## Phase 1 Test

Run through this after `npm install`:

1. `npm install` completes with no errors
2. `npm run build` completes with no type/lint errors
3. `npm run dev` → open `http://localhost:3000` and check the landing
   page: Navbar (Login / Start Free), Hero, Features, How It Works,
   Pricing (Coming Soon), FAQ accordion, Footer all render
4. Click each Navbar anchor link (Features / How it works / Pricing /
   FAQ) — page smooth-scrolls to that section
5. On Pricing, submit an email in "Notify me" — it shows a confirmation
   message (UI only for now; not yet wired to a real waitlist backend)
6. Click **Start Free** or **Login** → **Continue with Google** → lands
   on `/dashboard` signed in
7. Refresh `/dashboard` — session persists (no bounce to `/login`)
8. Resize to phone width — Navbar collapses to a hamburger menu, and once
   in the dashboard the sidebar becomes a drawer + bottom nav bar
9. Sign out from the profile menu (top right) → redirected to `/login`
10. Visit `/dashboard` directly while signed out → redirected to `/login`
    (route protection works)

Report back what breaks, if anything, and I'll fix it before Phase 2.

## Roadmap (next phases)

- **Phase 2:** Product image upload → Cloudinary storage, Supabase schema
  for users/products
- **Phase 3:** AI Prompt Generator + Script Generator (OpenAI)
- **Phase 4:** Caption Generator + WhatsApp Copy + Hashtag Generator
- **Phase 5:** Download Assets (zip/export), polish, Kling API groundwork

## Brand colors

| Token | Hex |
|---|---|
| Primary | `#344CB7` |
| Secondary | `#577BC1` |
| Accent | `#0EA5E9` |
| Dark | `#000957` |

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#344CB7",
          secondary: "#577BC1",
          accent: "#0EA5E9",
          dark: "#000957",
        },
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #000957 0%, #344CB7 55%, #0EA5E9 100%)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-in-out",
        "fade-in-up": "fadeInUp 0.6s ease-out both",
        float: "float 6s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-12px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

export default eslintConfig;

[Uploading package.json…]()
[README.md](https://github.com/user-attachments/files/32349827/README.md)
