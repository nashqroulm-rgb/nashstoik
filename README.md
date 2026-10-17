# 🏛️ NASH STOIK & MINDSET (`@nashstoik`)

Autonomous multi-platform content pipeline for **Nash Stoik & Mindset** (`@nashstoik`), integrating **HyperFrames** vector animations with **Remotion** multi-track compositing.

---

## 🌟 Channel Overview
* **Handle:** `@nashstoik`
* **Niche:** Stoicisme Klasik, Logika, Ketahanan Mental (Mental Toughness), Disiplin Diri, dan Seni Menguasai Diri di Era Modern.
* **Email:** `nasheroulb@gmail.com`
* **Bio:** *"Logika, ketahanan mental, dan seni menguasai diri di tengah badai kehidupan modern."*

---

## ⚙️ Architecture: Dual-Engine Visual Production

```
                               ┌──────────────────────────────────────────────┐
                               │  Curriculum & Narrative Architecture         │
                               │  (content_packet_day_XXX.json)               │
                               └──────────────────────┬───────────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
         ┌───────────────────────────┐                                 ┌───────────────────────────┐
         │ HyperFrames Vector Core   │                                 │ Edge-TTS Audio Engine     │
         │ (GSAP / Dynamic SVG Compass)│                               │ (id-ID-ArdiNeural)        │
         └─────────────┬─────────────┘                                 └─────────────┬─────────────┘
                       │                                                             │
                       └──────────────────────────────┬──────────────────────────────┘
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │ Remotion Compositor Engine  │
                                       │ (Aesthetic Dark Vignette,   │
                                       │  Kinetic Impact Subtitles,  │
                                       │  Branded Header & Outro)    │
                                       └──────────────┬──────────────┘
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │ FFmpeg Pre-Upload Compress  │
                                       │ (< 3.8 MB Payload Guard)    │
                                       └──────────────┬──────────────┘
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │ Multi-Platform Publisher    │
                                       │ (TikTok, Instagram, YouTube)│
                                       └─────────────────────────────┘
```

---

## 🚀 Quick Start & CLI Commands

```bash
# 1. Synthesize Audio
python scripts/generate-voiceover.py

# 2. Render HyperFrames Vector Scene
npx hyperframes render -c "hyperframes_scenes/scenes/scene_dichotomy_compass.html" -o "public/hyperframes_dichotomy_compass.mp4" --fps 24 --low-memory-mode

# 3. Render Remotion Master Video
npx tsx scripts/render-video.ts --day 1

# 4. Check Platform Integration Status
python scripts/publish.py status
```

---

## 🏛️ Sovereign Fleet Standards
* **1 Channel = 1 Sovereign Codebase**
* **Sacred Subtitle Zone:** y=1350 to 1920 strictly preserved for kinetic subtitles.
* **Payload Invariant:** Every published vertical video is hardware-compressed to `< 3.8 MB` to ensure zero HTTP 413 rejections on serverless gateways (Zernio).
