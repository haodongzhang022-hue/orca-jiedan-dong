#!/bin/bash
# ============================================================
# 路线1：全自动模式（推荐常规商单）
# 一键启动：Hermes 生成简报 → 自动推 Codex → 自动推 CloudCode
# 用法：bash scripts/route1_fullauto.sh <任务卡路径>
# 示例：bash scripts/route1_fullauto.sh fleet_exchange/incoming/20260725_232000_0__Hermes_金羊钥匙扣_可旋转金片_高级感.md
# ============================================================
set -euo pipefail

PROJECT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
SCRIPTS="$PROJECT/scripts"
EX="$PROJECT/fleet_exchange"
OUTPUTS="$PROJECT/outputs"

TASK_FILE="$1"
if [ -z "$TASK_FILE" ] || [ ! -f "$TASK_FILE" ]; then
  echo "[ERROR] 用法: bash scripts/route1_fullauto.sh <任务卡路径>"
  echo "[HINT]  任务卡位于 fleet_exchange/incoming/ 下"
  exit 1
fi

TASK_ID=$(grep '^task_id:' "$TASK_FILE" | head -1 | sed 's/task_id: *//')
if [ -z "$TASK_ID" ]; then
  TASK_ID=$(basename "$TASK_FILE" | cut -d'_' -f1-2)
fi

echo "========================================="
echo "路线1：全自动模式"
echo "任务ID: $TASK_ID"
echo "任务卡: $(basename "$TASK_FILE")"
echo "========================================="

# Step 0: 自动归档初始化
echo "[ARCHIVE] 初始化任务目录..."
python "$SCRIPTS/auto_archive.py" init "$TASK_FILE"

# Step 1: 运行 pipeline_autopilot（自动检测 Hermes 结果并推 Codex/CloudCode）
echo ""
echo "[Step 1/3] 启动流水线自动驾驶..."
cd "$PROJECT"
python scripts/pipeline_autopilot.py

echo ""
echo "[Step 2/3] 启动后台守护进程（每30秒自动检查推进）..."
# 守护进程会在后台持续运行，自动推进后续阶段
nohup python scripts/pipeline_autopilot_daemon.py > logs/route1_daemon_${TASK_ID}.log 2>&1 &
DAEMON_PID=$!
echo "[DAEMON] PID=$DAEMON_PID, 日志: logs/route1_daemon_${TASK_ID}.log"

echo ""
echo "[Step 3/3] 流水线已启动"
echo "========================================="
echo "后续自动流程："
echo "  Hermes 完成 → 自动推 Codex 任务"
echo "  Codex 完成 → 自动推 CloudCode 任务"
echo "  CloudCode 完成 → 自动汇总交付物"
echo ""
echo "监控命令："
echo "  tail -f logs/route1_daemon_${TASK_ID}.log"
echo "  python scripts/pipeline_autopilot.py  # 手动触发一次检查"
echo "========================================="
