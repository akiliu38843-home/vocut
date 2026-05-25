"""vocut CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_fetch(args: argparse.Namespace) -> int:
    from vocut.fetch import DEFAULT_OUT_DIR, DISCLAIMER, fetch_all, parse_url_input

    urls = parse_url_input(args.input)
    if not urls:
        print("error: no URLs to fetch", file=sys.stderr)
        return 2

    out_dir = Path(args.to) if args.to else DEFAULT_OUT_DIR
    print(f"⚠️  {DISCLAIMER}", file=sys.stderr)

    def progress(event: dict) -> None:
        phase = event.get("phase")
        if phase == "begin":
            print(f"[{event['i']}/{event['total']}] {event['url']}", file=sys.stderr)
        elif phase == "done":
            r = event["result"]
            if r["status"] == "downloaded":
                print(f"  → downloaded: {Path(r['path']).name}", file=sys.stderr)
            elif r["status"] == "skipped":
                print(f"  → skipped (already in archive)", file=sys.stderr)
            else:
                print(f"  → error: {r.get('error','?')[:200]}", file=sys.stderr)

    summary = fetch_all(
        urls=urls,
        out_dir=out_dir,
        force=args.force,
        quiet=not args.verbose,
        progress_callback=progress,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["errors"] == 0 else 1


def _cmd_render(args: argparse.Namespace) -> int:
    from vocut.render import render

    plan_path = Path(args.plan).resolve()
    if not plan_path.exists():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        return 2
    voiceover = Path(args.voiceover).resolve() if args.voiceover else None
    if voiceover and not voiceover.exists():
        print(f"error: voiceover not found: {voiceover}", file=sys.stderr)
        return 2
    out_path = Path(args.out).resolve()

    def progress(event: dict) -> None:
        phase = event.get("phase")
        if phase == "segment":
            print(
                f"  [{event['i']}/{event['total']}] rendering {event['kind']}",
                file=sys.stderr,
            )
        elif phase == "concat":
            print(f"  concatenating {event['n']} segments", file=sys.stderr)
        elif phase == "overlay_voiceover":
            print("  overlaying voiceover audio", file=sys.stderr)

    stats = render(
        plan_path=plan_path,
        out_path=out_path,
        voiceover=voiceover,
        fps=args.fps,
        width=args.width,
        height=args.height,
        card_duration_sec=args.card_duration,
        progress_callback=progress,
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    from vocut.index import db_path_in
    from vocut.plan import DEFAULT_LLM_MODEL, plan

    script_path = Path(args.script).resolve()
    if not script_path.exists():
        print(f"error: script not found: {script_path}", file=sys.stderr)
        return 2

    db_path = Path(args.db).resolve() if args.db else db_path_in(Path.cwd())
    if not db_path.exists():
        print(
            f"error: index db not found: {db_path}\n  run `vocut index <folder>` first",
            file=sys.stderr,
        )
        return 2

    output_path = Path(args.out).resolve() if args.out else Path("plan.json").resolve()
    llm_model = args.llm_model or DEFAULT_LLM_MODEL

    def progress(event: dict) -> None:
        phase = event.get("phase")
        if phase == "load_embedder":
            print(f"  loading embedder: {event['model']}", file=sys.stderr)
        elif phase == "embed_script":
            print(f"  embedding {event['n']} sentences", file=sys.stderr)
        elif phase == "match":
            print(
                f"  [{event['i']}/{event['total']}] matching "
                f"({event['n_candidates']} candidates)",
                file=sys.stderr,
            )

    stats = plan(
        script_path=script_path,
        db_path=db_path,
        output_path=output_path,
        llm_model=llm_model,
        topk=args.topk,
        confidence_threshold=args.threshold,
        use_llm=False if args.no_llm else None,
        progress_callback=progress,
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def _cmd_index(args: argparse.Namespace) -> int:
    from vocut.index import (
        DEFAULT_EMBED_MODEL,
        DEFAULT_WHISPER_MODEL,
        db_path_in,
        get_status,
        index_folder,
    )

    if args.status:
        status = get_status(Path(args.db) if args.db else None)
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    if not args.folder:
        print("error: <folder> required (or use --status to inspect existing index)", file=sys.stderr)
        return 2

    folder = Path(args.folder).resolve()
    db_path = Path(args.db).resolve() if args.db else db_path_in(Path.cwd())

    def progress(event: dict) -> None:
        phase = event.get("phase")
        if phase == "scan":
            print(f"[{event['i']}/{event['total']}] {event['file']}", file=sys.stderr)
        elif phase == "load_whisper":
            print(f"  loading whisper: {event['model']} (downloads on first run)", file=sys.stderr)
        elif phase == "load_embedder":
            print(f"  loading embedder: {event['model']} (downloads on first run)", file=sys.stderr)
        elif phase == "transcribe":
            print(f"  transcribing: {event['file']}", file=sys.stderr)
        elif phase == "embed":
            print(f"  embedding {event['n_segments']} segments", file=sys.stderr)

    stats = index_folder(
        folder=folder,
        db_path=db_path,
        whisper_model_name=args.whisper_model,
        embed_model_name=args.embed_model,
        force=args.force,
        progress_callback=progress,
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def _cmd_not_implemented(args: argparse.Namespace) -> int:
    print(f"vocut {args.command}: not yet implemented (planned for P0.2+)", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vocut",
        description="Voiceover-first long-form video editor.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Scaffold a new vocut project in current directory")

    p_fetch = sub.add_parser(
        "fetch",
        help="Download footage via yt-dlp (requires `pip install vocut[fetch]`)",
    )
    p_fetch.add_argument(
        "input", help="A single URL, or a path to a text file with one URL per line"
    )
    p_fetch.add_argument("--to", help="Output folder (default: ./footage/)")
    p_fetch.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if URL is in the download archive",
    )
    p_fetch.add_argument(
        "-v", "--verbose", action="store_true", help="Show yt-dlp progress output"
    )

    p_index = sub.add_parser("index", help="Index a footage library (transcribe + embed + store)")
    p_index.add_argument("folder", nargs="?", help="Footage folder to scan (recursive)")
    p_index.add_argument("--db", help="Path to index database (default: ./.vocut_index/footage.db)")
    p_index.add_argument(
        "--whisper-model",
        default=None,
        help="faster-whisper model name (default: env VOCUT_WHISPER_MODEL or 'base')",
    )
    p_index.add_argument(
        "--embed-model",
        default=None,
        help="sentence-transformers model (default: env VOCUT_EMBED_MODEL or 'BAAI/bge-small-zh-v1.5')",
    )
    p_index.add_argument(
        "--force", action="store_true", help="Re-index files even if already in database"
    )
    p_index.add_argument(
        "--status",
        action="store_true",
        help="Print stats about existing index; do not index any new files",
    )

    p_plan = sub.add_parser(
        "plan", help="Generate plan.json from voiceover script + indexed library"
    )
    p_plan.add_argument("script", help="Markdown voiceover script")
    p_plan.add_argument("--db", help="Path to index database (default: ./.vocut_index/footage.db)")
    p_plan.add_argument(
        "--out", help="Output path for plan.json (default: ./plan.json)"
    )
    p_plan.add_argument(
        "--llm-model",
        default=None,
        help="Claude model for rerank (default: env VOCUT_LLM_MODEL or claude-haiku-4-5)",
    )
    p_plan.add_argument(
        "--topk", type=int, default=5, help="How many cosine candidates to send to the LLM (default 5)"
    )
    p_plan.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Confidence threshold (heuristic mode only) (default 0.6)",
    )
    p_plan.add_argument(
        "--no-llm",
        action="store_true",
        help="Force heuristic mode even if ANTHROPIC_API_KEY is set",
    )

    p_render = sub.add_parser("render", help="Render plan.json into final mp4")
    p_render.add_argument("plan", help="plan.json from `vocut plan`")
    p_render.add_argument("--out", default="output.mp4", help="Output mp4 path (default: ./output.mp4)")
    p_render.add_argument("--voiceover", help="Voiceover audio (mp3/wav) to overlay")
    p_render.add_argument("--fps", type=int, default=30)
    p_render.add_argument("--width", type=int, default=1280)
    p_render.add_argument("--height", type=int, default=720)
    p_render.add_argument(
        "--card-duration",
        type=float,
        default=4.0,
        help="Seconds per motion-graphic placeholder card (default 4)",
    )
    sub.add_parser("dev", help="Watch mode — re-plan and re-render on script change")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "fetch":
        return _cmd_fetch(args)

    if args.command == "plan":
        return _cmd_plan(args)

    if args.command == "render":
        return _cmd_render(args)

    # Inject defaults for whisper / embed models (so env var can take effect lazily)
    if args.command == "index":
        if args.whisper_model is None:
            from vocut.index import DEFAULT_WHISPER_MODEL

            args.whisper_model = DEFAULT_WHISPER_MODEL
        if args.embed_model is None:
            from vocut.index import DEFAULT_EMBED_MODEL

            args.embed_model = DEFAULT_EMBED_MODEL
        return _cmd_index(args)

    return _cmd_not_implemented(args)


if __name__ == "__main__":
    raise SystemExit(main())
