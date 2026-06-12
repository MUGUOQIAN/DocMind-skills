@echo off
chcp 65001 >nul 2>&1
title DocMind - 执行整理桌面
echo.
echo ========================================
echo   DocMind 执行整理（将移动桌面文件）
echo ========================================
echo.
echo 建议先运行「预览整理桌面」确认方案。
set /p CONFIRM=确定要整理桌面吗？输入 Y 继续，其他键取消: 
if /i not "%CONFIRM%"=="Y" (
  echo 已取消。
  pause
  exit /b 0
)
echo.
call "%~dp0_env.bat"
call "%~dp0_run.bat" run --desktop --user-id %DOCMIND_USER_ID%
echo.
echo 整理完成。文件已移入配置中的归档目录（默认：用户目录\DocMind归档）。
echo 如需撤销，请使用「DocMind - 撤销上次整理」。
echo.
pause
