#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
five_lib_dispatch.py  v2.0  (龙虾五库分发守卫 v2.0 · 龙虾零成本运维守卫 v1.7 组件)

v1.0 -> v2.0 变更（全部由实证驱动，非空想）：
  P0-A  目录健康探针 —— 「假成功」第 7 形态：存在性/可写性检查全绿，但 listdir 抛
        WinError 1392（2026-09-19 实测 G:\\tmp：8 项检查 6 项 OK、listdir/scandir 崩）。
        后果：TMP/TEMP 指向坏目录时，任何依赖列举的代码（glob/walk/rmtree/tempfile 清理）
        在运行中途炸，而前置门禁一路放行。v2.0 用 6 项探针判定 + 自动降级到健康临时目录。
  P0-B  CNB 现签令牌自动注入 —— 清掉长期挂起待办。~/.cnb/token 长令牌已死，
        唯一活凭据 = `cnb git-credential get` 现签 27 位短令牌。v2.0 三通道回退：
        A 令牌 URL 内嵌 → B 干净 URL + GIT_ASKPASS → C 环境注入 CNB_TOKEN，
        逐条实测并回报哪条通。
  P0-C  GitHub 通道自适应 —— v1.0 硬编码 socks5://127.0.0.1:1081，实测 1081 常 DOWN
        （2026-09-19 未监听）→ git 挂死。v2.0 先探 1081 LISTENING，再探 github.com:443
        直连窗口，按「代理 → 直连 → gh-proxy 镜像」三级自动选路，并全程清掉污染代理
        （全局 http.proxy=127.0.0.1:7897 在 7897 未监听时会让直连也失败）。
  P1-D  五端预检 --precheck：分发前先出绿/黄/红，避免推到一半才发现端不可达。
  P1-E  待补发队列 pending_queue.json：BLOCKED/FAIL 的端自动入队，授权后
        --retry-pending 一键补发。解决 IMA/乐享 连续多期阻断后无追踪、靠回忆补。

五端职责（诚实边界，不吹）：
  ① obsidian  本地文件系统  -> 全自动
  ④ cnb      git 推送      -> 全自动（门禁 + 通道回退 + ls-remote 回查）
  ⑤ github   git 推送      -> 全自动（通道自适应 + 连通窗口 + 回查）
  ② lexiang  乐享 MCP      -> 半自动：脚本出载荷 + 入队，MCP 调用由 Agent 执行
  ③ ima      IMA  MCP      -> 半自动：同上（推荐 import_urls 导乐享已发布页）

用法:
  python five_lib_dispatch.py --precheck
  python five_lib_dispatch.py --probe-tmp
  python five_lib_dispatch.py --all --src <技能目录> --repo <镜像仓> --title "标题"
  python five_lib_dispatch.py --target cnb|github|obsidian --repo <仓> [--branch main]
  python five_lib_dispatch.py --pending
  python five_lib_dispatch.py --retry-pending [--target cnb]
  python five_lib_dispatch.py --record-receipt lexiang --url <链接>
  python five_lib_dispatch.py --report

退出码: 0 = 全通或仅有已知阻断  2 = 有端 FAIL  4 = 参数错误
零积分：纯 stdlib，不调任何模型。
"""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DOCTOR = os.path.join(HERE, "remote_repo_doctor.py")
SAFE_PUSH = os.path.join(HERE, "git_mirror_safe_push.py")
RECEIPT_DIR = os.path.join(PROJECT, "待分发任务")

OBSIDIAN_LIB = r"G:\龙虾AI主控中心\Obsidian\技能库"
PY = sys.executable
CNB_ASKPASS = r"G:\WorkBuddy_Data\cnb_askpass.sh"
CNB_CLEAN_URL = "https://cnb.cool/TJF19770107/lobster-knowledge-base.git"

SKIP_DIRS = {".git", "__pycache__", ".idea", ".vscode", "node_modules", ".workbuddy"}

# 候选临时目录（按优先级）。G:\tmp 已实证损坏，但仍在 TMP 环境变量里，故必须探针判定。
TMP_CANDIDATES = [
    r"G:\WorkBuddy_Data\tmp",
    r"G:\temp",
    r"E:\temp",
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"),
]

_GOOD_TMP = {"path": None}


def log(tag, msg):
    print("[%s] %s" % (tag, msg), flush=True)


# ---------------------------------------------------------------- P0-A 目录健康
def probe_dir_health(path):
    """6 项探针。关键：只有 listdir/scandir 通过才算健康——
    存在性 + 可写性在损坏目录上是**假阳性**（假成功第 7 形态）。"""
    res = {}

    def t(name, fn):
        try:
            res[name] = (True, str(fn())[:60])
        except Exception as e:
            res[name] = (False, "%s: %s" % (type(e).__name__, str(e)[:70]))

    if not path:
        return {"healthy": False, "reason": "路径为空", "checks": res}
    t("exists", lambda: os.path.exists(path))
    t("isdir", lambda: os.path.isdir(path))
    t("writable", lambda: os.access(path, os.W_OK))
    if not res.get("isdir", (False,))[0]:
        try:
            os.makedirs(path, exist_ok=True)
            res["makedirs"] = (True, "created")
        except Exception as e:
            res["makedirs"] = (False, "%s: %s" % (type(e).__name__, str(e)[:70]))
    else:
        res["makedirs"] = (True, "exist_ok")
    f = os.path.join(path, "_lb5health_%d.tmp" % os.getpid())

    def _w():
        with open(f, "w") as fo:
            fo.write("x")
        os.remove(f)
        return "write+remove ok"

    t("write", _w)
    # 决定性探针：列举。损坏目录在这里才现行。
    t("listdir", lambda: len(os.listdir(path)))
    t("scandir", lambda: sum(1 for _ in os.scandir(path)))
    bad = [k for k, v in res.items() if not v[0]]
    return {"healthy": not bad, "failed": bad, "checks": res,
            "reason": ("列举探针失败(WinError 1392 类损坏): " + ",".join(bad)) if bad else "全绿"}


def pick_healthy_tmp(verbose=True):
    """选一个 6 项全绿的临时目录。返回路径（找不到返回 None）。"""
    if _GOOD_TMP["path"]:
        return _GOOD_TMP["path"]
    for cand in TMP_CANDIDATES:
        r = probe_dir_health(cand)
        if r["healthy"]:
            _GOOD_TMP["path"] = cand
            if verbose:
                log("TMP", "健康临时目录 -> %s" % cand)
            return cand
        if verbose:
            log("TMP", "不可用 %s -> %s" % (cand, r["reason"][:80]))
    return None


def current_tmp_report():
    """检查当前 TMP/TEMP 是否落在损坏目录上——这是最阴的隐性故障源。"""
    out = []
    for k in ("TMP", "TEMP"):
        v = os.environ.get(k)
        if not v:
            out.append((k, "(未设置)", "WARN", "无"))
            continue
        r = probe_dir_health(v)
        out.append((k, v, "OK" if r["healthy"] else "FAIL", r["reason"][:60]))
    return out


# ---------------------------------------------------------------- 子进程
def _env():
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run(cmd, cwd=None, timeout=180, env=None):
    """stdout 走临时文件不用管道（规避 GCM 孙进程持管道导致 timeout 失效）。
    v2.0：临时文件落在**探针确认健康**的目录，不再盲信 TMP。"""
    tmpdir = pick_healthy_tmp(verbose=False) or os.path.dirname(os.path.abspath(__file__))
    tmp = os.path.join(tmpdir, "_lb5_%d.tmp" % os.getpid())
    try:
        with open(tmp, "w", errors="ignore") as fo:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=fo, stderr=subprocess.STDOUT,
                                 text=True, env=env or _env())
            try:
                p.communicate(timeout=timeout)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                p.kill()
                try:
                    p.communicate(timeout=5)
                except Exception:
                    pass
                rc = -9
        with open(tmp, "r", errors="ignore") as fi:
            out = fi.read()
    except Exception as e:
        return 1, type(e).__name__ + " " + str(e)[:120]
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return rc, out


# ---------------------------------------------------------------- P0-B CNB 令牌
def _cnb_launchers():
    """cnb CLI 启动方式回退链。
    坑（2026-09-19 实测）：`cnb` 只是 Git Bash 的 423 字节 sh shim，
    Python subprocess 直接调 `cnb` -> FileNotFoundError（which 找得到，子进程找不到）。
    真实体是 node_modules/@cnbcool/cnb-cli/bin/cnb.js，必须用 node 直调。"""
    base = r"G:\WorkBuddy_Data\binaries\node\cli-connector-packages"
    js = os.path.join(base, "node_modules", "@cnbcool", "cnb-cli", "bin", "cnb.js")
    nodes = [r"C:\Program Files\nodejs\node.exe",
             r"G:\WorkBuddy_Data\binaries\node\versions\22.22.2-3\node.exe"]
    out = []
    if os.path.exists(js):
        for n in nodes:
            if os.path.exists(n):
                out.append(("node:" + os.path.basename(os.path.dirname(n)), [n, js]))
        out.append(("node:PATH", ["node", js]))
    out.append(("shim:cnb", ["cnb"]))
    out.append(("cmd:cnb.cmd", [os.path.join(base, "cnb.cmd")]))
    return out


def cnb_fresh_token():
    """调 cnb CLI 现签短令牌。返回 (username, password) 或 (None, None)。"""
    out, p = None, None
    used = ""
    for name, argv in _cnb_launchers():
        try:
            p = subprocess.Popen(argv + ["git-credential", "get"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, env=_env(),
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            out, _ = p.communicate("protocol=https\nhost=cnb.cool\n\n", timeout=90)
        except Exception as e:
            log("CNB", "启动方式 %s 不可用: %s" % (name, type(e).__name__))
            continue
        if p.returncode == 0 and out and "password=" in out:
            used = name
            break
        log("CNB", "启动方式 %s rc=%s: %s" % (name, p.returncode, (out or "").strip()[:100]))
    else:
        log("CNB", "全部启动方式失败，拿不到现签令牌")
        return None, None
    if used:
        log("CNB", "现签令牌获取成功（启动方式=%s）" % used)
    u = re.search(r"^username=(.+)$", out, re.M)
    w = re.search(r"^password=(.+)$", out, re.M)
    if not w:
        log("CNB", "返回体无 password 字段: %s" % out.strip()[:120])
        return None, None
    return (u.group(1).strip() if u else "cnb"), w.group(1).strip()


def cnb_channel(repo_url=None):
    """构造 CNB 三通道回退列表。返回 [(名称, git参数, env)]。"""
    url = repo_url or CNB_CLEAN_URL
    chans = []
    user, tok = cnb_fresh_token()
    if tok:
        # 通道 A：令牌 URL 内嵌（唯一实证可用）+ 清凭据助手 + 清代理
        if "://" in url:
            scheme, rest = url.split("://", 1)
            if "@" in rest:
                rest = rest.split("@", 1)[1]          # 剥掉旧凭据
            embed = "%s://%s:%s@%s" % (scheme, user or "cnb", tok, rest)
        else:
            embed = url
        env = _env()
        env.pop("CNB_TOKEN", None)
        env.pop("CNB_GIT_TOKEN", None)
        env["GIT_TERMINAL_PROMPT"] = "0"
        chans.append(("A-令牌内嵌", ["-c", "http.proxy=", "-c", "https.proxy=",
                                     "-c", "credential.helper="], embed, env))
    # 通道 B：干净 URL + GIT_ASKPASS（v1.0 老通道）
    env_b = _env()
    env_b.pop("CNB_TOKEN", None)
    if os.path.exists(CNB_ASKPASS):
        env_b["GIT_ASKPASS"] = CNB_ASKPASS
        env_b["GIT_TERMINAL_PROMPT"] = "1"
    chans.append(("B-askpass", ["-c", "http.proxy=", "-c", "https.proxy=",
                                "-c", "credential.helper="],
                  re.sub(r"://[^/@]*@", "://", url), env_b))
    # 通道 C：环境注入
    if tok:
        env_c = _env()
        env_c["GIT_ASKPASS"] = ""
        env_c["GIT_TERMINAL_PROMPT"] = "0"
        env_c["CNB_TOKEN"] = tok
        chans.append(("C-env注入", ["-c", "http.proxy=", "-c", "https.proxy=",
                                    "-c", "credential.helper="],
                      re.sub(r"://[^/@]*@", "://", url), env_c))
    return chans


# ---------------------------------------------------------------- P0-C GitHub 通道
def port_listening(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except Exception:
        return False


def tcp_window(host, port, tries=3, timeout=8):
    """测连通窗口：全通才返回 True（GFW 抖动时单次成功不可信）。"""
    ok = 0
    lat = []
    for _ in range(tries):
        t = time.time()
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            ok += 1
            lat.append(time.time() - t)
        except Exception:
            pass
    return ok == tries, (sum(lat) / len(lat) if lat else 0), ok


def github_channel():
    """三级选路：socks5 代理 → 直连 → gh-proxy 镜像。返回 (名称, git参数前缀, remote)。"""
    if port_listening(1081):
        ok, lat, n = tcp_window("github.com", 443, tries=2)
        log("NET", "1081 socks5 已监听，github.com:443 %d/2 通 (%.2fs)" % (n, lat))
        return ("socks5:1081", ["-c", "http.proxy=socks5://127.0.0.1:1081",
                                "-c", "https.proxy=socks5://127.0.0.1:1081"], "direct")
    ok, lat, n = tcp_window("github.com", 443, tries=3)
    if ok:
        # 关键：全局 http.proxy=127.0.0.1:7897 在 7897 DOWN 时会让「直连」也失败，必须清空
        log("NET", "1081 未监听；github.com:443 直连 3/3 通 (%.2fs) -> 走直连并清代理" % lat)
        return ("直连+清代理", ["-c", "http.proxy=", "-c", "https.proxy="], "direct")
    ok2, lat2, n2 = tcp_window("gh-proxy.com", 443, tries=3)
    if ok2:
        log("NET", "直连不通；gh-proxy.com:443 %d/3 通 (%.2fs) -> 走镜像" % (n2, lat2))
        return ("gh-proxy镜像", ["-c", "http.proxy=", "-c", "https.proxy="], "github")
    return ("全断", ["-c", "http.proxy=", "-c", "https.proxy="], "direct")


# ---------------------------------------------------------------- ① Obsidian
def dispatch_obsidian(src, report):
    if not src or not os.path.isdir(src):
        report("obsidian", "SKIP", "未指定 --src 或目录不存在: %s" % src)
        return
    h = probe_dir_health(OBSIDIAN_LIB)
    if not h["healthy"]:
        report("obsidian", "FAIL", "目标库不健康: %s -> %s" % (OBSIDIAN_LIB, h["reason"]))
        return
    name = os.path.basename(os.path.normpath(src))
    dst = os.path.join(OBSIDIAN_LIB, name)
    os.makedirs(dst, exist_ok=True)
    copied = skipped = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, src)
        tgt = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            if f.endswith((".pyc", ".tmp")):
                skipped += 1
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(tgt, f))
            copied += 1
    # 回读核实：落盘≠成功，必须列得出来
    got = 0
    try:
        for root, dirs, files in os.walk(dst):
            got += len([f for f in files if not f.endswith((".pyc", ".tmp"))])
    except Exception as e:
        report("obsidian", "FAIL", "落盘后回读失败: %s" % e)
        return
    report("obsidian", "OK" if got >= copied else "FAIL",
           "%s -> %s（复制 %d，回读 %d，跳过 %d）" % (name, dst, copied, got, skipped))


# ---------------------------------------------------------------- 门禁
def doctor_gate(repo, remote):
    if not os.path.exists(DOCTOR):
        return True, "诊断器缺失，跳过门禁"
    rc, out = run([PY, "-u", DOCTOR, "--repo", repo, "--remote", remote], timeout=120)
    m = re.search(r"\[(OK|FAIL|WARN)\]\s+IDN01\s+(.*)", out)
    if m and m.group(1) == "FAIL":
        return False, "令牌失效（身份探针 401）：%s" % m.group(2).strip()[:90]
    if rc == 0:
        return True, "诊断通过（身份探针 200 + ls-remote 可达）"
    return True, "门禁弱通过（rc=%d，无令牌失效证据），继续实测推送" % rc


# ---------------------------------------------------------------- 待补发队列
def queue_path():
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    return os.path.join(RECEIPT_DIR, "pending_queue.json")


def enqueue(target, title, src, reason):
    p = queue_path()
    data = {}
    if os.path.exists(p):
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("items", [])
    data["items"] = [i for i in data["items"]
                     if not (i.get("target") == target and i.get("title") == title)]
    data["items"].append({"target": target, "title": title, "src": src,
                          "reason": reason[:200], "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                          "status": "pending"})
    data["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log("QUEUE", "%s 已入待补发队列（%s）" % (target, reason[:60]))
    return p


def dequeue(target):
    p = queue_path()
    if not os.path.exists(p):
        return []
    try:
        data = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    items = data.get("items", [])
    if target:
        items = [i for i in items if i.get("target") == target]
    return [i for i in items if i.get("status") == "pending"]


def mark_done(target, title):
    p = queue_path()
    if not os.path.exists(p):
        return
    data = json.load(open(p, encoding="utf-8"))
    for i in data.get("items", []):
        if i.get("target") == target and i.get("title") == title:
            i["status"] = "done"
            i["done_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def show_pending():
    p = queue_path()
    if not os.path.exists(p):
        print("无待补发队列")
        return 0
    data = json.load(open(p, encoding="utf-8"))
    items = [i for i in data.get("items", []) if i.get("status") == "pending"]
    if not items:
        print("待补发队列已清空（更新于 %s）" % data.get("updated"))
        return 0
    print("=== 待补发队列 %d 项 ===" % len(items))
    for i in items:
        print("  [%-8s] %-28s %s  | %s" % (i.get("target"), i.get("title"),
                                           i.get("at"), (i.get("reason") or "")[:60]))
    return 0


# ---------------------------------------------------------------- ④⑤ git 端
def dispatch_git(target, repo, branch, report, do_push=True, title="五库分发", only=None,
                 dry_run=False):
    if not repo or not os.path.isdir(os.path.join(repo, ".git")):
        report(target, "SKIP", "仓库不存在: %s" % repo)
        return
    h = probe_dir_health(repo)
    if not h["healthy"]:
        report(target, "FAIL", "仓库目录不健康: %s" % h["reason"])
        enqueue(target, title, repo, "仓库目录不健康: " + h["reason"])
        return

    if target == "github":
        ch_name, ch_args, remote = github_channel()
        if ch_name == "全断":
            report(target, "BLOCKED", "github.com 与 gh-proxy.com 443 均不通 -> 已入队，未挂起")
            enqueue(target, title, repo, "网络全断")
            return
    else:
        ch_args = ["-c", "http.proxy=", "-c", "https.proxy=", "-c", "credential.helper="]
        remote = None

    ok, why = doctor_gate(repo, target if target != "github" else remote)
    if not ok:
        report(target, "BLOCKED", why + " -> 已跳过推送（未挂起）。处置：重签令牌后复跑")
        enqueue(target, title, repo, why)
        return
    log("GATE", "%s %s" % (target, why[:110]))

    rc, out = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, timeout=30)
    cur = out.strip()
    if cur != branch:
        report(target, "SKIP", "当前分支 %s ≠ 目标 %s，不擅自切分支" % (cur, branch))
        return

    # 坑：core.quotepath=true 会把中文路径转成八进制，直接 add 会「路径不存在」
    # -> 暂存为空 -> commit rc=1 -> push 什么都没推，而回查两边都是旧 HEAD -> 误报成功
    rc, out = run(["git", "-c", "core.quotepath=false", "status", "--porcelain"],
                  cwd=repo, timeout=60)
    dirty = [l for l in out.splitlines() if l.strip()]
    # 安全闸门：仓库里常有上百个 untracked 订单目录，默认全量 add 会一次性推走全部。
    # --only 用路径前缀白名单收敛范围；不给就只放行「已跟踪文件的修改」，不碰 untracked。
    if only:
        pre = [p.strip().replace("\\", "/") for p in only.split(",") if p.strip()]
        dirty = [l for l in dirty
                 if any(l[3:].strip().strip('"').replace("\\", "/").startswith(p) for p in pre)]
        log("GIT", "--only 白名单收敛: %d 项（前缀 %s）" % (len(dirty), ",".join(pre)))
    else:
        untracked = [l for l in dirty if l.startswith("??")]
        if untracked:
            log("GIT", "⚠ 有 %d 个 untracked 未纳入（安全闸门）；如需提交请显式 --only <路径前缀>"
                % len(untracked))
            dirty = [l for l in dirty if not l.startswith("??")]
    head_before = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo, timeout=30)[1].strip()
    made_commit = False
    if dirty and dry_run:
        # 真·干跑：连 commit 都不做。
        # 坑（2026-09-19 实测）：原 --no-push 只挡 push 不挡 commit，
        # 「干跑」照样把 HEAD 从 3b81dae 推到 4ed6ab2 —— 名为演练实为落子。
        log("GIT", "--dry-run：跳过 commit（本应提交 %d 项: %s）"
            % (len(dirty), dirty[0][3:][:60]))
        dirty = []
    if dirty:
        paths = sorted({l[3:].strip().strip('"').split(" -> ")[-1] for l in dirty})
        # 只 add 具体路径，绝不 add -A（假删除 3652 文件险情）
        rc, out = run(["git", "add", "--"] + paths, cwd=repo, timeout=120)
        if rc != 0:
            report(target, "FAIL", "git add 失败 rc=%d: %s" % (rc, out.strip()[-160:]))
            enqueue(target, title, repo, "git add 失败 rc=%d" % rc)
            return
        rc, out = run(["git", "commit", "-m", "五库分发: %s" % time.strftime("%Y-%m-%d %H:%M")],
                      cwd=repo, timeout=120)
        if rc != 0:
            report(target, "FAIL", "commit 失败 rc=%d: %s" % (rc, out.strip()[-200:]))
            enqueue(target, title, repo, "commit 失败 rc=%d" % rc)
            return
        made_commit = True
        _, out2 = run(["git", "-c", "core.quotepath=false", "status", "--porcelain"],
                      cwd=repo, timeout=60)
        # 只核对「本次纳入范围」的条目；被安全闸门主动排除的 untracked 不算失败，
        # 否则会像 2026-09-19 首跑那样把 139 个主动排除项误报成 FAIL。
        want = set(paths)
        rest = [l for l in out2.splitlines()
                if l.strip() and l[3:].strip().strip('"') in want]
        if rest:
            report(target, "FAIL", "commit 后仍有 %d 项未入库: %s" % (len(rest), rest[0][:80]))
            enqueue(target, title, repo, "commit 后残留 %d 项" % len(rest))
            return
        log("GIT", "commit ok (%d 项)" % len(paths))
    else:
        log("GIT", "工作区干净，无需 commit")

    head = run(["git", "rev-parse", "--short", "HEAD"], cwd=repo, timeout=30)[1].strip()
    if not do_push:
        report(target, "OK", "门禁通过（未推送 --no-push/--dry-run），HEAD=%s" % head)
        return

    if target == "cnb":
        # 目标 URL 必须从**仓库自己的远端**解析，不能用全局常量。
        # 坑（2026-09-19 血案）：硬编码 CNB_CLEAN_URL(lobster-knowledge-base) 时，
        # 拿接单项目仓库跑分发 → 把项目提交推到了知识库仓，凭空多出一个 main 分支。
        _, rurl = run(["git", "remote", "get-url", "origin"], cwd=repo, timeout=30)
        rurl = rurl.strip()
        if not rurl:
            report(target, "FAIL", "仓库 %s 无 origin 远端，拒绝盲推" % repo)
            enqueue(target, title, repo, "无 origin 远端")
            return
        log("CNB", "目标远端取自仓库 origin = %s" % re.sub(r"://[^/@]*@", "://", rurl))
        # 三通道回退：逐条实测，谁通谁上
        last = ""
        for name, args, push_url, penv in cnb_channel(rurl):
            rc, out = run(["git"] + args + ["push", push_url, branch],
                          cwd=repo, timeout=300, env=penv)
            last = out.strip()[-200:]
            if rc == 0:
                log("CNB", "通道 %s 推送成功" % name)
                break
            log("CNB", "通道 %s 失败 rc=%d，换下一条" % (name, rc))
        else:
            report(target, "FAIL", "CNB 三通道全失败: %s" % last)
            enqueue(target, title, repo, "CNB 三通道全失败")
            return
        vcmd = ["git"] + ["-c", "http.proxy=", "-c", "https.proxy=",
                          "-c", "credential.helper="] + \
               ["ls-remote", re.sub(r"://[^/@]*@", "://", rurl), "refs/heads/" + branch]
        venv = _env()
        venv.pop("CNB_TOKEN", None)
    else:
        rc, out = run(["git"] + ch_args + ["push", remote, branch], cwd=repo, timeout=600)
        if rc != 0:
            report(target, "FAIL", "push rc=%d（通道=%s）: %s" % (rc, ch_name, out.strip()[-200:]))
            enqueue(target, title, repo, "push 失败 通道=%s rc=%d" % (ch_name, rc))
            return
        log("GIT", "GitHub 推送通道 = %s" % ch_name)
        vcmd = ["git"] + ch_args + ["ls-remote", remote, "refs/heads/" + branch]
        venv = None

    rc2, out2 = run(vcmd, cwd=repo, timeout=180, env=venv)
    remote_sha = out2.split()[0][:len(head)] if out2.split() else ""
    # 假成功防线：commit 没做成就 push，回查当然「一致」，因为两边都还是旧 HEAD
    if remote_sha == head:
        if dirty and head == head_before:
            report(target, "FAIL", "回查一致但 HEAD 未前进（%s）——有改动却没提交成功，"
                                   "假成功第 4 形态" % head)
            enqueue(target, title, repo, "HEAD 未前进的假成功")
        elif made_commit:
            report(target, "OK", "推送成功，ls-remote 回查一致 HEAD=%s（%s→%s）"
                   % (head, head_before, head))
            mark_done(target, title)
        else:
            report(target, "OK", "推送完成，远端已同步 HEAD=%s（本轮无新增提交）" % head)
            mark_done(target, title)
    else:
        report(target, "FAIL", "push 返回 0 但回查不一致(本地=%s 远端=%s)"
               % (head, remote_sha or "空"))
        enqueue(target, title, repo, "回查不一致")


# ---------------------------------------------------------------- ②③ MCP 端
def record_receipt(target, url, report=None):
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    path = os.path.join(RECEIPT_DIR, "五库分发回执_%s.json" % time.strftime("%Y%m%d"))
    data = {}
    if os.path.exists(path):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            data = {}
    data.setdefault("date", time.strftime("%Y-%m-%d"))
    data[target] = {"url": url, "at": time.strftime("%H:%M:%S")}
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    log("RECEIPT", "%s -> %s" % (target, url))
    mark_done(target, data.get("title", "五库分发"))
    return path


def prepare_payload(title, src, report):
    os.makedirs(RECEIPT_DIR, exist_ok=True)
    payload = {"title": title, "source": src, "generated": time.strftime("%Y-%m-%d %H:%M:%S")}
    if src and os.path.isdir(src):
        try:
            payload["skill_files"] = [f for f in os.listdir(src) if f.upper().endswith(".MD")]
        except Exception as e:
            payload["skill_files"] = "列举失败: %s" % e
    p = os.path.join(RECEIPT_DIR, "五库分发载荷_%s.json" % time.strftime("%Y%m%d"))
    json.dump(payload, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    report("payload", "OK", "MCP 端载荷已生成 %s" % p)
    return p


# ---------------------------------------------------------------- 预检
def precheck(repo=None):
    print("=== 五库分发预检 %s ===\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    rows = []

    # 0. 临时目录（假成功第7形态高发区）
    for k, v, st, why in current_tmp_report():
        rows.append(("临时目录 %s" % k, st, "%s %s" % (v, why)))
    good = pick_healthy_tmp(verbose=False)
    rows.append(("健康临时目录", "OK" if good else "FAIL", good or "无可用候选"))

    # 1. Obsidian
    h = probe_dir_health(OBSIDIAN_LIB)
    rows.append(("① Obsidian", "OK" if h["healthy"] else "FAIL", "%s %s" % (OBSIDIAN_LIB, h["reason"])))

    # 2/3. MCP 端：脚本无法自证，只能看回执与环境变量
    for tgt, envk in (("② 乐享 lexiang", "LEXIANG_TOKEN"), ("③ IMA", "IMA_TOKEN")):
        v = os.environ.get(envk)
        rows.append((tgt, "OK" if v else "WARN",
                     "环境变量 %s %s（MCP 挂载需 Agent 侧确认）" % (envk, "已设置" if v else "未设置")))

    # 4. CNB
    u, tok = cnb_fresh_token()
    rows.append(("④ CNB", "OK" if tok else "FAIL",
                 "现签短令牌 %s（长度 %d）" % ("可用" if tok else "不可用", len(tok or ""))))
    rows.append(("④ CNB askpass", "OK" if os.path.exists(CNB_ASKPASS) else "WARN",
                 CNB_ASKPASS if os.path.exists(CNB_ASKPASS) else "缺失，通道B 不可用"))

    # 5. GitHub
    name, _, remote = github_channel()
    rows.append(("⑤ GitHub", "OK" if name != "全断" else "FAIL", "选路=%s remote=%s" % (name, remote)))
    for p in (1081, 7897):
        rows.append(("   端口 %d" % p, "OK" if port_listening(p) else "WARN",
                     "LISTENING" if port_listening(p) else "未监听"))

    # 仓库
    if repo:
        h2 = probe_dir_health(repo)
        rows.append(("镜像仓", "OK" if h2["healthy"] else "FAIL", "%s %s" % (repo, h2["reason"])))

    for t, s, m in rows:
        mark = {"OK": "🟢", "WARN": "🟡", "FAIL": "🔴"}.get(s, "•")
        print("  %s %-18s %-6s %s" % (mark, t, s, m))
    nfail = sum(1 for r in rows if r[1] == "FAIL")
    nwarn = sum(1 for r in rows if r[1] == "WARN")
    print("\n  合计: 绿=%d 黄=%d 红=%d" % (len(rows) - nfail - nwarn, nwarn, nfail))
    pend = dequeue(None)
    if pend:
        print("  待补发: %d 项 -> %s" % (len(pend), ",".join(sorted({i['target'] for i in pend}))))
    return 2 if nfail else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--target", choices=["obsidian", "lexiang", "ima", "cnb", "github", "payload"])
    ap.add_argument("--src", help="技能目录（Obsidian 落盘源）")
    ap.add_argument("--repo", help="镜像仓路径")
    ap.add_argument("--branch", default="fresh-main")
    ap.add_argument("--title", default="五库分发")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--only", help="只提交这些路径前缀（逗号分隔）；不给则只放行已跟踪修改，不碰 untracked")
    ap.add_argument("--dry-run", action="store_true", help="真干跑：不 commit 不 push（--no-push 仍会 commit）")
    ap.add_argument("--record-receipt", metavar="TARGET")
    ap.add_argument("--url", help="回执 URL")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--precheck", action="store_true")
    ap.add_argument("--probe-tmp", action="store_true")
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--retry-pending", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    results = []

    def report(target, status, msg):
        results.append((target, status, msg))
        mark = {"OK": "✅", "SKIP": "⏸", "BLOCKED": "⛔", "FAIL": "❌"}.get(status, "•")
        log(mark, "%-9s %s" % (target, msg))

    if a.probe_tmp:
        for k, v, st, why in current_tmp_report():
            print("  %-6s %-8s %-30s %s" % (k, st, v, why))
        print("  候选:")
        for c in TMP_CANDIDATES:
            r = probe_dir_health(c)
            print("    %-6s %-40s %s" % ("OK" if r["healthy"] else "BAD", c, r["reason"][:70]))
        print("  选定: %s" % pick_healthy_tmp(verbose=False))
        return 0
    if a.pending:
        return show_pending()
    if a.precheck:
        return precheck(a.repo)
    if a.status:
        return precheck(a.repo)
    if a.report:
        p = os.path.join(RECEIPT_DIR, "五库分发回执_%s.json" % time.strftime("%Y%m%d"))
        print(open(p, encoding="utf-8").read() if os.path.exists(p) else "今日无回执: %s" % p)
        return 0
    if a.record_receipt:
        record_receipt(a.record_receipt, a.url or "", report)
        return 0

    if a.retry_pending:
        items = dequeue(a.target)
        if not items:
            print("待补发队列为空，无需补发")
            return 0
        print("=== 补发 %d 项 ===" % len(items))
        for i in items:
            if i["target"] in ("cnb", "github"):
                dispatch_git(i["target"], i.get("src"), a.branch, report,
                             not (a.no_push or a.dry_run), i.get("title", "五库分发"), a.only, a.dry_run)
            elif i["target"] == "obsidian":
                dispatch_obsidian(i.get("src"), report)
            else:
                log("INFO", "%s 为 MCP 端，需 Agent 调用 MCP 后 "
                            "--record-receipt %s --url <链接>" % (i["target"], i["target"]))
        print("\n=== 补发报告 ===")
        for t, s, m in results:
            print("  %-9s %-8s %s" % (t, s, m))
        return 2 if any(r[1] == "FAIL" for r in results) else 0

    if a.all or a.target == "payload":
        prepare_payload(a.title, a.src, report)
    if a.all or a.target == "obsidian":
        dispatch_obsidian(a.src, report)
    if a.all or a.target == "cnb":
        dispatch_git("cnb", a.repo, a.branch, report, not (a.no_push or a.dry_run), a.title, a.only, a.dry_run)
    if a.all or a.target == "github":
        dispatch_git("github", a.repo, a.branch, report, not (a.no_push or a.dry_run), a.title,
                     a.only, a.dry_run)
    if a.target in ("lexiang", "ima"):
        log("INFO", "%s 为 MCP 端：Agent 调用 MCP 后用 --record-receipt %s --url <链接> 记录回执"
            % (a.target, a.target))
        enqueue(a.target, a.title, a.src or "", "MCP 端待 Agent 调用后回执")

    print("\n=== 五库分发报告 %s ===" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for t, s, m in results:
        print("  %-9s %-8s %s" % (t, s, m))
    print("  合计: OK=%d SKIP=%d BLOCKED=%d FAIL=%d"
          % (sum(1 for r in results if r[1] == "OK"),
             sum(1 for r in results if r[1] == "SKIP"),
             sum(1 for r in results if r[1] == "BLOCKED"),
             sum(1 for r in results if r[1] == "FAIL")))
    pend = dequeue(None)
    if pend:
        print("  ⚠ 待补发 %d 项: %s" % (len(pend), ",".join(sorted({i["target"] for i in pend}))))
    return 2 if any(r[1] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
