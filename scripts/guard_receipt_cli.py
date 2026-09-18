#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
guard_receipt_cli.py v1.0 —— 回执命令行接入点（给 .bat / 非 Python 守卫用）
================================================================
【为什么需要它】
guard_receipt.py 是 Python 模块，只有 Python 守卫能 import。
但龙虾舰队里一半守卫是 .bat（lobster_fleet_autostart.bat / hk_proxy_tunnel.bat），
它们没法 import，于是只能裸靠「计划任务结果码」判健康 —— 而结果码 267009
(0x41301 SCHED_S_TASK_RUNNING) 只表示「实例正在跑」，与成功与否无关。

本 CLI 让任何能起进程的守卫都能一行落回执：

    %PY% guard_receipt_cli.py <guard> <healthy:0|1> "<detail>" [exit_code] [version]

.bat 内典型用法：
    set "PY=C:\Users\...\python.exe"
    "%PY%" "E:\...\scripts\guard_receipt_cli.py" fleet_autorestore 1 "4/4 端口已恢复" %ERRORLEVEL% 1.4

【回执名与计划任务的匹配铁律】
审计器把两边都做归一化（只留 a-z0-9 小写）后判断「回执名 ⊂ 任务名」。
所以 guard 名必须从任务名里真实截取，举例：
    LobsterFleet_AutoRestore  -> "fleet_autorestore"   ✅（"fleetautorestore" 是子串）
    Lobster_HKTunnel          -> "hktunnel"            ✅
    Lobster_HTTP2Socks_7897   -> "http2socks"          ✅
写成 "fleet"（太短易误配）或 "fleet_autostart"（非子串）都会匹配不上。

【退出码约定】永远返回 0 —— 回执写失败不许拖垮宿主守卫。
零积分：纯 stdlib，不联网。密钥：无。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from guard_receipt import write_receipt
except Exception as e:            # 模块缺失也不能崩宿主
    print("[receipt-cli] import guard_receipt failed: %s" % e)
    sys.exit(0)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)
    guard = sys.argv[1]
    healthy = sys.argv[2].strip().lower() in ("1", "true", "ok", "yes", "y")
    detail = sys.argv[3] if len(sys.argv) > 3 else ""
    try:
        exit_code = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    except Exception:
        exit_code = 0
    version = sys.argv[5] if len(sys.argv) > 5 else "1.0"
    p = write_receipt(guard, healthy, detail, version=version, exit_code=exit_code)
    print("[receipt-cli] %s healthy=%s -> %s" % (guard, healthy, p or "FAILED"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[receipt-cli] error: %s" % e)
    sys.exit(0)
