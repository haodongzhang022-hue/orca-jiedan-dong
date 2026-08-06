#!/usr/bin/env bash
# =============================================================================
# Obsidian 知识库归档脚本（四角色矩阵 v1.6.0 闭环）
# =============================================================================
# 功能：
#   1. 把四角色 NPC v1.6.0 验收/矩阵文档 + 脚手架模板归档到 Obsidian 主库
#   2. 在 Obsidian wiki/index.md 追加索引条目（幂等，重复执行不产生重复条目）
#   3. 不提交任何密钥（只复制 md/sh/yml/JSON 文档资产，跳过 .env/*.key/*.pem）
# 用法：
#   bash scripts/archive_obsidian_v1.6.0.sh [--obsidian <path>]
#     默认 Obsidian 主库：E:/龙虾AI主控中心/Obsidian/（junction→G盘）
# 安全：不读取/不打印密钥；只做文档资产复制
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OBSIDIAN_ROOT="${1:-E:/龙虾AI主控中心/Obsidian}"
ARCHIVE_DIR="$OBSIDIAN_ROOT/ORCA数据/orca-jiedan/CNB四角色NPC_v1.6.0"
WIKI_INDEX="$OBSIDIAN_ROOT/wiki/index.md"
INDEX_TITLE="CNB四角色NPC_v1.6.0"

echo "🦞 Obsidian 归档：四角色 NPC v1.6.0 闭环"
echo "=========================================="
echo "归档目录: $ARCHIVE_DIR"

# ---- 1. 创建归档目录 ----
mkdir -p "$ARCHIVE_DIR/docs" "$ARCHIVE_DIR/templates"

# ---- 2. 复制文档资产（跳过敏感文件）----
copy_safe() {
  local src="$1" dst="$2"
  [ -f "$src" ] || { echo "  ⚠️ 跳过(不存在): $src"; return; }
  cp "$src" "$dst"
  echo "  ✅ $src"
}

echo "[1/3] 复制核心文档..."
copy_safe docs/四角色矩阵_验收报告_v1.6.0_20260807.md "$ARCHIVE_DIR/docs/"
copy_safe docs/双盘备份与Obsidian归档清单_v1.6.0.md  "$ARCHIVE_DIR/docs/"
copy_safe docs/claude_code_cloud_vs_local.md         "$ARCHIVE_DIR/docs/"
copy_safe docs/脚手架升级_v1.6.0_接入原生HermesCLI_20260807.md "$ARCHIVE_DIR/docs/"
copy_safe docs/验收报告_Claude-Code_CNB云端NPC_DeepSeekV4Flash_20260807.md "$ARCHIVE_DIR/docs/"

echo "[2/3] 复制脚手架模板快照..."
if [ -d templates/cnb_npc_path_b_scaffold ]; then
  cp -r templates/cnb_npc_path_b_scaffold/. "$ARCHIVE_DIR/templates/"
  # 防御性过滤敏感文件
  find "$ARCHIVE_DIR/templates" -type f \( -name "*.env*" -o -name "*.key" -o -name "*.pem" \
    -o -name "secrets.yaml" -o -name "secrets.yml" -o -name ".quota_state.json" \) -delete
  echo "  ✅ templates/cnb_npc_path_b_scaffold → $ARCHIVE_DIR/templates/"
else
  echo "  ⚠️ 模板目录不存在，跳过"
fi

# ---- 3. wiki 索引追加（幂等）----
echo "[3/3] 更新 wiki 索引..."
mkdir -p "$OBSIDIAN_ROOT/wiki"
if [ -f "$WIKI_INDEX" ] && grep -q "$INDEX_TITLE" "$WIKI_INDEX" 2>/dev/null; then
  echo "  ✅ 索引已存在，跳过追加"
else
  cat >> "$WIKI_INDEX" <<EOF

## $INDEX_TITLE
- 归档：ORCA数据/orca-jiedan/CNB四角色NPC_v1.6.0/
- 版本：1.6.0 ｜ 基座：CNB 内置免费 DeepSeek-V4-Flash
- 四角色：claude-code / hermes / codex（路径B 自定义镜像）+ lobster（路径A 轻量化）
- 验收：Issue#10 闭环报告 ｜ AI 用量 audit milli_credit=0（0 外部付费）
- 归档脚本：scripts/archive_obsidian_v1.6.0.sh
EOF
  echo "  ✅ 索引条目已追加: $INDEX_TITLE"
fi

echo "=========================================="
echo "✅ Obsidian 归档完成"
echo "  归档目录: $ARCHIVE_DIR"
echo "  wiki 索引: $WIKI_INDEX"
echo "  （E盘 Obsidian 主库 junction→G盘，双盘同步由文件系统层级自动完成）"
