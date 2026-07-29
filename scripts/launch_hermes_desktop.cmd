@echo off
REM ============================================================
REM launch_hermes_desktop.cmd — Hermes 双实例启动器（存量复用）
REM 分支结论: Hermes 运行时已安装于 C:\Users\Administrator\AppData\Local\hermes
REM           （venv + hermes-agent 完整），无需重复安装 E:\tmp\Hermes-Setup.exe
REM GUI = Hermes 内置 Web GUI 服务器，端口 15800（已实测监听）
REM 程序本体: 既有安装 | 数据: G盘 | 总线端口: 15800
REM ============================================================
chcp 65001 >nul
set "HERMES_BIN=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts"
set "ORCA_G_DATA=G:\龙虾AI主控中心\ORCA数据"
set "ORCA_BUS_PORT=15800"

REM 1) 端口占用检查（若已监听说明GUI已常驻，直接打开面板）
netstat -ano | findstr ":15800" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo [OK] Hermes GUI 已在 15800 常驻，打开面板...
  start "" "http://127.0.0.1:15800/"
  exit /b 0
)

REM 2) 未监听则启动 Hermes GUI 实例
if exist "%HERMES_BIN%\hermes.exe" (
  echo [OK] 启动 Hermes GUI 实例 (端口 %ORCA_BUS_PORT%)...
  start "Hermes-GUI" "%HERMES_BIN%\hermes.exe" gui --port %ORCA_BUS_PORT%
) else (
  echo [WARN] venv 内未找到 hermes.exe，尝试 PATH 调用...
  start "Hermes-GUI" hermes gui --port %ORCA_BUS_PORT%
)

timeout /t 5 /nobreak >nul
netstat -ano | findstr ":15800" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
  echo [OK] Hermes GUI 启动成功
  start "" "http://127.0.0.1:15800/"
) else (
  echo [ERROR] Hermes GUI 启动失败，请检查 C:\Users\Administrator\AppData\Local\hermes\logs
  exit /b 1
)
exit /b 0
