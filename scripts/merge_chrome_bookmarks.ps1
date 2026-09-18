$ErrorActionPreference = 'Stop'
$local = 'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Bookmarks'
$localBackup = 'C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Bookmarks.bak_20260906'
$proxy = 'C:\Users\Administrator\AppData\Local\Google\Chrome\ProxyProfile\Default\Bookmarks'
if (-not (Test-Path $localBackup)) { throw "本地原始备份不存在，停止合并" }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
Copy-Item $local "$local.bak_before_merge_$stamp" -Force
$l = Get-Content $localBackup -Raw | ConvertFrom-Json
$p = Get-Content $proxy -Raw | ConvertFrom-Json
function Walk($node) {
  $items = @($node)
  foreach ($child in @($node.children)) { $items += Walk $child }
  return $items
}
$seen = @{}
foreach ($node in Walk $l.roots.bookmark_bar) { if ($node.url) { $seen[$node.url] = $true } }
foreach ($node in Walk $p.roots.bookmark_bar) {
  if ($node.url -and -not $seen.ContainsKey($node.url)) {
    $l.roots.bookmark_bar.children += $node
    $seen[$node.url] = $true
  }
}
$l | ConvertTo-Json -Depth 100 | Set-Content $local -Encoding UTF8
Write-Output "MERGED local_backup=$localBackup proxy=$proxy output=$local"
Write-Output "BACKUP=$local.bak_before_merge_$stamp"
