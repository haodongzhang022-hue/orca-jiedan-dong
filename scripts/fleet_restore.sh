#!/bin/bash
# =====================================================================
# 龙虾舰队 · 一键恢复脚本 v2.0
# 功能：自动健康检查 → 自动修复 → 分支同步 → 快照备份
# 用途：打开项目时自动执行，无需手动干预
# 运行：bash scripts/fleet_restore.sh [--auto] [--snapshot]
#   --auto     静默模式，不显示交互提示
#   --snapshot 恢复后自动创建快照
# =====================================================================

set -e

PROJECT_ROOT="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
MCP_DIR="E:/龙虾AI主控中心/MCP服务"
PYEXE="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
CODEX_DESKTOP_CONFIG="$HOME/.codex/config.toml"
CODEX_PROJECT_CONFIG="E:/龙虾AI主控中心/Codex/.codex/config.toml"
SNAPSHOT_DIR="$PROJECT_ROOT/snapshots"
MAX_SNAPSHOT_SIZE=20  # MB
AUTO_MODE=false
DO_SNAPSHOT=false
ERRORS=0
FIXES=0

# 解析参数
for arg in "$@"; do
    case $arg in
        --auto) AUTO_MODE=true ;;
        --snapshot) DO_SNAPSHOT=true ;;
    esac
done

log() { echo "[$(date '+%H:%M:%S')] $1"; }
ok() { echo "  ✓ $1"; }
warn() { echo "  ⚠ $1"; }
fail() { echo "  ✗ $1"; ((ERRORS++)); }
fix() { echo "  🔧 $1"; ((FIXES++)); }

# =====================================================================
# 第一步：端口健康检查 + 自动拉起
# =====================================================================
check_and_start_port() {
    local port=$1
    local name=$2
    local script=$3

    if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
        local pid=$(netstat -ano 2>/dev/null | grep "LISTENING" | grep ":${port} " | awk '{print $5}' | head -1)
        ok "$name (端口 $port) 运行中 [PID: $pid]"
        return 0
    else
        warn "$name (端口 $port) 未运行，正在拉起..."
        if [ -f "$script" ]; then
            start //min "AutoRestore-${port}" "$PYEXE" "$script" 2>/dev/null &
            sleep 3
            if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
                fix "$name 已自动恢复 (端口 $port)"
                return 0
            else
                fail "$name 拉起失败 (端口 $port)"
                return 1
            fi
        else
            fail "$name 脚本不存在: $script"
            return 1
        fi
    fi
}

# =====================================================================
# 第二步：配置文件校验 + 自动修复
# =====================================================================
fix_codex_desktop_config() {
    if [ ! -f "$CODEX_DESKTOP_CONFIG" ]; then
        fail "Codex 桌面版配置不存在: $CODEX_DESKTOP_CONFIG"
        return 1
    fi

    local needs_fix=false

    # 检查 wire_api
    if ! grep -q 'wire_api = "chat"' "$CODEX_DESKTOP_CONFIG" 2>/dev/null; then
        warn "Codex 桌面版 wire_api 不是 chat"
        needs_fix=true
    fi

    # 检查 base_url
    if ! grep -q '127.0.0.1:15730' "$CODEX_DESKTOP_CONFIG" 2>/dev/null; then
        warn "Codex 桌面版 base_url 未指向 15730 代理"
        needs_fix=true
    fi

    # 检查 model_provider 是否为 mimo-v2.5-pro
    if ! grep -q 'model_provider.*mimo' "$CODEX_DESKTOP_CONFIG" 2>/dev/null; then
        warn "Codex 桌面版 model_provider 不是 mimo"
        needs_fix=true
    fi

    if $needs_fix; then
        # 备份
        cp "$CODEX_DESKTOP_CONFIG" "${CODEX_DESKTOP_CONFIG}.bak.$(date +%Y%m%d_%H%M%S)"
        fix "Codex 桌面版配置已备份"

        # 重写正确配置
        cat > "$CODEX_DESKTOP_CONFIG" << 'TOMLEOF'
model_provider = "mimo-v2.5-pro"
model = "mimo-v2.5-pro"
model_reasoning_effort = "high"
disable_response_storage = true
preferred_auth_method = "apikey"

[model_providers.mimo-v2.5-pro]
name = "MiMo V2.5 Pro (via Proxy)"
wire_api = "chat"
base_url = "http://127.0.0.1:15730/v1"
api_key = "tp-cs3zbef7vhc75lcpsw9x7pau27mjftwhqnovn5zrq2d0puft"

[features]
js_repl = false

[memories]
generate_memories = true
use_memories = true

[windows]
sandbox = "elevated"

[projects.'e:\龙虾ai主控中心\我的ai分身']
trust_level = "trusted"

[projects.'e:\龙虾ai主控中心\我的ai分身\企业微信群定制接单项目']
trust_level = "trusted"

[mcp_servers.node_repl]
args = []
command = 'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\3c238e29bbc930ff\node_repl.exe'
startup_timeout_sec = 120

[mcp_servers.node_repl.env]
BROWSER_USE_AVAILABLE_BACKENDS = "chrome,iab"
BROWSER_USE_MARKETPLACE_NAME = "openai-bundled"
CODEX_CLI_PATH = 'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\3f4fb8cdd344abc7\codex.exe'
CODEX_HOME = 'C:\Users\Administrator\.codex'
NODE_REPL_NATIVE_PIPE_CONNECT_TIMEOUT_MS = "1000"
NODE_REPL_NODE_MODULE_DIRS = ""
NODE_REPL_NODE_PATH = 'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\5b9024f90663758b\node.exe'
NODE_REPL_TRUSTED_BROWSER_CLIENT_SHA256S = "167fdf579477181fba1773c1efb067b00c5a64fe85dafb50a2001bde198dc739"
NODE_REPL_TRUSTED_CODE_PATHS = 'C:\Users\Administrator\.codex'
NODE_REPL_UNTRUSTED_ENV_ALLOWLIST = "BROWSER_USE_MARKETPLACE_NAME"
TOMLEOF
        fix "Codex 桌面版配置已修复 (wire_api=chat, base_url=15730, model=mimo-v2.5-pro)"
    else
        ok "Codex 桌面版配置正确"
    fi
}

# =====================================================================
# 第三步：API 连通性验证
# =====================================================================
verify_api() {
    local port=$1
    local name=$2

    local health=$(curl -s --max-time 5 "http://127.0.0.1:${port}/health" 2>/dev/null)
    if echo "$health" | grep -q '"status".*"ok"'; then
        ok "$name API 连通正常"
        return 0
    else
        warn "$name API 健康检查异常，尝试实际调用..."
        local result=$(curl -s --max-time 10 -X POST "http://127.0.0.1:${port}/v1/chat/completions" \
            -H "Content-Type: application/json" \
            -d '{"model":"mimo-v2.5-pro","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' 2>/dev/null)
        if echo "$result" | grep -q '"choices"'; then
            ok "$name 实际调用正常"
            return 0
        else
            fail "$name API 调用失败"
            return 1
        fi
    fi
}

# =====================================================================
# 第四步：分支同步
# =====================================================================
sync_branches() {
    cd "$PROJECT_ROOT"
    local current_branch=$(git branch --show-current 2>/dev/null)

    for worktree_path in "$PROJECT_ROOT/worktrees/claude" "$PROJECT_ROOT/worktrees/codex" "$PROJECT_ROOT/worktrees/hermes"; do
        if [ -d "$worktree_path" ]; then
            local branch_name=$(cd "$worktree_path" && git branch --show-current 2>/dev/null)
            local behind=$(cd "$worktree_path" && git rev-list --count HEAD..master 2>/dev/null || echo "0")
            if [ "$behind" -gt 0 ]; then
                (cd "$worktree_path" && git merge master --no-edit 2>/dev/null)
                fix "$branch_name 同步到 master (追上 $behind 个提交)"
            else
                ok "$branch_name 已是最新"
            fi
        fi
    done
}

# =====================================================================
# 第五步：快照管理
# =====================================================================
manage_snapshots() {
    # 清理超过限制的旧快照
    if [ -d "$SNAPSHOT_DIR" ]; then
        local total_size=$(du -sm "$SNAPSHOT_DIR" 2>/dev/null | awk '{print $1}')
        if [ "$total_size" -gt "$MAX_SNAPSHOT_SIZE" ]; then
            warn "快照目录 ${total_size}MB 超过 ${MAX_SNAPSHOT_SIZE}MB 限制，清理旧快照..."
            cd "$SNAPSHOT_DIR"
            ls -t *.tar.gz 2>/dev/null | tail -n +3 | xargs rm -f 2>/dev/null
            fix "旧快照已清理"
        fi
    fi

    if $DO_SNAPSHOT; then
        local snapshot_name="fleet_snapshot_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$SNAPSHOT_DIR"
        cd "$PROJECT_ROOT"

        # 只打包关键配置文件，不打包 node_modules 等
        tar czf "$SNAPSHOT_DIR/${snapshot_name}.tar.gz" \
            --exclude='worktrees' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='node_modules' \
            .env .gitignore README.md \
            scripts/*.sh scripts/*.cmd \
            snapshots/README.md \
            SKILL.md skill_registry.json \
            config/ docs/ templates/ \
            2>/dev/null || true

        local snap_size=$(du -h "$SNAPSHOT_DIR/${snapshot_name}.tar.gz" 2>/dev/null | awk '{print $1}')
        ok "快照已创建: ${snapshot_name}.tar.gz ($snap_size)"
    fi
}

# =====================================================================
# 主流程
# =====================================================================
echo ""
echo "=========================================="
echo "  🦞 龙虾舰队 · 一键恢复 v2.0"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

log "▸ 第一步：端口健康检查 + 自动拉起"
check_and_start_port 15721 "Anthropic Proxy (Claude Code)" "$MCP_DIR/anthropic_proxy_15721.py"
check_and_start_port 15730 "Codex Tool Proxy (Codex)" "$MCP_DIR/codex_tool_proxy.py"
echo ""

log "▸ 第二步：配置文件校验 + 自动修复"
fix_codex_desktop_config
echo ""

log "▸ 第三步：API 连通性验证"
verify_api 15730 "Codex Proxy"
verify_api 15721 "Anthropic Proxy"
echo ""

log "▸ 第四步：分支同步"
sync_branches
echo ""

log "▸ 第五步：快照管理"
manage_snapshots
echo ""

# =====================================================================
# 汇总报告
# =====================================================================
echo "=========================================="
echo "  恢复完成"
echo "  问题: $ERRORS | 修复: $FIXES"
if [ $ERRORS -eq 0 ]; then
    echo "  状态: ✅ 全部正常"
else
    echo "  状态: ⚠️  有 $ERRORS 个问题需要手动处理"
fi
echo "=========================================="
echo ""

if [ $ERRORS -gt 0 ] && ! $AUTO_MODE; then
    echo "如需手动排查，请运行: bash scripts/fleet_health_check.sh"
fi

exit $ERRORS
