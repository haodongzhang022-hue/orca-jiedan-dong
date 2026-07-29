# 项目脚手架：三Agent自动就绪机制
# 原理：Orca IDE 打开项目时，通过 .codex/config.toml + CLAUDE.md 自动恢复协议
# 确保 Hermes / Codex / Claude Code 三Agent默认处于正常工作状态
# 
# 本脚本由计划任务 LobsterFleet_AutoRestore 调用，也可手动执行

#!/bin/bash
set -e

echo "========================================="
echo "  龙虾舰队自动就绪检查 $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="

ERRORS=0

# ---- 1. 代理端口检查 ----
for PORT in 15721 15730; do
    if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${PORT} "; then
        echo "[!] 端口 $PORT 未运行，正在拉起..."
        if [ "$PORT" = "15721" ]; then
            start //min "AutoRestore-15721" \
                "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
                "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
        elif [ "$PORT" = "15730" ]; then
            start //min "AutoRestore-15730" \
                "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
                "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"
        fi
        sleep 3
    else
        echo "[OK] 端口 $PORT 正常"
    fi
done

# ---- 2. Codex CLI shim 检查 ----
SHIM_PATH="/c/Users/Administrator/AppData/Roaming/npm/codex"
if [ ! -f "$SHIM_PATH" ]; then
    echo "[!] Codex CLI shim 缺失，正在创建..."
    cat > "$SHIM_PATH" << 'SHIM'
#!/bin/sh
exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
SHIM
    chmod +x "$SHIM_PATH"
    echo "[OK] Codex shim 已创建"
else
    echo "[OK] Codex shim 存在"
fi

# ---- 3. Codex 配置一致性检查 ----
CODEX_CONFIG="$HOME/.codex/config.toml"
EXPECTED_WIRE="wire_api = \"chat\""
EXPECTED_BASE="base_url = \"http://127.0.0.1:15730/v1\""

if ! grep -q "$EXPECTED_WIRE" "$CODEX_CONFIG" 2>/dev/null; then
    echo "[!] Codex wire_api 配置错误，修复中..."
    sed -i 's/wire_api = "responses"/wire_api = "chat"/' "$CODEX_CONFIG" 2>/dev/null
    ERRORS=$((ERRORS+1))
fi

if ! grep -q "127.0.0.1:15730" "$CODEX_CONFIG" 2>/dev/null; then
    echo "[!] Codex base_url 配置错误"
    ERRORS=$((ERRORS+1))
fi

# 同步到 Orca runtime
RUNTIME_CONFIG="$HOME/AppData/Roaming/Orca/codex-runtime-home/home/config.toml"
if [ -f "$CODEX_CONFIG" ] && [ -f "$(dirname "$RUNTIME_CONFIG")" ]; then
    cp "$CODEX_CONFIG" "$RUNTIME_CONFIG" 2>/dev/null
    echo "[OK] Codex runtime 配置已同步"
fi

# ---- 4. API 连通验证 ----
for ENDPOINT in "http://127.0.0.1:15730/health" "http://127.0.0.1:15721/health"; do
    if curl -s --connect-timeout 3 "$ENDPOINT" > /dev/null 2>&1; then
        echo "[OK] $ENDPOINT 连通"
    else
        echo "[!] $ENDPOINT 不可达"
        ERRORS=$((ERRORS+1))
    fi
done

# ---- 5. 分支同步检查 ----
PROJECT_ROOT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
if [ -d "$PROJECT_ROOT/.git" ]; then
    cd "$PROJECT_ROOT"
    for BRANCH in "claude/reviewer" "codex/executor" "hermes/brain"; do
        WORKTREE="worktrees/$(echo $BRANCH | cut -d'/' -f1)"
        if [ -d "$WORKTREE" ]; then
            echo "[OK] worktree $BRANCH 存在"
        fi
    done
fi

# ---- 结果 ----
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "========================================="
    echo "  ✅ 三Agent全部就绪，零错误"
    echo "========================================="
else
    echo "========================================="
    echo "  ⚠️ 完成（$ERRORS 项需关注）"
    echo "========================================="
fi
