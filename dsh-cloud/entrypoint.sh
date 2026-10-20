#!/usr/bin/env bash
# =============================================================================
# CNB 云端 dsh + ds-bot 群聊界面 · 启动编排
# =============================================================================
# 三层进程，各司其职：
#
#   [1] CNB LLM Adapter  127.0.0.1:15741
#       标准 OpenAI 接口 → CNB 免费网关（强制流式 + 非流式聚合）
#       CNB 403/400/超时时回落 FALLBACK_BASE
#
#   [2] dsh web          127.0.0.1:8831
#       ⚠️ 必须绑 127.0.0.1：源码明确禁止 --host 0.0.0.0（防 RCE 暴露）
#       ⚠️ /api 有 browser-trust fence，非信任 Host 一律 403
#
#   [3] Host Rewrite Proxy  0.0.0.0:8830
#       对外唯一入口。把 Host 改写成 127.0.0.1:8831 绕过 fence，
#       并把 127.0.0.1 的 dsh web 暴露到 0.0.0.0 供 CNB PORTS 转发。
#       本机实测：直连+fake Host = 403；经代理+fake Host = 401（放行）
#
# 访问方式：CNB WebIDE → PORTS 面板转发 8830 → https://{实例ID}-8830.cnb.run
# =============================================================================
set -uo pipefail

ADAPTER_PORT="${ADAPTER_PORT:-15741}"
DSH_PORT="${DSH_PORT:-8831}"
PUBLIC_PORT="${PUBLIC_PORT:-8830}"
DSH_HOME="${DSH_HOME:-/opt/dsh-home}"
LOG_DIR=/tmp/dsh-cloud
mkdir -p "$LOG_DIR" /tmp
export DSH_HOME
export CNB_ADAPTER_KEY="${CNB_ADAPTER_KEY:-local-placeholder-key}"

echo "============================================================="
echo "[dsh-cloud] 启动 dsh + ds-bot 群聊界面（CNB 免费 DeepSeek V4）"
echo "[dsh-cloud] 模型基座  = ${CNB_MODEL:-deepseek-v4-flash}"
echo "[dsh-cloud] 端口编排  = 适配层:${ADAPTER_PORT}  dsh:${DSH_PORT}  对外:${PUBLIC_PORT}"
echo "============================================================="

if [ -n "${CNB_TOKEN:-}" ]; then
  echo "[dsh-cloud] CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）"
else
  echo "[dsh-cloud] ⚠️ CNB_TOKEN 未注入 —— 主通道会 403/401，需有回落通道"
fi

# ---- [1] CNB LLM Adapter ----
if [ -f /opt/dsh-cloud/cnb_llm_adapter.py ]; then
  echo "[dsh-cloud] [1/3] 启动 CNB LLM Adapter (127.0.0.1:${ADAPTER_PORT})..."
  python3 /opt/dsh-cloud/cnb_llm_adapter.py --host 127.0.0.1 --port "$ADAPTER_PORT" \
    >"$LOG_DIR/adapter.log" 2>&1 &
  ADAPTER_PID=$!
  echo "[dsh-cloud]        PID=$ADAPTER_PID  日志=$LOG_DIR/adapter.log"
else
  echo "[dsh-cloud] ⚠️ cnb_llm_adapter.py 不存在"
  ADAPTER_PID=0
fi

# ---- [2] dsh web（绑 127.0.0.1，禁止 0.0.0.0）----
echo "[dsh-cloud] [2/3] 启动 dsh web (127.0.0.1:${DSH_PORT})..."
if ! command -v dsh >/dev/null 2>&1; then
  echo "[dsh-cloud] ❌ dsh 命令不存在，镜像构建可能失败"
  exit 1
fi

# --trusted-host 双保险：即使代理改写失效，loopback 字面量也应被放行
dsh --profile web --host 127.0.0.1 --port "$DSH_PORT" --no-open \
    --trusted-host 127.0.0.1 --trusted-host localhost \
    >"$LOG_DIR/dsh-web.log" 2>&1 &
DSH_PID=$!
echo "[dsh-cloud]        PID=$DSH_PID  日志=$LOG_DIR/dsh-web.log"

# ---- 等 dsh web 真正监听（L4：连续探测 socket，不看进程存在）----
echo "[dsh-cloud]        等待 dsh web 就绪..."
ready=0
i=0
while [ "$i" -lt 90 ]; do
  i=$((i + 1))
  if (echo >/dev/tcp/127.0.0.1/"$DSH_PORT") 2>/dev/null; then
    ready=1
    echo "[dsh-cloud]        ✅ dsh web 已监听 ${DSH_PORT}（第 ${i} 次探测）"
    break
  fi
  sleep 1
done
if [ "$ready" = "0" ]; then
  echo "[dsh-cloud] ⚠️ dsh web 90 秒内未就绪，尾部日志："
  tail -30 "$LOG_DIR/dsh-web.log" 2>/dev/null
fi

# ---- [3] Host 改写代理（对外唯一入口）----
echo "[dsh-cloud] [3/3] 启动 Host Rewrite Proxy (0.0.0.0:${PUBLIC_PORT} → 127.0.0.1:${DSH_PORT})..."
if [ -f /opt/dsh-cloud/host_rewrite_proxy.py ]; then
  python3 /opt/dsh-cloud/host_rewrite_proxy.py \
    --listen-host 0.0.0.0 --listen-port "$PUBLIC_PORT" \
    --target-host 127.0.0.1 --target-port "$DSH_PORT" \
    >"$LOG_DIR/proxy.log" 2>&1 &
  PROXY_PID=$!
  echo "[dsh-cloud]        PID=$PROXY_PID  日志=$LOG_DIR/proxy.log"
else
  echo "[dsh-cloud] ⚠️ host_rewrite_proxy.py 不存在，外部将无法访问"
  PROXY_PID=0
fi
sleep 2

# ---- 打印访问凭证（token 从 dsh 日志里抓，不落任何文件）----
TOKEN="$(grep -o -E 'token=[A-Za-z0-9_-]+' "$LOG_DIR/dsh-web.log" 2>/dev/null | head -1 | cut -d= -f2)"
echo "============================================================="
if [ -f /opt/dsh-cloud/install-report.txt ]; then
  echo "[dsh-cloud] 安装报告："
  sed 's/^/    /' /opt/dsh-cloud/install-report.txt
fi
if [ -n "${TOKEN:-}" ]; then
  echo "[dsh-cloud] ✅ 访问地址（PORTS 转发 ${PUBLIC_PORT} 后）："
  echo "             https://{实例ID}-${PUBLIC_PORT}.cnb.run/?token=${TOKEN}"
  echo "[dsh-cloud] 本地自检： http://127.0.0.1:${PUBLIC_PORT}/?token=${TOKEN}"
else
  echo "[dsh-cloud] ⚠️ 未从日志抓到 token，请查看 $LOG_DIR/dsh-web.log"
fi
echo "============================================================="
echo "[dsh-cloud] 自检命令（容器内）："
echo "   curl -s http://127.0.0.1:${ADAPTER_PORT}/health"
echo "   curl -s -H 'Host: test.cnb.run' http://127.0.0.1:${PUBLIC_PORT}/"

# ---- 前台守护：任一关键进程退出即打印原因（不静默假活）----
while true; do
  sleep 20
  if [ "$DSH_PID" != "0" ] && ! kill -0 "$DSH_PID" 2>/dev/null; then
    echo "[dsh-cloud] ❌ dsh web 已退出，尾部日志："
    tail -40 "$LOG_DIR/dsh-web.log" 2>/dev/null
    exit 1
  fi
  if [ "$PROXY_PID" != "0" ] && ! kill -0 "$PROXY_PID" 2>/dev/null; then
    echo "[dsh-cloud] ❌ Host 代理已退出，重启一次..."
    python3 /opt/dsh-cloud/host_rewrite_proxy.py \
      --listen-host 0.0.0.0 --listen-port "$PUBLIC_PORT" \
      --target-host 127.0.0.1 --target-port "$DSH_PORT" \
      >>"$LOG_DIR/proxy.log" 2>&1 &
    PROXY_PID=$!
  fi
done
