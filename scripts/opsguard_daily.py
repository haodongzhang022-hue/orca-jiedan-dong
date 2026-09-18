#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
opsguard_daily.py v1.1 —— 龙虾零成本运维守卫「每日编排器」

v1.1 (2026-09-13)：接入 guard_receipt 状态回执
  原先本编排器只落日志、不落回执，守卫的守卫只能用「计划任务结果码」猜健康度。
  实测结果码分三类（真失败 / 调度器状态 0x4130x / GUI 退出码），只有第一类能判红，
  靠结果码判断 = 制造假故障。现改为同时落结构化回执，成为审计器的最强证据。

设计要点：
- 纯 Python 编排，**不写 .bat/.cmd** —— 绕开 Windows bat 的 GBK/CRLF 编码坑
  （bat 静默失败是「任务 Result=0 却没干活」的头号形态）。
- 串行跑子守卫，任一 FAIL 汇总到结尾，退出码透传给计划任务（非 0 即看得见）。
- 日志按天落盘，保留 30 天，绝不无限增长。
- 零积分：只调本地脚本，不联网调模型。

用法:
  python opsguard_daily.py              # 跑全部
  python opsguard_daily.py --only runtime
  python opsguard_daily.py --only remote
"""
import os
import subprocess
import sys
import time
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
sys.path.insert(0, HERE)
try:
    from guard_receipt import write_receipt
except Exception:                      # 回执模块缺失不许拖垮编排器本体
    write_receipt = None
LOG_DIR = r"E:\龙虾AI主控中心\MCP服务\logs"
REPOS = [
    r"G:\tmp\lobster-knowledge-base",
]
GITHUB_PROXY = "socks5://127.0.0.1:1081"
KEEP_DAYS = 30


def log(fh, s=""):
    print(s)
    try:
        fh.write(s + "\n")
        fh.flush()
    except Exception:
        pass


def run(fh, title, args, timeout=600):
    log(fh, "\n" + "=" * 60)
    log(fh, "### %s   %s" % (title, time.strftime("%H:%M:%S")))
    log(fh, "$ " + " ".join(args[1:]))
    log(fh, "=" * 60)
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           errors="ignore", cwd=os.path.dirname(HERE))
    except subprocess.TimeoutExpired:
        log(fh, "[FAIL] 子守卫超时 %ss" % timeout)
        return 3
    except Exception as e:
        log(fh, "[FAIL] 子守卫异常 %s" % type(e).__name__)
        return 4
    out = (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
    log(fh, out.rstrip())
    return r.returncode


def cleanup_old_logs(fh):
    try:
        now = time.time()
        for p in glob.glob(os.path.join(LOG_DIR, "opsguard_*.log")):
            if (now - os.path.getmtime(p)) > KEEP_DAYS * 86400:
                os.remove(p)
                log(fh, "[INFO] 清理旧日志 " + os.path.basename(p))
    except Exception:
        pass


def main():
    only = None
    if "--only" in sys.argv:
        i = sys.argv.index("--only")
        if i + 1 < len(sys.argv):
            only = sys.argv[i + 1]

    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "opsguard_%s.log" % time.strftime("%Y%m%d"))
    fh = open(path, "a", encoding="utf-8")
    log(fh, "\n\n########## 运维守卫日报 %s ##########" % time.strftime("%Y-%m-%d %H:%M:%S"))
    log(fh, "[INFO] 解释器: " + PY)

    codes = {}
    if only in (None, "runtime"):
        codes["runtime"] = run(fh, "Python 运行时守卫",
                               [PY, "-u", os.path.join(HERE, "python_runtime_guard.py")])
    if only in (None, "remote"):
        for repo in REPOS:
            if os.path.isdir(os.path.join(repo, ".git")):
                codes["remote"] = run(fh, "远端仓库诊断 " + repo,
                                      [PY, "-u", os.path.join(HERE, "remote_repo_doctor.py"),
                                       "--repo", repo, "--all", "--proxy", GITHUB_PROXY],
                                      timeout=900)

    cleanup_old_logs(fh)

    bad = {k: v for k, v in codes.items() if v not in (0,)}
    log(fh, "\n=== 汇总: " + ", ".join("%s=%d" % (k, v) for k, v in codes.items()) + " ===")
    log(fh, "=== 结论: " + ("有守卫报警 -> " + str(bad) if bad else "全绿") + " ===")
    log(fh, "[INFO] 日志: " + path)
    fh.close()

    rc = 3 if bad else 0
    if write_receipt:
        detail = "全绿 (%s)" % time.strftime("%H:%M:%S") if not bad \
            else "子守卫报警: %s" % bad
        p = write_receipt("opsguard_daily", healthy=not bad, detail=detail,
                          version="1.1", exit_code=rc,
                          extra={"codes": codes, "log": path})
        if p:
            print("[INFO] 状态回执 -> " + p)
    return rc


if __name__ == "__main__":
    sys.exit(main())
