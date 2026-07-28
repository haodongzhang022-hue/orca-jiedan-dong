@echo off
chcp 65001 >nul 2>&1
setlocal
title [龙虾舰队] 服务恢复 - Codex/Claude Code 代理

set "PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "MCP_DIR=E:\龙虾AI主控中心\MCP服务"

echo ============================================
echo  龙虾舰队一键启动 v1.0
echo  恢复 Codex + Claude Code 连通性
echo ============================================
echo.

:: 检查 Python
if not exist "%PYEXE%" (
    echo [ERROR] 系统 Python 未找到: %PYEXE%
    pause
    exit /b 1
)

:: === 1. Anthropic 代理 (15721) - Claude Code 依赖 ===
netstat -an | findstr ":15721 " >nul 2>&1
if not errorlevel 1 (
    echo [OK] Anthropic 代理 已在运行 (15721)
) else (
    echo [START] 启动 Anthropic 代理 (15721)...
    start /min "Anthropic-Proxy-15721" "%PYEXE%" "%MCP_DIR%\anthropic_proxy_15721.py"
    timeout /t 2 /nobreak >nul
    netstat -an | findstr ":15721 " >nul 2>&1
    if not errorlevel 1 (echo [OK] Anthropic 代理 启动成功) else (echo [FAIL] Anthropic 代理 启动失败)
)

:: === 2. Codex 工具代理 (15730) - Codex 依赖 ===
netstat -an | findstr ":15730 " >nul 2>&1
if not errorlevel 1 (
    echo [OK] Codex 工具代理 已在运行 (15730)
) else (
    echo [START] 启动 Codex 工具代理 (15730)...
    start /min "Codex-Tool-Proxy-15730" "%PYEXE%" "%MCP_DIR%\codex_tool_proxy.py"
    timeout /t 2 /nobreak >nul
    netstat -an | findstr ":15730 " >nul 2>&1
    if not errorlevel 1 (echo [OK] Codex 工具代理 启动成功) else (echo [FAIL] Codex 工具代理 启动失败)
)

echo.
echo ============================================
echo  服务状态汇总
echo ============================================
echo.
netstat -an | findstr -E "15721 15730 57320 57321" | findstr "LISTENING"
echo.
echo [INFO] Claude Code 应连接: http://127.0.0.1:15721
echo [INFO] Codex 应连接: http://127.0.0.1:15730
echo.
echo 按任意键退出...
pause >nul
endlocal
