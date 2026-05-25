"""vocut fetch — thin wrapper around yt-dlp.

Pure convenience: read URL(s), call yt-dlp, drop files in ./footage/.
No retry magic, no quality heuristics, no per-platform special cases —
yt-dlp handles all of that already.

vocut does not endorse copyright infringement. Users are responsible for
ensuring their downloads comply with platform Terms of Service and
applicable fair-use law.
"""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_OUT_DIR = Path("./footage")
ARCHIVE_FILENAME = ".yt-dlp-archive.txt"

# yt-dlp output template — `.200B` truncates to 200 bytes of UTF-8 (filesystem safe)
DEFAULT_OUTTMPL = "%(title).200B.%(ext)s"

# Prefer mp4-in-mp4 (best video mp4 + best audio m4a → merged mp4). Fall back to
# any best format yt-dlp can produce. We avoid format-string opinions beyond that.
DEFAULT_FORMAT = "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"

DISCLAIMER = (
    "vocut fetch wraps yt-dlp. Respect platform ToS and copyright law; "
    "vocut does not endorse infringement."
)


def parse_url_input(arg: str) -> list[str]:
    """Accept either a single URL or a path to a text file of URLs.

    Text file format: one URL per line; lines starting with `#` and blank
    lines are ignored.
    """
    p = Path(arg)
    if p.exists() and p.is_file():
        urls: list[str] = []
        for raw in p.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
        return urls
    return [arg]


def _resolve_ffmpeg() -> str | None:
    """Find an ffmpeg binary. Prefer imageio-ffmpeg's bundled static binary so
    users don't have to install system ffmpeg.
    """
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None  # fall back to whatever yt-dlp finds on PATH


def _build_opts(out_dir: Path, force: bool, quiet: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(out_dir / DEFAULT_OUTTMPL),
        "format": DEFAULT_FORMAT,
        "merge_output_format": "mp4",
        "no_color": True,
        "no_warnings": quiet,
        "quiet": quiet,
        "noprogress": quiet,
    }
    ffmpeg_path = _resolve_ffmpeg()
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path
    if not force:
        opts["download_archive"] = str(out_dir / ARCHIVE_FILENAME)
    return opts


def _resolve_actual_path(reported_path: str) -> str:
    """yt-dlp may swap extension after merge/convert. Return the file that
    actually exists on disk, preferring container-merged outputs."""
    p = Path(reported_path)
    if p.exists():
        return str(p)
    for ext in ("mp4", "mkv", "webm", "m4a", "mp3"):
        candidate = p.with_suffix(f".{ext}")
        if candidate.exists():
            return str(candidate)
    return reported_path  # gave it our best shot


def fetch_one(url: str, out_dir: Path, force: bool = False, quiet: bool = True) -> dict:
    """Download one URL into out_dir. Returns a result dict.

    status: "downloaded" | "skipped" | "error"
    """
    try:
        import yt_dlp  # imported lazily so vocut.fetch is importable without [fetch] extras
    except ImportError as e:
        return {
            "url": url,
            "status": "error",
            "error": "yt-dlp not installed. Install with: pip install vocut[fetch]",
            "exception": type(e).__name__,
        }

    opts = _build_opts(out_dir, force=force, quiet=quiet)
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            # yt-dlp returns DownloadError("ERROR: ...") even when the file was
            # successfully skipped via download_archive on older versions.
            return {"url": url, "status": "error", "error": msg}

        if info is None:
            return {"url": url, "status": "skipped", "url_normalized": url}

        title = info.get("title")
        duration = info.get("duration")
        reported = ydl.prepare_filename(info)
        return {
            "url": url,
            "status": "downloaded",
            "path": _resolve_actual_path(reported),
            "title": title,
            "duration_sec": duration,
        }


def fetch_all(
    urls: list[str],
    out_dir: Path = DEFAULT_OUT_DIR,
    force: bool = False,
    quiet: bool = True,
    progress_callback=None,
) -> dict:
    """Fetch a list of URLs sequentially. Returns aggregate stats + per-URL results."""
    results: list[dict] = []
    for i, url in enumerate(urls, 1):
        if progress_callback:
            progress_callback({"phase": "begin", "i": i, "total": len(urls), "url": url})
        r = fetch_one(url, out_dir=out_dir, force=force, quiet=quiet)
        results.append(r)
        if progress_callback:
            progress_callback({"phase": "done", "i": i, "total": len(urls), "result": r})

    n_dl = sum(1 for r in results if r["status"] == "downloaded")
    n_skip = sum(1 for r in results if r["status"] == "skipped")
    n_err = sum(1 for r in results if r["status"] == "error")
    return {
        "out_dir": str(out_dir.resolve()),
        "urls_input": len(urls),
        "downloaded": n_dl,
        "skipped": n_skip,
        "errors": n_err,
        "results": results,
    }


def sanitize_filename(title: str) -> str:
    """Public helper: sanitize a title to a filesystem-safe filename.

    yt-dlp already does this internally; we expose it for tests and for any
    future code paths that name files outside yt-dlp.
    """
    cleaned = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "_", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:200] or "untitled"
