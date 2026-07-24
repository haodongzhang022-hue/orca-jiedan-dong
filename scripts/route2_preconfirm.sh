#!/bin/bash
# ============================================================
# 路线2：前置确认模式（需求模糊时使用）
# 解析需求卡 → 生成确认清单 → 等待用户确认后再启动流水线
# 用法：bash scripts/route2_preconfirm.sh <任务卡路径>
# ============================================================
set -euo pipefail

PROJECT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
EX="$PROJECT/fleet_exchange"
OUTPUTS="$PROJECT/outputs"

TASK_FILE="$1"
if [ -z "$TASK_FILE" ] || [ ! -f "$TASK_FILE" ]; then
  echo "[ERROR] 用法: bash scripts/route2_preconfirm.sh <任务卡路径>"
  exit 1
fi

TASK_ID=$(grep '^task_id:' "$TASK_FILE" | head -1 | sed 's/task_id: *//')
if [ -z "$TASK_ID" ]; then
  TASK_ID=$(basename "$TASK_FILE" | cut -d'_' -f1-2)
fi

echo "========================================="
echo "路线2：前置确认模式"
echo "任务ID: $TASK_ID"
echo "========================================="

# 提取待确认事项
echo ""
echo "📋 需求卡中的待确认事项："
echo "---"
grep -A 20 "待确认" "$TASK_FILE" 2>/dev/null || echo "(未找到待确认段落)"
echo "---"

# 提取报价信息
echo ""
echo "💰 报价信息："
grep -iE "(报价|到手|零售|价格)" "$TASK_FILE" 2>/dev/null || echo "(未找到报价信息)"

# 提取交付格式
echo ""
echo "📦 交付要求："
grep -iE "(格式|交付|\.ai|\.psd|\.pdf)" "$TASK_FILE" 2>/dev/null || echo "(未找到交付格式)"

echo ""
echo "========================================="
echo "请完成以下步骤："
echo "1. 与客户确认上述待确认事项"
echo "2. 确认无误后，运行路线1启动流水线："
echo "   bash scripts/route1_fullauto.sh \"$TASK_FILE\""
echo ""
echo "或直接标记已确认并启动："
echo "   bash scripts/route2_preconfirm.sh \"$TASK_FILE\" --confirm"
echo "========================================="

# 如果传入 --confirm 参数，直接启动流水线
if [ "${2:-}" == "--confirm" ]; then
  echo ""
  echo "[CONFIRMED] 用户已确认，启动全自动流水线..."
  bash "$SCRIPTS/route1_fullauto.sh" "$TASK_FILE"
fi
