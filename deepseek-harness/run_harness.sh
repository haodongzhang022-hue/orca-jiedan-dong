#!/usr/bin/env bash
# =============================================================================
# DeepSeek Harness · 一键本地启动 + 自检
# =============================================================================
# 用法：
#   bash deepseek-harness/run_harness.sh [--port 8080]
# 说明：
#   - 启动免费 DeepSeek-V4-Flash 网关 + 企微接单 + 编排 Agent
#   - 需要 CNB_TOKEN 环境变量（云端容器自动注入）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT="${1:-8080}"
if [ "${1:-}" = "--port" ]; then PORT="${2:-8080}"; fi

echo "==== DeepSeek Harness 自检 ===="

# 1. 语法检查
python3 -c "import ast; ast.parse(open('harness_proxy.py').read()); print('[ok] harness_proxy.py 语法')"
python3 -c "import ast; ast.parse(open('harness_agent.py').read()); print('[ok] harness_agent.py 语法')"

# 2. CNB_TOKEN 检查（只显示前缀，不打印明文）
if [ -n "${CNB_TOKEN:-}" ]; then
  echo "[ok] CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）"
else
  echo "[warn] CNB_TOKEN 未注入——免费网关将无法调用"
fi

# 3. 启动网关
echo "==== 启动 Harness 网关 (0.0.0.0:$PORT) ===="
exec python3 harness_proxy.py --port "$PORT" --host 0.0.0.0
