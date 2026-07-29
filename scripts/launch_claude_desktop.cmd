@echo off
REM ============================================================
REM launch_claude_desktop.cmd — Claude 桌面版启动器（存量复用）
REM 来源: G→E→D 多磁盘检索命中 (2026-07-28)
REM 程序本体: E盘 | 数据: G盘 | 总线端口: 15800
REM ============================================================
chcp 65001 >nul
set "CLAUDE_DESKTOP=E:\龙虾AI主控中心\我的AI分身\ClaudeCode\AnthropicClaude\claude.exe"
set "ORCA_G_DATA=G:\龙虾AI主控中心\ORCA数据"
set "ORCA_BUS_PORT=15800"

if not exist "%CLAUDE_DESKTOP%" (
  echo [ERROR] Claude 桌面版未找到: %CLAUDE_DESKTOP%
  echo [HINT] 请重新运行多磁盘检索或检查 registry.json desktop_binaries
  exit /b 1
)

echo [OK] 启动 Claude 桌面版 (总线端口 %ORCA_BUS_PORT%)...
start "" "%CLAUDE_DESKTOP%"
exit /b 0
