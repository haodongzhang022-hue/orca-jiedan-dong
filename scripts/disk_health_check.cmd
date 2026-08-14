@echo off
rem ============================================
rem  Disk Health Check (C drive space + desktop shortcut + junction targets)
rem  Created 2026-08-14 after WeChat failed to open (desktop shortcut symlink
rem  pointed to a moved-away F: dir; xwechat junction target missing; C: 100% full)
rem  Pure ASCII on purpose - GBK cmd cannot render UTF-8 paths.
rem ============================================

set LOG=E:\??AI????\??AI??\???????????\logs\disk_health.log
echo [%date% %time%] ====== Disk Health Check Start ====== >> "%LOG%"

rem ---------- 1. C drive free space alert (<2GB = risk) ----------
rem PowerShell is locale-safe (findstr "bytes free" fails on zh-CN cmd)
for /f "delims=" %%a in ('powershell -NoProfile -Command "[math]::Round((Get-PSDrive C).Free/1MB,0)"') do set FREEMB=%%a
if "%FREEMB%"=="" set FREEMB=0
echo [%date% %time%] C drive free: %FREEMB% MB >> "%LOG%"
if %FREEMB% LSS 2048 (
  echo [%date% %time%] ALERT: C drive free below 2GB ^( %FREEMB% MB ^) - clean Docker/wsl caches! >> "%LOG%"
  msg * "C drive free below 2GB! Please clean Docker/wsl caches to avoid app crashes." >nul 2>&1
)

rem ---------- 2. Desktop WeChat shortcut target check ----------
if exist "C:\Users\Administrator\Desktop\WeChatSetup.exe" (
  echo [%date% %time%] ALERT: Desktop WeChatSetup.exe still exists - check it is not a broken symlink to F: >> "%LOG%"
) else (
  echo [%date% %time%] Desktop WeChatSetup.exe gone - OK (??.lnk points to real Weixin.exe) >> "%LOG%"
)
if exist "C:\Users\Administrator\Desktop\??.lnk" (
  echo [%date% %time%] Desktop ??.lnk present - OK >> "%LOG%"
) else (
  echo [%date% %time%] ALERT: Desktop ??.lnk missing! >> "%LOG%"
)

rem ---------- 3. xwechat junction target check ----------
if exist "C:\Users\Administrator\AppData\Roaming\Tencent\xwechat\crashinfo" (
  echo [%date% %time%] xwechat real dir OK (crashinfo present) >> "%LOG%"
) else (
  echo [%date% %time%] ALERT: xwechat\crashinfo missing - WeChat crash reporter will fail! >> "%LOG%"
)

echo [%date% %time%] ====== Disk Health Check Done ====== >> "%LOG%"
exit /b 0
