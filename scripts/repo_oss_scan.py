# -*- coding: utf-8 -*-
"""
Codex 开源福利申请 · 仓库体检扫描器
零成本：纯本地 git 元数据 + GitHub 公开 API（无需 token，60次/小时）
输出：JSON 体检结果，供五维打分
"""
import os, subprocess, json, re, time, sys

ROOT = r"E:\龙虾AI主控中心"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo_oss_scan_result.json")
GIT = "git"


def run(cmd, cwd, timeout=15):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout,
                           shell=True, errors="ignore")
        return (p.stdout or "").strip()
    except Exception as e:
        return ""


def find_repos(root, max_depth=3):
    repos = []
    root_depth = root.rstrip("\\/").count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.count(os.sep) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
        if ".git" in dirnames:
            dirnames.remove(".git")
            repos.append(dirpath)
        # 跳过超大缓存目录
        dirnames[:] = [d for d in dirnames if d not in
                       ("node_modules", ".venv", "venv", "__pycache__", ".git", "dist", "build")]
    return repos


def scan(repo):
    d = {"path": repo, "name": os.path.basename(repo)}
    d["remote"] = run("git config --get remote.origin.url", repo)
    d["branch"] = run("git rev-parse --abbrev-ref HEAD", repo)
    d["commits"] = run("git rev-list --count HEAD", repo)
    try:
        d["commits"] = int(d["commits"]) if d["commits"] else 0
    except Exception:
        d["commits"] = 0
    d["last_commit"] = run("git log -1 --format=%ci", repo)
    d["authors"] = run("git log --format=%an | sort -u | head -20", repo).split("\n")
    d["authors"] = [a for a in d["authors"] if a]
    d["has_readme"] = any(f.lower().startswith("readme") for f in os.listdir(repo)
                          if os.path.isfile(os.path.join(repo, f)))
    d["has_license"] = any(f.lower().startswith("license") or f.lower().startswith("licence")
                           for f in os.listdir(repo) if os.path.isfile(os.path.join(repo, f)))
    # 体积与文件数（快速采样）
    cnt, size = 0, 0
    for dp, dn, fn in os.walk(repo):
        dn[:] = [x for x in dn if x not in (".git", "node_modules", ".venv", "__pycache__")]
        for f in fn:
            cnt += 1
            try:
                size += os.path.getsize(os.path.join(dp, f))
            except Exception:
                pass
        if cnt > 20000:
            break
    d["files"], d["size_mb"] = cnt, round(size / 1024 / 1024, 1)
    # GitHub slug
    m = re.search(r"github\.com[:/]([^/]+)/([^/\s]+?)(\.git)?$", d["remote"] or "")
    d["gh_owner"], d["gh_repo"] = (m.group(1), m.group(2)) if m else (None, None)
    return d


def gh_star(owner, repo):
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lobster-scanner"})
        with urllib.request.urlopen(req, timeout=10) as r:
            j = json.loads(r.read().decode())
        return {
            "stars": j.get("stargazers_count"),
            "forks": j.get("forks_count"),
            "open_issues": j.get("open_issues_count"),
            "pushed_at": j.get("pushed_at"),
            "created_at": j.get("created_at"),
            "language": j.get("language"),
            "is_fork": j.get("fork"),
            "license": (j.get("license") or {}).get("spdx_id"),
            "desc": (j.get("description") or "")[:200],
            "archived": j.get("archived"),
            "homepage": j.get("homepage"),
        }
    except Exception as e:
        return {"error": str(e)[:120]}


if __name__ == "__main__":
    repos = find_repos(ROOT, max_depth=3)
    print(f"发现 {len(repos)} 个 git 仓库，开始扫描...", flush=True)
    out = []
    for i, r in enumerate(repos):
        try:
            d = scan(r)
        except Exception as e:
            continue
        out.append(d)
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(repos)}", flush=True)
    # GitHub API 补 star（只查有 github remote 的，限 45 个）
    targets = [d for d in out if d.get("gh_owner")][:45]
    print(f"查询 GitHub 元数据 {len(targets)} 个...", flush=True)
    for d in targets:
        d["gh"] = gh_star(d["gh_owner"], d["gh_repo"])
        time.sleep(0.3)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("DONE ->", OUT, flush=True)
