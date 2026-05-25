#!/usr/bin/env bash
# vocut quickstart — end-to-end demo.
#
# 1. Generate 5 synthetic footage clips
# 2. Generate a TTS voiceover from script.md
# 3. vocut index   (Whisper transcribe + embed -> sqlite)
# 4. vocut plan    (semantic match + LLM rerank)
# 5. vocut render  (concat footage + overlay voiceover -> output.mp4)
# 6. Open output.mp4
#
# Prereqs:
#   - macOS (uses `say`); see README for Linux notes
#   - vocut installed:        pip install vocut       (or: pip install -e <repo>)
#   - LLM credentials in env: VOCUT_LLM_BASE_URL + VOCUT_LLM_API_KEY  (OpenAI-compatible)
#                       OR:   OPENAI_API_KEY  /  ANTHROPIC_API_KEY
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${HERE}"

step() { printf "\n\033[1;36m── %s ──\033[0m\n" "$1"; }

if ! command -v vocut >/dev/null 2>&1; then
  echo "error: \`vocut\` CLI not on PATH. Activate your venv or pip install vocut." >&2
  exit 1
fi

step "1/5  Synthesizing 5 footage clips"
[ -d footage ] && [ "$(ls -A footage 2>/dev/null)" ] \
  && echo "  (skipping; ./footage already populated — delete to regenerate)" \
  || ./make_footage.sh

step "2/5  Synthesizing voiceover.wav"
[ -f voiceover.wav ] \
  && echo "  (skipping; ./voiceover.wav exists — delete to regenerate)" \
  || ./make_voiceover.sh

step "3/5  vocut index"
vocut index ./footage/ --db ./.vocut_index/footage.db

step "4/5  vocut plan"
vocut plan ./script.md --db ./.vocut_index/footage.db --out ./plan.json

step "5/5  vocut render"
vocut render ./plan.json --out ./output.mp4 --voiceover ./voiceover.wav

step "Done"
echo "Output: ${HERE}/output.mp4"
[ "$(uname)" = "Darwin" ] && open ./output.mp4
