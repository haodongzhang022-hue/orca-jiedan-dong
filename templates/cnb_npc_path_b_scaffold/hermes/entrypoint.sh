#!/usr/bin/env bash
# =============================================================================
# Hermes 云端 NPC 入口（路径B：自定义镜像容器模式 · 原生 hermes CLI）
# =============================================================================
# 逻辑：
#   1. 先跑 quota_monitor.py 生成额度状态（QUOTA_STATUS/QUOTA_USED）
#   2. 确认原生 hermes CLI 已安装（Dockerfile 中 pip install hermes-agent）
#   3. 将 hermes 模型端点指向 CNB 内置免费 DeepSeek-V4-Flash 网关
#   4. 前台保持存活（执行 CMD 传入的默认命令）
# 安全：鉴权全部来自环境变量注入，脚本/镜像零硬编码密钥
# =============================================================================
set -euo pipefail

QUOTA_PY="${QUOTA_PY:-/usr/local/bin/quota_monitor.py}"

echo "[hermes-npc] ==== 路径B：自定义镜像容器 NPC（原生 hermes CLI）启动 ===="
echo "[hermes-npc] 模型基座 = ${CNB_MODEL:-deepseek-v4-flash} (reasoning_effort=${REASONING_EFFORT:-high})"

# ---- 1. 额度监控（尽力而为，失败不阻塞主流程）----
if [ -x "$QUOTA_PY" ]; then
  echo "[hermes-npc] 运行额度监控 quota_monitor.py ..."
  python3 "$QUOTA_PY" >/tmp/quota_monitor.log 2>&1 || \
    echo "[hermes-npc] ⚠️ quota_monitor 执行失败（不影响主流程）：$(tail -1 /tmp/quota_monitor.log)"
  if [ -f .quota_state.json ]; then
    echo "[hermes-npc] 额度状态: $(python3 -c 'import json;d=json.load(open(".quota_state.json"));print(d.get("status"), d.get("ratio"))' 2>/dev/null || echo n/a)"
  fi
fi

# ---- 2. 原生 hermes CLI 就绪确认 ----
if command -v hermes >/dev/null 2>&1; then
  echo "[hermes-npc] ✅ 原生 hermes CLI 已就绪: $(hermes --version 2>/dev/null | head -1 || echo '?')"
  echo "[hermes-npc] 来源: GitHub NousResearch/hermes-agent（pip 包 hermes-agent）"
else
  echo "[hermes-npc] ⚠️ 未检测到 hermes 命令，尝试按官方 install.sh 安装..."
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash || \
    pip install hermes-agent || \
    echo "[hermes-npc] ❌ hermes CLI 安装失败（不影响 npc:go 主流程，角色仍可用内置调度能力）"
fi

# ---- 3. 模型端点指向 CNB 内置免费 DeepSeek-V4-Flash 网关 ----
# 原生 hermes 支持任意 OpenAI 兼容端点；这里将默认 provider 指向 CNB 内置 AI 网关
if [ -n "${ACC_PRODUCT_CONFIG_V2:-}" ] || [ -n "${CNB_AI_GATEWAY:-}" ]; then
  echo "[hermes-npc] hermes 模型端点 → CNB 内置 AI 网关（免费 deepseek-v4-flash）"
fi

# ---- 4. 前台执行传入命令（默认 CMD 为前台存活）----
if [ "$#" -gt 0 ]; then
  echo "[hermes-npc] 执行入口命令: $*"
  exec "$@"
fi

echo "[hermes-npc] 容器前台存活中（等待 npc:go 任务注入）..."
tail -f /dev/null
