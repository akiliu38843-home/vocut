"""vocut CLI entry point — skeleton only. Real implementation comes in P0."""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vocut",
        description="Voiceover-first long-form video editor.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Scaffold a new vocut project in current directory")
    sub.add_parser("index", help="Index a footage library (transcribe + tag + embed)")
    sub.add_parser("plan", help="Generate plan.json from voiceover script + indexed library")
    sub.add_parser("render", help="Render plan.json into final mp4")
    sub.add_parser("dev", help="Watch mode — re-plan and re-render on script change")

    args = parser.parse_args(argv)
    print(f"vocut {args.command}: not yet implemented (P0 milestone)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
