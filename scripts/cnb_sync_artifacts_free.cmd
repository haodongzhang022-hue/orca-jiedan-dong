@echo off
REM ============================================================
REM   scripts/cnb_sync_artifacts_free.cmd
REM   Push this workspace to CNB free (orca-jiedan, public)
REM   ZERO COST: git push only, no LLM call
REM   触发词: 同步CNB / 云端同步 / cnb push / 原路同步
REM   整理: Codex 2026-08-20
REM ============================================================

setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0..
cd /d "%ROOT%"

echo ============================================================
echo   [CNB SYNC] Push workspace to cnb.cool (free, public)
echo   remote:  https://cnb.cool/TJF19770107/orca-jiedan.git
echo   ZERO COST: git push, no LLM
echo ============================================================
echo.

REM ---- 1. Verify CNB_TOKEN
echo [STEP 1/7] Verify CNB_TOKEN injection
if "%CNB_TOKEN%"=="" (
    echo   [WARN] CNB_TOKEN not set in env, will use local credential cache
) else (
    echo   [OK] CNB_TOKEN prefix: !CNB_TOKEN:~0,8!...
)

REM ---- 2. Verify git remote
echo [STEP 2/7] Verify git remote origin
git remote get-url origin 2>nul
if errorlevel 1 (
    echo   [ERROR] no git remote configured
    exit /b 1
)

REM ---- 3. Status snapshot
echo.
echo [STEP 3/7] git status snapshot
git status --short

REM ---- 4. Add all
echo.
echo [STEP 4/7] git add -A
git add -A

REM ---- 5. Commit (if needed)
echo [STEP 5/7] git commit -m "automation: 1234 sync artifacts (CNB free push)"
git commit -m "automation: 1234 sync artifacts (CNB free push at %date% %time%)" 2>nul
if errorlevel 1 (
    echo   [INFO] nothing to commit, or commit cached
)

REM ---- 6. Push to CNB (origin = cnb.cool direct)
echo.
echo [STEP 6/7] git push origin main  (cnb.cool direct)
REM Force-clear any proxy that breaks CNB handshake
HTTPS_PROXY= HTTP_PROXY= https_proxy= http_proxy= GIT_TERMINAL_PROMPT=0 ^ git -c http.proxy= -c https.proxy= push "https://oauth2:%CNB_TOKEN%@cnb.cool/TJF19770107/orca-jiedan.git" HEAD:main 2>&1
if errorlevel 1 (
    echo   [ERROR] push failed, try alternative remote path
    git push origin HEAD:main
)

REM ---- 7. Verify
echo.
echo [STEP 7/7] git log --oneline -3
git log --oneline -3

echo.
echo ============================================================
echo   [CNB SYNC] DONE.
echo   Public URL: https://cnb.cool/TJF19770107/orca-jiedan
echo ============================================================
echo.
endlocal
exit /b 0
