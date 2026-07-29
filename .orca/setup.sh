#!/bin/bash
# =====================================================
# ORCA 项目级全局启动脚本
# 用途：Orca 创建新 worktree 时自动执行环境就绪
# 触发：Orca → 项目 → 添加设置脚本 → 配置此文件
# =====================================================

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"

echo ""
echo "========================================="
echo "  🦞 ORCA 项目自动就绪"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

# 1. 代理端口自愈
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

# 2. Codex CLI shim 校验
if ! codex --version &>/dev/null; then
    echo "[FIX] 重建 Codex shim..."
    SHIM_DIR="/c/Users/Administrator/AppData/Roaming/npm"
    cat > "$SHIM_DIR/codex" << 'EOF'
#!/bin/sh
exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
EOF
    cat > "$SHIM_DIR/codex.cmd" << 'EOF'
@ECHO off
node "I:\npm\node_modules\@openai\codex\bin\codex.js" %*
EOF
    chmod +x "$SHIM_DIR/codex"
fi

# 3. Codex 配置同步
CODEX_CONFIG="$HOME/.codex/config.toml"
RUNTIME_CONFIG="$HOME/AppData/Roaming/Orca/codex-runtime-home/home/config.toml"
if [ -f "$CODEX_CONFIG" ] && [ -d "$(dirname "$RUNTIME_CONFIG")" ]; then
    cp "$CODEX_CONFIG" "$RUNTIME_CONFIG" 2>/dev/null
fi

# 4. 连通验证
OK=1
for EP in "http://127.0.0.1:15721/health" "http://127.0.0.1:15730/health"; do
    if ! curl -s --connect-timeout 3 "$EP" >/dev/null 2>&1; then
        echo "[FAIL] $EP 不可达"
        OK=0
    fi
done

if [ "$OK" = "1" ]; then
    echo "✅ 全部就绪"
fi
echo "========================================="
