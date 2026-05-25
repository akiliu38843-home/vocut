"""Unit tests for vocut.render — Pillow runs (cheap), ffmpeg is not exercised."""

from __future__ import annotations

from pathlib import Path

import pytest

from vocut.render import (
    CARD_BACKGROUND,
    DEFAULT_BACKGROUND,
    _hex_to_rgb,
    _max_chars_for_frame,
    _pick_font_path,
    _wrap_text_cjk,
    render_card_png,
)


def test_hex_to_rgb_known_values() -> None:
    assert _hex_to_rgb("#000000") == (0, 0, 0)
    assert _hex_to_rgb("#ffffff") == (255, 255, 255)
    assert _hex_to_rgb("#1a1a1a") == (26, 26, 26)
    assert _hex_to_rgb("0f172a") == (15, 23, 42)  # no leading hash


def test_wrap_text_cjk_breaks_at_punctuation() -> None:
    lines = _wrap_text_cjk("第一句话很长很长很长很长很长很长。第二句话很短。", max_chars=10)
    # Should have broken after the first 。 (which lands past max_chars=10)
    assert len(lines) >= 2


def test_wrap_text_cjk_handles_short_text_in_one_line() -> None:
    lines = _wrap_text_cjk("简短。", max_chars=20)
    assert lines == ["简短。"]


def test_wrap_text_cjk_never_returns_empty() -> None:
    lines = _wrap_text_cjk("x", max_chars=20)
    assert lines == ["x"]


def test_wrap_text_cjk_hard_breaks_long_unpunctuated_text() -> None:
    """Regression: a long sentence with NO punctuation must still get broken
    to prevent visual overflow."""
    text = "这意味着当工程师在写自动驾驶算法时他们不只是在写代码而是在做伦理决策"  # 33 chars, no breaks
    lines = _wrap_text_cjk(text, max_chars=20, hard_overflow=6)
    assert len(lines) >= 2
    for line in lines:
        assert len(line) <= 26  # max_chars + hard_overflow


def test_wrap_text_cjk_retro_breaks_at_last_comma() -> None:
    """When a comma lands well inside the line, the line should break there
    even if no further breakable char follows."""
    text = "这意味着，当工程师在写自动驾驶算法时，他们不只是在写代码——"  # 30 chars, commas at 4, 18
    lines = _wrap_text_cjk(text, max_chars=20, hard_overflow=6)
    assert len(lines) >= 2
    # First line should end at the punctuation, not just hit max_chars
    assert lines[0].endswith("，") or lines[0].endswith("。")


def test_max_chars_for_frame_scales_with_size() -> None:
    assert _max_chars_for_frame(854, 34) >= 15
    assert _max_chars_for_frame(1920, 64) >= _max_chars_for_frame(854, 34) - 5
    assert _max_chars_for_frame(10, 1) >= 10  # floor


def test_pick_font_path_returns_existing_file_or_none() -> None:
    p = _pick_font_path()
    if p is not None:
        assert Path(p).exists()


def test_card_background_palette_includes_all_components() -> None:
    expected = {
        "key_number",
        "pull_quote",
        "title_card",
        "comparison_panel",
        "list_item",
        "keyword_highlight",
    }
    assert expected.issubset(set(CARD_BACKGROUND.keys()))


def test_card_background_default_is_hex() -> None:
    assert DEFAULT_BACKGROUND.startswith("#") and len(DEFAULT_BACKGROUND) == 7


def test_render_card_png_creates_valid_image(tmp_path: Path) -> None:
    out = tmp_path / "card.png"
    p = render_card_png(
        "这是一个测试句子, 用来验证文字卡片能正确画出来.",
        component="pull_quote",
        out_png=out,
        width=640,
        height=360,
    )
    assert p.exists()

    # Verify it's a real PNG of the expected size
    from PIL import Image

    img = Image.open(p)
    assert img.size == (640, 360)
    assert img.mode == "RGB"
