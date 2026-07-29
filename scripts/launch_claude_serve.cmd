@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Claude Code Serve - 交付质量审核 :57330

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "CLAUDE_WORKTREE=%PROJECT_ROOT%\worktrees\claude"

echo ============================================
echo  ORCA Dual-Instance: Claude Code Serve
echo  Project: 企业微信群定制接单项目 | Port: 57330
echo ============================================

if not exist "%CLAUDE_WORKTREE%" (echo [ERROR] Worktree not found & pause & exit /b 1)

netstat -an | findstr ":57330 " >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":57330 "') do taskkill /PID %%a /F >nul 2>&1
)

cd /d "%CLAUDE_WORKTREE%"
start /B claude serve --port 57330 2>nul
echo [OK] Claude Code Serve ready on :57330
endlocal
