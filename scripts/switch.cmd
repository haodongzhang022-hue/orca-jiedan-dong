@echo off
chcp 65001 >nul
REM 双实例一键切换: switch --agent hermes --to gui  /  switch --agent codex --to cli
set PROJ=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
set CORE=E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\dual_core
set PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PYEXE%" set PYEXE=python
"%PYEXE%" "%CORE%\orca_switch.py" --project "%PROJ%" %*
