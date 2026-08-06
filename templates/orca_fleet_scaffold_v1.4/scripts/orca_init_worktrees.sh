#!/usr/bin/env bash
# =============================================================================
# ORCA 三工作树初始化脚本（脚手架 v1.4 通用版）
# -----------------------------------------------------------------------------
# 用途：在项目根目录执行，一键创建 hermes/brain、codex/executor、
#       claude/reviewer 三个工作树分支，并生成三层系统提示词
# 用法：bash scripts/orca_init_worktrees.sh
# 注意：仅需在尚未初始化工作树的新项目执行一次（幂等：已存在则跳过）
# =============================================================================

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🦞 初始化 ORCA 三工作树 @ $(basename "$ROOT")"

# 1. 确保在默认分支且无未提交变更
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ 存在未提交变更，请先提交或 stash"
  exit 1
fi
BASE_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"

# 2. 定义工作树
declare -A WORKTREES=(
  [hermes]="hermes/brain"
  [codex]="codex/executor"
  [claude]="claude/reviewer"
)

mkdir -p worktrees config/orca

# 3. 逐角色创建分支 + 工作树
for role in hermes codex claude; do
  BRANCH="${WORKTREES[$role]}"
  WT="worktrees/$role"
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "  [SKIP] 分支 $BRANCH 已存在"
  else
    git branch "$BRANCH" "$BASE_BRANCH"
    echo "  [OK] 创建分支 $BRANCH"
  fi
  if [ -d "$WT/.git" ]; then
    echo "  [SKIP] 工作树 $WT 已存在"
  else
    git worktree add "$WT" "$BRANCH" 2>/dev/null || git -C "$ROOT" worktree add "$WT" "$BRANCH"
    echo "  [OK] 创建工作树 $WT"
  fi
done

# 4. 生成三层系统提示词（若不存在）
[ -f config/orca/hermes_system_prompt.md ] || cat > config/orca/hermes_system_prompt.md << 'EOF'
# Hermes · 大脑层（战略调度）

你是 Hermes，本项目的战略调度大脑。

## 核心职责
- 需求拆解：将高层需求拆成可执行子任务
- 任务编排：生成任务清单，分配给 Codex / Claude
- 流程控制：维护状态机与进度跟踪
- 知识联动：调用知识库，沉淀方法论

## 工作流程
1. 接收需求 → 拆解 → 生成任务卡
2. 写任务卡到 fleet_exchange/incoming/
3. 调度 Codex 执行 → 路由 Claude 审核
4. 确认无误 → 合并 master → 归档沉淀
EOF

[ -f config/orca/codex_system_prompt.md ] || cat > config/orca/codex_system_prompt.md << 'EOF'
# Codex · 执行层（代码实现）

你是 Codex，本项目的执行工程师。

## 核心职责
- 代码实现：按任务卡编写可运行代码
- 脚本开发：自动化脚本、工具封装
- 批量执行：批量任务与数据处理
- 日志反馈：记录进度与异常

## 工作流程
1. 从 fleet_exchange/incoming/ 领取任务卡
2. 在代码区实现功能
3. 输出产物到 fleet_exchange/doing/ → done/
4. 通知 Claude 审查
EOF

[ -f config/orca/claude_system_prompt.md ] || cat > config/orca/claude_system_prompt.md << 'EOF'
# Claude · 审核层（质量把关）

你是 Claude Code，本项目的质量守护者。

## 核心职责
- 代码审查：安全、性能、可读性、健壮性
- 质量校验：边界测试、回归测试
- 合规检查：版权、隐私、安全红线
- 审查报告：输出可追溯的审查结论

## 工作流程
1. 接收 Codex 产物（fleet_exchange/done/）
2. 执行四项硬校验（安全/性能/可读/健壮）
3. 输出审查报告到 fleet_exchange/results/
4. 通过 → 放行合并；不通过 → 退回 Codex 修复
EOF

# 5. 写入 setup_one_liner（贴入 ORCA 设置脚本框的一行命令）
cat > config/orca/setup_one_liner.txt << 'EOF'
bash ../../scripts/orca_setup_worktree.sh
EOF

echo ""
echo "✅ 三工作树初始化完成："
echo "   - hermes/brain    → worktrees/hermes"
echo "   - codex/executor  → worktrees/codex"
echo "   - claude/reviewer → worktrees/claude"
echo "   - 系统提示词：config/orca/*_system_prompt.md"
echo ""
echo "下一步：在 ORCA 每个工作树「添加设置脚本」框粘贴："
echo "  bash ../../scripts/orca_setup_worktree.sh"
