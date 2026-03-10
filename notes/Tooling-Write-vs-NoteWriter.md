# 写文件：`write` 工具 vs `note-writer` 脚本（Obsidian）
关键词：#OpenClaw #note-writer #write #Obsidian #PowerShell #路径限制 #工作流

## 结论
- `write`（OpenClaw 工具）：适合写入 OpenClaw workspace 内的文件；可能受“不能写出 workspace”的安全限制。
- `note-writer`（技能）：通过本地 PowerShell 脚本写入 `D:\Notes`（Obsidian），不依赖 `write` 工具。

## 为什么我会“经常犯错”
- 很多技能/示例是“直接用 `write` 写文件”，在受限环境里会失败（Path escapes workspace root）。
- `note-writer` 这个技能的设计就是为了解决这个问题：用脚本写到 Obsidian vault。
- 我当时先用 `write`，是因为在确认技能实现之前按通用路径限制做了保守操作；你指出后我立刻改为用脚本写入，并已成功落到 `D:\Notes`。

## `write` 工具（通用）
- 用途：创建/覆盖文件（自动创建父目录）。
- 典型限制：某些运行环境会限制只能在 workspace 内写入，避免误写系统路径或敏感目录。
- 适合：项目文件、配置、临时输出、日志（都在 workspace）。

## `note-writer` 技能（Obsidian）
- 用途：把整理后的笔记写入 Obsidian vault（默认 `D:\Notes`）。
- 实现：运行 `skills/note-writer/scripts/write_note.ps1`，参数为 `-Path` 和 `-Content`。
- 特点：
  - 直接写 `D:\Notes\...`
  - UTF-8（无 BOM）
  - 自动创建目录

## 建议的工作流（以后避免踩坑）
1) 目标是 Obsidian 笔记 → 优先用 `note-writer`（脚本写入）。
2) 目标是 OpenClaw 工作区文件 → 用 `write`。
3) 如果不确定路径是否会被限制 → 先用 `Test-Path`/`Get-Item` 或先写到 workspace 再复制。
