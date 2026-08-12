#!/usr/bin/env bash
# =============================================================================
# cnb_echo_ping.sh — 群聊痕迹墙写入口（云端 NPC ↔ 桌面 Hermes Studio 可见）
# =============================================================================
# 用途：
#   让 CNB 云端 NPC（hermes/codex/claude-code）与本地 Hermes Studio 桌面版
#   通过「git 可同步的痕迹目录」互相看到交流过程，实现需求③的可见化。
#
# 用法：
#   bash scripts/cnb_echo_ping.sh --from hermes --to codex \
#        --title "海报商单拆SVG" --body "已分发，见 fleet_exchange/incoming/xxx.md"
#   bash scripts/cnb_echo_ping.sh --from codex --to claude-code --title "SVG完成" --body "待审核"
#
# 输出：
#   msgbus/inbox/echo_wall/<UTC时间戳>_<from>_to_<to>.md
#
# 安全：
#   - 幂等：同名文件已存在则追加序号，不覆盖
#   - 绝不写入 Token/密码/量化闲鱼凭证（调用方自查，脚本只做兜底关键词过滤）
# =============================================================================
set -euo pipefail 2>/dev/null || set -euo

# ---- 参数解析 ----
FROM=""
TO=""
TITLE=""
BODY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --from)  FROM="$2";  shift 2 ;;
    --to)    TO="$2";    shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --body)  BODY="$2";  shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

if [ -z "$FROM" ] || [ -z "$TO" ]; then
  echo "用法: bash scripts/cnb_echo_ping.sh --from <角色> --to <角色> [--title <标题>] [--body <内容>]"
  exit 1
fi

# ---- 兜底敏感词过滤（Token/Key/密码）----
FORBIDDEN="token|api[_-]?key|password|secret|BEGIN.*PRIVATE|CNB_TOKEN|ACC_PRODUCT_CONFIG_V2"
if echo "$BODY" | grep -qiE "$FORBIDDEN"; then
  echo "⚠️ body 含疑似敏感信息，已拒绝写入（请脱敏后重试）"
  exit 2
fi

# ---- 目标目录（兼容云端容器与本地 E/G 盘两层）----
if [ -d "msgbus" ]; then
  WALL="msgbus/inbox/echo_wall"
else
  WALL="msgbus/inbox/echo_wall"
fi
mkdir -p "$WALL"

TS=$(date -u +%Y%m%d_%H%M%S)
BASE="${WALL}/${TS}_${FROM}_to_${TO}"
OUT="${BASE}.md"
i=1
while [ -e "$OUT" ]; do
  OUT="${BASE}_${i}.md"
  i=$((i+1))
done

# ---- 写痕迹 ----
{
  echo "> **群聊痕迹墙** · $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo ""
  echo "| 项 | 值 |"
  echo "|---|---|"
  echo "| 发件 | ${FROM} |"
  echo "| 收件 | ${TO} |"
  echo "| 标题 | ${TITLE:-（未填）} |"
  echo ""
  echo "## 内容"
  echo ""
  echo "${BODY:-（无内容）}"
} > "$OUT"

echo "✅ 已写入痕迹：$OUT"
