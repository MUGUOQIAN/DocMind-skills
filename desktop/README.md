# DocMind 桌面应用

跨平台 **macOS / Windows** 图形界面，复用 `lib/` 整理与搜索能力，无需 AI Agent。

## 功能

| 页签 | 能力 |
|------|------|
| **整理** | 预览 / 执行 / 撤销；显示并设置**整理后保存目录**（可选磁盘与文件夹） |
| **搜索** | 在已归档索引中关键词查找 |
| **设置** | 待整理目录、**归档磁盘/路径**、行业/职位 |

预览免费；执行整理按云端计费规则扣减额度（新用户 3 个月试用）。

## 安装依赖

在 `DocMind-skills` 根目录：

```bash
pip install -r requirements.txt
pip install -r desktop/requirements.txt
```

## 启动

```bash
# 方式 1：直接运行
python desktop/main.py

# 方式 2：统一 CLI
python scripts/docmind.py gui
```

### Windows

双击 `windows/docmind-app.bat`（需先运行 `install.bat`）。

安装脚本会在桌面创建 **DocMind 应用** 快捷方式。

### macOS

```bash
chmod +x desktop/run-mac.command
./desktop/run-mac.command
```

或：

```bash
python3 desktop/main.py
```

## 打包为独立应用（可选）

需安装 [PyInstaller](https://pyinstaller.org/)：

```bash
pip install pyinstaller
pip install -r requirements.txt -r desktop/requirements.txt
```

**Windows**（在 `DocMind-skills` 根目录）：

```powershell
.\desktop\build\build-windows.ps1
```

输出：`desktop/dist/DocMind/DocMind.exe`

**macOS**：

```bash
chmod +x desktop/build/build-macos.sh
./desktop/build/build-macos.sh
```

输出：`desktop/dist/DocMind.app`

> 打包后仍需本机安装 Tesseract 才能 OCR 图片；PDF/Office 解析库已随包内置。

## 环境变量

| 变量 | 说明 |
|------|------|
| `DOCMIND_BACKEND_URL` | API 地址，默认 `https://api.blt3d.cn` |
| `DOCMIND_USER_ID` | 覆盖自动生成的桌面用户 ID |
| `DOCMIND_PLATFORM` | 固定为 `desktop`（应用启动时自动设置） |

## 与 CLI / 监视的关系

- 桌面应用与 `scripts/docmind.py` 共用 `~/.docmind/config.json`
- 后台自动监视（`monitor`）仍可通过 CLI 或 Windows `.bat` 运行；后续版本将集成到应用托盘
