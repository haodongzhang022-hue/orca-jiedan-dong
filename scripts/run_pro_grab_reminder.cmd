@echo off
rem ASCII-only wrapper (avoid GBK/UTF-8 mixup with Chinese paths in cmd)
cd /d "%~dp0"
"C:\Program Files\Git\bin\bash.exe" -lc "bash 'remind_pro_grab.sh'"
exit /b 0
