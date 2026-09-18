"""v2.7 综合交付验证 — HTTP + 落盘 + 活动流"""
import urllib.request, json
from pathlib import Path
from collections import Counter
from datetime import datetime

PROJ = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目')
KB = Path(r'E:\龙虾AI主控中心\我的AI分身\知识库')

def http_head(url, timeout=5):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get('Content-Type','?'), r.headers.get('Content-Length','?')
    except Exception as e:
        return None, str(e), '?'

def http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)

print('='*80)
print('🦞 v2.7 综合交付验证 · zero-cost · 零网络 · 零积分')
print(f'  · 时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print(f'  · 项目: {PROJ}')
print('='*80)

# ============ 验证1: HTTP 健康 ============
print('\n[1] HTTP :18765 健康 + MIME 诊断')
checks = [
    ('工作台 v2.7', 'http://127.0.0.1:18765/.workbuddy/artifacts/lobster-design-jiedan-station.html'),
    ('活动流', 'http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl'),
    ('订单数', 'http://127.0.0.1:18765/.workbuddy/orders_count.txt'),
    ('子库调取:wecom_jd', 'http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=wecom_jd'),
    ('子库调取:gold_dh', 'http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=gold_dh'),
    ('子库调取:wangpan_jc', 'http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=wangpan_jc'),
    ('子库调取:xianyu_yw', 'http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=xianyu_yw'),
]
for name, url in checks:
    status, mime, sz = http_head(url)
    if status == 200:
        print(f'  ✅ {name:18} → {status} | {mime:50} | {sz}B')
    else:
        print(f'  ❌ {name:18} → {status} | {mime}')

# ============ 验证2: 活动流实时 ============
print('\n[2] 活动流实时')
acts = [json.loads(l) for l in (PROJ/'.workbuddy/activity_stream.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
print(f'  · 总条数: {len(acts)}')
print(f'  · Agent 分布: {dict(Counter(a["agent"] for a in acts))}')
print(f'  · Channel 分布: {dict(Counter(a["channel"] for a in acts))}')
last5 = acts[-5:]
print(f'  · 最新 5 条:')
for a in last5:
    print(f'      · {a["ts"]} · {a["agent"]}/{a["channel"]} · {a["action"][:40]}')

# ============ 验证3: 文件落地（含本次 mock） ============
print('\n[3] 文件落地验证')
total_files = 0
total_dirs = 0
for d in sorted((PROJ/'01_正在执行实单').iterdir()):
    if not d.is_dir(): continue
    total_dirs += 1
    fs = [f for f in d.rglob('*') if f.is_file()]
    total_files += len(fs)
print(f'  · 01_正在执行实单 共 {total_dirs} 目录 / {total_files} 文件')

# 本次 mock 跑出来的 4 条新建目录
mock_now = []
for d in sorted((PROJ/'01_正在执行实单').iterdir()):
    if '企微自动入库' in d.name:
        fs = list(d.rglob('*.md'))
        mock_now.extend([(d.name, f.name, f.stat().st_size) for f in fs])
print(f'  · 本次 mock 自动入库: {len(mock_now)} 个文件')
for dn, fn, sz in mock_now:
    print(f'      · {dn[:40]}.../{fn} = {sz}B')

# ============ 验证4: 5子库映射 ============
print('\n[4] 5 子库本地存在性')
cfg = json.loads((PROJ/'scripts/lib/lib_config.json').read_text(encoding='utf-8'))
for lib in cfg['libraries']:
    p = Path(lib['local_path'])
    exists = p.exists()
    n_files = len([f for f in p.rglob('*') if f.is_file()]) if exists else 0
    mark = '✅' if exists else '❌'
    print(f'  {mark} {lib["icon"]} [{lib["id"]:12}] {lib["name"]:25} → {n_files:6} 文件')

# ============ 验证5: 知识库说明文档 ============
print('\n[5] 知识库-5项目联动说明.md')
md = KB/'知识库‑5项目联动说明.md'
if md.exists():
    sz = md.stat().st_size
    lines = md.read_text(encoding='utf-8').count('\n')
    print(f'  ✅ {md} = {sz}B / {lines} 行')
else:
    print(f'  ❌ 未找到: {md}')

# ============ 验证6: 同步脚本可执行 ============
print('\n[6] 脚本可执行性')
for py in ['lexiang_sync.py', 'wecom_filter.py', 'recall_from_lib.py']:
    p = PROJ / 'scripts/lib' / py
    print(f'  ✅ {py:30} ({p.stat().st_size}B)' if p.exists() else f'  ❌ {py} 不存在')

print('\n' + '='*80)
print('✅ 三验证完成')
print('='*80)
