#!/bin/bash
# =====================================================
# 企业微信群定制接单项目 · Orca 项目自动就绪脚本
# 用途：Orca 打开项目时自动检查并恢复所有服务
# 位置：scripts/orca_project_startup.sh
# =====================================================

set -e

PROJECT_ROOT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"

echo ""
echo "========================================="
echo "  🦞 企微接单项目 · 自动就绪检查"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

ERRORS=0

# ---- 1. 代理端口检查 ----
echo "[1/4] 代理端口检查..."
for PORT in 15721 15730; do
    if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "  [OK] 端口 $PORT 正常"
    else
        echo "  [FIX] 端口 $PORT 未运行，正在拉起..."
        if [ "$PORT" = "15721" ]; then
            start //min "AutoRestore-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        elif [ "$PORT" = "15730" ]; then
            start //min "AutoRestore-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
        fi
        sleep 3
        if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
            echo "  [OK] 端口 $PORT 已恢复"
        else
            echo "  [FAIL] 端口 $PORT 拉起失败"
            ERRORS=$((ERRORS+1))
        fi
    fi
done

# ---- 2. Codex CLI 检查 ----
echo ""
echo "[2/4] Codex CLI 检查..."
CODEX_VERSION=$(codex --version 2>/dev/null || echo "FAIL")
if [ "$CODEX_VERSION" != "FAIL" ]; then
    echo "  [OK] Codex CLI: $CODEX_VERSION"
else
    echo "  [FIX] Codex CLI 不可用，检查 shim..."
    SHIM_PATH="/c/Users/Administrator/AppData/Roaming/npm/codex"
    if [ ! -f "$SHIM_PATH" ]; then
        cat > "$SHIM_PATH" << 'SHIM'
#!/bin/sh
exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
SHIM
        chmod +x "$SHIM_PATH"
    fi
    # 重建 .cmd
    cat > "/c/Users/Administrator/AppData/Roaming/npm/codex.cmd" << 'CMDSHIM'
@ECHO off
node "I:\npm\node_modules\@openai\codex\bin\codex.js" %*
CMDSHIM
    CODEX_VERSION=$(codex --version 2>/dev/null || echo "STILL_FAIL")
    if [ "$CODEX_VERSION" != "STILL_FAIL" ]; then
        echo "  [OK] Codex CLI 已恢复: $CODEX_VERSION"
    else
        echo "  [FAIL] Codex CLI 恢复失败"
        ERRORS=$((ERRORS+1))
    fi
fi

# ---- 3. Claude Code 检查 ----
echo ""
echo "[3/4] Claude Code 检查..."
if command -v claude &>/dev/null; then
    CLAUDE_VER=$(claude --version 2>/dev/null || echo "unknown")
    echo "  [OK] Claude Code: $CLAUDE_VER"
else
    echo "  [SKIP] Claude Code 不在 PATH 中"
fi

# ---- 4. API 连通验证 ----
echo ""
echo "[4/4] API 连通验证..."
for ENDPOINT in "http://127.0.0.1:15730/health" "http://127.0.0.1:15721/health"; do
    PORT=$(echo "$ENDPOINT" | grep -oP ':\K\d+')
    if curl -s --connect-timeout 3 "$ENDPOINT" > /dev/null 2>&1; then
        echo "  [OK] 端口 $PORT 连通"
    else
        echo "  [FAIL] 端口 $PORT 不可达"
        ERRORS=$((ERRORS+1))
    fi
done

# ---- 汇总 ----
echo ""
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ 全部就绪！零错误"
    echo ""
    echo "  Claude Code → http://127.0.0.1:15721"
    echo "  Codex CLI   → http://127.0.0.1:15730"
    echo ""
    echo "  可以直接启动 Claude Code 或 Codex"
else
    echo "  ⚠️ $ERRORS 项异常，请检查上方日志"
fi
echo "========================================="
echo ""
