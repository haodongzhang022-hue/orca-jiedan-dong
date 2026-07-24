#!/bin/bash
# ============================================================
# 路线3：自动轮询模式（批量来单场景）
# 持续扫描 fleet_exchange/incoming，有新单自动认领处理
# 用法：bash scripts/route3_autopoll.sh [扫描间隔秒] [超时退出秒]
# 默认：每30秒扫描，连续10分钟无任务自动退出
# ============================================================
set -euo pipefail

PROJECT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
SCRIPTS="$PROJECT/scripts"
EX="$PROJECT/fleet_exchange"
IN="$EX/incoming"
DO="$EX/doing"
RS="$EX/results"
LOG="$EX/logs"

mkdir -p "$IN" "$DO" "$RS" "$LOG"

INTERVAL="${1:-30}"
TIMEOUT="${2:-600}"

echo "========================================="
echo "路线3：自动轮询模式"
echo "扫描间隔: ${INTERVAL}s | 超时退出: ${TIMEOUT}s"
echo "扫描目录: $IN"
echo "========================================="

idle_count=0
processed=0

while true; do
  # 扫描 incoming 中的任务卡
  found=""
  for f in $(ls -1t "$IN"/*.md 2>/dev/null | head -50); do
    fname=$(basename "$f")
    # 检查是否是 Hermes 任务（文件名含 _Hermes_ 或 frontmatter to: Hermes）
    to_agent=""
    if head -1 "$f" 2>/dev/null | grep -q '^---'; then
      to_agent=$(sed -n '/^---$/,/^---$/p' "$f" 2>/dev/null | grep -E '^to:' | sed 's/^to: *//' | head -1)
    fi
    if [[ "$fname" =~ _Hermes_ ]] || [ "$to_agent" == "Hermes" ]; then
      found="$f"
      break
    fi
  done

  if [ -z "$found" ]; then
    echo "[$(date '+%H:%M:%S')] 无新任务，等待 ${INTERVAL}s..."
    idle_count=$((idle_count + INTERVAL))
    if [ "$idle_count" -ge "$TIMEOUT" ]; then
      echo "[EXIT] 连续 ${TIMEOUT}s 无新任务，已处理 $processed 个任务，退出"
      exit 0
    fi
    sleep "$INTERVAL"
    continue
  fi

  # 认领任务
  idle_count=0
  task=$(basename "$found")
  task_id=$(grep '^task_id:' "$found" | head -1 | sed 's/task_id: *//')
  if [ -z "$task_id" ]; then
    task_id=$(echo "$task" | cut -d'_' -f1-2)
  fi

  echo ""
  echo "========================================="
  echo "[NEW ORDER] $task"
  echo "任务ID: $task_id"
  echo "========================================="

  # 保存截图到输出目录（如果有）
  mkdir -p "$OUTPUTS/$task_id"
  cp "$found" "$OUTPUTS/$task_id/任务卡.md" 2>/dev/null || true

  # 运行流水线自动驾驶
  echo "[PIPELINE] 启动流水线处理 $task_id..."
  cd "$PROJECT"
  python scripts/pipeline_autopilot.py

  processed=$((processed + 1))
  echo "[DONE] $task_id 已进入流水线 (累计处理: $processed)"

  # 继续扫描
  sleep "$INTERVAL"
done
