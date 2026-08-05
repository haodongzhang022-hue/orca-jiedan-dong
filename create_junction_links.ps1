# ORCA项目磁盘分层存储 - 软链接创建脚本
# 版本：v1.0 | 生成时间：2026-08-03
# 使用方法：以管理员身份运行PowerShell，执行本脚本

# 配置变量
$G_DATA_POOL = "G:\orca_data_pool"
$E_PROJECT_ROOT = "E:\龙虾AI主控中心\我的AI分身\orca\企业微信群定制接单项目"

# 创建G盘数据池目录结构
Write-Host "创建G盘数据池目录结构..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\wav2lip"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\sadtalker"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\voxcpm"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\hyperframes"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\model_weights\moneyprinter"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\input"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\output"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\media_assets\background"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\dataset_cache"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\database_storage"
New-Item -ItemType Directory -Force -Path "$G_DATA_POOL\temp_render_output"

# 创建软链接函数
function Create-JunctionLink {
    param(
        [string]$Source,
        [string]$Target,
        [string]$Description
    )
    
    Write-Host "处理: $Description" -ForegroundColor Cyan
    
    # 检查目标目录是否存在
    if (-not (Test-Path $Target)) {
        Write-Host "  目标目录不存在: $Target" -ForegroundColor Red
        return $false
    }
    
    # 检查源路径是否已存在
    if (Test-Path $Source) {
        # 检查是否已经是软链接
        $item = Get-Item $Source
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Write-Host "  软链接已存在: $Source -> $Target" -ForegroundColor Yellow
            return $true
        } else {
            Write-Host "  源路径已存在且不是软链接，需要备份" -ForegroundColor Yellow
            $backupPath = "${Source}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Rename-Item -Path $Source -NewName $backupPath
            Write-Host "  已备份: $Source -> $backupPath" -ForegroundColor Yellow
        }
    }
    
    # 创建软链接
    try {
        New-Item -ItemType Junction -Path $Source -Target $Target -Force | Out-Null
        Write-Host "  创建成功: $Source -> $Target" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  创建失败: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 创建软链接
Write-Host "`n开始创建软链接..." -ForegroundColor Green

$successCount = 0
$totalCount = 0

# 1. Wav2Lip模型权重软链接
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\tools\wav2lip\checkpoints" -Target "$G_DATA_POOL\model_weights\wav2lip" -Description "Wav2Lip模型权重") {
    $successCount++
}

# 2. SadTalker模型权重软链接（预留）
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\tools\sadtalker\checkpoints" -Target "$G_DATA_POOL\model_weights\sadtalker" -Description "SadTalker模型权重") {
    $successCount++
}

# 3. 媒体素材软链接
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\media_assets" -Target "$G_DATA_POOL\media_assets" -Description "媒体素材目录") {
    $successCount++
}

# 4. 数据集缓存软链接
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\dataset_cache" -Target "$G_DATA_POOL\dataset_cache" -Description "数据集缓存") {
    $successCount++
}

# 5. 数据库存储软链接
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\database_storage" -Target "$G_DATA_POOL\database_storage" -Description "数据库存储") {
    $successCount++
}

# 6. 临时渲染输出软链接
$totalCount++
if (Create-JunctionLink -Source "$E_PROJECT_ROOT\temp_render_output" -Target "$G_DATA_POOL\temp_render_output" -Description "临时渲染输出") {
    $successCount++
}

# 输出结果
Write-Host "`n软链接创建完成！" -ForegroundColor Green
Write-Host "成功: $successCount / $totalCount" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

# 验证清单
Write-Host "`n验证清单：" -ForegroundColor Cyan
Write-Host "1. 检查目录是否可访问" -ForegroundColor White
Write-Host "2. 测试程序是否能正常读写文件" -ForegroundColor White
Write-Host "3. 验证软链接指向正确" -ForegroundColor White

# 显示软链接状态
Write-Host "`n软链接状态：" -ForegroundColor Cyan
$links = @(
    "$E_PROJECT_ROOT\tools\wav2lip\checkpoints",
    "$E_PROJECT_ROOT\tools\sadtalker\checkpoints",
    "$E_PROJECT_ROOT\media_assets",
    "$E_PROJECT_ROOT\dataset_cache",
    "$E_PROJECT_ROOT\database_storage",
    "$E_PROJECT_ROOT\temp_render_output"
)

foreach ($link in $links) {
    if (Test-Path $link) {
        $item = Get-Item $link
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $target = $item.Target
            Write-Host "  ✅ $link -> $target" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $link (不是软链接)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ⚠️ $link (不存在)" -ForegroundColor Yellow
    }
}

Write-Host "`n使用说明：" -ForegroundColor Cyan
Write-Host "1. 将模型权重下载到G盘对应目录" -ForegroundColor White
Write-Host "2. 程序将自动通过软链接访问G盘文件" -ForegroundColor White
Write-Host "3. 如需迁移现有文件，请手动移动到G盘目录" -ForegroundColor White