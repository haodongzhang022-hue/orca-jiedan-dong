#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
remote_repo_doctor.py  v1.3  (龙虾零成本运维守卫 v1.3 组件)

v1.3 变更（2026-09-11）：修复「SEC02 说有凭据、IDN01 却跳过」的弱判定缺口。
  旧版 credential_fill() 只返回 True/False，**从不取回明文令牌**，
  导致远端 URL 一旦脱敏（v1.2 的 SEC01 根治），身份探针就永远没令牌可用 -> 只能出弱判定。
  新增 credential_get_token()：多源取令牌
      环境变量 > ~/.git-credentials 明文 > git credential fill 子进程
  并把来源以脱敏形式记入 IDN00。至此「令牌失效 vs 仓库被删」可出强判定。
远端仓库可达性「分步诊断器」——专治「仓库是不是没了？」这类误判。

核心铁律：**身份探针优先于对象探针**
  绝大多数代码托管平台（GitHub / CNB / GitLab）对「认证失败」与「仓库不存在」
  一律返回 404「Repository Not Found」，目的是不泄露仓库是否存在。
  因此看到 404 **绝不能**直接判定「仓库被删」——
  必须先用「身份探针」（/user 这类与仓库无关的接口）确认凭据是否还活着：
    - 身份探针 401/403  -> 凭据失效  -> 404 是假象，真因是令牌，去换令牌
    - 身份探针 200      -> 凭据有效  -> 404 才是真的「仓库不存在/无权限」

零积分：纯 stdlib（urllib + subprocess），不调任何模型。

用法:
  python remote_repo_doctor.py --repo <本地仓库路径> [--remote <名>] [--all]
  python remote_repo_doctor.py --url  https://host/owner/repo.git
  python remote_repo_doctor.py --repo . --fix-inline-cred     # 内嵌明文 token -> 凭据库
  python remote_repo_doctor.py --repo . --json                # 机器可读输出

退出码:
  0 = 全部健康  2 = 有告警(WARN)  3 = 有阻断(FAIL)  4 = 参数/环境错误
"""
import argparse
import base64
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE  # 仅用于探测连通性，不传输敏感判断

UA = "lobster-remote-repo-doctor/1.0"

# 平台画像：api_root + 身份探针路径 + 对象探针路径
PLATFORMS = {
    "github.com": {
        "api": "https://api.github.com",
        "identity": "/user",
        "object": "/repos/{owner}/{repo}",
        "auth_headers": lambda t: {"Authorization": "Bearer " + t},
        "anon_identity_code": 401,   # 匿名访问 /user 的返回码
    },
    "cnb.cool": {
        "api": "https://api.cnb.cool",
        "identity": "/user",
        "object": "/repos/{owner}/{repo}",
        "auth_headers": lambda t: {"Authorization": "Bearer " + t},
        "anon_identity_code": 401,
    },
    "gitee.com": {
        "api": "https://gitee.com/api/v5",
        "identity": "/user",
        "object": "/repos/{owner}/{repo}",
        "auth_headers": lambda t: {"Authorization": "token " + t},
        "anon_identity_code": 401,
    },
}

SECRET_RE = re.compile(r"(?i)(sk-[A-Za-z0-9_\-]{8,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}"
                       r"|github_pat_[A-Za-z0-9_]{20,}|cnb_[A-Za-z0-9]{10,}"
                       r"|(?:^|[:@/])[A-Za-z0-9_\-]{32,}(?=$|[@/:?])|[0-9a-f]{40})")
INLINE_CRED_RE = re.compile(r"^(https?://)([^/@\s]+):([^/@\s]+)@(.+)$")

findings = []  # (level, code, msg)
PROXY = ""  # 全局代理，可用 --proxy 覆盖；默认清空走直连（国内平台直连更快）


def add(level, code, msg):
    findings.append((level, code, msg))
    icon = {"FAIL": "[FAIL]", "WARN": "[WARN]", "OK": "[ OK ]", "INFO": "[INFO]"}[level]
    print(f"{icon} {code}  {msg}")


def mask(s):
    """脱敏：任何疑似密钥串统一打码，避免日志二次泄漏。"""
    if not s:
        return s
    s = re.sub(r"(https?://)([^/@\s]+):([^/@\s]+)@", r"\1\2:***@", s)
    s = SECRET_RE.sub(lambda m: (m.group(0)[:3] + "***" + m.group(0)[-2:])
                      if len(m.group(0)) > 8 else "***", s)
    return s


def git(args, cwd=None, timeout=180, env=None):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                           text=True, timeout=timeout, errors="ignore", env=env)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout after %ss" % timeout
    except FileNotFoundError:
        return -2, "", "git not found"


def http_probe(url, headers=None, timeout=25):
    """返回 (code, body_snippet)；code 为 'ERR' 表示网络层失败。"""
    h = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        h.update(headers)
    try:
        req = Request(url, headers=h)
        with urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read(300).decode("utf-8", "ignore")
    except HTTPError as e:
        try:
            body = e.read(200).decode("utf-8", "ignore")
        except Exception:
            body = ""
        return e.code, body
    except URLError as e:
        return "ERR", str(e.reason)[:120]
    except Exception as e:
        return "ERR", type(e).__name__ + " " + str(e)[:80]


def parse_remote(url):
    """解析 remote URL -> dict(platform, owner, repo, inline_user, inline_token, safe_url, web_url)"""
    info = {"raw": url, "safe_url": mask(url), "inline_user": None,
            "inline_token": None, "platform": None, "owner": None, "repo": None}
    m = INLINE_CRED_RE.match(url)
    if m:
        info["inline_user"], info["inline_token"] = m.group(2), m.group(3)
        scheme, rest = m.group(1), m.group(4)
    else:
        scheme, rest = ("https://" if url.startswith("http") else ""), url
    mm = re.match(r"^(?:https?://)?([^/:]+)[/:](.+?)(?:\.git)?$", rest)
    if not mm:
        return info
    host, path = mm.group(1), mm.group(2)
    # 坑（v1.3 修复）：`https://user@host/...` 这种「只有用户名没有密码」的 URL，
    #   INLINE_CRED_RE 不匹配（它要求 user:pass@），host 于是变成 `user@host`
    #   -> PLATFORMS 查不到 -> 身份探针被当成「无平台画像」跳过，结论退化成弱判定。
    #   实测：v1.2 做完 SEC01 脱敏后 remote 恰好变成这种形式，诊断器从此只剩弱判定。
    host = re.sub(r"^[^/@\s]+@", "", host)
    info["platform"] = host if host in PLATFORMS else None
    parts = [p for p in re.split(r"[:/]", path) if p]
    if len(parts) >= 2:
        info["owner"], info["repo"] = parts[-2], parts[-1]
    info["web_url"] = scheme + host + "/" + "/".join(parts)
    return info


def credential_fill(host):
    """问凭据库要账号密码（不打印），只回报有没有。"""
    # 双重坑（实测挂死 6 分钟）：
    #  1) helper=GCM 时，fill 无匹配条目会拉起 GUI 交互进程；
    #  2) 该 GUI 进程继承 stdout 管道 -> 即使 subprocess 超时 kill 掉 git，
    #     communicate() 仍因管道被孙进程持有而永久阻塞（timeout 形同虚设）。
    # 解法：stdout 重定向到临时文件（不用管道）+ GCM_INTERACTIVE=never + 显式 kill
    #       + 用 `-c credential.helper= -c credential.helper=store` 屏蔽 GCM（追加≠替换）
    # 快路径（零子进程）：直接读 ~/.git-credentials
    try:
        pf = os.path.expanduser("~/.git-credentials")
        if os.path.exists(pf):
            with open(pf, "r", errors="ignore") as f:
                if any(host in ln and "@" in ln for ln in f):
                    return True, "file-hit"
    except Exception:
        pass
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    tmp = os.path.join(os.environ.get("TEMP", "."), "_lkr_cred_%d.tmp" % os.getpid())
    try:
        with open(tmp, "w", errors="ignore") as fo:
            p = subprocess.Popen(["git", "-c", "credential.helper=",
                                  "-c", "credential.helper=store",
                                  "credential", "fill"], stdin=subprocess.PIPE,
                                 stdout=fo, stderr=subprocess.DEVNULL, text=True, env=env)
            try:
                p.communicate(input=f"protocol=https\nhost={host}\n\n", timeout=20)
            except subprocess.TimeoutExpired:
                p.kill()
                try:
                    p.communicate(timeout=5)
                except Exception:
                    pass
                return False, "TIMEOUT(凭据助手挂起，已降级为无凭据)"
        with open(tmp, "r", errors="ignore") as fi:
            out = fi.read()
    except Exception as e:
        return False, type(e).__name__ + " " + str(e)[:60]
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return "password=" in out, out


# 令牌来源：环境变量（按 host 定制） -> 通用变量
TOKEN_ENV_BY_HOST = {
    "github.com": ["GITHUB_TOKEN", "GH_TOKEN"],
    "cnb.cool": ["CNB_TOKEN", "CNB_GIT_TOKEN"],
    "gitee.com": ["GITEE_TOKEN", "GITEE_ACCESS_TOKEN"],
}
GENERIC_TOKEN_ENVS = ["LOBSTER_GIT_TOKEN", "GIT_TOKEN"]


def mask_token(t):
    """令牌脱敏：只留前 4 位前缀与长度，永不落明文。"""
    if not t:
        return "(空)"
    return "%s***(len=%d)" % (t[:4], len(t))


def _token_from_credentials_file(host):
    """直读 ~/.git-credentials（store helper 落盘即明文，格式 https://user:pass@host）。"""
    pf = os.path.expanduser("~/.git-credentials")
    if not os.path.exists(pf):
        return None
    try:
        with open(pf, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if not ln or "@" not in ln:
                    continue
                m = re.match(r"^https?://([^:/@\s]+):([^@\s]+)@([^/\s]+)", ln)
                if m and m.group(3) == host:
                    return m.group(2)
    except Exception:
        pass
    return None


def _token_from_cnb_cli():
    """~/.cnb/token —— cnb CLI 的登录态，与 ~/.git-credentials 是**两套独立凭据**。

    2026-09-11 实测：git-credentials 里那条 94 位 cnb_ 令牌已失效（身份探针 401），
    但 ~/.cnb/token 里的 access_token 仍然有效（身份探针 200、push 成功）。
    **「CNB 令牌失效」这句话必须带上「哪一套」才有意义。**
    """
    p = os.path.expanduser("~/.cnb/token")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(open(p, encoding="utf-8"))
        t = d.get("access_token")
        exp = d.get("expires_at")
        if t and exp and time.time() > float(exp):
            return None          # 已过期，别拿去污染判定
        return t or None
    except Exception:
        return None


def token_candidates(host):
    """返回该 host 的**全部**候选令牌 [(token, source), ...]。

    为什么不再只取一个：不同来源的令牌是不同权限/不同生命周期的东西，
    只试一个就会得出「令牌失效」这种以偏概全的结论（2026-09-10/11 连续误判两次）。
    正确做法是逐个打身份探针，谁 200 用谁。
    """
    out = []

    def add(t, src):
        if t and (t, src) not in out:
            out.append((t, src))

    add(_token_from_credentials_file(host), "file:~/.git-credentials")
    if host == "cnb.cool":
        add(_token_from_cnb_cli(), "file:~/.cnb/token(cnb CLI 登录态)")
    for var in TOKEN_ENV_BY_HOST.get(host, []) + GENERIC_TOKEN_ENVS:
        v = os.environ.get(var)
        if v and v.strip():
            add(v.strip(), "env:" + var)
    return out


def credential_get_token(host):
    """多源取明文令牌 -> (token, source)。拿不到返回 (None, reason)。

    设计要点：令牌只在内存中流转，任何日志/输出一律走 mask_token()，
    绝不进入 git、四端同步产物或记忆文件（密钥红线）。

    顺序铁律（v1.3 实测纠正）：**凭据库优先于环境变量**。
      环境变量里的往往是「平台 API 令牌」而非「git 推送令牌」——
      实测 cnb.cool 环境有 CNB_TOKEN/CNB_GIT_TOKEN 各 27 位（API 用），
      而 git 真正拿来推送的是凭据库里那条 94 位 cnb_ 开头的令牌。
      拿 API 令牌去打身份探针会得出与实际 git 行为不符的结论。
      本脚本诊断的是 git 可达性，所以必须与 git 用同一份凭据。
    """
    # 1) ~/.git-credentials 明文（git 实际使用的凭据，零子进程）
    t = _token_from_credentials_file(host)
    if t:
        return t, "file:~/.git-credentials"
    # 2) 环境变量（无落盘凭据时的兜底，如 CI / 计划任务）
    for var in TOKEN_ENV_BY_HOST.get(host, []) + GENERIC_TOKEN_ENVS:
        v = os.environ.get(var)
        if v and v.strip():
            return v.strip(), "env:" + var
    # 3) 退回 git credential fill（GCM 也走这条；已按坑1/坑2加固）
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    tmp = os.path.join(os.environ.get("TEMP", "."), "_lkr_tok_%d.tmp" % os.getpid())
    try:
        with open(tmp, "w", errors="ignore") as fo:
            p = subprocess.Popen(["git", "-c", "credential.helper=",
                                  "-c", "credential.helper=store",
                                  "credential", "fill"], stdin=subprocess.PIPE,
                                 stdout=fo, stderr=subprocess.DEVNULL, text=True, env=env)
            # 坑：stdout 必须是文件不是管道，否则 GCM 孙进程持有管道导致 timeout 失效
            try:
                p.communicate(input="protocol=https\nhost=%s\n\n" % host, timeout=20)
            except subprocess.TimeoutExpired:
                p.kill()
                try:
                    p.communicate(timeout=5)
                except Exception:
                    pass
                return None, "credential fill 超时（凭据助手挂起）"
        with open(tmp, "r", errors="ignore") as fi:
            out = fi.read()
        m = re.search(r"(?m)^password=(.*)$", out)
        if m and m.group(1).strip():
            return m.group(1).strip(), "cmd:git credential fill"
    except Exception as e:
        return None, type(e).__name__ + " " + str(e)[:60]
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass
    return None, "凭据库无该 host 的可用明文条目"


def credential_approve(host, user, token):
    """写入 git 凭据库（GCM 优先，失败退回 store）。"""
    payload = f"protocol=https\nhost={host}\nusername={user}\npassword={token}\n\n"
    last_err = ""
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    # 坑1：`-c credential.helper=store` 是**追加**不是替换，全局配的 GCM 仍会被调用并挂死。
    #      必须先 `-c credential.helper=` 清空列表再设值。
    # 坑2：`-c` 是 git 全局选项，必须在子命令 credential 之前。
    # 坑3：GCM 在本机（无 GUI 会话/计划任务上下文）会挂起 -> 默认优先用 store，GCM 仅作兜底。
    for helper in ("store", None):
        cmd = ["git"]
        if helper:
            cmd += ["-c", "credential.helper=", "-c", "credential.helper=" + helper]
        cmd += ["credential", "approve"]
        # 同样规避 GCM 继承管道导致的假挂：stdout 走临时文件、stderr 丢弃、显式 kill
        tmp = os.path.join(os.environ.get("TEMP", "."), "_lkr_appr_%d.tmp" % os.getpid())
        try:
            with open(tmp, "w", errors="ignore") as fo:
                errf = tmp + ".err"
                fe = open(errf, "w", errors="ignore")
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=fo,
                                     stderr=fe, text=True, env=env)
                try:
                    p.communicate(input=payload, timeout=25)
                    rc = p.returncode
                except subprocess.TimeoutExpired:
                    p.kill()
                    try:
                        p.communicate(timeout=5)
                    except Exception:
                        pass
                    rc = -1
            if rc == 0:
                try:
                    fe.close()
                except Exception:
                    pass
                return True, helper or "system-default(GCM)"
            try:
                fe.close()
                with open(errf, "r", errors="ignore") as f2:
                    last_err = f2.read().strip()[:120]
            except Exception:
                last_err = ""
        except Exception as e:
            last_err = type(e).__name__
        finally:
            for f_ in (tmp, tmp + ".err"):
                try:
                    os.remove(f_)
                except Exception:
                    pass
    return False, "all helpers failed; last=" + (last_err or "?")


def diagnose(url, do_fix=False, repo_path=None, remote_name=None):
    info = parse_remote(url)
    add("INFO", "URL01", "目标: " + info["safe_url"])
    if not info["owner"] or not info["repo"]:
        add("FAIL", "URL02", "无法从 URL 解析 owner/repo")
        return
    # 必须先把内嵌凭证剥掉再取 host，否则会把「用户名」当成 host
    # （实测坑：https://user:tok@cnb.cool/... 直接 split(":")[0] 得到的是 user）
    host = re.sub(r"^https?://", "", info["raw"])
    host = re.sub(r"^[^/@\s]+:[^/@\s]+@", "", host)   # 剥 user:token@
    host = re.sub(r"^[^/@\s]+@", "", host)            # 剥 user@
    host = host.split("/")[0].split(":")[0]

    # ---------- 1. 内嵌明文凭证（SEC01）----------
    if info["inline_token"]:
        add("FAIL", "SEC01",
            f"远端 URL 内嵌明文凭证（user={info['inline_user']}, token长度={len(info['inline_token'])}）"
            " -> .git/config 一旦进备份/同步即泄漏")
        if do_fix and repo_path and remote_name:
            fix_inline_cred(repo_path, remote_name, info, host)
            info = parse_remote(git(["remote", "get-url", remote_name], cwd=repo_path)[1])
    else:
        add("OK", "SEC01", "远端 URL 无内嵌凭证")

    # ---------- 2. 凭据库存量 ----------
    has_cred, _ = credential_fill(host)
    add("OK" if has_cred else "WARN", "SEC02",
        "凭据库已有 %s 条目" % host if has_cred else "凭据库无 %s 条目（每次推需交互或依赖 URL 明文）" % host)

    # 候选令牌：URL 内嵌（已告警）> 凭据库 > cnb CLI 登录态 > 环境变量
    cands = []
    if info["inline_token"]:
        cands.append((info["inline_token"], "url-inline"))
    cands += token_candidates(host)
    token, tok_src = (cands[0] if cands else (None, "无"))
    add("INFO", "IDN00", "候选令牌 %d 个: %s"
        % (len(cands), ", ".join("%s=%s" % (s, mask_token(t)) for t, s in cands) or "无"))
    plat = PLATFORMS.get(info["platform"])

    # ---------- 3. 匿名对象探针（最容易骗人的一步）----------
    anon_code, _ = http_probe(info["web_url"])
    add("INFO", "OBJ00", f"匿名访问仓库页 -> {anon_code}"
        + ("（404 未必等于被删，见下）" if anon_code == 404 else ""))

    # ---------- 4. 身份探针（真因判定关键）----------
    identity_ok = None
    if plat and cands:
        # 逐个试，谁 200 用谁——避免「一条令牌死了就说令牌失效」
        for t, src in cands:
            code, _ = http_probe(plat["api"] + plat["identity"], headers=plat["auth_headers"](t))
            if code == 200:
                identity_ok, token, tok_src = True, t, src
                add("OK", "IDN01", f"{info['platform']} 身份探针 200 -> 凭据有效（{src}）")
                break
            last_code = code
        if identity_ok is None:
            identity_ok = False
            add("FAIL", "IDN01",
                f"{info['platform']} 全部 {len(cands)} 个候选令牌身份探针均非 200"
                f"（末次 {last_code}）-> **凭据均已失效**（过期/被撤销/权限不足）")
    elif not token:
        add("INFO", "IDN01", "无可用令牌（URL 无内嵌且凭据库未取到明文），跳过身份探针")
    else:
        add("INFO", "IDN01", f"平台 {host} 无预置画像，跳过 API 身份探针，仅用 git 判定")

    # ---------- 5. git 对象探针（权威）----------
    args = ["-c", "http.proxy=" + PROXY, "-c", "https.proxy=" + PROXY, "ls-remote", "--heads"]
    # cnb.cool 特例（2026-09-11 实测）：remote URL 里带 `user@` 时 git 拿 user 去换凭据，
    # 服务端回 `token:` 为空 → 伪装成「仓库不存在」。改用无用户名 URL + GIT_ASKPASS（cnb CLI 登录态）才通。
    genv = None
    if host == "cnb.cool" and _token_from_cnb_cli():
        clean = re.sub(r"^(https?://)[^/@\s]+@", r"\1", url)
        args = ["-c", "http.proxy=", "-c", "https.proxy=",
                "-c", "credential.helper=", "ls-remote", "--heads", clean]
        genv = dict(os.environ)
        genv.pop("CNB_TOKEN", None)
        genv.pop("CNB_GIT_TOKEN", None)
        genv["GIT_TERMINAL_PROMPT"] = "0"
        ap = r"G:\WorkBuddy_Data\cnb_askpass.sh"
        if os.path.exists(ap):
            genv["GIT_ASKPASS"] = ap
        else:
            # 无 askpass 脚本时的兜底：临时 URL 内嵌（用完即弃，不写 .git/config）
            genv = None
            args[-1] = re.sub(r"^(https?://)", r"\1cnb:" + _token_from_cnb_cli() + "@", clean)
    if genv is not None or not repo_path:
        rc, out, err = git(args, cwd=repo_path, env=genv)   # args 已含完整 URL
    else:
        rc, out, err = git(args + [remote_name or "origin"], cwd=repo_path)
    git_ok = (rc == 0)
    err_masked = mask((err or "").replace("\n", " | ")[:200])

    # v1.1 (2026-09-14) 代理/链路误报识别
    # 实测：身份探针 200（令牌有效）+ git 报 "Failed to receive SOCKS response,
    # proxy closed connection"，被判定矩阵判成 FAIL「凭据有效但仓库不可达」——
    # 于是 OpsGuard 天天给仓库记红，实际挂的是 7897→1081→香港 这条代理链路。
    # `-c http.proxy=` 只能清 git config 级代理，清不掉系统级/链路级故障。
    # 所以这里按**错误文本特征**分流：链路问题 ≠ 仓库问题，不许记到仓库头上。
    proxy_suspect = (not git_ok) and bool(re.search(
        r"socks|proxy|tunnel|closed connection|connection reset|"
        r"couldn't connect|Could not resolve|timed out|Failed to receive",
        err or "", re.I))
    # 代理/链路故障降级为 WARN：仓库本身没病，别让它背锅（否则 OpsGuard 天天记红）
    add("OK" if git_ok else ("WARN" if proxy_suspect else "FAIL"), "OBJ01",
        f"git ls-remote -> rc={rc}" + ("" if git_ok else f"  {err_masked}"))
    if proxy_suspect:
        add("WARN", "PRX01",
            "git 报错形似**代理/链路故障**，不是仓库或凭据问题："
            f"{err_masked[:120]}\n"
            "        处置：① `netstat -ano | grep :7897` 看中转器在不在听；"
            "② 直连复测 `git -c http.proxy= -c https.proxy= ls-remote`（国内平台应走直连）；"
            "③ 链路修好后复跑本脚本。在链路恢复前，本项**不计入仓库健康度**。")

    # ---------- 6. 判定矩阵（本脚本的价值所在）----------
    print("\n--- 判定 ---")
    if git_ok:
        add("OK", "VERDICT", "仓库可达且凭据有效，无需处置")
    elif identity_ok is False:
        add("FAIL", "VERDICT",
            "**令牌失效是根因**：身份探针 401 证明凭据已死；"
            f"此时 {host} 返回的 404「仓库不存在」是平台标准伪装，**不可据此判定仓库被删**。\n"
            f"        处置：去 {info['platform'] or host} 重新签发令牌 -> "
            f"`git -c credential.helper=store credential approve` 写入凭据库 -> 复跑本脚本。")
    elif identity_ok is True and proxy_suspect:
        add("WARN", "VERDICT",
            "**疑似代理/链路故障，非仓库问题**：身份探针 200 证明令牌活着，"
            "git 失败原因落在传输层（见 PRX01）。\n"
            "        结论降级为 WARN：先修链路再复跑，不要据此判定仓库被删或令牌失效。")
    elif identity_ok is True:
        add("FAIL", "VERDICT",
            "凭据有效但仓库不可达 -> 仓库确实不存在，或该令牌账号无访问权限。"
            "处置：网页端确认仓库归属 / 检查令牌 scope。")
    else:
        add("WARN", "VERDICT",
            "无法完成身份探针（无令牌/无平台画像），结论为弱判定："
            "git ls-remote 失败，可能是网络、代理或权限任一原因。\n"
            "        处置：先 `git -c http.proxy= -c https.proxy= ls-remote` 排代理；"
            "再补令牌跑本脚本拿强判定。")
    return info


def fix_inline_cred(repo_path, remote_name, info, host):
    """把内嵌明文 token 迁进凭据库，并把 remote URL 改成无明文形式。"""
    cfg = os.path.join(repo_path, ".git", "config")
    bak = cfg + ".bak_" + time.strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(cfg, bak)
        add("INFO", "FIX01", "已备份 .git/config -> " + bak)
    except Exception as e:
        add("FAIL", "FIX00", "备份 .git/config 失败: %s" % e)
        return
    # 红线留档：明文只留在不进 git、不进四端的本地红线目录
    try:
        red = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "_security_red_lines")
        os.makedirs(red, exist_ok=True)
        p = os.path.join(red, f"{host}_token_backup_{time.strftime('%Y%m%d')}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"# 本地红线留档，禁止进 git / 禁止进四端同步\n"
                    f"host={host}\nuser={info['inline_user']}\ntoken={info['inline_token']}\n")
        add("OK", "FIX02", "明文令牌留档（不进 git）-> " + p)
    except Exception as e:
        add("WARN", "FIX02", "红线留档失败: %s" % e)
    ok, helper = credential_approve(host, info["inline_user"], info["inline_token"])
    if not ok:
        add("FAIL", "FIX03", "写入凭据库失败(%s)，已中止，remote URL 保持原样" % helper)
        return
    add("OK", "FIX03", "已写入凭据库 helper=%s" % helper)
    new_url = re.sub(r"^(https?://)[^/@\s]+:[^/@\s]+@",
                     r"\1" + info["inline_user"] + "@", info["raw"])
    rc, _, err = git(["remote", "set-url", remote_name, new_url], cwd=repo_path)
    if rc != 0:
        add("FAIL", "FIX04", "改写 remote 失败: " + mask(err))
        return
    add("OK", "FIX04", "remote URL 已脱敏 -> " + mask(new_url))

    # FIX05（必须）：光写入 store 不够——默认 helper 是 GCM，而 GCM 读的是自己的库，
    # 结果 git 仍取不到刚存的凭据（实测服务端回 `token:` 为空 = 未带认证）。
    # 在本仓库 local 层先置空重置 helper 列表，再挂 store，才能确保 git 用得上。
    git(["config", "--local", "credential.helper", ""], cwd=repo_path)
    rc5, _, e5 = git(["config", "--local", "--add", "credential.helper", "store"], cwd=repo_path)
    if rc5 != 0:
        add("WARN", "FIX05", "设置 local helper=store 失败: " + mask(e5))
    else:
        cur = git(["config", "--local", "--get-all", "credential.helper"], cwd=repo_path)[1]
        add("OK", "FIX05", "本仓库 helper 已改为 " + (cur.replace("\n", ",") or "?")
            + "（空值重置 + store，屏蔽会挂起的 GCM）")


def main():
    ap = argparse.ArgumentParser(description="远端仓库可达性分步诊断器")
    ap.add_argument("--repo", help="本地仓库路径")
    ap.add_argument("--remote", default="origin", help="remote 名，默认 origin")
    ap.add_argument("--all", action="store_true", help="诊断该仓库所有 remote")
    ap.add_argument("--url", help="直接给远端 URL（无需本地仓库）")
    ap.add_argument("--fix-inline-cred", action="store_true", help="迁移内嵌明文 token 到凭据库")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--proxy", default="", help="git ls-remote 用的代理，如 socks5://127.0.0.1:1081；默认清空")
    a = ap.parse_args()
    global PROXY
    PROXY = a.proxy

    targets = []
    if a.url:
        targets.append((a.url, None, None))
    elif a.repo:
        repo = os.path.abspath(a.repo)
        if not os.path.isdir(os.path.join(repo, ".git")):
            print("[FAIL] ENV01 不是 git 仓库: " + repo)
            return 4
        names = []
        if a.all:
            names = git(["remote"], cwd=repo)[1].split()
        else:
            names = [a.remote]
        for n in names:
            u = git(["remote", "get-url", n], cwd=repo)[1]
            if u:
                targets.append((u, repo, n))
    else:
        print("[FAIL] ENV02 需要 --repo 或 --url")
        return 4

    if not targets:
        print("[FAIL] ENV03 未找到任何 remote")
        return 4

    for i, (u, rp, rn) in enumerate(targets):
        if i:
            print("\n" + "=" * 66 + "\n")
        print(f"### remote: {rn or '(url)'}   {time.strftime('%Y-%m-%d %H:%M:%S')}")
        diagnose(u, do_fix=a.fix_inline_cred, repo_path=rp, remote_name=rn)

    lv = [f[0] for f in findings]
    if a.json:
        print("\n" + json.dumps([{"level": l, "code": c, "msg": mask(m)} for l, c, m in findings],
                                ensure_ascii=False, indent=2))
    print("\n=== 汇总 FAIL=%d WARN=%d ===" % (lv.count("FAIL"), lv.count("WARN")))
    if "FAIL" in lv:
        return 3
    if "WARN" in lv:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
