---
name: docmind
description: "智能文件整理：按内容归类到生活/工作目录，在已归档文件中快速检索。触发词：整理桌面、文件太乱了、找合同、搜归档、清理下载目录。"
version: 1.6.1
license: MIT
homepage: https://github.com/MUGUOQIAN/DocMind-skills
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash(python:*)
metadata:
  author: MUGUOQIAN
  platform: workbuddy
  category: 文档处理
---

# DocMind（腾讯 WorkBuddy）

> 规范 Skill 主文件：仓库根目录 `SKILL.md` 含完整 SOP；本文件为 WorkBuddy 安装与调用说明。

## 安装

1. 将本仓库复制到 `~/.workbuddy/skills/docmind/`（目录名须为 `docmind`）
2. 安装依赖：

```bash
pip install -r ${CODEBUDDY_SKILL_DIR}/requirements.txt
```

3. 默认 API：`https://api.blt3d.cn`（无需用户自备 AI Key）
4. 用户 ID 自动取自 `DOCMIND_USER_ID` 或 `${CODEBUDDY_SESSION_ID}`

## Agent 调用方式（推荐）

所有子命令经 `workbuddy_dispatch.py` 分发，自动注入 `--user-id` 与 `DOCMIND_PLATFORM=workbuddy`：

```bash
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py preview --desktop
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py run --desktop
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py search --query "东方广场 合同"
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py quota
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py watch --sync-on-start
```

| 用户意图 | 命令 |
|----------|------|
| 整理桌面 | `workbuddy_dispatch.py preview --desktop` → 确认后 `run --desktop` |
| 找已归档文件 | `workbuddy_dispatch.py search --query "<关键词>"` |
| 查剩余额度 | `workbuddy_dispatch.py quota` |
| 保持索引新鲜 | `workbuddy_dispatch.py watch --sync-on-start`（见下文后台运行） |

## 首次配置（非交互）

WorkBuddy Agent 环境无法使用 `input()` 交互引导。首次使用请用环境变量或复制示例配置：

```bash
# 方式 A：环境变量（推荐）
export DOCMIND_INDUSTRY=建筑
export DOCMIND_JOB_TITLE=项目经理
export DOCMIND_TARGET_FOLDER=C:/Users/me/Desktop
export DOCMIND_ARCHIVE_ROOT=C:/Users/me/DocMind归档
export DOCMIND_SKIP_SETUP=1
python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py preview --desktop

# 方式 B：复制 config.example.json 到 ~/.docmind/config.json 后编辑
```

## 索引监视后台运行

`watch` 为长驻进程。Windows 后台示例：

```powershell
Start-Process python -ArgumentList "${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py watch --sync-on-start" -WindowStyle Hidden
```

macOS / Linux：

```bash
nohup python ${CODEBUDDY_SKILL_DIR}/scripts/workbuddy_dispatch.py watch --sync-on-start > ~/.docmind/watch.log 2>&1 &
```

查看状态：`workbuddy_dispatch.py watch-status`

## 平台用户 ID

计费与额度按 `platform_user_id` + `platform=workbuddy` 统计。优先级：

1. 命令行 `--user-id`
2. 环境变量 `DOCMIND_USER_ID`（建议设为腾讯账号或 WorkBuddy 用户标识）
3. `${CODEBUDDY_SESSION_ID}`（会话级回退）

## 完整 SOP

整理流程、检索恢复顺序、计费规则见仓库根目录 `SKILL.md` 与 `references/`。

## 参考

- 配置：`${CODEBUDDY_SKILL_DIR}/references/configuration.md`
- 安全说明：`${CODEBUDDY_SKILL_DIR}/references/security.md`
- SkillHub 上架素材：`${CODEBUDDY_SKILL_DIR}/docs/SKILLHUB_LISTING.md`
