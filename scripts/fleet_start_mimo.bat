@echo off
REM ============================================
REM 舰队一键启动脚本：MIMO V2.5 Pro
REM 用途：视觉任务、图文解析、K线截图分析
REM 到期：2026-08-14
REM ============================================

echo [龙虾舰队] 启动 MIMO V2.5 Pro 模式...
echo.

REM 设置配置文件路径
set FLEET_CONFIG=%~dp0config\fleet_profiles\mimo.env
set PROJECT_ROOT=%~dp0

REM 加载配置
echo [1/5] 加载MIMO配置...
if exist "%FLEET_CONFIG%" (
    echo    配置文件: %FLEET_CONFIG%
) else (
    echo    [错误] 配置文件不存在: %FLEET_CONFIG%
    pause
    exit /b 1
)

REM 检查端口
echo [2/5] 检查端口状态...
netstat -ano | findstr ":15721" >nul 2>&1
if %errorlevel% equ 0 (
    echo    Anthropic代理 15721: 运行中
) else (
    echo    Anthropic代理 15721: 未运行，正在启动...
    start /min "Anthropic-15721" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
    timeout /t 3 >nul
)

netstat -ano | findstr ":15730" >nul 2>&1
if %errorlevel% equ 0 (
    echo    Codex代理 15730: 运行中
) else (
    echo    Codex代理 15730: 未运行，正在启动...
    start /min "Codex-15730" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"
    timeout /t 3 >nul
)

REM 设置环境变量
echo [3/5] 设置MIMO环境变量...
set MODEL_NAME=mimo-v2.5-pro
set API_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
set VISION_PROVIDER=mimo

REM 启动Hermes
echo [4/5] 启动Hermes Agent...
cd /d "%PROJECT_ROOT%"
start "Hermes-MIMO" cmd /k "title Hermes-MIMO && echo [MIMO模式] Hermes已启动 && bash"

REM 启动Claude Code
echo [5/5] 启动Claude Code...
start "Claude-MIMO" cmd /k "title Claude-MIMO && echo [MIMO模式] Claude Code已启动 && bash"

echo.
echo ============================================
echo [完成] MIMO V2.5 Pro 舰队已启动
echo - Hermes: 后台运行
echo - Claude Code: 后台运行
echo - 视觉任务: MIMO原生支持
echo ============================================
echo.
pause