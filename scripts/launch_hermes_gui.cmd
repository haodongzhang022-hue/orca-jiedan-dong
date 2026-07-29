@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Hermes GUI - 商单调度中心

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "HERMES_WORKTREE=%PROJECT_ROOT%\worktrees\hermes"

echo ============================================
echo  ORCA Dual-Instance: Hermes GUI Launcher
echo  Project: 企业微信群定制接单项目
echo ============================================

if not exist "%HERMES_WORKTREE%" (echo [ERROR] Worktree not found & pause & exit /b 1)
echo [INFO] Launching Hermes GUI (商单调度面板)...
start "" "%PROJECT_ROOT%\fleet_exchange\logs" 2>nul
call "%PROJECT_ROOT%\scripts\launch_hermes_cli.cmd"
endlocal
