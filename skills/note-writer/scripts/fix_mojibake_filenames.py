from __future__ import annotations

import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'<>:"/\\|?*'


def safe_slug(title: str) -> str:
    title = title.strip() or "未命名"
    title = re.sub(r"\s+", "-", title)
    title = "".join(ch for ch in title if ch not in INVALID_FILENAME_CHARS)
    title = title.strip("-.")
    return title or "note"


def main() -> int:
    vault = Path(r"D:\Notes\topics\文案")
    if not vault.exists():
        return 0

    for f in list(vault.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            continue

        m = re.search(r"^#\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else "未命名"

        if "�" not in f.name and "�" not in title:
            continue

        slug = safe_slug(title)

        # Keep existing datetime prefix if present
        new_name = None
        if re.match(r"^\d{4}-\d{2}-\d{2}-\d{4}-", f.name):
            prefix = f.name[:16]  # YYYY-MM-DD-HHMM-
            new_name = prefix + slug + ".md"
        elif re.match(r"^\d{4}-\d{2}-\d{2}-", f.name):
            prefix = f.name[:11]  # YYYY-MM-DD-
            new_name = prefix + slug + ".md"
        else:
            new_name = slug + ".md"

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
        print(f"RENAMED {f.name} -> {target.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
