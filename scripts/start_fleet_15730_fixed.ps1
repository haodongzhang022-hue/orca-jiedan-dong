$ErrorActionPreference = 'Stop'
$py = 'C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe'
$service = (Get-ChildItem -LiteralPath 'E:\lobster_fleet_mcp' -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'codex_tool_proxy.py') } | Select-Object -First 1).FullName
$runtime = 'E:\lobster_ai_temp_fleet'
$logs = Join-Path $runtime 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$out = Join-Path $logs 'codex15730_out.log'
$err = Join-Path $logs 'codex15730_err.log'
$script = Join-Path $service 'codex_tool_proxy.py'
$py_ok = Test-Path -LiteralPath $py
$script_ok = Test-Path -LiteralPath $script
if (-not $py_ok) { throw 'python_runtime_missing' }
if (-not $script_ok) { throw 'proxy_script_missing' }
$existing = Get-NetTCPConnection -LocalPort 15730 -State Listen -ErrorAction SilentlyContinue
if (!$existing) {
  $args = @($script)
  Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $service -RedirectStandardOutput $out -RedirectStandardError $err -WindowStyle Hidden
  Start-Sleep -Seconds 5
}
$conn = Get-NetTCPConnection -LocalPort 15730 -State Listen -ErrorAction SilentlyContinue
if (!$conn) { throw ('port_15730_not_listening: ' + $err) }
$health = Invoke-WebRequest 'http://127.0.0.1:15730/health' -UseBasicParsing -TimeoutSec 5
Write-Output ('15730 LISTENING PID=' + $conn.OwningProcess)
Write-Output ('HEALTH ' + $health.StatusCode)
