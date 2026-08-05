#!/bin/bash
# 三Agent一键启动脚本
PROJECT_ROOT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"
echo "🦞 龙虾舰队 · 三Agent一键启动"
for PORT in 15721 15730; do
    if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "[FIX] 拉起端口 $PORT..."
        if [ "$PORT" = "15721" ]; then
            cmd.exe /c start //min "Fleet-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        else
            cmd.exe /c start //min "Fleet-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
        fi
        sleep 3
    fi
done
echo "Codex:       $(codex --version 2>/dev/null || echo FAIL)"
echo "Claude Code: $(claude --version 2>/dev/null || echo FAIL)"
echo "🧠 Hermes → 大脑/编排"
echo "⚡ Codex → 执行器"
echo "🔍 Claude Code → 审核器"
echo "✅ 龙虾舰队就绪"
