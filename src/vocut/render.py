"""vocut render — plan.json + footage → output.mp4.

P0.4 minimal walking skeleton. Motion-graphic items render as Pillow-drawn
text cards (placeholder for the eventual Remotion P0.3 components).

Pipeline per plan item:
  1. footage      → ffmpeg trim from source file, scale + pad to target frame
  2. hybrid       → same as footage (overlay will land when Remotion arrives)
  3. motion_graphic → Pillow renders a card PNG → ffmpeg makes a still mp4

All segments are then concatenated via the ffmpeg concat filter (re-encode
ensures uniform stream params; concat-demuxer with -c copy is fragile).

If a voiceover audio file is provided, it is overlaid on the final video
(simple replace; voiceover-to-sentence alignment is a P1 task).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_FPS = 30
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_CARD_DURATION_SEC = 4.0

# Claude-design-ish muted palette per component (placeholder until P0.3 components ship).
CARD_BACKGROUND = {
    "key_number": "#0f172a",        # near-black with cool tone
    "pull_quote": "#1f1611",        # warm dark
    "title_card": "#000000",        # darkest
    "comparison_panel": "#0c1428",  # cool blue-tinged
    "list_item": "#161616",         # neutral dark
    "keyword_highlight": "#1a1a1a", # neutral dark
}
DEFAULT_BACKGROUND = "#1a1a1a"

CARD_TEXT_COLOR = (236, 236, 232)   # off-white, lower contrast than pure white

# Macos system fonts that handle Chinese well. First match wins.
FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # cross-platform fallback (Linux / Docker)
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]


# -----------------------------------------------------------------------------
# Toolchain helpers
# -----------------------------------------------------------------------------


def _ffmpeg_bin() -> str:
    """Path to bundled ffmpeg via imageio-ffmpeg (no system install required)."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(cmd: list[str]) -> None:
    """Run a subprocess, raise with stderr if it fails."""
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpeg failed (exit {e.returncode}):\n"
            f"  cmd: {' '.join(cmd[:6])} …\n"
            f"  stderr: {e.stderr.decode('utf-8', errors='replace')[-500:]}"
        ) from e


def _pick_font_path() -> str | None:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


# -----------------------------------------------------------------------------
# Card renderer (motion-graphic placeholder)
# -----------------------------------------------------------------------------


def _max_chars_for_frame(width: int, font_size: int) -> int:
    """Rough chars-per-line for CJK text at this width + font size."""
    return max(10, int(width / max(1, font_size) * 0.85))


def _wrap_text_cjk(text: str, max_chars: int = 20, hard_overflow: int = 6) -> list[str]:
    """CJK-friendly word wrap.

    Strategy: once the current line exceeds max_chars, retro-break at the
    most recent punctuation (or whitespace). If no breakable position exists
    in-line and the line passes (max_chars + hard_overflow), force a hard break.
    """
    breakable = set(" 　。，！？、；：.,!?;:")
    hard_limit = max_chars + hard_overflow

    lines: list[str] = []
    line_start = 0
    last_break_at = -1  # latest absolute index of a breakable char in current line

    for i, ch in enumerate(text):
        if ch in breakable:
            last_break_at = i
        cur_len = i - line_start + 1
        if cur_len > max_chars:
            if last_break_at >= line_start:
                lines.append(text[line_start : last_break_at + 1].strip())
                line_start = last_break_at + 1
                last_break_at = -1
            elif cur_len >= hard_limit:
                lines.append(text[line_start : i + 1].strip())
                line_start = i + 1
                last_break_at = -1

    remainder = text[line_start:].strip()
    if remainder:
        lines.append(remainder)
    return lines or [text]


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def render_card_png(
    sentence: str,
    component: str,
    out_png: Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Path:
    """Draw a single-frame card PNG via Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    bg = _hex_to_rgb(CARD_BACKGROUND.get(component, DEFAULT_BACKGROUND))
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    font_path = _pick_font_path()
    base_font_size = max(28, min(64, height // 14))
    if font_path:
        font = ImageFont.truetype(font_path, base_font_size)
    else:
        font = ImageFont.load_default()

    lines = _wrap_text_cjk(sentence, max_chars=_max_chars_for_frame(width, base_font_size))
    line_h = base_font_size + 14
    total_h = line_h * len(lines)
    y_start = (height - total_h) // 2

    # Component label in the corner (subtle, helps debugging)
    if font_path:
        small_font = ImageFont.truetype(font_path, max(14, base_font_size // 3))
        draw.text((24, 18), f"[{component}]", fill=(110, 110, 110), font=small_font)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        y = y_start + i * line_h
        draw.text((x, y), line, fill=CARD_TEXT_COLOR, font=font)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    return out_png


def render_card_segment(
    sentence: str,
    component: str,
    out_mp4: Path,
    duration_sec: float = DEFAULT_CARD_DURATION_SEC,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Path:
    """Render PNG card → silent mp4 segment of N seconds."""
    png_path = out_mp4.with_suffix(".png")
    render_card_png(sentence, component, png_path, width=width, height=height)
    cmd = [
        _ffmpeg_bin(), "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png_path),
        "-t", str(duration_sec),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-an",  # no audio track; voiceover added later
        str(out_mp4),
    ]
    _run(cmd)
    png_path.unlink(missing_ok=True)
    return out_mp4


# -----------------------------------------------------------------------------
# Remotion motion-graphic renderer (P0.3 — replaces Pillow placeholders)
# -----------------------------------------------------------------------------


def _components_dir_ready(p: Path) -> bool:
    """A directory is a usable components subproject if it has node_modules,
    the Remotion entry, and the Card composition."""
    return (
        (p / "node_modules").is_dir()
        and (p / "package.json").exists()
        and (p / "src" / "Root.tsx").exists()
    )


def _find_components_dir() -> Path | None:
    """Locate the Remotion components subproject. Search order:
      1. VOCUT_COMPONENTS_DIR env var
      2. ./components or ./vocut/components relative to cwd
      3. Walk up from this file (works for editable installs)
    """
    if env := os.environ.get("VOCUT_COMPONENTS_DIR"):
        p = Path(env).resolve()
        if _components_dir_ready(p):
            return p

    for c in (Path.cwd() / "components", Path.cwd() / "vocut" / "components"):
        if _components_dir_ready(c):
            return c.resolve()

    here = Path(__file__).resolve()
    for i in range(2, min(6, len(here.parents))):
        c = here.parents[i] / "components"
        if _components_dir_ready(c):
            return c
    return None


def render_remotion_segment(
    item: dict[str, Any],
    out_mp4: Path,
    components_dir: Path,
    *,
    duration_sec: float = DEFAULT_CARD_DURATION_SEC,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> Path:
    """Render a motion-graphic plan item by invoking `npx remotion render`.

    Builds a Card-shape props JSON from the plan item, writes it to a temp
    file (avoids shell-escape pain with Chinese strings), then shells out.
    """
    match = item.get("match", {})
    component = match.get("component", "keyword_highlight")
    raw_props = dict(match.get("props") or {})
    total_frames = max(1, int(round(duration_sec * fps)))

    # palette / bg_style / text_motion / accent_fx can live at match level
    # (canonical) or be tucked into match.props (LLM convenience). Strip
    # them out of props either way so they reach Card's top-level args.
    def _take(key: str) -> Any:
        return match.get(key) or raw_props.pop(key, None)

    card_props: dict[str, Any] = {
        "component": component,
        "props": raw_props,
        "sentence": item.get("sentence", ""),
        "durationInFrames": total_frames,
    }
    for k in ("palette", "bg_style", "text_motion", "accent_fx"):
        v = _take(k)
        if v is not None:
            card_props[k] = v

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    props_json = out_mp4.with_suffix(".props.json")
    props_json.write_text(json.dumps(card_props, ensure_ascii=False))

    raw_path = out_mp4.with_name(out_mp4.stem + "-raw.mp4")
    cmd = [
        "npx", "--no-install", "remotion", "render",
        "src/index.ts", "Card",
        str(raw_path.resolve()),
        f"--props={props_json.resolve()}",
        "--scale=1",
        "--codec=h264",
        "--concurrency=1",
        f"--width={width}",
        f"--height={height}",
        "--log=error",
    ]
    try:
        subprocess.run(
            cmd, check=True, capture_output=True, cwd=str(components_dir)
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"remotion render failed (exit {e.returncode}):\n"
            f"  cmd: {' '.join(cmd[:8])} …\n"
            f"  stderr: {e.stderr.decode('utf-8', errors='replace')[-500:]}"
        ) from e
    finally:
        props_json.unlink(missing_ok=True)

    # Normalize Remotion's output to match footage segments exactly so the
    # concat filter doesn't choke on mismatched pix_fmt / SAR / audio stream
    # presence. Remotion ships h264 with yuvj420p + a silent stereo track;
    # footage segments are yuv420p + no audio. One ffmpeg re-encode per
    # motion-graphic scene is fine — they're short.
    _run([
        _ffmpeg_bin(), "-y", "-loglevel", "error",
        "-i", str(raw_path),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-vf", "setsar=1:1,fps=" + str(fps),
        "-an",
        str(out_mp4),
    ])
    raw_path.unlink(missing_ok=True)
    return out_mp4


# -----------------------------------------------------------------------------
# Footage segment renderer
# -----------------------------------------------------------------------------


def render_footage_segment(
    footage: dict[str, Any],
    out_mp4: Path,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    duration_scale: float = 1.0,
) -> Path:
    """Trim [start_sec, end_sec] from source_file. Scale + letterbox to target frame.

    For audio-only sources (.wav / .mp3), produces a silent video segment of the
    requested duration (so the segment can still be concatenated).

    `duration_scale` multiplies the requested duration (e.g. 0.85 to shrink
    each scene by 15% so total runtime aligns with a voiceover).
    """
    src = footage["source_file"]
    if not Path(src).exists():
        raise FileNotFoundError(f"footage source not found: {src}")

    start = float(footage["start_sec"])
    duration = (float(footage["end_sec"]) - start) * max(0.1, duration_scale)
    audio_only = Path(src).suffix.lower() in {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}

    if audio_only:
        cmd = [
            _ffmpeg_bin(), "-y", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"color=c=black:s={width}x{height}:r={fps}:d={duration}",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an",
            str(out_mp4),
        ]
        _run(cmd)
        return out_mp4

    cmd = [
        _ffmpeg_bin(), "-y", "-loglevel", "error",
        "-ss", str(start), "-i", src,
        "-t", str(duration),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1:1,"
            f"fps={fps}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an",
        str(out_mp4),
    ]
    _run(cmd)
    return out_mp4


# -----------------------------------------------------------------------------
# Concat + audio overlay
# -----------------------------------------------------------------------------


def concat_segments(segments: list[Path], out_mp4: Path) -> Path:
    """Concat via the concat filter (re-encode for stream-uniformity safety)."""
    if not segments:
        raise ValueError("no segments to concat")
    if len(segments) == 1:
        shutil.copyfile(segments[0], out_mp4)
        return out_mp4

    cmd = [_ffmpeg_bin(), "-y", "-loglevel", "error"]
    for s in segments:
        cmd.extend(["-i", str(s)])
    filter_inputs = "".join(f"[{i}:v:0]" for i in range(len(segments)))
    filter_complex = f"{filter_inputs}concat=n={len(segments)}:v=1:a=0[outv]"
    cmd.extend(
        [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-an",
            str(out_mp4),
        ]
    )
    _run(cmd)
    return out_mp4


def _probe_duration(path: Path) -> float | None:
    """Return media duration in seconds via ffmpeg -i stderr parse.

    Returns None if duration can't be determined. ffmpeg without an output
    target exits non-zero, so this swallows that.
    """
    import re
    try:
        result = subprocess.run(
            [_ffmpeg_bin(), "-i", str(path)],
            capture_output=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    stderr = result.stderr.decode("utf-8", errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if not m:
        return None
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def overlay_voiceover(video: Path, voiceover: Path, out_mp4: Path) -> Path:
    """Overlay voiceover and clamp output to voiceover length.

    `-shortest` is unreliable with `-c:v copy` — we explicitly probe the
    voiceover and pass `-t` so the muxer hard-stops at the right boundary
    regardless of how long the silent video pre-roll happens to be.
    """
    vo_dur = _probe_duration(voiceover)
    cmd = [
        _ffmpeg_bin(), "-y", "-loglevel", "error",
        "-i", str(video),
        "-i", str(voiceover),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
    ]
    if vo_dur and vo_dur > 0:
        cmd.extend(["-t", f"{vo_dur:.3f}"])
    else:
        cmd.append("-shortest")
    cmd.append(str(out_mp4))
    _run(cmd)
    return out_mp4


# -----------------------------------------------------------------------------
# Top-level orchestrator
# -----------------------------------------------------------------------------


def _segment_match_type(item: dict[str, Any]) -> str:
    return item["match"]["type"]


def render(
    plan_path: Path,
    out_path: Path,
    *,
    voiceover: Path | None = None,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    card_duration_sec: float = DEFAULT_CARD_DURATION_SEC,
    progress_callback=None,
) -> dict[str, Any]:
    """End-to-end render. Returns stats dict."""
    plan_doc = json.loads(plan_path.read_text())
    items = plan_doc.get("plan", [])
    if not items:
        raise ValueError(f"plan has no items: {plan_path}")

    work_dir = Path(tempfile.mkdtemp(prefix="vocut-render-"))
    segments: list[Path] = []
    failed: list[dict[str, Any]] = []

    use_remotion = os.environ.get("VOCUT_NO_REMOTION") != "1"
    components_dir = _find_components_dir() if use_remotion else None
    motion_backend = "remotion" if components_dir else "pillow"

    # If voiceover is provided, scale every scene's duration so the concatenated
    # video matches voiceover length. Otherwise the muxer hard-cuts the tail
    # mid-frame at the -t boundary; pre-scaling gives every scene a fair share
    # of the timeline.
    duration_scale = 1.0
    if voiceover:
        vo_dur = _probe_duration(voiceover)
        if vo_dur and vo_dur > 0:
            planned: list[float] = []
            for item in items:
                m = item.get("match", {})
                if m.get("type") in ("footage", "hybrid"):
                    block = m if m.get("type") == "footage" else (m.get("primary") or {})
                    planned.append(max(0.1, float(block.get("end_sec", 0)) - float(block.get("start_sec", 0))))
                else:
                    planned.append(float(item.get("duration_estimate_sec") or card_duration_sec))
            total_planned = sum(planned)
            if total_planned > 0:
                duration_scale = vo_dur / total_planned

    try:
        for i, item in enumerate(items, 1):
            seg_path = work_dir / f"seg_{i:04d}.mp4"
            kind = _segment_match_type(item)
            if progress_callback:
                progress_callback(
                    {"phase": "segment", "i": i, "total": len(items), "kind": kind}
                )
            try:
                if kind == "footage":
                    render_footage_segment(item["match"], seg_path, fps, width, height, duration_scale=duration_scale)
                elif kind == "hybrid":
                    # P0.4: render footage only; overlay deferred to Remotion (P0.3/P0.4.1).
                    render_footage_segment(item["match"]["primary"], seg_path, fps, width, height, duration_scale=duration_scale)
                else:
                    seg_dur = float(item.get("duration_estimate_sec") or card_duration_sec) * duration_scale
                    if components_dir is not None:
                        try:
                            render_remotion_segment(
                                item, seg_path, components_dir,
                                duration_sec=seg_dur, fps=fps,
                                width=width, height=height,
                            )
                        except Exception as e:
                            # Soft fallback to Pillow so one bad component
                            # doesn't kill the whole render.
                            print(
                                f"  [segment {i}] remotion failed, falling back to pillow: {e}",
                                file=sys.stderr,
                            )
                            render_card_segment(
                                item["sentence"],
                                item["match"].get("component", "keyword_highlight"),
                                seg_path,
                                duration_sec=seg_dur,
                                fps=fps, width=width, height=height,
                            )
                    else:
                        render_card_segment(
                            item["sentence"],
                            item["match"].get("component", "keyword_highlight"),
                            seg_path,
                            duration_sec=seg_dur,
                            fps=fps, width=width, height=height,
                        )
                segments.append(seg_path)
            except Exception as e:
                failed.append({"sentence_idx": item.get("sentence_idx"), "error": str(e)})

        if not segments:
            raise RuntimeError(
                f"all {len(items)} segments failed to render. First few errors: {failed[:3]}"
            )

        if progress_callback:
            progress_callback({"phase": "concat", "n": len(segments)})
        concat_path = work_dir / "concat.mp4"
        concat_segments(segments, concat_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        if voiceover:
            if progress_callback:
                progress_callback({"phase": "overlay_voiceover"})
            overlay_voiceover(concat_path, voiceover, out_path)
        else:
            shutil.copyfile(concat_path, out_path)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "output": str(out_path.resolve()),
        "segments_rendered": len(segments),
        "segments_failed": len(failed),
        "failed_items": failed,
        "with_voiceover": voiceover is not None,
        "frame_size": f"{width}x{height}",
        "fps": fps,
        "motion_backend": motion_backend,
        "components_dir": str(components_dir) if components_dir else None,
    }
