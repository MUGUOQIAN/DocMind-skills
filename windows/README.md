# DocMind Windows 一键安装（无需 Agent）

适合**没有安装 WorkBuddy / OpenClaw** 的电脑，双击即可整理桌面。

## 准备

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（勾选 **Add Python to PATH**）
2. 下载或克隆本仓库到本地，例如：
   `C:\Users\你的用户名\DocMind-skills`

## 安装（只需一次）

1. 进入文件夹 `DocMind-skills\windows\`
2. **双击 `install.bat`**
3. 等待安装完成（约 1～3 分钟，需联网）
4. 桌面上会出现 4 个快捷方式

## 日常使用

| 快捷方式 | 作用 |
|----------|------|
| **DocMind - 预览整理桌面** | 模拟整理，**不移动文件**，先看归类方案 |
| **DocMind - 执行整理桌面** | 确认方案后真正移动文件到归档目录 |
| **DocMind - 撤销上次整理** | 恢复上一次整理前的桌面 |
| **DocMind - 查询剩余额度** | 查看免费试用与剩余次数 |
| **DocMind - 监视桌面(预览)** | 有新文件时自动预览整理方案 |
| **DocMind - 监视桌面(自动整理)** | 有新文件时自动归档（扣整理额度） |

### 推荐流程

```
预览 → 查看窗口中的归档路径 → 执行整理
```

默认归档位置：`C:\Users\你的用户名\DocMind归档\`

## 如何修改归档目录

整理后文件会移动到 **`archive_root`（归档根目录）** 下，由 AI 自动创建 `生活`、`工作` 等子文件夹。  
**根目录位置可以改**，子目录结构仍按 DocMind 分类规则生成。

### 整理结果长什么样

假设你把归档目录设为 `D:\我的资料库`，整理后大致为：

```
D:\我的资料库\
├── 生活\财务\银行账单\xxx.pdf
├── 工作\某某项目\合同\xxx.docx
├── 应用快捷方式\...
└── .docmind\          ← 索引与日志（自动生成，勿删）
    ├── file_index.json
    └── file_index.md
```

### 方式一：配置引导（推荐，最简单）

1. 进入 `DocMind-skills\windows\`
2. 双击 **`setup-config.bat`**
3. 按提示选择或输入：
   - **待整理位置**：桌面 / 指定文件夹（如下载目录）
   - **归档根目录**：整理后文件存放位置

示例输入：

| 你想做的事 | 归档根目录示例 |
|------------|----------------|
| 存到 D 盘 | `D:\我的归档` |
| 存到网盘同步文件夹 | `C:\Users\你\OneDrive\DocMind归档` |
| 按项目集中管理 | `E:\工作资料\DocMind` |

改完后先运行 **「预览整理桌面」** 确认路径正确，再执行整理。

### 方式二：直接编辑配置文件

1. 用记事本打开：

   ```
   C:\Users\你的用户名\.docmind\config.json
   ```

2. 修改下面两个字段（路径用双反斜杠 `\\` 或正斜杠 `/`）：

   ```json
   {
     "target_folder": "C:\\Users\\你\\Desktop",
     "archive_root": "D:\\我的归档"
   }
   ```

   | 字段 | 含义 |
   |------|------|
   | `target_folder` | 待整理目录（默认桌面） |
   | `archive_root` | 整理后文件的根目录 |

3. 保存文件，再运行预览或整理。

### 方式三：仅整理「下载」等其他文件夹

若不想整理桌面，只整理下载目录：

**用配置引导：** `setup-config.bat` → 待整理位置选「指定文件夹」→ 填 `C:\Users\你\Downloads`

**或改 config.json：**

```json
{
  "target_folder": "C:\\Users\\你\\Downloads",
  "archive_root": "D:\\我的归档"
}
```

> 当前桌面快捷方式固定带 `--desktop` 参数。若常整理其他文件夹，可在 `windows` 目录复制 `preview-desktop.bat` 为 `preview-downloads.bat`，把其中的 `--desktop` 改为 `--folder "C:\Users\你\Downloads"`。

### 修改后请注意

1. **先预览再执行**，确认窗口里显示的 `destination` 路径符合预期。  
2. **已整理过的文件不会自动搬家**；更换 `archive_root` 后，新整理进新目录，旧文件仍在原归档位置。  
3. **搜索索引按归档目录记录**；换目录后搜索新文件无影响；若要搜旧归档，需记得旧路径，或对旧目录执行 `rebuild-index`。  
4. 归档目录所在磁盘需有**足够空间**和**写入权限**（勿选只读或系统保护目录）。

## 自动监视桌面

桌面或 `target_folder` 出现新文件时，防抖后自动整理：

| 快捷方式 | 模式 | 说明 |
|----------|------|------|
| **监视桌面(预览)** | `preview` | 只输出方案，不移动文件 |
| **监视桌面(自动整理)** | `run` | 自动归档；**每次触发扣 1 次整理会话** |

```bash
python scripts/docmind.py monitor --desktop --mode preview
python scripts/docmind.py monitor-status --desktop
```

## 常见问题

**Q：需要 AI Agent 吗？**  
不需要。本安装包通过命令行直连 DocMind 云端 API。

**Q：需要自己的 API Key 吗？**  
不需要。默认连接 `https://api.blt3d.cn`。

**Q：收费吗？**  
新用户 **3 个月免费试用**，每月 5 次整理 + 20 次搜索；预览始终免费。

**Q：想改行业、归档目录？**  
运行 `setup-config.bat`，或参见上文 [如何修改归档目录](#如何修改归档目录)。

**Q：重新安装？**  
再次双击 `install.bat` 即可（会覆盖 `_env.bat`，保留已有 `~/.docmind/config.json`）。

## 文件说明

| 文件 | 说明 |
|------|------|
| `install.bat` / `install.ps1` | 一键安装 |
| `_env.bat` | 安装后生成的路径与用户 ID（勿手改） |
| `preview-desktop.bat` 等 | 各功能入口 |
