# DocMind Windows 一键安装（无需 Agent）
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$WindowsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $WindowsDir "..")).Path
$VenvPath = Join-Path $RepoRoot ".venv"
$EnvBat = Join-Path $WindowsDir "_env.bat"

function Write-Step([string]$Msg) {
    Write-Host ""
    Write-Host ">> $Msg" -ForegroundColor Cyan
}

function Find-Python {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3.10") },
        @{ Exe = "python"; Args = @() }
    )
    $check = "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)"
    foreach ($c in $candidates) {
        try {
            & $c.Exe @($c.Args) -c $check 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { return $c }
        } catch { }
    }
    return $null
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  DocMind 一键安装（整理桌面，无需 Agent）" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Step "检查 Python 3.10+"
$py = Find-Python
if (-not $py) {
    Write-Host "[错误] 未找到 Python。请先安装：https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "       安装时勾选「Add Python to PATH」。" -ForegroundColor Yellow
    exit 1
}
$verOut = & $py.Exe @($py.Args) --version 2>&1 | Out-String
Write-Host "  已找到：$($verOut.Trim())"

Write-Step "创建虚拟环境并安装依赖"
if (-not (Test-Path $VenvPath)) {
    & $py.Exe @($py.Args) -m venv $VenvPath
}
$pip = Join-Path $VenvPath "Scripts\pip.exe"
$python = Join-Path $VenvPath "Scripts\python.exe"
& $pip install -q --upgrade pip
& $pip install -q -r (Join-Path $RepoRoot "requirements.txt")
& $pip install -q -r (Join-Path $RepoRoot "desktop\requirements.txt")

Write-Step "写入默认配置（桌面 -> DocMind归档）"
$bootstrap = & $python (Join-Path $RepoRoot "scripts\bootstrap_windows.py")
$info = $bootstrap | ConvertFrom-Json
$userId = $info.user_id
Write-Host "  待整理：$($info.target_folder)"
Write-Host "  归档到：$($info.archive_root)"
Write-Host "  用户 ID：$userId"

$envContent = @"
@echo off
rem 由 install.ps1 自动生成于 $(Get-Date -Format 'yyyy-MM-dd HH:mm')
set "DOCMIND_ROOT=$RepoRoot"
set "DOCMIND_VENV=$VenvPath"
set "DOCMIND_BACKEND_URL=https://api.blt3d.cn"
set "DOCMIND_PLATFORM=standalone"
set "DOCMIND_USER_ID=$userId"
"@
Set-Content -Path $EnvBat -Value $envContent -Encoding ASCII

Write-Step "创建桌面快捷方式"
$desktop = [Environment]::GetFolderPath("Desktop")
$wsh = New-Object -ComObject WScript.Shell

function New-Shortcut([string]$Name, [string]$Bat) {
    $lnk = Join-Path $desktop "$Name.lnk"
    $sc = $wsh.CreateShortcut($lnk)
    $sc.TargetPath = $Bat
    $sc.WorkingDirectory = $WindowsDir
    $sc.IconLocation = "$env:SystemRoot\System32\imageres.dll,184"
    $sc.Save()
    Write-Host "  + $Name"
}

New-Shortcut "DocMind - 预览整理桌面" (Join-Path $WindowsDir "preview-desktop.bat")
New-Shortcut "DocMind - 执行整理桌面" (Join-Path $WindowsDir "run-desktop.bat")
New-Shortcut "DocMind - 撤销上次整理" (Join-Path $WindowsDir "undo-desktop.bat")
New-Shortcut "DocMind - 查询剩余额度" (Join-Path $WindowsDir "quota.bat")
New-Shortcut "DocMind - 监视桌面(预览)" (Join-Path $WindowsDir "monitor-desktop-preview.bat")
New-Shortcut "DocMind - 监视桌面(自动整理)" (Join-Path $WindowsDir "monitor-desktop-run.bat")
New-Shortcut "DocMind - 监视下载(预览)" (Join-Path $WindowsDir "monitor-downloads-preview.bat")
New-Shortcut "DocMind - 监视下载(自动整理)" (Join-Path $WindowsDir "monitor-downloads-run.bat")
New-Shortcut "DocMind - 监视桌面+下载(预览)" (Join-Path $WindowsDir "monitor-all-preview.bat")
New-Shortcut "DocMind - 监视桌面+下载(自动整理)" (Join-Path $WindowsDir "monitor-all-run.bat")
New-Shortcut "DocMind 应用" (Join-Path $WindowsDir "docmind-app.bat")

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "桌面上已创建 11 个快捷方式。建议使用步骤：" -ForegroundColor Yellow
Write-Host "  1. 双击「DocMind - 预览整理桌面」查看方案"
Write-Host "  2. 确认后双击「DocMind - 执行整理桌面」"
Write-Host ""
Write-Host "新用户免费试用 3 个月（每月 5 次整理 + 20 次搜索）。" -ForegroundColor Gray
Write-Host "详细配置可运行 windows\setup-config.bat" -ForegroundColor Gray
Write-Host ""

$detail = Read-Host "是否现在运行详细配置引导？(Y/N，默认 N)"
if ($detail -eq "Y" -or $detail -eq "y") {
    & (Join-Path $WindowsDir "setup-config.bat")
}
