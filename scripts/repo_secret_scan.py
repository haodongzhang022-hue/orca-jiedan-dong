# -*- coding: utf-8 -*-
"""
仓库公开化脱敏体检 —— 扫描候选仓库中禁止公开的内容
红线：sk-/token/secret/密码/内网IP/真实姓名/客户标识/手机号/邮箱/身份证
零成本纯本地，只读不修改
用法: python repo_secret_scan.py <仓库路径> [<仓库路径2> ...]
"""
import os, re, sys, json

PATTERNS = [
    ("OpenAI密钥",   re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("通用APIKey",   re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
    ("Token",        re.compile(r"(?i)(access[_-]?token|auth[_-]?token|bt[_-]?token|\btoken\b)\s*[:=]\s*['\"][^'\"]{8,}['\"]")),
    ("Secret",       re.compile(r"(?i)(client[_-]?secret|app[_-]?secret|\bsecret\b)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("密码",         re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]")),
    ("私钥",         re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("内网IP",       re.compile(r"\b(10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)\b")),
    ("公网服务器IP",  re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("手机号",       re.compile(r"\b1[3-9]\d{9}\b")),
    ("身份证",       re.compile(r"\b\d{17}[\dXx]\b")),
    ("邮箱",         re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("微信/企微ID",  re.compile(r"(?i)(corpid|corpsecret|agentid|webhook)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("腾讯云SecretId", re.compile(r"AKID[A-Za-z0-9]{16,}")),
    ("GitHub PAT",   re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("Slack/其他Webhook", re.compile(r"https://hooks\.[a-z]+\.com/services/[A-Za-z0-9/]+")),
]

SKIP_DIR = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
            ".idea", ".vscode", ".next", "site-packages", ".workbuddy"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".mp4", ".mp3", ".wav", ".zip",
            ".7z", ".gz", ".tar", ".exe", ".dll", ".so", ".pdf", ".woff", ".woff2",
            ".ttf", ".pyc", ".svg", ".min.js", ".lock"}
MAX_SIZE = 1024 * 1024  # 1MB 以上跳过


def scan_repo(root):
    findings = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIR]
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT:
                continue
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) > MAX_SIZE:
                    continue
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for name, pat in PATTERNS:
                            m = pat.search(line)
                            if m:
                                s = m.group(0)
                                masked = s[:6] + "***" + s[-4:] if len(s) > 14 else s[:3] + "***"
                                findings.append({
                                    "type": name, "file": os.path.relpath(p, root),
                                    "line": i, "masked": masked,
                                    "snippet": line.strip()[:100]
                                })
                                break
            except Exception:
                continue
    return findings


if __name__ == "__main__":
    targets = sys.argv[1:]
    if not targets:
        print("用法: python repo_secret_scan.py <仓库路径> [...]")
        sys.exit(1)
    all_res = {}
    for t in targets:
        res = scan_repo(t)
        all_res[t] = res
        print(f"\n=== {t} === 命中 {len(res)} 条")
        bytype = {}
        for r in res:
            bytype.setdefault(r["type"], []).append(r)
        for k, v in sorted(bytype.items(), key=lambda x: -len(x[1])):
            print(f"  [{k}] {len(v)} 条  例: {v[0]['file']}:{v[0]['line']} -> {v[0]['masked']}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo_secret_scan_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_res, f, ensure_ascii=False, indent=1)
    print("\n明细 ->", out)
