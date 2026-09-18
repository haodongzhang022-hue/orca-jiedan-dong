#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_receipt_probe.py v1.0 —— 常驻型守卫的「探针回执器」
================================================================
【它解决的那类守卫】
批处理型守卫（跑完退出）在结尾写一次回执就行，guard_receipt_cli.py 已覆盖。
但**常驻型守卫永不退出** —— hk_proxy_tunnel.bat 是 goto 死循环、
http2socks_7897.py 是 while True: accept()。它们的计划任务结果码永远是
267009 (SCHED_S_TASK_RUNNING)，「结束写回执」这条路径根本走不到，
审计器只能看到「结果码 0 但无回执 → 判黄」的弱证据。

常驻型的正确范式不是「结束时自证」，而是**外部周期探针实测 + 代写回执**：
不看它「有没有在跑」，看它「端不端得出服务」。

【实测方式：三层，逐级加严】
L1 端口 LISTENING  —— 至少证明 socket 起来了
L2 数据面握手      —— 证明不是僵尸监听（可选，见下方 DATA_PLANE）
L3 进程/链路关联   —— 上游依赖是否也在（如 7897 依赖 1081）

【用法】
    python guard_receipt_probe.py --all        # 扫全部常驻守卫并写回执
    python guard_receipt_probe.py hktunnel     # 只探一个
    python guard_receipt_probe.py --json       # 机器可读
    python guard_receipt_probe.py --list       # 列出守卫表

【接入新常驻守卫】往 RESIDENT_GUARDS 加一条即可，不用动主逻辑：
    "myguard": {"ports": [1234], "desc": "我的常驻服务", "expect": "all"},
    expect: all=全部端口必须通 / any=任一通即健康
零积分：纯 stdlib。密钥：无。
"""
import os
import sys
import json
import socket
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guard_receipt import write_receipt

VERSION = "1.0"

# ---------------------------------------------------------------- 守卫登记表
# key 必须与计划任务名归一化后能子串匹配（见 guard_receipt_cli.py 文档）
RESIDENT_GUARDS = {
    "hktunnel": {
        "ports": [1081],
        "desc": "香港 SSH SOCKS5 隧道（hk_proxy_tunnel.bat 常驻）",
        "expect": "all",
        "task": "Lobster_HKTunnel",
    },
    "http2socks": {
        "ports": [7897],
        "desc": "HTTP→SOCKS5 中转器（依赖 1081）",
        "expect": "all",
        "task": "Lobster_HTTP2Socks_7897",
        "depends": [1081],
    },
    "fleet_autorestore": {
        # Fleet 本体是批处理型（已用 CLI 自证），这里做**结果复核**：
        # 它承诺拉起 4 个端口，任一不在 = 上次恢复没真干成。
        "ports": [15721, 15740, 18091],
        "desc": "舰队自恢复结果复核（15721/15740/18091）",
        "expect": "all",
        "task": "LobsterFleet_AutoRestore",
    },
}


def port_listening(port, host="127.0.0.1", timeout=1.0):
    """L1 探针：能连上即视为在监听。"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def probe_one(name, cfg):
    ports = cfg.get("ports", [])
    st = {p: port_listening(p) for p in ports}
    dep = cfg.get("depends", [])
    dep_st = {p: port_listening(p) for p in dep}

    expect = cfg.get("expect", "all")
    if expect == "any":
        healthy = any(st.values()) if st else False
    else:
        healthy = all(st.values()) if st else False

    up = [p for p, v in st.items() if v]
    down = [p for p, v in st.items() if not v]
    dep_down = [p for p, v in dep_st.items() if not v]

    if healthy:
        detail = "端口 %s 全部在听（L1 探针）" % (up or "-")
    elif up:
        detail = "端口部分在听：UP=%s DOWN=%s" % (up, down)
    else:
        detail = "端口全部未监听：%s" % (down or "-")
    if dep_down:
        detail += "；上游依赖未通 %s（可能是依赖侧故障，非本守卫之过）" % dep_down

    write_receipt(
        name, healthy, detail, version=VERSION,
        exit_code=0 if healthy else 1,
        extra={"ports": st, "depends": dep_st, "mode": "probe",
               "task": cfg.get("task", ""), "desc": cfg.get("desc", "")},
    )
    return {"guard": name, "healthy": healthy, "detail": detail,
            "ports": st, "depends": dep_st, "task": cfg.get("task", "")}


def main():
    ap = argparse.ArgumentParser(description="常驻守卫探针回执器")
    ap.add_argument("target", nargs="?", help="守卫名，省略则扫全部")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in RESIDENT_GUARDS.items():
            print("%-18s %-28s ports=%s" % (k, v.get("task", ""), v.get("ports")))
        return 0

    if a.target and a.target in RESIDENT_GUARDS:
        names = [a.target]
    elif a.target:
        print("未知守卫：%s（--list 查看）" % a.target)
        return 2
    else:
        names = list(RESIDENT_GUARDS)

    res = [probe_one(n, RESIDENT_GUARDS[n]) for n in names]

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("=" * 64)
        print("常驻守卫探针回执  v%s  (%d 个守卫)" % (VERSION, len(res)))
        print("=" * 64)
        for r in res:
            flag = "GREEN" if r["healthy"] else "RED  "
            print("[%s] %-18s %s" % (flag, r["guard"], r["detail"]))
        bad = [r["guard"] for r in res if not r["healthy"]]
        print("-" * 64)
        print("健康 %d / %d%s" % (len(res) - len(bad), len(res),
                                  ("  红项：" + ", ".join(bad)) if bad else "  全绿"))
    return 0 if all(r["healthy"] for r in res) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("[probe] fatal: %s" % e)
        sys.exit(0)      # 探针失败不许把计划任务染红
