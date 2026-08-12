@echo off
rem ============================================
rem  Disk Cleanup Task (C/D/E/F drives, keep >10G)
rem  Only safe items: recycle bins, temp dirs, caches
rem ============================================

set LOG=E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\logs\disk_cleanup.log
echo [%date% %time%] ====== Disk Cleanup Start ====== >> "%LOG%"

rem ---------- 1. Empty recycle bins (PowerShell, all drives) ----------
powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
echo [%date% %time%] Recycle bins cleared >> "%LOG%"

rem ---------- 2. System temp dirs ----------
rd /s /q "C:\Users\Administrator\AppData\Local\Temp" 2>nul
mkdir "C:\Users\Administrator\AppData\Local\Temp" 2>nul
del /q /f "C:\Windows\Temp\*" 2>nul
echo [%date% %time%] Temp dirs cleared >> "%LOG%"

rem ---------- 3. E drive temp dirs (full clear, they are temp by nature) ----------
rd /s /q "E:\tmp" 2>nul
mkdir "E:\tmp" 2>nul
rd /s /q "E:\temp" 2>nul
mkdir "E:\temp" 2>nul
echo [%date% %time%] E:\tmp E:\temp fully cleared >> "%LOG%"

rem ---------- 4. Package manager caches ----------
rd /s /q "C:\Users\Administrator\AppData\Local\npm-cache" 2>nul
rd /s /q "C:\Users\Administrator\AppData\Local\uv\cache" 2>nul
rd /s /q "C:\Users\Administrator\.cache" 2>nul
echo [%date% %time%] Package caches cleared >> "%LOG%"

echo [%date% %time%] ====== Disk Cleanup Done ====== >> "%LOG%"
exit /b 0
