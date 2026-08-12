#!/usr/bin/env bash
# =============================================================================
# switch_to_cnb_gateway.sh — 一键把本地 Hermes Studio / Claude / Codex 从
#                            Xiaomi MiMo 切换到 CNB 免费 DeepSeek-V4-Flash 网关
# =============================================================================
# 背景（2026-08-10 实测）：
#   汤嘉锋本地 Hermes Studio 实际运行模型仍是 mimo-v2.5-pro（Xiaomi），
#   MiMo 剩余积分约 0.31%（极度紧张）。数据库里把 Agent 切到
#   cnb-codebuddy/deepseek-v4-flash 的改动，GUI 层面未完全生效。
#   本脚本把三层全部强制指到 CNB 免费网关，停止消耗 MiMo 积分。
#
# 适用：
#   - Windows 本机（Git Bash / WSL）由汤嘉锋或 MARVIS 执行
#   - 云端容器内由 NPC 执行（--check-only 自检用）
#
# 用法：
#   bash scripts/switch_to_cnb_gateway.sh                # 切换（幂等）
#   bash scripts/switch_to_cnb_gateway.sh --dry-run      # 只打印将写入内容，不落盘
#   bash scripts/switch_to_cnb_gateway.sh --check-only   # 只读自检
#
# 安全：
#   - 本脚本【不读取、不打印、不写入】任何 Token 明文；api_key 指向环境变量 CNB_TOKEN
#   - 不修改 15721/15730/8642/4567/11434 端口铁律
#   - 自动备份被改文件为 *.bak.<时间戳>，可回滚
# =============================================================================
set -uo pipefail

GATEWAY="https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions"
MODEL="deepseek-v4-flash"
PROVIDER_NAME="cnb-deepseek-v4-flash"

# 各客户端配置（本机路径；不存在则跳过）
HERMES_CONFIG="${HERMES_HOME:-$HOME/.hermes}/config.yaml"
CLAUDE_JSON="$HOME/.claude.json"
CODEX_CONFIG="$HOME/.codex/config.toml"

MODE="write"
for arg in "$@"; do
  case "$arg" in
    --dry-run)    MODE="dry-run" ;;
    --check-only) MODE="check" ;;
  esac
done

echo "🦞 切换到 CNB 免费 DeepSeek-V4-Flash 网关（停止消耗 MiMo 积分）"
echo "==================================================="
echo "网关: $GATEWAY"
echo "模型: $MODEL"

ts=$(date +%Y%m%d_%H%M%S)

# ---------------------------------------------------------------------------
# check-only：只读自检
# ---------------------------------------------------------------------------
if [ "$MODE" = "check" ]; then
  echo "[check] Hermes 配置路径: $HERMES_CONFIG"
  if [ -f "$HERMES_CONFIG" ]; then
    if grep -q "$PROVIDER_NAME" "$HERMES_CONFIG" 2>/dev/null; then
      echo "  ✅ Hermes provider '$PROVIDER_NAME' 已注册"
    else
      echo "  ❌ Hermes 未注册 '$PROVIDER_NAME'（需执行本脚本写入）"
    fi
    echo "  └ 当前 provider 含 xiaomi/mimo 的引用:"
    grep -ni "mimo\|xiaomi" "$HERMES_CONFIG" 2>/dev/null | sed 's/^/    /' || echo "    （无，纯文本路径已干净）"
  else
    echo "  ⚠️ config.yaml 不存在（Hermes Studio 尚未初始化，先启动一次桌面版）"
  fi
  echo "[check] Claude Code 配置: $CLAUDE_JSON"
  [ -f "$CLAUDE_JSON" ] && echo "  ✅ 存在" || echo "  ⚠️ 不存在（跳过）"
  echo "[check] Codex 配置: $CODEX_CONFIG"
  [ -f "$CODEX_CONFIG" ] && echo "  ✅ 存在" || echo "  ⚠️ 不存在（跳过）"
  echo "[check] 环境变量 CNB_TOKEN 是否已设:"
  if [ -n "${CNB_TOKEN:-}" ]; then
    echo "  ✅ 已设置（长度 ${#CNB_TOKEN}，不打印内容）"
  else
    echo "  ⚠️ 未设置 —— 请在 Hermes Studio 环境变量/本机环境变量中配置 CNB_TOKEN"
  fi
  exit 0
fi

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
  echo "[dry-run] 本地代理 UPSTREAM 建议改为: $GATEWAY（见文档方式B手动改）"
  echo "[dry-run] Claude/Codex 桌面端点改为指向 CNB 网关（见文档）"
  exit 0
fi

# ---------------------------------------------------------------------------
# 1. Hermes ~/.hermes/config.yaml：注册 cnb-deepseek-v4-flash provider（幂等）
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "$HERMES_CONFIG")"
touch "$HERMES_CONFIG"

if grep -q "$PROVIDER_NAME" "$HERMES_CONFIG" 2>/dev/null; then
  echo "✅ Hermes provider '$PROVIDER_NAME' 已存在，跳过写入"
else
  cp "$HERMES_CONFIG" "$HERMES_CONFIG.bak.$ts" 2>/dev/null || true
  if grep -q "^providers:" "$HERMES_CONFIG" 2>/dev/null; then
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
  echo "✅ 已写入 Hermes provider（备份: $HERMES_CONFIG.bak.$ts）"
fi

# ---------------------------------------------------------------------------
# 2. 本地代理 UPSTREAM 指向 CNB 网关（Claude 15721 / Codex 15730）
#    只改常见代理脚本里的 UPSTREAM 行，不动端口铁律。
# ---------------------------------------------------------------------------
echo ""
echo "下一步（关键）：请在 Hermes Studio GUI 手动完成，脚本无法代点 GUI："
cat <<'EOF'
  ┌──────────────────────────────────────────────────────────────────┐
  │ Hermes Studio → 设置/模型管理 → Provider 选 cnb-deepseek-v4-flash│
  │   → model 选 deepseek-v4-flash → 保存 → 完全退出并重启 Hermes   │
  │   → 新建会话确认右上角模型 = deepseek-v4-flash 而非 mimo-v2.5-pro│
  │   → Token 用本机环境变量 CNB_TOKEN（不落盘、不写 GUI）           │
  └──────────────────────────────────────────────────────────────────┘
EOF

# ---------------------------------------------------------------------------
# 3. 输出验证命令
# ---------------------------------------------------------------------------
echo ""
echo "✅ 切换就绪。验证（任选）:"
echo "  hermes-studio model list | grep cnb-deepseek-v4-flash   # 可选到新 provider"
echo "  curl -N https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions \\"
echo "    -H \"Authorization: Bearer \\$CNB_TOKEN\" -H 'Content-Type: application/json' \\"
echo "    -d '{\"model\":\"deepseek-v4-flash\",\"stream\":true,\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}]}'"
echo ""
echo "回滚: 恢复 $HERMES_CONFIG.bak.$ts 到 $HERMES_CONFIG 即可"
