@echo off
chcp 65001 >nul 2>&1
title DocMind
call "%~dp0_env.bat"
"%DOCMIND_VENV%\Scripts\python.exe" "%DOCMIND_ROOT%\desktop\main.py"
