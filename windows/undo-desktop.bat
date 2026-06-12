@echo off
chcp 65001 >nul 2>&1
title DocMind - 撤销整理
echo.
echo ========================================
echo   DocMind 撤销上一次整理
echo ========================================
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" undo --desktop --user-id %DOCMIND_USER_ID%
echo.
pause
