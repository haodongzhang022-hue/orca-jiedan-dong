@echo off
REM ============================================
REM 舰队一键启动脚本：Ollama Cloud DeepSeek
REM 用途：量化策略、代码编写、长上下文任务
REM 限制：5小时刷新算力配额，高峰期可能429
REM ============================================

echo [龙虾舰队] 启动 Ollama Cloud DeepSeek 模式...
echo.

REM 设置配置文件路径
set FLEET_CONFIG=%~dp0config\fleet_profiles\ollama_ds.env
set PROJECT_ROOT=%~dp0

REM 加载配置
echo [1/6] 加载Ollama DS配置...
if exist "%FLEET_CONFIG%" (
    echo    配置文件: %FLEET_CONFIG%
) else (
    echo    [错误] 配置文件不存在: %FLEET_CONFIG%
    pause
    exit /b 1
)

REM 检查Ollama服务
echo [2/6] 检查Ollama服务...
netstat -ano | findstr ":11434" >nul 2>&1
if %errorlevel% equ 0 (
    echo    Ollama服务 11434: 运行中
) else (
    echo    Ollama服务 11434: 未运行，正在启动...
    start /min "Ollama-Server" ollama serve
    timeout /t 5 >nul
    netstat -ano | findstr ":11434" >nul 2>&1
    if %errorlevel% neq 0 (
        echo    [错误] Ollama启动失败，请手动启动
        pause
        exit /b 1
    )
)

REM 检查内存
echo [3/6] 检查系统内存...
for /f "tokens=2 delims==" %%a in ('wmic OS get TotalVisibleMemorySize /value') do set /a TOTAL_MEM=%%a/1024
for /f "tokens=2 delims==" %%a in ('wmic OS get FreePhysicalMemory /value') do set /a FREE_MEM=%%a/1024
echo    总内存: %TOTAL_MEM%MB
echo    可用内存: %FREE_MEM%MB
if %FREE_MEM% LSS 2048 (
    echo    [警告] 可用内存不足2GB，建议切换到官方DS线路
)

REM 检查端口
echo [4/6] 检查代理端口...
netstat -ano | findstr ":15721" >nul 2>&1
if %errorlevel% equ 0 (
    echo    Anthropic代理 15721: 运行中
) else (
    echo    Anthropic代理 15721: 未运行，正在启动...
    start /min "Anthropic-15721" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
    timeout /t 3 >nul
)

REM 设置环境变量
echo [5/6] 设置Ollama DS环境变量...
set MODEL_NAME=deepseek-v4-flash:0731-cloud
set API_BASE_URL=http://127.0.0.1:11434/v1
set FALLBACK_ENABLED=true
set FALLBACK_TARGET=official_ds

REM 启动舰队
echo [6/6] 启动舰队...
cd /d "%PROJECT_ROOT%"
start "Hermes-OllamaDS" cmd /k "title Hermes-OllamaDS && echo [Ollama DS模式] Hermes已启动 && bash"
start "Claude-OllamaDS" cmd /k "title Claude-OllamaDS && echo [Ollama DS模式] Claude Code已启动 && bash"

echo.
echo ============================================
echo [完成] Ollama Cloud DeepSeek 舰队已启动
echo - Hermes: 后台运行
echo - Claude Code: 后台运行
echo - 视觉任务: 自动旁路MIMO
echo - 降级策略: 429时自动切官方API
echo ============================================
echo.
pause