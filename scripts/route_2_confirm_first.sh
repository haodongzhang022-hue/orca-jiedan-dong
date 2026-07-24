#!/bin/bash
# ============================================================
# 路线 2：前置确认校验模式
# 适用场景：客户需求模糊（尺寸/结构/包装未确认），先让 Hermes 拆需求并暂停，
#          人工确认后再放行 Codex，避免返工。
#
# 使用方法：
#   1. Hermes worktree 执行一次（只处理当前 incoming 任务，不轮询）：
#        bash scripts/route_2_confirm_first.sh
#   2. Hermes 产出 design_brief 后，autopilot 在 CONFIRM_MODE 下会把 Codex 任务写入
#      待确认/ 目录，不自动进入 incoming。
#   3. 用户在 WorkBuddy / ORCA 中确认需求，然后放行：
#        bash scripts/confirm_task.sh <task_id>
#   4. 三个工作树切回路线 1：
#        bash scripts/route_1_auto_pipeline.sh
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
  echo "[ERROR] 无法判断当前 Agent。请手动指定：bash scripts/route_2_confirm_first.sh <Hermes|Codex|CloudCode>"
  exit 1
fi

if [ "$AGENT" != "Hermes" ]; then
  echo "[ROUTE-2] 当前 Agent 为 ${AGENT}，无需执行前置确认。"
  echo "[ROUTE-2] 请先用 Hermes 跑需求拆解，确认后再放行。"
  exit 0
fi

export ORCA_AGENT_NAME=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')
export CONFIRM_MODE=true

echo "[ROUTE-2] 启动前置确认模式，Agent=${AGENT}"
echo "[ROUTE-2] Hermes 只执行一次，产出 design_brief 后自动把 Codex 任务写入 待确认/"
echo "[ROUTE-2] 确认完成后请执行：bash scripts/confirm_task.sh <task_id>"

bash "$SCRIPT_DIR/fleet_pull.sh" manual
