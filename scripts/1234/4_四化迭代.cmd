@echo off
chcp 65001 >nul
REM ============================================================
REM   scripts/1234/4_四化迭代.cmd
REM   1234-快捷-4: Four-Up Iteration (智能化/定制化/全自动化/自我净化)
REM   零成本: 仅本地 Obsidian 同步 + SelfLearn 追加, 不调任何 LLM
REM   触发词: 四化迭代 Obsidian / 知识库反向赋能 / 4
REM   整理: Codex 2026-08-20
REM ============================================================

setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0..\..
set OB=E:\龙虾AI主控中心\Obsidian\
set SELF=%ROOT%\SelfLearn_Record.md
set MEMO=%ROOT%\.workbuddy\memory\

echo ============================================================
echo   [1234-4] FOUR-UP ITERATION ON OBSIDIAN
echo   智能化 (intelligent)       - AI 员工自主工作
echo   定制化 (custom)            - 蒸馏客户/订单思维
echo   全自动化 (auto-zero-touch) - 一公司一人, 零人工
echo   自我净化 (self-clean)      - 每次迭代优化脚手架+知识库
echo ------------------------------------------------------------
echo   国际对标 v2.0: 9 家一流 (Alibaba/Tencent/MS/NVIDIA/OpenAI/
echo                Anthropic⭐NEW/Tesla/SpaceX🚀NEW/Meta)
echo   模式 v2.0:   我方 vs CNB vs 联手(三模式生产标准)
echo ------------------------------------------------------------
echo ============================================================
echo.

echo [STEP 1/6] Verify Obsidian path
if exist "%OB%" (
    echo   [OK] Obsidian main library ready: %OB%
) else (
    echo   [WARN] Obsidian not found, will skip sync to wiki (不影响主流程)
)

echo.
echo [STEP 2/6] Search today's archive output in .workbuddy/memory
if exist "%MEMO%" (
    for /f "delims=" %%F in ('dir /b /o-n "%MEMO%" 2^>nul') do (
        echo   [MEMO] %%F
    )
) else (
    mkdir "%MEMO%" >nul 2>&1
    echo   [CREATED] %MEMO%
)

echo.
echo [STEP 3/6] Append SelfLearn header (新条目必须头部, 不重写)
if exist "%SELF%" (
    echo   [OK] SelfLearn_Record.md present, size = 
    for %%S in ("%SELF%") do @echo %%~zS bytes
    echo   Pre-action: 不由本脚本直接改 SelfLearn (需 Codex 调用 Edit 工具)
    echo   Pre-action: Codex 会在本脚本调用后执行 Edit header insertion
) else (
    echo   [WARN] SelfLearn_Record.md missing, skip
)

echo.
echo [STEP 4/6] Obsidian wiki categories (归档映射)
echo   wiki\          知识条目 (distilled knowledge)
echo   副业变现\       商单复盘 (commercial order archive)
echo   学习\           对标学习 (learning reference)
echo   故障库\         故障与排查 (failure-mode library)
echo   工作流程\       SOP/脚手架 (workflow SOP)

echo.
echo [STEP 5/6] Sync pattern (write-side)
echo   [a] Codex Edit SelfLearn_Record.md (insert new 2026-08-20 entry at HEAD)
echo   [b] Codex Edit docs/数字快捷调用执行手册.md (追加 1234 执行记录表新行)
echo   [c] Codex Write docs/技能沉淀/20260820_xxx_1234执行复盘.md (本轮复盘)
echo   [d] Codex Write .workbuddy/memory/2026-08-20.md (当日 work log)
echo   [e] Optional: git add -A + commit + push origin main  (CNB sync)

echo.
echo [STEP 6/6] Reverse-enrich (reverse data flow from Obsidian to skills)
echo   - 从 wiki 提取可复用范式 -> 更新 技能库\...\SKILL.md
echo   - 反复盘失败模式 -> 归档 故障库\
echo   - 反复盘经验范式 -> 归档 工作流程\
echo   - 反向验证: 知识库引用率 / 失败率 / 复现率
echo.

echo [1234-4] DONE. (Side effect on Obsidian + SelfLearn will be appended by Codex)
echo [1234-4] Chain order complete. Return code 0.
echo.
endlocal
exit /b 0
