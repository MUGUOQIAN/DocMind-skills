@echo off
chcp 65001 >nul 2>&1
title DocMind - 监视下载文件夹（预览模式）
echo.
echo ========================================
echo   自动监视下载文件夹：有新文件时预览整理方案
echo   不移动文件；Ctrl+C 停止
echo ========================================
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" monitor --downloads --mode preview
pause
