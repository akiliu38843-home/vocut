# vocut

> Voiceover-first long-form video editor.
> 配音稿驱动的长视频剪辑工具，专为知识博主而生。

**Status**: 🌱 Pre-alpha · 设计阶段 · 不可用

---

## What it does

Give vocut your voiceover script + a folder of footage clips (or a list of URLs).
It will:

1. (Optional) Download footage from YouTube / Bilibili / etc. via yt-dlp
2. Index the footage library (Whisper transcription + visual tagging)
3. Match each script sentence to the best clip via semantic search + LLM rerank
4. Fill the gaps with **Claude design**-style code-driven motion graphics
5. Render the final video — captions, transitions, everything baked in

**Designed for**: voiceover-first knowledge creators (financial / tech / history / philosophy YouTubers and bilibili UPs) who spend 4-8 hours per video manually pairing their script with B-roll.

**Not designed for**: vloggers, livestreamers, gaming highlight makers.

---

## Pipeline (planned)

```
voiceover.md  +  urls.txt (optional)
                       │
                       ▼
                vocut fetch         ← P0.1.5 ✓ (yt-dlp thin wrapper)
                       │
                       ▼
                ./footage/*.mp4
                       │
                       ▼
                vocut index         ← P0.1 ✓
                  ├─ Whisper transcribe
                  ├─ embed (bge-small-zh-v1.5)
                  └─ sqlite store
                       │
                       ▼
                footage.db
                       │
                       ▼
                vocut plan          ← P0.2 ✓ (heuristic + Claude rerank)
                       │
                       ▼
                plan.json
                       │
                       ▼
                vocut render        ← P0.4 (todo)
                  ├─ auto-editor pre-clean
                  ├─ moviepy / ffmpeg assemble
                  └─ Remotion motion graphics
                       │
                       ▼
                output.mp4
```

---

## Stack

| Layer | Choice | License |
|---|---|---|
| Footage fetch (optional) | yt-dlp | Unlicense |
| ffmpeg binary | imageio-ffmpeg (bundled, cross-platform) | BSD-2-Clause |
| Transcription | faster-whisper | MIT |
| Embedding | sentence-transformers (default: bge-small-zh-v1.5) | MIT |
| Vector store | sqlite (raw bytes BLOBs in P0; sqlite-vec in P1) | public domain / MIT |
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
