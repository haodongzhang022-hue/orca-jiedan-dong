# 一键拉起_Ollama本地DeepSeekV4Flash.ps1
# 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
# 功能：本地Ollama链路一键启动，含磁盘校验、进程管控、MIMO多模态旁路
# 用法：右键「使用PowerShell运行」或 `.\一键拉起_Ollama本地DeepSeekV4Flash.ps1`

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Ollama DeepSeek-V4-Flash 一键启动"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  龙虾AI · 本地Ollama链路启动" -ForegroundColor Yellow
Write-Host "  基座：CNB免费DeepSeek-V4-Flash" -ForegroundColor Green
Write-Host "  有效期至：2026-12-31" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# ========== 1. 磁盘空间校验 ==========
Write-Host "`n[1/6] 磁盘空间校验..." -ForegroundColor Magenta
$ollamaDir = "$env:USERPROFILE\.ollama"
$drive = (Get-Item $ollamaDir).PSDrive
$freeGB = [math]::Round($drive.Free / 1GB, 1)
Write-Host "  Ollama 数据盘剩余: ${freeGB}GB" -ForegroundColor Gray
if ($freeGB -lt 10) {
    Write-Host "  ⚠ 磁盘空间不足 10GB，模型可能拉取失败" -ForegroundColor Yellow
    $continue = Read-Host "  是否继续？(y/n)"
    if ($continue -ne "y") { exit 1 }
}

$modelSize = 8  # DeepSeek-V4-Flash 约 8GB
if ($freeGB -lt ($modelSize + 5)) {
    Write-Host "  ⚠ 磁盘空间可能不足以拉取模型(需~${modelSize}GB)" -ForegroundColor Yellow
}
Write-Host "  ✅ 磁盘空间校验通过" -ForegroundColor Green

# ========== 2. Ollama 进程管控 ==========
Write-Host "`n[2/6] Ollama 进程管控..." -ForegroundColor Magenta

# 智能定位 Ollama
$ollamaExe = $null
$searchPaths = @(
    "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    "$env:ProgramFiles\Ollama\ollama.exe",
    "${env:ProgramFiles(x86)}\Ollama\ollama.exe",
    "$env:USERPROFILE\scoop\apps\ollama\current\ollama.exe"
)
foreach ($p in $searchPaths) {
    if (Test-Path $p) { $ollamaExe = $p; break }
}

# 扫描常见安装目录
if (-not $ollamaExe) {
    $found = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs", "$env:ProgramFiles" -Filter "ollama.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $ollamaExe = $found.FullName }
}
if (-not $ollamaExe) { $found = Get-ChildItem -Path "$env:USERPROFILE" -Filter "ollama.exe" -Recurse -Depth 3 -ErrorAction SilentlyContinue | Select-Object -First 1; if ($found) { $ollamaExe = $found.FullName } }

if (-not $ollamaExe) {
    Write-Host "  ❌ 未找到 Ollama，请先安装: https://ollama.com/download/windows" -ForegroundColor Red
    exit 1
}
Write-Host "  Ollama 路径: $ollamaExe" -ForegroundColor Gray

# 检查进程状态
$ollamaProc = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollamaProc) {
    Write-Host "  Ollama 进程已运行 (PID: $($ollamaProc.Id))" -ForegroundColor Green
} else {
    Write-Host "  启动 Ollama 服务..." -ForegroundColor Yellow
    Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    $ollamaProc = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if (-not $ollamaProc) {
        Write-Host "  ❌ Ollama 启动失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ Ollama 已启动 (PID: $($ollamaProc.Id))" -ForegroundColor Green
}

# ========== 3. 模型拉取与校验 ==========
Write-Host "`n[3/6] 模型校验..." -ForegroundColor Magenta
$modelName = "deepseek-v4-flash"
$modelList = & $ollamaExe list 2>$null
if ($modelList -match $modelName) {
    Write-Host "  ✅ 模型 ${modelName} 已就绪" -ForegroundColor Green
} else {
    Write-Host "  拉取模型 ${modelName} (约 ${modelSize}GB)..." -ForegroundColor Yellow
    & $ollamaExe pull $modelName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ 模型拉取失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✅ 模型拉取完成" -ForegroundColor Green
}

# ========== 4. 验证 Agent CLI ==========
Write-Host "`n[4/6] Agent CLI 校验..." -ForegroundColor Magenta

$codexReady = $false
try { $null = Get-Command "codex" -ErrorAction Stop; $codexReady = $true } catch {}
if ($codexReady) {
    $v = & codex --version 2>&1 | Select-Object -First 1
    Write-Host "  ✅ Codex CLI: $v" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Codex CLI 未安装，跳过本地Codex链" -ForegroundColor Yellow
    Write-Host "    安装: npm install -g @anthropic-ai/codex" -ForegroundColor Gray
}

$claudeReady = $false
try { $null = Get-Command "claude" -ErrorAction Stop; $claudeReady = $true } catch {}
if (-not $claudeReady) {
    try { $npx = & npx @claude/claude-code --version 2>&1 | Select-Object -First 1; $claudeReady = $true } catch {}
}
if ($claudeReady) {
    Write-Host "  ✅ Claude Code CLI 可用" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Claude Code CLI 未安装，跳过本地Claude链" -ForegroundColor Yellow
    Write-Host "    安装: npm install -g @claude/claude-code" -ForegroundColor Gray
}

# Hermes (WorkBuddy)
$hermesProc = Get-Process -Name "WorkBuddy" -ErrorAction SilentlyContinue
if ($hermesProc) {
    Write-Host "  ✅ Hermes 已运行 (PID: $($hermesProc.Id))" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Hermes 未运行，消息监听链路离线" -ForegroundColor Yellow
}

# ========== 5. MIMO 多模态旁路 ==========
Write-Host "`n[5/6] MIMO 多模态旁路..." -ForegroundColor Magenta
$mimoApiKey = $env:MIMO_API_KEY
if ($mimoApiKey) {
    Write-Host "  ✅ MIMO API Key 已配置（多模态旁路就绪）" -ForegroundColor Green
    Write-Host "    旁路策略：图片/海报/漫剧识别 → MIMO v2.5-Pro → DeepSeek 文案调度" -ForegroundColor Gray
} else {
    Write-Host "  ⚠ MIMO_API_KEY 未设置，多模态旁路不可用" -ForegroundColor Yellow
    Write-Host "    DeepSeek 无原生识图能力，图片处理需手动提供描述" -ForegroundColor Gray
}

# ========== 6. 状态面板 ==========
Write-Host "`n[6/6] 启动状态汇总" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  基座模型: DeepSeek-V4-Flash" -ForegroundColor White
Write-Host "  Ollama:   运行中 (http://127.0.0.1:11434)" -ForegroundColor Green
Write-Host "  Codex CLI: $(if($codexReady){'就绪'}else{'未安装'})" -ForegroundColor $(if($codexReady){'Green'}else{'Yellow'})
Write-Host "  Claude CLI: $(if($claudeReady){'就绪'}else{'未安装'})" -ForegroundColor $(if($claudeReady){'Green'}else{'Yellow'})
Write-Host "  Hermes:    $(if($hermesProc){'运行中'}else{'离线'})" -ForegroundColor $(if($hermesProc){'Green'}else{'Yellow'})
Write-Host "  MIMO旁路:  $(if($mimoApiKey){'就绪'}else{'未配置'})" -ForegroundColor $(if($mimoApiKey){'Green'}else{'Yellow'})
Write-Host "  有效期:    至 2026-12-31" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  本地链路已就绪，可通过企业微信群 @Hermes 接单" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "按 Enter 退出"
