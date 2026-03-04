import argparse
import datetime as dt
import re
from pathlib import Path

from io_utils import print_utf8

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
    ap.add_argument("--body")
    ap.add_argument("--body-file", help="Read body from a UTF-8 file (recommended on Windows).")
    ap.add_argument("--write", action="store_true")

    args = ap.parse_args()

    if not args.body and not args.body_file:
        ap.error("the following arguments are required: --body (or --body-file)")

    body = args.body or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8", errors="strict")

    now = dt.datetime.now()
    date = now.strftime("%Y-%m-%d")
    hhmm = now.strftime("%H%M")

    vault = Path(args.vault)

    safe = slugify(args.title)
    # Prefix with a stable ASCII slug to avoid mojibake in some terminals/tools.
    fname = f"{date}-{hhmm}-{safe}.md"

    if args.type == "daily":
        rel = Path("daily") / f"{date}.md"
    elif args.type == "copywriting":
        rel = Path("topics") / "文案" / fname
    else:
        rel = Path("inbox") / fname

    tags = pick_tags(body + "\n" + args.title, args.type)
    content = build_content(args.title, body, tags)
    path = vault / rel

    if args.write:
        tmp_root = Path(__file__).resolve().parent.parent / "tmp"
        tmp_root.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_root / fname
        tmp_path.write_text(content, encoding="utf-8", errors="strict")

        from write_note import main as write_note_main

        try:
            write_note_main(
                [
                    "--quiet",
                    "--path",
                    str(path),
                    "--content-file",
                    str(tmp_path),
                ]
            )
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

    print_utf8(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
