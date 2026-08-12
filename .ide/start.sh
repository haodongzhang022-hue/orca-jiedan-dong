#!/usr/bin/env bash
# =============================================================================
# CNB 云原生开发环境 · Hermes Studio Web GUI 启动脚本
# =============================================================================
# 职责：
#   1. 后台拉起 CNB 内置免费 DeepSeek-V4-Flash 网关适配层（127.0.0.1:8787，
#      Anthropic 协议 → CNB OpenAI Chat Completions 免费网关）
#   2. 前台运行 Hermes Web UI（node dist/server/index.js，端口 6060，监听 0.0.0.0）
#   3. 通过 CNB_WELCOME_CMD 或环境变量可注入 token（仅运行时，不落镜像）
#
# 环境变量（全部运行时注入，镜像零硬编码密钥）：
#   CNB_TOKEN / ACC_PRODUCT_CONFIG_V2   → CNB 免费网关鉴权
#   CNB_MODEL                           → 默认 deepseek-v4-flash
#   CNB_AI_GATEWAY                      → 网关地址（可选，默认自动解析）
#   PORT / BIND_HOST                    → Web UI 监听（默认 6060 / 0.0.0.0）
# =============================================================================
set -euo pipefail

# ---- 1. 启动 CNB 免费网关适配层（后台，失败不阻断 Web UI）----
if command -v python3 >/dev/null 2>&1 && [ -f /usr/local/bin/anthropic_to_cnb.py ]; then
  echo "[cnb-hermes-studio] 启动 CNB 免费 DeepSeek-V4-Flash 网关适配层 (127.0.0.1:8787)..."
  nohup python3 /usr/local/bin/anthropic_to_cnb.py >/tmp/anthropic_to_cnb.log 2>&1 &
  echo "[cnb-hermes-studio] 适配层 PID: $!"
else
  echo "[cnb-hermes-studio] ⚠️ 适配层不可用，Web UI 将以默认 provider 运行"
fi

# ---- 2. 前台运行 Hermes Web UI（官方入口）----
echo "[cnb-hermes-studio] 启动 Hermes Web UI (PORT=${PORT:-6060}, BIND_HOST=${BIND_HOST:-0.0.0.0})..."
cd /app || cd /
exec node dist/server/index.js
