@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Hermes CLI - 商单调度中心 :57361

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "HERMES_WORKTREE=%PROJECT_ROOT%\worktrees\hermes"
set "HERMES_PORT=57361"

echo ============================================
echo  ORCA Dual-Instance: Hermes CLI Launcher
echo  Project: 企业微信群定制接单项目 | Port: %HERMES_PORT%
echo ============================================

if not exist "%HERMES_WORKTREE%" (echo [ERROR] Worktree not found & pause & exit /b 1)

netstat -an | findstr ":%HERMES_PORT% " >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%HERMES_PORT% "') do taskkill /PID %%a /F >nul 2>&1
)

cd /d "%HERMES_WORKTREE%"
echo [INFO] Starting Hermes CLI (商单调度) on port %HERMES_PORT%...
python -m http.server %HERMES_PORT% --bind 127.0.0.1 2>nul
endlocal
