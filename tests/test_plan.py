"""Unit tests for vocut.plan — no LLM calls, no sentence-transformer downloads."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from vocut.plan import (
    build_plan_item,
    heuristic_motion_graphic,
    heuristic_pick,
    parse_script,
    topk_candidates,
)


# -----------------------------------------------------------------------------
# parse_script
# -----------------------------------------------------------------------------


def test_parse_script_strips_numbered_list_prefix() -> None:
    content = (
        "# Trolley Problem\n\n"
        "## Opening\n\n"
        "1. Assume you are a switch operator.\n"
        "2. Five people are tied to the track.\n"
    )
    sents = parse_script(content)
    texts = [s["text"] for s in sents]
    assert texts == [
        "Assume you are a switch operator.",
        "Five people are tied to the track.",
    ]
    # Section context should be the most recent header
    assert sents[0]["section"] == {"level": 2, "title": "Opening"}


def test_parse_script_splits_chinese_punctuation() -> None:
    content = (
        "## 开场\n\n"
        "假如你是扳道工。前方有五人。你拉吗？这就是电车难题！\n"
    )
    sents = parse_script(content)
    texts = [s["text"] for s in sents]
    assert texts == [
        "假如你是扳道工。",
        "前方有五人。",
        "你拉吗？",
        "这就是电车难题！",
    ]


def test_parse_script_ignores_blockquotes_and_blank_lines() -> None:
    content = (
        "> this is a metadata blockquote\n\n"
        "## Section\n\n"
        "Sentence one.\n\n"
        "> another comment\n"
        "Sentence two.\n"
    )
    sents = parse_script(content)
    assert [s["text"] for s in sents] == ["Sentence one.", "Sentence two."]


def test_parse_script_indices_are_sequential() -> None:
    content = "1. A.\n2. B.\n3. C.\n"
    sents = parse_script(content)
    assert [s["idx"] for s in sents] == [0, 1, 2]


# -----------------------------------------------------------------------------
# heuristic detectors
# -----------------------------------------------------------------------------


def test_heuristic_picks_pull_quote_for_quoted_text() -> None:
    r = heuristic_motion_graphic('康德说："人永远是目的，不是手段。"', None)
    assert r["component"] == "pull_quote"
    assert "人永远是目的" in r["props"]["quote"]


def test_heuristic_picks_key_number_for_numeric_facts() -> None:
    r = heuristic_motion_graphic("全球累计有 4000 万人参与了这个测试。", None)
    assert r["component"] == "key_number"
    assert r["props"]["primary"] == "4000"
    assert "万" in r["props"]["unit"]


def test_heuristic_picks_comparison_panel_for_versus_markers() -> None:
    r = heuristic_motion_graphic("对比同档期的原神和崩坏星穹铁道", None)
    assert r["component"] == "comparison_panel"


def test_heuristic_picks_list_item_for_enumeration() -> None:
    r = heuristic_motion_graphic("首先，去找你的素材库。", None)
    assert r["component"] == "list_item"


def test_heuristic_falls_back_to_keyword_highlight() -> None:
    r = heuristic_motion_graphic("一段没有特征的陈述。", None)
    assert r["component"] == "keyword_highlight"


def test_heuristic_pick_prefers_footage_when_similarity_high() -> None:
    sentence = "elephants have long trunks"
    candidates = [{"similarity": 0.85, "transcript": "elephants and their trunks"}]
    r = heuristic_pick(sentence, None, candidates, threshold=0.6)
    assert r["type"] == "footage"
    assert r["candidate_idx"] == 0


def test_heuristic_pick_falls_back_to_motion_graphic_when_similarity_low() -> None:
    candidates = [{"similarity": 0.20, "transcript": "totally unrelated text"}]
    r = heuristic_pick("4000 万人参与了测试", None, candidates, threshold=0.6)
    assert r["type"] == "motion_graphic"
    assert r["component"] == "key_number"


# -----------------------------------------------------------------------------
# topk_candidates
# -----------------------------------------------------------------------------


def test_topk_candidates_orders_by_similarity() -> None:
    # 3 clips with embeddings pointing in roughly known directions
    clips = [
        {"clip_id": 1, "file_path": "/a.mp4", "segment_idx": 0,
         "start_sec": 0, "end_sec": 5, "transcript": "north"},
        {"clip_id": 2, "file_path": "/a.mp4", "segment_idx": 1,
         "start_sec": 5, "end_sec": 10, "transcript": "east"},
        {"clip_id": 3, "file_path": "/a.mp4", "segment_idx": 2,
         "start_sec": 10, "end_sec": 15, "transcript": "northwest"},
    ]
    clip_matrix = np.array(
        [[1.0, 0.0], [0.0, 1.0], [0.707, 0.707]],
        dtype=np.float32,
    )
    # Sentence vector pointing exactly north → clip 1 wins, clip 3 second
    sentence_vec = np.array([1.0, 0.0], dtype=np.float32)
    top = topk_candidates(sentence_vec, clips, clip_matrix, k=2)
    assert [c["clip_id"] for c in top] == [1, 3]
    assert top[0]["similarity"] == pytest.approx(1.0)


def test_topk_candidates_empty_db() -> None:
    top = topk_candidates(np.zeros(8, dtype=np.float32), [], np.zeros((0, 0), dtype=np.float32), k=5)
    assert top == []


# -----------------------------------------------------------------------------
# build_plan_item
# -----------------------------------------------------------------------------


def test_build_plan_item_footage() -> None:
    sentence = {"idx": 0, "text": "elephants", "section": None}
    candidates = [
        {
            "clip_id": 7,
            "file_path": "/footage/zoo.mp4",
            "start_sec": 1.0,
            "end_sec": 4.5,
            "transcript": "look at the elephants",
            "similarity": 0.8,
        }
    ]
    match = {"type": "footage", "candidate_idx": 0, "confidence": 0.85, "reasoning": "ok"}
    item = build_plan_item(sentence, candidates, match)
    assert item["match"]["type"] == "footage"
    assert item["match"]["clip_id"] == 7
    assert item["match"]["confidence"] == 0.85
    assert item["duration_estimate_sec"] == 3.5


def test_build_plan_item_motion_graphic() -> None:
    sentence = {"idx": 1, "text": "去年的数据", "section": None}
    match = {
        "type": "motion_graphic",
        "component": "key_number",
        "props": {"primary": "100"},
        "confidence": 0.9,
        "reasoning": "number",
    }
    item = build_plan_item(sentence, [], match)
    assert item["match"]["type"] == "motion_graphic"
    assert item["match"]["component"] == "key_number"
    assert item["match"]["props"] == {"primary": "100"}


def test_build_plan_item_hybrid() -> None:
    sentence = {"idx": 2, "text": "1500 抽", "section": None}
    candidates = [
        {
            "clip_id": 3,
            "file_path": "/g.mp4",
            "start_sec": 10.0,
            "end_sec": 15.0,
            "transcript": "the gacha screen",
            "similarity": 0.7,
        }
    ]
    match = {
        "type": "hybrid",
        "candidate_idx": 0,
        "component": "key_number",
        "props": {"primary": "1500", "unit": "抽"},
        "confidence": 0.82,
        "reasoning": "gacha screen + number overlay",
    }
    item = build_plan_item(sentence, candidates, match)
    assert item["match"]["type"] == "hybrid"
    assert item["match"]["primary"]["clip_id"] == 3
    assert item["match"]["overlay"]["component"] == "key_number"
    assert item["match"]["overlay"]["props"]["primary"] == "1500"


def test_build_plan_item_out_of_range_candidate_degrades() -> None:
    """If the LLM hallucinates candidate_idx=99 with only 2 candidates,
    we must NOT crash. We degrade to keyword_highlight."""
    sentence = {"idx": 0, "text": "x", "section": None}
    candidates = [
        {"clip_id": 1, "file_path": "/a.mp4", "start_sec": 0, "end_sec": 1,
         "transcript": "t", "similarity": 0.5},
    ]
    match = {"type": "footage", "candidate_idx": 99, "confidence": 0.8, "reasoning": "?"}
    item = build_plan_item(sentence, candidates, match)
    assert item["match"]["type"] == "motion_graphic"
    assert item["match"]["component"] == "keyword_highlight"
