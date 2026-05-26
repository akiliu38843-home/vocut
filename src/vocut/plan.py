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

DEFAULT_TOPK = 5
DEFAULT_CONFIDENCE_THRESHOLD = 0.6

# Auto-select a default model. Custom OpenAI-compatible endpoints (uyilink etc.)
# get a sensible GPT-5.x default; Anthropic native gets haiku-4-5.
def _default_llm_model() -> str:
    explicit = os.environ.get("VOCUT_LLM_MODEL")
    if explicit:
        return explicit
    if os.environ.get("VOCUT_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL"):
        return "gpt-5.4-mini"
    if os.environ.get("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    return "claude-haiku-4-5-20251001"


DEFAULT_LLM_MODEL = _default_llm_model()


# -----------------------------------------------------------------------------
# Lottie pool — vendored MIT animations under components/public/lottie/
# -----------------------------------------------------------------------------


def _find_lottie_manifest() -> dict[str, Any]:
    """Locate components/public/lottie/manifest.json. Returns an empty
    {"animations": []} if it can't be found (production builds without the
    Remotion subproject still work — they just won't pick lottie ids)."""
    here = Path(__file__).resolve()
    candidates = [
        Path(os.environ.get("VOCUT_COMPONENTS_DIR", "")) / "public" / "lottie" / "manifest.json",
        Path.cwd() / "components" / "public" / "lottie" / "manifest.json",
    ]
    for i in range(2, min(6, len(here.parents))):
        candidates.append(here.parents[i] / "components" / "public" / "lottie" / "manifest.json")
    for c in candidates:
        try:
            if c and c.exists():
                return json.loads(c.read_text())
        except Exception:
            continue
    return {"animations": []}


_LOTTIE_MANIFEST_CACHE: dict[str, Any] | None = None


def get_lottie_manifest() -> dict[str, Any]:
    """Lazily-loaded cached manifest. Safe to call repeatedly."""
    global _LOTTIE_MANIFEST_CACHE
    if _LOTTIE_MANIFEST_CACHE is None:
        _LOTTIE_MANIFEST_CACHE = _find_lottie_manifest()
    return _LOTTIE_MANIFEST_CACHE


def pick_lottie_id(
    sentence: str,
    seed: int = 0,
    tag: str | None = None,
) -> str:
    """Pick a Lottie animation id from the manifest. Deterministic — same
    inputs always return the same id.

    Strategy:
      1. If `tag` is provided, narrow to animations carrying that tag (LLM
         supplies it via `lottie_tag`).
      2. Within the candidate set, rotate by seed so adjacent lottie scenes
         pick different animations even when they share a tag.
      3. Fall back to the full pool (then to "ripple") if nothing matches.
    """
    manifest = get_lottie_manifest()
    anims = manifest.get("animations", [])
    if not anims:
        return "ripple"  # safe default present in the vendored set

    candidates = anims
    if tag:
        t = tag.lower().strip()
        tagged = [a for a in anims if t in [x.lower() for x in a.get("tags", [])]]
        if tagged:
            candidates = tagged

    idx = seed % len(candidates)
    return candidates[idx]["id"]

# Motion-graphic catalog (PoC v1+v2 validated these as the P0 essentials).
MOTION_GRAPHIC_COMPONENTS = {
    "key_number",
    "pull_quote",
    "title_card",
    "comparison_panel",
    "list_item",
    "keyword_highlight",
    "lottie",  # long-tail fallback: vendored MIT Lottie pool, see components/public/lottie/
}

# -----------------------------------------------------------------------------
# Style direction — auto-assign palette + bg_style per motion-graphic scene
# -----------------------------------------------------------------------------
# Two motion-graphic scenes never share a palette in a row; the same video
# carries a "primary" palette ~60% of the time so it doesn't feel like a slot
# machine. The remaining scenes rotate through the other 7 palettes.

PALETTE_NAMES = [
    "editorial_dark", "cobalt_data", "warm_paper", "gold_on_black",
    "minimal_light", "deep_purple", "verdant", "ink_red",
]

# Which bg styles look right for each component. First entry is preferred.
BG_AFFINITY: dict[str, list[str]] = {
    "title_card":        ["gradient", "solid"],
    "key_number":        ["shader", "particles"],
    "pull_quote":        ["particles", "shader"],
    "comparison_panel":  ["solid", "gradient"],
    "list_item":         ["gradient", "solid"],
    "keyword_highlight": ["particles", "shader"],
}

# Per-component preference for entry motion of the primary text.
TEXT_MOTION_AFFINITY: dict[str, list[str]] = {
    "title_card":        ["scale_in", "fade"],
    "key_number":        ["scale_in", "wave"],
    "pull_quote":        ["typewriter", "fade"],
    "comparison_panel":  ["fade", "scale_in"],
    "list_item":         ["wave", "fade"],
    "keyword_highlight": ["fade", "scale_in"],  # char-modes lose partial highlight
    "lottie":            ["fade", "scale_in"],  # caption over animation
}

# Per-component preference for accent decoration.
ACCENT_FX_AFFINITY: dict[str, list[str]] = {
    "title_card":        ["underline_sweep", "none"],
    "key_number":        ["glow", "burst"],
    "pull_quote":        ["none", "glow"],          # quote mark + italics already
    "comparison_panel":  ["none", "underline_sweep"],
    "list_item":         ["none", "underline_sweep"],
    "keyword_highlight": ["underline_sweep", "glow"],
    "lottie":            ["none", "underline_sweep"], # animation carries energy
}


def _insert_section_title_cards(
    plan_items: list[dict[str, Any]],
    *,
    card_duration_sec: float = 2.5,
) -> list[dict[str, Any]]:
    """Insert a synthetic title_card scene before each unique section header
    encountered in the script.

    Each sentence in plan_items may carry `preceding_headers` (set by
    parse_script). Each header's title becomes a title_card scene if we
    haven't already rendered one for that title. The resulting list keeps
    the original sentences in order, with synthetic cards spliced in.
    """
    result: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for item in plan_items:
        headers = item.get("preceding_headers") or []
        for h in headers:
            title = h.get("title")
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            level = int(h.get("level", 2))
            # H1 gets a longer "intro" card; deeper sections get shorter flashes.
            dur = card_duration_sec * (1.4 if level == 1 else 0.9)
            result.append({
                "sentence_idx": -1,
                "sentence": title,
                "section": dict(h),
                "duration_estimate_sec": round(dur, 2),
                "synthetic": "section_title",
                "match": {
                    "type": "motion_graphic",
                    "component": "title_card",
                    "props": {"title": title},
                    "confidence": 1.0,
                    "reasoning": f"auto-inserted title_card for section (H{level})",
                },
            })
        result.append(item)
    return result


def _assign_motion_styles(
    plan_items: list[dict[str, Any]],
    seed_source: str = "",
) -> dict[str, Any]:
    """Walk plan_items and fill palette + bg_style on each motion-graphic match.

    Rules:
      - Respect any palette / bg_style already present (LLM- or hand-set).
      - Pick a video-level primary palette deterministically from seed_source.
      - Aim for the primary palette to win ~60% of scenes; rotate the other
        palettes for the rest.
      - Never repeat palette or bg_style on directly adjacent scenes.
      - Each component prefers its affinity bg style.

    Returns a small stats dict the caller can fold into plan_doc.meta.
    """
    import hashlib

    h = int(hashlib.sha256(seed_source.encode("utf-8")).hexdigest(), 16)
    primary = PALETTE_NAMES[h % len(PALETTE_NAMES)]
    accents = [p for p in PALETTE_NAMES if p != primary]

    prev_palette: str | None = None
    prev_bg: str | None = None
    prev_motion: str | None = None
    prev_fx: str | None = None
    primary_count = 0
    motion_count = 0
    accent_idx = h % len(accents)  # rotate starting index

    def _pick_affinity(
        candidates: list[str],
        prev: str | None,
        component_seed: int,
    ) -> str:
        """Affinity-first, anti-adjacent, with a deterministic rotation tiebreak."""
        rotated = candidates[component_seed % len(candidates):] + candidates[: component_seed % len(candidates)]
        return next((c for c in rotated if c != prev), rotated[0])

    for i, item in enumerate(plan_items):
        match = item.get("match", {})
        kind = match.get("type")
        # hybrid items style their overlay; motion_graphic styles itself.
        if kind == "motion_graphic":
            target = match
        elif kind == "hybrid" and isinstance(match.get("overlay"), dict):
            target = match["overlay"]
            if target.get("type") != "motion_graphic":
                continue
        else:
            continue

        motion_count += 1
        component = target.get("component", "keyword_highlight")

        # Palette: prefer primary while under the soft cap and no collision
        # with the previous scene; otherwise rotate accents until non-collision.
        primary_cap = max(1, int(round(motion_count * 0.6)))
        if target.get("palette"):
            chosen_palette = target["palette"]
        elif primary != prev_palette and primary_count < primary_cap:
            chosen_palette = primary
            primary_count += 1
        else:
            chosen_palette = accents[accent_idx % len(accents)]
            accent_idx += 1
            while chosen_palette == prev_palette and accents:
                chosen_palette = accents[accent_idx % len(accents)]
                accent_idx += 1

        # bg_style / text_motion / accent_fx: respect existing; otherwise pick
        # via per-component affinity, rotated by a deterministic seed so
        # different scenes pull different affinity entries.
        seed = (h + motion_count * 31) % 7919

        # Lottie supplies its own visual background; bg_style does not apply.
        if component == "lottie":
            chosen_bg = None
            # Pick a Lottie id if the caller didn't specify one. LLM-suggested
            # `lottie_tag` narrows the pool to thematically matching animations.
            if not target.get("props"):
                target["props"] = {}
            if not target["props"].get("lottie_id") and not target["props"].get("lottie_src"):
                target["props"]["lottie_id"] = pick_lottie_id(
                    item.get("sentence", ""),
                    seed=seed,
                    tag=target.get("lottie_tag"),
                )
        elif target.get("bg_style"):
            chosen_bg = target["bg_style"]
        else:
            chosen_bg = _pick_affinity(
                BG_AFFINITY.get(component, ["solid", "gradient", "particles", "shader"]),
                prev_bg, seed,
            )

        if target.get("text_motion"):
            chosen_motion = target["text_motion"]
        else:
            chosen_motion = _pick_affinity(
                TEXT_MOTION_AFFINITY.get(component, ["fade", "scale_in", "wave", "typewriter"]),
                prev_motion, seed + 7,
            )

        if target.get("accent_fx"):
            chosen_fx = target["accent_fx"]
        else:
            chosen_fx = _pick_affinity(
                ACCENT_FX_AFFINITY.get(component, ["none", "glow", "burst", "underline_sweep"]),
                prev_fx, seed + 13,
            )

        target["palette"] = chosen_palette
        if chosen_bg is not None:
            target["bg_style"] = chosen_bg
        target["text_motion"] = chosen_motion
        target["accent_fx"] = chosen_fx
        prev_palette = chosen_palette
        prev_bg = chosen_bg or prev_bg  # don't let lottie reset the anti-adjacent state
        prev_motion = chosen_motion
        prev_fx = chosen_fx

    # Diversity score: unique 4-tuples / motion-graphic scenes. For lottie
    # components, lottie_id stands in for bg_style (it IS the background).
    tuples: set[tuple[str, str, str, str]] = set()
    for item in plan_items:
        m = item.get("match", {})
        if m.get("type") == "motion_graphic":
            t = m
        elif m.get("type") == "hybrid" and isinstance(m.get("overlay"), dict):
            t = m["overlay"]
        else:
            continue
        bg_or_lottie = t.get("bg_style") or (t.get("props") or {}).get("lottie_id")
        if t.get("palette") and bg_or_lottie and t.get("text_motion") and t.get("accent_fx"):
            tuples.add((t["palette"], bg_or_lottie, t["text_motion"], t["accent_fx"]))

    diversity = round(len(tuples) / motion_count, 3) if motion_count else 0.0
    return {
        "primary_palette": primary,
        "motion_scenes": motion_count,
        "primary_usage": primary_count,
        "unique_style_tuples": len(tuples),
        "style_diversity_score": diversity,
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
    pending_headers: list[dict[str, Any]] = []

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
            pending_headers.append(dict(current_section))
            continue

        list_m = LIST_ITEM_PREFIX.match(line)
        text = list_m.group(1) if list_m else line

        for part in SENTENCE_SPLIT_RE.split(text):
            part = part.strip()
            if part:
                entry: dict[str, Any] = {
                    "idx": len(sentences),
                    "text": part,
                    "section": dict(current_section) if current_section else None,
                }
                if pending_headers:
                    entry["preceding_headers"] = pending_headers
                    pending_headers = []
                sentences.append(entry)
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
  - pull_quote       direct quotes, mottos, italicized sayings, maxims,
                     aphorisms, OR any sentence that reads like a quoted
                     truth even when no "" 「」 marks are present
                     (e.g. "X 的 Y，N 成花在你看不见的地方")
  - title_card       section transitions, chapter markers
  - comparison_panel explicit comparisons (A vs B, before vs after, multi-region)
  - list_item        enumerated items ("首先/其次", "第一/第二", "A、B、C")
  - keyword_highlight generic short emphatic statements WITH a clear keyword to highlight
  - lottie           atmospheric / illustrative scene with no specific structural element —
                     a designer-made animation carries the visual, your caption sits on top.
                     Use it for transitional / mood sentences ("镜头转到…", "故事的开端是…",
                     抽象比喻 / 氛围铺垫 / 没有具体数字或列表的过渡句).
                     When picking lottie, also set `lottie_tag` to ONE of these themes
                     so the right animation gets chosen:
                       abstract | data | nature | organic | minimal | particles |
                       lights | festive | celebration | character | scifi | header

Be honest with confidence. If no candidate is a good match AND no structural component
(number/quote/list/comparison) fits, prefer lottie over keyword_highlight for variety.
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
            "lottie_tag": {
                "type": "string",
                "description": (
                    "When component is 'lottie', pick one theme tag from this set: "
                    "abstract, data, nature, organic, minimal, particles, lights, "
                    "festive, celebration, character, scifi, header. "
                    "Ignored for non-lottie components."
                ),
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


def _format_user_msg(
    sentence: str,
    candidates: list[dict[str, Any]],
    section: dict[str, Any] | None,
) -> str:
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

    return (
        f"{section_hint}"
        f"Sentence: {sentence!r}\n\n"
        f"Candidate clips:\n{candidates_block}\n\n"
        f"Pick the best match via the select_match tool."
    )


def rerank_with_anthropic(
    client,
    sentence: str,
    candidates: list[dict[str, Any]],
    section: dict[str, Any] | None,
    model: str,
) -> dict[str, Any]:
    """One Claude call (Anthropic API) to pick the best match."""
    user_msg = _format_user_msg(sentence, candidates, section)
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
    raise RuntimeError("Anthropic did not return a tool_use block")


def rerank_with_openai(
    client,
    sentence: str,
    candidates: list[dict[str, Any]],
    section: dict[str, Any] | None,
    model: str,
) -> dict[str, Any]:
    """One OpenAI-compatible call to pick the best match.

    Uses Chat Completions tools API with tool_choice='required' (forces tool
    use without naming the specific tool — compatible with backends like
    uyilink that don't support `tool_choice: {function: ...}`)."""
    user_msg = _format_user_msg(sentence, candidates, section)
    openai_tool = {
        "type": "function",
        "function": {
            "name": RERANK_TOOL["name"],
            "description": RERANK_TOOL["description"],
            "parameters": RERANK_TOOL["input_schema"],
        },
    }
    response = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        tools=[openai_tool],
        tool_choice="required",
    )
    msg = response.choices[0].message
    if msg.tool_calls:
        return json.loads(msg.tool_calls[0].function.arguments)
    raise RuntimeError("OpenAI-compatible backend did not return a tool_call")


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
    if sentence.get("preceding_headers"):
        item["preceding_headers"] = sentence["preceding_headers"]
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
            overlay = {
                "type": "motion_graphic",
                "component": match.get("component", "keyword_highlight"),
                "props": match.get("props", {}),
            }
            if match.get("component") == "lottie" and match.get("lottie_tag"):
                overlay["lottie_tag"] = match["lottie_tag"]
            item["match"] = {
                "type": "hybrid",
                "primary": footage_block,
                "overlay": overlay,
                "reasoning": match.get("reasoning", ""),
            }
        else:
            item["match"] = {**footage_block, "reasoning": match.get("reasoning", "")}
        item["duration_estimate_sec"] = round(clip["end_sec"] - clip["start_sec"], 2)
    else:
        mg = {
            "type": "motion_graphic",
            "component": match.get("component", "keyword_highlight"),
            "props": match.get("props", {}),
            "confidence": float(match.get("confidence", 0.0)),
            "reasoning": match.get("reasoning", ""),
        }
        if match.get("component") == "lottie" and match.get("lottie_tag"):
            mg["lottie_tag"] = match["lottie_tag"]
        item["match"] = mg
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


def _try_load_llm_client() -> tuple[Any, str] | tuple[None, None]:
    """Return (client, provider_tag) for whichever LLM provider is configured.

    Order of preference:
      1. VOCUT_LLM_BASE_URL + VOCUT_LLM_API_KEY → OpenAI-compatible
         (any third-party gateway: uyilink, deepseek, ollama, vllm, etc.)
      2. OPENAI_API_KEY (+ optional OPENAI_BASE_URL) → OpenAI proper or compat
      3. ANTHROPIC_API_KEY → Anthropic native

    Returns (None, None) if none are configured.
    """
    vocut_base = os.environ.get("VOCUT_LLM_BASE_URL")
    vocut_key = os.environ.get("VOCUT_LLM_API_KEY")
    if vocut_base and vocut_key:
        try:
            import openai

            return openai.OpenAI(api_key=vocut_key, base_url=vocut_base), "openai"
        except ImportError:
            pass

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai

            kwargs = {"api_key": openai_key}
            if os.environ.get("OPENAI_BASE_URL"):
                kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
            return openai.OpenAI(**kwargs), "openai"
        except ImportError:
            pass

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            return anthropic.Anthropic(api_key=anthropic_key), "anthropic"
        except ImportError:
            pass

    return None, None


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

    client, provider = (None, None)
    if use_llm is None:
        client, provider = _try_load_llm_client()
    elif use_llm:
        client, provider = _try_load_llm_client()
        if client is None:
            raise RuntimeError(
                "use_llm=True but no LLM provider configured. Set one of:\n"
                "  - VOCUT_LLM_BASE_URL + VOCUT_LLM_API_KEY (OpenAI-compatible)\n"
                "  - OPENAI_API_KEY (+ optional OPENAI_BASE_URL)\n"
                "  - ANTHROPIC_API_KEY"
            )

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

    # Anti-repeat bookkeeping. A clip should not be reused back-to-back,
    # and its total usage is soft-capped so one filename-fallback-friendly
    # clip can't eat the whole video.
    import math
    n_clips = max(1, len({c["file_path"] for c in clips})) if clips else 1
    max_per_file = max(1, math.ceil(len(sentences) / n_clips * 1.5))
    usage_counts: dict[str, int] = {}
    prev_file_path: str | None = None

    def _shape_candidates(cands: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop clips already at the per-video cap; demote the just-used clip."""
        eligible = [c for c in cands if usage_counts.get(c["file_path"], 0) < max_per_file]
        # If everything's been capped, fall back to the full list (rare).
        eligible = eligible or list(cands)
        if prev_file_path is not None:
            same = [c for c in eligible if c["file_path"] == prev_file_path]
            diff = [c for c in eligible if c["file_path"] != prev_file_path]
            return diff + same  # diff first, prev-clip last
        return eligible

    for s, vec in zip(sentences, sentence_vecs):
        raw_candidates = topk_candidates(vec, clips, clip_matrix, k=topk)
        candidates = _shape_candidates(raw_candidates)
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
            rerank_fn = (
                rerank_with_openai if provider == "openai" else rerank_with_anthropic
            )
            match = rerank_fn(
                client, s["text"], candidates, s.get("section"), llm_model
            )
        else:
            match = heuristic_pick(s["text"], s.get("section"), candidates, confidence_threshold)

        item = build_plan_item(s, candidates, match)
        plan_items.append(item)
        stats_match_types[item["match"]["type"]] += 1

        # Update bookkeeping if the LLM picked footage / hybrid.
        used_file = None
        m = item["match"]
        if m.get("type") == "footage":
            used_file = m.get("source_file")
        elif m.get("type") == "hybrid":
            used_file = (m.get("primary") or {}).get("source_file")
        if used_file:
            usage_counts[used_file] = usage_counts.get(used_file, 0) + 1
            prev_file_path = used_file
        else:
            prev_file_path = None  # motion_graphic-only scene resets the anti-adjacent state

    # Splice in title_card scenes for every section header encountered.
    plan_items = _insert_section_title_cards(plan_items)

    # Auto-assign palette + bg_style on every motion-graphic / hybrid scene.
    style_stats = _assign_motion_styles(plan_items, seed_source=str(script_path.resolve()))

    plan_doc = {
        "meta": {
            "script_path": str(script_path.resolve()),
            "db_path": str(db_path.resolve()),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "embed_model": embed_model_name,
            "llm_model": llm_model if client else None,
            "llm_provider": provider,
            "llm_used": client is not None,
            "confidence_threshold": confidence_threshold,
            "topk": topk,
            "style": style_stats,
        },
        "plan": plan_items,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan_doc, indent=2, ensure_ascii=False))

    # Hybrid matches keep `confidence` under `primary`; flatten for the summary.
    def _conf(m: dict) -> float:
        if "confidence" in m:
            return m["confidence"]
        if "primary" in m and isinstance(m["primary"], dict):
            return m["primary"].get("confidence", 0.0)
        return 0.0

    return {
        "sentences": len(sentences),
        "match_types": stats_match_types,
        "mean_confidence": round(
            float(np.mean([_conf(p["match"]) for p in plan_items])), 3
        )
        if plan_items
        else 0.0,
        "style_diversity_score": style_stats["style_diversity_score"],
        "primary_palette": style_stats["primary_palette"],
        "output": str(output_path.resolve()),
        "llm_used": client is not None,
    }
