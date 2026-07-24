#!/bin/bash
# ============================================================
# 路线 3：无限轮询批量接单模式
# 适用场景：企业微信群持续涌入多单，三 Agent 常驻后台，自动排队处理。
#
# 使用方法：
#   1. 在项目根目录启动 autopilot daemon（批量调度）：
#        python scripts/pipeline_autopilot_daemon.py
#   2. 在三个 ORCA 工作树终端分别执行：
#        Hermes worktree:  bash scripts/route_3_batch_daemon.sh
#        Codex worktree:   bash scripts/route_3_batch_daemon.sh
#        CloudCode worktree: bash scripts/route_3_batch_daemon.sh
#   3. 各 Agent 会永久轮询 incoming/，有新任务立即认领，无需人工切换。
#
# 停止：按 Ctrl+C 或关闭对应工作树终端。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

AGENT="${1:-}"
if [ -z "$AGENT" ]; then
  if [[ "${ORCA_AGENT_NAME:-}" == "hermes" ]]; then
    AGENT="Hermes"
  elif [[ "${ORCA_AGENT_NAME:-}" == "codex" ]]; then
    AGENT="Codex"
  elif [[ "${ORCA_AGENT_NAME:-}" == "claude" ]]; then
    AGENT="CloudCode"
  else
    CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    if [[ "$CURRENT_BRANCH" == "hermes/brain" ]]; then
      AGENT="Hermes"
    elif [[ "$CURRENT_BRANCH" == "codex/executor" ]]; then
      AGENT="Codex"
    elif [[ "$CURRENT_BRANCH" == "claude/reviewer" ]]; then
      AGENT="CloudCode"
    fi
  fi
fi

if [ -z "$AGENT" ]; then
  echo "[ERROR] 无法判断当前 Agent。请手动指定：bash scripts/route_3_batch_daemon.sh <Hermes|Codex|CloudCode>"
  exit 1
fi

echo "[ROUTE-3] 启动无限轮询批量接单模式，Agent=${AGENT}"
echo "[ROUTE-3] 轮询间隔 30 秒，timeout=0（永不退出）"
echo "[ROUTE-3] 按 Ctrl+C 停止"

export ORCA_AGENT_NAME=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')
bash "$SCRIPT_DIR/fleet_pull.sh" auto 30 0
