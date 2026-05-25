"""Unit tests for the db layer of vocut.index — no ML dependencies."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pytest

from vocut.index import (
    file_already_indexed,
    get_status,
    init_db,
    store_file_and_clips,
)


@pytest.fixture
def fake_clip(tmp_path: Path) -> Path:
    """Make a fake file on disk so file_path.stat() works."""
    p = tmp_path / "fake.wav"
    p.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")  # bogus tiny payload
    return p


def test_init_db_creates_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "index.db"
    conn = init_db(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {"files", "clips"}.issubset(tables)
    finally:
        conn.close()


def test_store_and_status_roundtrip(tmp_path: Path, fake_clip: Path) -> None:
    db_path = tmp_path / "index.db"
    conn = init_db(db_path)

    segments = [
        {"idx": 0, "start": 0.0, "end": 3.2, "text": "first sentence"},
        {"idx": 1, "start": 3.2, "end": 7.5, "text": "second sentence"},
    ]
    embeddings = np.random.rand(2, 32).astype(np.float32)

    store_file_and_clips(
        conn,
        fake_clip,
        {"duration_sec": 7.5, "language": "en"},
        segments,
        embeddings,
        whisper_model_name="base",
        embed_model_name="test-embed",
    )
    conn.close()

    status = get_status(db_path)
    assert status["exists"]
    assert status["files_indexed"] == 1
    assert status["clips"] == 2
    assert status["total_footage_sec"] == 7.5
    assert status["models"] == [{"whisper": "base", "embed": "test-embed", "dim": 32}]
    assert len(status["sample_clips"]) == 2


def test_file_already_indexed_matches_by_size(tmp_path: Path, fake_clip: Path) -> None:
    db_path = tmp_path / "index.db"
    conn = init_db(db_path)

    assert not file_already_indexed(conn, fake_clip)

    embeddings = np.zeros((0, 0), dtype=np.float32)
    store_file_and_clips(
        conn,
        fake_clip,
        {"duration_sec": 0.0, "language": None},
        segments=[],
        embeddings=embeddings,
        whisper_model_name="base",
        embed_model_name="test",
    )

    assert file_already_indexed(conn, fake_clip)

    # If file content (size) changes, fingerprint mismatches → not indexed
    fake_clip.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt EXTRA")
    assert not file_already_indexed(conn, fake_clip)

    conn.close()


def test_re_storing_replaces_old_clips(tmp_path: Path, fake_clip: Path) -> None:
    db_path = tmp_path / "index.db"
    conn = init_db(db_path)
    embeddings = np.random.rand(2, 8).astype(np.float32)

    store_file_and_clips(
        conn,
        fake_clip,
        {"duration_sec": 5.0, "language": "en"},
        [{"idx": 0, "start": 0, "end": 2, "text": "a"},
         {"idx": 1, "start": 2, "end": 5, "text": "b"}],
        embeddings,
        "base",
        "test-embed",
    )

    # Re-store with different segments
    new_embeddings = np.random.rand(1, 8).astype(np.float32)
    store_file_and_clips(
        conn,
        fake_clip,
        {"duration_sec": 3.0, "language": "en"},
        [{"idx": 0, "start": 0, "end": 3, "text": "rewritten"}],
        new_embeddings,
        "base",
        "test-embed",
    )

    n = conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
    assert n == 1  # old rows replaced, not appended

    text = conn.execute("SELECT transcript FROM clips").fetchone()[0]
    assert text == "rewritten"

    conn.close()


def test_status_on_missing_db(tmp_path: Path) -> None:
    db_path = tmp_path / "does_not_exist.db"
    status = get_status(db_path)
    assert status["exists"] is False
