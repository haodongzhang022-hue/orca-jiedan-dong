#!/bin/bash
# =====================================================
# 三Agent一键启动脚本
# 用法：bash scripts/launch_all_agents.sh
# 功能：同时拉起 Hermes + Codex + Claude Code 三实例
# =====================================================

PROJECT_ROOT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║   🦞 龙虾舰队 · 三Agent一键启动              ║"
echo "║   $(date '+%Y-%m-%d %H:%M:%S')                  ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# ---- Phase 1: 代理自愈 ----
echo "▶ [Phase 1] 代理端口检查..."
for PORT in 15721 15730; do
    if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "  [OK] 端口 $PORT"
    else
        echo "  [FIX] 拉起端口 $PORT..."
        if [ "$PORT" = "15721" ]; then
            start //min "Fleet-15721" "$PYEXE" "$MCP_DIR/anthropic_proxy_15721.py"
        else
            start //min "Fleet-15730" "$PYEXE" "$MCP_DIR/codex_tool_proxy.py"
        fi
        sleep 3
    fi
done

# ---- Phase 2: CLI校验 ----
echo ""
echo "▶ [Phase 2] CLI 工具校验..."
CODEX_VER=$(codex --version 2>/dev/null || echo "FAIL")
CLAUDE_VER=$(claude --version 2>/dev/null || echo "FAIL")
echo "  Codex:       $CODEX_VER"
echo "  Claude Code: $CLAUDE_VER"

if [ "$CODEX_VER" = "FAIL" ]; then
    echo "  [FIX] 重建 Codex shim..."
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

# ---- Phase 3: 身份播报 ----
echo ""
echo "▶ [Phase 3] 三Agent身份播报"
echo "  ┌─────────────────────────────────────────┐"
echo "  │  🧠 Hermes    → 大脑/编排 (本终端)       │"
echo "  │  ⚡ Codex      → 执行器 (worktrees/codex) │"
echo "  │  🔍 Claude    → 审核器 (worktrees/claude) │"
echo "  └─────────────────────────────────────────┘"

# ---- Phase 4: 交互入口提示 ----
echo ""
echo "▶ [Phase 4] 启动完成"
echo ""
echo "  启动交互式终端："
echo "    Codex:       cd $PROJECT_ROOT/worktrees/codex && codex"
echo "    Claude Code: cd $PROJECT_ROOT/worktrees/claude && claude"
echo ""
echo "  或在 Orca IDE 中直接点击对应 Agent 标签页"
echo ""
echo "========================================="
echo "  ✅ 龙虾舰队就绪，等待指令"
echo "========================================="
