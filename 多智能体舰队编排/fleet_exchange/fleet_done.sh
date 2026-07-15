#!/bin/bash
# ============================================================
# 舰队任务交换区 v2.0 - 回写结果（Agent 侧）
#
# 新位置：E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/
# 用法：bash <本脚本> "<WORKING_FILE>" "<结果文本>"
# ============================================================
EX="E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange"
DO="$EX/doing"
DN="$EX/done"
RS="$EX/results"
LOG="$EX/logs"
WF="$1"
shift
RESULT="$*"

if [ -z "$WF" ] || [ ! -f "$WF" ]; then
  echo "[ERROR] 用法: bash \"$EX/fleet_done.sh\" \"<WORKING_FILE>\" \"<结果文本>\""
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

# 日志记录
echo "[$(date '+%Y-%m-%d %H:%M:%S')] DONE $BASENAME → done/ + results/" >> "$LOG/ops_$(date +%Y%m%d).log"
