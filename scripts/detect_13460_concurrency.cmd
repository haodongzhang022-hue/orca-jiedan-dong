@echo off
chcp 65001 >nul
REM ============================================================
REM detect_13460_concurrency.cmd · 13460 代理并发限流检测去重 v1.0
REM 归档：docs/13460并发限流_预案_20260814.md
REM 触发：群聊报 429/403 atomgit_session_concurrency_conflict 时一键跑
REM ============================================================
setlocal enabledelayedexpansion

echo ============================================================
echo  13460 代理并发检测 · %date% %time%
echo ============================================================

REM --- 1. AtomCode 代理实例数（atomcode_proxy.py） ---
echo.
echo [1] AtomCode 代理实例（atomcode_proxy.py 13460）：
set AP_CNT=0
for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'atomcode_proxy.py.*13460' } | Select-Object -ExpandProperty ProcessId)" 2^>nul') do (
  set /a AP_CNT+=1
  echo     !AP_CNT!. PID %%P
)
echo     --- 代理实例数：!AP_CNT! 份

if !AP_CNT! GTR 1 (
  echo     [警告] 代理跑多份，这是 403 atomgit_session_concurrency_conflict 的直接来源，开始去重...
  REM 保留 PID 最小的一份，杀其余
  set KEEP_PID=999999
  for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'atomcode_proxy.py.*13460' } | Sort-Object ProcessId | Select-Object -First 1 -ExpandProperty ProcessId)" 2^>nul') do set KEEP_PID=%%P
  echo     保留 PID !KEEP_PID!，杀其余...
  for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'atomcode_proxy.py.*13460' -and $_.ProcessId -ne !KEEP_PID! } | Select-Object -ExpandProperty ProcessId)" 2^>nul') do (
    echo     taskkill /F /PID %%P
    taskkill /F /PID %%P >nul 2>&1
  )
) else (
  echo     [正常] 代理仅一份
)

REM --- 2. Hermes Gateway 实例数 ---
echo.
echo [2] Hermes Gateway 实例（hermes_cli.main gateway run）：
set GW_CNT=0
for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'hermes_cli.main gateway run' } | Select-Object -ExpandProperty ProcessId)" 2^>nul') do (
  set /a GW_CNT+=1
  echo     !GW_CNT!. PID %%P
)
echo     --- Gateway 实例数：!GW_CNT! 份

if !GW_CNT! GTR 1 (
  echo     [警告] Gateway 跑多份，偶发 401 token rejected，去重...
  set KEEP_GW=999999
  for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'hermes_cli.main gateway run' } | Sort-Object ProcessId | Select-Object -First 1 -ExpandProperty ProcessId)" 2^>nul') do set KEEP_GW=%%P
  for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'hermes_cli.main gateway run' -and $_.ProcessId -ne !KEEP_GW! } | Select-Object -ExpandProperty ProcessId)" 2^>nul') do (
    taskkill /F /PID %%P >nul 2>&1
  )
  echo     已去重，保留 PID !KEEP_GW!
) else (
  echo     [正常] Gateway 仅一份
)

REM --- 3. ESTABLISHED 连接数 ---
echo.
echo [3] 13460 ESTABLISHED 连接：
set EST_CNT=0
for /f %%P in ('netstat -ano ^| findstr "13460" ^| findstr "ESTABLISHED"') do (
  set /a EST_CNT+=1
  echo     !EST_CNT!. %%P
)
echo     --- 活跃连接数：!EST_CNT!
if !EST_CNT! GTR 3 (
  echo     [警告] 并发连接>3，Lite/Pro 套餐易触发 429，建议三引擎只留一个活跃窗口
) else (
  echo     [正常] 并发连接在阈值内
)

REM --- 4. 三引擎 hermes_bridge 活跃数 ---
echo.
echo [4] Hermes Studio 引擎桥（hermes_bridge.py）：
set HB_CNT=0
for /f %%P in ('powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'hermes_bridge.py' } | Select-Object -ExpandProperty ProcessId)" 2^>nul') do (
  set /a HB_CNT+=1
  echo     !HB_CNT!. PID %%P
)
echo     --- 引擎桥数：!HB_CNT!
if !HB_CNT! GTR 1 (
  echo     [警告] 多引擎桥同时活跃，群聊期间建议只留应答引擎的房间，其余暂停
)

echo.
echo ============================================================
echo  检测完成。代理=!AP_CNT! Gateway=!GW_CNT! EST=!EST_CNT! 引擎桥=!HB_CNT!
echo  处理建议：多份已去重；多引擎桥需在 Studio 里手动暂停非应答房间
echo ============================================================
echo.
pause
endlocal
