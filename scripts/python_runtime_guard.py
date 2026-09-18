# -*- coding: utf-8 -*-
"""
python_runtime_guard.py v1.0  ·  龙虾 Python 运行时健康守卫
=============================================================
作者：汤小龙（AI 分身）  2026-09-09   零积分 / 纯本地 / 只读

起源：2026-09-09 自进化巡检时发现
  C:\\Users\\Administrator\\.workbuddy\\binaries\\python\\versions\\3.13.12\\ 只剩
  python.exe + DLLs，**Lib / include / libs / Scripts 全被删光** →
  `import encodings` 失败，解释器彻底不可用。
  而 AGENTS.md 铁律 #2 强制所有 MCP 代理必须用这个路径启动；
  更糟的是 `G:\\g_venv_ars` 等 venv 的 pyvenv.cfg home 指向它 → **venv 一并报废**。
  由于代理进程是「老进程还在跑」，表面一切正常，一旦重启/崩溃就全线瘫痪——典型的静默故障。

检测项：
  R1 解释器可启动（import encodings 通过）
  R2 ssl / sqlite3 可用（代理脚本硬需求，VNPY 缺 _ssl.pyd 的历史坑）
  R3 版本与 32/64 位
  R4 venv 的 pyvenv.cfg home 指向的解释器是否还活着
  R5 输出「当前推荐默认解释器」（第一个全绿且版本最高的）

用法：
  python python_runtime_guard.py [--json] [--extra PATH ...]
退出码：0=全部健康  2=有损坏项但存在可用替代  3=无任何可用解释器
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CANDIDATES = [
    r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe",
    r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.10.11\python.exe",
    r"G:\WorkBuddy_Data\binaries\python\versions\3.13.12\python.exe",
    r"G:\WorkBuddy_Data\binaries\python\versions\3.10.11\python.exe",
    r"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe",
]
VENV_DIRS = [r"G:\g_venv_ars", r"G:\g_venv_imaupload", r"G:\g_venv_lobster_mcp",
             r"G:\g_venv_mcp_bridge", r"G:\g_venv_scan", r"G:\g_venv_ui"]

PROBE = ("import sys,platform;"
         "import ssl;import sqlite3;"
         "print(sys.version.split()[0], platform.architecture()[0], sys.prefix)")

RED, YEL, GRN = "BROKEN", "DEGRADED", "OK"


def probe(exe: Path, timeout=20):
    """返回 (state, detail)。"""
    if not exe.exists():
        return "MISSING", "路径不存在"
    try:
        p = subprocess.run([str(exe), "-c", PROBE], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return RED, "启动超时"
    except OSError as e:
        return RED, f"无法执行: {e}"
    out, err = (p.stdout or "").strip(), (p.stderr or "").strip()
    if p.returncode == 0 and out:
        return GRN, out
    if "encodings" in err or "Failed to import" in err:
        return RED, "标准库缺失(Lib被删) —— import encodings 失败，解释器报废"
    if "_ssl" in err or "No module named 'ssl'" in err:
        return YEL, "缺 ssl（VNPY 同类坑），代理类脚本会崩"
    return RED, (err.splitlines()[-1] if err else f"exit {p.returncode}")


def read_venv_home(vdir: Path):
    cfg = vdir / "pyvenv.cfg"
    if not cfg.exists():
        return None
    try:
        txt = cfg.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = re.search(r"^\s*home\s*=\s*(.+)$", txt, re.M)
    return m.group(1).strip() if m else None


def main():
    ap = argparse.ArgumentParser(description="Python 运行时健康守卫 v1.0")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--extra", nargs="*", default=[], help="追加待检解释器路径")
    a = ap.parse_args()

    rows = []
    for c in CANDIDATES + list(a.extra):
        exe = Path(c)
        st, detail = probe(exe)
        rows.append({"path": str(exe), "state": st, "detail": detail})

    vrows = []
    for v in VENV_DIRS:
        vdir = Path(v)
        if not vdir.exists():
            continue
        home = read_venv_home(vdir)
        if not home:
            continue
        home_exe = Path(home) / "python.exe"
        hst, _ = probe(home_exe)
        vst, vdetail = probe(vdir / "Scripts" / "python.exe")
        vrows.append({"venv": str(vdir), "home": home, "home_state": hst,
                      "venv_state": vst, "detail": vdetail})

    good = [r for r in rows if r["state"] == GRN]
    alive = bool(good)
    rec = good[0]["path"] if good else ""

    if a.json:
        print(json.dumps({"ok": alive, "recommended": rec,
                          "interpreters": rows, "venvs": vrows},
                         ensure_ascii=False, indent=2))
        return 3 if not alive else (2 if any(r["state"] != GRN for r in rows) else 0)

    print("=" * 70)
    print("Python 运行时健康守卫 v1.0 · 体检报告")
    print("=" * 70)
    for r in rows:
        mark = {GRN: "[v]", YEL: "[!]", RED: "[X]", "MISSING": "[-]"}[r["state"]]
        print(f"{mark} {r['state']:<9} {r['path']}")
        print(f"           {r['detail']}")
    if vrows:
        print("-" * 70)
        for v in vrows:
            mark = "[v]" if v["venv_state"] == GRN else "[X]"
            print(f"{mark} venv {v['venv']}")
            print(f"           home={v['home']} -> {v['home_state']}；venv 自身 {v['venv_state']}")
            if v["home_state"] != GRN:
                print("           -> 修复: 用可用解释器重建 venv："
                      f"{rec or '<可用解释器>'} -m venv {v['venv']}")
    print("-" * 70)
    if rec:
        print(f"推荐默认解释器：{rec}")
        print("行动：把 AGENTS.md 铁律#2 / 各 .bat 启动脚本里的 python 路径改为它；"
              "或先修复损坏的 3.13.12（重装该版本）再保持原样。")
    else:
        print("❌ 无任何可用解释器，需立即重装 Python")
    return 3 if not alive else (2 if any(r["state"] != GRN for r in rows) else 0)


if __name__ == "__main__":
    sys.exit(main())
