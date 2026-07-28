@echo off
chcp 65001 >nul 2>&1

:: 注册 Anthropic 代理计划任务
schtasks /create /tn "AnthropicProxy_AutoStart" /tr "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe E:\龙虾AI主控中心\MCP服务\anthropic_proxy_15721.py" /sc onlogon /rl highest /f

:: 注册 Codex 工具代理计划任务
schtasks /create /tn "CodexToolProxy_AutoStart" /tr "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe E:\龙虾AI主控中心\MCP服务\codex_tool_proxy.py" /sc onlogon /rl highest /f

:: 验证
echo.
echo === 验证 ===
schtasks /query /tn "AnthropicProxy_AutoStart" 2>nul && echo [OK] AnthropicProxy_AutoStart 已注册 || echo [FAIL]
schtasks /query /tn "CodexToolProxy_AutoStart" 2>nul && echo [OK] CodexToolProxy_AutoStart 已注册 || echo [FAIL]
