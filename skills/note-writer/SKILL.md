---
name: note-writer
description: Create quick notes and daily journal entries in an Obsidian vault on Windows, and auto-generate searchable keywords/tags. Use when the user asks to write a note, write a diary/journal entry, convert a message into a note, add a keyword line at the top, extract 7 keywords/tags from a note, or save notes into an Obsidian vault folder structure (inbox/daily/topics).
---

# Note Writer (Obsidian / Windows)

## Defaults

- Vault root: `D:\Notes`
- Daily notes: `D:\Notes\daily\YYYY-MM-DD.md`
- Notes folder: `D:\Notes\inbox\`
- Topics folder: `D:\Notes\topics\`
- Weekly reports: `D:\Notes\topics\周报\YYYY-Www-周X.md`
- Keyword line goes directly under the title:
  - `关键词：#...` (exactly 7 tags)

## Workflow

1. Ask for the raw note text (or use the provided text).
2. Determine note type:
   - If it is a dated journal entry → write to `daily/`.
   - Otherwise → write to `inbox/` (unless user provides a topic path).
3. Generate exactly 7 tags.
4. Output:
   - The keyword line
   - A cleaned, readable note (keep the user's tone)
5. If asked to "directly write": save the file to disk using UTF-8.

## Tagging rules (exactly 7)

- Prefer nouns / concrete searchable terms.
- Mix:
  - 3 topical tags (what it is about)
  - 2 action/process tags (what happened / what to do)
  - 2 tool/person/object/context tags
- Avoid filler tags: `#今天` `#感觉` `#一些`.
- Chinese or English is fine; keep tags short.

## Output templates

### Daily note

```
# YYYY-MM-DD
关键词：#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7

## Log
- ...

## Next
- ...
```

### Inbox note

```
# 标题
关键词：#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7

- ...正文...
```

### Weekly report (周报)

```
# 工作周报｜YYYY年第WW周｜周X
关键词：#周报 #第WW周 #tag3 #tag4 #tag5 #tag6 #tag7

- ...
```

## Writing to disk

- Always write as UTF-8.
- Prefer UTF-8 without BOM on Windows (reduces mojibake across tools).
- If `D:\Notes` does not exist, create needed directories.

## Scripts

- Create a note file deterministically: `scripts/new_note.py`
- Write file with UTF-8 (no BOM): `scripts/write_note.ps1`
- Search notes by keywords/tags: `scripts/search_notes.ps1`
- Fix mojibake filenames (rename using first `# Title`): `scripts/rename_from_title.py`
