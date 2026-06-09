# DocMind-skills

DocMind **客户端 Skill 包**（公开仓库）。在本地提取文件内容、整理归档、维护索引；分类与计费由云端 API 提供。

> 分类 / 计费 API 为私有化托管服务，请向服务提供方获取 `DOCMIND_BACKEND_URL`。

## 目录结构

```
DocMind-skills/          # 本仓库根目录
├── SKILL.md             # Agent 技能说明（OpenClaw / WorkBuddy / ClawHub）
├── scripts/docmind.py   # 统一 CLI
├── lib/                 # 本地整理、索引、配置
├── platforms/           # 各平台入口（workbuddy / harmers / openclaw）
├── references/          # 规则与 API 说明
├── setup.py             # 首次配置引导
└── requirements.txt
```

## 安装

```bash
git clone https://github.com/MUGUOQIAN/DocMind-skills.git
cd DocMind-skills
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

```bash
# 指向 DocMind 云端 API（由服务商提供）
export DOCMIND_BACKEND_URL=https://api.example.com
export DOCMIND_USER_ID=your-platform-user-id

python scripts/docmind.py setup
```

用户配置写入 `~/.docmind/config.json`（待整理目录、归档根目录等）。

## 常用命令

```bash
python scripts/docmind.py preview --desktop --user-id <ID>
python scripts/docmind.py run --desktop --user-id <ID>
python scripts/docmind.py search --query "东方广场 合同" --user-id <ID>
python scripts/docmind.py quota --user-id <ID>
python scripts/docmind.py confirm-structure
```

## 各平台安装

| 平台 | 方式 |
|------|------|
| **OpenClaw** | 将本仓库克隆到 skills 目录，或安装 `SKILL.md` + `scripts/` |
| **WorkBuddy** | 复制到 `~/.workbuddy/skills/docmind/`（整仓或软链） |
| **ClawHub** | 见 `PUBLISH.md` |

`{baseDir}` = 本仓库根目录（含 `SKILL.md` 的目录）。

若 Skill 安装路径不是仓库根，设置：

```bash
export DOCMIND_REPO_ROOT=/path/to/DocMind-skills
```

## 计费（由云端 API 执行）

| 操作 | 免费额度 | 超出后 | 订阅 |
|------|----------|--------|------|
| `preview` / `rebuild-index` | 免费 | — | — |
| `run` | 5 次/月 | 2 元/次 | 9.9 元/月 |
| `search` | 20 次/月 | 0.05 元/次 | 9.9 元/月 |

## 依赖说明

- **Python 3.10+**
- 图片 OCR 需本机安装 [Tesseract](https://github.com/tesseract-ocr/tesseract)（可选）
- 无需克隆后端仓库；仅需可访问的 `DOCMIND_BACKEND_URL`

## 文档

- Agent 技能：`SKILL.md`
- 分类规则：`references/classification-rules.md`
- 后端 API 摘要：`references/api.md`
- 文件索引：`references/file-index.md`
