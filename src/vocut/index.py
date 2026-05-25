"""vocut index — scan footage folder, transcribe + embed, store in sqlite.

P0.1 walking skeleton. Visual tagging is deferred to P0.2 (vision LLM).
For now `visual_tags_json` is stored as '[]' and `scene_description` as NULL.

Architecture: see docs/ARCHITECTURE.md — this module owns the index pipeline.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

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


def transcribe_file(path: Path, model) -> tuple[list[dict], dict]:
    """Transcribe one audio/video file. Returns (segments, meta).

    segments = [{idx, start, end, text}, ...]
    meta = {duration_sec, language}
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
