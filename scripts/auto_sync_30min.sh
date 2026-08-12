#!/usr/bin/env bash
# auto_sync_30min.sh —— 每 30 分钟双同步（CNB云原生 + GitHub + Obsidian 增量）
# 职责：接单项目 git 双推（origin=CNB / direct=GitHub）+ Obsidian 增量同步
# 用法：bash scripts/auto_sync_30min.sh
# 计划任务：Lobster_AutoSync_30min（每 30 分钟，git-bash 运行）

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJ_DIR/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/auto_sync_$(date '+%Y%m%d').log"

echo "== $(date '+%Y-%m-%d %H:%M:%S') 30分钟双同步启动 ==" >> "$LOG"

cd "$PROJ_DIR"

# —— 1) 提交本地变更（排除 worktrees 物理隔离工作树）——
git add -A -- ':!worktrees' 2>>"$LOG" || true
if git diff --cached --quiet; then
  echo "ℹ️ 无新变更，跳过提交" >> "$LOG"
else
  git commit -q -m "chore: auto-sync $(date '+%Y-%m-%d %H:%M:%S')" >>"$LOG" 2>&1 || true
  echo "✅ 已提交本地变更" >> "$LOG"
fi

# —— 2) 双推：CNB云原生（origin）+ GitHub（direct）——
PUSH_CNB=1; PUSH_GH=1
git push origin main >>"$LOG" 2>&1 || { echo "⚠️ CNB 推送失败（稍后重试）" >> "$LOG"; PUSH_CNB=0; }
git push direct main >>"$LOG" 2>&1 || { echo "⚠️ GitHub 推送失败（稍后重试）" >> "$LOG"; PUSH_GH=0; }
echo "推送结果：CNB=$([ $PUSH_CNB -eq 1 ] && echo OK || echo FAIL) GitHub=$([ $PUSH_GH -eq 1 ] && echo OK || echo FAIL)" >> "$LOG"

# —— 3) Obsidian 增量同步（E盘 junction → G盘，robocopy 增量）——
OBSIDIAN_SRC="E:/龙虾AI主控中心/Obsidian"
OBSIDIAN_DST="G:/龙虾AI主控中心/Obsidian"  # 若 G 盘不存在则跳过
if [ -d "$OBSIDIAN_DST" ]; then
  robocopy "$OBSIDIAN_SRC" "$OBSIDIAN_DST" /MIR /XD .git /R:1 /W:1 /NJH /NJS >> "$LOG" 2>&1 || true
  echo "✅ Obsidian 增量同步完成" >> "$LOG"
else
  echo "ℹ️ G盘目标不存在，跳过 Obsidian 增量同步" >> "$LOG"
fi

echo "== $(date '+%Y-%m-%d %H:%M:%S') 双同步完成，日志：$LOG ==" >> "$LOG"
