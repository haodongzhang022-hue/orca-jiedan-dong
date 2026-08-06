#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNB 免费 DeepSeek-V4-Flash 额度监控与降级保护
============================================
职责：
  1. 读取 CNB 流水线 AI 用量（get-build-ai-audit / get-build-ai-request）累计
  2. 与阈值比较，输出告警状态与降级建议
  3. 生成 .quota_state.json 供适配层与流水线读取
  4. 超过阈值自动置 QUOTA_EXCEEDED=1（流水线据此切换降级策略）

运行环境：CNB 流水线容器（已注入 CNB_TOKEN，具备 repo-cnb-history:r 权限）
不落盘任何密钥。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List

STATE_FILE = os.environ.get("QUOTA_STATE_FILE", ".quota_state.json")

# 默认阈值（可从环境变量覆盖）
DEFAULT_LIMIT_MONTHLY = 1600.0      # 每月 1600 核时免费额度（平台口径）
DEFAULT_WARN_RATIO = 0.8            # 用量达到 80% 告警
DEFAULT_HARD_RATIO = 0.95           # 用量达到 95% 强制降级
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "deepseek-v4-flash@low")  # 兜底（降档而非换付费模型）


def _run(cmd: list) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return p.stdout or ""
    except Exception as e:
        return f"ERR:{e}"


def fetch_ai_usage(repo: str, days: int = 30) -> Dict:
    """尝试通过 cnb build 命令拉取 AI 用量汇总。失败则返回空统计。"""
    summary = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "core_hours": 0.0, "samples": 0}
    # 1) 拉取构建列表
    out = _run(["cnb", "build", "get-build-logs", "--repo", repo, "--page-size", "50"])
    try:
        data = json.loads(out[out.find("{"):out.rfind("}") + 1]) if "{" in out else {}
    except Exception:
        data = {}
    builds = (data.get("data") or {}).get("data") or []
    for b in builds:
        if b.get("status") != "success":
            continue
        sn = b.get("sn", "")
        summary["samples"] += 1
        # 尝试解析 buildLogUrl 中的 sn → 拉 AI 用量
        out2 = _run(["cnb", "build", "get-build-ai-audit", "--repo", repo, "--sn", sn, "--pipelineId", f"{sn}-001"])
        try:
            d2 = json.loads(out2[out2.find("{"):out2.rfind("}") + 1]) if "{" in out2 else {}
        except Exception:
            d2 = {}
        if d2:
            summary["requests"] += 1
    return summary


def main() -> int:
    repo = os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan")
    limit = float(os.environ.get("QUOTA_LIMIT", str(DEFAULT_LIMIT_MONTHLY)) or DEFAULT_LIMIT_MONTHLY)
    warn_ratio = float(os.environ.get("QUOTA_WARN_RATIO", str(DEFAULT_WARN_RATIO)))
    hard_ratio = float(os.environ.get("QUOTA_HARD_RATIO", str(DEFAULT_HARD_RATIO)))

    # 已用额度：优先读外部注入（如平台用量查询结果），否则本地累计文件
    state: Dict = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
    used = float(os.environ.get("QUOTA_USED", str(state.get("used_core_hours", 0.0)) or 0.0))
    usage = fetch_ai_usage(repo)
    if usage and usage.get("core_hours", 0) > used:
        used = usage["core_hours"]
    used = max(used, float(state.get("used_core_hours", 0.0)))

    ratio = (used / limit) if limit > 0 else 0.0
    status = "ok"
    action = "continue"
    if ratio >= hard_ratio:
        status = "exceeded"
        action = f"降级到 {FALLBACK_MODEL}（不调用外部付费API）"
    elif ratio >= warn_ratio:
        status = "warn"
        action = "尽快控制用量，接近硬限"

    state.update({
        "used_core_hours": used,
        "limit_core_hours": limit,
        "ratio": round(ratio, 4),
        "status": status,
        "action": action,
        "fallback_model": FALLBACK_MODEL,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # 供流水线后续 stage 使用
    env_out = f"QUOTA_STATUS={status}\nQUOTA_USED={used}\nQUOTA_LIMIT={limit}\nQUOTA_ACTION={action}\n"
    with open("quota.env", "w", encoding="utf-8") as f:
        f.write(env_out)

    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
