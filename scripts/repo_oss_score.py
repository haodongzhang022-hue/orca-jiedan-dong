# -*- coding: utf-8 -*-
"""五维打分选 Top 候选：原创度/活跃度/可公开性/生态重要性/可申性"""
import json, os, datetime, re

BASE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(BASE, "repo_oss_scan_result.json"), encoding="utf-8"))
NOW = datetime.datetime(2026, 9, 7)

# 明显不该申的黑名单关键词（镜像/笔记/私有业务/客户数据）
BAN = ["Obsidian", "笔记", "豆包", "备份", "bak", "config", "日志", "配置",
       "桥接", "终端隔离", "浏览器桥接", "templates", "lobster_templates"]
BIZ_SENSITIVE = ["企业微信群定制接单", "闲鱼", "赛事预测", "VibeTrading", "vnpy"]


def days_since(s):
    if not s:
        return 99999
    try:
        d = datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")
        return (NOW - d).days
    except Exception:
        return 99999


rows = []
for d in data:
    gh = d.get("gh") or {}
    if gh.get("error"):
        gh = {}
    name = d["name"]
    path = d["path"]
    stars = gh.get("stars") or 0
    commits = d.get("commits") or 0
    last = d.get("last_commit") or (gh.get("pushed_at") or "")
    age = days_since(last)
    is_fork = gh.get("is_fork", False)
    lic = gh.get("license")

    # 1 原创度 0-25
    orig = 10
    if not is_fork:
        orig += 8
    if d.get("authors") and len(d["authors"]) <= 3:
        orig += 4
    if any(k in path for k in BAN):
        orig -= 8
    orig = max(0, min(25, orig))

    # 2 活跃度 0-25
    act = 0
    act += 12 if age <= 30 else 8 if age <= 90 else 4 if age <= 365 else 0
    act += 8 if commits >= 100 else 5 if commits >= 30 else 2 if commits >= 5 else 0
    if gh.get("archived"):
        act = 0
    act = max(0, min(25, act))

    # 3 可公开性 0-20
    pub = 0
    if d.get("has_readme"):
        pub += 6
    if d.get("has_license") or lic:
        pub += 6
    if 0 < d.get("size_mb", 0) < 500:
        pub += 4
    if any(k in path for k in BIZ_SENSITIVE):
        pub -= 10
    pub = max(0, min(20, pub))

    # 4 生态重要性 0-20
    eco = 0
    eco += 10 if stars >= 100 else 6 if stars >= 20 else 3 if stars >= 5 else 1 if stars >= 1 else 0
    forks = gh.get("forks") or 0
    eco += 4 if forks >= 10 else 2 if forks >= 2 else 0
    if gh.get("language"):
        eco += 2
    if gh.get("desc"):
        eco += 2
    eco = max(0, min(20, eco))

    # 5 可申性（是否已公开在 GitHub + 非纯本地）0-10
    apply_ok = 8 if gh else 0
    if gh and gh.get("visibility_ok", True) and not gh.get("archived"):
        apply_ok += 2

    total = orig + act + pub + eco + apply_ok
    rows.append({
        "name": name, "path": path, "total": total,
        "orig": orig, "act": act, "pub": pub, "eco": eco, "apply": apply_ok,
        "stars": stars, "forks": forks, "commits": commits, "age_days": age,
        "lang": gh.get("language"), "lic": lic, "is_fork": is_fork,
        "readme": d.get("has_readme"), "license_file": d.get("has_license"),
        "size_mb": d.get("size_mb"), "files": d.get("files"),
        "remote": d.get("remote"), "desc": gh.get("desc", ""),
        "gh_url": f"https://github.com/{d['gh_owner']}/{d['gh_repo']}" if d.get("gh_owner") else None,
        "pushed": gh.get("pushed_at"),
    })

rows.sort(key=lambda r: -r["total"])
print(f"{'总分':>4} {'星':>6} {'提交':>5} {'天龄':>5} {'原创':>4}{'活跃':>4}{'公开':>4}{'生态':>4}{'可申':>4}  仓库")
print("-" * 100)
for r in rows[:20]:
    print(f"{r['total']:>4} {r['stars']:>6} {r['commits']:>5} {r['age_days']:>5} "
          f"{r['orig']:>4}{r['act']:>4}{r['pub']:>4}{r['eco']:>4}{r['apply']:>4}  {r['name'][:34]}")
    print(f"      {r['gh_url'] or r['path']}")
    if r["desc"]:
        print(f"      desc: {r['desc'][:90]}")

json.dump(rows, open(os.path.join(BASE, "repo_oss_score_result.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n明细 -> repo_oss_score_result.json")
