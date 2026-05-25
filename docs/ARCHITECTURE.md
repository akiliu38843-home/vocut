# vocut Architecture

> Pipeline shape, data contracts, and key design decisions. Read [ROADMAP.md](./ROADMAP.md) first for the product context.

---

## Pipeline

```
                          ┌─────────────────────────┐
                          │       USER INPUT        │
                          │  voiceover.md           │
                          │  ./footage/*.mp4        │
                          └─────────────┬───────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
                ▼                       ▼                       ▼
       ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
       │ vocut index    │      │ vocut plan     │      │ vocut render   │
       │ ──────────────  │      │ ──────────────  │      │ ──────────────  │
       │ Whisper        │      │ Embed sentence │      │ auto-editor    │
       │  transcribe    │ ───▶ │ Vector search  │ ───▶ │  pre-clean     │
       │ Vision LLM     │      │  top-k clips   │      │ moviepy        │
       │  tag visuals   │      │ Claude rerank  │      │  cut + concat  │
       │ Embed text     │      │  → confidence  │      │ Remotion       │
       │ sqlite-vss     │      │ Motion-graphic │      │  render mg     │
       │  store         │      │  fallback if   │      │ ffmpeg         │
       │                │      │  conf < 0.6    │      │  composite     │
       └────────────────┘      └────────────────┘      └────────────────┘
                │                       │                       │
                ▼                       ▼                       ▼
       footage_index.db            plan.json              output.mp4
       (sqlite + vss)              (sentence ↔ slot)
```

---

## Data contracts

### Footage index entry (one row in sqlite per clip segment)

```json
{
  "clip_id": "uuid",
  "source_file": "interview_2024_03.mp4",
  "start_sec": 12.5,
  "end_sec": 28.7,
  "transcript": "...so the question really is about agency...",
  "visual_tags": ["interview", "indoor", "single-person", "talking-head"],
  "scene_description": "Wide shot of a person in a library setting, talking to camera",
  "embedding_vector": [/* 1024-dim float32 */]
}
```

### `plan.json` schema (the central artifact)

```jsonc
{
  "meta": {
    "script_path": "voiceover.md",
    "library_path": "./footage/",
    "vocut_version": "0.0.1",
    "generated_at": "2026-05-25T10:00:00Z",
    "confidence_threshold": 0.6
  },
  "plan": [
    // Type 1: footage-driven
    {
      "sentence_idx": 1,
      "sentence": "...",
      "duration_estimate_sec": 5.2,
      "match": {
        "type": "footage",
        "clip_id": "uuid",
        "source_file": "interview.mp4",
        "start_sec": 12.5,
        "end_sec": 17.7,
        "confidence": 0.85,
        "reasoning": "interview close-up matches abstract concept of agency"
      }
    },
    // Type 2: motion-graphic-only
    {
      "sentence_idx": 2,
      "sentence": "...",
      "duration_estimate_sec": 4.0,
      "match": {
        "type": "motion_graphic",
        "component": "key_number",
        "props": {"primary": "4.2亿", "unit": "美元", "label": "Q1 2026"},
        "confidence": 0.92,
        "reasoning": "specific financial figure"
      }
    },
    // Type 3: hybrid (footage + overlay)
    {
      "sentence_idx": 3,
      "sentence": "...",
      "duration_estimate_sec": 6.0,
      "match": {
        "type": "hybrid",
        "primary": {
          "type": "footage",
          "clip_id": "uuid",
          "confidence": 0.85
        },
        "overlay": {
          "type": "motion_graphic",
          "component": "pull_quote",
          "props": {"quote": "人永远是目的", "attribution": "—— 康德"}
        }
      }
    }
  ]
}
```

`plan.json` is the **front-end / back-end contract**. Index and plan know nothing about render; render knows nothing about LLMs. You can hand-edit `plan.json` and re-render — this is a feature, not a leak.

---

## Stack rationale

| Layer | Choice | Why this, not alternatives |
|---|---|---|
| Transcription | faster-whisper (default) | Speed > accuracy for footage indexing. OpenAI Whisper API as opt-in. |
| Embedding | bge-m3 | Best Chinese+English bilingual model under MIT. Falls back to OpenAI `text-embedding-3-small` if not available. |
| Vector store | sqlite-vss | Local, zero-config, no server. Chroma / LanceDB add complexity without P0 benefit. |
| LLM rerank | Claude (default) | Best instruction-following in 2026-05; user can swap via `--llm-provider`. |
| Visual tagging | Claude vision | Single API call per sampled frame; can swap for local CLIP+caption in P2. |
| Pre-clean | WyattBlue/auto-editor | Battle-tested silence/filler removal; outputs OTIO/EDL we can re-import. |
| Composition | moviepy + ffmpeg | moviepy for clarity, ffmpeg directly for performance-critical paths. |
| Motion graphics | Remotion + Chromium | React components, frame-exact rendering, vast npm ecosystem. |

Full competitor analysis with stars / licenses / activity: see `docs/research/` (also linked from README).

---

## Key design decisions

### D1: Voiceover is the single source of truth

The user edits `voiceover.md`. They never edit a timeline. When the script changes, `vocut plan` is re-derived. There is no "timeline view"; the script IS the timeline.

**Implication**: incremental render must operate at sentence granularity. P1 milestone.

### D2: Motion graphics fill structural gaps, not decorate

When `vocut plan` cannot find a clip with confidence ≥ 0.6, it does NOT leave a hole. It picks a motion-graphic component appropriate to the sentence's semantic shape (number → `key_number`, quote → `pull_quote`, etc.). PoC v1 + v2 confirmed this happens for 40–60% of sentences in real content. This is the design, not a fallback.

### D3: Hybrid mode (footage + overlay) is P0, not P1

PoC v2 showed 32% of sentences in data-rich content (gaming, finance, history) want footage AND a motion-graphic overlay (clip showing the scene + key_number with the actual statistic). Without hybrid, knowledge content with concrete data feels visually flat.

`plan.json` schema supports `type: "hybrid"`. Render must support two-layer compositing (footage base + motion-graphic overlay with transparency).

### D4: One plan, one render, deterministic

Same `plan.json` + same footage + same component versions → identical output. This makes incremental render trustworthy: if a sentence didn't change, neither did its rendered segment, so we cache.

### D5: Components are React, animations are code

No After Effects, no Lottie, no AI image generation. Every motion graphic is a Remotion React component with explicit props. This means:
- ✅ Reproducible across runs
- ✅ Versionable in git
- ✅ Style updates propagate atomically
- ❌ Visual quality bounded by what we can write in React + CSS (intentional ceiling — keeps the aesthetic coherent)

---

## What's *not* in the architecture (and why)

- **No fetching layer** — vocut does not download footage. Users use yt-dlp / browser extensions / their own cameras. Reduces legal surface and scope creep.
- **No cloud storage** — everything is local. We assume `./footage/` lives on the user's machine.
- **No user accounts** — self-hosted, no auth, no profiles. The maintainer of the running instance owns the data.
- **No realtime collaboration** — single creator, single workstation. P1+ may add file-based merge, but not before.
- **No browser-rendered preview during edit** — user iterates on `voiceover.md` in their editor, runs `vocut render --preview` if they want a fast low-quality render. We don't build a web UI in P0/P1.

---

## Known limitations (P0)

- **Embedding is Chinese-optimized by default.** The default `BAAI/bge-small-zh-v1.5` model performs poorly on cross-language matching (e.g. Chinese voiceover + English B-roll). Workaround for now: `export VOCUT_EMBED_MODEL=BAAI/bge-m3` before running `vocut index` to use the multilingual model (2.3 GB). P1 will make `bge-m3` the default once we've validated quality on real bilingual content. Whisper transcription itself already supports 99 languages out of the box.
- **Footage with audio-only sources renders as a black video.** WAV / MP3 segments produce no visual frame in the rough cut. This is intentional for the dogfood phase (gives a duration anchor); real productions should use video sources.
- **Motion-graphic placeholders are Pillow-drawn text cards.** Real Claude-design Remotion components land in P0.3.
- **No voiceover-to-sentence timing alignment yet.** `--voiceover` simply overlays the audio onto the concatenated visuals; the visual timing follows clip duration + a fixed card duration, not the voiceover. Aligned timing is P1.

## Performance targets (P0 dogfood)

| Stage | Target on M1/M2 16GB |
|---|---|
| Index 1h of footage | < 10 min (one-time, cached) |
| Plan a 15min script (~150 sentences) | < 2 min |
| Render 15min final mp4 (no preview pass) | < 1h |
| Incremental render (10% of sentences changed) | < 6 min |

Misses on these targets are P1 optimization tasks, not P0 blockers — as long as the dogfood video gets produced.
