#!/bin/bash
# ============================================================
# 舰队任务交换区 v2.0 - WorkBuddy 主动推送任务（调度中枢侧）
#
# 位置：E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/
# 用法：bash <本脚本> "<任务标题>" "<目标Agent>" "<优先级>" "<中文指令内容>"
# 示例：bash fleet_push.sh "回测EA" "Codex" "normal" "运行ea_gold_dark_horse.mq5回测2024年数据"
#
# 推送后 Agent 通过 fleet_pull.sh (auto模式) 自动拉取，无需人工中转
# ============================================================
EX="E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange"
IN="$EX/incoming"
LOG="$EX/logs"
mkdir -p "$IN" "$LOG"

TITLE="$1"
TO="${2:-any}"
PRIORITY="${3:-normal}"
shift 3
CONTENT="$*"

if [ -z "$TITLE" ] || [ -z "$CONTENT" ]; then
  echo "[ERROR] 用法: bash \"$EX/fleet_push.sh\" \"<标题>\" <目标Agent> <优先级> \"<指令内容>\""
  echo "  目标Agent: any | Hermes | Codex | ClaudeCode"
  echo "  优先级: low | normal | high"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
SEQ=$(ls "$IN/" 2>/dev/null | wc -l)
TASK_FILE="$IN/${TS}_${SEQ}__$(echo "$TITLE" | tr ' /' '_').md"

# 写入标准格式任务文件
cat > "$TASK_FILE" <<EOF
---
task_id: ${TS}_${SEQ}
from: WorkBuddy
to: $TO
priority: $PRIORITY
created: $(date '+%Y-%m-%d %H:%M:%S')
context: $TITLE
---

# 任务：$TITLE

$CONTENT

## 验收标准
- [ ] 执行无报错
- [ ] 结果写回 results/
- [ ] 符合预期输出
EOF

echo "[TASK_PUSHED] $TASK_FILE"
echo "[TARGET] $TO | PRIORITY: $PRIORITY"
echo "[NEXT] Agent 将通过 fleet_pull.sh auto 自动拉取此任务"
echo ""
echo "--- 任务预览 ---"
cat "$TASK_FILE"

# 日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PUSH $TASK_FILE → incoming/ target=$TO priority=$PRIORITY" >> "$LOG/ops_$(date +%Y%m%d).log"
