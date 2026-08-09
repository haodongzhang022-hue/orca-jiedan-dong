#!/usr/bin/env bash
# =============================================================================
# one_click_cnb_gateway.sh — 一键接入 CNB 免费基座（需求④）
# =============================================================================
# 用途：
#   把本地 Hermes Studio 桌面编排的模型端点指向 CNB 免费网关 deepseek-v4-flash，
#   零成本、一键完成。配套输出云端云上复刻指引 + 群聊痕迹墙联动说明。
#
# 适用：
#   - Windows 本机（Git Bash / WSL）由汤嘉锋或 MARVIS 执行
#   - 云端容器内由 NPC 执行（此时 --check-only 自检用）
#
# 用法：
#   bash scripts/one_click_cnb_gateway.sh             # 写入 provider 配置（自动）
#   bash scripts/one_click_cnb_gateway.sh --dry-run   # 只打印将写入的内容，不落盘
#   bash scripts/one_click_cnb_gateway.sh --check-only # 只读自检（容器/本机）
#
# 安全：
#   - 本脚本【不读取、不打印、不写入】任何 Token 明文
#   - api_key 指向环境变量 CNB_TOKEN（由调用方在 Hermes Studio 或本机环境变量设置）
#   - 不修改 15721/15730/8642/4567/11434 端口铁律
# =============================================================================
set -euo pipefail

GATEWAY="https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions"
MODEL="deepseek-v4-flash"
PROVIDER_NAME="cnb-deepseek-v4-flash"
HERMES_CONFIG="${HERMES_HOME:-$HOME/.hermes}/config.yaml"

MODE="write"
for arg in "$@"; do
  case "$arg" in
    --dry-run)   MODE="dry-run" ;;
    --check-only) MODE="check" ;;
  esac
done

echo "🦞 Hermes Studio 一键接入 CNB 免费基座（deepseek-v4-flash · 0 成本）"
echo "==================================================="
echo "网关: $GATEWAY"
echo "模型: $MODEL"

# ---- check-only：只读自检 ----
if [ "$MODE" = "check" ]; then
  echo "[check] Hermes 配置路径: $HERMES_CONFIG"
  if [ -f "$HERMES_CONFIG" ]; then
    echo "[check] 已存在 config.yaml，当前 providers 含 cnb-deepseek-v4-flash:"
    grep -n "cnb-deepseek-v4-flash" "$HERMES_CONFIG" || echo "  （未找到，需要执行本脚本写入）"
  else
    echo "[check] config.yaml 不存在（Hermes Studio 尚未初始化，先启动一次桌面版）"
  fi
  echo "[check] 环境变量 CNB_TOKEN 是否已设:"
  [ -n "${CNB_TOKEN:-}" ] && echo "  ✅ 已设置（长度 ${#CNB_TOKEN}，不打印内容）" || echo "  ⚠️ 未设置，请在 Hermes Studio 环境变量中配置"
  exit 0
fi

# ---- dry-run：打印不落盘 ----
PROVIDER_BLOCK=$(cat <<YAML
  - name: $PROVIDER_NAME
    base_url: $GATEWAY
    api_key_env: CNB_TOKEN
    model: $MODEL
YAML
)

if [ "$MODE" = "dry-run" ]; then
  echo "---- 将写入 $HERMES_CONFIG 的 provider ----"
  echo "$PROVIDER_BLOCK"
  echo "----------------------------------------"
  exit 0
fi

# ---- write：真实写入（幂等） ----
mkdir -p "$(dirname "$HERMES_CONFIG")"
touch "$HERMES_CONFIG"

if grep -q "$PROVIDER_NAME" "$HERMES_CONFIG"; then
  echo "✅ provider '$PROVIDER_NAME' 已存在，无需重复写入"
else
  # 简单追加到 providers: 段（若文件无 providers: 则新建一节）
  if grep -q "^providers:" "$HERMES_CONFIG"; then
    cat >> "$HERMES_CONFIG" <<YAML
  - name: $PROVIDER_NAME
    base_url: $GATEWAY
    api_key_env: CNB_TOKEN
    model: $MODEL
YAML
  else
    cat >> "$HERMES_CONFIG" <<YAML

providers:
  - name: $PROVIDER_NAME
    base_url: $GATEWAY
    api_key_env: CNB_TOKEN
    model: $MODEL
YAML
  fi
  echo "✅ 已写入 $HERMES_CONFIG"
fi

echo ""
echo "下一步（在 Hermes Studio 模型管理界面）："
echo "  1. 选择 provider  cnb-deepseek-v4-flash"
echo "  2. 确认环境变量 CNB_TOKEN 已设置（本机，不落盘）"
echo "  3. 验证: hermes-studio model list"
echo ""
echo "云端配套（本 PR 已交付）："
echo "  - 云上复刻 Web GUI：仓库点「云原生开发」→ 浏览器开 https://{id}-6060.cnb.run"
echo "  - 群聊痕迹墙：msgbus/inbox/echo_wall/（云端 NPC 交流可见）"
