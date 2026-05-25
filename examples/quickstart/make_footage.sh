#!/usr/bin/env bash
# Generate 5 synthetic footage clips for the quickstart example.
#
# Each clip is a 5-7 second 1280x720 mp4 with:
#   - solid color background
#   - large title text (PingFang)
#   - TTS narration as audio track (macOS `say` -> aiff -> wav)
#
# These clips are deliberately on-the-nose so the matching step's quality is
# visible: each script sentence semantically lines up with exactly one clip.
#
# Requires: macOS (uses `say`). For Linux see README "Cross-platform note".
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${HERE}/work"
FOOTAGE="${HERE}/footage"

if ! command -v say >/dev/null 2>&1; then
  echo "error: this script uses macOS \`say\` for TTS. On Linux, swap in espeak/festival or pre-record audio." >&2
  exit 1
fi

# Locate ffmpeg: prefer the imageio-ffmpeg bundled binary so the example
# works without a system ffmpeg install (matches vocut's own dependency).
# Use the python that ships next to the `vocut` CLI — that's the venv with
# imageio-ffmpeg installed.
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
if [ -z "${FFMPEG}" ] || [ ! -x "${FFMPEG}" ]; then
  FFMPEG="$(command -v ffmpeg || true)"
fi
if [ -z "${FFMPEG}" ]; then
  echo "error: ffmpeg not found. \`pip install imageio-ffmpeg\` (or brew install ffmpeg) and retry." >&2
  exit 1
fi

mkdir -p "${WORK}" "${FOOTAGE}"

# name | bg color (0xRRGGBB) | on-screen label | spoken narration
CLIPS=(
  "01-data|0x1E40AF|数据规模|今年全球数据总量达到一百七十五ZB，比十年前增长六十倍。"
  "02-compare|0xB91C1C|战略对比|苹果押注端侧推理和隐私，谷歌押注云端模型和规模化。"
  "03-list|0x047857|三大趋势|本地模型够用，边缘计算普及，隐私优先成为产品默认。"
  "04-quote|0x111827|金句引用|AI不会取代人类，但是会用AI的人会取代不会用AI的人。"
  "05-case|0x6D28D9|真实案例|二十人的初创团队，靠AI把客服业务做到了行业头部。"
)

# Pick a system Chinese font (best-effort; ffmpeg drawtext needs an absolute path)
FONT="/System/Library/Fonts/PingFang.ttc"
[ ! -f "${FONT}" ] && FONT="/System/Library/Fonts/STHeiti Medium.ttc"
[ ! -f "${FONT}" ] && FONT="/System/Library/Fonts/Helvetica.ttc"

for entry in "${CLIPS[@]}"; do
  IFS='|' read -r name color label text <<< "$entry"
  echo "── ${name} ──"

  # 1) TTS narration
  say -v Tingting -o "${WORK}/${name}.aiff" "${text}"

  # 2) aiff -> wav
  "${FFMPEG}" -y -loglevel error -i "${WORK}/${name}.aiff" "${WORK}/${name}.wav"

  # 3) compose colored card + label + TTS audio.
  # `color` source gets a generous duration (60s); `-shortest` clips the
  # output to the wav length. Avoids fragile duration parsing.
  "${FFMPEG}" -y -loglevel error \
    -f lavfi -i "color=c=${color}:s=1280x720:d=60" \
    -i "${WORK}/${name}.wav" \
    -vf "drawtext=text='${label}':fontfile=${FONT}:fontsize=120:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
    "${FOOTAGE}/${name}.mp4"

  echo "  -> ${FOOTAGE}/${name}.mp4"
done

echo
echo "Done. 5 clips in ${FOOTAGE}/"
ls -lh "${FOOTAGE}"/
