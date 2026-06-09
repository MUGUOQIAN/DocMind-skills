---
name: docmind
description: "Organize and classify local files by content into 生活/工作 archive folders. Use when the user wants to tidy desktop, clean up Downloads, sort messy files, or says 整理桌面/文件太乱了."
version: 1.0.1
homepage: https://github.com/MUGUOQIAN/DocMind
user-invocable: true
command-dispatch: tool
command-tool: bash
command-arg-mode: raw
metadata: {"openclaw":{"emoji":"📁","homepage":"https://github.com/MUGUOQIAN/DocMind","skillKey":"docmind","os":["win32","darwin","linux"],"requires":{"anyBins":["python","python3"]},"primaryEnv":"DOCMIND_BACKEND_URL","envVars":[{"name":"DOCMIND_BACKEND_URL","required":false,"description":"DocMind API URL"},{"name":"DOCMIND_REPO_ROOT","required":false,"description":"Repo root when skill installed without clone"},{"name":"DOCMIND_USER_ID","required":false,"description":"User id for billing"}]}}
---

# DocMind（OpenClaw）

> 规范 Skill 主文件：`skills/docmind/SKILL.md`。

## `/docmind` 斜杠命令（确定性分发）

Frontmatter 已配置 `command-dispatch: tool`、`command-tool: bash`、`command-arg-mode: raw`。

Bash 工具应执行（将 `<raw-args>` 换为用户在 `/docmind` 后输入的原文）：

```bash
python {baseDir}/scripts/openclaw_dispatch.py <raw-args>
```

| 用户输入 | Bash 命令 |
|----------|-----------|
| `/docmind preview --desktop` | `python {baseDir}/scripts/openclaw_dispatch.py preview --desktop` |
| `/docmind run --folder C:/Users/me/Downloads` | `python {baseDir}/scripts/openclaw_dispatch.py run --folder C:/Users/me/Downloads` |
| `/docmind setup` | `python {baseDir}/scripts/openclaw_dispatch.py setup` |
| `/docmind confirm-structure` | `python {baseDir}/scripts/openclaw_dispatch.py confirm-structure` |
| `/docmind quota` | `python {baseDir}/scripts/openclaw_dispatch.py quota` |
| `/docmind undo --desktop` | `python {baseDir}/scripts/openclaw_dispatch.py undo --desktop` |
| `/docmind search 东方广场 合同` | `python {baseDir}/scripts/openclaw_dispatch.py search --query "东方广场 合同"` |

`openclaw_dispatch.py` 会自动附加 `--user-id`（来自 `DOCMIND_USER_ID`）。

Windows 备选：`powershell -File {baseDir}/scripts/openclaw_dispatch.ps1 <raw-args>`

## 自然语言触发

未使用斜杠命令时，Agent 按 `skills/docmind/SKILL.md` 中「触发场景」「Agent 执行步骤」执行：先 `preview` 确认，再 `run`；文件归档到 `archive_root`，不支持独立语义搜索。

## 参考

- `{baseDir}/references/classification-rules.md`
- `{baseDir}/references/configuration.md`
