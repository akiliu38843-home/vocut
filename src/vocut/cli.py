"""vocut CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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

    sub.add_parser("plan", help="Generate plan.json from voiceover script + indexed library")
    sub.add_parser("render", help="Render plan.json into final mp4")
    sub.add_parser("dev", help="Watch mode — re-plan and re-render on script change")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
