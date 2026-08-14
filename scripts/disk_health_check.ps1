# Disk Health Check - created 2026-08-14 after WeChat failed to open
# Checks: C drive free space (<2GB alert) / desktop WeChat shortcut / xwechat crashinfo
$log = 'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\logs\disk_health.log'
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content -Path $log -Value "[$stamp] ====== Disk Health Check Start ======"

# 1. C drive free space
$freeMB = [math]::Round((Get-PSDrive C).Free / 1MB, 0)
Add-Content -Path $log -Value "[$stamp] C drive free: $freeMB MB"
if ($freeMB -lt 2048) {
    Add-Content -Path $log -Value "[$stamp] ALERT: C drive free below 2GB ($freeMB MB) - clean Docker/wsl caches!"
    try { [System.Windows.Forms.MessageBox]::Show("C drive free below 2GB! Clean Docker/wsl caches.", 'Disk Alert') | Out-Null } catch {}
}

# 2. Desktop WeChat shortcut target
$desk = [Environment]::GetFolderPath('Desktop')
if (Test-Path "$desk\WeChatSetup.exe") {
    Add-Content -Path $log -Value "[$stamp] ALERT: Desktop WeChatSetup.exe still exists - check broken symlink to F:"
} else {
    Add-Content -Path $log -Value "[$stamp] Desktop WeChatSetup.exe gone - OK"
}
if (Test-Path "$desk\微信.lnk") {
    Add-Content -Path $log -Value "[$stamp] Desktop 微信.lnk present - OK"
} else {
    Add-Content -Path $log -Value "[$stamp] ALERT: Desktop 微信.lnk missing!"
}

# 3. xwechat crashinfo
if (Test-Path 'C:\Users\Administrator\AppData\Roaming\Tencent\xwechat\crashinfo') {
    Add-Content -Path $log -Value "[$stamp] xwechat\crashinfo OK"
} else {
    Add-Content -Path $log -Value "[$stamp] ALERT: xwechat\crashinfo missing - WeChat crash reporter will fail!"
}

Add-Content -Path $log -Value "[$stamp] ====== Disk Health Check Done ======"
Write-Output 'Disk health check done. See logs/disk_health.log'
