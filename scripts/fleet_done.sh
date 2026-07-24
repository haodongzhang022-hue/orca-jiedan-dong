#!/bin/bash
# ============================================================
# 项目本地舰队结果回写脚本（v2.0）
# 路径：E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/scripts/fleet_done.sh
# 用法：bash scripts/fleet_done.sh "<WORKING_FILE>" "<结果文本>"
# ============================================================
set -euo pipefail

EX="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/fleet_exchange"
DO="$EX/doing"
DN="$EX/done"
RS="$EX/results"
LOG="$EX/logs"

mkdir -p "$DO" "$DN" "$RS" "$LOG"

WF="$1"
shift
RESULT="$*"

if [ -z "$WF" ] || [ ! -f "$WF" ]; then
  echo "[ERROR] 用法: bash scripts/fleet_done.sh \"<WORKING_FILE>\" \"<结果文本>\""
  echo "[HINT] WORKING_FILE 通常是 fleet_exchange/doing/ 下的文件路径"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
BASENAME=$(basename "$WF" .md)

# 写结果文件
printf '%s\n' "$RESULT" > "$RS/${BASENAME}__result_${TS}.md"

# 归档任务到 done/
mv "$WF" "$DN/${BASENAME}__${TS}.md"

echo "[TASK_COMPLETED] $BASENAME"
echo "[RESULT_FILE] $RS/${BASENAME}__result_${TS}.md"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] DONE $BASENAME -> done/ + results/" >> "$LOG/ops_$(date +%Y%m%d).log"
