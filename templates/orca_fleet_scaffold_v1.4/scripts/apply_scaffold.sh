#!/usr/bin/env bash
# =============================================================================
# ORCA 舰队脚手架 · 一键部署脚本（v1.4）
# -----------------------------------------------------------------------------
# 用途：把本脚手架模板批量部署到多个 ORCA 项目（本机路径），
#       统一补齐 CNB NPC 事件绑定 + 三工作树 + Maris 调度接入
# 用法（在本机 Git Bash 执行）：
#   bash templates/orca_fleet_scaffold_v1.4/scripts/apply_scaffold.sh \
#       "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/币安/我的黑马策略" \
#       "E:/龙虾AI主控中心/我的AI分身/赛事预测分析系统"
#   # 或批量：
#   bash templates/orca_fleet_scaffold_v1.4/scripts/apply_scaffold.sh --all
# =============================================================================

set -e
# 模板根（本脚本所在目录的上级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TPL="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "============================================="
echo "  🦞 ORCA 舰队脚手架一键部署 v1.4"
echo "  模板: $TPL"
echo "============================================="
echo ""

# 默认 ORCA 项目根目录列表（按需修改）
DEFAULT_PROJECTS=(
  "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
  "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/嘉盛/黄金黑马策略"
  "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/币安/我的黑马策略"
  "E:/龙虾AI主控中心/我的AI分身/网盘课程资源知识萃取与沉淀体系建设"
  "E:/龙虾AI主控中心/我的AI分身/赛事预测分析系统"
)

apply_one() {
  local ROOT="$1"
  [ -d "$ROOT" ] || { echo "❌ 目录不存在，跳过: $ROOT"; return 1; }
  local NAME="$(basename "$ROOT")"
  echo "===== 部署 → $NAME ====="

  # 1. .cnb.yml
  if [ -f "$ROOT/.cnb.yml" ]; then
    echo "  [SKIP] .cnb.yml 已存在"
  else
    cp "$TPL/.cnb.yml" "$ROOT/.cnb.yml" && echo "  [ADD] .cnb.yml"
  fi

  # 2. .cnb/settings.yml
  if [ -f "$ROOT/.cnb/settings.yml" ]; then
    echo "  [SKIP] .cnb/settings.yml 已存在（角色已定义）"
  else
    mkdir -p "$ROOT/.cnb"
    cp "$TPL/.cnb/settings.yml" "$ROOT/.cnb/settings.yml"
    echo "  [ADD] .cnb/settings.yml（通用版，建议改项目名）"
  fi

  # 3. .orca/setup.sh
  mkdir -p "$ROOT/.orca"
  cp "$TPL/.orca/setup.sh" "$ROOT/.orca/setup.sh" && echo "  [ADD] .orca/setup.sh"

  # 4. CODEX.md / CLAUDE.md
  [ -f "$ROOT/CODEX.md" ] || { sed "s|{project_name}|$NAME|g; s|{repo}|$NAME|g" "$TPL/CODEX.md" > "$ROOT/CODEX.md" && echo "  [ADD] CODEX.md"; }
  [ -f "$ROOT/CLAUDE.md" ] || { sed "s|{project_name}|$NAME|g; s|{repo}|$NAME|g" "$TPL/CLAUDE.md" > "$ROOT/CLAUDE.md" && echo "  [ADD] CLAUDE.md"; }

  # 5. scripts 标准件（不覆盖已存在的）
  mkdir -p "$ROOT/scripts"
  for f in orca_setup_worktree.sh orca_project_startup.sh orca_init_worktrees.sh maris_dispatch.sh maris_gen_readme.sh; do
    if [ -f "$ROOT/scripts/$f" ]; then
      echo "  [SKIP] scripts/$f 已存在"
    else
      cp "$TPL/scripts/$f" "$ROOT/scripts/$f" && echo "  [ADD] scripts/$f"
    fi
  done

  # 6. config/orca 目录
  mkdir -p "$ROOT/config/orca"

  # 7. 脚手架 README + 版本
  [ -f "$ROOT/脚手架README.md" ] || { sed "s|{project_name}|$NAME|g; s|{repo}|$NAME|g" "$TPL/脚手架README.md" > "$ROOT/脚手架README.md" && echo "  [ADD] 脚手架README.md"; }
  [ -f "$ROOT/scaffold_version" ] || { cp "$TPL/scaffold_version" "$ROOT/scaffold_version" && echo "  [ADD] scaffold_version"; }

  # 8. fleet_exchange 目录
  for d in incoming accepted doing done results parsed logs; do
    mkdir -p "$ROOT/fleet_exchange/$d"
    [ -f "$ROOT/fleet_exchange/$d/.gitkeep" ] || touch "$ROOT/fleet_exchange/$d/.gitkeep"
  done
  [ -f "$ROOT/fleet_exchange/README.md" ] || cp "$TPL/fleet_exchange/README.md" "$ROOT/fleet_exchange/README.md"
  echo "  [ADD] fleet_exchange/（目录结构）"

  echo "===== $NAME 完成 ====="
  echo ""
}

# --all 模式：部署到所有默认项目
if [ "$1" = "--all" ]; then
  for p in "${DEFAULT_PROJECTS[@]}"; do
    apply_one "$p"
  done
  echo "✅ 全部默认项目部署完成"
  echo "   部署后建议：在每个项目执行 bash scripts/orca_init_worktrees.sh 初始化工作树"
  exit 0
fi

# 指定目录模式
if [ $# -eq 0 ]; then
  echo "用法："
  echo "  bash $0 <项目目录1> [项目目录2 ...]"
  echo "  bash $0 --all"
  echo ""
  echo "默认项目列表："
  for p in "${DEFAULT_PROJECTS[@]}"; do echo "  - $p"; done
  exit 1
fi

for d in "$@"; do
  apply_one "$d"
done
echo "✅ 全部部署完成"
