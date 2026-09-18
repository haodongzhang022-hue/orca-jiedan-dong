# ============================================================
#   scripts/one-click-rollback.ps1
#   龙虾舰队 · 一键回滚（恢复到最近正常节点快照）
#   用法：
#     pwsh -File scripts/one-click-rollback.ps1 -List
#     pwsh -File scripts/one-click-rollback.ps1 -DryRun
#     pwsh -File scripts/one-click-rollback.ps1
#     pwsh -File scripts/one-click-rollback.ps1 -Snapshot xxx.tar.gz
#   安全：
#     - 仅解压 snapshots/normal_node_*.tar.gz 到项目根目录
#     - 解压前校验体积 <20MB 与 tar 完整性
#     - 回滚前对当前关键配置做一次 .pre-rollback 备份
# ============================================================
param(
    [switch]$List,
    [switch]$DryRun,
    [string]$Snapshot,
    [int]$MaxMB = 20
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$SnapDir = Join-Path $Root 'snapshots'

function Get-Snapshots {
    Get-ChildItem -LiteralPath $SnapDir -Filter 'normal_node_*.tar.gz' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending
}

$snaps = @(Get-Snapshots)
if ($snaps.Count -eq 0) {
    Write-Warning "snapshots/ 下没有 normal_node_*.tar.gz 快照"
    exit 1
}

if ($List) {
    Write-Host ("可用快照（{0} 个）:" -f $snaps.Count)
    foreach ($s in $snaps) {
        Write-Host ("  {0}  {1:N2}MB" -f $s.Name, ($s.Length / 1MB))
    }
    exit 0
}

$target = $snaps[0]
if ($Snapshot) {
    $target = $snaps | Where-Object { $_.Name -eq $Snapshot } | Select-Object -First 1
    if (-not $target) { throw "未找到快照: $Snapshot" }
}

$SizeMB = [Math]::Round($target.Length / 1MB, 2)
Write-Host ("[回滚] 目标快照: {0} ({1}MB)" -f $target.Name, $SizeMB)
if ($target.Length -ge $MaxMB * 1MB) {
    throw "快照 ${SizeMB}MB 超出 ${MaxMB}MB 上限，拒绝回滚"
}

Write-Host "[回滚] 校验 tar 完整性 ..."
$check = & tar -tzf $target.FullName 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "tar 完整性校验失败: $check"
}

if ($DryRun) {
    Write-Host ("[回滚] DRY-RUN 通过：{0} 个条目，体积正常，未解压" -f @($check).Count)
    exit 0
}

$backupTag = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = Join-Path $SnapDir "pre-rollback_${backupTag}"
New-Item -ItemType Directory -Path $backupDir | Out-Null
$configs = @('AGENTS.md','CODEX.md','CLAUDE.md','HERMES.md','SelfLearn_Record.md','.gitignore')
foreach ($c in $configs) {
    $p = Join-Path $Root $c
    if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination $backupDir -Force }
}
Write-Host "[回滚] 关键配置已备份到 $backupDir"

Write-Host "[回滚] 解压快照到项目根目录 ..."
Push-Location $Root
try {
    & tar -xzf $target.FullName
    if ($LASTEXITCODE -ne 0) { throw "tar 解压失败，退出码 $LASTEXITCODE" }
}
finally {
    Pop-Location
}

Write-Host "[回滚] 完成。按项目自动恢复协议拉起代理并验证三引擎连通。"