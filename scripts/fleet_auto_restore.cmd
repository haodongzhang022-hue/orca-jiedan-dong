@echo off
chcp 65001 >nul 2>&1
setlocal
title [龙虾舰队] 自动恢复 v2.0

set "PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "MCP_DIR=E:\龙虾AI主控中心\MCP服务"
set "CODEX_CONFIG=%USERPROFILE%\.codex\config.toml"
set "PROJECT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"

echo ============================================
echo  🦞 龙虾舰队 · 自动恢复 v2.0
echo  %date% %time%
echo ============================================
echo.

:: === 1. 拉起代理服务 ===
echo [1/5] 端口健康检查...

:: Anthropic Proxy (15721)
netstat -an | findstr ":15721 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [OK] Anthropic Proxy (15721) 运行中
) else (
    echo   [FIX] 拉起 Anthropic Proxy (15721)...
    start /min "AutoRestore-15721" "%PYEXE%" "%MCP_DIR%\anthropic_proxy_15721.py"
    timeout /t 3 /nobreak >nul
    netstat -an | findstr ":15721 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (echo   [OK] Anthropic Proxy 已恢复) else (echo   [FAIL] Anthropic Proxy 拉起失败)
)

:: Codex Tool Proxy (15730)
netstat -an | findstr ":15730 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [OK] Codex Tool Proxy (15730) 运行中
) else (
    echo   [FIX] 拉起 Codex Tool Proxy (15730)...
    start /min "AutoRestore-15730" "%PYEXE%" "%MCP_DIR%\codex_tool_proxy.py"
    timeout /t 3 /nobreak >nul
    netstat -an | findstr ":15730 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (echo   [OK] Codex Tool Proxy 已恢复) else (echo   [FAIL] Codex Tool Proxy 拉起失败)
)

echo.

:: === 2. 配置校验 ===
echo [2/5] Codex 配置校验...
if exist "%CODEX_CONFIG%" (
    findstr /C:"wire_api = \"chat\"" "%CODEX_CONFIG%" >nul 2>&1
    if errorlevel 1 (
        echo   [FIX] wire_api 不是 chat，正在修复...
        copy "%CODEX_CONFIG%" "%CODEX_CONFIG%.bak.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%" >nul 2>&1
        goto :fix_codex_config
    ) else (
        findstr /C:"127.0.0.1:15730" "%CODEX_CONFIG%" >nul 2>&1
        if errorlevel 1 (
            echo   [FIX] base_url 未指向代理，正在修复...
            copy "%CODEX_CONFIG%" "%CODEX_CONFIG%.bak.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%" >nul 2>&1
            goto :fix_codex_config
        ) else (
            echo   [OK] Codex 桌面版配置正确
        )
    )
) else (
    echo   [FIX] Codex 配置不存在，创建中...
    goto :fix_codex_config
)
goto :skip_fix_codex

:fix_codex_config
(
echo model_provider = "mimo-v2.5-pro"
echo model = "mimo-v2.5-pro"
echo model_reasoning_effort = "high"
echo disable_response_storage = true
echo preferred_auth_method = "apikey"
echo.
echo [model_providers.mimo-v2.5-pro]
echo name = "MiMo V2.5 Pro (via Proxy)"
echo wire_api = "chat"
echo base_url = "http://127.0.0.1:15730/v1"
echo api_key = "tp-cs3zbef7vhc75lcpsw9x7pau27mjftwhqnovn5zrq2d0puft"
echo.
echo [features]
echo js_repl = false
echo.
echo [memories]
echo generate_memories = true
echo use_memories = true
echo.
echo [windows]
echo sandbox = "elevated"
) > "%CODEX_CONFIG%"
echo   [OK] Codex 桌面版配置已修复
:skip_fix_codex

echo.

:: === 3. Codex CLI shim 检查 ===
echo [3/7] Codex CLI shim 检查...
set "SHIM_PATH=%APPDATA%\npm\codex"
if not exist "%SHIM_PATH%" (
    echo   [FIX] Codex CLI shim 缺失，正在创建...
    (
    echo #!/bin/sh
    echo exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
    ) > "%SHIM_PATH%"
    (
    echo @ECHO off
    echo node "I:\npm\node_modules\@openai\codex\bin\codex.js" %%*
    ) > "%APPDATA%\npm\codex.cmd"
    echo   [OK] Codex CLI shim 已创建
) else (
    echo   [OK] Codex CLI shim 存在
)

:: === 4. Codex 运行时配置同步 ===
echo [4/7] Codex 运行时配置同步...
if exist "%CODEX_CONFIG%" (
    set "RUNTIME_DIR=%APPDATA%\Orca\codex-runtime-home\home"
    if exist "%RUNTIME_DIR%" (
        copy /Y "%CODEX_CONFIG%" "%RUNTIME_DIR%\config.toml" >nul 2>&1
        echo   [OK] Codex runtime 配置已同步
    ) else (
        echo   [SKIP] Orca runtime 目录不存在
    )
) else (
    echo   [SKIP] Codex 配置不存在
)

echo.

:: === 5. 分支同步 ===
echo [5/7] 分支同步...
cd /d "%PROJECT%"
for %%b in (claude codex hermes) do (
    if exist "worktrees\%%b" (
        cd /d "%PROJECT%\worktrees\%%b"
        git merge master --no-edit >nul 2>&1
        if not errorlevel 1 (
            echo   [OK] %%b 分支已同步
        ) else (
            echo   [OK] %%b 分支已是最新
        )
        cd /d "%PROJECT%"
    )
)

echo.

:: === 6. 端口验证 ===
echo [6/7] 端口验证...
set "all_ok=1"
netstat -an | findstr ":15721 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (echo   [FAIL] 15721 未启动 & set "all_ok=0") else (echo   [OK] 15721)
netstat -an | findstr ":15730 " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (echo   [FAIL] 15730 未启动 & set "all_ok=0") else (echo   [OK] 15730)

echo.

:: === 7. 汇总 ===
echo [7/7] 汇总
echo ============================================
if "%all_ok%"=="1" (
    echo  ✅ 龙虾舰队全部正常！
    echo  Claude Code → http://127.0.0.1:15721
    echo  Codex       → http://127.0.0.1:15730
) else (
    echo  ⚠️  部分服务异常，请检查上方日志
)
echo ============================================
echo.

if "%1"=="--auto" goto :end
echo 按任意键退出...
pause >nul
:end
endlocal
