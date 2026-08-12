#!/usr/bin/env bash
# daily_learning_benchmark.sh —— 每日学习对标（09:00 计划任务）
# 职责：生成当日对标任务清单 → 调用知识萃取流水线 → Obsidian wiki 入库（自我进化）
# 用法：bash scripts/daily_learning_benchmark.sh
# 计划任务：Lobster_DailyLearn_0900（每日 09:00，git-bash 运行）

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATE="$(date '+%Y%m%d')"
OBSIDIAN_WIKI="E:/龙虾AI主控中心/Obsidian/wiki"
SKILL_DIR="E:/龙虾AI主控中心/我的AI分身/技能库"
DAILY_DIR="$PROJ_DIR/对话记录/daily"
LOG_DIR="$PROJ_DIR/logs"
mkdir -p "$DAILY_DIR" "$LOG_DIR"
LOG="$LOG_DIR/daily_learning_$(date '+%Y%m%d').log"

echo "== $(date '+%Y-%m-%d %H:%M:%S') 每日学习对标启动 ==" | tee -a "$LOG"

# —— 1) 生成当日对标任务清单（设计商单主题优先）——
TASK_FILE="$DAILY_DIR/learning_benchmark_${DATE}.md"
if [ ! -f "$TASK_FILE" ]; then
  cat > "$TASK_FILE" << EOF
# 每日学习对标任务清单 $DATE
> 自动生成：scripts/daily_learning_benchmark.sh | 职责：Hermes 大脑 → 赛博书屋萃取 → wiki 入库

## 对标主题（本周聚焦：平面设计 + 网页设计）
1. GitHub 检索：平面设计 模板/教程 高星仓库（关键词：design template, html css portfolio）
2. B站检索：平面设计 / 网页设计 教学视频（对标博主：秋芝2046、编程大佬陈悠秀）
3. 萃取：赛博书屋流水线 → wiki 层蒸馏 → 设计偏好模板
4. 回灌：Obsidian/副业变现 + 技能库设计技能迭代

## 执行结果（由萃取完成后回填）
- [ ] GitHub 对标记录
- [ ] B站 对标记录
- [ ] wiki 入库条目
- [ ] 技能迭代建议
EOF
  echo "✅ 生成任务清单：$TASK_FILE" | tee -a "$LOG"
else
  echo "⏭️ 任务清单已存在，跳过生成：$TASK_FILE" | tee -a "$LOG"
fi

# —— 2) 调用知识萃取流水线（存在则执行）——
EXTRACT_SCRIPT="$PROJ_DIR/scripts/auto_knowledge_extract.py"
if [ -f "$EXTRACT_SCRIPT" ]; then
  echo "🔍 调用知识萃取流水线 auto_knowledge_extract.py ..." | tee -a "$LOG"
  (cd "$PROJ_DIR" && python "$EXTRACT_SCRIPT" --source "$TASK_FILE" --output "$OBSIDIAN_WIKI" 2>>"$LOG" || echo "⚠️ 萃取脚本执行失败（不影响任务清单生成）" | tee -a "$LOG")
else
  echo "ℹ️ 未发现 auto_knowledge_extract.py，跳过自动萃取（可由 Hermes 大脑在群内触发赛博书屋）" | tee -a "$LOG"
fi

# —— 3) Obsidian wiki 入库确认（目录存在性）——
if [ -d "$OBSIDIAN_WIKI" ]; then
  echo "✅ Obsidian wiki 就绪：$OBSIDIAN_WIKI" | tee -a "$LOG"
else
  echo "⚠️ Obsidian wiki 目录不存在：$OBSIDIAN_WIKI" | tee -a "$LOG"
fi

echo "== $(date '+%Y-%m-%d %H:%M:%S') 每日学习对标完成，日志：$LOG ==" | tee -a "$LOG"
