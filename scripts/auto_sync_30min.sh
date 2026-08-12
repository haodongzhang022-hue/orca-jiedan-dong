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
  # 注意：Git Bash 会把 /MIR 转换为 C:/Program Files/Git/MIR，必须 MSYS_NO_PATHCONV=1
  MSYS_NO_PATHCONV=1 robocopy "$OBSIDIAN_SRC" "$OBSIDIAN_DST" /MIR /XD .git /R:1 /W:1 /NJH /NJS >> "$LOG" 2>&1 || true
  echo "✅ Obsidian 增量同步完成" >> "$LOG"
else
  echo "ℹ️ G盘目标不存在，跳过 Obsidian 增量同步" >> "$LOG"
fi

# —— 4) 反向回流：Obsidian 记忆卡 + wiki → 仓库（双向闭环 P1-1 修复）——
# 目的：Obsidian 编辑/新增的画像/知识 → 回流仓库 → 赋能 Agent 执行（非单向）
REPO_MEM="$PROJ_DIR/docs/记忆卡片"
OBS_WIKI="$OBSIDIAN_SRC/wiki"
OBS_MEM="$OBSIDIAN_SRC/记忆卡片"
if [ -d "$OBS_WIKI" ] || [ -d "$OBS_MEM" ]; then
  # 回流 wiki（仅同步 .md，避免把图片/附件膨胀仓库）
  if [ -d "$OBS_WIKI" ]; then
    mkdir -p "$PROJ_DIR/docs/obsidian_wiki"
    for f in "$OBS_WIKI"/*.md; do
      [ -f "$f" ] && cp -f "$f" "$PROJ_DIR/docs/obsidian_wiki/" 2>>"$LOG" || true
    done
    echo "✅ Obsidian wiki 反向回流仓库" >> "$LOG"
  fi
  # 回流记忆卡（若 Obsidian 侧有独立记忆卡目录）
  if [ -d "$OBS_MEM" ]; then
    mkdir -p "$REPO_MEM"
    for f in "$OBS_MEM"/*.md; do
      [ -f "$f" ] && cp -f "$f" "$REPO_MEM/" 2>>"$LOG" || true
    done
    echo "✅ Obsidian 记忆卡反向回流仓库" >> "$LOG"
  fi
  # 回流传入 git
  git add -A -- ':!worktrees' 2>>"$LOG" || true
  if ! git diff --cached --quiet; then
    git commit -q -m "chore: obsidian反向回流 $(date '+%Y-%m-%d %H:%M:%S')" >>"$LOG" 2>&1 || true
    git push origin main >>"$LOG" 2>&1 || echo "⚠️ 反向回流推送失败（稍后重试）" >> "$LOG"
    echo "✅ Obsidian 反向回流已提交并推送" >> "$LOG"
  else
    echo "ℹ️ Obsidian 反向回流无新变更" >> "$LOG"
  fi
else
  echo "ℹ️ Obsidian wiki/记忆卡目录不存在，跳过反向回流" >> "$LOG"
fi

echo "== $(date '+%Y-%m-%d %H:%M:%S') 双同步完成，日志：$LOG ==" >> "$LOG"