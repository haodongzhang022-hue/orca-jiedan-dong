#!/usr/bin/env bash
# =============================================================================
# fix_dsh_provider.sh · DeepSeek-Harness Provider 一键修复（2026-08-18 1234）
# =============================================================================
# 用途：修复 DeepSeek-Harness 桌面端「没有创建成提供方」问题。
#   根因：provider 网关地址缺仓库 slug（如 https://api.cnb.cool/chat/completions），
#         创建提供方时校验请求返回 404 "Resource not found" → 无法创建成功。
#   正确网关：https://api.cnb.cool/{组织}/{仓库}/-/ai/chat/completions
#
# 功能：
#   1. 校验并自动修正 settings.yaml 中 provider 的 baseURL（缺 slug 自动补全）
#   2. 校验 CNB_TOKEN / ACC_PRODUCT_CONFIG_V2 是否就绪
#   3. 对修正后的网关做一次真实流式调用冒烟测试（验证 provider 可用）
#   4. 输出「创建提供方」正确操作顺序（不点获取可用模型，直接创建保存）
#
# 用法：
#   bash scripts/fix_dsh_provider.sh            # 校验+自动修复
#   bash scripts/fix_dsh_provider.sh --check    # 仅校验不改写
#   bash scripts/fix_dsh_provider.sh --file /path/settings.yaml  # 指定配置文件
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."   # 仓库根

MODE="fix"
SETTINGS_FILE=""
for a in "$@"; do
  case "$a" in
    --check) MODE="check" ;;
    --file) ;;
    --file=*) SETTINGS_FILE="${a#*=}" ;;
    *) if [ -z "$SETTINGS_FILE" ]; then SETTINGS_FILE="$a"; fi ;;
  esac
done

SLUG="${CNB_REPO_SLUG:-TJF19770107/orca-jiedan}"
GOOD_GW="https://api.cnb.cool/${SLUG}/-/ai/chat/completions"

# ---- 解析真实网关（与 entrypoint.sh / harness_proxy.py 同规则）----
resolve_gateway() {
  local gw="${CNB_AI_GATEWAY:-}"
  if [ -n "$gw" ]; then
    case "$gw" in
      */chat/completions) echo "$gw"; return ;;
      *) echo "${gw%/}/chat/completions"; return ;;
    esac
  fi
  local acc="${ACC_PRODUCT_CONFIG_V2:-}"
  if [ -n "$acc" ]; then
    local ep
    ep=$(printf '%s' "$acc" | python3 -c "import sys,json;print(json.load(sys.stdin).get('endpoint','').strip().rstrip('/'))" 2>/dev/null || true)
    if [ -n "$ep" ]; then
      case "$ep" in
        */ai-ide) echo "${ep%/ai-ide}/ai/chat/completions"; return ;;
        */chat/completions) echo "$ep"; return ;;
        *) echo "${ep}/chat/completions"; return ;;
      esac
    fi
  fi
  echo "$GOOD_GW"
}

ACTUAL_GW=$(resolve_gateway)

echo "======================================================"
echo " DeepSeek-Harness Provider 一键修复 (1234)"
echo "======================================================"
echo "仓库: $SLUG"
echo "正确网关: $GOOD_GW"
echo "实际网关: $ACTUAL_GW"
echo ""

# ---- 1. 校验令牌 ----
echo "[1/4] 校验鉴权令牌..."
if [ -n "${CNB_TOKEN:-}" ]; then
  echo "  ✅ CNB_TOKEN 已注入（前缀 ${CNB_TOKEN:0:6}...）"
else
  echo "  ⚠️  CNB_TOKEN 未注入——调用将 401，请设置环境变量后再试。"
fi

# ---- 2. 定位 settings.yaml ----
echo ""
echo "[2/4] 定位 settings.yaml ..."
if [ -z "$SETTINGS_FILE" ]; then
  # 常见候选路径
  for cand in \
    "${DSH_HOME:-}/settings.yaml" \
    "$HOME/.dsh/settings.yaml" \
    "$HOME/.config/deepseek-harness/settings.yaml" \
    "deepseek-harness/config/settings.yaml" \
    "config/settings.yaml" \
    "settings.yaml"; do
    if [ -f "$cand" ]; then SETTINGS_FILE="$cand"; break; fi
  done
fi

if [ -z "$SETTINGS_FILE" ] || [ ! -f "$SETTINGS_FILE" ]; then
  echo "  ⚠️  未找到 settings.yaml。将在容器内由 entrypoint.sh 启动时自动生成（已修复默认网关）。"
  echo "     本机可手动创建提供方，API 地址填: $ACTUAL_GW"
  echo "     或通过 3081 本地网关填: http://127.0.0.1:3081/v1"
else
  echo "  ✅ 找到: $SETTINGS_FILE"
  # 检查 baseURL 是否含正确 slug
  if grep -q "$GOOD_GW" "$SETTINGS_FILE"; then
    echo "  ✅ provider baseURL 已指向正确网关，无需修复。"
  elif grep -q "api.cnb.cool" "$SETTINGS_FILE"; then
    echo "  ❌ 检测到 provider baseURL 缺仓库 slug（或指向错误网关）！"
    if [ "$MODE" = "fix" ]; then
      # 自动修正：把所有 api.cnb.cool 错误网关统一替换为正确网关
      sed -i.bak "s#https://api.cnb.cool/chat/completions#${GOOD_GW}#g; s#https://api.cnb.cool/[^\"' ]*/chat/completions#${GOOD_GW}#g" "$SETTINGS_FILE"
      echo "  ✅ 已自动修正 baseURL → $GOOD_GW （备份: ${SETTINGS_FILE}.bak）"
    else
      echo "  ⚠️  --check 模式：未改写。请用无 --check 运行以自动修复。"
    fi
  else
    echo "  ℹ️  未在配置中发现 api.cnb.cool 网关，可能走本地 3081 网关或未配置。"
  fi
fi

# ---- 3. 对正确网关做真实流式冒烟测试 ----
echo ""
echo "[3/4] 流式冒烟测试（验证 provider 可用）..."
if [ -n "${CNB_TOKEN:-}" ]; then
  python3 -c "
import os, json, urllib.request, urllib.error
gw='''$ACTUAL_GW'''
tok=os.environ.get('CNB_TOKEN','')
payload={'model':'deepseek-v4-flash','messages':[{'role':'user','content':'请只回复OK两个字符'}],'stream':True}
req=urllib.request.Request(gw, data=json.dumps(payload).encode(),
    headers={'Content-Type':'application/json','Authorization':f'Bearer {tok}'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body=resp.read().decode()[:120]
        ok = resp.status==200
        print(f'  HTTP {resp.status} → 流式返回正常 ✅' if ok else f'  HTTP {resp.status}')
        if 'OK' in body or 'ok' in body.lower(): print('  模型内容命中 OK ✅')
except urllib.error.HTTPError as e:
    print(f'  ❌ HTTPError {e.code}: {e.read().decode()[:200]}')
except Exception as e:
    print(f'  ❌ 调用失败: {e}')
"
else
  echo "  ⚠️  无 CNB_TOKEN，跳过冒烟测试。"
fi

# ---- 4. 输出「创建提供方」正确操作顺序 ----
echo ""
echo "[4/4] DeepSeek-Harness 新增提供方·正确操作顺序 + Failed to fetch 排查"
cat <<'GUIDE'
  ┌────────────────────────────────────────────────────────────┐
  │ 场景A·API 地址用「本机 3081 网关」http://127.0.0.1:3081/v1   │
  │  若创建时底部报 `Failed to fetch`（网络层连不上，不是404）  │
  │  → 根因：本机 3081 网关(gateway_3080.py)没有启动！           │
  │  → 解决：先双击运行 scripts/start_gateway_3080.bat 启动网关  │
  │    再验证 curl http://127.0.0.1:3081/health 返回 {"ok":true}│
  │    最后回 Harness 点【创建提供方】保存                       │
  └────────────────────────────────────────────────────────────┘

  【关键】在 Harness WebUI（http://127.0.0.1:3080）新增自定义提供方：
  1. 填写 Provider ID / 显示名称 / API 地址 / API 协议 / API 密钥 / 模型
  2. ⚠️ 弹窗里【不要点"获取可用模型"】——CNB 网关无 /models 接口，点必 404
  3. 直接右下角【创建提供方】保存
  4. 保存完回到列表页，再点"获取可用模型"即可看到模型

  字段对照（直连 CNB 云端，最稳，不依赖本机网关）：
    Provider ID : cnb-deepseek-v4-flash
    显示名称     : CNB 免费 DeepSeek-V4-Flash
    API 地址     : https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai
    API 协议     : openai-completions
    API 密钥     : 你的 CNB 访问令牌（CNB_TOKEN）
    模型         : deepseek-v4-flash（必须精确，不是 pro）

  字段对照（本机 3081 网关，需先启动网关）：
    Provider ID : cnb-gateway-local
    显示名称     : CNB本地网关(DeepSeekV4+GLM5.2)
    API 地址     : http://127.0.0.1:3081/v1  （⚠️ 需先启动 3081 网关）
    API 协议     : openai-completions
    API 密钥     : local（占位即可，网关内部自动读 CNB_TOKEN）
    模型         : deepseek-v4-flash / z-ai/glm-5.2
  ⚠️ Provider ID 红色提示是实时校验提示，忽略即可，ID 合法可直接创建保存。
GUIDE

echo ""
echo "======================================================"
echo " 修复完成。若网关地址有误，请重新拉取最新代码后重试。"
echo "======================================================"
