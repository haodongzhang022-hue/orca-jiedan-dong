#!/bin/bash
# 一键拉起 MiMo V2.5 Pro 全栈服务
set -e

echo "========================================="
echo "  🚀 一键拉起 MiMo V2.5 Pro"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

# 1. 检查并拉起代理服务
echo "[1/4] 检查代理服务..."
bash scripts/fleet_auto_ready.sh

# 2. 检查 Claude Code
echo "[2/4] 检查 Claude Code..."
if command -v claude &> /dev/null; then
    echo "[OK] Claude Code 已安装"
    claude --version
else
    echo "[!] Claude Code 未安装，正在安装..."
    npm install -g @anthropic-ai/claude-code
fi

# 3. 检查 Codex
echo "[3/4] 检查 Codex..."
if command -v codex &> /dev/null; then
    echo "[OK] Codex 已安装"
    codex --version
else
    echo "[!] Codex 未安装，请手动安装"
fi

# 4. 验证 MiMo API
echo "[4/4] 验证 MiMo API..."
curl -s http://127.0.0.1:15721/health | grep -q "ok" && echo "[OK] MiMo API 连通" || echo "[!] MiMo API 异常"

echo ""
echo "========================================="
echo "  ✅ MiMo V2.5 Pro 全栈就绪"
echo "========================================="
echo ""
echo "可用服务："
echo "  - Anthropic Proxy: http://127.0.0.1:15721"
echo "  - Codex Proxy: http://127.0.0.1:15730"
echo "  - Claude Code: $(which claude)"
echo "  - Codex: $(which codex)"
echo ""
echo "快速命令："
echo "  - 一键恢复: bash scripts/fleet_auto_ready.sh"
echo "  - 三引擎状态: lobster-cmd 状态"
echo "  - 快照: lobster-cmd 快照"
