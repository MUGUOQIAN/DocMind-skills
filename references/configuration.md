# DocMind 配置说明

## 配置文件

默认路径：`~/.docmind/config.json`

| 字段 | 说明 |
|------|------|
| `industry` | 行业（辅助分类） |
| `job_title` | 职业（辅助分类） |
| `target_folder` | 待整理目录 |
| `archive_root` | 归档根目录 |
| `dry_run` | 预览模式 |
| `structure_confirmed` | 是否已确认归档结构 |
| `habit_discovery_enabled` | 是否已做习惯学习 |
| `categories` | 自定义子类与项目名 |

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DOCMIND_BACKEND_URL` | 否 | 分类/计费 API，默认 `http://127.0.0.1:8000` |
| `DOCMIND_REPO_ROOT` | 否* | DocMind-skills 仓库根目录（非克隆目录运行时必填） |
| `DOCMIND_USER_ID` | 否 | 平台用户 ID，默认 `default-user` |
| `DOCMIND_INDUSTRY` | 否 | 跳过引导时设置行业 |
| `DOCMIND_JOB_TITLE` | 否 | 跳过引导时设置职业 |
| `DOCMIND_TARGET_FOLDER` | 否 | 待整理目录 |
| `DOCMIND_ARCHIVE_ROOT` | 否 | 归档目录 |
| `DOCMIND_SKIP_SETUP` | 否 | `1` 跳过交互引导 |

\* 从 `DocMind-skills` 克隆目录运行 `scripts/docmind.py` 时自动检测，无需设置。

## 计费说明

- **preview** / **rebuild-index**：免费
- **run**：每轮整理 = **1 次整理会话**（不是按文件计费）；单次会话默认最多 500 个文件
- **search**：每次索引查找 = **1 次查找额度**
- 免费：每月 **5 次整理** + **20 次查找**
- 超出后：整理 **2 元/次**；查找 **0.05 元/次**
- 订阅：**9.9 元/月**，整理与查找均无限

Skill 本身不包含定价元数据；详见项目 README 与 `api.md`。
