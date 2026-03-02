import argparse
import datetime as dt
import os
import re
from pathlib import Path

INVALID_FILENAME_CHARS = r'<>:"/\\|?*'


def slugify(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\s+", "-", title)
    title = title.strip("-.")
    title = "".join(ch for ch in title if ch not in INVALID_FILENAME_CHARS)
    if not title:
        return "note"
    if len(title) > 40:
        return title[:40]
    return title


def pick_tags(text: str, note_type: str) -> list[str]:
    text = text.strip()

    base = []
    if note_type == "copywriting":
        base.append("#文案")
    elif note_type == "daily":
        base.append("#日记")
    else:
        base.append("#笔记")

    # Heuristics: pull a few meaningful tokens
    candidates: list[str] = []

    # Common domain hints
    if re.search(r"Obsidian|黑曜石", text, re.I):
        candidates += ["#Obsidian", "#笔记"]
    if re.search(r"winget|安装", text, re.I):
        candidates += ["#安装", "#Windows"]
    if re.search(r"赚钱|价值|需求|迭代|模型|杠杆", text):
        candidates += ["#赚钱", "#价值", "#需求", "#迭代", "#模型", "#杠杆"]
    if re.search(r"日记|记录|复盘", text):
        candidates += ["#记录", "#复盘"]
    if re.search(r"学习|专注", text):
        candidates += ["#学习", "#专注"]

    # Extract short Chinese phrases as topics
    phrases = re.findall(r"[\u4e00-\u9fff]{2,6}", text)
    for ph in phrases[:30]:
        if ph in {"今天", "所以", "就是", "我们", "你们", "这个", "那个", "因为", "不是", "可以", "需要"}:
            continue
        candidates.append("#" + ph)

    # Deduplicate while preserving order
    seen = set()
    for t in base + candidates:
        if not t.startswith("#"):
            t = "#" + t
        if t in seen:
            continue
        seen.add(t)
        if t in {"#今天", "#感觉", "#一些"}:
            continue
        base.append(t)
        if len(base) >= 7:
            break

    # Pad if needed
    while len(base) < 7:
        base.append(f"#tag{len(base)+1}")

    return base[:7]


def build_content(title: str, body: str, tags: list[str]) -> str:
    title = title.strip() or "未命名"
    body = body.strip()
    kw = "关键词：" + " ".join(tags)

    return "\n".join(
        [
            f"# {title}",
            kw,
            "",
            body,
            "",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=r"D:\\Notes")
    ap.add_argument("--type", choices=["daily", "copywriting", "inbox"], default="inbox")
    ap.add_argument("--title", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--write", action="store_true")

    args = ap.parse_args()

    now = dt.datetime.now()
    date = now.strftime("%Y-%m-%d")
    hhmm = now.strftime("%H%M")

    vault = Path(args.vault)

    if args.type == "daily":
        rel = Path("daily") / f"{date}.md"
    elif args.type == "copywriting":
        rel = Path("topics") / "文案" / f"{date}-{hhmm}-{slugify(args.title)}.md"
    else:
        rel = Path("inbox") / f"{date}-{hhmm}-{slugify(args.title)}.md"

    tags = pick_tags(args.body + "\n" + args.title, args.type)
    content = build_content(args.title, args.body, tags)
    path = vault / rel

    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        # UTF-8 (no BOM)
        path.write_text(content, encoding="utf-8", errors="strict")

    print(str(path))
    print("---")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
