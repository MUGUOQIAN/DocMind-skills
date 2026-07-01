@echo off
chcp 65001 >nul 2>&1
title DocMind - 监视下载文件夹（自动整理）
echo.
echo ========================================
echo   自动监视下载文件夹：有新文件时自动归档
echo   每次触发扣 1 次整理额度；Ctrl+C 停止
echo ========================================
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" monitor --downloads --mode run
pause
