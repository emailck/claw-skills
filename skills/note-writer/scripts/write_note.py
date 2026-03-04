from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--quiet", action="store_true", help="Do not print the final path.")

    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--content", help="Raw content string (hard to pass on Windows).")
    src.add_argument("--content-file", help="Read full content from a UTF-8 text file.")
    src.add_argument("--stdin", action="store_true", help="Read full content from stdin (UTF-8).")

    args = ap.parse_args(argv)

    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8", errors="strict")
    elif args.stdin:
        content = "".join(line for line in __import__("sys").stdin)
    else:
        content = args.content or ""

    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", errors="strict")

    from io_utils import print_utf8

    if not getattr(args, "quiet", False):
        print_utf8(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
