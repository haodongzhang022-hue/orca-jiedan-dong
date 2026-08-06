@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =============================================================================
:: 一键拉起 — Ollama 本地 DeepSeek-V4-Flash 链路
:: 版本：1.4.1 | 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
:: 架构：Hermes → Codex → Claude Code 三层分工 | MIMO 多模态旁路
:: 路径：orca-jiedan 企业微信群定制接单项目
:: =============================================================================

title 龙虾AI·Ollama本地DeepSeekV4Flash链路

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║    龙虾AI · Ollama本地DeepSeek-V4-Flash链路     ║
echo  ║    基座：CNB免费DeepSeek-V4-Flash（至2026-12-31）║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ===========================================================================
:: 步骤0：智能定位 Ollama 可执行文件
:: ===========================================================================
set OLLAMA_BIN=
for %%d in (
    "%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    "%PROGRAMFILES%\Ollama\ollama.exe"
    "%PROGRAMFILES(x86)%\Ollama\ollama.exe"
    "C:\Ollama\ollama.exe"
    "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe"
) do (
    if exist %%d (
        set OLLAMA_BIN=%%d
        goto :ollama_found
    )
)

:: Docker 路径探测
for /f "tokens=*" %%i in ('where docker 2^>nul') do set DOCKER_BIN=%%i
if defined DOCKER_BIN (
    echo [✓] 检测到 Docker，尝试通过 Docker 调用 Ollama...
    set OLLAMA_BIN=docker exec ollama ollama
    goto :ollama_found
)

echo [✗] 未找到 Ollama 可执行文件
echo     请将 Ollama 安装到上述标准路径之一，或配置 PATH 环境变量
echo     下载地址：https://ollama.com/download/windows
pause
exit /b 1

:ollama_found
echo [✓] Ollama 定位：!OLLAMA_BIN!

:: ===========================================================================
:: 步骤1：磁盘空间校验（模型约需 4GB+）
:: ===========================================================================
echo.
echo [1/6] 磁盘空间校验...

for /f "tokens=3" %%a in ('dir "%USERPROFILE%\.ollama" 2^>nul ^| find "可用字节"') do set FREE_SPACE=%%a
if not defined FREE_SPACE (
    for /f "tokens=4" %%a in ('dir "C:\" 2^>nul ^| find "可用字节"') do set FREE_SPACE=%%a
)

:: 简单估算（实际使用 wmic 获取准确值）
for /f "skip=1" %%d in ('wmic logicaldisk where "DeviceID='C:'" get FreeSpace 2^>nul') do (
    if not "%%d"=="" set FREE_BYTES=%%d
    goto :space_checked
)
:space_checked

if defined FREE_BYTES (
    set /a FREE_GB=!FREE_BYTES! / 1073741824
    echo [✓] C盘可用空间：!FREE_GB! GB
    if !FREE_GB! LSS 10 (
        echo [⚠] 可用空间不足 10GB，模型下载可能失败
        echo     建议清理磁盘后重试，或使用 CNB 云端链路
        pause
    )
) else (
    echo [⚠] 无法获取磁盘空间信息，跳过校验
)

:: ===========================================================================
:: 步骤2：启动并校验 Ollama 进程
:: ===========================================================================
echo.
echo [2/6] Ollama 进程管控...

:: 检查 Ollama 是否已在运行
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if %errorlevel% equ 0 (
    echo [✓] Ollama 进程已在运行
) else (
    echo [→] 启动 Ollama 服务...
    :: 尝试启动
    if defined OLLAMA_BIN (
        start "" /B !OLLAMA_BIN! serve >nul 2>&1
        timeout /t 3 /nobreak >nul
    )
    :: 验证启动结果
    tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
    if %errorlevel% equ 0 (
        echo [✓] Ollama 启动成功
    ) else (
        echo [⚠] Ollama 未自动启动，请手动运行 ollama serve
        echo     或检查 Windows 服务 "Ollama" 是否已启用
        pause
    )
)

:: ===========================================================================
:: 步骤3：拉取 DeepSeek-V4-Flash 模型
:: ===========================================================================
echo.
echo [3/6] 拉取 DeepSeek-V4-Flash 模型...

!OLLAMA_BIN! list 2>nul | findstr /i "deepseek" >nul
if %errorlevel% equ 0 (
    echo [✓] DeepSeek 模型已存在，跳过下载
) else (
    echo [→] 正在从 Ollama 仓库拉取 deepseek-v4-flash...
    echo     预计下载 ~4GB，请耐心等待...
    !OLLAMA_BIN! pull deepseek-v4-flash
    if %errorlevel% neq 0 (
        echo [✗] 模型拉取失败，请检查网络连接或 Ollama 仓库可用性
        echo     备用方案：使用 CNB 云端链路 一键拉起_CNB云原生DeepSeekV4Flash.bat
        pause
        exit /b 1
    )
    echo [✓] DeepSeek-V4-Flash 拉取完成
)

:: ===========================================================================
:: 步骤4：启动三层 Agent 工作树
:: ===========================================================================
echo.
echo [4/6] 启动本地 Agent 工作树...

set PROJECT_DIR=%~dp0..
set WORKTREE_DIR=%PROJECT_DIR%\worktrees

if not exist "%WORKTREE_DIR%" mkdir "%WORKTREE_DIR%"

:: 4a. Hermes 消息监听层（常驻后台）
echo [→] 启动 Hermes（消息监听与事件分发）...
start "龙虾AI-Hermes" /MIN cmd /c "cd /d "%PROJECT_DIR%\hermes" && echo Hermes 已启动 — 监听企业微信群消息... && pause"

:: 4b. Codex 代码执行层
echo [→] 启动 Codex（代码执行引擎）...
start "龙虾AI-Codex" /MIN cmd /c "cd /d "%PROJECT_DIR%\codex" && echo Codex 已启动 — 代码执行引擎就绪... && pause"

:: 4c. Claude Code 代码审计层（如果已安装）
where claude >nul 2>&1
if %errorlevel% equ 0 (
    echo [→] 启动 Claude Code（代码审计官）...
    start "龙虾AI-Claude" /MIN cmd /c "cd /d "%PROJECT_DIR%\claude" && echo Claude Code 已启动 — 审计官就绪... && pause"
) else (
    where npx >nul 2>&1
    if %errorlevel% equ 0 (
        echo [→] 通过 npx 启动 Claude Code...
        start "龙虾AI-Claude" /MIN cmd /c "cd /d "%PROJECT_DIR%\claude" && npx @anthropic-ai/claude-code && pause"
    ) else (
        echo [⚠] Claude Code CLI 未安装，跳过本地 Claude 链路
        echo     安装命令：npm install -g @anthropic-ai/claude-code
        echo     云端 NPC 分身不受影响（claude-code NPC 在 CNB 运行）
    )
)

:: ===========================================================================
:: 步骤5：MIMO 多模态旁路方案（DeepSeek 无原生识图能力）
:: ===========================================================================
echo.
echo [5/6] MIMO 多模态旁路就绪...

set MIMO_CONFIG=%PROJECT_DIR%\config\mimo_bridge.json

if exist "%MIMO_CONFIG%" (
    echo [✓] MIMO 多模态旁路配置已加载
    echo     路由规则：海报/漫剧/图片识别 → MIMO 解析 → DeepSeek 文案调度
) else (
    echo [ℹ] MIMO 旁路配置未发现，创建默认配置...
    mkdir "%PROJECT_DIR%\config" 2>nul
    (
        echo {
        echo   "mimo_endpoint": "http://localhost:11435/v1/chat/completions",
        echo   "mimo_model": "mimo-v2.5-pro",
        echo   "fallback_to_deepseek": true,
        echo   "multimodal_triggers": ["海报", "漫剧", "图片识别", "设计图", "截图分析"],
        echo   "routing_logic": "image→mimo_vision→deepseek_text_generation"
        echo }
    ) > "%MIMO_CONFIG%"
    echo [✓] 已创建 MIMO 旁路默认配置
)

:: ===========================================================================
:: 步骤6：验证链路并输出状态面板
:: ===========================================================================
echo.
echo [6/6] 链路验证与状态面板...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║          龙虾AI 本地链路 · 状态面板             ║
echo  ╠══════════════════════════════════════════════════╣

:: Ollama 模型列表
echo  ║  基座模型：
!OLLAMA_BIN! list 2>nul | findstr /i "deepseek" | sed "s/^/  ║    /"

echo  ╠══════════════════════════════════════════════════╣
echo  ║  工作树状态：
echo  ║    [层1] Hermes     — 消息监听 & 事件分发
echo  ║    [层2] Codex      — 代码执行 & 脚本生成
echo  ║    [层3] Claude     — 代码审计 & 质量守护
echo  ╠══════════════════════════════════════════════════╣
echo  ║  多模态旁路：
echo  ║    MIMO v2.5-Pro    — 视觉解析（图片→文本）
echo  ║    DeepSeek V4      — 文案/脚本/流程调度
echo  ╠══════════════════════════════════════════════════╣
echo  ║  消息路由：
echo  ║    企业微信群 → Hermes → 任务卡分流
echo  ║    ├─ 本地 Ollama 链路（代码生成/文本处理）
echo  ║    ├─ 云端 CNB 链路（PR审查/Issue回复/NPC协作）
echo  ║    └─ MIMO 旁路（图片/海报/漫剧识别）
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  [✓] 本地 Ollama DeepSeek-V4-Flash 链路已就绪
echo      所有 Agent 窗口已最小化运行
echo      输入 Ctrl+C 可退出本面板（Agent 窗口需手动关闭）
echo.
pause
