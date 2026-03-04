from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    args = ap.parse_args()

    path = Path(args.path)
    text = path.read_text(encoding="utf-8", errors="replace")

    from io_utils import print_utf8

    print_utf8(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
