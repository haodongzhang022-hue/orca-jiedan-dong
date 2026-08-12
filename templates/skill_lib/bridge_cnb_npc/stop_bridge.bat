@echo off
chcp 65001 >nul
title CNB-V4-BRIDGE 停止

echo [停止] CNB-V4-BRIDGE 桥接网关...
taskkill /f /im python.exe /fi "WINDOWTITLE eq CNB-V4-BRIDGE*" >nul 2>&1

REM 停止监听9000端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":9000" ^| findstr "LISTENING"') do (
    echo [停止] 端口9000进程 PID:%%a
    taskkill /f /pid %%a >nul 2>&1
)

echo [完成] 桥接网关已停止
pause
