@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Codex CLI - 物料生成引擎 :57362

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "CODEX_WORKTREE=%PROJECT_ROOT%\worktrees\codex"

echo ============================================
echo  ORCA Dual-Instance: Codex CLI Launcher
echo  Project: 企业微信群定制接单项目 | Port: 57362
echo ============================================

if not exist "%CODEX_WORKTREE%" (echo [ERROR] Worktree not found & pause & exit /b 1)
cd /d "%CODEX_WORKTREE%"
echo [INFO] Codex CLI ready (物料生成/自动化流水线)
endlocal
