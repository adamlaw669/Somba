# SOMBA — THE FILM

A cinematic, browser-native motion explainer for **Somba** (Nomba × DevCareer
2026, Team SetId). One HTML page that plays like a video — no render step, no
video file, fully offline-capable except Google Fonts.

## Play it

Open `index.html` in Chrome/Edge (double-click works — everything is local):

```bash
start pitch-video/index.html
```

Press **PLAY FILM** (this also unlocks the audio engine), then hit `F` for
fullscreen.

| Key | Action |
|---|---|
| `Space` | play / pause |
| `F` | fullscreen |
| `M` | music on / off |
| `←` / `→` | skip 5 s |

The scrub bar at the bottom has a tick at every scene boundary — click to seek.

## What's inside

- **`index.html` / `style.css` / `video.js`** — ten scenes on one anime.js
  master timeline (3:26), scaled 1920×1080 stage, a unique transition per cut:
  iris flood, hazard-strip wipe, full-stage 3D flip, rolling-coin shove,
  shutter slats, stamp slam, diagonal squeegee, flash phone-zoom, hazard doors.
- **`music.js`** — generative Web-Audio soundtrack (112 BPM, A minor): kick,
  hats, clap, sub bass, pads, delayed arps, sidechain pump. Intensity follows
  the story scene-by-scene; risers, impacts and success dings are cued to the
  cuts. No audio files.
- **`assets/`** — anime.js + six 3D renders (gpt-image-1-mini, black/yellow
  brand palette): naira coin, credit card, vault, money bag, alarm clock,
  check shield.
- **`SCRIPT.md`** — timestamped voiceover script to read alongside.

## Design

Palette from the pitch deck: black `#0a0a0a` · yellow `#FFC907` · white.
Type: **Unbounded** (display), **Space Grotesk** (body), **JetBrains Mono**
(data) — deliberately punchier than the deck's system font. Film grain +
vignette overlay, deck motifs (squiggle strokes, collage tiles with hard
offset shadows) carried through.

Competitor marks (Paystack, Flutterwave, Stripe, Remita) are simplified
inline-SVG/wordmark approximations used nominatively in the comparison scene.
