@echo off
chcp 65001 >nul
REM ============================================================
REM   scripts/1234/3_三载体联动.cmd
REM   1234-快捷-3: Three-Vector Linked Update
REM   五步法 + 全域模板 + 项目脚手架 (三处同步)
REM   零成本: 仅本地文件比对/写入, 不调任何 LLM
REM   触发词: 三载体联动 / 联动迭代 / 记忆资产同步 / 3
REM   整理: Codex 2026-08-20
REM ============================================================

setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0..\..
set STEP5=E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\龙虾五步法V3.6·PR#21闭环版（成本优先置顶）SKILL.md
set TEMPLATE=E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\龙虾全域官方模板-最终版.md
set SCAFFOLD=%ROOT%

echo ============================================================
echo   [1234-3] THREE-VECTOR LINKED UPDATE
echo   Vector 1: 龙虾五步法       (workflow SKILL.md)
echo   Vector 2: 龙虾全域模板      (template)
echo   Vector 3: 项目脚手架        (AGENTS / CODEX / CLAUDE / HERMES)
echo   ZERO COST: local file diff/write, no LLM call
echo ============================================================
echo.

echo [STEP 1/6] Verify three vectors exist
echo   [V1] %STEP5%
if exist "%STEP5%" echo   [OK] V1 (五步法) ready
echo   [V2] %TEMPLATE%
if exist "%TEMPLATE%" echo   [OK] V2 (全域模板) ready
echo   [V3] %SCAFFOLD%\AGENTS.md  /CODEX.md  /CLAUDE.md  /HERMES.md
if exist "%SCAFFOLD%\AGENTS.md" echo   [OK] V3-1 AGENTS.md
if exist "%SCAFFOLD%\CODEX.md"  echo   [OK] V3-2 CODEX.md
if exist "%SCAFFOLD%\CLAUDE.md" echo   [OK] V3-3 CLAUDE.md
if exist "%SCAFFOLD%\HERMES.md" echo   [OK] V3-4 HERMES.md

echo.
echo [STEP 2/6] Five-section enforcement (四化对应执行)
echo   1) 记忆资产同步   - ai memory sync (Obsidian)
echo   2) DeepSeek 运维   - DS V4 Flash / Harness / 15730/15721 proxy
echo   3) 群聊链路       - Wecom listener / OCR / 接单池
echo   4) 补强事项       - SelfLearn_Record / 数字快捷手册
echo   5) 复盘闭环       - docs/技能沉淀/yyyyMMdd_*.md

echo.
echo [STEP 3/6] Cost control (top priority per V3.6 PR#21)
echo   - 零积分任务: 全本地 Read + cmd + 写入
echo   - 单一工具尽量复用, 不并发起飞
echo   - SelfLearn_Record 头部追加 (不重写)
echo   - 执行前先查 git log --oneline -5, 避免回退

echo.
echo [STEP 4/6] Sync order (mandatory)
echo   Step A: 改五步法 SKILL.md  (升版本 + 新增章节)
echo   Step B: 改全域模板          (新增迭代记录 #N)
echo   Step C: 改项目脚手架 4 文件 (AGENTS/CODEX/CLAUDE/HERMES 同步)
echo   Step D: 数字快捷手册          (执行记录表追加新行)
echo   Step E: SelfLearn_Record     (新条目写文件头部)
echo   Step F: git add -A + commit + push (CNB 或 GitHub)

echo.
echo [STEP 5/6] Auto-linkage (this script hooks everything)
echo   - 本脚本由  scripts/一键1234执行.cmd  调度
echo   - 每个 1234 子脚本写日志到  logs/1234_N_*.log
echo   - 调度链: 一键1234 -> 1/2/3/4 子脚本 -> 输出汇总 -> 退出码 0

echo.
echo [STEP 6/6] Audit checklist
echo   [ ] V1 五步法升版        [ ] V2 全域模板 #N 追加
echo   [ ] V3 脚手架 4 文件同步   [ ] SelfLearn 头部新条目
echo   [ ] 数字快捷手册 记录表+1    [ ] CNB git push origin main成功
echo.

echo [1234-3] DONE.
echo [1234-3] Next: scripts\1234\4_四化迭代.cmd  for Obsidian sync
echo.
endlocal
exit /b 0
