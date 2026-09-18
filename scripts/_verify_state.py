"""真状态盘点 — 9单 + 活动流"""
from pathlib import Path
import json
from collections import Counter

base = Path('01_正在执行实单')
total = 0
print('=== v2.6 真跑成果（截图2 自证） ===')
for d in sorted(base.iterdir()):
    if not d.is_dir():
        continue
    fs = [f for f in d.rglob('*') if f.is_file()]
    sz = sum(f.stat().st_size for f in fs)
    total += len(fs)
    print(f'  📦 {d.name[:50]}... → {len(fs)} 文件 / {sz} B')
print(f'\n  💎 全部订单共 {total} 个真实文件已落盘')

print('\n=== 活动流实时 ===')
acts = [json.loads(l) for l in Path('.workbuddy/activity_stream.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
print(f'  🎬 活动流: {len(acts)} 条')
print(f'     Agent 分布:   {dict(Counter(a["agent"] for a in acts))}')
print(f'     Channel 分布: {dict(Counter(a["channel"] for a in acts))}')
print(f'     最新3条:')
for a in acts[-3:]:
    print(f'        · {a["ts"]} · {a["agent"]}/{a["channel"]} · {a["action"][:30]}')

print('\n=== HTTP 18765 健康 + MIME 诊断 ===')
import urllib.request
for url, name in [
    ('http://127.0.0.1:18765/.workbuddy/artifacts/lobster-design-jiedan-station.html', '工作台'),
    ('http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl', '活动流'),
    ('http://127.0.0.1:18765/.workbuddy/orders_count.txt', '订单数'),
    ('http://127.0.0.1:18765/.workbuddy/auto_scanned_orders.json', '订单池'),
]:
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=3) as r:
            print(f'  ✅ {name} → HTTP {r.status} | MIME={r.headers.get("Content-Type","?")} | size={r.headers.get("Content-Length","?")}B')
    except Exception as e:
        print(f'  ❌ {name} → {e}')
