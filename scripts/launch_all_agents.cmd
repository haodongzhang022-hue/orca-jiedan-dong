@echo off
chcp 65001 >nul 2>&1
setlocal
title [龙虾舰队] 三Agent一键启动

set "PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "MCP_DIR=E:\龙虾AI主控中心\MCP服务"
set "PROJECT=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"

echo.
echo ╔═══════════════════════════════════════════════╗
echo ║   🦞 龙虾舰队 · 三Agent一键启动              ║
echo ║   %date% %time%
echo ╚═══════════════════════════════════════════════╝
echo.

:: Phase 1: 代理自愈
echo ▶ [Phase 1] 代理端口检查...
for %%p in (15721 15730) do (
    netstat -an | findstr ":%%p " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo   [OK] 端口 %%p
    ) else (
        echo   [FIX] 拉起端口 %%p...
        if "%%p"=="15721" start /min "Fleet-15721" "%PYEXE%" "%MCP_DIR%\anthropic_proxy_15721.py"
        if "%%p"=="15730" start /min "Fleet-15730" "%PYEXE%" "%MCP_DIR%\codex_tool_proxy.py"
        timeout /t 3 /nobreak >nul
    )
)

:: Phase 2: CLI校验
echo.
echo ▶ [Phase 2] CLI 工具校验...
codex --version >nul 2>&1
if not errorlevel 1 (echo   [OK] Codex CLI) else (echo   [!] Codex CLI 不可用)
where claude >nul 2>&1
if not errorlevel 1 (echo   [OK] Claude Code) else (echo   [!] Claude Code 不在 PATH)

:: Phase 3: 身份播报
echo.
echo ▶ [Phase 3] 三Agent身份播报
echo   ┌─────────────────────────────────────────┐
echo   │  🧠 Hermes    → 大脑/编排 (Hermes桌面)   │
echo   │  ⚡ Codex      → 执行器 (worktrees\codex) │
echo   │  🔍 Claude    → 审核器 (worktrees\claude) │
echo   └─────────────────────────────────────────┘

:: Phase 4: 完成
echo.
echo ▶ [Phase 4] 启动完成
echo.
echo   启动交互式终端：
echo     Codex:       cd %PROJECT%\worktrees\codex ^& codex
echo     Claude Code: cd %PROJECT%\worktrees\claude ^& claude
echo.
echo   或在 Orca IDE 中直接点击对应 Agent 标签页
echo.
echo =========================================
echo   ✅ 龙虾舰队就绪，等待指令
echo =========================================
echo.
pause
endlocal
