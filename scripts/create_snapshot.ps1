# ============================================================
#   scripts/create_snapshot.ps1
#   龙虾舰队 · 轻量快照（正常节点备份，体积 < 20MB）
#   用法：
#     pwsh -File scripts/create_snapshot.ps1
#     pwsh -File scripts/create_snapshot.ps1 -MaxMB 20
#   说明：
#     - 命名 normal_node_YYYYMMDD_HHMMSS.tar.gz，落到 snapshots/
#     - 先打包到系统临时目录，再移入 snapshots/，避免 tar 读到自身
#     - 排除 .git/对话记录/msgbus/fleet_exchange/worktrees/logs/旧快照等
# ============================================================
param(
    [int]$MaxMB = 20
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$SnapDir = Join-Path $Root 'snapshots'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Name = "normal_node_${Stamp}.tar.gz"
$Tmp = Join-Path $env:TEMP $Name
$Final = Join-Path $SnapDir $Name

if (-not (Test-Path $SnapDir)) { New-Item -ItemType Directory -Path $SnapDir | Out-Null }

$Excludes = @(
    '.git', '对话记录', 'msgbus', 'fleet_exchange', 'worktrees',
    'logs', 'snapshots', 'tools', '.workbuddy', '__pycache__',
    '*.pyc', 'node_modules', 'tests', 'backups', 'archive',
    # 大媒体不入代码快照（本体保留在订单目录）
    '*.wav', '*.mp4', '*.mp3'
)

$Args = @('-c', '-z', '-f', $Tmp)
foreach ($e in $Excludes) { $Args += "--exclude=$e" }
$Args += '.'

Write-Host "[快照] 正在打包 $Name ..."
Push-Location $Root
try {
    & tar @Args
    if ($LASTEXITCODE -ne 0) { throw "tar 打包失败，退出码 $LASTEXITCODE" }
}
finally {
    Pop-Location
}

$Size = (Get-Item $Tmp).Length
$SizeMB = [Math]::Round($Size / 1MB, 2)
if ($SizeMB -ge $MaxMB) {
    Remove-Item $Tmp -Force
    throw "快照 ${SizeMB}MB 超出 ${MaxMB}MB 上限，未写入"
}

Move-Item -LiteralPath $Tmp -Destination $Final -Force
Write-Host ("[快照] 完成: {0} ({1}MB)" -f $Final, $SizeMB)
Write-Host "[快照] 校验通过：体积小于 ${MaxMB}MB"
