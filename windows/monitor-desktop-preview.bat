@echo off
chcp 65001 >nul 2>&1
title DocMind - 监视桌面（预览模式）
echo.
echo ========================================
echo   自动监视桌面：有新文件时预览整理方案
echo   不移动文件；Ctrl+C 停止
echo ========================================
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" monitor --desktop --mode preview
pause
