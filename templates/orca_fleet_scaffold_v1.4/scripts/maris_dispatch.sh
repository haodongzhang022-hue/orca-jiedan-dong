#!/usr/bin/env bash
# =============================================================================
# Maris 一键投递任务卡到舰队（脚手架 v1.4 通用版）
# -----------------------------------------------------------------------------
# 用途：让 Maris / 任意调度端一键把任务写进 fleet_exchange/incoming/，
#       触发 codex / claude-code / CodeBuddy 接单
# 用法：
#   bash scripts/maris_dispatch.sh "朋友圈餐饮海报，露营烤肉套餐198元"
#   bash scripts/maris_dispatch.sh --type poster --desc "开业大吉" --price 300
# =============================================================================

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INCOMING="$ROOT/fleet_exchange/incoming"
mkdir -p "$INCOMING"

# 参数解析
TYPE="task"
DESC=""
PRICE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --type) TYPE="$2"; shift 2;;
    --desc) DESC="$2"; shift 2;;
    --price) PRICE="$2"; shift 2;;
    -h|--help)
      echo "用法: bash scripts/maris_dispatch.sh [--type 类型] [--desc 描述] [--price 报价]"
      echo "示例: bash scripts/maris_dispatch.sh \"朋友圈海报需求描述\""
      exit 0;;
    *) DESC="$1"; shift;;
  esac
done

if [ -z "$DESC" ]; then
  echo "❌ 请提供任务描述"
  exit 1
fi

# 生成任务卡
TASK_ID="TASK-$(date +%Y%m%d)-$(date +%H%M%S)"
cat > "$INCOMING/$TASK_ID.md" << EOF
---
task_id: $TASK_ID
from: maris
to: fleet
pipeline: route_1_auto_pipeline
simulation: false
created_at: $(date '+%Y-%m-%d %H:%M:%S')
type: $TYPE
price: ${PRICE:-未定}
---

# $TASK_ID

## 需求描述
$DESC

## 期望交付物
- [ ] 初稿（fleet_exchange/doing/）
- [ ] 审核通过（fleet_exchange/done/）
- [ ] 最终结果（fleet_exchange/results/）
EOF

echo "✅ 任务卡已投递: $INCOMING/$TASK_ID.md"
echo "   Codex/Claude Code/CodeBuddy 将自动接单处理"
echo "   查看状态: ls $INCOMING"
