"""强制清理18765旧进程 + 重启带新MIME的server"""
import subprocess, time, urllib.request, sys
from pathlib import Path

ROOT_PY = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
SCRIPT = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\serve_dashboard.py"

# 1) 用 PowerShell 杀掉所有占用 18765 的进程
ps_kill = """
$conns = Get-NetTCPConnection -LocalPort 18765 -ErrorAction SilentlyContinue
foreach ($c in $conns) {
  try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
}
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*serve_dashboard*' } | Stop-Process -Force
"""
subprocess.run(['powershell', '-NoProfile', '-Command', ps_kill], capture_output=True)
time.sleep(0.5)

# 2) 启动新 server
out = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.workbuddy\server_18765.log')
log = out.open('w', encoding='utf-8')
proc = subprocess.Popen([ROOT_PY, SCRIPT], stdout=log, stderr=log,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
time.sleep(1.5)

# 3) 验证
for url, name in [
    ('http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl', '活动流'),
    ('http://127.0.0.1:18765/.workbuddy/artifacts/lobster-design-jiedan-station.html', '工作台'),
    ('http://127.0.0.1:18765/.workbuddy/orders_count.txt', '订单数'),
]:
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=3) as r:
            print(f'  ✅ {name:6} → HTTP {r.status} | MIME={r.headers.get("Content-Type")}')
    except Exception as e:
        print(f'  ❌ {name:6} → {e}')

print(f'\n📝 server log: {out}')
