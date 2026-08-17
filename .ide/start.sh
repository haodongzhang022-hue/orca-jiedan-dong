#!/usr/bin/env bash
# =============================================================================
# CNB 云原生开发环境 · 双方案并行启动脚本
# =============================================================================
# 职责：
#   A. 后台拉起 CNB 内置免费 DeepSeek-V4-Flash 网关适配层（127.0.0.1:8787，
#      Anthropic 协议 → CNB OpenAI Chat Completions 免费网关，供 Hermes Web UI 使用）
#   B. 后台启动 DeepSeek Harness 云端运行时（harness_proxy.py，端口 8080）
#      OpenAI 兼容网关 + 企业微信接单 + 编排 Agent + Web 控制台
#   C. 前台运行 Hermes Web UI（node dist/server/index.js，端口 6060，监听 0.0.0.0）
#
# 三者并行存在，互相独立，均可正常工作。
#
# 环境变量（全部运行时注入，镜像零硬编码密钥）：
#   CNB_TOKEN / ACC_PRODUCT_CONFIG_V2   → CNB 免费网关鉴权
#   CNB_MODEL                           → 默认 deepseek-v4-flash
#   CNB_AI_GATEWAY                      → 网关地址（可选，默认自动解析）
# =============================================================================
set -euo pipefail

echo "[cnb-start] ==== 双方案并行启动（Hermes Web UI + DeepSeek Harness）===="
echo "[cnb-start] 模型基座 = ${CNB_MODEL:-deepseek-v4-flash}（CNB 免费）"

# ---- 1. 环境变量校验（不打印密钥明文）----
if [ -n "${CNB_TOKEN:-}" ]; then
  echo "[cnb-start] CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）✅"
else
  echo "[cnb-start] ⚠️ CNB_TOKEN 未注入，免费网关调用将失败"
fi

# ---- 2. 启动 CNB 免费网关适配层（供 Hermes Web UI 使用，后台）----
if command -v python3 >/dev/null 2>&1 && [ -f /usr/local/bin/anthropic_to_cnb.py ]; then
  echo "[cnb-start] 启动 CNB 免费 DeepSeek-V4-Flash 网关适配层 (127.0.0.1:8787)..."
  nohup python3 /usr/local/bin/anthropic_to_cnb.py >/tmp/anthropic_to_cnb.log 2>&1 &
  echo "[cnb-start] 适配层 PID: $!"
else
  echo "[cnb-start] ⚠️ 适配层不可用，Hermes Web UI 将以默认 provider 运行"
fi

# ---- 3. 启动 DeepSeek Harness 云端运行时（后台，端口 8080）----
HARNESS_PORT="${HARNESS_PORT:-8080}"
if [ -f /opt/deepseek-harness/harness_proxy.py ]; then
  echo "[cnb-start] 启动 DeepSeek Harness 云端运行时 (0.0.0.0:${HARNESS_PORT})..."
  cd /opt/deepseek-harness
  nohup python3 harness_proxy.py --port "$HARNESS_PORT" --host 0.0.0.0 >/tmp/harness.log 2>&1 &
  echo "[cnb-start] Harness PID: $!"
  # 等待 harness 就绪
  sleep 2
  if (echo >/dev/tcp/127.0.0.1/$HARNESS_PORT) 2>/dev/null; then
    echo "[cnb-start] ✅ DeepSeek Harness 已监听 0.0.0.0:${HARNESS_PORT}"
  else
    echo "[cnb-start] ⚠️ Harness 未就绪，查看 /tmp/harness.log"
  fi
else
  echo "[cnb-start] ⚠️ /opt/deepseek-harness/harness_proxy.py 不存在，跳过 Harness 启动"
fi

# ---- 4. 前台运行 Hermes Web UI（官方入口，端口 6060）----
echo "[cnb-start] 启动 Hermes Web UI (PORT=${PORT:-6060}, BIND_HOST=${BIND_HOST:-0.0.0.0})..."
cd /app || cd /
exec node dist/server/index.js
