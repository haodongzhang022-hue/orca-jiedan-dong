#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lobster_mem_guard.py —— 龙虾进程泄漏与内存健康守卫 v1.0

定位（与 ai-workstation-morning-check 的边界）：
  - morning-check = 七维晨检（磁盘/端口/MCP/Chrome/运行时），「组件在不在」
  - 本守卫       = 内存与进程专项（压力/泄漏/僵尸实例），「系统扛不扛得住」
  两者互补，不重复。

背景（2026-09-19 实证）：
  卡顿真凶不是磁盘、不是掉盘，而是 **进程泄漏堆积把内存压到 90%**：
  GptBrowser 78 实例 / 11.88GB，WorkBuddy 18 实例 / 2.76GB。
  诊断出来了却没有工具化 —— 本守卫就是把这个洞补上。

铁律：
  1. 纯 stdlib、零积分：ctypes 取内存，tasklist /FO CSV 取进程（禁 wmic）。
  2. **默认只读**，绝不自动杀进程。`--apply` 才动手，且必须再加 `--i-know-what-i-am-doing`。
  3. 白名单进程（含宿主自身 WorkBuddy / python / node）**永不杀**。
  4. 回执诚实：每项结论都要有数字证据，禁止「看起来正常」。

用法：
  python lobster_mem_guard.py                  # 体检报告（默认）
  python lobster_mem_guard.py --json           # 机器可读，接 guard_receipt
  python lobster_mem_guard.py --plan           # 输出清理计划 + 可直接执行的 .bat（不执行）
  python lobster_mem_guard.py --watch 5 60     # 采样 5 次、间隔 60s，写趋势历史
  python lobster_mem_guard.py --apply --i-know-what-i-am-doing   # 真正清理（谨慎）
"""

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime

VERSION = "1.0"

# ---------------------------------------------------------------- 配置

# 内存压力阈值
MEM_LOAD_YELLOW = 80          # 物理内存占用率 %
MEM_LOAD_RED = 90
AVAIL_GB_YELLOW = 4.0         # 可用物理内存 GB
AVAIL_GB_RED = 2.0
SINGLE_PROC_GB_REPORT = 1.5   # 单进程内存超过此值单独点名
SINGLE_PROC_GB_RED = 3.0

# 进程实例数阈值：yellow / red / keep(清理时保留的最大实例数) / killable
DEFAULT_RULE = {"yellow": 15, "red": 40, "keep": 0, "killable": False, "note": "未登记进程，只观察不动手"}
RULES = {
    "GptBrowser.exe":  {"yellow": 12, "red": 30, "keep": 3, "killable": True,
                        "note": "本机泄漏头号源（09-19 实测 78 实例/11.88GB）"},
    "360se.exe":       {"yellow": 8,  "red": 20, "keep": 2, "killable": True,  "note": "360 安全浏览器"},
    "Doubao.exe":      {"yellow": 8,  "red": 18, "keep": 2, "killable": True,  "note": "豆包客户端"},
    "chrome.exe":      {"yellow": 15, "red": 40, "keep": 3, "killable": True,  "note": "Chrome 官方版"},
    "msedge.exe":      {"yellow": 12, "red": 30, "keep": 2, "killable": True,  "note": "Edge"},
    "WorkBuddy.exe":   {"yellow": 12, "red": 25, "keep": 0, "killable": False,
                        "note": "宿主自身，杀了自己会打断会话 —— 只报不杀"},
    "Marvis.exe":      {"yellow": 8,  "red": 20, "keep": 0, "killable": False, "note": "AI 客户端，人工确认后再动"},
    "python.exe":      {"yellow": 10, "red": 25, "keep": 0, "killable": False, "note": "MCP 服务/脚本运行时"},
    "pythonw.exe":     {"yellow": 10, "red": 25, "keep": 0, "killable": False, "note": "MCP 服务/脚本运行时"},
    "node.exe":        {"yellow": 10, "red": 25, "keep": 0, "killable": False, "note": "Node 服务"},
}

# 绝对白名单：任何情况下都不杀（系统 + 自身运行时 + shell）
NEVER_KILL = {
    "System", "System Idle Process", "Registry", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe", "explorer.exe", "dwm.exe",
    "conhost.exe", "ctfmon.exe", "fontdrvhost.exe", "audiodg.exe", "spoolsv.exe",
    "taskhostw.exe", "RuntimeBroker.exe", "dllhost.exe", "WUDFHost.exe", "MsMpEng.exe",
    "SecurityHealthService.exe", "SearchIndexer.exe", "ShellExperienceHost.exe",
    "StartMenuExperienceHost.exe", "ApplicationFrameHost.exe", "TextInputHost.exe",
    "WorkBuddy.exe", "python.exe", "pythonw.exe", "node.exe", "bash.exe", "cmd.exe",
    "powershell.exe", "pwsh.exe", "git.exe", "ssh.exe",
}

# 系统天生多实例的进程：只计数不判级（否则 svchost 81 个直接把守卫刷成红，误报会毁掉守卫可信度）
SYSTEM_NOISE = {
    "svchost.exe", "conhost.exe", "RuntimeBroker.exe", "dllhost.exe", "WUDFHost.exe",
    "taskhostw.exe", "MsMpEng.exe", "SearchIndexer.exe", "fontdrvhost.exe",
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe",
    "audiodg.exe", "spoolsv.exe", "SecurityHealthService.exe", "ctfmon.exe", "dwm.exe",
}

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "mem_guard_history.jsonl")


# ---------------------------------------------------------------- 采集层

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def memory_status():
    """ctypes 直取物理内存，禁 wmic。"""
    st = MEMORYSTATUSEX()
    st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
    if not ok:
        return None
    gb = float(1 << 30)
    return {
        "load_pct": st.dwMemoryLoad,
        "total_gb": round(st.ullTotalPhys / gb, 2),
        "avail_gb": round(st.ullAvailPhys / gb, 2),
        "used_gb": round((st.ullTotalPhys - st.ullAvailPhys) / gb, 2),
        "total_pagefile_gb": round(st.ullTotalPageFile / gb, 2),
        "avail_pagefile_gb": round(st.ullAvailPageFile / gb, 2),
    }


def list_processes():
    """tasklist /FO CSV /NH —— 返回 [(name, pid, mem_kb)]。"""
    out = []
    try:
        raw = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                             capture_output=True, timeout=90)
        text = raw.stdout.decode("utf-8", errors="replace")
    except Exception as exc:                                  # noqa: BLE001
        sys.stderr.write("[warn] tasklist 调用失败: %s\n" % exc)
        return out
    for line in text.splitlines():
        parts = line.split('","')
        if len(parts) < 5:
            continue
        name = parts[0].lstrip('"')
        pid_s = parts[1].strip('"')
        mem_s = parts[4].strip('"').replace(",", "").replace(" K", "").replace("K", "").strip()
        try:
            pid = int(pid_s)
        except ValueError:
            continue
        try:
            mem_kb = int(mem_s)
        except ValueError:
            mem_kb = 0
        out.append((name, pid, mem_kb))
    return out


# ---------------------------------------------------------------- 分析层

def aggregate(procs):
    cnt, mem = Counter(), Counter()
    for name, _pid, kb in procs:
        cnt[name] += 1
        mem[name] += kb
    return cnt, mem


def rule_of(name):
    return RULES.get(name, DEFAULT_RULE)


def level_of(count, rule, name=""):
    if name in SYSTEM_NOISE:
        return "GREEN"          # 系统进程天生多实例，不参与泄漏判级
    if count >= rule["red"]:
        return "RED"
    if count >= rule["yellow"]:
        return "YELLOW"
    return "GREEN"


def analyze(procs):
    """产出结构化体检结果。"""
    mem_st = memory_status() or {}
    cnt, mem = aggregate(procs)

    groups = []
    for name, c in cnt.most_common():
        rule = rule_of(name)
        total_mb = round(mem[name] / 1024.0, 1)
        groups.append({
            "name": name,
            "count": c,
            "total_mb": total_mb,
            "total_gb": round(mem[name] / 1024.0 / 1024.0, 2),
            "avg_mb": round(total_mb / c, 1) if c else 0.0,
            "system_noise": name in SYSTEM_NOISE,
            "level": level_of(c, rule, name),
            "killable": rule["killable"] and name not in NEVER_KILL,
            "keep": rule["keep"],
            "note": rule["note"],
        })

    # 单进程巨兽
    giants = []
    for name, pid, kb in procs:
        if kb / 1024.0 / 1024.0 >= SINGLE_PROC_GB_REPORT:
            giants.append({
                "name": name, "pid": pid,
                "gb": round(kb / 1024.0 / 1024.0, 2),
                "level": "RED" if kb / 1024.0 / 1024.0 >= SINGLE_PROC_GB_RED else "YELLOW",
            })
    giants.sort(key=lambda x: -x["gb"])

    # 内存总体判级
    load = mem_st.get("load_pct", 0)
    avail = mem_st.get("avail_gb", 999.0)
    if load >= MEM_LOAD_RED or avail <= AVAIL_GB_RED:
        mem_level = "RED"
    elif load >= MEM_LOAD_YELLOW or avail <= AVAIL_GB_YELLOW:
        mem_level = "YELLOW"
    else:
        mem_level = "GREEN"

    reds = [g for g in groups if g["level"] == "RED"]
    yellows = [g for g in groups if g["level"] == "YELLOW"]
    if mem_level == "RED" or reds:
        overall = "RED"
    elif mem_level == "YELLOW" or yellows or giants:
        overall = "YELLOW"
    else:
        overall = "GREEN"

    return {
        "version": VERSION,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "memory": mem_st,
        "mem_level": mem_level,
        "process_total": len(procs),
        "process_kinds": len(cnt),
        "groups": groups,
        "giants": giants,
        "overall": overall,
    }


def build_plan(result, procs):
    """生成清理计划：只挑 killable 且超 keep 的实例，按内存降序保留 Top-keep。"""
    plan = []
    by_name = {}
    for name, pid, kb in procs:
        by_name.setdefault(name, []).append((pid, kb))

    for g in result["groups"]:
        name = g["name"]
        if not g["killable"]:
            continue
        keep = max(0, int(g["keep"]))
        items = sorted(by_name.get(name, []), key=lambda x: -x[1])
        to_kill = items[keep:]                       # 保留内存最大的 keep 个（视为主窗口）
        if not to_kill:
            continue
        freed_mb = sum(kb for _pid, kb in to_kill) / 1024.0
        plan.append({
            "name": name,
            "keep": keep,
            "kill_count": len(to_kill),
            "freed_mb": round(freed_mb, 1),
            "pids": [pid for pid, _kb in to_kill],
            "protected": name in NEVER_KILL,
        })
    plan.sort(key=lambda x: -x["freed_mb"])
    return plan


# ---------------------------------------------------------------- 输出层

ICON = {"GREEN": "[绿]", "YELLOW": "[黄]", "RED": "[红]"}


def render(result, plan=None, top=15):
    lines = []
    m = result["memory"]
    lines.append("=" * 66)
    lines.append("龙虾进程泄漏与内存健康守卫 v%s    %s" % (VERSION, result["ts"]))
    lines.append("=" * 66)
    lines.append("总评：%s %s" % (ICON.get(result["overall"], "?"), result["overall"]))
    lines.append("")
    lines.append("【内存】占用 %s%%  已用 %.2fGB / 共 %.2fGB  可用 %.2fGB  (页文件可用 %.2fGB)  -> %s" % (
        m.get("load_pct", "?"), m.get("used_gb", 0), m.get("total_gb", 0),
        m.get("avail_gb", 0), m.get("avail_pagefile_gb", 0), ICON.get(result["mem_level"], "?")))
    lines.append("【进程】总数 %d，种类 %d" % (result["process_total"], result["process_kinds"]))
    lines.append("")
    lines.append("--- 实例数最多的进程（泄漏嫌疑） ---")
    lines.append("%-6s %-7s %-10s %-9s %-8s %s" % ("等级", "实例", "总内存", "均值", "可清?", "进程名"))
    for g in result["groups"][:top]:
        if g["count"] < 3 and g["level"] == "GREEN":
            continue
        killable = "系统常驻" if g.get("system_noise") else ("是" if g["killable"] else "否(保护)")
        lines.append("%-6s %-7d %-10s %-9s %-8s %s" % (
            ICON.get(g["level"], "?"), g["count"],
            "%.1fMB" % g["total_mb"], "%.1fMB" % g["avg_mb"],
            killable, g["name"]))
        if g["level"] != "GREEN" and g["note"]:
            lines.append("        └ %s" % g["note"])
    if result["giants"]:
        lines.append("")
        lines.append("--- 单进程内存巨兽 (>=%.1fGB) ---" % SINGLE_PROC_GB_REPORT)
        for gi in result["giants"][:8]:
            lines.append("  %s %-22s PID %-8d %.2fGB" % (
                ICON.get(gi["level"], "?"), gi["name"], gi["pid"], gi["gb"]))
    if plan:
        lines.append("")
        lines.append("--- 清理计划（默认不执行，需 --apply --i-know-what-i-am-doing） ---")
        total = 0.0
        for p in plan:
            lines.append("  %-22s 杀 %3d 个 / 保留 %d 个   预计释放 %8.1fMB" % (
                p["name"], p["kill_count"], p["keep"], p["freed_mb"]))
            total += p["freed_mb"]
        lines.append("  合计预计释放：%.2f GB" % (total / 1024.0))
    elif result["overall"] == "RED":
        lines.append("")
        lines.append("  无可自动清理项（全部命中白名单），请人工在任务管理器中处理。")
    lines.append("=" * 66)
    return "\n".join(lines)


def write_kill_bat(plan, path):
    """写清理 bat。铁律：ASCII 注释 + 精确 CRLF（防「假成功第 1 形态」——bat 编码/行尾错会静默失效）。"""
    lines = ["@echo off",
             "rem generated by lobster_mem_guard v%s at %s" % (
                 VERSION, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             "rem keep the largest-memory instances (treated as main windows), kill the rest",
             ""]
    for p in plan:
        lines.append("rem %s : kill %d, keep %d, free ~%.1fMB" % (
            p["name"], p["kill_count"], p["keep"], p["freed_mb"]))
        for pid in p["pids"]:
            lines.append("taskkill /PID %d /T /F" % pid)
        lines.append("")
    lines.append("echo done.")
    with open(path, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write("\n".join(lines))
    return path


# ---------------------------------------------------------------- 趋势

def append_history(result):
    path = os.path.abspath(HISTORY_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec = {
        "ts": result["ts"],
        "load_pct": result["memory"].get("load_pct"),
        "avail_gb": result["memory"].get("avail_gb"),
        "proc_total": result["process_total"],
        "overall": result["overall"],
        "top": {g["name"]: g["count"] for g in result["groups"][:6]},
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def trend_summary(n=6):
    path = os.path.abspath(HISTORY_FILE)
    if not os.path.exists(path):
        return "无历史（首次运行）"
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    rows = rows[-n:]
    out = ["最近 %d 次采样：" % len(rows)]
    prev = None
    for r in rows:
        delta = ""
        if prev is not None and r.get("load_pct") is not None:
            d = r["load_pct"] - prev
            delta = "  (%+d%%)" % d
        out.append("  %s  load=%s%%  avail=%sGB  进程=%s  %s%s" % (
            r["ts"], r.get("load_pct"), r.get("avail_gb"), r.get("proc_total"),
            r.get("overall"), delta))
        prev = r.get("load_pct")
    if len(rows) >= 2:
        d = rows[-1].get("load_pct", 0) - rows[0].get("load_pct", 0)
        verdict = "上升（疑似泄漏累积）" if d > 5 else ("下降" if d < -5 else "平稳")
        out.append("  趋势：%+.0f%% -> %s" % (d, verdict))
    return "\n".join(out)


# ---------------------------------------------------------------- 执行

def do_apply(plan, dry=True):
    done, failed = [], []
    for p in plan:
        if p["protected"]:
            continue
        for pid in p["pids"]:
            if dry:
                done.append((p["name"], pid, "DRY-RUN"))
                continue
            try:
                r = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                   capture_output=True, timeout=30)
                (done if r.returncode == 0 else failed).append(
                    (p["name"], pid, r.returncode))
            except Exception as exc:                          # noqa: BLE001
                failed.append((p["name"], pid, str(exc)))
    return done, failed


def main():
    ap = argparse.ArgumentParser(description="龙虾进程泄漏与内存健康守卫 v%s" % VERSION)
    ap.add_argument("--json", action="store_true", help="输出 JSON（接 guard_receipt）")
    ap.add_argument("--plan", action="store_true", help="输出清理计划与可执行 bat（默认不执行）")
    ap.add_argument("--bat", metavar="PATH", help="指定清理 bat 落盘路径")
    ap.add_argument("--watch", metavar="N", type=int, default=0, help="采样次数")
    ap.add_argument("--interval", metavar="SEC", type=int, default=60, help="采样间隔秒")
    ap.add_argument("--apply", action="store_true", help="真正执行清理")
    ap.add_argument("--i-know-what-i-am-doing", dest="ikwid", action="store_true",
                    help="--apply 的双保险确认")
    ap.add_argument("--top", metavar="N", type=int, default=15, help="报告里列出的进程数")
    ap.add_argument("--trend", action="store_true", help="只看历史趋势")
    args = ap.parse_args()

    if args.trend:
        print(trend_summary())
        return 0

    rounds = max(1, args.watch)
    last = None
    for i in range(rounds):
        procs = list_processes()
        if not procs:
            sys.stderr.write("[fail] 进程采集为空，检查 tasklist 是否可用\n")
            return 2
        result = analyze(procs)
        plan = build_plan(result, procs)
        last = (result, plan, procs)
        append_history(result)
        if not args.json:
            print(render(result, plan, top=args.top))
            if rounds > 1:
                print("[watch %d/%d]" % (i + 1, rounds))
        if i < rounds - 1:
            time.sleep(args.interval)

    result, plan, procs = last
    if args.json:
        print(json.dumps({"result": result, "plan": plan}, ensure_ascii=False, indent=2))
        return 0

    if args.plan or args.apply:
        bat = args.bat or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "mem_guard_cleanup.bat")
        write_kill_bat(plan, bat)
        print("\n清理脚本已生成：%s" % bat)
        if args.apply:
            if not args.ikwid:
                print("[拒绝] --apply 必须同时给 --i-know-what-i-am-doing（防误杀双保险）")
                return 3
            done, failed = do_apply(plan, dry=False)
            print("已清理 %d 个进程，失败 %d 个" % (len(done), len(failed)))
            for f in failed[:20]:
                print("  [失败] %s PID %s -> %s" % f)
            after = analyze(list_processes())
            print("\n清理后复检：总评 %s，内存占用 %s%%，可用 %.2fGB，进程总数 %d" % (
                after["overall"], after["memory"].get("load_pct"),
                after["memory"].get("avail_gb", 0), after["process_total"]))
        else:
            print("（只读模式，未执行任何 kill。人工核对后自行运行该 bat，或加 --apply）")

    if rounds > 1:
        print("\n" + trend_summary())
    return 0 if result["overall"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
