#!/bin/bash
# ============================================================
# 项目本地舰队结果回写脚本（v2.1）
# 路径：scripts/fleet_done.sh
# 用法：bash scripts/fleet_done.sh "<WORKING_FILE>" "<结果文本>"
# 说明：
#   1. 将结果摘要写入 fleet_exchange/results/
#   2. 将原始任务文件归档到 fleet_exchange/done/
#   3. 自动把 WORKING_FILE 同目录下的产物（outputs/任务ID/ 下）整理归档到 G 盘
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

EX="$PROJECT_ROOT/fleet_exchange"
DO="$EX/doing"
DN="$EX/done"
RS="$EX/results"
LOG="$EX/logs"

G_DRIVE_ROOT="${G_DRIVE_ROOT:-G:/WorkBuddy-Cache/企业微信群定制接单项目}"
G_OUTPUTS="$G_DRIVE_ROOT/outputs"
G_LOGS="$G_DRIVE_ROOT/logs"

mkdir -p "$DO" "$DN" "$RS" "$LOG"
mkdir -p "$G_OUTPUTS" "$G_LOGS" 2>/dev/null || true

if [ $# -lt 2 ]; then
  echo "[ERROR] 用法: bash scripts/fleet_done.sh \"<WORKING_FILE>\" \"<结果文本>\""
  echo "[HINT] WORKING_FILE 通常是 fleet_exchange/doing/ 下的文件路径"
  exit 1
fi

WF="$1"
shift
RESULT="$*"

if [ ! -f "$WF" ]; then
  echo "[ERROR] 工作文件不存在: $WF"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
BASENAME=$(basename "$WF" .md)

# 提取 task_id（前段）
TASK_ID=$(echo "$BASENAME" | grep -oE '^[0-9]{8}_[0-9]{6}_[0-9]+' || echo "$BASENAME")

# 写结果文件
RESULT_FILE="$RS/${BASENAME}__result_${TS}.md"
printf '%s\n' "$RESULT" > "$RESULT_FILE"

# 归档任务到 done/
DONE_FILE="$DN/${BASENAME}__${TS}.md"
mv "$WF" "$DONE_FILE"

# 自动将当前任务产物目录同步到 G 盘（如果存在）
E_SRC="$PROJECT_ROOT/outputs/$TASK_ID"
G_DST="$G_OUTPUTS/$TASK_ID"
if [ -d "$E_SRC" ]; then
  mkdir -p "$G_DST" 2>/dev/null || true
  if [ -d "$G_DST" ]; then
    cp -r "$E_SRC"/* "$G_DST"/ 2>/dev/null || true
    echo "[ARCHIVED] 产物已镜像到 G 盘: $G_DST"
  fi
fi

echo "[TASK_COMPLETED] $BASENAME"
echo "[RESULT_FILE] $RESULT_FILE"
echo "[DONE_FILE] $DONE_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] DONE $BASENAME -> done/ + results/" >> "$LOG/ops_$(date +%Y%m%d).log"
