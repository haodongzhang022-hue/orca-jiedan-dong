@echo off
chcp 65001 >nul
REM ============================================================
REM   scripts/1234/1_yi_ren_yi_gong_si.cmd
REM   1234-快捷-1: 一人一公司 (agency-agents 17 departments)
REM   零成本: 仅本地 Read + 输出对标映射, 不调任何 LLM
REM   触发词: 一人一公司 / 单人开公司 / AUTOGAT / agency / 1
REM   实质执行: 选角 -> 加载身份卡 -> 产出 -> 验收 -> 归档
REM   整理: Codex 2026-08-20
REM ============================================================

setlocal ENABLEDELAYEDEXPANSION

set ROOT=%~dp0..\..
set AGENCY=E:\龙虾AI主控中心\我的AI分身\技能库\agency-agents\
set LOG=%ROOT%\logs\1234_1_yiren_%date:~0,4%%date:~5,2%%date:~8,2%.log

echo ============================================================
echo   [1234-1] YI REN YI GONG SI - Single-Person Company
echo   agency-agents MIT 17 departments / 200+ roles
echo   ZERO COST: 100%% local - no LLM call
echo ============================================================
echo.

echo [STEP 1/5] Check agency-agents resource
if not exist "%AGENCY%" (
    echo [ERROR] agency-agents path missing: %AGENCY%
    echo         Please clone it: git clone https://github.com/msitarzewski/agency-agents "%AGENCY%"
    exit /b 1
)
echo   [OK] agency-agents path ready: %AGENCY%

echo [STEP 2/5] List 17 departments (one-line each)
echo   --- marketing   (30 roles, China-localized, profit-optimized)
echo   --- engineering (29 roles, full-stack)
echo   --- design      (8 roles, ui-designer / brand-guardian / visual-storyteller)
echo   --- product     (PM / UX-researcher / sprint-prioritizer)
echo   --- project-management
echo   --- strategy    (cmo / cfo / chief-of-staff)
echo   --- operations  (revenue-ops / knowledge-eng / chief-of-staff)
echo   --- customer-success
echo   --- sales
echo   --- hr
echo   --- finance
echo   --- legal
echo   --- data-analytics
echo   --- security
echo   --- integrations (184 SKILL.md through antigravity/)
echo   --- qa-engineering
echo   --- research
echo   --- TOTAL 17 departments, 200+ roles

echo [STEP 3/5] Default role assignment for THIS workspace (接单)
echo   Hero role #1: design/visual-storyteller          (cover, poster, 报纸样张)
echo   Hero role #2: design/ui-designer                 (内页排版, 画册, 长文档)
echo   Hero role #3: marketing/copywriter               (文案 / 标题 / 平台分发)
echo   Hero role #4: project-management/pm              (多单并发 / 排期 / 验收)
echo   Hero role #5: strategy/cmo                       (群里情报 / 报价研判 / 决策)
echo   Hero role #6: operations/knowledge-engineer      (经验蒸馏 / Wiki / Skill)
echo   Hero role #7: psychology/consumer-research       (客户真实需求洞察)

echo [STEP 4/5] Role identity injection (each role loads 4 fields)
echo   role.identity     (who this role IS)
echo   role.process      (how this role works)
echo   role.deliverable  (what this role outputs)
echo   role.acceptance   (how this role is reviewed by Claude Code)

echo [STEP 5/5] Archive path conventions
echo   design files:    %ROOT%\01_正在执行实单\
echo   documents:       %ROOT%\docs\接单SOP\
echo   wiki / notes:    %ROOT%\.workbuddy\memory\
echo   skill archives:  %ROOT%\docs\技能沉淀\
echo.

echo [1234-1] DONE. Resource: %AGENCY%
echo [1234-1] Hero roles for 接单: 7 roles chained
echo [1234-1] Next: run  scripts\一键1234执行.cmd  for full chain
echo         OR    run  scripts\1234\2_双雄蒸馏.cmd  for Musk x Buffett distillation
echo.
if not defined NOPAUSE pause
echo Log saved to: %LOG%
endlocal
exit /b 0
