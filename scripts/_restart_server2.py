"""强制清18765 + 重启"""
import subprocess, time, urllib.request
from pathlib import Path

PY = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\serve_dashboard.py"

# 1) 杀掉所有占用 18765 的进程 + 所有旧 serve_dashboard
ps = r"""
$ErrorActionPreference = 'SilentlyContinue'
Get-NetTCPConnection -LocalPort 18765 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Killing PID $($_.OwningProcess) ..."
    Stop-Process -Id $_.OwningProcess -Force
}
Start-Sleep -Milliseconds 500
$procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like '*serve_dashboard*' -or $_.Id -in (Get-NetTCPConnection -LocalPort 18765 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess)
}
foreach ($p in $procs) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
"""
subprocess.run(['powershell', '-NoProfile', '-Command', ps], capture_output=True, text=True)
time.sleep(1.0)

# 2) 启新
log_path = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.workbuddy\server_18765.log')
log_path.write_text('--- restart @ ' + time.strftime('%H:%M:%S') + ' ---\n', encoding='utf-8')
log = log_path.open('a', encoding='utf-8')
p = subprocess.Popen([PY, SCRIPT], stdout=log, stderr=log,
                     creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
time.sleep(1.5)

# 3) 验证
print('--- HTTP 验证 ---')
for url, name in [
    ('http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl', '活动流'),
    ('http://127.0.0.1:18765/.workbuddy/artifacts/lobster-design-jiedan-station.html', '工作台'),
    ('http://127.0.0.1:18765/.workbuddy/orders_count.txt', '订单数'),
    ('http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=wecom_jd', 'CGI: wcom_jd'),
    ('http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=gold_dh', 'CGI: gold_dh'),
    ('http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=wangpan_jc', 'CGI: wangpan_jc'),
]:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            head = r.read(160).decode('utf-8', errors='ignore').replace('\n', ' ')
            print(f'  ✅ {name} → {r.status} | bytes={r.headers.get("Content-Length","?")} | 头={head[:80]}')
    except Exception as e:
        print(f'  ❌ {name} → {e}')

print(f'\n📝 server log: {log_path}')
