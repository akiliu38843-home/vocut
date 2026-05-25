# vocut Roadmap

> **Status**: Pre-alpha · Pre-P0 · Design complete, code not yet started.
> **Orientation**: 100% open source · MIT · self-hosted only · no SaaS planned.

This roadmap is grounded in:
- A 12-project [open-source competitor analysis](./research/) (Remotion / Motion Canvas / auto-editor / OpenMontage / Descript / ...)
- Two cross-domain [PoC alignments](./research/) (philosophy script + gaming/anime script) that validated the core algorithm

---

## Vision

**One thing well**: give a knowledge creator their voiceover script + a folder of footage clips, return a 15min+ rough cut they can publish or fine-tune in any NLE.

**Why this matters**: voiceover-first creators (financial, tech, history, philosophy, gaming-analysis bloggers) spend 4–8 hours per video manually pairing script to B-roll. Existing tools either target short-form virality (Opus Clip / Submagic) or are general-purpose NLEs (Descript / Premiere). Nobody serves long-form-driven-by-script + code-aesthetic motion graphics.

**For** voiceover-first knowledge creators
**Not for** vloggers, livestream clippers, gaming highlight makers, talking-head interviewers

---

## Core design principles (locked)

1. **Voiceover is the single source of truth** — users edit the script, not a timeline. The script-to-clip mapping is derived, not authored.
2. **Motion graphics are a structural substitute for footage, not decoration** — when no clip semantically matches a sentence, an animated component fills the slot. Visual coverage is a system goal, not a creator burden.
3. **CLI first, no UI in P0** — UX investment doesn't earn its keep until the alignment algorithm proves itself.
4. **Self-host only, no hosted SaaS** — the maintainer cost of running a SaaS for an OSS tool is not justified. Users run vocut on their own machines.
5. **Footage acquisition is a thin yt-dlp wrapper, not a scraping engine** — `vocut fetch` lets users download via yt-dlp's battle-tested extractors (Optional dep, `pip install vocut[fetch]`). vocut itself does not maintain platform-specific extractors, AIGC generation, or any scraping cleverness — yt-dlp owns that domain. Users remain responsible for copyright / fair-use compliance.

---

## Pipeline (planned)

```
voiceover.md + ./footage/*.mp4
        │
        ▼
   ┌──────────────┐    Whisper + visual tagging + embeddings → sqlite-vss
   │ vocut index  │
   └──────────────┘
        │
        ▼
   ┌──────────────┐    semantic search + Claude rerank → confidence ≥ 0.6
   │ vocut plan   │    confidence < 0.6 → motion-graphic fallback
   └──────────────┘
        │
        ▼
     plan.json
        │
        ▼
   ┌──────────────┐    auto-editor pre-clean + moviepy assemble
   │ vocut render │  + Remotion render motion-graphic overlays
   └──────────────┘  + ffmpeg composite (footage layer + overlay layer)
        │
        ▼
     output.mp4
```

Full technical detail: [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Phases

### P0 — Dogfood (4–6 weeks)

> **Gate**: the maintainer produces ONE real 15min+ knowledge video using vocut end-to-end, and is satisfied with the output quality.

| Milestone | Deliverable |
|---|---|
| P0.1 | `vocut index ./footage/` — transcribes, embeds into local sqlite ✓ |
| P0.1.5 | `vocut fetch <url\|file>` — thin yt-dlp wrapper, idempotent ✓ |
| P0.2 | `vocut plan script.md` — emits `plan.json` (Claude rerank + heuristic fallback) ✓ |
| P0.3 | 5 motion-graphic components: `key_number` / `pull_quote` / `title_card` / `comparison_panel` / `list_item` |
| P0.4 | `vocut render plan.json` — produces final mp4 with caption burn-in |
| P0.5 | Maintainer dogfoods a real 15min video |

**P0 absolutely must include** (revised based on PoC findings):

- **Hybrid mode** — footage clip + motion-graphic overlay on the same segment. PoC v2 (gaming/anime) showed 32% of segments need this. Not optional, not P1.
- **`comparison_panel` as a P0 component** — most-used motion graphic across both PoCs (4× each).
- **`key_number` with 4 variants**: single value / value + unit / value + secondary / date-style / version-style. PoC v2 used `key_number` 10× across many formats.

### P1 — Production polish (4–8 weeks after P0)

> **Gate**: maintainer produces a 2nd and 3rd video without modifying tool code. Tool is stable enough to use.

- Incremental render (changed-sentence-only)
- Motion-graphic library expanded to 12–15 components, each with 2–3 style variants
- Chapter-aware rendering (Markdown headings → chapter cards)
- Caption style presets (minimalist / TED-style / keyword-highlight)
- Polished CLI UX (`init` / `index` / `plan` / `render` / `dev` watch mode)

### P2 — Public release (1+ month after P1)

> **Gate**: 100★ within one month of public announcement + 5 external users reporting successful end-to-end runs.

- One-line install (`pip install` + brew tap or docker image)
- README that achieves "first impression → trial" in under 5 minutes
- Bilingual docs (English + 简体中文)
- Example gallery: 3+ demo videos with open-sourced scripts and footage references
- GitHub Actions CI for tests and lint

### P3 — Community (continuous after P2)

> **Gate**: 3+ external creators publish videos that organically mention vocut as their tool.

- Component library extraction: `@vocut/components` published to npm separately
- CONTRIBUTING flow for community-submitted motion graphics
- Featured monthly community components in the main release
- Optional `--export-jianying` flag (CapCut/剪映 draft export, see [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft))

### P4 — Sustainability (not commercialization)

vocut does not have a P4 commercialization phase. If the project gains a user base, sustainable funding options to consider:

- GitHub Sponsors / 爱发电 for individual maintainers
- One-time consulting engagements (e.g. integrating vocut into an educational publisher's workflow)
- Optional cloud-render add-on by a third party (vocut itself stays self-host)

**Not planned**: paid features, paid components, paid SaaS, dual-licensing.

---

## Success metrics (OSS)

| Metric | P2 target | P3 target |
|---|---:|---:|
| GitHub stars | 100 | 1,000 |
| External contributors | 1 | 10 |
| Confirmed end-to-end runs by non-maintainer | 5 | 50 |
| Community-submitted motion graphics merged | 0 | 5 |
| README in supported languages | 2 | 3 |

Star count is a noisy metric. The truer signal is **external creators publishing videos that mention vocut**, because that requires the tool to actually work for someone other than the maintainer.

---

## Risk monitor

| Risk | Trigger | Response |
|---|---|---|
| Voiceover-driven alignment accuracy < 60% on real data | P0.5 dogfood | Lower confidence threshold + bias toward motion-graphic fallback |
| 15min+ render time > 2h on M1/M2 | P0.4 measurement | Chapter-based render queue with overnight job support |
| Motion graphics aesthetically off | Maintainer dogfood dissatisfaction | One-shot visual design consultation (paid or community) |
| Remotion license terms change | Official announcement | Fork at last permissive version, freeze upstream |
| OpenMontage relicenses to MIT | Repo file change | Reevaluate — may switch some pipeline modules to depend directly |
| Descript ships "long-form knowledge mode" | Their changelog | Accelerate P3 bilingual + 剪映 export differentiation |

---

## Open questions (resolved during P0 dogfood)

These influence P1+ design and will be answered as the maintainer uses the tool on real content:

1. Markdown script format vs plain text — which feels natural after 3 videos?
2. Typical footage library size — 30 clips? 300? Affects index strategy.
3. Anthropic Claude vs OpenAI GPT-4o vs local LLM for the rerank — quality vs cost tradeoff.
4. Whisper local vs OpenAI API — speed vs cost vs privacy.

---

## Out of scope (do not propose features for these)

- Maintaining platform-specific scrapers (we wrap yt-dlp; we don't fix YouTube extractor regressions ourselves)
- AIGC video generation (text-to-video models)
- Live streaming overlays
- Multi-creator collaboration
- Account systems / cloud profiles
- Mobile app
- Avatar generation / lip sync
- Short-form (< 5 min) optimization

- Automatic footage download (handled by `vocut fetch` as a thin yt-dlp wrapper; we don't build extractors)

Each of these is a different product. vocut is one product, one purpose.
