#!/usr/bin/env bash
# =============================================================================
# deploy_sihua_kb.sh —— 四化迭代 Obsidian 知识库 一键部署（全自动化组件）
# =============================================================================
# 功能：一键拉齐四化组件（智能化/定制化/全自动化/自我进化）
#   [智能化]   kb_search.py 语义检索 + 索引
#   [定制化]   三记忆卡骨架 + 用户画像蒸馏
#   [全自动化] 定时链检测 + 双向同步检查
#   [自我进化] kb_evolve.py 进化管线
# 用法：
#   bash scripts/deploy_sihua_kb.sh [--dry-run]
# 安全：不读取/不打印密钥；只做文档资产与脚本就绪检查
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
DRY="${1:---dry-run}"

echo "🦞 四化迭代 Obsidian 知识库 · 一键部署检查"
echo "============================================"

# 自动探测 Python
PY=""
for cand in python python3 py; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
[ -z "$PY" ] && { echo "❌ 未找到 Python，请先安装"; exit 1; }

pass=0; fail=0
check() { # check <描述> <命令>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "  ✅ $desc"; pass=$((pass+1));
  else echo "  ⚠️  $desc"; fail=$((fail+1)); fi
}

echo ""
echo "[1/4] 智能化组件"
check "语义检索脚本存在 scripts/kb_search.py" test -f scripts/kb_search.py
if test -f scripts/kb_search.py && [ "$DRY" = "--dry-run" ]; then
  echo "  🔍 重建索引（dry-run 跳过写入）..."
  $PY scripts/kb_search.py --index-only --root docs >/dev/null 2>&1 && echo "  ✅ 索引可构建" || echo "  ⚠️ 索引构建需实际目录"
fi

echo ""
echo "[2/4] 定制化组件"
check "记忆卡·我的笔记 存在" test -f docs/记忆卡片/我的笔记.md
check "记忆卡·用户画像 存在" test -f docs/记忆卡片/用户画像.md
check "记忆卡·灵魂 存在"     test -f docs/记忆卡片/灵魂.md
check "蒸馏脚本 scripts/distill_user_profile.py" test -f scripts/distill_user_profile.py

echo ""
echo "[3/4] 全自动化组件"
check "30min 同步脚本 scripts/auto_sync_30min.sh" test -f scripts/auto_sync_30min.sh
check "每日对标 scripts/daily_learning_benchmark.sh" test -f scripts/daily_learning_benchmark.sh

echo ""
echo "[4/4] 自我进化组件"
check "进化管线 scripts/kb_evolve.py" test -f scripts/kb_evolve.py
check "SelfLearn 记录 SelfLearn_Record.md" test -f SelfLearn_Record.md

echo ""
echo "============================================"
echo "部署检查完成：通过 $pass 项 / 警告 $fail 项"
echo "👉 下一步：按 docs/四化迭代_Obsidian知识库_高标准实施计划_v2.0.md 阶段清单逐项落地"
exit 0
