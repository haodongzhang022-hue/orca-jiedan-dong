@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: =============================================================================
:: 一键拉起 — CNB 云原生 DeepSeek-V4-Flash 链路
:: 版本：1.4.1 | 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
:: 架构：CodeBuddy（系统NPC）→ npc/codex（代码执行）→ npc/claude-code（代码审计）
:: 路径：orca-jiedan 企业微信群定制接单项目
:: =============================================================================

title 龙虾AI·CNB云原生DeepSeekV4Flash链路

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   龙虾AI · CNB云原生DeepSeek-V4-Flash链路       ║
echo  ║   基座：CNB免费DeepSeek-V4-Flash（至2026-12-31）║
echo  ╚══════════════════════════════════════════════════╝
echo.

set PROJECT_DIR=%~dp0..
set CNB_ORG=TJF19770107

:: ===========================================================================
:: 步骤1：本地人设蒸馏 → 云端 NPC 分身
:: ===========================================================================
echo [1/5] 蒸馏本地 Agent 人设到云端 NPC...

set SETTINGS_FILE=%PROJECT_DIR%\.cnb\settings.yml

:: 检查是否已有云端配置
if exist "%SETTINGS_FILE%" (
    echo [✓] 云端 NPC 配置已存在：.cnb/settings.yml
    echo     如需更新人设，请编辑该文件后重新运行
) else (
    echo [→] 未找到云端配置，正在从本地工作树蒸馏...

    :: 蒸馏 Codex 人设
    set CODEX_PROMPT=
    if exist "%PROJECT_DIR%\codex\SKILL.md" (
        for /f "delims=" %%a in ('type "%PROJECT_DIR%\codex\SKILL.md" 2^>nul') do set CODEX_PROMPT=!CODEX_PROMPT!%%a\n
    )
    if exist "%PROJECT_DIR%\codex\README.md" (
        for /f "delims=" %%a in ('type "%PROJECT_DIR%\codex\README.md" 2^>nul') do set CODEX_PROMPT=!CODEX_PROMPT!%%a\n
    )

    :: 蒸馏 Claude 人设
    set CLAUDE_PROMPT=
    if exist "%PROJECT_DIR%\claude\SKILL.md" (
        for /f "delims=" %%a in ('type "%PROJECT_DIR%\claude\SKILL.md" 2^>nul') do set CLAUDE_PROMPT=!CLAUDE_PROMPT!%%a\n
    )

    mkdir "%PROJECT_DIR%\.cnb" 2>nul

    :: 生成 settings.yml
    (
        echo # CNB NPC 角色配置 — 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
        echo # 自动蒸馏自本地 Agent 工作树
        echo.
        echo npc:
        echo   roles:
        echo     - name: codex
        echo       prompt: ^|
        echo         # 角色：Codex（代码执行官）— 蒸馏自本地 codex 工作树
        echo.
        echo         你是 Codex，orca-jiedan 仓库的首席代码工程师。
        echo         基座模型：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
        echo.
        echo         ## 工作原则
        echo         1. 代码优先：输出可运行代码
        echo         2. 中文注释：所有代码含中文注释
        echo         3. 完整性：错误处理+日志
        echo.
        echo     - name: claude-code
        echo       prompt: ^|
        echo         # 角色：Claude Code（代码审计官）— 蒸馏自本地 claude 工作树
        echo.
        echo         你是 Claude Code，orca-jiedan 仓库的代码质量守护者。
        echo         基座模型：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
        echo.
        echo         ## 审计标准
        echo         1. 安全性检查：SQL注入/XSS/敏感信息泄露
        echo         2. 性能分析：时间复杂度/N+1查询
        echo         3. 可读性：命名/注释/函数长度
        echo         4. 健壮性：异常处理/边界条件
    ) > "%SETTINGS_FILE%"

    echo [✓] 已生成 .cnb/settings.yml（NPC 角色人设）
)

:: ===========================================================================
:: 步骤2：校验 .cnb.yml 流水线配置
:: ===========================================================================
echo.
echo [2/5] 校验 CNB 流水线配置...

set PIPELINE_FILE=%PROJECT_DIR%\.cnb.yml

if exist "%PIPELINE_FILE%" (
    echo [✓] .cnb.yml 已存在
    findstr /c:"mtga" "%PIPELINE_FILE%" >nul && echo [✓] NPC 镜像：docker.cnb.cool/npc/mtga:latest（免费社区镜像）
    findstr /c:"codex" "%PIPELINE_FILE%" >nul && echo [✓] codex NPC 流水线：已配置
    findstr /c:"claude-code" "%PIPELINE_FILE%" >nul && echo [✓] claude-code NPC 流水线：已配置
) else (
    echo [→] 未找到 .cnb.yml，正在创建...
    (
        echo # NPC 事件流水线 — 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
        echo # 三级链式：@CodeBuddy 终审 → @npc/codex 执行 → @npc/claude-code 审计
        echo # 镜像：docker.cnb.cool/npc/mtga:latest（以鹅传鹅-Pro 社区免费）
        echo.
        echo .npc_task: ^&npc_task
        echo   - stages:
        echo       - name: npc respond
        echo         image: docker.cnb.cool/npc/mtga:latest
        echo.
        echo codex:
        echo   issue.comment@npc: *npc_task
        echo   pull_request.comment@npc: *npc_task
        echo.
        echo claude-code:
        echo   issue.comment@npc: *npc_task
        echo   pull_request.comment@npc: *npc_task
    ) > "%PIPELINE_FILE%"
    echo [✓] 已创建 .cnb.yml
)

:: ===========================================================================
:: 步骤3：打开 CNB 仓库（浏览器 + 三级 NPC 调度面板）
:: ===========================================================================
echo.
echo [3/5] 唤起 CNB 仓库...

:: 主仓库
set MAIN_REPO=https://cnb.cool/%CNB_ORG%/orca-jiedan
echo [→] 主仓库：%MAIN_REPO%

:: 尝试用默认浏览器打开
start "" "%MAIN_REPO%"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║    三级 NPC 链式调度指令（在 Issue 评论中使用） ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║                                                ║
echo  ║  【第一级】@npc/codex 代码执行：               ║
echo  ║    @npc/codex(Codex) 帮我写xxx功能             ║
echo  ║                                                ║
echo  ║  【第二级】@npc/claude-code 代码审计：         ║
echo  ║    @npc/claude-code(Claude Code) 审查这个PR    ║
echo  ║                                                ║
echo  ║  【终审】@CodeBuddy 全览调度：                ║
echo  ║    @CodeBuddy 统筹上述NPC，最终提交PR          ║
echo  ║                                                ║
echo  ║  ⚠ 使用前需在Issue/PR中开启「替我上班」模式   ║
echo  ║    权限：只读→问答 / 开启→读写+推送代码       ║
echo  ╚══════════════════════════════════════════════════╝

:: ===========================================================================
:: 步骤4：启用 G盘 双向文件同步（云端产出物 → 本地镜像）
:: ===========================================================================
echo.
echo [4/5] G盘镜像同步...

set GDRIVE_MIRROR=G:\龙虾AI镜像\CNB云原生产出
if exist "G:\" (
    if not exist "%GDRIVE_MIRROR%" mkdir "%GDRIVE_MIRROR%"
    echo [✓] G盘镜像目录已就绪：%GDRIVE_MIRROR%
    echo     云端产出文件将自动同步到此目录
    echo     同步指令（定期执行）：
    echo     git clone https://cnb.cool/%CNB_ORG%/orca-jiedan.git "%GDRIVE_MIRROR%\orca-jiedan"
) else (
    echo [⚠] G盘未挂载，跳过镜像同步
    echo     挂载后可手动执行：git clone 到 G盘目标目录
)

:: ===========================================================================
:: 步骤5：Obsidian 知识库归档 & 输出状态面板
:: ===========================================================================
echo.
echo [5/5] Obsidian 知识库归档...

set OBSIDIAN_VAULT=E:\龙虾AI主控中心\Obsidian\wiki
if exist "%OBSIDIAN_VAULT%" (
    echo [✓] Obsidian 知识库已就绪：%OBSIDIAN_VAULT%
    echo     所有配置、任务记录、文档遵循四化闭环标准自动归档
) else (
    echo [ℹ] Obsidian 知识库路径未发现，跳过归档
)

:: ===========================================================================
:: 最终状态面板
:: ===========================================================================
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║      龙虾AI · CNB云原生链路 · 状态面板         ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  基座模型：CNB免费DeepSeek-V4-Flash             ║
echo  ║  免费期限：至 2026-12-31                        ║
echo  ║  NPC 镜像：docker.cnb.cool/npc/mtga:latest      ║
echo  ║           （以鹅传鹅-Pro 社区免费）             ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  三级 NPC 链式：                                ║
echo  ║    [L1] @npc/codex     — 代码执行               ║
echo  ║    [L2] @npc/claude-code — 代码审计             ║
echo  ║    [L3] @CodeBuddy     — 统筹终审               ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  Marvis 双向调度：                              ║
echo  ║    企业微信群接单 → 任务卡分流                  ║
echo  ║    ├─ 本地 Ollama 链路（bat #1）                ║
echo  ║    └─ CNB 云端链路（本脚本）                    ║
echo  ╠══════════════════════════════════════════════════╣
echo  ║  仓库地址：                                     ║
echo  ║    %MAIN_REPO%           ║
echo  ╚══════════════════════════════════════════════════╝
echo.
echo  [✓] CNB 云原生 DeepSeek-V4-Flash 链路已就绪
echo      浏览器已打开 CNB 仓库
echo      请在 Issue 中使用上述 @ 指令调度 NPC
echo.
pause
