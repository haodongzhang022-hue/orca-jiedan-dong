#!/usr/bin/env bash
# =============================================================================
# ORCA 工作树非破坏性快照
# -----------------------------------------------------------------------------
# 用法：在项目根目录运行
#   bash scripts/orca_backup.sh
#
# 说明：把三个工作树 + 项目根 .env + config 复制到 backups/archive_YYYYMMDD_HHMMSS
#       不调用 git commit，不污染 Git 历史。
# =============================================================================

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
DEST="$PROJECT_ROOT/backups/archive_$TS"

mkdir -p "$DEST"

if [ -d "$PROJECT_ROOT/worktrees" ]; then
  cp -r "$PROJECT_ROOT/worktrees" "$DEST/"
fi

if [ -f "$PROJECT_ROOT/.env" ]; then
  cp "$PROJECT_ROOT/.env" "$DEST/"
fi

if [ -d "$PROJECT_ROOT/config" ]; then
  cp -r "$PROJECT_ROOT/config" "$DEST/"
fi

echo "📦 非破坏性快照已保存：$DEST"
