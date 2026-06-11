# SkillHub 上架素材（DocMind）

提交 [SkillHub](https://skillhub.cloud.tencent.com) 时可直接复用以下文案。

## 基本信息

| 字段 | 内容 |
|------|------|
| **技能 ID / 目录名** | `docmind` |
| **中文名称** | DocMind 智能文件整理 |
| **英文名称** | DocMind Smart File Organizer |
| **版本** | 1.6.1 |
| **分类标签** | 文档处理、办公效率、文件管理、AI 分类 |
| **许可证** | MIT |
| **仓库** | https://github.com/MUGUOQIAN/DocMind-skills |

## 一句话简介

读懂 PDF/Office/图片内容，自动归类到生活/工作目录树，并用自然语言搜索已归档文件。

## 详细描述

DocMind 是面向桌面办公场景的文件整理 Skill，兼容腾讯 WorkBuddy 与 OpenClaw。

**核心能力：**

- 按**文件内容**（非仅文件名）智能分类到 `生活/`、`工作/` 归档树
- 先 **preview** 预览再 **run** 执行，支持一键 **undo** 撤销
- 归档后通过 **search** 快速查找（「东方广场 合同」「银行账单」）
- **watch** 监视归档目录，增量更新索引

**定价（由云端 API 计费，Skill 内无密钥）：**

- 免费：每月 5 次整理 + 20 次搜索
- 超出：整理 2 元/次，搜索 0.05 元/次
- 订阅：9.9 元/月无限

用户无需自备 DeepSeek API Key；默认连接 `https://api.blt3d.cn`。

## 典型对话示例

```
用户：我桌面太乱了，帮我整理一下。
Agent：preview --desktop → 展示归档方案 → 用户确认 → run --desktop

用户：找一下东方广场的合同。
Agent：search --query "东方广场 合同" → 返回完整路径列表
```

## 安装说明（用户可见）

1. 复制到 `~/.workbuddy/skills/docmind/`
2. `pip install -r requirements.txt`
3. 对 Agent 说「帮我整理桌面」或「找一下某某合同」

## 安全披露（审核用）

- 风险等级：**MEDIUM**（本地文件操作 + HTTPS API）
- API 域名：`api.blt3d.cn`
- 仅传输文件名与文本摘要，不上传原文件
- 详见 `references/security.md`

## 截图建议（上架时补充）

1. 整理前凌乱的桌面/下载目录
2. `preview` 输出的归档路径列表
3. `search` 返回的合同/账单定位结果
4. `file_index.md` 索引表格预览

## 发布前自检

- [ ] `curl https://api.blt3d.cn/health` 返回正常
- [ ] `python scripts/workbuddy_dispatch.py quota` 可运行
- [ ] `preview` / `search` 端到端测试通过
- [ ] skill-vetter 扫描无 EXTREME 项
