# =====================================================
# ORCA 项目 · 自动就绪脚本（一键拉起云上Deepseek V4-Flash 标准版 v1.4.1）
# 用途：ORCA 打开项目时自动检查并恢复 Codex / Claude Code 代理
# 位置：scripts/orca_project_startup.sh
# =====================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"

echo ""
echo "========================================="
echo "  🦞 $(basename "$PROJECT_ROOT") · 自动就绪检查"
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
            cmd.exe /c start //min "AutoRestore-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        elif [ "$PORT" = "15730" ]; then
            cmd.exe /c start //min "AutoRestore-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
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
fi

# ---- 3. API 连通性 ----
echo ""
echo "[3/4] API 连通性检查..."
curl -s -o /dev/null -w "  [HTTP %{http_code}] Codex Proxy (15730)\n" http://127.0.0.1:15730/health 2>/dev/null || echo "  [FAIL] 15730 未连通"
curl -s -o /dev/null -w "  [HTTP %{http_code}] Anthropic Proxy (15721)\n" http://127.0.0.1:15721/health 2>/dev/null || echo "  [FAIL] 15721 未连通"

# ---- 4. 脚手架一致性 ----
echo ""
echo "[4/4] 脚手架版本检查..."
if [ -f "$PROJECT_ROOT/scaffold_version" ]; then
    echo "  [OK] 当前脚手架版本: $(cat "$PROJECT_ROOT/scaffold_version")"
else
    echo "  [WARN] 未找到 scaffold_version，建议从脚手架模板补齐"
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ 全部就绪，Codex / Claude Code 可正常使用"
else
    echo "⚠️ 有 $ERRORS 项异常，请检查上方输出"
fi
