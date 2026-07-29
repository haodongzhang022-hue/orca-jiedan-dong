@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo  注册龙虾舰队自动恢复计划任务
echo ============================================
echo.

:: 检查是否已存在
schtasks /query /tn "LobsterFleet_AutoRestore" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] 计划任务已存在，更新中...
    schtasks /delete /tn "LobsterFleet_AutoRestore" /f >nul 2>&1
)

:: 创建计划任务：用户登录时自动执行
schtasks /create ^
    /tn "LobsterFleet_AutoRestore" ^
    /tr "cmd /c \"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\fleet_auto_restore.cmd --auto\"" ^
    /sc onlogon ^
    /rl highest ^
    /f

if not errorlevel 1 (
    echo [OK] 计划任务注册成功
    echo      名称: LobsterFleet_AutoRestore
    echo      触发: 用户登录时
    echo      脚本: fleet_auto_restore.cmd
) else (
    echo [FAIL] 注册失败，请以管理员权限运行
)

echo.
echo 按任意键退出...
pause >nul
