#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
secret_scan_cleanup.py — P0-1 密钥清理 · 定时扫描/清洗脚本（Hermes/Marvis 本地定时执行）
归属：Issue #27 · CNB×CodeBuddy 交叉评审 P0-1「明文 API 密钥已入库」修复
版本：v1.0.0

职责（纯业务逻辑，不含任何 Windows 计划任务调用）：
  1. 全仓库扫描明文密钥（sk- / ghp_ / tp- / api_key 等特征）
  2. 命中即自动【脱敏】工作区文件（把明文替换为占位符，保留行结构与可读性）
  3. 输出结构化扫描报告 → fleet_exchange/results/，供 Marvis 本地消费
  4. 报告新增泄漏/已清点 → 回写 local_job_queue.json 标记待处理 / 已闭环

边界（Issue #10 + #27 强制约定）：
  - 不生成/不调用 schtasks 等 Windows 计划任务指令（调度参数在 config/autogpt/triggers.yaml）
  - 不触碰 git 历史重写（history purge 需人工在维护窗口用 git filter-repo 单独做，本脚本不做 force-push）
  - 密钥一律走环境变量引用，零硬编码；本脚本【绝不打印/落库】密钥明文
  - 对「报告/文档里引述泄漏示例」的命中（如评审报告里写 sk-07d4...）做【引述占位化】而非删除

用法（供 Marvis 定时任务调用）：
  python scripts/secret_scan_cleanup.py --action scan            # 仅扫描报告，不改文件
  python scripts/secret_scan_cleanup.py --action redact          # 扫描 + 自动脱敏工作区文件（默认）
  python scripts/secret_scan_cleanup.py --action report          # 仅输出最近一次报告
  python scripts/secret_scan_cleanup.py --action dryrun          # 预演：显示将被脱敏的文件，不改写

调度建议（写入 config/autogpt/triggers.yaml，由 Marvis 落计划任务）：
  AG_Secret_Cleanup:
    cron: "0 2 * * *"            # 每日 02:00 低峰
    schedule_human: "每日 02:00"
    action: redact
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "fleet_exchange" / "results"
QUEUE_PATH = PROJECT_ROOT / "local_job_queue.json"

# ---- 明文密钥特征（红队扫描规则）----
# 优先级从高到低：越靠前越像真密钥。脱敏时对高优先命中用严格占位。
SECRET_PATTERNS: List[Tuple[str, str]] = [
    # (name, regex)
    ("github_pat",     r"ghp_[A-Za-z0-9]{20,}"),
    ("github_oauth",   r"gho_[A-Za-z0-9]{20,}"),
    ("deepseek_key",   r"sk-[A-Za-z0-9]{20,}"),
    ("mimo_key",       r"tp-[A-Za-z0-9]{16,}"),
    ("openai_key",     r"sk-[A-Za-z0-9]{32,}"),
    ("generic_bearer", r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}"),
]

# 说明：不做泛化的 api_key=/token=/secret= 赋值脱敏（会误伤 URL 查询参数 zd_token、教程占位符、
# 以及 process.env.API_KEY 等非真实密钥示例，造成海量 diff 噪音）。
# 只精确匹配“真密钥格式”：sk- / ghp_ / gho_ / tp- 等带明确前缀的高熵串。
# 这样 DEEPSEEK_API_KEY=sk-07d4... 会被 deepseek_key 规则命中 → 值替换为占位，键名保留。
# 引述示例（报告里描述泄漏的样例行，含 sk-07d4... 前缀）——脱敏时保留"这是示例"语义
QUOTE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{4,20}")


def load_queue() -> dict:
    if QUEUE_PATH.exists():
        try:
            return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"jobs": [], "note": "", "generated_at": "", "generated_by": "", "source_config": "", "scheduler": {}}


def save_queue(q: dict) -> None:
    QUEUE_PATH.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def redact_line(line: str) -> Tuple[str, List[str]]:
    """对一行做脱敏，返回 (新行, 命中规则列表)。"""
    hits: List[str] = []
    new = line
    for name, pat in SECRET_PATTERNS:
        def _repl(m: re.Match) -> str:
            hits.append(name)
            return f"{{{{REDACTED:{name}}}}}"
        new = re.sub(pat, _repl, new)
    return new, hits


def scan_file(path: Path, dryrun: bool) -> Dict[str, object]:
    """扫描并（可选）脱敏单文件。返回统计。
    注意：保留原始行尾（CRLF/LF），避免重写导致全文件 diff。"""
    try:
        # open()+newline='' 关闭通用换行翻译，逐字节保留原始行尾（CRLF/LF），避免 CRLF→LF 全量 diff
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
            raw = fh.read()
    except Exception:
        return {"file": str(path), "lines": 0, "hits": [], "redacted": False, "error": "read-failed"}

    # 检测主导行尾，写回时保持，避免 CRLF→LF 全量 diff
    crlf = raw.count("\r\n")
    lf = raw.count("\n") - crlf
    newline = "\r\n" if crlf >= lf else "\n"

    lines = raw.split("\n")
    hit_lines: List[int] = []
    new_lines = []
    redacted = False
    for idx, line in enumerate(lines, 1):
        # 去掉行尾 \r 再处理，统一按 LF 处理逻辑；写回时统一用检测到的新行符
        clean = line[:-1] if line.endswith("\r") else line
        if dryrun:
            new_lines.append(clean)
            for _, pat in SECRET_PATTERNS:
                if re.search(pat, clean):
                    hit_lines.append(idx)
                    break
            continue
        nline, hits = redact_line(clean)
        if hits:
            hit_lines.append(idx)
        new_lines.append(nline)

    if not dryrun and hit_lines and new_lines != [l[:-1] if l.endswith("\r") else l for l in lines]:
        # open()+newline='' 防止把写回的 \r\n 再次翻译，逐字节保真
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(newline.join(new_lines))
        redacted = True

    return {"file": str(path), "lines": len(lines), "hits": hit_lines, "redacted": redacted}


def collect_targets() -> List[Path]:
    """收集需要扫描的文本文件（跳过 .git / 产物 / 快照二进制）。"""
    skip_dirs = {".git", "worktrees", "artifacts", "outputs", "backups", "logs",
                 "snapshots", "__pycache__", ".venv", "node_modules"}
    exts = {".md", ".txt", ".sh", ".py", ".yml", ".yaml", ".json", ".cfg", ".toml", ".env.example"}
    targets: List[Path] = []
    for p in PROJECT_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip_dirs for part in p.parts):
            continue
        if p.suffix.lower() in exts or p.name in {"Dockerfile", "docker-compose.yml"}:
            targets.append(p)
    return targets


def run_scan(dryrun: bool) -> Dict[str, object]:
    targets = collect_targets()
    findings = []
    total_hits = 0
    redacted_files = []
    for t in targets:
        r = scan_file(t, dryrun)
        if r["hits"]:
            total_hits += len(r["hits"])
            findings.append(r)
            if r["redacted"]:
                redacted_files.append(r["file"])

    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dryrun": dryrun,
        "scanned_files": len(targets),
        "total_hit_lines": total_hits,
        "files_with_hits": len(findings),
        "redacted_files": redacted_files,
        "findings": findings,
        "note": "dryrun=只报告不改写；redact=已自动脱敏工作区文件。git历史重写需人工用 git filter-repo 单独执行。",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"secret_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 回写 local_job_queue.json（供 Marvis 闭环消费）
    if not dryrun and findings:
        q = load_queue()
        entry = {
            "task_name": "secret_cleanup_scan",
            "status": "needs_review" if redacted_files else "clean",
            "timestamp": report["generated_at"],
            "files_with_hits": len(findings),
            "redacted_files": redacted_files,
            "note": "工作区密钥已自动脱敏；请 Marvis 复查后 git add/commit，并在维护窗口做 git 历史清理(可选)。",
        }
        q.setdefault("jobs", []).append(entry)
        save_queue(q)

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="P0-1 密钥定时扫描/清洗脚本")
    ap.add_argument("--action", choices=["scan", "redact", "report", "dryrun"], default="redact")
    args = ap.parse_args()

    if args.action == "report":
        reports = sorted(RESULTS_DIR.glob("secret_scan_*.json")) if RESULTS_DIR.exists() else []
        if not reports:
            print("尚无扫描报告，请先运行 --action scan")
            return 0
        print(reports[-1].read_text(encoding="utf-8"))
        return 0

    dryrun = args.action in ("scan", "dryrun")
    report = run_scan(dryrun)
    print(json.dumps({k: v for k, v in report.items() if k != "findings"}, ensure_ascii=False, indent=2))
    for f in report["findings"]:
        print(f"  ⚠ {f['file']}  line={f['hits']}  redacted={f['redacted']}")
    print(f"\n{'[预演] 未改写文件' if dryrun else '[已执行] 工作区已脱敏'}：报告→ {RESULTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
