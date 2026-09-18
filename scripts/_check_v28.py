#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8 现状盘点: HTTP + 活动流 + 订单"""
import os, sys, json, subprocess
from pathlib import Path
from collections import Counter

ROOT = Path(r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目')
os.chdir(ROOT)

def curl(url):
    try:
        r = subprocess.run(['curl','-s','-o','/dev/null','-w',
            '%{http_code}|%{size_download}|%{content_type}',url],
            capture_output=True, text=True, timeout=5)
        code, size, mime = r.stdout.split('|')
        return f'{code} | {size}B | {mime}'
    except Exception as e:
        return f'ERR {e}'

print('=== A. HTTP :18765 健康 ===')
print(f'  工作台 v2.7: {curl("http://127.0.0.1:18765/.workbuddy/artifacts/lobster-design-jiedan-station.html")}')
print(f'  活动流:     {curl("http://127.0.0.1:18765/.workbuddy/activity_stream.jsonl")}')
print(f'  订单数:     {curl("http://127.0.0.1:18765/.workbuddy/orders_count.txt")}')
print(f'  5子库 CGI:  {curl("http://127.0.0.1:18765/scripts/lib/recall_from_lib.py?lib=wecom_jd")}')

print()
print('=== B. 活动流实时统计 ===')
acts_file = Path('.workbuddy/activity_stream.jsonl')
if acts_file.exists():
    acts = []
    for line in acts_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            try: acts.append(json.loads(line))
            except: pass
    print(f'  总活动数: {len(acts)} 条')
    print(f'  Agent 分布: {dict(Counter(a.get("agent","?") for a in acts))}')
    print(f'  Channel 分布: {dict(Counter(a.get("channel","?") for a in acts))}')
    print(f'  其中 channel=wecom (真实企微): {sum(1 for a in acts if a.get("channel")=="wecom")} 条')
    if acts:
        print(f'  最新一条: {acts[-1].get("ts","?")} · {acts[-1].get("agent","?")}/{acts[-1].get("channel","?")} · {acts[-1].get("action","?")}')

print()
print('=== C. 真实订单落盘目录 ===')
d = Path('01_正在执行实单')
total_files = 0
total_dirs = 0
for sub in sorted(d.iterdir()):
    if not sub.is_dir(): continue
    fs = list(sub.rglob('*'))
    real_files = [f for f in fs if f.is_file()]
    sz = sum(f.stat().st_size for f in real_files)
    total_files += len(real_files)
    total_dirs += 1
    print(f'  📦 {sub.name} → {len(real_files)}文件 / {sz}B')
print(f'  💎 合计: {total_dirs} 单 / {total_files} 文件')
