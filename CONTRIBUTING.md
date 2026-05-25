# Contributing to vocut

Thanks for the interest! vocut is in pre-alpha — the alignment algorithm and motion-graphic library are still settling. This guide gets thinner over time as the project stabilizes.

---

## Before you contribute

**vocut has a deliberately narrow scope.** Please read [ROADMAP.md § Out of scope](./docs/ROADMAP.md#out-of-scope-do-not-propose-features-for-these) first.

Things we **welcome**:
- New motion-graphic components (e.g. `chapter_outro`, `timeline_point`, `data_chart`)
- Bug fixes
- Alignment algorithm improvements (prompts, rerank strategies, threshold tuning)
- Documentation in additional languages
- Performance optimizations
- Test cases on new content domains

Things we **probably won't merge** (no judgment — just different products):
- Footage scraping / download
- AIGC video generation
- Cloud / SaaS features
- A GUI editor (we may add a read-only preview in P2, nothing more)
- Account systems

If unsure, open an issue with `[discussion]` before writing code.

---

## Dev setup

```bash
git clone https://github.com/akiliu38843-home/vocut.git
cd vocut
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Required system tools:
- `ffmpeg` (`brew install ffmpeg` on macOS)
- `node` ≥ 20 (for Remotion side, installed via npm in `components/` once that side exists)

---

## Running tests

```bash
pytest
```

When you add a new component or pipeline change, please include at least one test that runs end-to-end on a tiny fixture (a 10-second mp3 + 2 short mp4 clips). Pre-baked fixtures live in `tests/fixtures/`.

---

## Proposing a new motion-graphic component

Components live in `components/src/components/<name>.tsx` (Remotion side). The contract:

```typescript
type ComponentProps = {
  /* required: durationFrames + fps from Remotion */
  /* component-specific: define in TypeScript */
}
```

To propose a new component:

1. Open an issue with `[component] <name>` — describe the trigger condition (which kind of sentence should select this component) and a small visual mockup or reference (a screenshot from Anthropic / Linear / Vercel works).
2. Wait for ack from a maintainer (we may already have a similar component planned).
3. Implement the component + register its trigger rule in `src/vocut/planner/triggers.py`.
4. Add a regression test using a sample sentence.
5. Open PR.

We aim to keep the component library **opinionated and small** — minimalist editorial aesthetic, no neon, no 3D, no shader-heavy effects. If your component needs more than vanilla CSS animations + Remotion built-ins, propose it but expect pushback.

---

## Commit convention

Lightweight conventional commits:

```
feat: add comparison_panel three-way variant
fix: handle empty footage library
docs: update P0 milestone list
refactor: extract embedding interface
test: cover hybrid plan rendering
chore: bump dependency versions
```

PR titles should follow the same shape.

---

## License consent

By contributing, you agree your changes are licensed under MIT (same as the project). You retain copyright on your contributions; the MIT license grants vocut and downstream users perpetual rights to your code.

If your employer holds rights to your work, please confirm with them before contributing.

---

## Code of conduct

Be kind. Be specific. Disagree about ideas, not people. The maintainer reserves the right to remove comments or block users that make the project unpleasant for others. There is no formal CoC document yet; if vocut grows to where one is needed, we'll adopt Contributor Covenant.

---

## Getting help

- Open an issue: https://github.com/akiliu38843-home/vocut/issues
- Discussion: not yet enabled — for now, issues are the only channel.
