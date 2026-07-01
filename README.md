# 🧠 DocMind – 桌面文件智能管家

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-安装-blue)](https://clawhub.ai)
[![WorkBuddy Skill](https://img.shields.io/badge/WorkBuddy-可用-brightgreen)](https://workbuddy.qq.com)
[![GitHub](https://img.shields.io/badge/GitHub-DocMind--skills-181717)](https://github.com/MUGUOQIAN/DocMind-skills)

在本地读懂文件内容，自动归类到「生活 / 工作」目录树；用自然语言搜索已归档文件。分类与计费由 DocMind 云端 API 提供，**用户无需自备 AI API Key**。**新用户免费试用 3 个月**，适合 WorkBuddy / OpenClaw Agent 即装即用。

---

## ✨ 告别手动整理文件夹

- 文件堆满桌面，找不到想要的合同、发票？
- 下载的资料不知道丢在哪？
- 同一项目的图纸、邮件、照片散落各处？

**DocMind 来了。** 它是一个能 **读懂文件内容** 的 AI 助手，帮你分类整理、快速找回。

- 📄 **读取内容** — PDF、Word、Excel、PPT、TXT；图片可 OCR（需本机 [Tesseract](https://github.com/tesseract-ocr/tesseract)）
- 🧠 **智能分类** — 按内容归入 `工作/项目名/图纸`、`生活/财务/银行账单` 等路径
- 🔍 **索引搜索** — 「东方广场 合同」「上个月银行账单」，在已归档文件中快速定位
- 👀 **先预览再执行** — 整理前模拟运行，确认后再移动，支持一键撤销
- ☁️ **连接云服务** — 安装 Skill 或克隆本仓库，配置平台用户 ID 即可使用（API 由服务商托管）

---

## 💰 定价 – 新用户免费试用 3 个月

| 套餐 | 价格 | 适合人群 | 核心权益 |
|------|------|----------|----------|
| **免费试用** | ¥0 | 新用户 / Agent 体验 | **前 3 个月**每月 **5 次整理** + **20 次搜索** |
| **按次** | 整理 ¥2/次<br>搜索 ¥0.05/次 | 试用结束后偶尔使用 | 超出免费额度后按次扣费 |
| **月度订阅** | **¥9.9 / 月** | 高频使用、职场人 | **无限次**整理 + 搜索 |
| **年度订阅** | **¥99 / 年** | 重度用户 | 无限整理+搜索，约 ¥8.3/月 |

> 🎁 **拉新友好**：每个平台用户 ID 首次使用自动开启 3 个月免费试用，无需绑卡，适合 WorkBuddy / OpenClaw Agent 直接安装体验。

- `preview`（预览整理）与 `rebuild-index`（重建索引）**始终免费**（不受试用期限制）
- 一次 `run` = 1 次整理会话（单轮最多约 500 个文件，不按文件另计费）
- 一次 `search` = 1 次查找

查询剩余额度：`python scripts/docmind.py quota --user-id <ID>`

---

## 🚀 功能一览

| 功能 | 免费试用（3 个月） | 订阅版 |
|------|------------------|--------|
| 手动整理（按内容分类） | ✅ 5 次/月 | ✅ 无限 |
| 归档文件索引搜索 | ✅ 20 次/月 | ✅ 无限 |
| 预览整理（不移动文件） | ✅ 免费 | ✅ 免费 |
| 撤销上次整理 | ✅ | ✅ |
| 习惯学习 / 项目名识别 | ✅ | ✅ |
| 确认结构后增量归入 | ✅ | ✅ |
| 自定义行业 / 分类子类 | ✅ | ✅ |
| 图片 OCR | ✅* | ✅* |
| 归档目录监视（`watch` 增量索引） | ✅ | ✅ |
| 自动监视桌面/下载并归类（`monitor`） | ✅ preview 免费 / run 扣整理额度 | ✅ |
| **桌面应用**（macOS / Windows GUI） | ✅ | ✅ |

## 桌面应用（macOS / Windows）

图形界面，无需命令行或 Agent：

```bash
pip install -r requirements.txt -r desktop/requirements.txt
python desktop/main.py
# 或
python scripts/docmind.py gui
```

Windows 安装后双击桌面 **「DocMind 应用」** 快捷方式。详见 [desktop/README.md](desktop/README.md)。

---

## 🛠️ 快速开始（推荐：OpenClaw / WorkBuddy）

1. 打开 **OpenClaw** 或 **腾讯 WorkBuddy**
2. 安装 DocMind Skill（ClawHub 或复制本仓库）
3. 对 Agent 说：**「帮我整理桌面」** 或 **「找一下东方广场的合同」**
4. Agent 会先 **preview** 展示归类方案，你确认后再 **run**

典型对话：

```
用户：我桌面太乱了，帮我整理一下。
Agent：preview → 展示归档路径 → 确认后 run

用户：找一下东方广场的合同。
Agent：search --query "东方广场 合同"
```

> 通过平台安装时，通常只需平台账号与文件夹授权；**无需自行申请 DeepSeek API Key**。

---

## 🪟 Windows 一键安装（无需 Agent）

没有 WorkBuddy / OpenClaw 也能用。适合普通用户整理桌面：

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 Add to PATH）
2. 克隆本仓库后，双击 **`windows\install.bat`**
3. 使用桌面快捷方式：**预览整理桌面** → **执行整理桌面**

详见 [`windows/README.md`](windows/README.md)。

---

## 💻 开发者 / 命令行安装

```bash
git clone https://github.com/MUGUOQIAN/DocMind-skills.git
cd DocMind-skills
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 默认生产 API（本地开发可改为 http://127.0.0.1:8000）
export DOCMIND_BACKEND_URL=https://api.blt3d.cn
export DOCMIND_USER_ID=your-platform-user-id
export DOCMIND_PLATFORM=workbuddy

python scripts/docmind.py setup
python scripts/docmind.py preview --desktop --user-id <ID>
python scripts/docmind.py run --desktop --user-id <ID>
python scripts/docmind.py search --query "东方广场 合同" --user-id <ID>
```

| 平台 | 安装方式 |
|------|----------|
| **OpenClaw** | 克隆本仓库到 skills 目录，或 ClawHub；见 `platforms/openclaw/` |
| **WorkBuddy** | 复制到 `~/.workbuddy/skills/docmind/`；见 `platforms/workbuddy/SKILL.md` |
| **命令行** | 本仓库 `scripts/docmind.py` |

`{baseDir}` = 含 `SKILL.md` 的目录。非仓库根运行时设置 `DOCMIND_REPO_ROOT`。

---

## 📁 仓库结构

```
DocMind-skills/
├── SKILL.md             # Agent 技能说明
├── scripts/docmind.py   # 统一 CLI
├── lib/                 # 本地整理、索引、配置
├── platforms/           # WorkBuddy / OpenClaw / Harmers 入口与 SKILL
├── references/security.md
├── docs/SKILLHUB_LISTING.md
├── references/          # 规则、API、配置说明
├── setup.py             # 首次配置引导
└── requirements.txt
```

---

## 🔧 自托管与技术文档

本仓库为 **公开客户端**（Skill + 本地整理逻辑）。若你希望自己部署 API 服务，请参考主仓私有后端或技术文档：

- [技术文档（安装、API、分拆说明）](docs/TECHNICAL_README.md)
- Agent 技能详解：`SKILL.md`
- 分类规则：`references/classification-rules.md`
- 后端 API：`references/api.md`
- 文件索引：`references/file-index.md`

---

## 📄 许可证

客户端 Skill 包采用 **MIT 许可证**，欢迎学习与贡献。  
DocMind 云端分类 / 计费服务为专有托管能力，使用条款以服务商公示为准。

---

## 🤝 社区与支持

- 🐛 [提交 Issue](https://github.com/MUGUOQIAN/DocMind-skills/issues)
- 📦 公开客户端：[DocMind-skills](https://github.com/MUGUOQIAN/DocMind-skills)
- 🔒 API / 部署主仓（私有）：由项目维护者托管

**Star 🌟 支持我们，让更多人用上 AI 整理！**
