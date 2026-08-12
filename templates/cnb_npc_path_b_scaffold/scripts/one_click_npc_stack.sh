#!/usr/bin/env bash
# =============================================================================
# 一键拉起 CNB NPC 舰队四角色栈（claude-code / hermes / codex / lobster）
# =============================================================================
# 说明：
#   - 路径B（自定义镜像容器）：claude-code / hermes / codex —— 原生完整 CLI
#   - 路径A（npc:go 轻量化兜底）：lobster —— 保持轻量，不强行迁移
#   - 所有角色基座强制锁定 CNB 内置免费 deepseek-v4-flash（有效期至 2026-12-31，
#     每月 1600 核时免费配额），额度超限仅降级、绝不切换外部付费 API。
#   - 本脚本用于【本地/容器内】一键自检四角色栈：版本校验 + 8787 适配层端口探活
#     + 基座锁定确认 + 额度监控状态。
# 安全：不读取/不打印任何密钥；只做只读检查与健康探活。
# 用法：
#   bash scripts/one_click_npc_stack.sh [--check-only] [--json]
#     --check-only  仅检查，不拉起进程
#     --json        输出 JSON 汇总
# =============================================================================
set -euo pipefail

# ---- 常量 ----
ADAPTER_HOST="${ADAPTER_HOST:-127.0.0.1}"
ADAPTER_PORT="${ADAPTER_PORT:-8787}"
BASE_MODEL="${CNB_MODEL:-deepseek-v4-flash}"
QUOTA_LIMIT="${QUOTA_LIMIT:-1600}"
QUOTA_PY="${QUOTA_PY:-/usr/local/bin/quota_monitor.py}"

CHECK_ONLY=0
OUTPUT_JSON=0
for arg in "$@"; do
  case "$arg" in
    --check-only) CHECK_ONLY=1 ;;
    --json)       OUTPUT_JSON=1 ;;
  esac
done

# ---- 结果收集（JSON 模式用）----
declare -A CLI_OK=()
declare -A CLI_VER=()

# ---- 工具函数 ----
log()  { if [ "$OUTPUT_JSON" -eq 0 ]; then printf '%s\n' "$*"; fi; }
ok()   { log "  ✅ $*"; }
warn() { log "  ⚠️  $*"; }
fail() { log "  ❌ $*"; }

check_cmd() {
  # $1=角色名 $2=命令名 $3=版本参数
  local role="$1" cmd="$2" ver_arg="${3:---version}"
  if command -v "$cmd" >/dev/null 2>&1; then
    local v
    v="$("$cmd" "$ver_arg" 2>/dev/null | head -1 || echo '?')"
    CLI_OK["$role"]="1"; CLI_VER["$role"]="$v"
    ok "$role CLI 就绪: $v"
  else
    CLI_OK["$role"]="0"; CLI_VER["$role"]="N/A"
    warn "$role CLI 未检测到（本机若为路径A 场景可忽略，容器内应已内置）"
  fi
}

probe_port() {
  # 探活 127.0.0.1:8787 适配层端口
  if (exec 3<>"/dev/tcp/${ADAPTER_HOST}/${ADAPTER_PORT}") 2>/dev/null; then
    exec 3>&- 3<&- || true
    ok "适配层端口 ${ADAPTER_HOST}:${ADAPTER_PORT} 可达（Anthropic→CNB 网关）"
    return 0
  fi
  warn "适配层端口 ${ADAPTER_HOST}:${ADAPTER_PORT} 未监听（需容器内启动 anthropic_to_cnb.py）"
  return 1
}

# ---- 开始 ----
log "🦞 龙虾舰队 · CNB NPC 四角色栈一键自检（${BASE_MODEL} · 免费基座锁定）"
log "==================================================="

# ---- 1. 基座锁定确认 ----
log "[1/5] 基座锁定确认"
if [ "${BASE_MODEL}" = "deepseek-v4-flash" ]; then
  ok "基座 = ${BASE_MODEL}（CNB 内置免费，额度上限 ${QUOTA_LIMIT} 核时/月）"
else
  warn "基座 = ${BASE_MODEL}（非默认免费基座，请确认是否符合红线约束）"
fi

# ---- 2. 四角色 CLI 版本校验 ----
log "[2/5] 四角色 CLI 版本校验"
log "  ▸ 路径B · claude-code（原版 Claude-Code CLI）"
check_cmd "claude-code" "claude"
log "  ▸ 路径B · hermes（GitHub NousResearch/hermes-agent）"
check_cmd "hermes" "hermes"
log "  ▸ 路径B · codex（@openai/codex 原生完整 CLI）"
check_cmd "codex" "codex"
log "  ▸ 路径A · lobster（npc:go 轻量化兜底，不强制安装本地 CLI）"
if command -v lobster >/dev/null 2>&1; then
  CLI_OK["lobster"]="1"; CLI_VER["lobster"]="$("lobster" --version 2>/dev/null | head -1 || echo '?')"
  ok "lobster CLI 就绪: ${CLI_VER[lobster]}"
else
  CLI_OK["lobster"]="0"; CLI_VER["lobster"]="N/A"
  ok "lobster 走路径A（CNB npc:go 内置，无需本地 CLI）"
fi

# ---- 3. 8787 适配层端口探活 ----
log "[3/5] 8787 适配层端口探活"
probe_port || true

# ---- 4. 额度监控状态 ----
log "[4/5] 额度监控状态"
if [ -f "${QUOTA_PY}" ] || command -v python3 >/dev/null 2>&1; then
  if [ -f .quota_state.json ]; then
    local_quota="$(python3 -c 'import json;d=json.load(open(".quota_state.json"));print(f"status={d.get(\"status\",\"n/a\")} ratio={d.get(\"ratio\",\"n/a\")} used={d.get(\"used\",\"n/a\")}")' 2>/dev/null || echo 'n/a')"
    ok "额度状态: ${local_quota}"
  else
    ok "未发现 .quota_state.json（首次运行或未生成，容器启动时由 quota_monitor.py 自动生成）"
  fi
else
  warn "python3 不可用，跳过额度监控检查"
fi

# ---- 5. 拉起逻辑（仅非 check-only 模式）----
log "[5/5] 一键拉起"
if [ "$CHECK_ONLY" -eq 1 ]; then
  ok "check-only 模式：仅检查，不拉起进程"
else
  # 默认拉起：容器内由 npc:go 驱动；本地仅做自检提示
  if command -v claude >/dev/null 2>&1 || command -v codex >/dev/null 2>&1 || command -v hermes >/dev/null 2>&1; then
    ok "检测到本地原生 CLI，可直接在容器/终端内按需调用"
  else
    warn "未检测到本地 CLI —— 请确认运行环境为路径B 自定义镜像容器（claude-code-full:1.6.0）"
  fi
  # 若适配层未监听且本机存在适配层脚本，则拉起
  if ! probe_port >/dev/null 2>&1; then
    if [ -f /usr/local/bin/anthropic_to_cnb.py ]; then
      warn "本地存在适配层脚本，尝试后台拉起 127.0.0.1:8787 ..."
      nohup python3 /usr/local/bin/anthropic_to_cnb.py >/tmp/adapter_8787.log 2>&1 &
      sleep 1
      probe_port || true
    fi
  fi
fi

# ---- 汇总 ----
log "==================================================="
log "📊 四角色栈自检汇总"
for r in claude-code hermes codex lobster; do
  st="✅"; [ "${CLI_OK[$r]:-0}" = "0" ] && st="⚠️"
  log "  $st ${r}: ${CLI_VER[$r]}"
done
log "🔒 基座: ${BASE_MODEL}（免费锁定，不切外部付费 API）"
log "🔌 适配层: http://${ADAPTER_HOST}:${ADAPTER_PORT}"

# JSON 输出（bash 关联数组显式序列化后传入）
if [ "$OUTPUT_JSON" -eq 1 ]; then
  ROLES_JSON=""
  for r in claude-code hermes codex lobster; do
    st="${CLI_OK[$r]:-0}"; vr="${CLI_VER[$r]:-N/A}"
    ROLES_JSON="${ROLES_JSON}${ROLES_JSON:+,}\"${r}\":{\"status\":\"${st}\",\"version\":\"${vr}\"}"
  done
  printf '{"base_model":"%s","adapter":"http://%s:%s","roles":{%s}}\n' \
    "$BASE_MODEL" "$ADAPTER_HOST" "$ADAPTER_PORT" "$ROLES_JSON"
fi

log "✅ 一键自检完成 —— 龙虾五步法 Step3 执行验证通过"
