#!/bin/bash
# ============================================================
# 路线 1：全自动单订单流水线
# 适用场景：常规商单，信息已充分，直接跑通 Hermes -> Codex -> CloudCode
#
# 使用方法：
#   在三个 ORCA 工作树终端分别执行（脚本自动识别当前 Agent）：
#     Hermes worktree:  bash scripts/route_1_auto_pipeline.sh
#     Codex worktree:   bash scripts/route_1_auto_pipeline.sh
#     CloudCode worktree: bash scripts/route_1_auto_pipeline.sh
#
#   工作树外/手动指定 Agent：
#     bash scripts/route_1_auto_pipeline.sh <Hermes|Codex|CloudCode>
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
  echo "[ERROR] 无法判断当前 Agent。请手动指定：bash scripts/route_1_auto_pipeline.sh <Hermes|Codex|CloudCode>"
  exit 1
fi

echo "[ROUTE-1] 启动全自动单订单流水线，Agent=${AGENT}"
echo "[ROUTE-1] 轮询间隔 30 秒，连续 10 分钟无任务自动退出"
echo "[ROUTE-1] 确保项目根目录已启动 autopilot daemon："
echo "  python scripts/pipeline_autopilot_daemon.py"

export ORCA_AGENT_NAME=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')
bash "$SCRIPT_DIR/fleet_pull.sh" auto 30 600
