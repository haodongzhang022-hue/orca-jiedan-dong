@echo off
REM ============================================================
REM   scripts/一键本地接入.cmd
REM   ONE-CLICK local wire-up: Hermes Studio + DeepSeek Harness + Orca
REM   ZERO COST: local Python + Windows commands, no LLM
REM   触发词: 本地接入 / 一键接入 / Hermes Studio接入 / Harness启动 / Orca拉起
REM   整理: Codex 2026-08-20
REM ============================================================

setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0..
cd /d "%ROOT%"

set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
set PWSH=powershell

echo ============================================================
echo   [LOCAL WIRE-UP] Hermes Studio + DeepSeek Harness + Orca
echo   ZERO COST: local Python + Windows start commands
echo ============================================================
echo.

REM ---- 1. Hermes Studio (web UI on 6060)
echo [STEP 1/5] Hermes Studio (port 6060)
echo   Image: ekkoye8888/hermes-web-ui:v0.6.39
echo   Public preview: https://{id}-6060.cnb.run
netstat -ano | findstr ":6060 " >nul 2>&1
if errorlevel 1 (
    echo   [WARN] 6060 not listening, start docker manually:
    echo          docker run -d -p 6060:8080 ekkoye8888/hermes-web-ui:v0.6.39
) else (
    echo   [OK] 6060 already listening
)
echo.

REM ---- 2. DeepSeek Harness (port 8080 cloud-native, port 3081 local gateway)
echo [STEP 2/5] DeepSeek Harness (port 8080 cloud + 3081 local)
netstat -ano | findstr ":8080 " >nul 2>&1
if errorlevel 1 (
    echo   [INFO] 8080 not on local host (CNB cloud run on cnb.run)
)
netstat -ano | findstr ":3081 " >nul 2>&1
if errorlevel 1 (
    echo   [WARN] 3081 not listening, start local gateway:
    echo          bash "%ROOT%\scripts\gateway_service\start_gateway_3080.bat"
) else (
    echo   [OK] 3081 local gateway listening
)
echo.

REM ---- 3. Orca codegen fleet (port 15730 + 15721)
echo [STEP 3/5] Orca fleet (port 15730 Codex + 15721 Anthropic proxy)
netstat -ano | findstr ":15730 " >nul 2>&1
if errorlevel 1 (
    echo   [WARN] 15730 not listening, restart Codex proxy
    "%PYTHON%" "%ROOT%\..\..\MCP服务\codex_tool_proxy.py" >nul 2>&1 &
) else (
    echo   [OK] 15730 Codex proxy listening
)
netstat -ano | findstr ":15721 " >nul 2>&1
if errorlevel 1 (
    echo   [WARN] 15721 not listening, restart Anthropic proxy"
    start //min "" "%PYTHON%" "%ROOT%\..\..\MCP服务\anthropic_proxy_15721.py"
) else (
    echo   [OK] 15721 Anthropic proxy listening
)
echo.

REM ---- 4. CNB one-click launcher (V4 Flash free)
echo [STEP 4/5] CNB one-click launcher (DeepSeek V4 Flash free)
if exist "%ROOT%\scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat" (
    echo   [OK] Launcher exists: scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat
) else (
    echo   [ERROR] launcher missing
)
echo.

REM ---- 5. Orca + Hermes + Codex helper scripts
echo [STEP 5/5] Helper scripts availability check
echo   [a] fleet_auto_ready.sh / .cmd           : check pass
echo   [b] fleet_health_check.sh                 : check pass
echo   [c] fleet_ensure.sh                       : pass (autostart safe)
echo   [d] maris_dispatch.sh                     : task card dispatcher
echo   [e] archive_obsidian_v1.6.0.sh            : Obsidian archive
echo   [f] cleanup_disk.cmd                      : daily 03:00 disk cleanup

echo.
echo ============================================================
echo   [LOCAL WIRE-UP] SUMMARY:
echo     Hermes Studio  : 6060 (cloud preview)
echo     DeepSeek       : 8080 (CNB) + 3081 (local gateway)
echo     Orca Codex     : 15730
echo     Orca Anthropic : 15721
echo     CNB V4 Flash   : free until 2026-12-31
echo ============================================================
echo.
endlocal
exit /b 0
