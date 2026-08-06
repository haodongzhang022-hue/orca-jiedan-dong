#!/usr/bin/env bash
# =============================================================================
# Maris 接入说明生成器（脚手架 v1.4）
# 用途：在每个项目生成 docs/Maris接入说明.md，告诉 Maris 如何与本项目协作
# =============================================================================

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_NAME="$(basename "$ROOT")"
mkdir -p "$ROOT/docs"

cat > "$ROOT/docs/Maris接入说明.md" << EOF
# Maris 接入说明 · $REPO_NAME

> 本文档说明 Maris（调度端）如何与本项目舰队协作。
> 更新：$(date '+%Y-%m-%d')

## 一、协作总览

\`\`\`
Maris(调度) ──投递任务卡──▶ fleet_exchange/incoming/
                              │
                              ▼
                    CodeBuddy / Codex / Claude Code（CNB 云上 NPC）
                              │
                              ▼
                    fleet_exchange/done → results/（交付物）
\`\`\`

## 二、Maris 一键投递

在项目根目录执行：

\`\`\`bash
bash scripts/maris_dispatch.sh "任务需求描述"
bash scripts/maris_dispatch.sh --type poster --desc "开业海报" --price 300
\`\`\`

脚本会把任务卡写入 \`fleet_exchange/incoming/\`，舰队自动接单。

## 三、在 CNB 平台召唤 NPC

在 CNB Issue/PR 评论区 @ 即可（需勾选「替我上班」）：

- \`@TJF19770107/$REPO_NAME(codex)\` → Codex 执行
- \`@TJF19770107/$REPO_NAME(claude-code)\` → Claude Code 审核
- \`@CodeBuddy\` → CodeBuddy（平台默认 NPC，可做最终审查/汇总）

> 注意：\`@codex\` 这种简写平台不认，必须用完整格式 \`@仓库路径(角色名)\`。

## 四、舰队三层协作

| 层 | 角色 | 分支 | 职责 |
|----|------|------|------|
| 大脑 | Hermes | hermes/brain | 需求拆解、任务编排 |
| 执行 | Codex | codex/executor | 代码实现、物料生成 |
| 审核 | Claude | claude/reviewer | 质量校验、合规把关 |

## 五、任务卡流转

\`incoming → accepted → doing → done → results → logs\`
EOF

echo "✅ 已生成 $ROOT/docs/Maris接入说明.md"
