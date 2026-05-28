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
    pack: str | None = None,
) -> str:
    """Pick a Lottie animation id from the manifest. Deterministic — same
    inputs always return the same id.

    Strategy:
      1. Filter by `pack` first (an animation enters consideration when its
         packs list includes the active pack — entries without a packs field
         are treated as universal).
      2. If `tag` is provided, narrow further to animations carrying that tag.
      3. Rotate by seed within the candidate set so adjacent scenes vary.
      4. Fall back to the full pool (then to "ripple") if nothing matches.
    """
    manifest = get_lottie_manifest()
    anims = manifest.get("animations", [])
    if not anims:
        return "ripple"

    pack_name = pack or os.environ.get("VOCUT_STYLE_PACK", DEFAULT_STYLE_PACK)

    def in_pack(a: dict) -> bool:
        packs = a.get("packs")
        return packs is None or pack_name in packs

    candidates = [a for a in anims if in_pack(a)] or list(anims)
    if tag:
        t = tag.lower().strip()
        tagged = [a for a in candidates if t in [x.lower() for x in a.get("tags", [])]]
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

# ─── Style packs ─────────────────────────────────────────────────────────────
# vocut serves two distinct audiences with their own visual languages:
#   - "editorial"  knowledge / commentary creators: restrained, serif, dark.
#   - "anime"      B站 二次元杂谈 creators: kawaii, neon, particle-heavy.
# Each pack ships its own palette roster + per-component affinity tables.
# VOCUT_STYLE_PACK=anime switches the active pack at runtime.

# theme.ts 保留全 16 套 palette 定义（素材库不动）。
# 这里只保留每个 pack 主用的 4 套精选——v0 prompt 的 "3-5 色封顶" 哲学。
# 主用名单越短，整支视频的视觉一致性越强。
PALETTE_NAMES_EDITORIAL = [
    "editorial_dark",  # 默认主调，Claude 风格黑底暖琥珀
    "cobalt_data",     # 数据 / 科技场景
    "warm_paper",      # 编辑 / 引言场景
    "minimal_light",   # 明亮场景（少用）
]
PALETTE_NAMES_ANIME = [
    "sakura",          # 默认主调，樱粉
    "neon_purple",     # 高潮场景，霓虹紫
    "anime_noir",      # 严肃场景，黑金
    "dreamy_pastel",   # 梦境 / 过渡，粉紫
]
# 其他 8 套 (gold_on_black / deep_purple / verdant / ink_red / mikan /
# matcha / navy_white / rose_gold) 仍可在 theme.ts 里被手动 prop 显式指定，
# 但自动分配不再使用它们。

# Editorial: 纯 solid + gradient 两种背景，不再用 shader / particles。
# v0 prompt 第 § Color "不用渐变 / 不用复杂背景" → vocut 编辑模式守这条。
BG_AFFINITY_EDITORIAL: dict[str, list[str]] = {
    "title_card":        ["gradient", "solid"],
    "key_number":        ["solid", "gradient"],
    "pull_quote":        ["gradient", "solid"],
    "comparison_panel":  ["solid", "gradient"],
    "list_item":         ["solid", "gradient"],
    "keyword_highlight": ["gradient", "solid"],
}
# Anime: 二次元杂谈允许一个性格背景 (sakura 樱花 / danmaku 弹幕)，但只在主标题 / 引言
# 等"情绪场景"上用；数据 / 列表保持 solid + gradient 避免干扰阅读。
BG_AFFINITY_ANIME: dict[str, list[str]] = {
    "title_card":        ["sakura", "gradient"],
    "key_number":        ["solid", "gradient"],
    "pull_quote":        ["sakura", "gradient"],
    "comparison_panel":  ["solid", "gradient"],
    "list_item":         ["solid", "gradient"],
    "keyword_highlight": ["sakura", "solid"],
}
# CardBackground.tsx 仍保留 shader / particles / danmaku 6 种 bg 的实现代码
# (素材库不动)，但 plan 自动分配不再选 shader / particles / danmaku 这 3 种除非
# 用户在 plan.json 里手动覆盖。

# 入场动效收敛到 fade + scale_in 两种 (Atlassian Motion "Single focal point"原则)。
# wave / typewriter 在素材库里仍有实现 (TextMotion.tsx 不动)，但 plan 自动分配只用
# fade 和 scale_in 来避免 "每帧一种动效" 的混乱节奏。
TEXT_MOTION_AFFINITY_EDITORIAL: dict[str, list[str]] = {
    "title_card":        ["scale_in", "fade"],
    "key_number":        ["scale_in", "fade"],
    "pull_quote":        ["fade", "scale_in"],
    "comparison_panel":  ["fade", "scale_in"],
    "list_item":         ["fade", "scale_in"],
    "keyword_highlight": ["fade", "scale_in"],
    "lottie":            ["fade", "scale_in"],
}
TEXT_MOTION_AFFINITY_ANIME: dict[str, list[str]] = {
    # Anime 允许 scale_in 多一点（活泼感），但仍不用 wave / typewriter
    "title_card":        ["scale_in", "fade"],
    "key_number":        ["scale_in", "fade"],
    "pull_quote":        ["fade", "scale_in"],
    "comparison_panel":  ["scale_in", "fade"],
    "list_item":         ["fade", "scale_in"],
    "keyword_highlight": ["scale_in", "fade"],
    "lottie":            ["scale_in", "fade"],
}

# AccentFx 极简：默认 none，只在 keyword_highlight 才允许 glow (Refactoring UI
# "less decoration" + Atlassian "single focal point")。burst (取景器角标) 仍在
# AccentFx.tsx 里 (素材库不动)，但 plan 不再自动选——它是手动场景才用的。
ACCENT_FX_AFFINITY_EDITORIAL: dict[str, list[str]] = {
    "title_card":        ["none", "none"],
    "key_number":        ["none", "glow"],
    "pull_quote":        ["none", "none"],
    "comparison_panel":  ["none", "none"],
    "list_item":         ["none", "none"],
    "keyword_highlight": ["glow", "none"],
    "lottie":            ["none", "none"],
}
ACCENT_FX_AFFINITY_ANIME: dict[str, list[str]] = {
    # Anime 比 editorial 稍狂躁，允许 glow 多一点但不用 burst (太抢戏)
    "title_card":        ["glow", "none"],
    "key_number":        ["glow", "none"],
    "pull_quote":        ["none", "glow"],
    "comparison_panel":  ["none", "glow"],
    "list_item":         ["none", "none"],
    "keyword_highlight": ["glow", "none"],
    "lottie":            ["none", "glow"],
}

STYLE_PACKS: dict[str, dict[str, Any]] = {
    "editorial": {
        "palette_names": PALETTE_NAMES_EDITORIAL,
        "bg_affinity": BG_AFFINITY_EDITORIAL,
        "text_motion_affinity": TEXT_MOTION_AFFINITY_EDITORIAL,
        "accent_fx_affinity": ACCENT_FX_AFFINITY_EDITORIAL,
    },
    "anime": {
        "palette_names": PALETTE_NAMES_ANIME,
        "bg_affinity": BG_AFFINITY_ANIME,
        "text_motion_affinity": TEXT_MOTION_AFFINITY_ANIME,
        "accent_fx_affinity": ACCENT_FX_AFFINITY_ANIME,
    },
}

DEFAULT_STYLE_PACK = "editorial"


def _resolve_style_pack() -> dict[str, Any]:
    name = os.environ.get("VOCUT_STYLE_PACK", DEFAULT_STYLE_PACK)
    return STYLE_PACKS.get(name, STYLE_PACKS[DEFAULT_STYLE_PACK])


# Back-compat: legacy code paths read PALETTE_NAMES / BG_AFFINITY / etc directly.
# Keep those names pointing at the editorial pack so existing imports work.
PALETTE_NAMES = PALETTE_NAMES_EDITORIAL
BG_AFFINITY = BG_AFFINITY_EDITORIAL
TEXT_MOTION_AFFINITY = TEXT_MOTION_AFFINITY_EDITORIAL
ACCENT_FX_AFFINITY = ACCENT_FX_AFFINITY_EDITORIAL


# ─── Transitions ────────────────────────────────────────────────────────────
# 转场设计宪法 docs/research/methodology/transitions-charter.md
# vocut 只用 4 种 (其他 14 种 @remotion/transitions presentations 禁用):
#   none      硬切, 0 帧
#   fade      默认转场, 15-20 帧 (0.5-0.67s)
#   slide     章节切换专用, 20-30 帧
#   dissolve  跟 fade 类似, 更柔
TRANSITION_DURATION_FRAMES = {
    "none": 0,
    "fade": 18,
    "slide": 25,
    "dissolve": 18,
}


def _assign_transitions(plan_items: list[dict[str, Any]]) -> dict[str, int]:
    """给每个 scene 加 transition_to_next 字段, 按转场宪法 §6 规则:
      - 当前是 title_card → 接下来用 slide (章节切换感)
      - 下一段是 title_card → 用 slide (准备进章节)
      - 当前是 lottie → fade (温柔过渡)
      - 同类型 footage→footage 衔接 → none (硬切保节奏)
      - 类型差异大 → fade (默认)
    一致性约束:
      - 整支 slide 总次数 ≤ title_card 数量
      - 整支 none 总次数 ≤ 总场景 30%
    最后一个 scene 不带 transition_to_next.
    """
    stats = {"fade": 0, "slide": 0, "none": 0, "dissolve": 0}
    total = len(plan_items)
    title_count = sum(1 for it in plan_items if _scene_kind(it) == "title_card")
    max_none = max(1, int(total * 0.3))

    def _comp(item: dict[str, Any]) -> str:
        m = item.get("match", {})
        if m.get("type") == "motion_graphic":
            return m.get("component", "")
        if m.get("type") == "hybrid" and isinstance(m.get("overlay"), dict):
            return m["overlay"].get("component", "")
        return ""

    for i, item in enumerate(plan_items[:-1]):
        cur_kind = _scene_kind(item)
        next_kind = _scene_kind(plan_items[i + 1])
        cur_comp = _comp(item)
        next_comp = _comp(plan_items[i + 1])

        # 章节切换 → slide
        if cur_comp == "title_card" or next_comp == "title_card":
            chosen = "slide"
        # lottie → fade
        elif cur_comp == "lottie" or next_comp == "lottie":
            chosen = "fade"
        # 同类型连续 footage → 硬切保节奏 (但不超 30%)
        elif cur_kind == "footage" and next_kind == "footage" and stats["none"] < max_none:
            chosen = "none"
        else:
            chosen = "fade"

        item["transition_to_next"] = chosen
        stats[chosen] += 1

    return stats


def _scene_kind(item: dict[str, Any]) -> str:
    """Return one of {footage, motion_graphic, hybrid, title_card}."""
    m = item.get("match", {})
    t = m.get("type", "motion_graphic")
    if t == "motion_graphic" and m.get("component") == "title_card":
        return "title_card"
    return t


def _stamp_scene_metadata(plan_items: list[dict[str, Any]]) -> None:
    """Write scene_idx / total_scenes / section_label / style_pack onto each
    motion-graphic (and hybrid-overlay) target. SceneFrame in the Remotion
    side reads these to render the supervisory text + framing decorations.

    Mutates plan_items in place.
    """
    total = len(plan_items)
    style_pack = os.environ.get("VOCUT_STYLE_PACK", DEFAULT_STYLE_PACK)
    current_section: str | None = None
    for i, item in enumerate(plan_items):
        # Track current section by either preceding_headers or item.section.
        headers = item.get("preceding_headers") or []
        if headers:
            current_section = headers[-1].get("title")
        elif item.get("section"):
            current_section = item["section"].get("title")

        match = item.get("match", {})
        kind = match.get("type")
        if kind == "motion_graphic":
            target = match
        elif kind == "hybrid" and isinstance(match.get("overlay"), dict):
            target = match["overlay"]
        else:
            continue
        target["scene_idx"] = i
        target["total_scenes"] = total
        if current_section:
            target["section_label"] = current_section
        target["style_pack"] = style_pack


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

    pack = _resolve_style_pack()
    palette_names: list[str] = pack["palette_names"]
    bg_affinity: dict[str, list[str]] = pack["bg_affinity"]
    text_motion_affinity: dict[str, list[str]] = pack["text_motion_affinity"]
    accent_fx_affinity: dict[str, list[str]] = pack["accent_fx_affinity"]

    h = int(hashlib.sha256(seed_source.encode("utf-8")).hexdigest(), 16)
    primary = palette_names[h % len(palette_names)]
    accents = [p for p in palette_names if p != primary]

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
                bg_affinity.get(component, ["solid", "gradient", "particles", "shader"]),
                prev_bg, seed,
            )

        if target.get("text_motion"):
            chosen_motion = target["text_motion"]
        else:
            chosen_motion = _pick_affinity(
                text_motion_affinity.get(component, ["fade", "scale_in", "wave", "typewriter"]),
                prev_motion, seed + 7,
            )

        if target.get("accent_fx"):
            chosen_fx = target["accent_fx"]
        else:
            chosen_fx = _pick_affinity(
                accent_fx_affinity.get(component, ["none", "glow", "burst", "underline_sweep"]),
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
        "style_pack": os.environ.get("VOCUT_STYLE_PACK", DEFAULT_STYLE_PACK),
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

LLM_SYSTEM_PROMPT = """你是 vocut 的"视频编辑导演"，把配音稿和素材库映射到一支视频每一帧的设计。

vocut 把视频拆成一连串「场景 (scene)」，每个场景对应配音稿里的一句话。你的工作是
为每一句决定它的视觉形态，遵守下方的硬规则——这些规则提炼自 v0 (Vercel)、Material
Design、IBM Carbon、BBC GEL、Refactoring UI 等开源设计系统的共识。

═══════════════════════════════════════════════════════════════════════════
§ A 场景类型选择 (TYPE)
═══════════════════════════════════════════════════════════════════════════

每个句子三选一：
  - footage         候选 footage 跟句子语义相符 (置信度 ≥ 0.6)
  - motion_graphic  没合适 footage → 用文字 / 图形组件画出来
  - hybrid          footage 半合适，再叠一个文字图形 (例: 数据画面 + key_number 数字)

诚实给 confidence。如果候选都不像，**直接给 motion_graphic**，不要硬挑。

═══════════════════════════════════════════════════════════════════════════
§ B 组件选择 (COMPONENT)
═══════════════════════════════════════════════════════════════════════════

motion_graphic / hybrid 时挑一个组件——按句子的"信息类型"挑，不要凭手感：

  ① key_number        含明确数字 / 日期 / 时长 / 百分比 / 版本号 / 排名
                      → "175 ZB" / "2026 年 Q4" / "47 名" / "60 亿日元" / "前 30"
  ② pull_quote        引用、警句、格言、有引号的话、有"被引用感"的箴言
                      → "AI 不会取代人，但用 AI 的人会"
                      → "精品咖啡的成本，八成花在你看不见的地方"
                      （注意：箴言不一定有"" 「」标点也算）
  ③ title_card        章节过场、阶段标题、章节宣告
                      → 章节切换处由 plan.py 自动插入，你不用主动选这个
  ④ comparison_panel  显式对比 (A vs B、前后、左右、左侧右侧)
                      → "苹果押注端侧，谷歌押注云端"
                      → "公测 vs 当下"
  ⑤ list_item         明确的枚举 ("首先/其次" / "第一/第二" / 顿号分隔的并列项)
                      → "种植、采摘、处理、烘焙、冲煮"
                      → "三个关键趋势..."
  ⑥ keyword_highlight 短句强调，有一个关键词需要高亮
                      → "AI 不会停下来"
                      → "他做到了——单凭一己之力"
  ⑦ lottie            氛围 / 抽象 / 过渡句 (没具体数字、引言、对比、列表)
                      → "故事的开端是..." / "镜头转到一个安静的下午"
                      → "这是一个被忽略了二十年的问题"
                      → 用此组件时**必须**给 lottie_tag (见 § B.7)

§ B.7  lottie_tag 集合（picking lottie 时必填）：
  abstract  data  nature  organic  minimal  particles  lights
  festive   celebration  character  scifi  header

§ B 决策树（按顺序问，第一个 YES 的就是答案）：
  1. 句子里有数字、日期、版本号或排名? → key_number
  2. 句子是引用、警句、有"格言"感? → pull_quote
  3. 句子是 A vs B 的对比? → comparison_panel
  4. 句子是 3 个或更多并列项? → list_item
  5. 句子很短 + 有 1 个关键词值得高亮? → keyword_highlight
  6. 句子是抽象的过渡、氛围、铺垫? → lottie
  7. 都不像 → keyword_highlight（默认兜底）

**禁止**：因为相邻几句都是 lottie 就强行换成 keyword_highlight 凑多样。按句子真实
含义挑，多样性由 vocut 后处理自动调。

═══════════════════════════════════════════════════════════════════════════
§ C 颜色系统 (来自 v0 prompt + WCAG)
═══════════════════════════════════════════════════════════════════════════

**vocut 的 palette 已经预设了** (editorial_dark / cobalt_data / warm_paper /
sakura / neon_purple 等)，你不直接挑颜色。但是你需要理解：

  ① 一支视频每个场景最多 3 个颜色（背景 + 主文字 + 1 accent）
  ② accent 颜色每场景**只用一次**——在主焦点上
  ③ 永远满足 WCAG AA：正文 4.5:1，大字 3:1
  ④ 不用渐变（除非作为微妙的 accent，不能用于主背景）
  ⑤ 不混冷暖（红→青、橘→蓝禁忌组合）

如果你看到 reference 图（vision 提取的），按它的色相提示场景配色。

═══════════════════════════════════════════════════════════════════════════
§ D 排版 (来自 v0 + BBC GEL + Butterick)
═══════════════════════════════════════════════════════════════════════════

vocut 已经预设了字体三件套和字号阶梯，你不直接调字号。但你需要理解：

  ① 主标题 / hero text   = 屏幕高度 9-12% (Vox / Kurzgesagt 行业标准)
  ② 大数字 hero number   = 屏幕高度 14-16% (key_number 主角)
  ③ 引言 / 关键词        = 屏幕高度 5-6%
  ④ 列表项 / 对比项      = 屏幕高度 4-5%
  ⑤ 监督文字 / 标签      = 屏幕高度 1.4-1.6%

**写 props 时尽量短**：
  - title_card 主标题：≤ 15 个汉字 / 30 个拉丁字符
  - pull_quote 引言：≤ 30 个汉字 / 60 个拉丁字符
  - keyword_highlight text：≤ 25 个汉字 (要能在一行内显示)
  - list_item 单项：≤ 12 个汉字
  - key_number primary：≤ 8 个字符（"60 亿日元" / "2026 年" / "175 ZB" / "47 名")
  - key_number unit：1-3 字符 ("ZB" / "亿日元" / "%")
  - **重要**：如果 primary 字段已经包含单位（如 "60 亿日元"），unit 字段就**留空**，
              不要重复

═══════════════════════════════════════════════════════════════════════════
§ E 版式与对齐 (来自 v0 prompt + Refactoring UI)
═══════════════════════════════════════════════════════════════════════════

vocut 组件已经定好了版式，但你要理解一个总原则：

  - 每个场景**单一焦点** (Single focal point)：一个主元素抢眼，其他静默
  - 每个场景**最多 1 个装饰** (除主文字 + 必要 label 外)
  - 留白比装饰更重要 (Refactoring UI 3)
  - 装饰必须锚定具体内容 (不能浮空)

═══════════════════════════════════════════════════════════════════════════
§ F 风格判断框架 (来自 v0 Creative Decision Framework)
═══════════════════════════════════════════════════════════════════════════

根据脚本性质切换创作激进度：

  脚本类型              → 风格策略                  → 建议组件偏好
  ─────────────────────────────────────────────────────────────────
  数据 / 财经 / 科技    → BE CONSERVATIVE          → key_number 多用
                                                    → bg_style: solid > gradient
                                                    → 颜色: cobalt_data / editorial_dark
  ─────────────────────────────────────────────────────────────────
  二次元 / B 站杂谈     → BE EXPERIMENTAL          → keyword_highlight + lottie 多用
                                                    → bg_style: sakura / 渐变
                                                    → 颜色: sakura / neon_purple
  ─────────────────────────────────────────────────────────────────
  知识 / 编辑型         → BE RESPECTFUL            → 7 组件均衡用
                                                    → bg_style: gradient / solid
                                                    → 颜色: warm_paper / editorial_dark
  ─────────────────────────────────────────────────────────────────
  个人 / 创意           → BE BOLD                  → pull_quote + lottie 多用
                                                    → bg_style: shader / particles
                                                    → 颜色: 大胆撞色

  **Final Rule**: Ship something interesting rather than boring, but never ugly.

═══════════════════════════════════════════════════════════════════════════
§ G 反则（绝对不允许）
═══════════════════════════════════════════════════════════════════════════

  ❌ 主文字超 30 汉字 / 60 拉丁字符 (会折行 + 视觉拥堵)
  ❌ key_number primary 含单位时再填 unit (会出 "60 亿日元日元")
  ❌ pull_quote 引用了一个不存在于句子的"被引用对象"（不要瞎编 attribution）
  ❌ comparison_panel 只放 1 个 item (那是 keyword_highlight 的活)
  ❌ list_item items 数量 ≤ 1 (同上)
  ❌ 给 lottie 不给 lottie_tag
  ❌ 凭多样性强行换组件 (按句意挑，多样性后处理自动管)
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
    system_prompt: str | None = None,
) -> dict[str, Any]:
    """One Claude call (Anthropic API) to pick the best match."""
    user_msg = _format_user_msg(sentence, candidates, section)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt or LLM_SYSTEM_PROMPT,
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
    system_prompt: str | None = None,
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
            {"role": "system", "content": system_prompt or LLM_SYSTEM_PROMPT},
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


def describe_visual_reference(image_path: Path, model: str | None = None) -> str | None:
    """Ask a vision LLM to extract a 'design style description' from a reference
    image. The output gets injected into LLM_SYSTEM_PROMPT so plan decisions
    take the reference's vibe into account.

    Modeled on tldraw/make-real's "wireframe → polished HTML" bridge pattern.
    Returns a 3-5 sentence Chinese description or None if anything fails.
    """
    if not image_path.exists():
        return None
    api_key = os.environ.get("VOCUT_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("VOCUT_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return None

    try:
        import base64
        import openai
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        ext = image_path.suffix.lstrip(".").lower() or "jpeg"
        if ext == "jpg":
            ext = "jpeg"
        client = openai.OpenAI(
            api_key=api_key,
            **({"base_url": base_url} if base_url else {}),
        )
        default_model = "gpt-5.4-mini" if (base_url and "openai.com" not in base_url) else "gpt-4o"
        chosen = model or os.environ.get("VOCUT_VISION_MODEL") or default_model
        resp = client.chat.completions.create(
            model=chosen,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": (
                        "你是 vocut 的设计参考分析师。这张图是用户给的'希望视频长成这样'的视觉参考。\n\n"
                        "用 3-5 句中文，给后续的设计决策者一份'风格档案'，覆盖：\n"
                        "1. 主色调（暖 / 冷 / 黑白 / 鲜艳 / 低饱和）\n"
                        "2. 字体风格（衬线 / 无衬线 / 手写 / 厚重 / 纤细）\n"
                        "3. 版式特征（居中 / 左对齐 / 留白多少 / 装饰多少）\n"
                        "4. 整体情绪（编辑感 / 二次元 / 商业 / 创意 / 怀旧）\n"
                        "5. 一句话总结风格定位\n\n"
                        "不要逐字描述图里有什么；提炼**风格特征**就好。"
                    )},
                    {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64}"}},
                ],
            }],
        )
        text = (resp.choices[0].message.content or "").strip()
        return text if text and "NO_CONTENT" not in text else None
    except Exception:
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
    reference_image: Path | None = None,
    progress_callback=None,
) -> dict[str, Any]:
    """Generate plan.json. Returns stats dict.

    use_llm=None (default) auto-detects ANTHROPIC_API_KEY.
    reference_image: optional path to an inspiration image; if given, vocut
    asks a vision LLM to describe its style and injects that description
    into the system prompt so plan decisions align with it.
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

    # 视觉参考接入 (make-real 启发): 用户给了 --reference 图，调 vision LLM
    # 出风格描述，预拼接到 system prompt 前。
    reference_description: str | None = None
    effective_system_prompt = LLM_SYSTEM_PROMPT
    if reference_image and reference_image.exists():
        if progress_callback:
            progress_callback({"phase": "reference_describe", "image": str(reference_image)})
        reference_description = describe_visual_reference(reference_image)
        if reference_description:
            effective_system_prompt = (
                "═══════════════════════════════════════════════════════════════\n"
                "§ R 用户提供的视觉参考 (优先级最高)\n"
                "═══════════════════════════════════════════════════════════════\n\n"
                f"{reference_description}\n\n"
                "**根据这份风格档案调整你的所有决策**：组件选择、置信度、是否选 lottie。"
                "如果场景的内容明显跟参考的氛围不搭, 偏向选择能贴合参考视觉的组件。\n\n"
                "═══════════════════════════════════════════════════════════════\n\n"
                + LLM_SYSTEM_PROMPT
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
                client, s["text"], candidates, s.get("section"), llm_model,
                system_prompt=effective_system_prompt,
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

    # Stamp scene_idx / total_scenes / section_label / style_pack on each
    # motion-graphic target so SceneFrame can render the "01 / 16 — SECTION"
    # monitor text. This must run AFTER title-card insertion (so indices line
    # up with the rendered scene list).
    _stamp_scene_metadata(plan_items)

    # Assign scene-to-scene transitions per the transitions charter
    # (docs/research/methodology/transitions-charter.md).
    transition_stats = _assign_transitions(plan_items)

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
            "transitions": transition_stats,
            "reference_image": str(reference_image.resolve()) if reference_image else None,
            "reference_description": reference_description,
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
