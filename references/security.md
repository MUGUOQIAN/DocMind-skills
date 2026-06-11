# DocMind Skill 安全与隐私说明

供 skill-vetter / SkillHub 安全扫描与用户审查参考。

## 风险自评：MEDIUM

| 类别 | 行为 | 说明 |
|------|------|------|
| 网络访问 | `httpx` 请求 `DOCMIND_BACKEND_URL` | 默认 `https://api.blt3d.cn`；仅分类与计费 API |
| 上传内容 | 文件名 + 内容摘要（约 2000 字符） | **不上传**原文件二进制 |
| 本地文件 | 读取用户指定目录；移动至 `archive_root` | 仅在用户授权路径内操作 |
| 敏感目录 | 习惯学习跳过系统目录 | 不读取 `~/.ssh`、`~/.aws` 等 |
| 凭证 | 不要求用户 API Key / 密码 | 服务端托管 DeepSeek |
| 动态执行 | 无 `eval` / `exec` | 子进程仅调用本 Skill 的 Python CLI |

## 数据传输

整理时客户端向 API 发送：

- `platform_user_id`、`platform`（如 `workbuddy`）
- `filename`、`content_preview`（文本摘要）
- 用户行业/职位（辅助分类，来自本地配置）

不向第三方发送完整文件内容。

## 本地写入

| 路径 | 用途 |
|------|------|
| `~/.docmind/config.json` | 用户配置 |
| `<archive_root>/.docmind/` | 索引、日志、监视状态 |
| 源目录 `.docmind/logs/` | 整理会话日志（支持 undo） |

## 权限建议

Skill frontmatter 限制为：

```yaml
allowed-tools: Read, Write, Glob, Grep, Bash(python:*)
```

Agent 仅通过 `python …/scripts/workbuddy_dispatch.py` 或 `docmind.py` 执行，不调用任意 Shell 命令。

## 用户可控项

- `DOCMIND_BACKEND_URL`：可指向自托管 API
- `DOCMIND_USER_ID`：计费身份
- `target_folder` / `archive_root`：限定文件操作范围
