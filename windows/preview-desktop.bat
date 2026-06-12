@echo off
chcp 65001 >nul 2>&1
title DocMind - 预览整理桌面
echo.
echo ========================================
echo   DocMind 预览整理（不会移动任何文件）
echo ========================================
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" preview --desktop --user-id %DOCMIND_USER_ID%
echo.
echo 预览完成。请在窗口中查看归档方案。
echo 确认无误后，双击桌面快捷方式「DocMind - 执行整理桌面」。
echo.
pause
