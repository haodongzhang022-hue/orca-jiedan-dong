@echo off
REM ============================================================
REM 一键拉起_CNB云原生DeepSeekV4Flash.bat
REM 所属模板：一键拉起云上Deepseek V4-Flash 标准版
REM ------------------------------------------------------------
REM 用途：一键拉起 CNB 云原生 DeepSeek-V4-Flash 免费模型舰队
REM 平台：cnb.cool → @CodeBuddy / @仓库(codex) / @仓库(claude-code)
REM 免费到 2026年12月底，无需 API Key，零本地占用
REM 模型基座：deepseek-v4-flash（替代 MiMo V2.5，三层分工不变）
REM ============================================================

echo [龙虾舰队] 一键拉起 CNB 云原生 DeepSeek-V4-Flash ...
echo.

REM [1/3] 检查代理端口
echo [1/3] 检查代理端口...
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

REM [2/3] 设置环境变量
echo [2/3] 设置环境变量...
set CNB_PLATFORM=cnb.cool
set CNB_MODEL=deepseek-v4-flash
set CNB_FREE_UNTIL=2026-12-31
echo    CNB_PLATFORM=%CNB_PLATFORM%
echo    CNB_MODEL=%CNB_MODEL%

REM [3/3] 完成
echo.
echo ============================================
echo [完成] CNB 云原生 DeepSeek-V4-Flash 已拉起
echo - 平台: cnb.cool
echo - 使用: @CodeBuddy / @仓库(codex) / @仓库(claude-code)
echo - 免费到: 2026年12月底
echo - API Key: 不需要
echo - 本地占用: 零内存/显存
echo - 模型基座: deepseek-v4-flash（替代 MiMo V2.5）
echo - 三层分工: Hermes/Codex/Claude Code 保持不变
echo ============================================
echo.
pause
