from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'<>:"/\\|?*'


def iso_week(date: dt.date) -> tuple[int, int]:
    y, w, _ = date.isocalendar()
    return y, w


def zh_weekday(date: dt.date) -> str:
    # Monday=0
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[date.weekday()]


def safe_slug(title: str) -> str:
    title = title.strip() or "周报"
    title = re.sub(r"\s+", "-", title)
    title = "".join(ch for ch in title if ch not in INVALID_FILENAME_CHARS)
    title = title.strip("-.")
    return title or "周报"


def default_tags(text: str) -> list[str]:
    # Keep it simple and deterministic.
    tags = ["#周报"]

    # Heuristic tags
    if "鸿蒙" in text:
        tags.append("#鸿蒙")
    if "软卡" in text:
        tags.append("#软卡")
    if re.search(r"SM2|sm2", text):
        tags.append("#SM2")
    if "密管" in text:
        tags.append("#密管")
    if "跨域" in text:
        tags.append("#跨域")

    # Pad to 7
    while len(tags) < 7:
        tags.append(f"#tag{len(tags)+1}")

    return tags[:7]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=r"D:\\Notes")
    ap.add_argument("--date", default="")
    ap.add_argument("--items", nargs="*", default=[])
    ap.add_argument("--title", default="工作周报")
    ap.add_argument("--write", action="store_true")

    args = ap.parse_args()

    date = dt.date.today()
    if args.date:
        date = dt.date.fromisoformat(args.date)

    year, week = iso_week(date)
    weekday = zh_weekday(date)

    folder = Path(args.vault) / "topics" / "周报"
    filename = f"{year}-W{week:02d}-{weekday}.md"
    path = folder / filename

    body_lines = []
    for item in args.items:
        item = item.strip()
        if not item:
            continue
        if item.startswith("-"):
            body_lines.append(item)
        else:
            body_lines.append("- " + item)

    body = "\n".join(body_lines) if body_lines else "- "

    tags = default_tags("\n".join(args.items))
    tags[1] = f"#第{week}周"  # keep week tag stable

    content = "\n".join(
        [
            f"# {safe_slug(args.title)}｜{year}年第{week}周｜{weekday}",
            "关键词：" + " ".join(tags),
            "",
            body,
            "",
        ]
    )

    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    print(str(path))
    print("---")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
