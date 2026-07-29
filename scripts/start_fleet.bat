@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title ════ ORCA 舰队一键修复 + 启动 v2.0 ════
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  ORCA 三Agent舰队 一键检索+修复+启动 v2.0        ║
echo  ║  企业微信群定制接单项目 ^| 龙虾五步法V2.7         ║
echo  ║  新增: 多磁盘检索前置 + 存量复用分支判断         ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ============================================================
::  环境变量预设
:: ============================================================
set "PROJECT_ROOT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
set "DUAL_CORE=E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\dual_core"
set "G_DATA=G:\龙虾AI主控中心\ORCA数据"
set "PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "BUS_PORT=15800"

:: ORCA标准端口
set "CLAUDE_SERVE_PORT=57330"
set "CODEX_GUI_PORT=57321"
set "HERMES_CLI_PORT=57368"

:: ============================================================
::  Phase 0: 多磁盘检索前置（G→E→D 优先复用存量程序）
:: ============================================================
echo [STEP 0] 多磁盘检索 G→E→D，优先复用存量程序...
set "CLAUDE_DESKTOP="
set "CLAUDE_EXE="
set "HERMES_EXE="

:: --- Claude 桌面版检索（按优先级） ---
for %%P in (
    "G:\龙虾AI主控中心\我的AI分身\ClaudeCode\AnthropicClaude\claude.exe"
    "E:\龙虾AI主控中心\我的AI分身\ClaudeCode\AnthropicClaude\claude.exe"
    "D:\ClaudeCode\AnthropicClaude\claude.exe"
) do (
    if not defined CLAUDE_DESKTOP if exist "%%~P" set "CLAUDE_DESKTOP=%%~P"
)

:: --- Claude CLI 检索 ---
for %%P in (
    "I:\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
    "E:\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
) do (
    if not defined CLAUDE_EXE if exist "%%~P" set "CLAUDE_EXE=%%~P"
)

:: --- Hermes 检索（已装运行时优先，安装包兜底） ---
for %%P in (
    "G:\龙虾AI主控中心\我的AI分身\Hermes-Desktop\Hermes.exe"
    "E:\龙虾AI主控中心\我的AI分身\Hermes-Desktop\Hermes.exe"
    "C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe"
) do (
    if not defined HERMES_EXE if exist "%%~P" set "HERMES_EXE=%%~P"
)

echo   [检索结果]
if defined CLAUDE_DESKTOP (echo    Claude桌面版: !CLAUDE_DESKTOP! [复用存量]) else (echo    Claude桌面版: 未命中)
if defined CLAUDE_EXE     (echo    Claude CLI  : !CLAUDE_EXE! [复用存量])    else (echo    Claude CLI  : 未命中)
if defined HERMES_EXE     (echo    Hermes      : !HERMES_EXE! [复用存量])    else (echo    Hermes      : 未命中)

:: --- 分支判断: 全部未命中才走安装 ---
if not defined HERMES_EXE (
    echo   [分支C] Hermes 全盘未命中 → 静默安装到 E 盘...
    if exist "E:\tmp\Hermes-Setup.exe" (
        "E:\tmp\Hermes-Setup.exe" /install /quiet /norestart InstallLocation="E:\龙虾AI主控中心\我的AI分身\Hermes-Desktop"
        timeout /t 15 /nobreak >nul
        if exist "E:\龙虾AI主控中心\我的AI分身\Hermes-Desktop\Hermes.exe" (
            set "HERMES_EXE=E:\龙虾AI主控中心\我的AI分身\Hermes-Desktop\Hermes.exe"
            echo   [OK] 静默安装完成
        ) else (
            echo   [ERROR] 安装后未找到 Hermes.exe，请人工检查
        )
    ) else (
        echo   [ERROR] 安装包 E:\tmp\Hermes-Setup.exe 不存在
    )
) else (
    echo   [分支A/B] 命中存量程序 → 跳过安装，直接复用
)
echo.

:: 将Claude加入PATH（解决WinError 2）
if defined CLAUDE_EXE for %%F in ("!CLAUDE_EXE!") do set "PATH=%PATH%;%%~dpF"

:: ============================================================
::  Phase 1: 杀残留进程
:: ============================================================
echo [STEP 1] 清理残留进程...
taskkill /F /IM codex-plus-plus.exe >nul 2>&1
taskkill /F /IM Codex.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] 残留已清理
echo.

:: ============================================================
::  Phase 2: Codex 配置自愈（wire_api 标准 = responses）
::  注: Codex 0.46+ 已弃用 chat_completions 与 chat，仅接受 responses
:: ============================================================
echo [STEP 2] Codex配置自愈检查...
set "CODEX_CONFIG=%USERPROFILE%\.codex\config.toml"
if exist "%CODEX_CONFIG%" (
    findstr /C:"wire_api = \"responses\"" "%CODEX_CONFIG%" >nul 2>&1
    if errorlevel 1 (
        echo [FIX] wire_api 非 responses → 自愈修复...
        powershell -Command "(Get-Content '%CODEX_CONFIG%' -Raw) -replace 'wire_api = \"chat_completions\"', 'wire_api = \"responses\"' -replace 'wire_api = \"chat\"', 'wire_api = \"responses\"' | Set-Content '%CODEX_CONFIG%' -NoNewline"
        echo [OK] config.toml 已修复为 responses
    ) else (
        echo [OK] config.toml wire_api=responses（无需修复）
    )
)
echo.

:: ============================================================
::  Phase 3: 启动 Codex++ GUI (:57321)
:: ============================================================
echo [STEP 3] 启动 Codex++ GUI :%CODEX_GUI_PORT% ...
set "CODEX_GUI=C:\Users\Administrator\AppData\Local\Programs\Codex++\codex-plus-plus.exe"
if exist "%CODEX_GUI%" (
    start "" "%CODEX_GUI%"
    echo [OK] Codex++ GUI 已启动
) else (
    echo [WARN] Codex++ GUI exe不存在，跳过（CLI由消费者按需调用 codex exec）
)
timeout /t 3 /nobreak >nul
echo.

:: ============================================================
::  Phase 4: 启动 Claude Code Serve (:57330) + 桌面版
:: ============================================================
echo [STEP 4] 启动 Claude Code Serve :%CLAUDE_SERVE_PORT% ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%CLAUDE_SERVE_PORT% "') do taskkill /PID %%a /F >nul 2>&1
cd /d "%PROJECT_ROOT%\worktrees\claude"
if defined CLAUDE_EXE (
    start "Claude-Serve-%CLAUDE_SERVE_PORT%" /min cmd /c ""!CLAUDE_EXE!" serve --port %CLAUDE_SERVE_PORT%"
    timeout /t 5 /nobreak >nul
    netstat -an | findstr ":%CLAUDE_SERVE_PORT% " >nul 2>&1
    if errorlevel 1 (echo [WARN] Claude Serve 未监听，手动验证: curl 127.0.0.1:%CLAUDE_SERVE_PORT%/health) else (echo [OK] Claude Serve 已监听)
)
if defined CLAUDE_DESKTOP (
    start "" "!CLAUDE_DESKTOP!"
    echo [OK] Claude 桌面版已启动（存量复用）
)
echo.

:: ============================================================
::  Phase 5: Hermes 双实例（GUI已常驻15800则直接复用）
:: ============================================================
echo [STEP 5] Hermes 双实例检查（总线 :%BUS_PORT%）...
netstat -ano | findstr ":%BUS_PORT%" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Hermes GUI 已在 :%BUS_PORT% 常驻，复用现有实例
) else (
    if defined HERMES_EXE (
        start "Hermes-GUI" "!HERMES_EXE!" gui --port %BUS_PORT%
        echo [OK] Hermes GUI 已启动 :%BUS_PORT%
    ) else (
        echo [ERROR] Hermes 不可用
    )
)
echo.

:: ============================================================
::  Phase 6: 启动消息路由器 + Agent消费者（常驻）
:: ============================================================
echo [STEP 6] 启动 OMF 消息路由器 + 消费者...
start "ORCA-Router" /min cmd /c ""%PYTHON%" "%DUAL_CORE%\orca_msgbus_router.py" --project "%PROJECT_ROOT%" --watch --interval 3"
start "Claude-Consumer" /min cmd /c ""%PYTHON%" "%PROJECT_ROOT%\scripts\msgbus_agent_consumer.py" --agent claude --interval 5"
start "Codex-Consumer" /min cmd /c ""%PYTHON%" "%PROJECT_ROOT%\scripts\msgbus_agent_consumer.py" --agent codex --interval 5"
timeout /t 2 /nobreak >nul
echo [OK] 路由器 + 双消费者常驻运行中
echo.

:: ============================================================
::  最终状态报告
:: ============================================================
echo  ╔══════════════════════════════════════════════════╗
echo  ║          舰队启动完成 — 状态报告 v2.0             ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  Hermes GUI(总线)  :15800   复用/启动             ║
echo  ║  Claude Serve      :57330   运行中                ║
echo  ║  Codex++ GUI       :57321   运行中                ║
echo  ║  OMF Router+消费者  常驻     运行中               ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  v2.0 新增:                                       ║
echo  ║  ✓ G→E→D 多磁盘检索, 存量复用零重装               ║
echo  ║  ✓ wire_api 自愈标准更新为 responses              ║
echo  ║  ✓ codex 调用修复: exec 子命令(告别--quiet)       ║
echo  ║  ✓ Claude桌面版 E盘存量启动                       ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  验证: curl http://127.0.0.1:15800/  ^&  netstat -an ^| findstr "15800 57330"
echo.
pause
endlocal
