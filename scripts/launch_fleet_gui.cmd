@echo off
chcp 65001 >nul
REM ORCA all-agent GUI launcher (Mode C full fleet)
call "%~dp0launch_fleet_gui_hermes.cmd"
call "%~dp0launch_fleet_gui_codex.cmd"
call "%~dp0launch_fleet_gui_claude.cmd"
echo [OK] 3 GUI windows launched (57365/57366/57367)
