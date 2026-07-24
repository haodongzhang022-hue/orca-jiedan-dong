#!/usr/bin/env bash
# =============================================================================
# ORCA 工作树自动初始化脚本（全域模板 #290）
# -----------------------------------------------------------------------------
# 用途：贴到 ORCA 每个工作树的「添加设置脚本」输入框，自动注入环境变量
# 设计：同一脚本适配 hermes / codex / claude 三个工作树，通过目录名识别角色
# 原则：
#   - 无 read -p / pause，全程静默
#   - 不修改用户全局 .bashrc
#   - 不自动 commit / push（避免污染 Git 历史）
#   - 路径用 cygpath -w 转为 Windows 反斜杠格式，避免 ORCA 解析失败
# 贴入 ORCA 的一行命令：
#   bash ../../scripts/orca_setup_worktree.sh
# =============================================================================

set -u

# 1. 当前工作树角色（hermes / codex / claude）
AGENT_ROLE="$(basename "$PWD")"

# 2. 项目根（当前在 worktrees/<role>，../.. 即项目根）
ORCA_ROOT_PATH="$(cd ../.. && pwd)"
ORCA_WORKSPACE_NAME="$(basename "$ORCA_ROOT_PATH")"
ORCA_WORKTREE_PATH="$PWD"

# 3. 转换为 Windows 原生路径（反斜杠），避免 ORCA / Python 解析 Git Bash 的 /e/ 写法出错
if command -v cygpath >/dev/null 2>&1; then
  ORCA_ROOT_PATH_WIN="$(cygpath -w "$ORCA_ROOT_PATH")"
  ORCA_WORKTREE_PATH_WIN="$(cygpath -w "$ORCA_WORKTREE_PATH")"
else
  ORCA_ROOT_PATH_WIN="$ORCA_ROOT_PATH"
  ORCA_WORKTREE_PATH_WIN="$ORCA_WORKTREE_PATH"
fi

# 4. 写入当前工作树独立的 .env（无密钥，仅路径与角色，可安全存在工作树中）
cat > .env <<ENV_BLOCK
# ORCA 工作树环境变量（由 orca_setup_worktree.sh 自动生成，无需手动改）
ORCA_ROOT_PATH=${ORCA_ROOT_PATH_WIN}
ORCA_WORKTREE_PATH=${ORCA_WORKTREE_PATH_WIN}
ORCA_WORKSPACE_NAME=${ORCA_WORKSPACE_NAME}
AGENT_ROLE=${AGENT_ROLE}
GH_PROXY=https://gh-proxy.com
ENV_BLOCK

# 5. 按角色打印中文就绪提示
printf '\n'
case $AGENT_ROLE in
  hermes)
    printf "✅ Hermes / 大脑层 已就绪\\n"
    printf "   工作目录：%s\\n" "$ORCA_WORKTREE_PATH_WIN"
    printf "   项目：%s\\n" "$ORCA_WORKSPACE_NAME"
    printf "   默认职责：制定知识萃取顶层方案、知识库架构、需求拆解（全域模板 #291）\\n"
    printf "   下一步：在 ORCA 中开启 Hermes Agent 对话，可加载 config/orca/hermes_system_prompt.md\\n"
    ;;
  codex)
    printf "✅ Codex / 执行层 已就绪\\n"
    printf "   工作目录：%s\\n" "$ORCA_WORKTREE_PATH_WIN"
    printf "   项目：%s\\n" "$ORCA_WORKSPACE_NAME"
    printf "   默认职责：批量解析网盘资源、文本提取、自动化脚本开发\\n"
    printf "   下一步：运行 scripts/auto_knowledge_extract.py 开始萃取\\n"
    ;;
  claude)
    printf "✅ Claude / 审核层 已就绪\\n"
    printf "   工作目录：%s\\n" "$ORCA_WORKTREE_PATH_WIN"
    printf "   项目：%s\\n" "$ORCA_WORKSPACE_NAME"
    printf "   默认职责：版权合规审计、数据脱敏校验、产出审核报告\\n"
    printf "   下一步：在 Claude Code 中执行合规检查，输出 docs/审核报告.md\\n"
    ;;
  *)
    printf "⚠️  未知角色：%s（应为 hermes / codex / claude 之一）\\n" "$AGENT_ROLE"
    printf "   请确认此脚本运行在 worktrees/* 目录下。\\n"
    ;;
esac
printf "📦 环境注入完成，.env 已写入：%s\\n" "$ORCA_WORKTREE_PATH_WIN/.env"
