#!/bin/bash
# ============================================================
# 项目本地舰队任务拉取脚本（v2.2）
# 路径：scripts/fleet_pull.sh
# 用法：
#   bash scripts/fleet_pull.sh                       # 手动拉取一次
#   bash scripts/fleet_pull.sh auto 30 600           # 每30秒扫描，连续10分钟无任务退出
#   bash scripts/fleet_pull.sh auto 30 0               # 每30秒扫描，永不退出（批量接单模式）
#   bash scripts/fleet_pull.sh auto 30 600 <Hermes>    # 显式指定 Agent
# ============================================================
set -euo pipefail

# 自动定位项目根目录（脚本位于 scripts/ 下）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

EX="$PROJECT_ROOT/fleet_exchange"
IN="$EX/incoming"
DO="$EX/doing"
RS="$EX/results"
LOG="$EX/logs"

mkdir -p "$IN" "$DO" "$RS" "$LOG"

MODE="${1:-manual}"
INTERVAL="${2:-30}"
TIMEOUT="${3:-600}"

AGENT_NAME=""
# 优先读取 ORCA_AGENT_NAME 环境变量
if [[ "${ORCA_AGENT_NAME:-}" == "hermes" ]]; then
  AGENT_NAME="Hermes"
elif [[ "${ORCA_AGENT_NAME:-}" == "codex" ]]; then
  AGENT_NAME="Codex"
elif [[ "${ORCA_AGENT_NAME:-}" == "claude" ]]; then
  AGENT_NAME="CloudCode"
fi

# 其次根据当前 git 分支判断（ORCA worktree 分支通常是 hermes/brain 等）
if [ -z "$AGENT_NAME" ]; then
  CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ "$CURRENT_BRANCH" == "hermes/brain" ]]; then
    AGENT_NAME="Hermes"
  elif [[ "$CURRENT_BRANCH" == "codex/executor" ]]; then
    AGENT_NAME="Codex"
  elif [[ "$CURRENT_BRANCH" == "claude/reviewer" ]]; then
    AGENT_NAME="CloudCode"
  fi
fi

# 如果无法自动判断，要求传入
if [ -z "$AGENT_NAME" ]; then
  AGENT_NAME="${4:-}"
  if [ -z "$AGENT_NAME" ]; then
    echo "[ERROR] 无法判断当前 Agent。请手动指定：bash scripts/fleet_pull.sh [auto] [interval] [timeout] <Hermes|Codex|CloudCode>"
    exit 1
  fi
fi

idle_count=0

while true; do
  found=""
  for f in $(ls -1t "$IN"/*.md 2>/dev/null | head -50); do
    fname=$(basename "$f")
    to_agent=""
    if head -1 "$f" 2>/dev/null | grep -q '^---'; then
      to_agent=$(sed -n '/^---$/,/^---$/p' "$f" 2>/dev/null | grep -E '^to:' | sed 's/^to: *//' | head -1)
    fi
    if [[ "$fname" =~ _${AGENT_NAME}_ ]] || [[ "$fname" =~ _${AGENT_NAME}\. ]] || [ "$to_agent" == "$AGENT_NAME" ]; then
      found="$f"
      break
    fi
  done

  if [ -z "$found" ]; then
    echo "[PULL] $(date '+%Y-%m-%d %H:%M:%S') 无 $AGENT_NAME 任务，等待 ${INTERVAL}s"
    if [ "$MODE" == "auto" ]; then
      idle_count=$((idle_count + INTERVAL))
      if [ "$TIMEOUT" -gt 0 ] && [ "$idle_count" -ge "$TIMEOUT" ]; then
        echo "[PULL] 连续 ${TIMEOUT}s 无任务，退出"
        exit 0
      fi
      sleep "$INTERVAL"
      continue
    else
      exit 0
    fi
  fi

  idle_count=0
  task=$(basename "$found")
  target="$DO/$task"
  mv "$found" "$target"
  echo "[CLAIMED] $task"
  echo "[WORKING_FILE] $target"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] CLAIM $task -> doing/" >> "$LOG/ops_$(date +%Y%m%d).log"

  if [ "$MODE" == "manual" ]; then
    exit 0
  fi
  sleep "$INTERVAL"
done
