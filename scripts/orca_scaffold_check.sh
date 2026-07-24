#!/usr/bin/env bash
# ============================================================================
# orca_scaffold_check.sh — ORCA 脚手架版本治理（一致性校验 + 交互式确认）
# ----------------------------------------------------------------------------
# 用途：项目启动 / 切换模板前调用，比对「项目脚手架版本」与「全域最新脚手架版本」
# 规则（全域模板 #290 / 龙虾五步法 v2.7）：
#   - 一致    → 直接通过，不弹窗（防冗余，避免「老点运行」）
#   - 不一致  → 强制交互确认（不可跳过、不可静默升级）
#       Y = 增量迭代：仅补新参数/技能/配置，保护目录完全不动
#       N = 不迭代  ：保留旧版，版本分叉，新旧长期并行、互不干扰
# 保护目录（永远不覆盖）：.env  database  conversations  skills  logs
# 非交互环境（无 TTY）→ 拒绝静默决策，输出手动命令后退出（exit 2）
# ============================================================================
set -u

# —— 定位项目根（兼容从工作树 worktrees/<role>/scripts 调用）——
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$(basename "$SCRIPT_DIR")" = "scripts" ]; then
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  PROJECT_ROOT="$(pwd)"
fi
if [ -f "$PROJECT_ROOT/../../../scaffold_version" ]; then
  PROJECT_ROOT="$(cd "$PROJECT_ROOT/../../.." && pwd)"
fi

# 脚手架最新版位置（可通过环境变量覆盖）
SCAFFOLD_DIR="${ORCA_SCAFFOLD_DIR:-E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0}"

# —— 读取版本 ——
CURR_VER="$(cat "$PROJECT_ROOT/scaffold_version" 2>/dev/null || echo 0.0.0)"
LATEST_VER="$(cat "$SCAFFOLD_DIR/scaffold_version" 2>/dev/null || echo unknown)"

echo "当前项目脚手架版本：$CURR_VER"
echo "全域最新脚手架版本：$LATEST_VER"

# —— 一致 → 直接通过（不弹窗）——
if [ "$CURR_VER" = "$LATEST_VER" ]; then
  echo "✅ 版本一致，无需迭代，直接启动（无弹窗）。"
  exit 0
fi

# —— 不一致 → 强制交互确认 ——
echo "=============================================="
echo "⚠️  脚手架版本不一致"
echo "  当前项目：$CURR_VER"
echo "  全域最新：$LATEST_VER"
echo "----------------------------------------------"
echo "【Y】增量迭代：仅补充新参数/技能/配置；数据库、会话、自定义技能完全不动"
echo "【N】不迭代  ：保留旧版，版本分叉，新旧长期并行、互不干扰"
echo "=============================================="

# 非交互环境（无 TTY）→ 拒绝静默决策，输出指引后退出
if [ ! -t 0 ]; then
  echo "❗ 检测到非交互环境，无法安全确认。请在本机终端手动执行以下之一："
  echo "   增量迭代：bash \"$SCAFFOLD_DIR/scripts/upgrade_incremental.sh\" \"$PROJECT_ROOT\""
  echo "   保留分叉：记录 fork_version.log 并沿用旧版（不执行任何写入）"
  exit 2
fi

read -p "请输入 Y/N：" CHOICE
case "$CHOICE" in
  Y|y)
    echo "🔧 执行增量迭代（保护核心数据）..."
    bash "$SCAFFOLD_DIR/scripts/upgrade_incremental.sh" "$PROJECT_ROOT"
    echo "✅ 迭代完成。"
    ;;
  N|n)
    echo "📌 已分叉，继续使用旧脚手架：$CURR_VER"
    {
      echo "fork_version=$CURR_VER"
      echo "forked_from_latest=$LATEST_VER"
      echo "forked_at=$(date +%Y-%m-%dT%H:%M:%S)"
    } >> "$PROJECT_ROOT/fork_version.log"
    echo "✅ 已写入 fork_version.log，旧版长期并行。"
    ;;
  *)
    echo "❌ 输入无效，默认分叉（沿用旧版）。"
    echo "fork_version=$CURR_VER (invalid-choice-default)" >> "$PROJECT_ROOT/fork_version.log"
    ;;
esac
