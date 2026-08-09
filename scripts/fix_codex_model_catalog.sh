#!/usr/bin/env bash
# =============================================================================
# fix_codex_model_catalog.sh — 修复 Hermes Studio 群聊 Codex 启动报错
# =============================================================================
# 报错（2026-08-10 Hermes Studio 群聊实测）：
#   Error: Codex exited with code 1: Error: failed to parse model_catalog json
#   path c:\users\administrator\.hermes-web-ui\coding-agent\model\default\xiaomi\codex\
#   group-chat\<room>\<room>\codex-model-catalog.json as JSON:
#   unknown variant max, expected one of none, minimal, low, medium, high, xhigh
#
# 根因：
#   Hermes Studio 生成群聊 Codex 的 model catalog 时，把推理强度字段写成了
#   "max"，而内置 Codex CLI 只接受 none/minimal/low/medium/high/xhigh 六档，
#   于是 JSON 解析直接失败 → Codex 退出码 1。
#
# 解法（本地修复，仅动 ~/.hermes-web-ui 下的 JSON 文件）：
#   1) 全盘扫描所有 codex-model-catalog.json（含已建群聊房间）
#   2) 把推理强度 "max" 改写为 "xhigh"（合法档位中最接近 max，Codex 可解析）
#   3) 修复后输出汇总 + 一键清掉损坏的群聊会话缓存（可选）
#
# 用法：
#   bash scripts/fix_codex_model_catalog.sh              # 全自动修复（推荐）
#   bash scripts/fix_codex_model_catalog.sh --dry-run    # 只扫描不修改
#   bash scripts/fix_codex_model_catalog.sh --clear-cache # 修复后同时清群聊会话缓存
#
# 安全：
#   - 只改 .hermes-web-ui 下 JSON 中的推理强度字段，不碰其他配置
#   - 自动备份原始文件（*.bak），可回滚
#   - 不读取/打印任何密钥
# =============================================================================
set -uo pipefail

MODE="fix"
for arg in "$@"; do
  case "$arg" in
    --dry-run)    MODE="dry-run" ;;
    --clear-cache) MODE="fix-clear" ;;
  esac
done

HERMES_WEB_UI="${HERMES_WEB_UI:-$HOME/.hermes-web-ui}"
echo "🦞 修复 Hermes Studio 群聊 Codex model-catalog（unknown variant max）"
echo "==================================================="
echo "扫描目录: $HERMES_WEB_UI"

if [ ! -d "$HERMES_WEB_UI" ]; then
  echo "❌ 未找到 $HERMES_WEB_UI 目录（Hermes Studio 还没初始化过）"
  exit 1
fi

mapfile -t CATALOGS < <(find "$HERMES_WEB_UI" -type f -name "codex-model-catalog.json" 2>/dev/null)
FIXED=0
DONE=0

if [ "${#CATALOGS[@]}" -eq 0 ]; then
  echo "ℹ️  未找到任何 codex-model-catalog.json（群聊 Codex 尚未拉起过）"
  exit 0
fi

for f in "${CATALOGS[@]}"; do
  DONE=$((DONE+1))
  # 只定位并统计非法档位，避免正则污染
  MAX_HITS=$(grep -o '"max"' "$f" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$MAX_HITS" -eq 0 ]; then
    echo "  [OK] 无非法档位: $f"
    continue
  fi

  if [ "$MODE" = "dry-run" ]; then
    echo "  [待修] $f （发现 $MAX_HITS 处 \"max\" 档位）"
    continue
  fi

  # 备份 + 用 Python 精确替换（只动 reasoning 档位字段）
  cp "$f" "$f.bak.$(date +%Y%m%d_%H%M%S)"
  python3 - "$f" <<'PYEOF'
import json, sys
path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as fp:
    raw = fp.read()
data = json.loads(raw)

def clean(obj):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and v == 'max' and k in ('effort', 'reasoning_effort', 'default_reasoning_level', 'reasoning_level'):
                obj[k] = 'xhigh'
            else:
                clean(v)
    elif isinstance(obj, list):
        for it in obj:
            clean(it)

clean(data)
with open(path, 'w', encoding='utf-8') as fp:
    json.dump(data, fp, ensure_ascii=False, indent=2)
PYEOF
  echo "  [已修复] $f （$MAX_HITS 处 max → xhigh，已备份 .bak）"
  FIXED=$((FIXED+1))
done

echo "==================================================="
echo "扫描 $DONE 个 catalog，修复 $FIXED 个"

if [ "$MODE" = "fix-clear" ]; then
  echo ""
  echo "🧹 清理损坏的群聊会话缓存（避免 Codex 仍读取旧状态）："
  find "$HERMES_WEB_UI/coding-agent" -maxdepth 4 -type d -name "group-chat" 2>/dev/null | head -20
  find "$HERMES_WEB_UI/coding-agent" -maxdepth 5 -type f -name "codex-model-catalog.json" -path "*group-chat*" -exec rm -f {} \; 2>/dev/null \
    && echo "  已清理 group-chat 下的损坏 catalog（重新拉起群聊时会自动重建）"
fi

if [ "$FIXED" -gt 0 ]; then
  echo ""
  echo "✅ 修复完成。请在 Hermes Studio 群聊里重新 @Codex 验证。"
  echo "  若群聊房间已损坏（反复报错），用 --clear-cache 清一次缓存即可。"
else
  echo "✅ 无需修复（若仍报错，请确认是不是新房间又生成了 max 档位，重跑一次本脚本）"
fi
