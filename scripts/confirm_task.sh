#!/bin/bash
# ============================================================
# 待确认任务放行脚本
# 用法：
#   bash scripts/confirm_task.sh <task_id>
# 示例：
#   bash scripts/confirm_task.sh 20260725_232000_0
# 说明：
#   将 待确认/ 目录中指定 task_id 的 Codex / CloudCode 任务卡移入 incoming，
#   触发后续 Agent 自动接力。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TASK_ID="${1:-}"
if [ -z "$TASK_ID" ]; then
  echo "[ERROR] 用法: bash scripts/confirm_task.sh <task_id>"
  echo "[HINT] 可用的 task_id 列表："
  ls -1 "$PROJECT_ROOT/待确认"/*.md 2>/dev/null | grep -oE '[0-9]{8}_[0-9]{6}_[0-9]+' | sort -u || echo "  （无）"
  exit 1
fi

CONFIRM_DIR="$PROJECT_ROOT/待确认"
INCOMING_DIR="$PROJECT_ROOT/fleet_exchange/incoming"

mkdir -p "$CONFIRM_DIR" "$INCOMING_DIR"

found=0
for f in "$CONFIRM_DIR"/*.md; do
  [ -f "$f" ] || continue
  if [[ "$(basename "$f")" =~ ^${TASK_ID} ]]; then
    mv "$f" "$INCOMING_DIR/"
    echo "[CONFIRMED] $(basename "$f") -> incoming/"
    found=$((found + 1))
  fi
done

if [ "$found" -eq 0 ]; then
  echo "[WARN] 待确认目录中未找到 task_id=${TASK_ID} 的任务卡"
  echo "[HINT] 当前待确认任务："
  ls -1 "$CONFIRM_DIR"/*.md 2>/dev/null || echo "  （无）"
  exit 1
fi

echo "[CONFIRMED] 共放行 ${found} 个任务卡，现在可切回路线 1 或 3 继续自动接力"
