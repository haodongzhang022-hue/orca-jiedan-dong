#!/usr/bin/env bash
# Claude-Code 云端 NPC 入口（路径B：容器内启动适配层 + Claude-Code CLI 服务）
set -euo pipefail
echo "[claude-npc] 启动 CNB 内置 DeepSeek-V4-Flash 适配层..."
python3 /usr/local/bin/anthropic_to_cnb.py &
ADAPTER_PID=$!
trap "kill $ADAPTER_PID 2>/dev/null || true" EXIT

echo "[claude-npc] 适配层已启动 (http://127.0.0.1:8787)"
echo "[claude-npc] ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "[claude-npc] 等待 Claude-Code CLI 请求..."
wait $ADAPTER_PID
