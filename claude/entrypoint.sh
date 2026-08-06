#!/usr/bin/env bash
# =============================================================================
# Claude-Code 云端 NPC 入口（路径B：自定义镜像容器模式）
# 容器内启动：额度监控 + 适配层(127.0.0.1:8787) + 完整 Claude-Code CLI 服务
# =============================================================================
# 逻辑：
#   1. 先跑 quota_monitor.py 生成额度状态（QUOTA_STATUS/QUOTA_USED）
#   2. 后台启动 anthropic_to_cnb.py 适配层，监听 127.0.0.1:8787
#   3. 校验适配层端口就绪
#   4. 前台保持存活（执行 CMD 传入的默认命令，默认是前台跑适配层）
# 安全：鉴权全部来自环境变量注入，脚本/镜像零硬编码密钥
# =============================================================================
set -euo pipefail

ADAPTER_PY="${ADAPTER_PY:-/usr/local/bin/anthropic_to_cnb.py}"
QUOTA_PY="${QUOTA_PY:-/usr/local/bin/quota_monitor.py}"

echo "[claude-npc] ==== 路径B：自定义镜像容器 NPC 启动 ===="
echo "[claude-npc] 模型基座 = ${CNB_MODEL:-deepseek-v4-flash} (reasoning_effort=${REASONING_EFFORT:-high})"
echo "[claude-npc] 适配层   = http://${ADAPTER_HOST:-127.0.0.1}:${ADAPTER_PORT:-8787}"

# ---- 1. 额度监控（尽力而为，失败不阻塞主流程）----
if [ -x "$QUOTA_PY" ]; then
  echo "[claude-npc] 运行额度监控 quota_monitor.py ..."
  python3 "$QUOTA_PY" >/tmp/quota_monitor.log 2>&1 || \
    echo "[claude-npc] ⚠️ quota_monitor 执行失败（不影响主流程）：$(tail -1 /tmp/quota_monitor.log)"
  if [ -f .quota_state.json ]; then
    echo "[claude-npc] 额度状态: $(python3 -c 'import json;d=json.load(open(".quota_state.json"));print(d.get("status"), d.get("ratio"))' 2>/dev/null || echo n/a)"
  fi
fi

# ---- 2. 后台启动协议适配层（监听 127.0.0.1:8787）----
echo "[claude-npc] 启动 CNB 内置 DeepSeek-V4-Flash 适配层..."
python3 "$ADAPTER_PY" &
ADAPTER_PID=$!

# ---- 3. 等待适配层端口就绪 ----
PORT="${ADAPTER_PORT:-8787}"
for i in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/${ADAPTER_HOST:-127.0.0.1}/$PORT") 2>/dev/null; then
    exec 3>&- 3<&- || true
    echo "[claude-npc] ✅ 适配层端口 $PORT 就绪（${i} 次探测）"
    break
  fi
  sleep 0.5
  if [ "$i" = "30" ]; then
    echo "[claude-npc] ⚠️ 适配层端口 $PORT 未就绪（继续启动前台命令）"
  fi
done

# ---- 4. 完整 Claude-Code CLI 能力声明 ----
if command -v claude >/dev/null 2>&1; then
  echo "[claude-npc] Claude-Code CLI 已就绪: $(claude --version 2>/dev/null || echo '?')"
  echo "[claude-npc] ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
  echo "[claude-npc] 原生 MCP / 插件 / Skill 能力完整保留（路径B 不蒸馏不裁剪）"
else
  echo "[claude-npc] ⚠️ 未检测到 claude 命令（安装失败？回退 SDK 包，见 Dockerfile）"
fi

# ---- 5. 前台执行传入命令（默认 CMD 为前台跑适配层）----
# 说明：若 ENTRYPOINT 收到自定义命令参数（如 claude / bash），优先执行之；
#       否则执行默认 CMD（python3 anthropic_to_cnb.py）保持前台存活。
if [ "$#" -gt 0 ]; then
  echo "[claude-npc] 执行入口命令: $*"
  # 确保退出时清理后台适配层
  trap 'echo "[claude-npc] 清理子进程..."; kill $ADAPTER_PID 2>/dev/null || true' EXIT
  exec "$@"
fi

echo "[claude-npc] 适配层前台运行中 (http://127.0.0.1:$PORT)，等待请求..."
trap 'echo "[claude-npc] 清理子进程..."; kill $ADAPTER_PID 2>/dev/null || true' EXIT
wait $ADAPTER_PID
