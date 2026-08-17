#!/usr/bin/env bash
# =============================================================================
# DeepSeek Harness 云端 NPC 入口（路径B：自定义镜像容器模式 · 超 Agent 编排运行时）
# =============================================================================
# 逻辑：
#   1. 先跑 quota_monitor.py 生成额度状态（QUOTA_STATUS/QUOTA_USED）
#   2. 后台启动 DeepSeek Harness 网关（deepseek-harness/harness_proxy.py），监听 8080
#      → OpenAI 兼容 /v1/chat/completions + /v1/models + /v1/orders 企微接单 + /console 控制台
#   3. 校验 8080 端口就绪
#   4. 前台保持存活（执行 CMD 传入的默认命令）
# 安全：鉴权全部来自环境变量注入（CNB_TOKEN / ACC_PRODUCT_CONFIG_V2），脚本/镜像零硬编码密钥
# =============================================================================
set -euo pipefail

QUOTA_PY="${QUOTA_PY:-/usr/local/bin/quota_monitor.py}"
HARNESS_DIR="${HARNESS_DIR:-/opt/deepseek-harness}"
HARNESS_PROXY="${HARNESS_PROXY:-$HARNESS_DIR/harness_proxy.py}"
HARNESS_PORT="${HARNESS_PORT:-8080}"

echo "[harness-npc] ==== 路径B：自定义镜像容器 NPC（DeepSeek Harness 超 Agent 运行时）启动 ===="
echo "[harness-npc] 模型基座 = ${CNB_MODEL:-deepseek-v4-flash} (reasoning_effort=${REASONING_EFFORT:-high})"
echo "[harness-npc] Harness 网关 = 0.0.0.0:${HARNESS_PORT}"

# ---- 1. 额度监控（尽力而为，失败不阻塞主流程）----
if [ -x "$QUOTA_PY" ]; then
  echo "[harness-npc] 运行额度监控 quota_monitor.py ..."
  python3 "$QUOTA_PY" >/tmp/quota_monitor.log 2>&1 || \
    echo "[harness-npc] ⚠️ quota_monitor 执行失败（不影响主流程）：$(tail -1 /tmp/quota_monitor.log)"
  if [ -f .quota_state.json ]; then
    echo "[harness-npc] 额度状态: $(python3 -c 'import json;d=json.load(open(".quota_state.json"));print(d.get("status"), d.get("ratio"))' 2>/dev/null || echo n/a)"
  fi
fi

# ---- 2. 确认 Harness 运行时文件就绪 ----
if [ -f "$HARNESS_PROXY" ]; then
  echo "[harness-npc] ✅ DeepSeek Harness 网关脚本就绪: $HARNESS_PROXY"
else
  echo "[harness-npc] ⚠️ $HARNESS_PROXY 不存在，尝试从工作区复制..."
  if [ -f /workspace/deepseek-harness/harness_proxy.py ]; then
    mkdir -p "$HARNESS_DIR"
    cp /workspace/deepseek-harness/*.py /workspace/deepseek-harness/*.json /workspace/deepseek-harness/*.html "$HARNESS_DIR"/ 2>/dev/null || true
  else
    echo "[harness-npc] ❌ Harness 运行时缺失，网关无法启动（仍继续前台存活）"
  fi
fi

# ---- 3. 后台启动 DeepSeek Harness 网关（监听 0.0.0.0:8080）----
if [ -f "$HARNESS_PROXY" ]; then
  echo "[harness-npc] 启动 DeepSeek Harness 网关（免费 deepseek-v4-flash 基座）..."
  cd "$HARNESS_DIR" && HARNESS_PORT="$HARNESS_PORT" HARNESS_HOST="0.0.0.0" python3 "$HARNESS_PROXY" >/tmp/harness.log 2>&1 &
  HARNESS_PID=$!

  # ---- 4. 等待网关端口就绪 ----
  for i in $(seq 1 30); do
    if (exec 3<>"/dev/tcp/127.0.0.1/$HARNESS_PORT") 2>/dev/null; then
      exec 3>&- 3<&- || true
      echo "[harness-npc] ✅ Harness 网关端口 $HARNESS_PORT 就绪（${i} 次探测）"
      break
    fi
    sleep 0.5
    if [ "$i" = "30" ]; then
      echo "[harness-npc] ⚠️ Harness 网关端口 $HARNESS_PORT 未就绪（请查看 /tmp/harness.log）"
      tail -5 /tmp/harness.log 2>/dev/null || true
    fi
  done
else
  HARNESS_PID=""
fi

# ---- 5. 前台执行传入命令（默认 CMD 为前台存活）----
if [ "$#" -gt 0 ]; then
  echo "[harness-npc] 执行入口命令: $*"
  trap 'echo "[harness-npc] 清理子进程..."; [ -n "$HARNESS_PID" ] && kill $HARNESS_PID 2>/dev/null || true' EXIT
  exec "$@"
fi

echo "[harness-npc] 容器前台存活中（DeepSeek Harness 网关已在后台运行，等待请求）..."
if [ -n "$HARNESS_PID" ]; then
  tail --pid="$HARNESS_PID" -f /dev/null
else
  tail -f /dev/null
fi
