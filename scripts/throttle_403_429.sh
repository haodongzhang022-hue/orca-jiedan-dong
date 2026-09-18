#!/usr/bin/env bash
# throttle_403_429.sh — 403/429 多窗口并发预案一键脚本（2026-08-14）
# 固化于：五步法 §15.7 + 全域模板 #307 + 脚手架三文件触发行
# 触发词：403/429/限流/多窗口/并发互斥/atomcode_session_concurrency
# 用法：bash scripts/throttle_403_429.sh         （诊断+提示）
#       bash scripts/throttle_403_429.sh check  （仅检测不提示关窗）
#       bash scripts/throttle_403_429.sh verify （关到 ≤1 窗后验通 13460+GLM）

set -uo pipefail

ACTION="${1:-diag}"

warn() { printf "\033[31m[预案]\033[0m %s\n" "$1" >&2; }
info() { printf "\033[36m[诊断]\033[0m %s\n" "$1"; }
ok()   { printf "\033[32m[OK]\033[0m %s\n" "$1"; }

# ── 1. 并发源计数 ──────────────────────────────────────────────
count_hermes_studio=$(tasklist 2>/dev/null | grep -c "Hermes Studio.exe")
count_atomcode_cli=$(tasklist 2>/dev/null | grep -c "atomcode.exe")
count_codex_main=$(tasklist 2>/dev/null | grep -c "Codex.exe")
count_codex_cli=$(tasklist 2>/dev/null | grep -c "^codex.exe")

# 13460 代理 PID
proxy_pid=$(netstat -ano 2>/dev/null | grep ":13460" | grep "LISTENING" | awk '{print $5}' | head -1)

# 上游并发会话数（ESTABLISHED 连到 13460 的）
proxy_sessions=$(netstat -ano 2>/dev/null | grep ":13460" | grep "ESTABLISHED" | wc -l)

info "Hermes Studio 窗口数 = ${count_hermes_studio}（阈值 ≤1）"
info "atomcode CLI 实例   = ${count_atomcode_cli}（阈值 ≤1，CLI 与 Studio 不叠）"
info "Codex 主进程        = ${count_codex_main}（派生子进程不算并发）"
info "codex CLI 实例      = ${count_codex_cli}"
info "13460 代理 PID = ${proxy_pid:-无}，活跃会话 = ${proxy_sessions}"

# ── 2. 13460 上游模型清单 ──────────────────────────────────────
models_json=$(curl -s -m 5 http://127.0.0.1:13460/v1/models 2>/dev/null)
has_deepseek=$(printf '%s' "$models_json" | grep -c '"deepseek-v4-flash"')
has_glm=$(printf '%s' "$models_json" | grep -c '"z-ai/glm-5.2"')
has_qwen_vl=$(printf '%s' "$models_json" | grep -c '"Qwen3-VL-8B"')
info "13460 上游模型：deepseek=${has_deepseek} glm-5.2=${has_glm} qwen3-vl=${has_qwen_vl}"

# ── 3. 15721/15730 代理健康 ────────────────────────────────────
h_15721=$(curl -s -m 3 http://127.0.0.1:15721/health 2>/dev/null | head -c 80)
h_15730=$(curl -s -m 3 http://127.0.0.1:15730/health 2>/dev/null | head -c 80)
info "15721 Anthropic 代理 = ${h_15721:-DOWN}"
info "15730 Codex 代理     = ${h_15730:-DOWN}"

# ── 4. 判定与预案输出 ──────────────────────────────────────────
risk=0
[ "${count_hermes_studio}" -gt 1 ] && { warn "Hermes Studio 开了 ${count_hermes_studio} 个窗口，上游 AtomGit 会判并发互斥直接 403。"; risk=1; }
[ "${count_hermes_studio}" -ge 1 ] && [ "${count_atomcode_cli}" -ge 1 ] && { warn "Hermes Studio 与 atomcode CLI 同时跑，叠 deepseek 配额并发，必 403。"; risk=1; }
[ "${count_atomcode_cli}" -gt 1 ] && { warn "atomcode CLI 跑了 ${count_atomcode_cli} 个实例，单账号同模型互斥。"; risk=1; }
[ "${proxy_sessions}" -gt 1 ] && { warn "13460 同时有 ${proxy_sessions} 条活跃会话，上游侧判定会话冲突。"; risk=1; }

if [ "$ACTION" = "check" ]; then
  [ "$risk" = 0 ] && ok "无并发风险，可继续接单。"
  exit $risk
fi

if [ "$risk" = 0 ]; then
  ok "无并发风险。13460=${has_deepseek} GLM=${has_glm}，可正常应答。"
  exit 0
fi

cat <<EOF
────────────────── 403/429 多窗口预案 ──────────────────
根因：AtomGit 免费档 deepseek-v4-flash 加了「同账号同模型并发互斥」闸门。
      多窗口同一秒发请求 → 上游 403 atomcode_session_concurrency_conflict。
      z-ai/glm-5.2（NVIDIA）是另一条限流（按分钟配额），叠加就看着像全群卡。

立即处置（按序执行）：
  1) 关 Hermes Studio 窗口到只剩 1 个（当前 ${count_hermes_studio} 个）
     → 在任务栏逐个右键关闭，或 PowerShell：Stop-Process -Name "Hermes Studio" -Force 再重开 1 个
  2) 若在跑 atomcode CLI（atomcode.exe）且同时开 Studio → 关掉 CLI，只留 Studio 1 个
  3) 等 10 秒让上游会话自然释放，再发请求
  4) 验通：bash scripts/throttle_403_429.sh verify

要研判/报价这类重思考任务，走 GLM 通道（不动 deepseek 配额）：
  bash scripts/glm52_call.sh "你的问题"

复盘/查证类，走本地脚本，不碰上游配额。

重启电脑后第一件事：先跑本脚本诊断（bash scripts/throttle_403_429.sh），
再开 Studio。开机自启项里若有 Hermes Studio 多开，改成手动启动。
─────────────────────────────────────────────────
EOF

if [ "$ACTION" = "verify" ]; then
  if [ "${count_hermes_studio}" -le 1 ] && [ "${proxy_sessions}" -le 1 ]; then
    ok "窗口已收敛到 ≤1，13460 会话 ≤1，并发互斥解除。"
    # 实测 deepseek 通道
    probe=$(curl -s -m 15 -X POST http://127.0.0.1:13460/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":4}' 2>/dev/null | head -c 200)
    if printf '%s' "$probe" | grep -q '"content"'; then
      ok "deepseek-v4-flash 通道实测通畅。"
    else
      warn "deepseek 通道仍未通（可能上游仍在限流窗口），稍等再试。"
    fi
  else
    warn "仍未收敛（Studio=${count_hermes_studio} 会话=${proxy_sessions}），请先执行处置第 1/2 步。"
    exit 1
  fi
fi

exit $risk
