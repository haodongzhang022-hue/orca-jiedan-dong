#!/usr/bin/env bash
# ==============================================================================
# Maris 调度分发脚本 — 将任务卡写入 fleet_exchange/incoming/
# ==============================================================================
# 用法：
#   bash scripts/maris_dispatch.sh --type <文案|海报|视频|通用> --title "<任务标题>" --desc "<任务描述>"
#   bash scripts/maris_dispatch.sh --file <任务卡文件路径>
# 示例：
#   bash scripts/maris_dispatch.sh --type 文案 --title "朋友圈餐饮海报文案" --desc "露营风格，5条文案"
#   bash scripts/maris_dispatch.sh --file /tmp/my_task.md
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INCOMING_DIR="$PROJECT_ROOT/fleet_exchange/incoming"

mkdir -p "$INCOMING_DIR"

# ---- 参数解析 ----
TASK_TYPE="通用"
TASK_TITLE=""
TASK_DESC=""
TASK_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)   TASK_TYPE="$2"; shift 2 ;;
    --title)  TASK_TITLE="$2"; shift 2 ;;
    --desc)   TASK_DESC="$2"; shift 2 ;;
    --file)   TASK_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "用法: bash scripts/maris_dispatch.sh --type <类型> --title <标题> --desc <描述>"
      echo "      bash scripts/maris_dispatch.sh --file <任务卡路径>"
      echo ""
      echo "类型: 文案 | 海报 | 视频 | 通用"
      exit 0 ;;
    *) echo "[ERROR] 未知参数: $1"; exit 1 ;;
  esac
done

# ---- 文件模式：直接复制 ----
if [ -n "$TASK_FILE" ]; then
  if [ ! -f "$TASK_FILE" ]; then
    echo "[ERROR] 文件不存在: $TASK_FILE"
    exit 1
  fi
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  DEST="$INCOMING_DIR/${TIMESTAMP}_Maris_$(basename "$TASK_FILE")"
  cp "$TASK_FILE" "$DEST"
  echo "[DISPATCHED] 文件模式 → $DEST"
  exit 0
fi

# ---- 参数模式：生成任务卡 ----
if [ -z "$TASK_TITLE" ]; then
  echo "[ERROR] 必须提供 --title 或 --file"
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TASK_ID="${TIMESTAMP}_0"
SAFE_TITLE=$(echo "$TASK_TITLE" | tr ' ' '_' | sed 's/[^a-zA-Z0-9_\x80-\xff]//g')
TASK_FILE_NAME="${TASK_ID}__Maris_${SAFE_TITLE}.md"

cat > "$INCOMING_DIR/$TASK_FILE_NAME" <<TASK_CARD
# 任务卡
- task_id: ${TASK_ID}
- source: Maris
- type: ${TASK_TYPE}
- title: ${TASK_TITLE}
- created_at: $(date '+%Y-%m-%d %H:%M:%S')
- status: incoming

## 描述
${TASK_DESC:-（无详细描述）}

## 执行要求
- [ ] 按 ${TASK_TYPE} 类型标准执行
- [ ] 产出物写入 fleet_exchange/results/
- [ ] 完成后移入 fleet_exchange/done/

## 约束
- 禁止越权：仅执行本任务卡明确要求的内容
- 产出格式：Markdown 文档 + 可选附件
TASK_CARD

echo "[DISPATCHED] 参数模式 → $INCOMING_DIR/$TASK_FILE_NAME"
echo "  task_id: ${TASK_ID}"
echo "  type:    ${TASK_TYPE}"
echo "  title:   ${TASK_TITLE}"
