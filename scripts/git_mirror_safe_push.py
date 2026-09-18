# -*- coding: utf-8 -*-
"""
git_mirror_safe_push.py v1.1  ·  龙虾 Git 多端镜像仓安全推送守卫
================================================================
作者：汤小龙（AI 分身）  首次生成：2026-09-09  许可：内部自用 / 可随技能包分发
定位：零积分、纯本地、只读优先。推送前做 12 项预检，命中阻断项即退出，绝不 `git add -A`。

起源（2026-09-09 真实事故）：
  并发会话同时向同一远端推送 → 本地旧克隆 rebase 后 `git status` 出现 3652 个 D（删除）条目
  → 险些 `git add -A` 提交一个「107 万行删除」的 commit，push 被拦才止损。
  本脚本把这次血泪固化成可复用的熔断规则。

用法：
  python git_mirror_safe_push.py --repo <PATH> [--remote origin] [--branch main]
                                 [--execute] [--json] [--allow-delete N]
  默认只体检不推送；加 --execute 才真正 push（且必须全绿）。

退出码：0=可推送  2=有 P1 警告但可推（需 --force-ignore 才推）  3=P0 阻断  4=参数/环境错误
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BLOCK, WARN, OK = "BLOCK", "WARN", "OK"

# ---- 红线：这些路径/模式一旦进入暂存区直接阻断 ----
RED_PATH_PAT = [
    r"(^|/)\.workbuddy/",      # 本地日志/记忆，禁进 git 与四端
    r"(^|/)\.env($|\.)",
    r"(^|/)\.codex/",
    r"(^|/)credentials?\.json$",
    r"(^|/).*\.pem$",
    r"(^|/).*\.pfx$",
    r"(^|/).*(secret|token|apikey|api_key).*\.(txt|json|ya?ml|md)$",
]
# 内容级密钥特征（只扫暂存区文本文件，<=200KB）
SECRET_CONTENT_PAT = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"cnb_at_[A-Za-z0-9_\-\.]{20,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]
BIG_FILE_BYTES = 20 * 1024 * 1024          # 轻量快照约束：单仓/单文件 < 20MB
DEFAULT_DELETE_CAP = 20                    # 暂存区删除条目熔断阈值


def sh(args, cwd=None, timeout=60):
    """统一 subprocess，避免 shell=True 与编码坑。"""
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "git not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, code, msg, fix=""):
        self.items.append({"level": level, "code": code, "msg": msg, "fix": fix})

    @property
    def blocked(self):
        return any(i["level"] == BLOCK for i in self.items)

    @property
    def warned(self):
        return any(i["level"] == WARN for i in self.items)

    def dump(self, as_json=False):
        if as_json:
            print(json.dumps({"blocked": self.blocked, "warned": self.warned,
                              "items": self.items}, ensure_ascii=False, indent=2))
            return
        icon = {BLOCK: "[X]", WARN: "[!]", OK: "[v]"}
        print("=" * 68)
        print("Git 多端镜像仓安全推送守卫 v1.1  ·  体检报告")
        print("=" * 68)
        for i in self.items:
            print(f"{icon[i['level']]} {i['code']:<10} {i['msg']}")
            if i["fix"]:
                print(f"            -> 修复: {i['fix']}")
        print("-" * 68)
        print("结论：" + ("阻断，禁止推送" if self.blocked else
                       ("有警告，建议处理后推送" if self.warned else "全绿，可推送")))


def mask(text):
    """脱敏：remote URL / 报错里的 token 一律打码，绝不落盘明文。"""
    return re.sub(r"://([^:/@\s]+):([^@\s]+)@", r"://\1:***@", text)


def check(repo: Path, remote: str, branch: str, delete_cap: int) -> Report:
    r = Report()
    if not (repo / ".git").exists():
        r.add(BLOCK, "GIT00", f"不是 git 仓库: {repo}")
        return r
    if sh(["git", "--version"])[0] != 0:
        r.add(BLOCK, "GIT00", "git 不可用")
        return r

    # --- 1. 仓库状态：detached / rebase / merge ---
    rc, head, _ = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    detached = (head == "HEAD")
    gitdir = sh(["git", "rev-parse", "--git-dir"], cwd=repo)[1]
    gitdir_p = Path(gitdir) if os.path.isabs(gitdir) else (repo / gitdir)
    for flag, name in [("rebase-merge", "rebase"), ("rebase-apply", "rebase/am"),
                       ("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick")]:
        if (gitdir_p / flag).exists():
            r.add(BLOCK, "GIT01", f"仓库处于 {name} 中间态，push 语义会错乱",
                  f"先完成或中止：git {name} --continue / --abort")
    if detached:
        r.add(WARN, "GIT02", "HEAD 处于 detached 状态",
              f"推送必须显式：git push {remote} HEAD:{branch}")
    else:
        r.add(OK, "GIT02", f"当前分支 {head}")
        if branch and head != branch:
            r.add(WARN, "GIT02b", f"当前分支 {head} 与指定分支 {branch} 不一致",
                  f"确认是否该先 git checkout {branch}")

    # --- 2. 远端与代理 ---
    rc, url, err = sh(["git", "remote", "get-url", remote], cwd=repo)
    if rc != 0:
        r.add(BLOCK, "GIT03", f"远端 {remote} 不存在", f"git remote add {remote} <url>")
    else:
        if re.search(r"://[^:/@\s]+:[^@\s]+@", url):
            r.add(BLOCK, "SEC01", "远端 URL 内嵌明文口令（会随 git remote -v / 日志泄漏）",
                  "改存凭据：git credential approve 或 git config credential.helper store，"
                  f"再 git remote set-url {remote} <纯https地址>")
        r.add(OK, "GIT03", f"远端 {remote} = {mask(url)}")
    for scope in ["--local", "--global"]:
        rc, proxy, _ = sh(["git", "config", scope, "--get", "http.proxy"], cwd=repo)
        if rc == 0 and proxy:
            r.add(WARN, "GIT04", f"{scope} 设置了 http.proxy={mask(proxy)}（CNB/国内仓常被拦）",
                  f"推送时清代理：git -c http.proxy= -c https.proxy= push {remote} {branch}")

    # --- 3. 工作区 / 暂存区扫描（假删除熔断核心）---
    rc, porcelain, _ = sh(["git", "status", "--porcelain", "-z"], cwd=repo)
    entries = [e for e in porcelain.split("\0") if e.strip()]
    staged_d, unstaged_d, untracked, modified = [], [], [], []
    for e in entries:
        xy, path = e[:2], e[3:]
        x, y = xy[0], xy[1]
        if x == "D":
            staged_d.append(path)
        if y == "D":
            unstaged_d.append(path)
        if xy == "??":
            untracked.append(path)
        if x in "MRCA" or y == "M":   # A=新增也必须纳入红线/密钥扫描（v1.1 修复漏检）
            modified.append(path)

    if len(staged_d) >= delete_cap:
        rc2, numstat, _ = sh(["git", "diff", "--cached", "--numstat"], cwd=repo)
        del_lines = sum(int(l.split("\t")[1]) for l in numstat.splitlines()
                        if len(l.split("\t")) >= 2 and l.split("\t")[1].isdigit())
        r.add(BLOCK, "DEL01",
              f"暂存区含 {len(staged_d)} 个删除条目（阈值 {delete_cap}），"
              f"累计删除 {del_lines} 行 —— 高度疑似「旧克隆落后远端」产生的假删除",
              "立刻 git reset --hard <正确commit> 丢弃；确认后再 git fetch && "
              f"git rebase {remote}/{branch}，且禁止 git add -A")
    elif staged_d:
        r.add(WARN, "DEL02", f"暂存区含 {len(staged_d)} 个删除条目（未达熔断阈值）",
              "逐个确认是真实删除：git diff --cached --stat | head -50")
    if unstaged_d:
        r.add(WARN, "DEL03", f"工作区有 {len(unstaged_d)} 个未暂存删除（push 不影响，但先确认）")

    # --- 4. 红线路径 / 密钥内容 / 大文件 ---
    scan = staged_d + modified + untracked
    hit_red = [p for p in scan if any(re.search(pat, p) for pat in RED_PATH_PAT)]
    if hit_red:
        r.add(BLOCK, "SEC02", f"{len(hit_red)} 个红线文件在变更列表：{hit_red[:3]}",
              "写入 .gitignore（.workbuddy/ / .env / .codex/），"
              "若已跟踪则 git rm --cached <f> 保留磁盘")
    else:
        r.add(OK, "SEC02", f"扫描 {len(scan)} 个变更路径，无红线路径")

    rc, staged_files, _ = sh(["git", "diff", "--cached", "--name-only"], cwd=repo)
    leaked = []
    for f in [x for x in staged_files.splitlines() if x.strip()]:
        fp = repo / f
        if not fp.exists() or fp.stat().st_size > 200 * 1024:
            continue
        try:
            txt = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in SECRET_CONTENT_PAT:
            if pat.search(txt):
                leaked.append(f)
                break
        if fp.stat().st_size > BIG_FILE_BYTES:
            r.add(BLOCK, "BIG01", f"{f} 超过 20MB（{fp.stat().st_size//1024//1024}MB）",
                  "大附件走 G盘/网盘，git 只管文本")
    if leaked:
        r.add(BLOCK, "SEC03", f"暂存文件疑似含明文密钥：{leaked[:3]}",
              "脱敏后再提交；sk-/token/secret 禁入任何可同步产物")

    # --- 5. 与远端的领先/落后（分叉是假删除的母亲）---
    rc, ahead_behind, _ = sh(["git", "rev-list", "--left-right", "--count",
                              f"HEAD...{remote}/{branch}"], cwd=repo)
    if rc == 0 and ahead_behind:
        try:
            a, b = [int(x) for x in ahead_behind.split()]
            r.add(OK if b == 0 else WARN, "SYNC01",
                  f"本地领先 {a} 个 commit，落后远端 {b} 个",
                  f"落后>0 必须先 git fetch {remote} {branch} && git rebase，再重跑本守卫")
        except ValueError:
            pass
    else:
        r.add(WARN, "SYNC01", f"无法比对 {remote}/{branch}（远端引用缺失）",
              f"先 git fetch {remote} {branch}；注意 fetch 带显式 refspec 只更新 FETCH_HEAD，"
              f"要更新引用请用 git fetch {remote} {branch}:refs/remotes/{remote}/{branch}")

    # --- 6. 未跟踪文件规模（防 add -A 洪水）---
    if len(untracked) > 200:
        r.add(BLOCK, "ADD01", f"{len(untracked)} 个未跟踪文件，git add -A 会引发提交洪水",
              "按需 git add <具体路径>；或先补 .gitignore")
    elif len(untracked) > 30:
        r.add(WARN, "ADD02", f"{len(untracked)} 个未跟踪文件，建议先整理 .gitignore")
    else:
        r.add(OK, "ADD02", f"未跟踪 {len(untracked)} 个")
    return r


def do_push(repo: Path, remote: str, branch: str) -> int:
    rc, head, _ = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)
    refspec = f"HEAD:{branch}" if head == "HEAD" else branch
    print(f"\n>>> 执行: git -c http.proxy= -c https.proxy= push {remote} {refspec}")
    rc, out, err = sh(["git", "-c", "http.proxy=", "-c", "https.proxy=",
                       "push", remote, refspec], cwd=repo, timeout=300)
    print(mask(out or err))
    if rc != 0:
        print(">>> 推送失败：按 GIT02/SYNC01 提示修正后重试")
        return 3
    # 回查：以远端 ls-remote 为准，不信任本地引用
    rc2, out2, _ = sh(["git", "-c", "http.proxy=", "-c", "https.proxy=",
                       "ls-remote", remote, branch], cwd=repo, timeout=120)
    remote_head = out2.split()[0] if out2 else ""
    local_head = sh(["git", "rev-parse", "HEAD"], cwd=repo)[1]
    print(f">>> 回查 ls-remote {remote}/{branch} = {remote_head[:12]}")
    print(f">>> 本地 HEAD                  = {local_head[:12]}")
    print(">>> 回查一致 ✅" if remote_head.startswith(local_head[:12]) else ">>> 回查不一致 ❌ 请人工确认")
    return 0 if remote_head.startswith(local_head[:12]) else 3


def main():
    ap = argparse.ArgumentParser(description="Git 多端镜像仓安全推送守卫 v1.1")
    ap.add_argument("--repo", default=".", help="仓库路径，默认当前目录")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="", help="目标分支，默认跟随当前分支")
    ap.add_argument("--execute", action="store_true", help="体检全绿才真正推送")
    ap.add_argument("--force-ignore-warn", action="store_true", help="忽略 WARN 强制推送")
    ap.add_argument("--ignore", default="",
                    help="临时豁免的检查码，逗号分隔，如 SEC01（仅限已知可接受项，需人工确认）")
    ap.add_argument("--allow-delete", type=int, default=DEFAULT_DELETE_CAP, help="删除条目熔断阈值")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    repo = Path(a.repo).resolve()
    branch = a.branch or (sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo)[1])
    if branch == "HEAD":
        branch = "main"
    r = check(repo, a.remote, branch, a.allow_delete)
    ig = {c.strip().upper() for c in a.ignore.split(",") if c.strip()}
    if ig:
        r.items = [dict(i, level=WARN, msg=i["msg"] + " （已豁免）")
                   if i["level"] == BLOCK and i["code"] in ig else i for i in r.items]
    r.dump(as_json=a.json)

    if r.blocked:
        sys.exit(3)
    if r.warned and not a.force_ignore_warn and a.execute:
        if not a.json:
            print("\n存在 P1 警告，未推送。确认无误后加 --force-ignore-warn。")
        sys.exit(2)
    if a.execute:
        sys.exit(do_push(repo, a.remote, branch))
    sys.exit(0)


if __name__ == "__main__":
    main()
