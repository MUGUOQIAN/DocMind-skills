@echo off
chcp 65001 >nul 2>&1
title DocMind 一键安装
echo.
echo 正在启动 DocMind 安装程序...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
pause
