# Quickstart — end-to-end in 5 minutes

A self-contained demo that exercises vocut's whole pipeline:

```
script.md  +  ./footage/*.mp4   ─►   vocut index  ─►   vocut plan  ─►   vocut render  ─►   output.mp4
```

The 5 footage clips are **synthesized on the fly** (`say` TTS + ffmpeg colored
cards) so there are no binaries committed to the repo and you can re-run
deterministically. Each clip's theme deliberately aligns with one paragraph of
`script.md` so the matching step's quality is visible at a glance.

---

## What you need

- **macOS** (uses the built-in `say` command for TTS).
  Linux users — see "Cross-platform note" at the bottom.
- **vocut installed** in your active Python env:
  ```bash
  pip install vocut
  # or, working from a clone:
  pip install -e /path/to/vocut
  ```
- **LLM credentials**. Pick one:
  - OpenAI-compatible (recommended, supports custom base URL):
    ```bash
    export VOCUT_LLM_BASE_URL="https://api.openai.com/v1"   # or any compat endpoint
    export VOCUT_LLM_API_KEY="sk-..."
    ```
  - OpenAI proper: `export OPENAI_API_KEY=sk-...`
  - Anthropic: `export ANTHROPIC_API_KEY=sk-ant-...`

`vocut plan` auto-detects which is set and picks a reasonable default model.

---

## Run

```bash
cd examples/quickstart
./run.sh
```

`run.sh` does six things in sequence: generate footage → generate voiceover →
index → plan → render → open the result. Each step is idempotent; re-running
after success is a no-op unless you delete the intermediate files.

Expected wall time on first run: **2–4 minutes** (the longest piece is
Whisper + bge-small-zh model download on first `vocut index`). Subsequent runs
are ~30 s.

---

## What success looks like

A 45-second 1280×720 mp4 (`output.mp4`) where each spoken sentence visually
matches the corresponding colored card:

| Voiceover sentence | Card you should see |
|---|---|
| "今年全球数据总量将达到 175 ZB…"   | 蓝底 "数据规模" |
| "苹果和谷歌在 AI 战略上走出了两条完全不同的路。" | 红底 "战略对比" |
| "接下来一年最值得关注的有三个趋势…" | 绿底 "三大趋势" |
| "AI 不会取代人，但用 AI 的人会取代不用 AI 的人。" | 黑底 "金句引用" |
| "这家只有二十个人的初创团队…"     | 紫底 "真实案例" |

Inspect `plan.json` to see the underlying decisions — each script sentence
carries a `match` block with `source_file`, `confidence`, and the LLM's
reasoning. On our reference run mean confidence was **0.92**.

---

## Run the steps individually

Each step is a standalone script so you can poke at intermediate state.

```bash
./make_footage.sh           # ./footage/01..05.mp4
./make_voiceover.sh         # ./voiceover.wav
vocut index ./footage/      # ./.vocut_index/footage.db
vocut plan ./script.md      # ./plan.json
vocut render ./plan.json --voiceover ./voiceover.wav   # ./output.mp4
```

Delete `./footage/`, `./voiceover.wav`, `./.vocut_index/`, `./plan.json`,
`./output.mp4` to reset and start from a clean state.

---

## Gotchas we hit while building this

These are noted here so you don't waste time on them.

- **macOS `say` pronounces "AI" like "ai-ai"** — Whisper `base` often
  transcribes it as "阿姨". Doesn't break matching (the LLM rerank still
  picks the right clip from semantic context), but the transcripts in
  `plan.json` will look funny. Workarounds: use Whisper `large-v3`
  (`vocut index --whisper-model large-v3`), use real recordings instead of
  TTS, or replace "AI" with "人工智能" in your narration.

- **uv-created venvs + editable install (`pip install -e .`)** can produce
  a `_editable_impl_<pkg>.pth` file that's missing a trailing newline.
  Python's `site.py` silently ignores the last line of a `.pth` file
  without a terminator, so `import vocut` fails even though pip says
  "Successfully installed". Fix: `printf "\n" >>
  .venv/lib/python3.12/site-packages/_editable_impl_vocut.pth`, or use a
  non-editable install (`pip install .`) for testing.

---

## Cross-platform note

`make_footage.sh` and `make_voiceover.sh` use macOS's built-in `say`. For
Linux, replace `say -v Tingting -o foo.aiff "text"` with one of:

- `espeak-ng -v zh -w foo.wav "text"` (Debian/Ubuntu: `apt install espeak-ng`)
- `edge-tts` Python package (`pip install edge-tts`) — better Chinese voice
- Pre-recorded `.wav` files of your own

Or just record your own narration with QuickTime / Audacity / OBS and skip
the TTS step entirely — that's the production path anyway.
