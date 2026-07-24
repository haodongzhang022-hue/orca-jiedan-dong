#!/usr/bin/env bash
# ============================================================================
# upgrade_incremental.sh — ORCA 脚手架增量迭代（只新增、不覆盖、不破坏）
# ----------------------------------------------------------------------------
# 用法：bash upgrade_incremental.sh "<项目根路径>"
# 规则（全域模板 #290 / 龙虾五步法 v2.7）：
#   - 仅新增「项目中不存在」的文件 / 目录
#   - 已存在的文件永远不覆盖、不修改
#   - 保护目录整体跳过：.env database conversations skills logs
#   - 完成后将项目 scaffold_version 更新为最新版
#   - 全程记录变更文件清单，便于追溯
# ============================================================================
set -u

PROJECT_ROOT="${1:-}"
if [ -z "$PROJECT_ROOT" ] || [ ! -d "$PROJECT_ROOT" ]; then
  echo "用法：bash upgrade_incremental.sh \"<项目根路径>\""
  exit 1
fi

SCAFFOLD_DIR="${ORCA_SCAFFOLD_DIR:-E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0}"

# 保护项（basename 匹配则整体跳过，永远不覆盖）
PROTECT=" .env database conversations skills logs outputs backups scaffold_version "

LATEST_VER="$(cat "$SCAFFOLD_DIR/scaffold_version" 2>/dev/null || echo unknown)"
CHANGED=0
CHANGE_LIST="$PROJECT_ROOT/.upgrade_changelog.txt"
: > "$CHANGE_LIST"

is_protected() {
  local b="$1"
  for p in $PROTECT; do [ "$b" = "$p" ] && return 0; done
  return 1
}

# 递归：只补缺失文件，不覆盖已有文件
copy_missing() {
  local src="$1" dst="$2"
  [ -e "$src" ] || return 0
  local base; base="$(basename "$src")"
  [ "$base" = "." ] || [ "$base" = ".." ] && return 0
  if is_protected "$base"; then
    echo "[skip-protect] $base"
    return 0
  fi
  if [ -d "$src" ]; then
    mkdir -p "$dst"
    local child cb
    for child in "$src"/* "$src"/.*; do
      [ -e "$child" ] || continue
      cb="$(basename "$child")"
      copy_missing "$child" "$dst/$cb"
    done
  else
    if [ -e "$dst" ]; then
      echo "[exists] ${dst#$PROJECT_ROOT/} （不覆盖）"
    else
      cp "$src" "$dst"
      local rel="${dst#$PROJECT_ROOT/}"
      echo "[add] $rel"
      echo "$rel" >> "$CHANGE_LIST"
      CHANGED=$((CHANGED + 1))
    fi
  fi
}

echo "增量迭代：从 $SCAFFOLD_DIR 补充到 $PROJECT_ROOT"
for item in "$SCAFFOLD_DIR"/* "$SCAFFOLD_DIR"/.*; do
  [ -e "$item" ] || continue
  b="$(basename "$item")"
  case "$b" in
    .|..|.git|init_orca_fleet.sh|init_orca_silent.sh) continue ;;
  esac
  copy_missing "$item" "$PROJECT_ROOT/$b"
done

# 更新项目版本号（始终记录到最新，便于下次比对不再误弹）
if [ "$LATEST_VER" != "unknown" ]; then
  echo "$LATEST_VER" > "$PROJECT_ROOT/scaffold_version"
  echo "[version] scaffold_version -> $LATEST_VER"
fi

echo "✅ 增量迭代完成，新增 $CHANGED 项，保护目录未动。"
echo "📄 变更清单：$CHANGE_LIST"
