@echo off
chcp 65001 >nul
REM ORCA Hermes GUI (MiMO V2.5) - dual_core central runtime
set PROJ=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
set CORE=E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\dual_core
set PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PYEXE%" set PYEXE=python
start "ORCA-hermes-GUI-server" /min "%PYEXE%" "%CORE%\gui_server.py" --project "%PROJ%" --agent hermes --port 15800
timeout /t 2 /nobreak >nul
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:15800/ --user-data-dir="G:\龙虾AI主控中心\ORCA数据\edge_profiles\wecom_hermes"
