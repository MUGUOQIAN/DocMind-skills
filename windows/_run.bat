@echo off
chcp 65001 >nul 2>&1
setlocal
call "%~dp0_env.bat"
if not exist "%DOCMIND_VENV%\Scripts\activate.bat" (
  echo [错误] 未找到 Python 虚拟环境，请先双击运行 install.bat
  pause
  exit /b 1
)
call "%DOCMIND_VENV%\Scripts\activate.bat"
cd /d "%DOCMIND_ROOT%"
python scripts\docmind.py %*
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
