@echo off
rem ASCII-only wrapper for codex_catalog_guard.py (avoid GBK/UTF-8 mixup with Chinese paths in cmd)
rem Called by scheduled task Lobster_CodexCatalogGuard every 5 minutes.
cd /d "%~dp0"
"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0codex_catalog_guard.py"
exit /b 0
