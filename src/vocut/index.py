"""vocut index — scan footage folder, transcribe + embed, store in sqlite.

P0.1 walking skeleton. Visual tagging is deferred to P0.2 (vision LLM).
For now `visual_tags_json` is stored as '[]' and `scene_description` as NULL.

Architecture: see docs/ARCHITECTURE.md — this module owns the index pipeline.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_WHISPER_MODEL = os.environ.get("VOCUT_WHISPER_MODEL", "base")
DEFAULT_EMBED_MODEL = os.environ.get("VOCUT_EMBED_MODEL", "BAAI/bge-small-zh-v1.5")
DEFAULT_DB_DIR = ".vocut_index"
DEFAULT_DB_NAME = "footage.db"

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi", ".mp3", ".wav", ".m4a"}


SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    file_path     TEXT PRIMARY KEY,
    file_size     INTEGER NOT NULL,
    duration_sec  REAL,
    language      TEXT,
    indexed_at    TEXT NOT NULL,
    whisper_model TEXT NOT NULL,
    embed_model   TEXT NOT NULL,
    embed_dim     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS clips (
    clip_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path         TEXT NOT NULL REFERENCES files(file_path) ON DELETE CASCADE,
    segment_idx       INTEGER NOT NULL,
    start_sec         REAL NOT NULL,
    end_sec           REAL NOT NULL,
    transcript        TEXT NOT NULL,
    embedding         BLOB,
    visual_tags_json  TEXT NOT NULL DEFAULT '[]',
    scene_description TEXT,
    UNIQUE(file_path, segment_idx)
);

CREATE INDEX IF NOT EXISTS idx_clips_file ON clips(file_path);
"""


def db_path_in(cwd: Path) -> Path:
    """Default database path: <cwd>/.vocut_index/footage.db"""
    return cwd / DEFAULT_DB_DIR / DEFAULT_DB_NAME


def init_db(db_path: Path) -> sqlite3.Connection:
    """Open (or create) the index database. Returns a connection with foreign keys on."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def file_already_indexed(conn: sqlite3.Connection, file_path: Path) -> bool:
    """Match by (absolute path + file size). Cheap fingerprint, good enough for P0."""
    abs_path = str(file_path.resolve())
    size = file_path.stat().st_size
    row = conn.execute(
        "SELECT file_size FROM files WHERE file_path = ?", (abs_path,)
    ).fetchone()
    return row is not None and row[0] == size


def _load_whisper(model_name: str):
    """Lazy import — only load when we actually transcribe."""
    from faster_whisper import WhisperModel

    return WhisperModel(model_name, device="auto", compute_type="auto")


def _load_embedder(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


# -----------------------------------------------------------------------------
# Visual captioning — fallback when audio is silent
# -----------------------------------------------------------------------------


def _ffmpeg_bin_for_capture() -> str:
    """Path to bundled ffmpeg (also used by vocut.render)."""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _extract_frame_jpeg(video_path: Path, t_sec: float) -> bytes | None:
    """Grab a single JPEG frame at time t_sec from video_path. None on failure."""
    out_path = Path(tempfile.mkstemp(suffix=".jpg")[1])
    try:
        result = subprocess.run(
            [
                _ffmpeg_bin_for_capture(), "-y", "-loglevel", "error",
                "-ss", f"{t_sec:.3f}",
                "-i", str(video_path),
                "-frames:v", "1",
                "-q:v", "5",
                "-vf", "scale='min(640,iw)':-2",  # downscale large frames to 640w
                str(out_path),
            ],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
            return None
        return out_path.read_bytes()
    except (subprocess.SubprocessError, OSError):
        return None
    finally:
        out_path.unlink(missing_ok=True)


def caption_video_via_vision(
    video_path: Path,
    duration_sec: float,
    *,
    n_frames: int = 5,
    model: str | None = None,
) -> str | None:
    """Ask a vision-capable LLM to describe what's in this clip.

    Samples `n_frames` evenly-spaced frames, base64-encodes them, sends to an
    OpenAI-compatible chat endpoint that supports image input. Returns a
    concise Chinese-language description string, or None if anything fails.

    Auth via VOCUT_LLM_API_KEY + VOCUT_LLM_BASE_URL (same vars as plan.py).
    Model: VOCUT_VISION_MODEL or sensible default. Set VOCUT_VISION=1 to enable.
    """
    if os.environ.get("VOCUT_VISION") != "1":
        return None
    api_key = os.environ.get("VOCUT_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("VOCUT_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return None

    if duration_sec <= 0:
        return None

    # Sample broadly across the clip (10-90%). Stock reels often splice
    # watermarks INTO the middle, not just front/back, so we can't safely
    # skip any one region. Instead we cast a wider net and let the model
    # pick the most informative frame in its response.
    if n_frames == 1:
        timestamps = [duration_sec * 0.5]
    else:
        timestamps = [duration_sec * (0.10 + 0.80 * i / max(1, n_frames - 1)) for i in range(n_frames)]

    images_b64: list[str] = []
    for t in timestamps:
        b = _extract_frame_jpeg(video_path, t)
        if b:
            images_b64.append(base64.b64encode(b).decode("ascii"))
    if not images_b64:
        return None

    try:
        import openai  # already a vocut dep
    except ImportError:
        return None

    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = openai.OpenAI(**kwargs)

    # gpt-4o is the OpenAI default but many compat endpoints (uyilink etc.)
    # don't proxy it — gpt-5.4-mini is the safer default for those.
    default_model = "gpt-5.4-mini" if (base_url and "openai.com" not in base_url) else "gpt-4o"
    chosen_model = model or os.environ.get("VOCUT_VISION_MODEL") or default_model

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "下面这些是同一段视频的截帧。**只要其中任何一张是真实世界场景**（有人、物、动作、自然/室内环境），"
                "就用那张为准，忽略其它含 ROYALTY FREE / STOCK FOOTAGE / 品牌 logo / 文字标题 / 滚动字幕 / "
                "纯色转场 / 模糊运动 的截帧——它们是水印噪声，**不是视频主题**。"
                "\n\n用一句不超过 25 字的中文描述真实世界那张里的 主体 + 动作 + 场景。"
                "例如：'咖啡师在吧台手冲咖啡'、'工人在咖啡树下采摘红色浆果'、'热水从手冲壶倒入咖啡粉'。"
                "\n\n如果**所有截帧都是文字/水印/广告**（没有任何真实世界画面），返回单词 NO_CONTENT。"
                "否则严格输出一句画面描述，不要写 '这张图...' / '视频显示...' 这种废话开头。"
            ),
        }
    ]
    for b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })

    try:
        resp = client.chat.completions.create(
            model=chosen_model,
            max_tokens=80,
            messages=[{"role": "user", "content": content}],
        )
        text = (resp.choices[0].message.content or "").strip()
        text = re.sub(r"\s+", " ", text)
        if not text or "NO_CONTENT" in text:
            return None
        return text
    except Exception:
        return None


def transcribe_file(path: Path, model) -> tuple[list[dict], dict]:
    """Transcribe one audio/video file. Returns (segments, meta).

    segments = [{idx, start, end, text}, ...]
    meta = {duration_sec, language}

    If the audio yields no speech (silent stock footage), fall back to a
    single synthetic segment derived from the filename so the clip still
    enters the search space. Disable with VOCUT_FILENAME_FALLBACK=0.
    """
    segments_iter, info = model.transcribe(str(path), beam_size=5, vad_filter=True)
    segments: list[dict] = []
    for idx, seg in enumerate(segments_iter):
        text = (seg.text or "").strip()
        if not text:
            continue
        segments.append(
            {
                "idx": idx,
                "start": float(seg.start),
                "end": float(seg.end),
                "text": text,
            }
        )
    meta = {
        "duration_sec": float(info.duration) if info.duration else None,
        "language": info.language,
    }

    if not segments:
        duration = meta["duration_sec"] or 0.0
        # Try vision-LLM captioning first; falls back to filename.
        vision_text = caption_video_via_vision(path, duration) if duration > 0 else None
        if vision_text:
            segments.append({
                "idx": 0,
                "start": 0.0,
                "end": float(duration),
                "text": vision_text,
                "_fallback": "vision",
            })
        else:
            fallback_on = os.environ.get("VOCUT_FILENAME_FALLBACK", "1") != "0"
            fname_text = re.sub(r"[-_.]+", " ", path.stem).strip()
            if fallback_on and fname_text and duration > 0.0:
                segments.append({
                    "idx": 0,
                    "start": 0.0,
                    "end": float(duration),
                    "text": fname_text,
                    "_fallback": "filename",
                })

    return segments, meta


def embed_texts(texts: list[str], model) -> np.ndarray:
    """Return shape (n, dim) float32 embeddings, L2-normalized."""
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)


def store_file_and_clips(
    conn: sqlite3.Connection,
    file_path: Path,
    file_meta: dict,
    segments: list[dict],
    embeddings: np.ndarray,
    whisper_model_name: str,
    embed_model_name: str,
) -> None:
    """Atomic insert: upsert file row + insert all clips."""
    abs_path = str(file_path.resolve())
    embed_dim = int(embeddings.shape[1]) if embeddings.size else 0
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with conn:
        conn.execute("DELETE FROM clips WHERE file_path = ?", (abs_path,))
        conn.execute("DELETE FROM files WHERE file_path = ?", (abs_path,))
        conn.execute(
            """INSERT INTO files
            (file_path, file_size, duration_sec, language, indexed_at,
             whisper_model, embed_model, embed_dim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                abs_path,
                file_path.stat().st_size,
                file_meta.get("duration_sec"),
                file_meta.get("language"),
                now_iso,
                whisper_model_name,
                embed_model_name,
                embed_dim,
            ),
        )
        rows = [
            (
                abs_path,
                seg["idx"],
                seg["start"],
                seg["end"],
                seg["text"],
                embeddings[i].tobytes() if i < len(embeddings) else None,
            )
            for i, seg in enumerate(segments)
        ]
        conn.executemany(
            """INSERT INTO clips
            (file_path, segment_idx, start_sec, end_sec, transcript, embedding)
            VALUES (?, ?, ?, ?, ?, ?)""",
            rows,
        )


def iter_media_files(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def index_folder(
    folder: Path,
    db_path: Path | None = None,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
    embed_model_name: str = DEFAULT_EMBED_MODEL,
    force: bool = False,
    progress_callback=None,
) -> dict:
    """Walk folder, transcribe + embed + store every supported media file.

    Returns stats dict: {files_seen, files_indexed, files_skipped, clips_added, elapsed_sec}.
    """
    if db_path is None:
        db_path = db_path_in(Path.cwd())
    folder = folder.resolve()
    if not folder.exists():
        raise FileNotFoundError(f"folder not found: {folder}")

    files = iter_media_files(folder)
    stats = {
        "files_seen": len(files),
        "files_indexed": 0,
        "files_skipped": 0,
        "clips_added": 0,
        "elapsed_sec": 0.0,
        "db_path": str(db_path),
    }
    if not files:
        return stats

    t0 = time.time()
    conn = init_db(db_path)

    whisper_model = None  # lazy
    embed_model = None

    try:
        for i, path in enumerate(files, 1):
            if progress_callback:
                progress_callback({"phase": "scan", "i": i, "total": len(files), "file": path.name})

            if not force and file_already_indexed(conn, path):
                stats["files_skipped"] += 1
                continue

            if whisper_model is None:
                if progress_callback:
                    progress_callback({"phase": "load_whisper", "model": whisper_model_name})
                whisper_model = _load_whisper(whisper_model_name)
            if embed_model is None:
                if progress_callback:
                    progress_callback({"phase": "load_embedder", "model": embed_model_name})
                embed_model = _load_embedder(embed_model_name)

            if progress_callback:
                progress_callback({"phase": "transcribe", "file": path.name})
            segments, meta = transcribe_file(path, whisper_model)

            if progress_callback:
                progress_callback({"phase": "embed", "file": path.name, "n_segments": len(segments)})
            embeddings = (
                embed_texts([s["text"] for s in segments], embed_model)
                if segments
                else np.zeros((0, 0), dtype=np.float32)
            )

            store_file_and_clips(
                conn, path, meta, segments, embeddings, whisper_model_name, embed_model_name
            )
            stats["files_indexed"] += 1
            stats["clips_added"] += len(segments)
    finally:
        conn.close()

    stats["elapsed_sec"] = round(time.time() - t0, 2)
    return stats


def get_status(db_path: Path | None = None) -> dict:
    """Return a summary of what's currently indexed."""
    if db_path is None:
        db_path = db_path_in(Path.cwd())
    if not db_path.exists():
        return {"db_path": str(db_path), "exists": False}

    conn = sqlite3.connect(str(db_path))
    try:
        n_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        n_clips = conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
        total_duration = conn.execute(
            "SELECT COALESCE(SUM(duration_sec), 0) FROM files"
        ).fetchone()[0]
        models = conn.execute(
            "SELECT DISTINCT whisper_model, embed_model, embed_dim FROM files"
        ).fetchall()
        sample = conn.execute(
            "SELECT file_path, start_sec, end_sec, transcript FROM clips LIMIT 5"
        ).fetchall()
    finally:
        conn.close()

    return {
        "db_path": str(db_path),
        "exists": True,
        "files_indexed": n_files,
        "clips": n_clips,
        "total_footage_sec": round(total_duration, 1),
        "models": [{"whisper": w, "embed": e, "dim": d} for w, e, d in models],
        "sample_clips": [
            {"file": Path(p).name, "start": s, "end": e, "text": t} for p, s, e, t in sample
        ],
    }
