@echo off
chcp 65001 >nul
title CNB-V4-BRIDGE 桥接网关

set BRIDGE_ROOT=%~dp0
cd /d "%BRIDGE_ROOT%"

echo ============================================================
echo  CNB-V4-BRIDGE 桥接网关 v1.0
echo  CNB云端 DeepSeek V4 Flash -^> 本地桌面端
echo ============================================================

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查依赖
pip show httpx >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] httpx...
    pip install httpx
)

REM 检查Token
if "%CNB_NPC_API_TOKEN%"=="" (
    echo [警告] CNB_NPC_API_TOKEN 环境变量未设置
    echo 请先设置: set CNB_NPC_API_TOKEN=your_token_here
    echo 或者修改 config\token_config.json 中的 token 字段
    echo.
)

echo [启动] 桥接网关服务...
python bridge_server.py

pause
