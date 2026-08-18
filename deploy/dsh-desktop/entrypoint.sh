#!/usr/bin/env bash
# =============================================================================
# DeepSeek Harness Desktop 可复用镜像 · 容器启动入口
# =============================================================================
# 职责（先镜像实例化容器的运行期逻辑）：
#   A. 动态生成 $DSH_HOME/settings.yaml：自定义 provider 指向 CNB 内置免费
#      DeepSeek-V4-Flash 网关（网关地址/鉴权 Token 全部来自容器环境变量，
#      零硬编码密钥、零外部公网 API）。
#   B. 后台启动原版 deepseek-harness WebUI，容器内监听 127.0.0.1:8080（loopback）。
#      → 与本地 3080 界面 1:1，全部插件/Agent 编排/Browser-Bridge 完整保留。
#      ⚠️ 官方安全限制禁止 --host 0.0.0.0（会暴露远程代码执行），因此容器内保持
#         loopback，对外 8080 访问靠 `docker run -p 8080:8080` 端口映射完成。
#   C. 后台启动自研 harness，监听 127.0.0.1:8081（容器内网，不对外）。
#      → 保留 /v1/orders 企微接单、/harness 编排接口，接单流水线不中断。
#   C2. 后台启动本机 3081 网关（双模式 MCP 插件，HTTP 兼容模式 127.0.0.1:3081）。
#      → 供本机/内网工具 base_url=http://127.0.0.1:3081 出站调用 CNB 免费模型。
#      ⚠️ 3080 留给 DeepSeek-Harness WebUI，避免端口冲突。
#   D. 前台保持存活，便于容器被监控/重建。
#
# 环境变量（全部运行时注入）：
#   CNB_AI_GATEWAY        → CNB 免费网关地址（如 https://api.cnb.cool/.../ai/chat/completions）
#   CNB_TOKEN             → CNB 网关鉴权 Token
#   CNB_MODEL             → 模型名（默认 deepseek-v4-flash）
#   DSH_WEB_PORT          → 原版 WebUI 监听端口（默认 8080）
#   HARNESS_PORT          → 自研 harness 监听端口（默认 8081）
#   GW_PORT               → 本机 3081 网关监听端口（默认 3081；3080 留给 dsh web WebUI）
# =============================================================================
set -euo pipefail

echo "[dsh-entrypoint] ==== DeepSeek Harness Desktop 可复用镜像 · 容器实例启动 ===="

# ---- 0. 默认值 ----
DSH_WEB_PORT="${DSH_WEB_PORT:-8080}"
HARNESS_PORT="${HARNESS_PORT:-8081}"
CNB_MODEL="${CNB_MODEL:-deepseek-v4-flash}"
DSH_HOME="${DSH_HOME:-/opt/dsh-home}"
DSH_DESKTOP_DIR="${DSH_DESKTOP_DIR:-/opt/dsh-desktop}"
DSH_CORE_DIR="${DSH_CORE_DIR:-/opt/dsh-desktop/deepseek-harness}"
SELF_HARNESS_DIR="${SELF_HARNESS_DIR:-/opt/deepseek-harness}"

# ---- 1. 网关地址解析（CNB_AI_GATEWAY 显式优先，否则尝试 ACC_PRODUCT_CONFIG_V2 自动解析）----
GATEWAY="${CNB_AI_GATEWAY:-}"
if [ -z "$GATEWAY" ]; then
  GATEWAY="https://api.cnb.cool/chat/completions"
fi
echo "[dsh-entrypoint] 模型基座 = ${CNB_MODEL}（CNB 内置免费 DeepSeek-V4-Flash）"
echo "[dsh-entrypoint] 网关地址 = ${GATEWAY}"
if [ -n "${CNB_TOKEN:-}" ]; then
  echo "[dsh-entrypoint] CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）✅"
else
  echo "[dsh-entrypoint] ⚠️ CNB_TOKEN 未注入，模型调用将失败（仍启动服务）"
fi

# ---- 2. 动态生成 $DSH_HOME/settings.yaml（自定义 provider → CNB 免费网关）----
# 关键：apiKeyEnv 引用 CNB_TOKEN 环境变量；baseURL 用注入的网关地址。
# 不写死网关地址、不写死密钥，实现「镜像预置配置 + 运行时取环境变量」。
mkdir -p "$DSH_HOME"
cat > "$DSH_HOME/settings.yaml" <<YAML
llm-pi-ai:
  providers:
    cnb-deepseek-v4-flash:
      displayName: CNB DeepSeek-V4-Flash (免费)
      api: openai-completions
      baseURL: "${GATEWAY}"
      apiKeyEnv: CNB_TOKEN
      defaultInput: [text]
      models:
        - id: ${CNB_MODEL}
          input: [text]
YAML
echo "[dsh-entrypoint] ✅ 已生成 \$DSH_HOME/settings.yaml（provider=cnb-deepseek-v4-flash）"

# ---- 3. 后台启动原版 Harness WebUI（容器内 loopback :8080，对外靠 -p 端口映射）----
# 官方 dsh web 默认监听 127.0.0.1:3080；用 --port 改为 8080，--host 保持 127.0.0.1
# （官方禁止 0.0.0.0，需在 docker run 时用 -p 8080:8080 完成对外暴露）。
echo "[dsh-entrypoint] 启动原版 DeepSeek Harness WebUI (127.0.0.1:${DSH_WEB_PORT}, 对外靠 -p 映射)..."
cd "$DSH_CORE_DIR"
DSH_HOME="$DSH_HOME" nohup dsh web \
  --host 127.0.0.1 \
  --port "$DSH_WEB_PORT" \
  >/tmp/dsh-web.log 2>&1 &
DSH_WEB_PID=$!
echo "[dsh-entrypoint] 原版 WebUI PID: ${DSH_WEB_PID}"

# ---- 4. 后台启动自研 harness（127.0.0.1:8081 内网，不对外）----
if [ -f "$SELF_HARNESS_DIR/harness_proxy.py" ]; then
  echo "[dsh-entrypoint] 启动自研 harness (127.0.0.1:${HARNESS_PORT} 内网) ..."
  cd "$SELF_HARNESS_DIR"
  nohup python3 harness_proxy.py \
    --port "$HARNESS_PORT" \
    --host 127.0.0.1 >/tmp/harness.log 2>&1 &
  SELF_HARNESS_PID=$!
  echo "[dsh-entrypoint] 自研 harness PID: ${SELF_HARNESS_PID}"
else
  SELF_HARNESS_PID=""
  echo "[dsh-entrypoint] ⚠️ 自研 harness 脚本缺失，跳过（接单接口不可用）"
fi

# ---- 4b. 启动本机 3081 网关（双模式 MCP 插件，HTTP 兼容模式 127.0.0.1:3081）----
# 内置进镜像；若需 MCP 模式供宿主工具加载，可去掉 --http 直接无参启动。
GW_PORT="${GW_PORT:-3081}"
if [ -f "$SELF_HARNESS_DIR/gateway_3080.py" ]; then
  echo "[dsh-entrypoint] 启动本机 3081 网关 (127.0.0.1:${GW_PORT}, HTTP 兼容模式) ..."
  cd "$SELF_HARNESS_DIR"
  CNB_TOKEN="${CNB_TOKEN:-}" CNB_AI_GATEWAY="${GATEWAY:-}" \
    nohup python3 gateway_3080.py --http --port "$GW_PORT" >/tmp/gw3080.log 2>&1 &
  GW3080_PID=$!
  echo "[dsh-entrypoint] 3081 网关 PID: ${GW3080_PID}"
else
  GW3080_PID=""
  echo "[dsh-entrypoint] ⚠️ gateway_3080.py 缺失，跳过 3081 网关"
fi

# ---- 5. 等待端口就绪并打印状态 ----
sleep 5
echo "------------------------------------"
echo "[dsh-entrypoint] 端口状态："
for p in "$DSH_WEB_PORT" "$HARNESS_PORT" "$GW_PORT"; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then
    exec 3>&- 3<&- || true
    echo "  ✅ :${p} 已监听"
  else
    echo "  ⚠️ :${p} 未就绪（可能仍在启动，或查看日志）"
  fi
done
echo "------------------------------------"

# ---- 6. 前台保持存活（清理子进程）----
cleanup() {
  echo "[dsh-entrypoint] 容器退出，清理子进程..."
  [ -n "${DSH_WEB_PID:-}" ] && kill "$DSH_WEB_PID" 2>/dev/null || true
  [ -n "${SELF_HARNESS_PID:-}" ] && kill "$SELF_HARNESS_PID" 2>/dev/null || true
  [ -n "${GW3080_PID:-}" ] && kill "$GW3080_PID" 2>/dev/null || true
}
trap cleanup EXIT

# 若传入额外命令则执行
if [ "$#" -gt 0 ]; then
  echo "[dsh-entrypoint] 执行传入命令: $*"
  exec "$@"
fi

echo "[dsh-entrypoint] 容器前台存活中（8080 原版 WebUI + 8081 内网自研 harness + 3081 网关）..."
tail -f /dev/null
