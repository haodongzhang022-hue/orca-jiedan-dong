@echo off
REM 龙虾舰队自动就绪脚本 (Windows版)
REM 由计划任务 LobsterFleet_AutoRestore 调用
REM 确保 Hermes / Codex / Claude Code 三Agent默认正常

echo =========================================
echo   龙虾舰队自动就绪检查 %date% %time%
echo =========================================

set ERRORS=0

REM ---- 1. 代理端口检查 ----
netstat -ano | findstr "LISTENING" | findstr ":15721 " >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 端口 15721 未运行，正在拉起...
    start /min "AutoRestore-15721" "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "E:\龙虾AI主控中心\MCP服务\anthropic_proxy_15721.py"
    timeout /t 3 /nobreak >nul
    set /a ERRORS+=1
) else (
    echo [OK] 端口 15721 正常
)

netstat -ano | findstr "LISTENING" | findstr ":15730 " >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 端口 15730 未运行，正在拉起...
    start /min "AutoRestore-15730" "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "E:\龙虾AI主控中心\MCP服务\codex_tool_proxy.py"
    timeout /t 3 /nobreak >nul
    set /a ERRORS+=1
) else (
    echo [OK] 端口 15730 正常
)

REM ---- 2. Codex CLI shim 检查 ----
if not exist "C:\Users\Administrator\AppData\Roaming\npm\codex" (
    echo [!] Codex CLI shim 缺失，正在创建...
    echo #!/bin/sh > "C:\Users\Administrator\AppData\Roaming\npm\codex"
    echo exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@" >> "C:\Users\Administrator\AppData\Roaming\npm\codex"
    echo @ECHO off > "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
    echo node "I:\npm\node_modules\@openai\codex\bin\codex.js" %%* >> "C:\Users\Administrator\AppData\Roaming\npm\codex.cmd"
    echo [OK] Codex shim 已创建
) else (
    echo [OK] Codex shim 存在
)

REM ---- 3. Codex 配置同步 ----
if exist "%USERPROFILE%\.codex\config.toml" (
    copy /Y "%USERPROFILE%\.codex\config.toml" "%APPDATA%\Orca\codex-runtime-home\home\config.toml" >nul 2>&1
    echo [OK] Codex runtime 配置已同步
) else (
    echo [!] Codex 配置文件不存在
    set /a ERRORS+=1
)

REM ---- 结果 ----
echo.
if %ERRORS% equ 0 (
    echo =========================================
    echo   [OK] 三Agent全部就绪，零错误
    echo =========================================
) else (
    echo =========================================
    echo   [!] 完成（%ERRORS% 项已自动修复）
    echo =========================================
)
