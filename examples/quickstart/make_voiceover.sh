#!/usr/bin/env bash
# Generate a TTS voiceover from script.md.
#
# Strips markdown structural elements (headings, blockquotes) then pipes the
# remaining narration text to macOS `say`. Output: voiceover.wav (mono, 22kHz).
#
# Real users replace this with their own recorded voiceover.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${HERE}/work"
SCRIPT="${HERE}/script.md"
OUT="${HERE}/voiceover.wav"

if ! command -v say >/dev/null 2>&1; then
  echo "error: this script uses macOS \`say\` for TTS." >&2
  exit 1
fi

VOCUT_BIN="$(command -v vocut || true)"
if [ -n "${VOCUT_BIN}" ]; then
  VOCUT_PY="$(dirname "${VOCUT_BIN}")/python"
fi
FFMPEG=""
if [ -n "${VOCUT_PY:-}" ] && [ -x "${VOCUT_PY}" ]; then
  FFMPEG="$("${VOCUT_PY}" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
fi
if [ -z "${FFMPEG}" ] || [ ! -x "${FFMPEG}" ]; then
  FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
fi
[ -z "${FFMPEG}" ] && FFMPEG="$(command -v ffmpeg || true)"
if [ -z "${FFMPEG}" ]; then
  echo "error: ffmpeg not found." >&2
  exit 1
fi

mkdir -p "${WORK}"

# Strip markdown: headings, blockquotes, leading whitespace; collapse blank
# lines into sentence-ending punctuation so `say` reads continuously.
python3 - <<PY
import pathlib, re
text = pathlib.Path("${SCRIPT}").read_text()
text = re.sub(r'^#+\s+.*$', '', text, flags=re.M)
text = re.sub(r'^>\s*', '', text, flags=re.M)
text = re.sub(r'\n{2,}', '。', text).strip()
pathlib.Path("${WORK}/voiceover.txt").write_text(text)
PY

say -v Tingting -r 200 -f "${WORK}/voiceover.txt" -o "${WORK}/voiceover.aiff"
"${FFMPEG}" -y -loglevel error -i "${WORK}/voiceover.aiff" "${OUT}"

echo "Done. voiceover.wav at ${OUT}"
"${FFMPEG}" -i "${OUT}" 2>&1 | grep Duration
