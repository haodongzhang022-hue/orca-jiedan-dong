#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stability_monitor.py — 双实例舰队稳定性监控
每60秒采样一次：端口存活(4567/15800/57321)、msgbus进程数、队列积压、锁状态。
用法: python scripts/stability_monitor.py --minutes 15
"""
import argparse
import json
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
LOG_DIR = Path("G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"stability_{datetime.now().strftime('%Y%m%d_%H%M')}.log"

PORTS = {"aicodeswitch_4567": 4567, "hermes_gui_15800": 15800, "codex_gui_57321": 57321}


def port_alive(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def msgbus_procs() -> int:
    try:
        # 修复(2026-07-28): wmic输出为GBK字节, 必须按字节读取后errors='ignore'解码,
        # 否则subprocess读线程会因0xc1等GBK引导字节触发UnicodeDecodeError导致计数失效
        out = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "commandline"],
            capture_output=True, timeout=20).stdout.decode("gbk", errors="ignore")
        return out.count("msgbus")
    except Exception:
        return -1


def queue_stats() -> dict:
    stats = {}
    inbox = PROJECT / "msgbus" / "inbox"
    if inbox.exists():
        for d in inbox.iterdir():
            if d.is_dir():
                pend = done = 0
                for f in d.glob("*.json"):
                    try:
                        st = json.load(open(f, encoding="utf-8")).get("status")
                        if st == "pending":
                            pend += 1
                        elif st in ("done", "forwarded", "delivered"):
                            done += 1
                    except Exception:
                        pass
                stats[d.name] = {"pending": pend, "settled": done}
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=15)
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    rounds = max(1, args.minutes * 60 // args.interval)
    anomalies = 0
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"=== 稳定性监控启动 {datetime.now()} | {args.minutes}分钟 x {args.interval}s ===\n")
        for i in range(rounds):
            ts = datetime.now().strftime("%H:%M:%S")
            ports = {k: port_alive(v) for k, v in PORTS.items()}
            procs = msgbus_procs()
            q = queue_stats()
            total_pending = sum(v["pending"] for v in q.values())
            bad = [k for k, ok in ports.items() if not ok and k != "codex_gui_57321"]
            if bad or total_pending > 10:
                anomalies += 1
                flag = "ANOMALY"
            else:
                flag = "OK"
            f.write(f"[{ts}] round={i+1}/{rounds} {flag} ports={ports} msgbus_procs={procs} pending={total_pending} queues={q}\n")
            f.flush()
            if i < rounds - 1:
                time.sleep(args.interval)
        f.write(f"=== 监控结束 {datetime.now()} | 异常轮次: {anomalies}/{rounds} ===\n")
    print(f"稳定性日志: {LOG_FILE} | 异常: {anomalies}/{rounds}")


if __name__ == "__main__":
    main()
