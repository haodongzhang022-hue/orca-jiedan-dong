<#
.SYNOPSIS
  企业微信群定制接单项目 · 标准目录一键创建（PowerShell 版）
.DESCRIPTION
  创建定型目录骨架 + .gitkeep 占位，确保空目录纳入 git。
  具体订单的【日期_简述】项目文件夹由 business_folders.py 在接单时自动生成。
.PARAMETER ProjectRoot
  项目根目录（默认取本脚本的上级目录）。
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File "创建目录结构.ps1"
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = 'Continue'
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "项目根目录: $ProjectRoot"

# 业务目录骨架（与用户定型标准一致）
$Dirs = @(
    "00_模拟演练案例库\海报设计案例",
    "00_模拟演练案例库\画册折页案例",
    "00_模拟演练案例库\PPT修改排版案例",
    "00_模拟演练案例库\短视频物料案例",
    "00_模拟演练案例库\其他品类案例",
    "01_正在执行实单",
    "02_已完结归档实单\海报类",
    "02_已完结归档实单\画册排版类",
    "02_已完结归档实单\PPT制作类",
    "02_已完结归档实单\视频图文类",
    "02_已完结归档实单\其他类",
    "03_通用素材资源库\Grunge摇滚风格素材",
    "03_通用素材资源库\科技风版式素材",
    "03_通用素材资源库\PPT版式模板"
)

foreach ($rel in $Dirs) {
    $full = Join-Path $ProjectRoot $rel
    if (-not (Test-Path $full)) { New-Item -ItemType Directory -Path $full -Force | Out-Null }
    $keep = Join-Path $full ".gitkeep"
    if (-not (Test-Path $keep)) { New-Item -ItemType File -Path $keep -Force | Out-Null }
    Write-Host "  [OK] $rel"
}

# 顶层业务目录说明 README
Set-Content -Path (Join-Path $ProjectRoot "00_模拟演练案例库\README.md") -Encoding UTF8 -Value @"
# 00_模拟演练案例库

群里几十元低价需求、内部训练需求统一归入此处，**仅用于跑通流水线、沉淀技能，不接真实交易、不对外交付实单**。

按品类分子目录：
- 海报设计案例
- 画册折页案例
- PPT修改排版案例
- 短视频物料案例
- 其他品类案例（钥匙扣/周边/包装/Logo 等）

> 每个需求单独建 `【日期_简述】` 文件夹，内部标配：聊天记录 / 参考原图 / 需求确认文档 / 工程源文件 / 各版本稿件 / 最终交付文件（由 business_folders.py 自动生成）。
"@

Set-Content -Path (Join-Path $ProjectRoot "01_正在执行实单\README.md") -Encoding UTF8 -Value @"
# 01_正在执行实单

满足 ￥300 起步标准、已收定金的真实付费订单放入此处。每个订单独立 `【日期_简述】` 文件夹。

> 交付完成、尾款结清后，运行 `python scripts/archive_order.py "【日期_简述】"` 移动到 `02_已完结归档实单/`。
"@

Set-Content -Path (Join-Path $ProjectRoot "02_已完结归档实单\README.md") -Encoding UTF8 -Value @"
# 02_已完结归档实单

交付完成、尾款结清的统一归档长期保存。按品类归档：
- 海报类
- 画册排版类
- PPT制作类
- 视频图文类
- 其他类
"@

Set-Content -Path (Join-Path $ProjectRoot "03_通用素材资源库\README.md") -Encoding UTF8 -Value @"
# 03_通用素材资源库

跨订单复用的通用素材：字体、纹理、风格参考图、提示词模板。当前分类：
- Grunge摇滚风格素材
- 科技风版式素材
- PPT版式模板

> 与 fleet_exchange / scripts / worktrees 等代码调度层互不干扰。
"@

Write-Host ""
Write-Host "✅ 标准目录结构已创建完毕。" -ForegroundColor Green
Write-Host "   下一步：接单时自动驾驶会自动调用 business_folders.py 把新需求落库到对应目录。"
