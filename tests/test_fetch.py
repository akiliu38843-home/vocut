"""Unit tests for vocut.fetch — no real downloads."""

from __future__ import annotations

from pathlib import Path

from vocut.fetch import parse_url_input, sanitize_filename


def test_parse_single_url() -> None:
    urls = parse_url_input("https://www.youtube.com/watch?v=abc")
    assert urls == ["https://www.youtube.com/watch?v=abc"]


def test_parse_url_file(tmp_path: Path) -> None:
    f = tmp_path / "urls.txt"
    f.write_text(
        "# this is a comment\n"
        "https://www.youtube.com/watch?v=abc\n"
        "\n"
        "https://www.bilibili.com/video/BV123\n"
        "  # indented comment\n"
        "https://example.com/video.mp4\n"
    )
    urls = parse_url_input(str(f))
    assert urls == [
        "https://www.youtube.com/watch?v=abc",
        "https://www.bilibili.com/video/BV123",
        "https://example.com/video.mp4",
    ]


def test_parse_nonexistent_path_treated_as_url() -> None:
    # If the arg doesn't point to a real file, treat it as a literal URL string.
    urls = parse_url_input("https://example.com/some-video")
    assert urls == ["https://example.com/some-video"]


def test_sanitize_drops_filesystem_unsafe_chars() -> None:
    assert sanitize_filename("Hello / World") == "Hello _ World"
    assert sanitize_filename("foo:bar?baz*qux") == "foo_bar_baz_qux"
    assert "\x00" not in sanitize_filename("name\x00with\x01control")


def test_sanitize_collapses_whitespace() -> None:
    assert sanitize_filename("  hello   world  ") == "hello world"


def test_sanitize_truncates_long_titles() -> None:
    long_title = "x" * 500
    assert len(sanitize_filename(long_title)) == 200


def test_sanitize_handles_empty_input() -> None:
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("   ") == "untitled"


def test_fetch_one_missing_ytdlp_returns_error(monkeypatch, tmp_path: Path) -> None:
    """If yt-dlp isn't installed, fetch_one should return a clean error dict
    rather than raising."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yt_dlp":
            raise ImportError("simulated missing yt_dlp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from vocut.fetch import fetch_one

    result = fetch_one("https://example.com/x", out_dir=tmp_path)
    assert result["status"] == "error"
    assert "yt-dlp not installed" in result["error"]
    assert result["url"] == "https://example.com/x"
