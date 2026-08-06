#!/usr/bin/env bash
# =============================================================================
# Maris 任务投递调度脚本
# 用途：Maris 通过此脚本将任务卡写入 fleet_exchange/incoming/ 目录
# 用法：bash scripts/maris_dispatch.sh --type "文案" --title "任务标题" [--desc "描述"] [--priority "中"] [--deadline "2026-08-10"]
# =============================================================================
set -euo pipefail

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INCOMING_DIR="$PROJECT_ROOT/fleet_exchange/incoming"

# 默认参数
TASK_TYPE="${TASK_TYPE:-文案}"
TASK_TITLE="${TASK_TITLE:-}"
TASK_DESC="${TASK_DESC:-}"
TASK_PRIORITY="${TASK_PRIORITY:-中}"
TASK_DEADLINE="${TASK_DEADLINE:-}"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)   TASK_TYPE="$2"; shift 2 ;;
    --title)  TASK_TITLE="$2"; shift 2 ;;
    --desc)   TASK_DESC="$2"; shift 2 ;;
    --priority) TASK_PRIORITY="$2"; shift 2 ;;
    --deadline) TASK_DEADLINE="$2"; shift 2 ;;
    *) echo "[错误] 未知参数: $1"; exit 1 ;;
  esac
done

# 校验必填参数
if [ -z "$TASK_TITLE" ]; then
  echo "[错误] --title 为必填参数"
  echo "用法: bash scripts/maris_dispatch.sh --type \"文案\" --title \"任务标题\""
  exit 1
fi

# 确保目录存在
mkdir -p "$INCOMING_DIR"

# 生成任务ID（格式：YYYYMMDD_HHMMSS_N）
TASK_ID=$(date +%Y%m%d_%H%M%S)_0
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 安全文件名（去除特殊字符）
SAFE_TITLE=$(echo "$TASK_TITLE" | tr ' ' '_' | tr -cd '[:alnum:]_\u4e00-\u9fff')

# 生成 Markdown 任务卡
TASK_FILE="$INCOMING_DIR/${TASK_ID}__Maris_${SAFE_TITLE}.md"

cat > "$TASK_FILE" << EOF
# 任务卡：${TASK_TITLE}

- 任务ID: ${TASK_ID}
- 类型: ${TASK_TYPE}
- 优先级: ${TASK_PRIORITY}
- 来源: Maris
- 创建时间: ${TIMESTAMP}
$( [ -n "$TASK_DEADLINE" ] && echo "- 截止日期: ${TASK_DEADLINE}" || true )

## 需求
${TASK_DESC:-（待补充）}

## 要求
- 中文输出
- 按照类型标准交付
EOF

# 同时生成 JSON 格式（供程序化消费）
JSON_FILE="$INCOMING_DIR/PKT_${TASK_ID}.json"
cat > "$JSON_FILE" << EOF
{
  "task_id": "${TASK_ID}",
  "task_type": "${TASK_TYPE}",
  "source": "Maris",
  "title": "${TASK_TITLE}",
  "description": "${TASK_DESC}",
  "priority": "${TASK_PRIORITY}",
  "deadline": "${TASK_DEADLINE}",
  "created_at": "${TIMESTAMP}"
}
EOF

echo "[Maris] ✅ 任务已投递"
echo "  任务ID: ${TASK_ID}"
echo "  类型: ${TASK_TYPE}"
echo "  标题: ${TASK_TITLE}"
echo "  优先级: ${TASK_PRIORITY}"
echo "  Markdown: ${TASK_FILE}"
echo "  JSON: ${JSON_FILE}"
echo ""
echo "  下一步: Codex 将自动从 incoming/ 读取并执行"
