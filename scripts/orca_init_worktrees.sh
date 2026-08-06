#!/usr/bin/env bash
# ==============================================================================
# ORCA 三工作树初始化脚本 — Maris 标准件
# ==============================================================================
# 用法：
#   bash scripts/orca_init_worktrees.sh [--project-root <路径>]
# 说明：
#   初始化 hermes / codex / claude 三个 Git worktree，
#   自动注入 .env 环境变量，适配本地与云端双链路。
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

# 支持显式传入
if [[ "$1" == "--project-root" ]]; then
  PROJECT_ROOT="$2"
fi

WORKTREES_DIR="$PROJECT_ROOT/worktrees"

echo "========================================="
echo "  ORCA 三工作树初始化"
echo "  项目根: $PROJECT_ROOT"
echo "========================================="
echo ""

# ---- 1. 确保分支存在 ----
echo "[1/4] 确保 Git 分支存在..."
for branch in hermes/brain codex/executor claude/reviewer; do
  if ! git -C "$PROJECT_ROOT" rev-parse --verify "$branch" >/dev/null 2>&1; then
    git -C "$PROJECT_ROOT" branch "$branch"
    echo "  创建分支: $branch"
  else
    echo "  已存在: $branch"
  fi
done

# ---- 2. 创建 worktree 目录 ----
echo ""
echo "[2/4] 创建 worktree 目录..."
for role in hermes codex claude; do
  WT_PATH="$WORKTREES_DIR/$role"
  if [ -d "$WT_PATH" ]; then
    echo "  已存在: $WT_PATH"
  else
    mkdir -p "$WT_PATH"
    echo "  创建: $WT_PATH"
  fi
done

# ---- 3. 注入 .env 环境变量 ----
echo ""
echo "[3/4] 注入 .env 环境变量..."
for role in hermes codex claude; do
  WT_PATH="$WORKTREES_DIR/$role"
  ENV_FILE="$WT_PATH/.env"

  # Windows 路径转换
  if command -v cygpath >/dev/null 2>&1; then
    ROOT_WIN="$(cygpath -w "$PROJECT_ROOT")"
    WT_WIN="$(cygpath -w "$WT_PATH")"
  else
    ROOT_WIN="$PROJECT_ROOT"
    WT_WIN="$WT_PATH"
  fi

  cat > "$ENV_FILE" <<ENV
# ORCA 工作树环境变量（由 orca_init_worktrees.sh 自动生成）
ORCA_ROOT_PATH=${ROOT_WIN}
ORCA_WORKTREE_PATH=${WT_WIN}
ORCA_WORKSPACE_NAME=$(basename "$PROJECT_ROOT")
AGENT_ROLE=${role}
ORCA_MODEL=deepseek-v4-flash
ORCA_FREE_UNTIL=2026-12-31
GH_PROXY=https://gh-proxy.com
ENV

  echo "  $role/.env ✓"
done

# ---- 4. 角色说明 ----
echo ""
echo "[4/4] 角色分配："
echo "  hermes/brain     → 大脑层（战略调度、消息监听、任务分发）"
echo "  codex/executor   → 执行层（代码编写、脚本执行、物料生成）"
echo "  claude/reviewer  → 审核层（代码审计、质量守护、合规检查）"
echo ""
echo "========================================="
echo "  ✅ 三工作树初始化完成"
echo "  下一步：运行 bash scripts/orca_setup_worktree.sh 完善各工作树"
echo "========================================="
