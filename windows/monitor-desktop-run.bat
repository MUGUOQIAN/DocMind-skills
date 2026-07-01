@echo off
chcp 65001 >nul 2>&1
title DocMind - 监视桌面（自动整理）
echo.
echo ========================================
echo   自动监视桌面：有新文件时自动归档
echo   每次触发扣 1 次整理会话；Ctrl+C 停止
echo ========================================
echo.
set /p CONFIRM=确定启用自动整理吗？输入 Y 继续: 
if /i not "%CONFIRM%"=="Y" (
  echo 已取消。
  pause
  exit /b 0
)
call "%~dp0_env.bat"
call "%~dp0_run.bat" monitor --desktop --mode run
pause
