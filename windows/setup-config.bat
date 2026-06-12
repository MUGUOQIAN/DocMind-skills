@echo off
chcp 65001 >nul 2>&1
title DocMind - 详细配置
echo.
echo 将启动交互式配置引导（行业、职业、归档目录等）。
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" setup
echo.
pause
