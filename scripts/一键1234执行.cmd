@echo off
chcp 65001 >nul
REM ============================================================
REM   scripts/一键1234执行.cmd
REM   TOP-LEVEL ENTRY POINT
REM   1234 = 1一人一公司 + 2双雄蒸馏 + 3三载体联动 + 4四化迭代
REM   零成本 (ZERO COST): 仅本地 bat 调度, 不调任何 LLM
REM   整理: Codex 2026-08-20 v2.1 (chcp 65001 加固 + 9 国际/三模式)
REM ============================================================
title LOBSTER 1234 DISPATCHER · ZERO COST v2.1

setlocal ENABLEDELAYEDEXPANSION
set ROOT=%~dp0..
set CHAIN=%ROOT%\scripts\1234
set LOGDIR=%ROOT%\logs
set STAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set STAMP=%STAMP: =0%

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
set LOG=%LOGDIR%\一键1234_%STAMP%.log

echo ============================================================   >  "%LOG%"
echo   [一键1234执行] Started at %date% %time%                    >> "%LOG%"
echo   ROOT=%ROOT%                                              >> "%LOG%"
echo ============================================================  >> "%LOG%"

cls
echo.
echo ============================================================
echo.
echo       LOBSTER 1234 quick-call dispatcher (top-level)
echo.
echo       1  yi ren yi gong si   (agency-agents 17 dept)
echo       2  Musk x Buffett      (first principles + circle)
echo       3  three-vector link   (五步法 + 模板 + 脚手架)
echo       4  four-up iteration   (Obsidian + SelfLearn)
echo.
echo       ZERO COST: 100%% local script, no LLM call
echo       chain:  1 -^> 2 -^> 3 -^> 4
echo.
echo       v2.1: 9 国际对标 (Alibaba/Tencent/MS/NVIDIA/OpenAI/
echo            Anthropic / Tesla / SpaceX / Meta)
echo       v2.1: 三模式生产 (我方 / CNB / 联手)
echo       v2.1: 6x 高清 PNG 已就位 (8640x7920)
echo       v2.1: chcp 65001 UTF-8 杜绝乱码
echo.
echo ============================================================
echo.

REM ===== Stage 1: 一人一公司 =====
echo [1/4] Running 1_一人一公司.cmd ...
call "%CHAIN%\1_一人一公司.cmd"
if !errorlevel! neq 0 (
    echo   [WARN] stage 1 returned !errorlevel!, continue anyway
)
echo.

REM ===== Stage 2: 双雄蒸馏 =====
echo [2/4] Running 2_双雄蒸馏.cmd ...
call "%CHAIN%\2_双雄蒸馏.cmd"
if !errorlevel! neq 0 (
    echo   [WARN] stage 2 returned !errorlevel!, continue anyway
)
echo.

REM ===== Stage 3: 三载体联动 =====
echo [3/4] Running 3_三载体联动.cmd ...
call "%CHAIN%\3_三载体联动.cmd"
if !errorlevel! neq 0 (
    echo   [WARN] stage 3 returned !errorlevel!, continue anyway
)
echo.

REM ===== Stage 4: 四化迭代 =====
echo [4/4] Running 4_四化迭代.cmd ...
call "%CHAIN%\4_四化迭代.cmd"
if !errorlevel! neq 0 (
    echo   [WARN] stage 4 returned !errorlevel!, continue anyway
)
echo.

echo ============================================================
echo.
echo   [一键1234执行] ALL 4 STAGES DONE.
echo.
echo   Output dirs:
echo     - logs\一键1234_%STAMP%.log
echo     - .workbuddy\memory\ (当日日志 + wiki 笔记)
echo     - docs\技能沉淀\ (本轮复盘 + 历史复盘)
echo.
echo   Quick verification:
echo     type "!LOG!"
echo.
echo   Next steps:
echo     [A] run scripts\cnb_sync_artifacts_free.cmd        (云端同步)
echo     [B] run scripts\一键本地接入.cmd                   (Hermes+Harness+Orca)
echo     [C] read  docs\接单SOP\一键1234使用手册.md          (完整SOP)
echo     [D] read  assets\diagram\agency_agents_国际对标.svg (国际对标架构图)
echo.
echo ============================================================
echo   [一键1234执行] Finished at %time%
echo ============================================================
echo.
if not defined NOPAUSE pause
endlocal
exit /b 0
