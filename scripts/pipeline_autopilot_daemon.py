#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流水线自动驾驶 daemon
每 30 秒调用一次 pipeline_autopilot.py，保持看板与任务分发实时更新
"""
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
SCRIPT = PROJECT / "scripts" / "pipeline_autopilot.py"
PYTHON = Path("C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe")

if not SCRIPT.exists():
    print(f"ERROR: {SCRIPT} not found", file=sys.stderr)
    sys.exit(1)

print("[daemon] 启动，每 30 秒执行一次 pipeline_autopilot.py")
while True:
    try:
        result = subprocess.run([str(PYTHON), str(SCRIPT)], cwd=str(PROJECT), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[daemon] ERROR: {result.stderr}", file=sys.stderr)
        else:
            print(f"[daemon] OK: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            for line in result.stdout.strip().splitlines():
                print(f"  {line}")
    except Exception as e:
        print(f"[daemon] EXCEPTION: {e}", file=sys.stderr)
    time.sleep(30)
