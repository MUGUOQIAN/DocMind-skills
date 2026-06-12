@echo off
chcp 65001 >nul 2>&1
title DocMind - 查询额度
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" quota --user-id %DOCMIND_USER_ID%
echo.
pause
