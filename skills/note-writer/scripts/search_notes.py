from __future__ import annotations

import argparse
import re
from pathlib import Path


def iter_md_files(vault: Path) -> list[Path]:
    files: list[Path] = []
    for folder in [vault / "inbox", vault / "daily", vault / "topics"]:
        if not folder.exists():
            continue
        files.extend([p for p in folder.rglob("*.md") if p.is_file()])
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=r"D:\\Notes")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    vault = Path(args.vault)
    q = args.query.strip()
    if not q:
        return 0

    from io_utils import print_utf8

    pattern = re.compile(re.escape(q), re.IGNORECASE)

    hits = 0
    for path in iter_md_files(vault):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if not pattern.search(text):
            continue

        print_utf8(str(path))
        hits += 1
        if hits >= args.limit:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
