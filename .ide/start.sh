#!/usr/bin/env bash
# =============================================================================
# CNB 云原生开发环境 · DeepSeek Harness 云端控制台启动脚本
# =============================================================================
# 职责：
#   1. 启动 DeepSeek Harness OpenAI 兼容网关（harness_proxy.py，端口 8080）
#   2. 网关内集成：/v1/chat/completions(免费V4Flash流式) /v1/models
#      /v1/orders(企业微信接单建档) /harness(编排Agent) /console(控制台)
#   3. 鉴权全程环境变量注入（CNB_TOKEN），镜像零硬编码密钥
#
# 通过 CNB WebIDE PORTS 端口映射，浏览器打开 https://{id}-8080.cnb.run 即控制台
# =============================================================================
set -euo pipefail

echo "[cnb-harness] ==== DeepSeek Harness 云端控制台启动 ===="
echo "[cnb-harness] 模型基座 = ${CNB_MODEL:-deepseek-v4-flash}（CNB 免费）"

# ---- 1. 环境变量注入校验（不打印密钥明文，仅提示）----
if [ -n "${CNB_TOKEN:-}" ]; then
  echo "[cnb-harness] CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）✅"
else
  echo "[cnb-harness] ⚠️ CNB_TOKEN 未注入，免费网关调用将失败（容器内默认环境可能自动注入）"
fi

# ---- 2. 启动 DeepSeek Harness 网关（前台保持存活）----
PORT="${HARNESS_PORT:-8080}"
echo "[cnb-harness] 启动 DeepSeek Harness 网关 (0.0.0.0:$PORT)..."
cd /opt/deepseek-harness
exec python3 harness_proxy.py --port "$PORT" --host 0.0.0.0
