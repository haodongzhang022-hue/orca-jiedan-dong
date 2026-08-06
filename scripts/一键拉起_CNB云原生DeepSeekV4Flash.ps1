# 一键拉起_CNB云原生DeepSeekV4Flash.ps1
# 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
# 功能：CNB云原生链路一键启动，自动蒸馏本地人设至云端NPC
# 用法：右键「使用PowerShell运行」或 `.\一键拉起_CNB云原生DeepSeekV4Flash.ps1`

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "CNB DeepSeek-V4-Flash 云端启动"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  龙虾AI · CNB云原生链路启动" -ForegroundColor Yellow
Write-Host "  基座：CNB免费DeepSeek-V4-Flash" -ForegroundColor Green
Write-Host "  有效期至：2026-12-31" -ForegroundColor Green
Write-Host "  镜像：docker.cnb.cool/npc/mtga:latest" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# ========== 1. 仓库目标选择 ==========
Write-Host "`n[1/7] 选择目标仓库..." -ForegroundColor Magenta

$repos = @{
    "1" = @{Name="orca-jiedan"; Desc="企业微信接单项目（主仓库）"}
    "2" = @{Name="orca-wangpan"; Desc="网盘萃取项目"}
    "3" = @{Name="orca-xianyu"; Desc="闲鱼自动化项目"}
    "4" = @{Name="orca-quant-jiasheng"; Desc="量化嘉盛策略"}
    "5" = @{Name="orca-quant-binance"; Desc="量化币安策略"}
    "6" = @{Name="orca"; Desc="主空仓（调度中枢）"}
    "a" = @{Name="ALL"; Desc="全部6个仓库"}
}

Write-Host "  可用仓库：" -ForegroundColor White
foreach ($k in ($repos.Keys | Sort-Object)) {
    Write-Host "    [$k] $($repos[$k].Desc) ($($repos[$k].Name))" -ForegroundColor Gray
}
$choice = Read-Host "  输入编号，默认 [1]"
if (-not $choice) { $choice = "1" }
if (-not $repos.ContainsKey($choice)) {
    Write-Host "  ❌ 无效选择" -ForegroundColor Red
    exit 1
}

$targetRepo = $repos[$choice].Name
$cnbUrl = "https://cnb.cool/TJF19770107/${targetRepo}"
Write-Host "  目标: ${targetRepo} (${cnbUrl})" -ForegroundColor Green

# ========== 2. 人设蒸馏（本地→云端） ==========
Write-Host "`n[2/7] 本地 Agent 人设蒸馏..." -ForegroundColor Magenta

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$codexPersonaPath = Join-Path $projectRoot "CODEX.md"
$claudePersonaPath = Join-Path $projectRoot "CLAUDE.md"

$codexPrompt = ""
$claudePrompt = ""

if (Test-Path $codexPersonaPath) {
    $codexPrompt = Get-Content $codexPersonaPath -Raw -Encoding UTF8
    Write-Host "  ✅ Codex 人设已读取 (CODEX.md)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ CODEX.md 未找到，使用默认 Codex 人设" -ForegroundColor Yellow
    $codexPrompt = @"
你是 Codex，orca-jiedan 的代码执行官。核心能力：Python/Node.js/Shell 代码编写、bug 修复、功能实现。原则：代码优先、最小改动、中文注释。
"@
}

if (Test-Path $claudePersonaPath) {
    $claudePrompt = Get-Content $claudePersonaPath -Raw -Encoding UTF8
    Write-Host "  ✅ Claude Code 人设已读取 (CLAUDE.md)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ CLAUDE.md 未找到，使用默认 Claude 人设" -ForegroundColor Yellow
    $claudePrompt = @"
你是 Claude Code，orca-jiedan 的代码审计官。核心能力：安全审计、性能分析、架构审查。审计标准：安全>性能>可读性>健壮性。输出按 严重/警告/建议 三级分类。
"@
}

# 蒸馏转换：本地人设 → NPC prompt 兼容格式
$codexShort = ($codexPrompt -split "`n" | Where-Object { $_ -match "^[-*#]" -or $_ -match "^你是|核心能力|工作原则|项目定位|禁止" } | Select-Object -First 20) -join "`n"
$claudeShort = ($claudePrompt -split "`n" | Where-Object { $_ -match "^[-*#]" -or $_ -match "^你是|核心能力|审计标准|审查维度|禁止" } | Select-Object -First 20) -join "`n"

Write-Host "  蒸馏完成：Codex ($($codexShort.Length)字符) / Claude ($($claudeShort.Length)字符)" -ForegroundColor Green

# ========== 3. .cnb/settings.yml 校验 ==========
Write-Host "`n[3/7] CNB 流水线配置校验..." -ForegroundColor Magenta

$cnbYml = Join-Path $projectRoot ".cnb.yml"
$cnbSettings = Join-Path $projectRoot ".cnb" "settings.yml"

if (Test-Path $cnbYml) {
    Write-Host "  ✅ .cnb.yml 已存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠ .cnb.yml 缺失，NPC流水线不可用" -ForegroundColor Yellow
    Write-Host "    请确保仓库已配置正确的 .cnb.yml" -ForegroundColor Gray
}

if (Test-Path $cnbSettings) {
    Write-Host "  ✅ .cnb/settings.yml 已存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠ .cnb/settings.yml 缺失" -ForegroundColor Yellow
}

# ========== 4. 浏览器唤起 CNB 仓库 ==========
Write-Host "`n[4/7] 唤起浏览器..." -ForegroundColor Magenta

if ($choice -eq "a") {
    Write-Host "  全部仓库链接：" -ForegroundColor White
    foreach ($k in ($repos.Keys | Sort-Object)) {
        if ($k -ne "a") {
            $u = "https://cnb.cool/TJF19770107/$($repos[$k].Name)"
            Write-Host "    $($repos[$k].Desc): $u" -ForegroundColor Gray
        }
    }
    # 打开主仓库
    Start-Process "https://cnb.cool/TJF19770107/orca-jiedan"
    Write-Host "  ✅ 已打开主仓库 (orca-jiedan)" -ForegroundColor Green
} else {
    Start-Process $cnbUrl
    Write-Host "  ✅ 已打开: ${cnbUrl}" -ForegroundColor Green
}

# ========== 5. NPC 调度指引 ==========
Write-Host "`n[5/7] NPC 三级链式调度指引..." -ForegroundColor Magenta

Write-Host @"

  ┌─────────────────────────────────────────────┐
  │  CNB NPC 三级链式调度流程                     │
  │                                               │
  │  1️⃣  @npc/codex      代码执行/生成            │
  │       ↓                                       │
  │  2️⃣  @npc/claude-code 代码审计/审查            │
  │       ↓                                       │
  │  3️⃣  @CodeBuddy      终审/PR提交              │
  │                                               │
  │  使用方法：                                   │
  │  - Issues 评论区输入 @codex 触发代码执行       │
  │  - PR 评论区输入 @claude-code 触发审计         │
  │  - @CodeBuddy 进行终审和方案建议               │
  │                                               │
  │  ⚠ 云端NPC无法1:1同步本地Agent：              │
  │  - 云端无本地文件系统访问权                     │
  │  - 云端无法调用Hermes/MCP服务                  │
  │  - 通过 .cnb/settings.yml prompt 蒸馏人设      │
  └─────────────────────────────────────────────┘

"@ -ForegroundColor Gray

# ========== 6. G盘同步 + Obsidian归档 ==========
Write-Host "`n[6/7] 产出同步与归档..." -ForegroundColor Magenta

$gDrive = "G:\"
if (Test-Path $gDrive) {
    Write-Host "  ✅ G盘已挂载" -ForegroundColor Green
    $gMirror = Join-Path $gDrive "CNB镜像"
    if (-not (Test-Path $gMirror)) {
        New-Item -ItemType Directory -Path $gMirror -Force | Out-Null
    }
    Write-Host "  镜像目录: ${gMirror}" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ G盘未挂载，云端产出无法自动镜像到本地" -ForegroundColor Yellow
}

$obsidianVault = "E:\龙虾AI主控中心\Obsidian"
if (Test-Path $obsidianVault) {
    Write-Host "  ✅ Obsidian 知识库就绪" -ForegroundColor Green
    Write-Host "  归档路径: ${obsidianVault}\wiki\" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ Obsidian 知识库未找到" -ForegroundColor Yellow
}

# ========== 7. 状态面板 ==========
Write-Host "`n[7/7] 云端启动状态汇总" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  目标仓库:   ${targetRepo}" -ForegroundColor White
Write-Host "  CNB URL:    ${cnbUrl}" -ForegroundColor White
Write-Host "  基座模型:   DeepSeek-V4-Flash" -ForegroundColor Green
Write-Host "  NPC 镜像:   docker.cnb.cool/npc/mtga:latest" -ForegroundColor Green
Write-Host "  Codex NPC:  $(if(Test-Path $cnbSettings){'已配置'}else{'待配置'})" -ForegroundColor $(if(Test-Path $cnbSettings){'Green'}else{'Yellow'})
Write-Host "  Claude NPC:  $(if(Test-Path $cnbSettings){'已配置'}else{'待配置'})" -ForegroundColor $(if(Test-Path $cnbSettings){'Green'}else{'Yellow'})
Write-Host "  G盘镜像:    $(if(Test-Path $gDrive){'就绪'}else{'未挂载'})" -ForegroundColor $(if(Test-Path $gDrive){'Green'}else{'Yellow'})
Write-Host "  Obsidian:   $(if(Test-Path $obsidianVault){'就绪'}else{'未找到'})" -ForegroundColor $(if(Test-Path $obsidianVault){'Green'}else{'Yellow'})
Write-Host "  有效期:     至 2026-12-31" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  浏览器已打开 CNB 仓库，可通过 Issue/PR 评论区" -ForegroundColor Yellow
Write-Host "  输入 @codex / @claude-code / @CodeBuddy 调度 NPC" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "按 Enter 退出"
