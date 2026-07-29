@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] Codex GUI - 物料生成引擎 :57321

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "CODEX_EXE=C:\Users\Administrator\AppData\Local\Programs\Codex++\codex-plus-plus.exe"

echo ============================================
echo  ORCA Dual-Instance: Codex GUI Launcher
echo  Project: 企业微信群定制接单项目
echo ============================================

:: 前置自愈
if exist "C:\Users\Administrator\WorkBuddy\2026-07-23-10-30-42\codex_self_heal.py" (
    python "C:\Users\Administrator\WorkBuddy\2026-07-23-10-30-42\codex_self_heal.py" --fix >nul 2>&1
)

:: 终止旧进程
taskkill /F /IM codex-plus-plus.exe >nul 2>&1
taskkill /F /IM Codex.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: 启动
start "" "%CODEX_EXE%"
timeout /t 5 /nobreak >nul
echo [OK] Codex++ GUI launched for 企业微信商单
endlocal
