---
name: doubao-chat-relay
description: "Use Chrome Relay to ask Doubao any question (optionally with a Douyin link) and extract Doubao's full reply."
---

# Doubao Chat Relay

## When to use

Use this skill when you want to:
- Ask Doubao (豆包) **any question** in the web UI.
- Get the **full** Doubao answer (not just the first screen).

Optional:
- Include a Douyin/TikTok CN link and ask for analysis (even if the link is app-gated, Doubao can still provide pattern-based analysis).

## Prereqs (one-time)

### 1) Install OpenClaw Browser Relay extension (official)

Run:
- `openclaw browser extension install`
- `openclaw browser extension path`

In Chrome:
- Open `chrome://extensions`
- Enable **Developer mode**
- Click **Load unpacked**
- Select the printed path (typically `C:\Users\<you>\.openclaw\browser\chrome-extension`)

### 2) Connect extension to local gateway

The extension may ask for:
- **WS URL**: `ws://127.0.0.1:18789`
- **Token**: from `C:\Users\<you>\.openclaw\openclaw.json` → `gateway.auth.token`

Safe helper (copy token to clipboard, don’t paste into chat):

```powershell
python -c "import json, pathlib, subprocess; p=pathlib.Path(r'C:\\Users\\<you>\\.openclaw\\openclaw.json'); t=json.loads(p.read_text(encoding='utf-8'))['gateway']['auth']['token']; subprocess.run(['powershell','-NoProfile','-Command', f'Set-Clipboard -Value {json.dumps(t)}'], check=True); print('Gateway token copied to clipboard.')"
```

## Workflow

### Step 1) Attach a clean Chrome tab (start a new chat each run)

- Open `https://www.doubao.com/chat/` in Chrome.
- Log in yourself (the agent should not handle passwords/2FA).
- Click the **OpenClaw Browser Relay** icon and switch the tab to **ON**.
- **Always start a new conversation** to avoid historical messages interfering with extraction:
  - Click the top-left **新对话** button.

### Step 2) Ask Doubao

Prompt template:

> <YOUR_QUESTION>
> 
> 请按以下格式输出，便于我复制：
1) 回复必须是纯文本，无Markdown/无列表符号/无加粗/无引用块
2) 在正文最开始单独一行输出：<<BEGIN>>
3) 在正文最后单独一行输出：<<END>>
4) 正文中不要再出现 <<BEGIN>> 或 <<END>> 字样
5) 不要输出“参考资料/推荐追问/快捷按钮”等额外内容；只输出正文
6) 不要强制逐行输出（保持自然段即可）

Example (Douyin link analysis):

> 请分析这个抖音视频为什么点赞高（从选题、情绪价值、叙事、画面、音乐、文案、受众、互动引导角度）。链接：<DOUYIN_LINK>

### Step 3) Extract the full answer (DOM-first; no OCR)

Goal: extract Doubao’s reply **from the web page itself**, reliably.

1) **Scroll to the bottom** (this matters with virtualized chat lists):
   - Press `End` (preferred), or use `PageDown` until you’re at the bottom.

2) **Read the page text via in-page JS** (preferred):
   - Evaluate `document.body.innerText` and extract the last reply.
   - If you used the `<<BEGIN>>` / `<<END>>` wrapper, extract **between** them.

Reference JS (run via Browser Relay evaluate):

```js
() => {
  const raw = document.body?.innerText || "";
  const begin = "<<BEGIN>>";
  const end = "<<END>>";

  const i = raw.lastIndexOf(begin);
  const j = raw.lastIndexOf(end);

  // Happy path: last wrapped block
  if (i !== -1 && j !== -1 && j > i) {
    return raw.slice(i, j + end.length).trim();
  }

  // Fallback: return tail text so the caller can inspect
  const lines = raw.split(/\n+/).map(s => s.trim()).filter(Boolean);
  return lines.slice(-120).join("\n");
}
```

3) **Only if BEGIN/END is missing**:
   - Re-ask Doubao using the wrapper format, then repeat Step 3.

Notes:
- This approach avoids relying on accessibility-tree snapshots (which can miss content) and avoids OCR entirely.
- If the page is not at the bottom, `innerText` may not include the latest message due to virtualization.

## Guardrails

- Don’t paste `gateway.auth.token` into chat logs.
- Don’t submit passwords / SMS codes / payment info.
- If Doubao cannot open the video link, ask it to analyze based on the title/theme and typical patterns.

## Output

Return (strict):
- Doubao’s full reply text (verbatim)

Notes:
- Do not filter based on “relevance”. If Doubao includes extra sections (e.g., templates, scripts, previous context), include them as part of the extracted reply.
- If the reply is long, extract it in multiple chunks, preserving original order and wording.
