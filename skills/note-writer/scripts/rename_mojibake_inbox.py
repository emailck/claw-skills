from __future__ import annotations

import re
from pathlib import Path

from io_utils import print_utf8

INVALID_FILENAME_CHARS = r'<>:"/\\|?*'


def safe_slug(title: str) -> str:
    title = title.strip() or "未命名"
    title = re.sub(r"\s+", "-", title)
    title = "".join(ch for ch in title if ch not in INVALID_FILENAME_CHARS)
    title = title.strip("-.")
    return title or "note"


def guess_prefix(name: str) -> str | None:
    if re.match(r"^\d{4}-\d{2}-\d{2}-\d{4}-", name):
        return name[:16]
    if re.match(r"^\d{4}-\d{2}-\d{2}-", name):
        return name[:11]
    return None


def main() -> int:
    vault = Path(r"D:\Notes\inbox")
    if not vault.exists():
        return 0

    renamed = 0
    for f in list(vault.glob("*.md")):
        if ("�" not in f.name) and ("?" not in f.name):
            continue

        text = f.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"^#\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else "未命名"
        slug = safe_slug(title)

        prefix = guess_prefix(f.name)
        new_name = (prefix + slug + ".md") if prefix else (slug + ".md")
        target = vault / new_name

        if target.exists() and target != f:
            i = 2
            while True:
                cand = target.with_name(f"{target.stem}-{i}{target.suffix}")
                if not cand.exists():
                    target = cand
                    break
                i += 1

        f.rename(target)
        renamed += 1

    print_utf8(f"renamed_files={renamed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
