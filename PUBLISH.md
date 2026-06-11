# DocMind Skill 发布指南

## 发布包位置

本仓库 **根目录** 即为可发布的 Skill 包：

```
DocMind-skills/           # 仓库根 = Skill 根
├── SKILL.md
├── scripts/
│   ├── docmind.py
│   ├── workbuddy_dispatch.py
│   └── openclaw_dispatch.py
├── platforms/
│   ├── workbuddy/SKILL.md
│   └── openclaw/SKILL.md
├── lib/
├── references/
│   └── security.md
├── docs/SKILLHUB_LISTING.md
└── .clawhubignore
```

## 生产 API

默认 `DOCMIND_BACKEND_URL=https://api.blt3d.cn`。上架前确认：

```bash
curl -s https://api.blt3d.cn/health
```

本地开发可覆盖：`export DOCMIND_BACKEND_URL=http://127.0.0.1:8000`

## 腾讯 WorkBuddy

### 安装

1. 复制到 `~/.workbuddy/skills/docmind/`（目录名 = frontmatter `name`）
2. `pip install -r requirements.txt`
3. 默认 API 已指向 `https://api.blt3d.cn`，用户无需配置 Key

### 调用

Agent 通过 `scripts/workbuddy_dispatch.py` 分发（自动 `--user-id` + `platform=workbuddy`）。

平台说明：`platforms/workbuddy/SKILL.md`

### 安全自评

| 项 | 结论 |
|----|------|
| 风险等级 | MEDIUM |
| 外网域名 | `api.blt3d.cn` |
| 传输内容 | 文件名 + 文本摘要，不上传原文件 |
| 敏感目录 | 不访问 `~/.ssh` 等 |
| 详情 | `references/security.md` |

上架前建议本地或 ClawHub 运行 **skill-vetter** 扫描并附说明。

## SkillHub（skillhub.cloud.tencent.com）

上架素材见 `docs/SKILLHUB_LISTING.md`。

提交清单：

- [ ] 中文名称、简介、分类标签（文档处理 / 办公效率）
- [ ] `https://api.blt3d.cn/health` 可用
- [ ] `references/security.md` 链接或摘要
- [ ] 截图：整理 preview、search 结果（可选但推荐）
- [ ] 许可证 MIT

审核流程：发布后自动安全扫描 → 管理员审核（通常 24h 内）。

## ClawHub

```bash
cd DocMind-skills   # 仓库根
clawhub publish
```

要求：`SKILL.md` frontmatter 完整；包内仅文本文件；≤50MB。计费由云端 API 提供，勿在 frontmatter 写定价。

## OpenClaw

1. 克隆本仓库或复制到 OpenClaw skills 目录
2. 斜杠命令：`python {baseDir}/scripts/openclaw_dispatch.py …`
3. 平台副本：`platforms/openclaw/SKILL.md`（含 `command-dispatch` frontmatter）

## 发布前检查

- [ ] `pip install -r requirements.txt`
- [ ] `python scripts/workbuddy_dispatch.py quota` 可运行
- [ ] `python scripts/workbuddy_dispatch.py preview --desktop` 可运行（需已配置 `~/.docmind/config.json` 或环境变量）
- [ ] `python scripts/workbuddy_dispatch.py search --query "测试"` 可运行（需已有索引）
- [ ] `curl https://api.blt3d.cn/health` 返回正常
- [ ] skill-vetter 无 EXTREME 项
- [ ] `DOCMIND_PLATFORM` 与分发脚本一致（workbuddy / openclaw）
