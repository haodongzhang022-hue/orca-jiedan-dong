#!/bin/bash
# fleet_ensure.sh — 一键确保舰队就绪（端口+shim+配置）
# 用法: source scripts/fleet_ensure.sh  或  bash scripts/fleet_ensure.sh
# 设计为可被 ~/.bashrc、Orca setup.sh、wrapper 脚本调用

PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"
FIXED=0

# 1. 代理端口检查+拉起
for PORT in 15721 15730; do
    if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "[fleet] 拉起端口 $PORT..."
        if [ "$PORT" = "15721" ]; then
            start //min "Fleet-Auto-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        else
            start //min "Fleet-Auto-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
        fi
        sleep 3
        FIXED=1
    fi
done

# 2. Codex shim 检查
SHIM_DIR="/c/Users/Administrator/AppData/Roaming/npm"
if ! codex --version &>/dev/null; then
    echo "[fleet] 重建 Codex shim..."
    echo '#!/bin/sh' > "$SHIM_DIR/codex"
    echo 'exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"' >> "$SHIM_DIR/codex"
    chmod +x "$SHIM_DIR/codex"
    echo '@ECHO off' > "$SHIM_DIR/codex.cmd"
    echo 'node "I:\npm\node_modules\@openai\codex\bin\codex.js" %*' >> "$SHIM_DIR/codex.cmd"
    FIXED=1
fi

# 3. Codex 配置同步
CODEX_CONFIG="$HOME/.codex/config.toml"
RUNTIME_CONFIG="$HOME/AppData/Roaming/Orca/codex-runtime-home/home/config.toml"
if [ -f "$CODEX_CONFIG" ] && [ -d "$(dirname "$RUNTIME_CONFIG")" ]; then
    cp "$CODEX_CONFIG" "$RUNTIME_CONFIG" 2>/dev/null
fi

# 3.5 doubao-proxy stdio 净化（根治 Codex++ 覆写导致的 url/stdio 报错）
# 根因：Codex++ 运行时把 doubao-proxy 覆写成 type=stdio + url 的坏形态，
# 而 stdio 模式不允许 url/transport 字段，强制还原为标准形态（command/args）。
if [ -f "$CODEX_CONFIG" ]; then
    if grep -q '^\[mcp_servers\.doubao-proxy\]' "$CODEX_CONFIG" 2>/dev/null; then
        if grep -A6 '^\[mcp_servers\.doubao-proxy\]' "$CODEX_CONFIG" | grep -q 'url\s*='; then
            cp "$CODEX_CONFIG" "$CODEX_CONFIG.bak.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
            "$PYEXE" - "$CODEX_CONFIG" << 'PYEOF'
import sys, re
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
good = '''[mcp_servers.doubao-proxy]
type = "stdio"
command = "cmd"
args = ["/c", "python", "-m", "doubao_proxy_server"]

'''
m = re.search(r'\[mcp_servers\.doubao-proxy\][^\[]*', s)
if m and 'url' in m.group(0):
    open(p, 'w', encoding='utf-8').write(s[:m.start()] + good + s[m.end():])
    print('[fix] doubao-proxy 已还原为标准 stdio 形态（url/transport 已清除）')
else:
    print('[ok] doubao-proxy 已是标准形态')
PYEOF
            FIXED=1
        fi
    fi
fi

# 4. 验证
ALL_OK=1
for PORT in 15721 15730; do
    if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "[fleet] ❌ 端口 $PORT 仍然不可用"
        ALL_OK=0
    fi
done
if ! codex --version &>/dev/null; then
    echo "[fleet] ❌ Codex CLI 仍然不可用"
    ALL_OK=0
fi

if [ "$ALL_OK" = "1" ]; then
    [ "$FIXED" = "1" ] && echo "[fleet] ✅ 舰队已恢复" || true
fi
