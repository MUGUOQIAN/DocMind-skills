# DocMind 配置说明

## 配置文件

默认路径：`~/.docmind/config.json`

| 字段 | 说明 |
|------|------|
| `industry` | 行业（辅助分类） |
| `job_title` | 职业（辅助分类） |
| `target_folder` | 待整理目录 |
| `archive_root` | 整理后文件的根目录（见下文「归档保存位置」） |
| `dry_run` | 预览模式 |
| `structure_confirmed` | 是否已确认归档结构 |
| `habit_discovery_enabled` | 是否已做习惯学习 |
| `categories` | 自定义子类与项目名 |

### 归档保存位置（archive_root）

整理后的文件会移动到 `archive_root` 下的 `生活/`、`工作/` 等子目录，**不会留在桌面原位置**。

| 设置方式 | 说明 |
|----------|------|
| **桌面应用** | 「整理」页或「设置」→ **选择磁盘/文件夹**，可看到各盘剩余空间 |
| **配置引导** | `setup` / `setup-config.bat` → 按磁盘编号选择，再输入文件夹名 |
| **配置文件** | 编辑 `~/.docmind/config.json` 的 `archive_root` |
| **安装时** | 环境变量 `DOCMIND_ARCHIVE_ROOT=D:\我的归档`（可选） |

示例：

```json
"archive_root": "D:\\我的归档"
```

更换 `archive_root` 后，**新整理**的文件进新目录；已归档文件不会自动迁移。

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DOCMIND_BACKEND_URL` | 否 | 分类/计费 API，默认 `https://api.blt3d.cn` |
| `DOCMIND_PLATFORM` | 否 | 计费平台标识，默认 `workbuddy`；OpenClaw 用 `openclaw` |
| `DOCMIND_REPO_ROOT` | 否* | DocMind-skills 仓库根目录（非克隆目录运行时必填） |
| `DOCMIND_USER_ID` | 否 | 平台用户 ID，见下文 |
| `DOCMIND_INDUSTRY` | 否 | 跳过引导时设置行业 |
| `DOCMIND_JOB_TITLE` | 否 | 跳过引导时设置职业 |
| `DOCMIND_TARGET_FOLDER` | 否 | 待整理目录 |
| `DOCMIND_ARCHIVE_ROOT` | 否 | 归档目录 |
| `DOCMIND_SKIP_SETUP` | 否 | `1` 跳过交互引导（WorkBuddy 推荐） |

\* 从 `DocMind-skills` 克隆目录运行 `scripts/docmind.py` 时自动检测，无需设置。

## 平台用户 ID（WorkBuddy）

计费按 `platform_user_id` + `platform` 统计。WorkBuddy 安装后建议：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | 命令行 `--user-id` | 显式指定 |
| 2 | `DOCMIND_USER_ID` | 建议设为腾讯账号或 WorkBuddy 用户标识 |
| 3 | `CODEBUDDY_SESSION_ID` | WorkBuddy/CodeBuddy 会话 ID（`workbuddy_dispatch.py` 自动回退） |
| 4 | `CLAUDE_SESSION_ID` | 兼容别名 |

分发脚本：

- WorkBuddy：`scripts/workbuddy_dispatch.py`（设置 `DOCMIND_PLATFORM=workbuddy`）
- OpenClaw：`scripts/openclaw_dispatch.py`（设置 `DOCMIND_PLATFORM=openclaw`）

## 非交互首次配置（WorkBuddy / Agent）

Agent 环境无法使用 `setup` 的 `input()` 交互。推荐：

```bash
export DOCMIND_INDUSTRY=建筑
export DOCMIND_JOB_TITLE=项目经理
export DOCMIND_TARGET_FOLDER=C:/Users/me/Desktop
export DOCMIND_ARCHIVE_ROOT=C:/Users/me/DocMind归档
export DOCMIND_SKIP_SETUP=1
```

或复制 `config.example.json` 到 `~/.docmind/config.json` 后编辑。

## 计费说明

- **preview** / **rebuild-index** / **watch** / **monitor --mode preview**：始终免费
- **monitor --mode run**：每次防抖触发 = 1 次整理会话
- **run**：每轮整理 = **1 次整理会话**；单次会话默认最多 500 个文件
- **search**：每次索引查找 = **1 次查找额度**
- **免费试用**：新用户自首次调用起 **3 个月内**，每月 **5 次整理** + **20 次查找**（自然月重置）
- 试用期结束后：不再赠送月度免费额度；整理 **2 元/次**；查找 **0.05 元/次**
- 订阅：**9.9 元/月**，整理与查找均无限

`quota` 响应含 `free_trial_active`、`free_trial_expire`、`free_trial_days_remaining`。

### 自动监视（monitor）

监视**待整理目录**（桌面、下载、自定义文件夹），有新文件时防抖后自动 preview 或 run。

| 字段 | 说明 |
|------|------|
| `auto_monitor_mode` | `preview`（默认，不移动）或 `run`（自动归档） |
| `auto_monitor_debounce_secs` | 新文件防抖秒数，默认 10 |
| `auto_monitor_targets` | 默认监视目标，如 `["desktop", "downloads"]` |
| `auto_monitor_folders` | 额外监视的绝对路径列表 |
| `auto_monitor_ignore_existing` | 启动时忽略目录内已有文件，默认 `true` |
| `auto_monitor_folder` | （兼容旧版）单目录；留空则用 `target_folder` 或桌面 |

CLI 示例：

```bash
python scripts/docmind.py monitor                    # 按配置监视 desktop+downloads+folders
python scripts/docmind.py monitor --all --mode run
python scripts/docmind.py monitor --desktop --downloads --mode preview
python scripts/docmind.py monitor --folder D:/Inbox --folder E:/Drop
python scripts/docmind.py monitor-status
```

Skill 本身不包含定价元数据；详见项目 README 与 `api.md`。
