# DocMind 文件索引

整理或预览完成后，DocMind 自动维护归档目录下的索引，供 Agent 快速查找文件。

## 索引位置

| 文件 | 路径 |
|------|------|
| JSON（机器读） | `<archive_root>/.docmind/file_index.json` |
| Markdown（Agent 读） | `<archive_root>/.docmind/file_index.md` |
| 全局汇总 | `~/.docmind/file_index.json` |

## 每条记录包含

- `filename` — 文件名
- `path` — 归档后完整路径
- `target_path` — 分类相对路径（如 `工作/东方广场改造/图纸`）
- `content_snippet` — 内容摘要（整理时提取）
- `indexed_at` — 索引时间
- `preview_only` — 是否为预览阶段写入（尚未实际移动）

## Agent 检索方式

**推荐：命令行搜索**（每次查找扣 1 次查找额度，需后端在线）

```bash
python {baseDir}/scripts/docmind.py search --query "东方广场 合同" --user-id <平台用户ID>
python {baseDir}/scripts/docmind.py search --query "银行账单" --archive "C:/Users/me/DocMind归档"
```

免费档每月 20 次查找；超出 0.05 元/次；订阅 9.9 元/月无限。`rebuild-index` 免费。

**或直接 Read**

```text
Read <archive_root>/.docmind/file_index.md
```

## 重建索引

归档目录已有文件但索引缺失时：

```bash
python {baseDir}/scripts/docmind.py rebuild-index --archive "C:/Users/me/DocMind归档"
```

## 监视归档目录（增量更新）

用户手动增删改归档内文件时，用 `watch` 保持索引与磁盘一致（**仅监视 `archive_root`**，本地执行，不耗整理额度）：

```bash
python {baseDir}/scripts/docmind.py watch --sync-on-start
python {baseDir}/scripts/docmind.py watch-status
```

| 事件 | 索引行为 |
|------|----------|
| 新建 / 修改 | 防抖后 upsert 条目并刷新摘要 |
| 删除 / 移出 | 从索引移除 |
| 移动 / 重命名 | 删旧路径、写入新路径 |

状态文件：`<archive_root>/.docmind/watch_state.json`

## 配置（~/.docmind/config.json）

- `index_enabled` — 默认 `true`
- `index_snippet_chars` — 摘要长度，默认 `400`
- `index_watch_debounce_secs` — 监视防抖秒数，默认 `3`

撤销整理（`undo`）会从索引中移除对应条目。
