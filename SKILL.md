---
name: docmind
description: "Organize and classify local files by content into 生活/工作 archive folders; search archived files via file index. Use when the user wants to tidy desktop, clean up Downloads, sort messy files, says 整理桌面/文件太乱了, asks to preview or run organization, or wants to find/search/locate already archived files (找文件/合同在哪/搜一下归档)."
version: 1.5.0
homepage: https://github.com/MUGUOQIAN/DocMind-skills
user-invocable: true
allowed-tools: Read, Write, Bash, Glob, Grep
command-dispatch: tool
command-tool: bash
command-arg-mode: raw
metadata:
  openclaw:
    emoji: "📁"
    homepage: https://github.com/MUGUOQIAN/DocMind-skills
    os:
      - win32
      - darwin
      - linux
    requires:
      anyBins:
        - python
        - python3
    primaryEnv: DOCMIND_BACKEND_URL
    envVars:
      - name: DOCMIND_BACKEND_URL
        required: false
        description: Classify/billing API base URL. Default http://127.0.0.1:8000
      - name: DOCMIND_REPO_ROOT
        required: false
        description: DocMind-skills repo root when Skill is not run from clone directory.
      - name: DOCMIND_USER_ID
        required: false
        description: Platform user id for quota and billing. Default default-user.
      - name: DOCMIND_INDUSTRY
        required: false
        description: User industry for assisted classification.
      - name: DOCMIND_JOB_TITLE
        required: false
        description: User job title for assisted classification.
      - name: DOCMIND_TARGET_FOLDER
        required: false
        description: Folder to organize.
      - name: DOCMIND_ARCHIVE_ROOT
        required: false
        description: Archive destination root.
    install:
      - kind: uv
        package: httpx
        bins: []
---

# DocMind — 智能文件整理

按文件**内容**（PDF、Office、图片 OCR 等）归类到 `生活` / `工作` / `应用快捷方式` 目录树。文件从**待整理目录**移动到 **`archive_root` 归档根目录**（不是留在源文件夹下建子目录）。分类请求发往 DocMind 计费后端。

## 触发场景

当用户需求包含以下意图时，**优先使用本 Skill**：

- 整理、分类、清理指定文件夹（桌面、下载目录、项目散落文件）
- 「帮我把桌面文件整理一下」「文件太乱了」
- 预览整理结果、确认后再正式移动
- 撤销上一次整理、确认归档结构、查询额度
- **在已整理归档中查找文件**（文件索引检索，见下文专节）
- 「找一下某某合同」「之前整理的文件在哪」「搜归档里的账单」

## 文件索引检索（Agent 可调用技能）

在**已通过 DocMind 整理或预览**的归档目录中，按关键词快速查找文件。Agent **必须优先使用本技能**，不要用 `Glob`/`Grep` 全盘扫描代替（对已归档文件）。

### 索引如何产生

| 时机 | 行为 |
|------|------|
| `preview` | 写入索引，`preview_only: true`（计划路径，文件尚未移动） |
| `run` | 更新索引，`exists: true`（文件已归档） |
| `undo` | 从索引移除对应条目 |
| `rebuild-index` | 扫描归档目录重建（修复缺失索引或补全摘要） |

索引文件位置：

- `<archive_root>/.docmind/file_index.json` — 机器读（`search` 使用）
- `<archive_root>/.docmind/file_index.md` — 人类/Agent 可读表格
- `~/.docmind/file_index.json` — 全局汇总（未指定 `--archive` 时搜索）

每条记录字段：`filename`、`path`（完整路径）、`target_path`（如 `工作/东方广场改造/图纸`）、`content_snippet`（内容摘要）、`score`（仅 search 输出）。

### Agent 执行 SOP（查找文件）

1. **判断意图**：用户要找的是**已归档**文件 → 走本流程；若要整理新文件 → 走「整理」流程（preview → run）。
2. **确定归档根** `archive_root`：
   - 读取 `~/.docmind/config.json` 的 `archive_root`
   - 或环境变量 `DOCMIND_ARCHIVE_ROOT`
   - 用户明确指定路径时使用 `--archive`
   - 多个归档且用户未说明 → 先不带 `--archive` 全局搜，或反问归档位置
3. **执行搜索**（首选；每次扣 1 次查找额度，需 `--user-id` 与后端在线）：

```bash
python {baseDir}/scripts/docmind.py search --query "东方广场 合同" --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py search --query "银行账单" --archive "C:/Users/me/DocMind归档" --user-id <ID>
python {baseDir}/scripts/docmind.py search --query "发票" --limit 10 --user-id <ID>
```

4. **解析 JSON 输出**（stdout）：

```json
{
  "query": "东方广场 合同",
  "count": 1,
  "results": [
    {
      "filename": "东方广场改造项目合同.txt",
      "path": "C:/Users/me/DocMind归档/工作/东方广场改造/业务往来/东方广场改造项目合同.txt",
      "target_path": "工作/东方广场改造/业务往来",
      "content_snippet": "项目名称：东方广场改造…",
      "score": 50
    }
  ],
  "index_paths": { "json": "...", "markdown": "..." },
  "billing": {
    "billing_type": "free",
    "free_search_remaining": 19,
    "search_credits": 0
  }
}
```

5. **向用户汇报**：列出 `count`、每条结果的**文件名**、**分类路径** `target_path`、**完整路径** `path`；可引用 `content_snippet` 说明匹配原因。按 `score` 从高到低展示。若 `billing.billing_type` 为 `free`，可提示本月剩余免费查找次数。
6. **`count` 为 0 时的恢复顺序**（依次尝试，并向用户说明）：
   - 换更短或更具体的关键词（如「东方广场」→「合同」）
   - 指定 `--archive` 若之前未指定
   - Read `<archive_root>/.docmind/file_index.md` 人工浏览
   - 若索引文件不存在或明显过旧：`rebuild-index`（会扫描磁盘提取摘要，较慢）

```bash
python {baseDir}/scripts/docmind.py rebuild-index --archive "C:/Users/me/DocMind归档"
```

   重建后再次 `search`。
7. **HTTP 402 / `payment_required`**：本月免费 20 次查找已用完，提示订阅（9.9 元/月）或购买查找次数（0.05 元/次）；可用 `quota` 查询剩余额度。
8. **仍无结果**：说明该文件可能从未被 DocMind 整理进该归档；建议对源目录（桌面/下载）执行 `preview` 再 `run`，或请用户提供更多线索（大致日期、文件类型）。

### OpenClaw 斜杠命令（检索）

```bash
python {baseDir}/scripts/openclaw_dispatch.py search --query "东方广场 合同"
python {baseDir}/scripts/openclaw_dispatch.py rebuild-index --archive "C:/Users/me/DocMind归档"
```

示例：`/docmind search 东方广场 合同`

### 检索对话示例

**用户**：「找一下东方广场的合同。」

**Agent**：

1. `python {baseDir}/scripts/docmind.py search --query "东方广场 合同"`
2. 若 `count >= 1`：回复「找到 N 个文件」，列出路径
3. 若 `count == 0`：检查 config 中 `archive_root` → 带 `--archive` 重试 → 必要时 `rebuild-index` 后再搜

**用户**：「我上个月整理的银行账单在哪？」

**Agent**：

1. `search --query "银行账单"`
2. 结合 `indexed_at` 与 `content_snippet` 筛选最相关条目
3. 给出完整路径，询问是否需要打开文件夹或进一步整理

**用户**：「帮我看看归档里有没有发票。」

**Agent**：

1. 先 `search --query "发票"`
2. 结果过多时用 `search --query "发票 2025"` 或 `--limit 5` 缩小范围
3. 可选 Read `file_index.md` 补充上下文

## Agent 执行步骤

1. **确定待整理目录**（`target_folder` / `--folder` / `--desktop`）：
   - 用户指定路径（如「整理 `C:/Users/me/Downloads`」）→ 使用 `--folder "<路径>"`
   - 用户说「整理桌面」→ 使用 `--desktop`
   - 无法确定 → 反问：「请问您想整理哪个文件夹？（例如：桌面、下载目录）」

2. **首次使用检查配置**：
   - 若无 `~/.docmind/config.json`，先执行 `setup`（含可选习惯学习）

3. **内容分析与预览**（必须先做）：
   - 运行 `preview`（不移动文件）
   - 对每个文件：本地提取内容预览 → 后端 AI 分类 → 返回 `target_path` 与 `destination`
   - 向用户展示将要移动到的归档路径列表，等待确认
   - PDF / 大文件可能较慢，告知用户耐心等待

4. **执行整理**（用户确认后）：
   - 运行 `run`，将文件移动到 `archive_root` 下对应目录（如 `工作/东方广场改造/图纸/`）
   - 无法识别的文件 → `其他/未分类`

5. **后续与反馈**：
   - 报告结果，例如：「整理完成，共处理 N 个文件，已归档到 `<archive_root>`；索引已写入 `.docmind/file_index.md`。」
   - 用户对目录满意后，可执行 `confirm-structure`，此后整理优先归入已有文件夹
   - 误操作可用 `undo`（仅撤销上一次非预览整理，并同步更新索引）

6. **查找已归档文件**：
   - 执行「文件索引检索」SOP：`search` → 解析 JSON → 汇报路径
   - 每次 `search` 扣 **1 次查找额度**（免费 20 次/月；超出 0.05 元/次）
   - `rebuild-index` 免费；浏览备选 Read `file_index.md`
   - **不消耗**整理会话额度，但需后端在线以扣减查找额度

## 对话示例

**用户**：「我桌面太乱了，帮我整理一下。」

**Agent**：

1. `python {baseDir}/scripts/docmind.py preview --desktop --user-id <ID>`
2. 展示预览结果，询问是否执行
3. 用户确认后：`python {baseDir}/scripts/docmind.py run --desktop --user-id <ID>`

## 前置条件

1. **Python 3.10+** 与 `httpx`（`pip install httpx`）
2. **整理类命令**（`preview` / `run` / `quota`）需 **DocMind 后端**（默认 `http://127.0.0.1:8000/health`）
3. **`search`** 需后端在线以扣减查找额度；**`rebuild-index`** 仅需本地 Python
4. **仓库**：克隆 [DocMind-skills](https://github.com/MUGUOQIAN/DocMind-skills)；非仓库根运行时时设 `DOCMIND_REPO_ROOT`

## OpenClaw 斜杠命令（`/docmind`）

```bash
python {baseDir}/scripts/openclaw_dispatch.py <raw-args>
```

示例：

- `/docmind preview --desktop`
- `/docmind search 东方广场 合同`
- `/docmind rebuild-index --archive "C:/Users/me/DocMind归档"`

Windows：`powershell -File {baseDir}/scripts/openclaw_dispatch.ps1 preview --desktop`

## 统一 CLI

Skill 目录：`{baseDir}`

```bash
python {baseDir}/scripts/docmind.py setup
python {baseDir}/scripts/docmind.py preview --desktop --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py preview --folder "C:/Users/me/Downloads" --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py run --desktop --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py undo --folder "C:/Users/me/Desktop" --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py discover-habits
python {baseDir}/scripts/docmind.py confirm-structure
python {baseDir}/scripts/docmind.py quota --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py search --query "东方广场 合同"
python {baseDir}/scripts/docmind.py rebuild-index --archive "C:/Users/me/DocMind归档"
```

## 归档路径示例

- `工作/办公/会议记录`
- `工作/技术资料/设计规范`
- `工作/东方广场改造/图纸`
- `生活/财务/银行账单`
- `生活/日常/家庭照片`
- `应用快捷方式`
- `其他/未分类`

## 注意事项

- **必须先 `preview`，用户确认后再 `run`**，禁止跳过预览直接移动
- 文件移动到 **`archive_root`**，不要在源目录下随意创建 `./合同/` 等自定义结构（除非该结构在归档规则内）
- 分类遵循 `生活/工作` 规则树，不是完全自由的文件夹命名
- 习惯学习扫描时自动排除系统目录与 `node_modules` 等

## 安全与权限

- `Read`：读取待整理文件内容预览（不上传原文件）
- `Write` / `Bash`：移动文件、执行 CLI
- `Glob` / `Grep`：仅辅助定位**未整理**源目录中的文件；**已归档**文件必须用 `search` 或 Read `file_index.md`
- 需访问 `DOCMIND_BACKEND_URL`（生产环境用 HTTPS）

## 参考文档

- 分类规则：`{baseDir}/references/classification-rules.md`
- 配置与环境变量：`{baseDir}/references/configuration.md`
- 后端 API：`{baseDir}/references/api.md`
- 文件索引：`{baseDir}/references/file-index.md`

## 计费

| 操作 | 免费额度 | 超出后 | 订阅 |
|------|----------|--------|------|
| `preview` / `rebuild-index` | 无限免费 | — | — |
| `run`（整理） | 5 次/月 | 2 元/次 | 9.9 元/月无限 |
| `search`（查找） | 20 次/月 | 0.05 元/次 | 9.9 元/月无限 |

- 一次 `run` = 1 次整理会话（会话内最多约 500 个文件，不按文件另计费）
- 一次 `search` = 1 次查找
- 用 `quota --user-id <ID>` 查询剩余免费整理/查找次数与按次余额
- HTTP 402 时提示充值或订阅；Skill 本身无定价元数据

## 版本

- Skill：1.5.0（独立客户端仓 DocMind-skills）
- 分类规则：`references/classification-rules.md`
