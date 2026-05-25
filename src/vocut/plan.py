"""vocut plan — align a voiceover script to indexed footage clips.

Output: plan.json (see docs/ARCHITECTURE.md for schema).

Pipeline:
  1. parse_script    — split markdown into sentences with section context
  2. embed_sentences — bge-small-zh-v1.5 (same model the index used)
  3. topk_candidates — cosine similarity, top-k clips per sentence
  4. rerank_with_llm — Claude tool-use returns structured match decision
  5. emit plan.json  — supports footage / motion_graphic / hybrid types

Without ANTHROPIC_API_KEY in env, falls back to a heuristic-only mode:
  - cosine top-1 if similarity >= threshold (default 0.5)
  - otherwise heuristic motion-graphic detector by regex
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_LLM_MODEL = os.environ.get("VOCUT_LLM_MODEL", "claude-haiku-4-5-20251001")
DEFAULT_TOPK = 5
DEFAULT_CONFIDENCE_THRESHOLD = 0.6

# Motion-graphic catalog (PoC v1+v2 validated these as the P0 essentials).
MOTION_GRAPHIC_COMPONENTS = {
    "key_number",
    "pull_quote",
    "title_card",
    "comparison_panel",
    "list_item",
    "keyword_highlight",
}


# -----------------------------------------------------------------------------
# Script parsing
# -----------------------------------------------------------------------------

# Sentence-ending punctuation. Chinese punctuation runs flush against text
# without a trailing space; English requires whitespace to avoid mis-splitting
# abbreviations / decimals.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？])|(?<=[.!?])\s+")
LIST_ITEM_PREFIX = re.compile(r"^\d+\.\s+(.+)$")
HEADER_PREFIX = re.compile(r"^(#+)\s+(.+)$")


def parse_script(content: str) -> list[dict[str, Any]]:
    """Split a markdown voiceover script into sentence units.

    Markdown structure conventions:
      - `# title` / `## section` headers set the current section context but
        do NOT themselves emit sentence entries.
      - `> blockquote` lines are skipped (these are metadata / notes).
      - `N. text...` numbered-list prefixes are stripped (markdown wrapping).
      - The remaining text is split on sentence-ending punctuation.

    Each returned sentence carries the active section as context (the LLM
    uses this to pick more appropriate motion-graphic components for headers).
    """
    sentences: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(">"):
            continue

        header_m = HEADER_PREFIX.match(line)
        if header_m:
            current_section = {
                "level": len(header_m.group(1)),
                "title": header_m.group(2).strip(),
            }
            continue

        list_m = LIST_ITEM_PREFIX.match(line)
        text = list_m.group(1) if list_m else line

        for part in SENTENCE_SPLIT_RE.split(text):
            part = part.strip()
            if part:
                sentences.append(
                    {
                        "idx": len(sentences),
                        "text": part,
                        "section": dict(current_section) if current_section else None,
                    }
                )
    return sentences


# -----------------------------------------------------------------------------
# Vector search over the indexed clips
# -----------------------------------------------------------------------------


def load_clips_from_db(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], np.ndarray]:
    """Load every clip + its embedding from the DB.

    Returns (clip_dicts, embedding_matrix_(n,dim)). For zero-clip dbs returns
    an empty list and an empty (0, 0) array.
    """
    rows = conn.execute(
        """SELECT clip_id, file_path, segment_idx, start_sec, end_sec, transcript, embedding
           FROM clips
           WHERE embedding IS NOT NULL"""
    ).fetchall()
    if not rows:
        return [], np.zeros((0, 0), dtype=np.float32)

    clips: list[dict[str, Any]] = []
    vectors: list[np.ndarray] = []
    for clip_id, file_path, seg_idx, start, end, transcript, emb_bytes in rows:
        clips.append(
            {
                "clip_id": clip_id,
                "file_path": file_path,
                "segment_idx": seg_idx,
                "start_sec": start,
                "end_sec": end,
                "transcript": transcript,
            }
        )
        vectors.append(np.frombuffer(emb_bytes, dtype=np.float32))
    return clips, np.stack(vectors, axis=0)


def topk_candidates(
    sentence_vec: np.ndarray,
    clips: list[dict[str, Any]],
    clip_matrix: np.ndarray,
    k: int,
) -> list[dict[str, Any]]:
    """Top-k clips by cosine similarity. Embeddings must be L2-normalized."""
    if clip_matrix.size == 0:
        return []
    sims = clip_matrix @ sentence_vec
    top_idx = np.argsort(-sims)[:k]
    result = []
    for i in top_idx:
        c = dict(clips[int(i)])
        c["similarity"] = float(sims[int(i)])
        result.append(c)
    return result


# -----------------------------------------------------------------------------
# LLM rerank (Claude tool use → structured output)
# -----------------------------------------------------------------------------

LLM_SYSTEM_PROMPT = """You align voiceover script sentences to footage clips for a knowledge video.

For each sentence, choose ONE of:
  - footage:        the clip semantically fits (confidence >= 0.6)
  - motion_graphic: no clip fits well → use a component instead
  - hybrid:         clip works but should carry an animated overlay (e.g. clip + key_number)

Motion-graphic components (pick whichever fits the sentence semantics):
  - key_number       numbers, dates, durations, percentages, version IDs
  - pull_quote       direct quotes, mottos, italicized sayings
  - title_card       section transitions, chapter markers
  - comparison_panel explicit comparisons (A vs B, before vs after, multi-region)
  - list_item        enumerated items ("首先/其次", "第一/第二", "A、B、C")
  - keyword_highlight generic fallback for short emphatic statements

Be honest with confidence. If no candidate is a good match, score it low and pick motion_graphic.
"""

RERANK_TOOL = {
    "name": "select_match",
    "description": "Choose the best footage clip OR a motion-graphic component for this sentence",
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["footage", "motion_graphic", "hybrid"],
                "description": "Which kind of segment to produce",
            },
            "candidate_idx": {
                "type": "integer",
                "minimum": 0,
                "description": "0-indexed into the candidate list (required for footage/hybrid)",
            },
            "component": {
                "type": "string",
                "description": "Motion-graphic component name (required for motion_graphic/hybrid)",
            },
            "props": {
                "type": "object",
                "description": "Component props, e.g. {'primary': '4.2 亿', 'unit': '美元'}",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "reasoning": {
                "type": "string",
                "description": "One-line justification",
            },
        },
        "required": ["type", "confidence", "reasoning"],
    },
}


def rerank_with_llm(
    client,
    sentence: str,
    candidates: list[dict[str, Any]],
    section: dict[str, Any] | None,
    model: str,
) -> dict[str, Any]:
    """One Claude call to pick the best match. Returns the tool input as dict."""
    if not candidates:
        candidates_block = "(no candidate clips — recommend motion_graphic)"
    else:
        lines = []
        for i, c in enumerate(candidates):
            lines.append(
                f"  [{i}] sim={c['similarity']:.2f}  {c['transcript']!r}  "
                f"(file: {Path(c['file_path']).name}, {c['start_sec']:.1f}–{c['end_sec']:.1f}s)"
            )
        candidates_block = "\n".join(lines)

    section_hint = (
        f"Section: {section['title']} (heading level {section['level']})\n"
        if section
        else ""
    )

    user_msg = (
        f"{section_hint}"
        f"Sentence: {sentence!r}\n\n"
        f"Candidate clips:\n{candidates_block}\n\n"
        f"Pick the best match via the select_match tool."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=LLM_SYSTEM_PROMPT,
        tools=[RERANK_TOOL],
        tool_choice={"type": "tool", "name": "select_match"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            return dict(block.input)
    raise RuntimeError("Claude did not return a tool_use block")


# -----------------------------------------------------------------------------
# Heuristic mode (no API key)
# -----------------------------------------------------------------------------

# Cheap detectors. They are NOT meant to replace the LLM — only to keep the
# pipeline executable end-to-end when ANTHROPIC_API_KEY is unset.

NUMBER_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(年|月|日|天|周|小时|分钟|秒|个|人|位|名|万|亿|千|百|"
    r"%|％|美元|元|块|台|场|次|条|个国家|国家|地区|"
    r"年代|世纪|MAU|DAU|百分|"
    r"hours?|minutes?|seconds?|days?|years?|months?|"
    r"million|billion|thousand|percent|countries?|users?)"
)
QUOTE_PATTERN = re.compile(r'[""「][^""」]+[""」]')
VERSUS_PATTERN = re.compile(r"(对比|相比|而|vs\.?\s|VS\.?\s|比起|相对|与.*不同)")
LIST_PATTERN = re.compile(r"(首先|其次|最后|第一|第二|第三|另一|此外|然后)")


def heuristic_motion_graphic(sentence: str, section: dict | None) -> dict[str, Any]:
    """Pick a motion-graphic component by pattern matching."""
    if section and section.get("level") == 1:
        return {
            "type": "motion_graphic",
            "component": "title_card",
            "props": {"title": section["title"]},
            "confidence": 0.85,
            "reasoning": "heuristic: H1 section header",
        }

    q = QUOTE_PATTERN.search(sentence)
    if q:
        return {
            "type": "motion_graphic",
            "component": "pull_quote",
            "props": {"quote": q.group(0).strip("\"“”「」")},
            "confidence": 0.75,
            "reasoning": "heuristic: contains quoted text",
        }

    n = NUMBER_PATTERN.search(sentence)
    if n:
        return {
            "type": "motion_graphic",
            "component": "key_number",
            "props": {"primary": n.group(1), "unit": n.group(2)},
            "confidence": 0.72,
            "reasoning": f"heuristic: contains '{n.group(0)}'",
        }

    if VERSUS_PATTERN.search(sentence):
        return {
            "type": "motion_graphic",
            "component": "comparison_panel",
            "props": {},
            "confidence": 0.65,
            "reasoning": "heuristic: contains comparison marker",
        }

    if LIST_PATTERN.search(sentence):
        return {
            "type": "motion_graphic",
            "component": "list_item",
            "props": {},
            "confidence": 0.60,
            "reasoning": "heuristic: contains list connector",
        }

    return {
        "type": "motion_graphic",
        "component": "keyword_highlight",
        "props": {},
        "confidence": 0.50,
        "reasoning": "heuristic: fallback",
    }


def heuristic_pick(
    sentence: str,
    section: dict | None,
    candidates: list[dict],
    threshold: float,
) -> dict[str, Any]:
    """Top-1 cosine if good enough; else motion-graphic heuristic."""
    if candidates and candidates[0]["similarity"] >= threshold:
        return {
            "type": "footage",
            "candidate_idx": 0,
            "confidence": round(float(candidates[0]["similarity"]), 3),
            "reasoning": f"heuristic: cosine top-1 = {candidates[0]['similarity']:.2f}",
        }
    return heuristic_motion_graphic(sentence, section)


# -----------------------------------------------------------------------------
# Build plan items from match dicts
# -----------------------------------------------------------------------------


def build_plan_item(
    sentence: dict[str, Any],
    candidates: list[dict[str, Any]],
    match: dict[str, Any],
) -> dict[str, Any]:
    """Translate a (sentence, candidates, match) triple into a plan entry."""
    item: dict[str, Any] = {
        "sentence_idx": sentence["idx"],
        "sentence": sentence["text"],
        "section": sentence.get("section"),
        "duration_estimate_sec": None,
    }
    match_type = match.get("type", "motion_graphic")

    if match_type == "footage" or match_type == "hybrid":
        idx = match.get("candidate_idx", 0)
        if idx < 0 or idx >= len(candidates):
            # LLM picked an out-of-range index → degrade to motion_graphic
            return build_plan_item(
                sentence,
                candidates,
                {
                    "type": "motion_graphic",
                    "component": "keyword_highlight",
                    "confidence": 0.3,
                    "reasoning": f"LLM returned out-of-range candidate_idx={idx}, falling back",
                },
            )
        clip = candidates[idx]
        footage_block = {
            "type": "footage",
            "clip_id": clip["clip_id"],
            "source_file": clip["file_path"],
            "start_sec": clip["start_sec"],
            "end_sec": clip["end_sec"],
            "transcript": clip["transcript"],
            "confidence": float(match.get("confidence", 0.0)),
        }
        if match_type == "hybrid":
            item["match"] = {
                "type": "hybrid",
                "primary": footage_block,
                "overlay": {
                    "type": "motion_graphic",
                    "component": match.get("component", "keyword_highlight"),
                    "props": match.get("props", {}),
                },
                "reasoning": match.get("reasoning", ""),
            }
        else:
            item["match"] = {**footage_block, "reasoning": match.get("reasoning", "")}
        item["duration_estimate_sec"] = round(clip["end_sec"] - clip["start_sec"], 2)
    else:
        item["match"] = {
            "type": "motion_graphic",
            "component": match.get("component", "keyword_highlight"),
            "props": match.get("props", {}),
            "confidence": float(match.get("confidence", 0.0)),
            "reasoning": match.get("reasoning", ""),
        }
    return item


# -----------------------------------------------------------------------------
# Top-level orchestrator
# -----------------------------------------------------------------------------


def _load_embedder(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _read_index_meta(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT embed_model, embed_dim FROM files LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    return {"embed_model": row[0], "embed_dim": row[1]}


def _try_load_anthropic_client():
    """Return an Anthropic client if API key is set, else None."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic

        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        return None


def plan(
    script_path: Path,
    db_path: Path,
    output_path: Path,
    *,
    llm_model: str = DEFAULT_LLM_MODEL,
    topk: int = DEFAULT_TOPK,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    use_llm: bool | None = None,
    progress_callback=None,
) -> dict[str, Any]:
    """Generate plan.json. Returns stats dict.

    use_llm=None (default) auto-detects ANTHROPIC_API_KEY.
    """
    sentences = parse_script(script_path.read_text())
    if not sentences:
        raise ValueError(f"no sentences parsed from {script_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        meta = _read_index_meta(conn)
        if meta is None:
            embed_model_name = os.environ.get("VOCUT_EMBED_MODEL", "BAAI/bge-small-zh-v1.5")
            clips, clip_matrix = [], np.zeros((0, 0), dtype=np.float32)
        else:
            embed_model_name = meta["embed_model"]
            clips, clip_matrix = load_clips_from_db(conn)
    finally:
        conn.close()

    client = None
    if use_llm is None:
        client = _try_load_anthropic_client()
    elif use_llm:
        client = _try_load_anthropic_client()
        if client is None:
            raise RuntimeError("use_llm=True but ANTHROPIC_API_KEY not set / anthropic not installed")

    if progress_callback:
        progress_callback({"phase": "load_embedder", "model": embed_model_name})
    embedder = _load_embedder(embed_model_name)

    if progress_callback:
        progress_callback({"phase": "embed_script", "n": len(sentences)})
    sentence_vecs = np.asarray(
        embedder.encode(
            [s["text"] for s in sentences],
            normalize_embeddings=True,
            show_progress_bar=False,
        ),
        dtype=np.float32,
    )

    plan_items: list[dict[str, Any]] = []
    stats_match_types: dict[str, int] = {"footage": 0, "motion_graphic": 0, "hybrid": 0}

    for s, vec in zip(sentences, sentence_vecs):
        candidates = topk_candidates(vec, clips, clip_matrix, k=topk)
        if progress_callback:
            progress_callback(
                {
                    "phase": "match",
                    "i": s["idx"] + 1,
                    "total": len(sentences),
                    "n_candidates": len(candidates),
                }
            )
        if client is not None:
            match = rerank_with_llm(
                client, s["text"], candidates, s.get("section"), llm_model
            )
        else:
            match = heuristic_pick(s["text"], s.get("section"), candidates, confidence_threshold)

        item = build_plan_item(s, candidates, match)
        plan_items.append(item)
        stats_match_types[item["match"]["type"]] += 1

    plan_doc = {
        "meta": {
            "script_path": str(script_path.resolve()),
            "db_path": str(db_path.resolve()),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "embed_model": embed_model_name,
            "llm_model": llm_model if client else None,
            "llm_used": client is not None,
            "confidence_threshold": confidence_threshold,
            "topk": topk,
        },
        "plan": plan_items,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan_doc, indent=2, ensure_ascii=False))

    return {
        "sentences": len(sentences),
        "match_types": stats_match_types,
        "mean_confidence": round(
            float(np.mean([p["match"]["confidence"] for p in plan_items])), 3
        )
        if plan_items
        else 0.0,
        "output": str(output_path.resolve()),
        "llm_used": client is not None,
    }
