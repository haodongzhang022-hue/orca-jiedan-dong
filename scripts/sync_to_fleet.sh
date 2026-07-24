#!/usr/bin/env bash
# sync_to_fleet.sh —— 把 autopilot 因沙箱写不进 fleet_exchange/incoming 的待分发任务同步过去
# 用法：在项目根目录运行 bash scripts/sync_to_fleet.sh

set -euo pipefail

PENDING="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/待分发任务"
FLEET_IN="E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/incoming"

mkdir -p "$FLEET_IN"

count=0
for f in "$PENDING"/*.md; do
  [ -f "$f" ] || continue
  echo "[SYNC] $f -> $FLEET_IN/"
  cp "$f" "$FLEET_IN/"
  rm "$f"
  ((count++)) || true
done

echo "✅ 已同步 $count 个任务到 $FLEET_IN"
