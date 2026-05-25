# vocut

> Voiceover-first long-form video editor.
> 配音稿驱动的长视频剪辑工具，专为知识博主而生。

**Status**: 🌱 Pre-alpha · 设计阶段 · 不可用

---

## What it does

Give vocut your voiceover script + a folder of footage clips. It will:

1. Index the footage library (Whisper transcription + visual tagging)
2. Match each script sentence to the best clip via semantic search + LLM rerank
3. Fill the gaps with **Claude design**-style code-driven motion graphics
4. Render the final video — captions, transitions, everything baked in

**Designed for**: voiceover-first knowledge creators (financial / tech / history / philosophy YouTubers and bilibili UPs) who spend 4-8 hours per video manually pairing their script with B-roll.

**Not designed for**: vloggers, livestreamers, gaming highlight makers.

---

## Pipeline (planned)

```
voiceover.md + ./footage/*.mp4
        │
        ├─ Whisper transcribe footage
        ├─ Vision LLM tag visuals  
        ├─ Embed → sqlite-vss index
        │
        ▼
   plan.json (sentence ↔ clip alignment, with confidence scores)
        │
        ├─ auto-editor pre-clean (silence/filler removal)
        ├─ ffmpeg + moviepy assemble footage segments
        ├─ Remotion render motion-graphic overlays
        │
        ▼
     output.mp4
```

---

## Stack

| Layer | Choice | License |
|---|---|---|
| Transcription | Whisper / faster-whisper | MIT |
| Embedding | bge-m3 | MIT |
| Vector store | sqlite-vss | MIT |
| Auto-clean | WyattBlue/auto-editor | Unlicense |
| Composition | moviepy + FFmpeg | MIT + LGPL |
| Motion graphics | Remotion | Custom (free for individuals) |
| LLM rerank | Claude API (default) | Commercial |

---

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| **P0** | Dogfood — produce one real 15min+ video using the tool | 🔨 In progress |
| **P1** | Production polish + 10-15 motion graphic components | – |
| **P2** | Public release on GitHub + simple read-only web UI | – |
| **P3** | Community-driven component library + bilingual docs | – |

Full roadmap and competitive research lives in `docs/research/` (linked from outside this repo for now).

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Acknowledgements

vocut would not exist without these projects:

- [Remotion](https://github.com/remotion-dev/remotion) — React-based programmatic video
- [auto-editor](https://github.com/WyattBlue/auto-editor) — silence / filler removal
- [moviepy](https://github.com/Zulko/moviepy) — Python video composition
- [Whisper](https://github.com/openai/whisper) — speech-to-text
- [Motion Canvas](https://github.com/motion-canvas/motion-canvas) — animation aesthetic inspiration

Special inspiration credit to [OpenMontage](https://github.com/calesthio/OpenMontage) for pioneering the agent-driven video production pipeline (we re-implement the ideas under MIT to stay license-compatible with the open ecosystem).
