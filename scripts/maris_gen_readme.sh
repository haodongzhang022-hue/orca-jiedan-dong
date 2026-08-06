#!/usr/bin/env bash
# ==============================================================================
# Maris 自动生成 README 脚本 — 为 fleet_exchange 生成状态说明
# ==============================================================================
# 用法：
#   bash scripts/maris_gen_readme.sh
# 说明：
#   扫描 fleet_exchange/ 四级目录，自动生成 README.md 状态报告
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EX_DIR="$PROJECT_ROOT/fleet_exchange"
README_FILE="$EX_DIR/README.md"

INCOMING="$EX_DIR/incoming"
DOING="$EX_DIR/doing"
DONE="$EX_DIR/done"
RESULTS="$EX_DIR/results"

mkdir -p "$INCOMING" "$DOING" "$DONE" "$RESULTS"

# ---- 计数 ----
n_incoming=$(find "$INCOMING" -maxdepth 1 -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | wc -l)
n_doing=$(find "$DOING" -maxdepth 1 -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | wc -l)
n_done=$(find "$DONE" -maxdepth 1 -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | wc -l)
n_results=$(find "$RESULTS" -maxdepth 1 -type f \( -name "*.md" -o -name "*.json" \) 2>/dev/null | wc -l)

# ---- 生成 README ----
cat > "$README_FILE" <<README
# Fleet Exchange — 任务流转目录

> 自动生成时间：$(date '+%Y-%m-%d %H:%M:%S')
> 生成脚本：scripts/maris_gen_readme.sh

## 目录结构

| 目录 | 用途 | 当前任务数 |
|------|------|-----------|
| **incoming/** | 待接单任务（Maris 投递 / 外部写入） | ${n_incoming} |
| **doing/** | 执行中（Codex 执行层处理） | ${n_doing} |
| **done/** | 已完成（Claude Code 审核通过） | ${n_done} |
| **results/** | 最终成品（CodeBuddy 终审归档） | ${n_results} |

## 流转规则

1. **Maris** → 写入任务卡到 \`incoming/\`
2. **Codex** → 从 \`incoming/\` 取任务 → 执行 → 移入 \`doing/\`
3. **Claude Code** → 从 \`doing/\` 审核校验 → 通过 → 移入 \`done/\`
4. **CodeBuddy** → 从 \`done/\` 终审 → 归档到 \`results/\`

## 任务卡格式

\`\`\`markdown
# 任务卡
- task_id: YYYYMMDD_HHMMSS_N
- source: Maris | Codex | Hermes
- type: 文案 | 海报 | 视频 | 通用
- title: <任务标题>
- status: incoming | doing | done | results
\`\`\`

## 手动操作

\`\`\`bash
# 投递新任务
bash scripts/maris_dispatch.sh --type 文案 --title "任务标题" --desc "描述"

# 确认待放行任务
bash scripts/confirm_task.sh <task_id>

# 完成任务并归档
bash scripts/fleet_done.sh "<doing/任务文件>" "<结果摘要>"
\`\`\`
README

echo "[README] 已生成 $README_FILE"
echo "  incoming: ${n_incoming} | doing: ${n_doing} | done: ${n_done} | results: ${n_results}"
