#!/usr/bin/env bash
# =============================================================================
# install_mcp_plugin.sh · 双模式 MCP 插件安装 + 集成 + 验证（一键）
# =============================================================================
# 把 gateway_3080 双模式 MCP 插件安装到 DeepSeek Harness，并融合进脚手架。
#
#  模式一 标准 MCP（默认）: python3 harness_mcp_loader.py --tool <工具> --args '{}'
#  模式二 HTTP 兼容      : python3 harness_mcp_loader.py --mode http --tool <工具> --args '{}'
#
# 安装路径:
#  插件源文件 : deploy/dsh-desktop/gateway_3080.py
#  安装位置   : deepseek-harness/plugins/gateway_3080/gateway_3080.py
#  加载器     : deepseek-harness/harness_mcp_loader.py
#  注册中心   : deepseek-harness/config/harness_mcp_registry.json
#  角色插件   : deepseek-harness/harness_plugin_loader.py + config/harness_plugins.json
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."   # 回到仓库根目录

HARNESS_DIR="deepseek-harness"
PLUGIN_DIR="$HARNESS_DIR/plugins/gateway_3080"
SRC="deploy/dsh-desktop/gateway_3080.py"
DEST="$PLUGIN_DIR/gateway_3080.py"

echo "[install-mcp] ==== 双模式 MCP 插件安装与集成 ===="

# ---- 1. 安装插件文件 ----
mkdir -p "$PLUGIN_DIR"
if [ -f "$SRC" ]; then
  cp "$SRC" "$DEST"
  chmod +x "$DEST"
  echo "[install-mcp] ✅ 已安装 gateway_3080 → $DEST"
else
  echo "[install-mcp] ⚠️ 源文件缺失 $SRC，跳过拷贝"
fi

# ---- 2. 语法校验 ----
python3 -m py_compile "$DEST" "$HARNESS_DIR/harness_mcp_loader.py" "$HARNESS_DIR/harness_plugin_loader.py"
echo "[install-mcp] ✅ 语法校验通过（gateway_3080 / mcp_loader / plugin_loader）"

# ---- 3. 注册中心 JSON 校验 ----
python3 -c "import json; json.load(open('$HARNESS_DIR/config/harness_mcp_registry.json')); print('[install-mcp] ✅ 注册中心 JSON 合法')"
python3 -c "import json; json.load(open('$HARNESS_DIR/config/harness_plugins.json')); print('[install-mcp] ✅ 插件清单 JSON 合法')"

# ---- 4. 冒烟验证：health（MCP 模式） ----
echo "[install-mcp] ---- 冒烟验证 health（MCP 模式）----"
timeout 30 python3 "$HARNESS_DIR/harness_mcp_loader.py" --tool health --mode mcp 2>&1 | tail -20

# ---- 5. 角色插件清单 ----
echo "[install-mcp] ---- 角色插件清单 ----"
python3 "$HARNESS_DIR/harness_plugin_loader.py" --list 2>&1

echo ""
echo "[install-mcp] ✅ 安装与集成完成"
echo "  · 安装路径 : $DEST"
echo "  · 加载器   : $HARNESS_DIR/harness_mcp_loader.py"
echo "  · 注册中心 : $HARNESS_DIR/config/harness_mcp_registry.json"
echo ""
echo "[install-mcp] 调用示例:"
echo "  # 模式一 MCP（免费模型对话）"
echo "  python3 $HARNESS_DIR/harness_mcp_loader.py --tool chat_completions \\"
echo "      --args '{\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}' --mode mcp"
echo "  # 模式二 HTTP（base_url=http://127.0.0.1:3080）"
echo "  python3 $HARNESS_DIR/harness_mcp_loader.py --tool chat_completions \\"
echo "      --args '{\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}' --mode http"
