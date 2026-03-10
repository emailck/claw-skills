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

    tags: list[str] = []
    if note_type == "copywriting":
        tags.append("#文案")
    elif note_type == "daily":
        tags.append("#日记")
    else:
        tags.append("#笔记")

    candidates: list[str] = []

    domain_rules: list[tuple[str, list[str]]] = [
        (r"Obsidian|黑曜石", ["#Obsidian", "#笔记系统"]),
        (r"winget|安装|卸载|部署", ["#安装", "#Windows"]),
        (r"验证码|打码|captcha|turnstile|hcaptcha|recaptcha", ["#验证码", "#自动化"]),
        (r"Playwright", ["#Playwright"]),
        (r"Tavily", ["#Tavily"]),
        (r"OhMyCaptcha", ["#OhMyCaptcha"]),
        (r"模型", ["#模型"]),
        (r"日记|记录|复盘", ["#记录", "#复盘"]),
        (r"学习|专注", ["#学习", "#专注"]),
    ]

    for pattern, rule_tags in domain_rules:
        if re.search(pattern, text, re.I):
            candidates.extend(rule_tags)

    stop_phrases = {
        "今天", "所以", "就是", "我们", "你们", "这个", "那个", "因为", "不是", "可以", "需要",
        "项目", "相关", "一个", "两个", "一些", "进行", "使用", "支持", "通过", "功能", "内容",
        "判断", "说明", "适合", "场景", "成本", "方案", "服务", "平台", "能力", "流程",
    }

    english_terms = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,30}", text)
    for term in english_terms[:20]:
        lowered = term.lower()
        if lowered in {"linux", "github", "windows", "markdown"}:
            continue
        candidates.append("#" + term)

    phrases = re.findall(r"[\u4e00-\u9fff]{2,8}", text)
    for ph in phrases[:50]:
        if ph in stop_phrases:
            continue
        if ph.startswith("我的") or ph.endswith("一个") or ph.endswith("两个"):
            continue
        candidates.append("#" + ph)

    seen = set()
    final_tags: list[str] = []
    for t in tags + candidates:
        if not t.startswith("#"):
            t = "#" + t
        if t in seen:
            continue
        if t in {"#今天", "#感觉", "#一些", "#一个", "#两个"}:
            continue
        seen.add(t)
        final_tags.append(t)
        if len(final_tags) >= 7:
            break

    while len(final_tags) < 7:
        final_tags.append(f"#tag{len(final_tags)+1}")

    return final_tags[:7]


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
