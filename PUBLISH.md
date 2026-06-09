# DocMind Skill 发布指南

## 发布包位置

本仓库 **根目录** 即为可发布的 Skill 包：

```
DocMind-skills/           # 仓库根 = Skill 根
├── SKILL.md
├── scripts/docmind.py
├── lib/
├── platforms/
├── references/
└── .clawhubignore
```

## ClawHub

```bash
cd DocMind-skills   # 仓库根
clawhub publish
```

要求：`SKILL.md` frontmatter 完整；包内仅文本文件；≤50MB。计费由云端 API 提供，勿在 frontmatter 写定价。

## OpenClaw

1. 克隆本仓库或复制到 OpenClaw skills 目录
2. 设置 `DOCMIND_BACKEND_URL` 为服务商 API 地址
3. 斜杠命令：`python {baseDir}/scripts/openclaw_dispatch.py …`
4. 平台副本：`platforms/openclaw/SKILL.md`

## WorkBuddy

1. 克隆到 `~/.workbuddy/skills/docmind/`（或软链本仓库）
2. 设置 `DOCMIND_REPO_ROOT`（若非从仓库根运行）
3. 平台副本：`platforms/workbuddy/`（经 `platforms/workbuddy/main.py` 调用）

## 发布前检查

- [ ] `pip install -r requirements.txt`
- [ ] `python scripts/docmind.py setup`
- [ ] `DOCMIND_BACKEND_URL` 指向可用 API
- [ ] `preview` / `search` / `quota` 可运行
