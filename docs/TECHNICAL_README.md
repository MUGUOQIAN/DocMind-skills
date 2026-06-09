# DocMind 技术文档

面向开发者与自托管场景。营销版说明见仓库根目录 [README.md](../README.md)。

## 架构

```
[用户本机]  DocMind-skills（本仓库）
    │  本地：读文件、预览、移动、建索引
    │  上传：content_preview（不上传原文件）
    ▼
[云端]  DocMind API（私有部署，FastAPI）
    │  分类（DeepSeek）、计费、额度
    ▼
[DeepSeek API]
```

- **公开仓**：`DocMind-skills` — 客户端 Skill
- **私有仓**：`DocMind` — `backend/`、`deploy/`、`admin_panel/`

## 环境要求

- Python **3.10+**
- `pip install -r requirements.txt`
- 图片 OCR：本机 [Tesseract](https://github.com/tesseract-ocr/tesseract)（可选）
- 可访问的 `DOCMIND_BACKEND_URL`

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DOCMIND_BACKEND_URL` | 是* | 分类/计费 API，默认 `http://127.0.0.1:8000` |
| `DOCMIND_USER_ID` | 否 | 平台用户 ID，默认 `default-user` |
| `DOCMIND_REPO_ROOT` | 否 | 非仓库根运行 CLI 时指向本仓库路径 |
| `DOCMIND_ARCHIVE_ROOT` | 否 | 归档根目录（也可在 setup 中配置） |
| `DOCMIND_TARGET_FOLDER` | 否 | 待整理目录 |

\* 生产环境使用服务商提供的 HTTPS 地址。

用户配置默认路径：`~/.docmind/config.json`

## CLI 命令

```bash
python scripts/docmind.py setup
python scripts/docmind.py preview --desktop --user-id <ID>
python scripts/docmind.py run --desktop --user-id <ID>
python scripts/docmind.py undo --desktop --user-id <ID>
python scripts/docmind.py search --query "关键词" --user-id <ID>
python scripts/docmind.py rebuild-index --archive "<归档根>"
python scripts/docmind.py quota --user-id <ID>
python scripts/docmind.py confirm-structure
python scripts/docmind.py discover-habits
```

## 计费（API 侧）

| 操作 | 免费 | 超出后 | 订阅 |
|------|------|--------|------|
| `preview` / `rebuild-index` | 免费 | — | — |
| `run` | 5 次/月 | ¥2/次 | ¥9.9/月无限 |
| `search` | 20 次/月 | ¥0.05/次 | ¥9.9/月无限 |

API 端点摘要见 [references/api.md](../references/api.md)。

## 自部署 API（私有主仓）

克隆私有 `DocMind` 仓库后：

```bash
cp .env.example .env
# 填入 DEEPSEEK_API_KEY、BILLING_SECRET

cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

客户端指向你的 API：

```bash
export DOCMIND_BACKEND_URL=https://your-api.example.com
```

Docker 与 Nginx 见私有仓 `deploy/`。

## 与营销版差异说明

| 营销表述 | 当前实现 |
|----------|----------|
| 无需配置 API Key | 用户无需 DeepSeek Key；需 `DOCMIND_BACKEND_URL` 连接托管 API |
| 自动监控桌面 | **尚未实现**，规划中 |
| 年度订阅 ¥99 | **尚未上线**，规划中 |
| 语义搜索 | 已实现为 **归档索引搜索**（`search` + `file_index`），非全盘语义向量检索 |

## 发布 Skill

见 [PUBLISH.md](../PUBLISH.md)。

## 同步公开仓

若在 monorepo 内维护 `DocMind-skills/` 副本，可用 `git subtree split` 推送到 `github.com/MUGUOQIAN/DocMind-skills`（详见私有仓 `REPO_SPLIT.md`）。
