#!/bin/bash
# ORCA 项目自动就绪脚本（通用版）
set -e
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"
echo "🦞 ORCA 项目自动就绪: $(basename "$PROJECT_ROOT")"
for PORT in 15721 15730; do
    if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "[FIX] 拉起端口 $PORT..."
        if [ "$PORT" = "15721" ]; then
            start //min "AutoRestore-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        else
            start //min "AutoRestore-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
        fi
        sleep 3
    fi
done
if ! codex --version &>/dev/null; then
    echo "[FIX] 重建 Codex shim..."
    SHIM_DIR="/c/Users/Administrator/AppData/Roaming/npm"
    echo '#!/bin/sh' > "$SHIM_DIR/codex"
    echo 'exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"' >> "$SHIM_DIR/codex"
    echo '@ECHO off' > "$SHIM_DIR/codex.cmd"
    echo 'node "I:\npm\node_modules\@openai\codex\bin\codex.js" %*' >> "$SHIM_DIR/codex.cmd"
    chmod +x "$SHIM_DIR/codex"
fi
CODEX_CONFIG="$HOME/.codex/config.toml"
RUNTIME_CONFIG="$HOME/AppData/Roaming/Orca/codex-runtime-home/home/config.toml"
if [ -f "$CODEX_CONFIG" ] && [ -d "$(dirname "$RUNTIME_CONFIG")" ]; then
    cp "$CODEX_CONFIG" "$RUNTIME_CONFIG" 2>/dev/null
fi
echo "✅ 全部就绪"
