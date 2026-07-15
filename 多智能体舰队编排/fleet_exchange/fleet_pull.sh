#!/bin/bash
# ============================================================
# 舰队任务交换区 v2.0 - 拉取任务 + 自动轮询（Agent 侧）
#
# 新位置：E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/
# 用法 1（手动单次）：bash <本脚本>
# 用法 2（自动轮询）：bash <本脚本> auto [间隔秒数，默认30]
# 升级点：v2.0 新增 auto 模式，后台定时扫描 incoming/ 自动认领
# ============================================================
EX="E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange"
IN="$EX/incoming"
DO="$EX/doing"
LOG="$EX/logs"
mkdir -p "$IN" "$DO" "$LOG"

# ---- 日志函数 ----
log_op() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG/ops_$(date +%Y%m%d).log"
}

# ---- 单次拉取核心逻辑 ----
pull_once() {
  TASK=$(ls -t "$IN"/*.md 2>/dev/null | tail -1)
  if [ -z "$TASK" ]; then
    echo "[NO_PENDING_TASK]"
    return 0
  fi
  TS=$(date +%Y%m%d_%H%M%S)
  NAME=$(basename "$TASK" .md)
  mv "$TASK" "$DO/${NAME}__${TS}.md"
  echo "=========================================="
  echo "[TASK_PULLED] $NAME  @ $TS"
  echo "=========================================="
  cat "$DO/${NAME}__${TS}.md"
  echo ""
  echo "[WORKING_FILE] $DO/${NAME}__${TS}.md"
  echo "[NEXT] 执行完后运行："
  echo "bash \"$EX/fleet_done.sh\" \"$DO/${NAME}__${TS}.md\" \"<你的结果摘要>\""
  log_op "PULL $NAME → doing/"
  return 1  # 有任务
}

# ---- 主入口 ----
if [ "$1" = "auto" ]; then
  INTERVAL=${2:-30}
  MAX_IDLE=${3:-600}  # 10分钟无任务自动退出
  echo "[AUTO_POLL] 启动自动轮询 | 间隔=${INTERVAL}s | 空闲超时=${MAX_IDLE}s"
  log_op "AUTO_POLL START interval=${INTER}s max_idle=${MAX_IDLE}s"
  IDLE_START=$(date +%s)
  while true; do
    if pull_once; then
      # 无任务，检查空闲超时
      NOW=$(date +%s)
      ELAPSED=$((NOW - IDLE_START))
      if [ "$ELAPSED" -ge "$MAX_IDLE" ]; then
        echo "[AUTO_POLL] 空闲 ${ELAPSED}s 达到上限，退出轮询"
        log_op "AUTO_POLL STOP idle_timeout elapsed=${ELAPSED}s"
        break
      fi
    else
      # 有任务被拉取，重置空闲计时器
      IDLE_START=$(date +%s)
    fi
    sleep "$INTERVAL"
  done
else
  pull_once
fi
