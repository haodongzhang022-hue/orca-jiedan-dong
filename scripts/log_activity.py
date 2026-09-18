#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/log_activity.py
龙虾·活动流留痕系统 (v1.0 · 2026-08-20)

功能：
  append-only JSONL 文件 .workbuddy/activity_stream.jsonl
  每条活动：{ts, agent, channel, action, evidence, status}

调用方式（任意脚本都能留痕）：
  python log_activity.py <agent> <channel> <action> <evidence> [status]

例：
  python log_activity.py hermes local "接单建档" "舔屏杂志6月刊·96元" ok
  python log_activity.py codex direct "写入文件" "01_正在执行实单/.../任务卡.md (B)" ok

五通道枚举（channel 字段）：
  direct   = 直接调（本机脚本/python/bash）
  hermes   = Hermes Studio CLI
  harness  = DeepSeek Harness (CNB容器 端口8080)
  orca     = ORCA多智能体舰队 (msgbus)
  cnb      = CNB云端仓库 (git push)

零成本 · 零网络 · 仅文件 append
"""
import json
import os
import sys
import datetime

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy",
    "activity_stream.jsonl"
)

VALID_AGENTS = ["hermes", "codex", "claude", "deepseek", "operator", "system"]
VALID_CHANNELS = ["direct", "hermes", "harness", "orca", "cnb", "marvis", "miMo", "ollama"]


def now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    if len(sys.argv) < 5:
        print("用法: python log_activity.py <agent> <channel> <action> <evidence> [status]")
        print("例:   python log_activity.py hermes direct '接单建档' '舔屏杂志6月刊·96元' ok")
        sys.exit(1)

    agent = sys.argv[1].lower()
    channel = sys.argv[2].lower()
    action = sys.argv[3]
    evidence = sys.argv[4]
    status = sys.argv[5] if len(sys.argv) > 5 else "ok"

    if agent not in VALID_AGENTS:
        agent = "operator"
    if channel not in VALID_CHANNELS:
        channel = "direct"

    rec = {
        "ts": now(),
        "agent": agent,
        "channel": channel,
        "action": action,
        "evidence": evidence,
        "status": status,
    }

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 标准输出也能看到（便于 bash 串联）
    print(f"📡 [{rec['ts']}] {agent}·{channel}: {action} → {evidence} [{status}]")


if __name__ == "__main__":
    main()
