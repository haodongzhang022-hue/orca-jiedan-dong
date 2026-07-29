@echo off
chcp 65001 >nul 2>&1
setlocal
title [企微接单] 项目自动就绪

set "PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "MCP_DIR=E:\龙虾AI主控中心\MCP服务"

echo.
echo =========================================
echo   🦞 企微接单项目 · 自动就绪检查
echo   %date% %time%
echo =========================================
echo.

set "ERRORS=0"

:: ---- 1. 代理端口检查 ----
echo [1/4] 代理端口检查...

netstat -an | findstr ":15721 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [OK] 端口 15721 正常
) else (
    echo   [FIX] 端口 15721 未运行，正在拉起...
    start /min "AutoRestore-15721" "%PYEXE%" "%MCP_DIR%\anthropic_proxy_15721.py"
    timeout /t 3 /nobreak >nul
    netstat -an | findstr ":15721 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (echo   [OK] 端口 15721 已恢复) else (echo   [FAIL] 端口 15721 拉起失败 & set /a ERRORS+=1)
)

netstat -an | findstr ":15730 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [OK] 端口 15730 正常
) else (
    echo   [FIX] 端口 15730 未运行，正在拉起...
    start /min "AutoRestore-15730" "%PYEXE%" "%MCP_DIR%\codex_tool_proxy.py"
    timeout /t 3 /nobreak >nul
    netstat -an | findstr ":15730 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (echo   [OK] 端口 15730 已恢复) else (echo   [FAIL] 端口 15730 拉起失败 & set /a ERRORS+=1)
)

echo.

:: ---- 2. Codex CLI 检查 ----
echo [2/4] Codex CLI 检查...
codex --version >nul 2>&1
if not errorlevel 1 (
    echo   [OK] Codex CLI 可用
) else (
    echo   [FIX] Codex CLI 不可用，重建 shim...
    (
    echo @ECHO off
    echo node "I:\npm\node_modules\@openai\codex\bin\codex.js" %%*
    ) > "%APPDATA%\npm\codex.cmd"
    (
    echo #!/bin/sh
    echo exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
    ) > "%APPDATA%\npm\codex"
    codex --version >nul 2>&1
    if not errorlevel 1 (echo   [OK] Codex CLI 已恢复) else (echo   [FAIL] Codex CLI 恢复失败 & set /a ERRORS+=1)
)

echo.

:: ---- 3. Claude Code 检查 ----
echo [3/4] Claude Code 检查...
where claude >nul 2>&1
if not errorlevel 1 (
    echo   [OK] Claude Code 在 PATH 中
) else (
    echo   [SKIP] Claude Code 不在 PATH 中
)

echo.

:: ---- 4. API 连通验证 ----
echo [4/4] API 连通验证...
curl -s --connect-timeout 3 http://127.0.0.1:15721/health >nul 2>&1
if not errorlevel 1 (echo   [OK] 端口 15721 连通) else (echo   [FAIL] 端口 15721 不可达 & set /a ERRORS+=1)

curl -s --connect-timeout 3 http://127.0.0.1:15730/health >nul 2>&1
if not errorlevel 1 (echo   [OK] 端口 15730 连通) else (echo   [FAIL] 端口 15730 不可达 & set /a ERRORS+=1)

echo.
echo =========================================
if "%ERRORS%"=="0" (
    echo   ✅ 全部就绪！零错误
    echo.
    echo   Claude Code → http://127.0.0.1:15721
    echo   Codex CLI   → http://127.0.0.1:15730
    echo.
    echo   可以直接启动 Claude Code 或 Codex
) else (
    echo   ⚠️ %ERRORS% 项异常，请检查上方日志
)
echo =========================================
echo.

if "%1"=="--auto" goto :end
echo 按任意键退出...
pause >nul
:end
endlocal
