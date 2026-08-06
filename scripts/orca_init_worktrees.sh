#!/usr/bin/env bash
# =============================================================================
# ORCA 三工作树批量初始化脚本
# 用途：一键创建 hermes/codex/claude 三个工作树并注入环境变量
# 前置条件：项目根目录已克隆，Git 已初始化
# 用法：bash scripts/orca_init_worktrees.sh
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKTREE_DIR="$PROJECT_ROOT/worktrees"

echo "=========================================="
echo "  ORCA 三工作树批量初始化"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. 创建工作树目录
echo ""
echo "[1/3] 创建工作树目录..."

for role in hermes codex claude; do
  TARGET="$WORKTREE_DIR/$role"
  if [ -d "$TARGET" ]; then
    echo "  ✓ $role 已存在，跳过"
  else
    mkdir -p "$TARGET"
    echo "  ✓ 已创建 $role"
  fi
done

# 2. 逐个注入环境变量
echo ""
echo "[2/3] 注入环境变量..."

for role in hermes codex claude; do
  TARGET="$WORKTREE_DIR/$role"
  ENV_FILE="$TARGET/.env"

  # 确定角色描述
  case $role in
    hermes)
      DESC="Hermes / 大脑层 — 制定知识萃取顶层方案、知识库架构、需求拆解"
      NEXT="在 ORCA 中开启 Hermes Agent 对话，可加载 config/orca/hermes_system_prompt.md"
      ;;
    codex)
      DESC="Codex / 执行层 — 批量解析网盘资源、文本提取、自动化脚本开发"
      NEXT="运行 scripts/auto_knowledge_extract.py 开始萃取"
      ;;
    claude)
      DESC="Claude / 审核层 — 版权合规审计、数据脱敏校验、产出审核报告"
      NEXT="在 Claude Code 中执行合规检查，输出 docs/审核报告.md"
      ;;
  esac

  # 生成 .env
  cat > "$ENV_FILE" << ENV_BLOCK
# ORCA 工作树环境变量（由 orca_init_worktrees.sh 自动生成）
ORCA_ROOT_PATH=${PROJECT_ROOT}
ORCA_WORKTREE_PATH=${TARGET}
ORCA_WORKSPACE_NAME=$(basename "$PROJECT_ROOT")
AGENT_ROLE=${role}
GH_PROXY=https://gh-proxy.com
ENV_BLOCK

  echo "  ✓ $role .env 已注入"
done

# 3. 创建 Git 分支（如果不存在）
echo ""
echo "[3/3] 初始化 Git 分支..."

BRANCH_MAP=(
  "hermes:hermes/brain"
  "codex:codex/executor"
  "claude:claude/reviewer"
)

for entry in "${BRANCH_MAP[@]}"; do
  ROLE="${entry%%:*}"
  BRANCH="${entry##*:}"
  if git -C "$PROJECT_ROOT" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
    echo "  ✓ 分支 $BRANCH 已存在"
  else
    git -C "$PROJECT_ROOT" worktree add "$WORKTREE_DIR/$ROLE" -b "$BRANCH" 2>/dev/null && \
      echo "  ✓ 已创建分支 $BRANCH → worktrees/$ROLE" || \
      echo "  ⚠ 分支 $BRANCH 创建失败（可能已存在 worktree）"
  fi
done

# 汇总
echo ""
echo "=========================================="
echo "  ✅ 三工作树初始化完成"
echo ""
echo "  hermes → worktrees/hermes (大脑层)"
echo "  codex  → worktrees/codex  (执行层)"
echo "  claude → worktrees/claude (审核层)"
echo ""
echo "  下一步："
echo "    1. 在各工作树中运行 bash ../../scripts/orca_setup_worktree.sh"
echo "    2. 启动 Agent: bash scripts/launch_all_agents.sh"
echo "=========================================="
