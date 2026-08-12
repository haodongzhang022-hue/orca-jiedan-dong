@echo off
rem ============================================================
rem  Lobster DiskCleanup - keep C/D/E/F above 10GB free
rem  Safe cleanup ONLY: recycle bin + temp files older than 7 days + package caches
rem  NOTE: upgrade candidate; ACTIVE scheduled task is
rem        Lobster_DiskCleanup_Daily -> scripts/cleanup_disk.cmd (daily 03:00)
rem  This file is wired via run_disk_cleanup.cmd (ASCII wrapper) but is
rem  NOT attached to any schtasks task yet - kept as the 10G-guard upgrade.
rem  Log: <project>/logs/disk_cleanup.log
rem  ASCII-only on purpose: GBK cmd cannot render UTF-8 Chinese paths.
rem ============================================================
set SCRIPT_DIR=%~dp0
set LOGDIR=%SCRIPT_DIR%..\logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
echo [%date% %time%] CLEANUP START >> "%LOGDIR%\disk_cleanup.log"

rem ---- 1. Empty recycle bins on C/D/E/F ----
for %%D in (C D E F) do (
  powershell -NoProfile -Command "Clear-RecycleBin -DriveLetter %%D -Force -ErrorAction SilentlyContinue" >> "%LOGDIR%\disk_cleanup.log" 2>&1
)

rem ---- 2. User temp older than 7 days (C: + E:) ----
powershell -NoProfile -Command "Get-ChildItem 'C:\Users\Administrator\AppData\Local\Temp' -Force -EA SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Recurse -Force -EA SilentlyContinue" >> "%LOGDIR%\disk_cleanup.log" 2>&1
powershell -NoProfile -Command "Get-ChildItem 'E:\temp' -Force -EA SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Recurse -Force -EA SilentlyContinue" >> "%LOGDIR%\disk_cleanup.log" 2>&1

rem ---- 3. Windows temp older than 7 days ----
powershell -NoProfile -Command "Get-ChildItem 'C:\Windows\Temp' -Force -EA SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item -Recurse -Force -EA SilentlyContinue" >> "%LOGDIR%\disk_cleanup.log" 2>&1

rem ---- 4. Package caches ----
"C:\Users\Administrator\AppData\Roaming\uv\uv.exe" cache clean >nul 2>&1
pip cache purge >nul 2>&1
if exist "C:\Users\Administrator\AppData\Local\npm-cache" rd /s /q "C:\Users\Administrator\AppData\Local\npm-cache" >nul 2>&1

echo [%date% %time%] CLEANUP DONE >> "%LOGDIR%\disk_cleanup.log"
exit /b 0
