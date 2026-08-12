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

# ---- 0. 守护进程检查（核心！彻底解决反复修复）----
GUARDIAN_PY="E:/龙虾AI主控中心/MCP服务/fleet_guardian.py"
if tasklist 2>/dev/null | grep python | awk '{print $2}' | while read pid; do
    wmic process where "ProcessId=$pid" get CommandLine 2>/dev/null | grep -q "fleet_guardian"
done | grep -q "true\|yes"; then
    echo "[OK] 守护进程 fleet_guardian 运行中（自动管理15721/15730）"
else
    echo "[!] 守护进程未运行，正在启动..."
    "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "$GUARDIAN_PY" --daemon &
    sleep 2
    echo "[OK] 守护进程已启动"
fi

ERRORS=0

# ---- 1. 代理端口检查（守护进程会自动拉起，这里只做验证）----
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

# ---- 2. Codex CLI shim 检查（双格式） ----
SHIM_DIR="/c/Users/Administrator/AppData/Roaming/npm"
SHIM_FIXED=0

# 检查 .sh shim
if [ ! -f "$SHIM_DIR/codex" ]; then
    echo "[!] .sh shim 缺失"
    SHIM_FIXED=1
fi
# 检查 .cmd shim
if [ ! -f "$SHIM_DIR/codex.cmd" ]; then
    echo "[!] .cmd shim 缺失"
    SHIM_FIXED=1
fi
# 验证 codex 命令可用
if ! codex --version &>/dev/null; then
    echo "[!] codex 命令不可用"
    SHIM_FIXED=1
fi

if [ "$SHIM_FIXED" = "1" ]; then
    echo "[FIX] 重建 Codex shim（双格式）..."
    cat > "$SHIM_DIR/codex" << 'SHIM'
#!/bin/sh
exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
SHIM
    cat > "$SHIM_DIR/codex.cmd" << 'CMDSHIM'
@ECHO off
node "I:\npm\node_modules\@openai\codex\bin\codex.js" %*
CMDSHIM
    chmod +x "$SHIM_DIR/codex"
    if codex --version &>/dev/null; then
        echo "[OK] Codex shim 已修复"
    else
        echo "[FAIL] Codex shim 修复失败"
        ERRORS=$((ERRORS+1))
    fi
else
    echo "[OK] Codex shim 正常（双格式）"
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

# ---- 3.5 doubao-proxy stdio 净化（根治 url 不支持 stdio 报错）----
# 根因：Codex++ 运行时把 doubao-proxy 覆写成 type=stdio + url 的坏形态
# stdio 模式不允许 url/transport 字段，此处强制还原为标准形态
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
if grep -q '^\[mcp_servers\.doubao-proxy\]' "$CODEX_CONFIG" 2>/dev/null && \
   grep -A6 '^\[mcp_servers\.doubao-proxy\]' "$CODEX_CONFIG" | grep -q 'url\s*='; then
    echo "[FIX] doubao-proxy 含非法 url（stdio 冲突），还原标准形态..."
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
PYEOF
    echo "[OK] doubao-proxy 已还原为标准形态"
    ERRORS=$((ERRORS+1))
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
