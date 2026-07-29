@echo off
chcp 65001 >nul 2>&1
setlocal
title [企业微信] ORCA 双实例 - 全部启动

set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "SCRIPTS=%PROJECT_ROOT%\scripts"

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║   ORCA 双实例启动 - 企业微信群定制接单项目        ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: Phase 1: Codex GUI (with self-heal)
echo [1/4] Codex++ GUI (物料生成引擎)...
start "" cmd /c "%SCRIPTS%\launch_codex_gui.cmd"
timeout /t 5 /nobreak >nul

:: Phase 2: Hermes CLI (商单调度)
echo [2/4] Hermes CLI (商单调度) :57361...
start "Hermes-CLI-企微" cmd /c "%SCRIPTS%\launch_hermes_cli.cmd"
timeout /t 2 /nobreak >nul

:: Phase 3: Claude Code Serve (交付审核)
echo [3/4] Claude Code Serve (交付审核) :57330...
start "" cmd /c "%SCRIPTS%\launch_claude_serve.cmd"
timeout /t 3 /nobreak >nul

:: Phase 4: Fleet Exchange 状态报告
echo [4/4] Fleet Exchange status...
if exist "%PROJECT_ROOT%\fleet_exchange\incoming" (
    for %%f in ("%PROJECT_ROOT%\fleet_exchange\incoming\*") do echo   Pending: %%~nxf
)

echo.
echo ═══════════════════════════════════════════════════
echo  Agent          Mode    Port      Status
echo ───────────────────────────────────────────────────
echo  Hermes         CLI     :57361    Running (商单调度)
echo  Codex          GUI     :57321    Running (物料生成)
echo  Claude Code    Serve   :57330    Running (交付审核)
echo  Fleet Exchange Filesys    Active  (%PROJECT_ROOT%\fleet_exchange)
echo ═══════════════════════════════════════════════════
echo.
pause
endlocal
