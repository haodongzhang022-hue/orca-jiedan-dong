#!/bin/bash
# 龙虾舰队 · 多代理健康检查脚本
# 用途：一键检查所有代理服务和端口状态
# 运行：bash scripts/fleet_health_check.sh

echo "=========================================="
echo "  龙虾舰队 · 健康检查  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_port() {
    local port=$1
    local name=$2
    if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
        local pid=$(netstat -ano 2>/dev/null | grep "LISTENING" | grep ":${port} " | awk '{print $5}' | head -1)
        echo -e "  ${GREEN}✓${NC} ${name} (端口 ${port}) - 运行中 [PID: ${pid}]"
        return 0
    else
        echo -e "  ${RED}✗${NC} ${name} (端口 ${port}) - ${RED}未运行${NC}"
        return 1
    fi
}

check_process() {
    local name=$1
    if tasklist 2>/dev/null | grep -qi "$name"; then
        echo -e "  ${GREEN}✓${NC} ${name} 进程存在"
        return 0
    else
        echo -e "  ${YELLOW}!${NC} ${name} 进程未找到"
        return 1
    fi
}

check_config() {
    local file=$1
    local name=$2
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} ${name}: ${file}"
        return 0
    else
        echo -e "  ${RED}✗${NC} ${name}: ${file} ${RED}不存在${NC}"
        return 1
    fi
}

errors=0

echo ""
echo "▸ 代理端口检查"
check_port 15721 "Anthropic Proxy (Claude Code)" || ((errors++))
check_port 15730 "Codex Tool Proxy (Codex 系列)" || ((errors++))
check_port 8642  "Hermes Gateway" || ((errors++))
check_port 5230  "Memos" || ((errors++))

echo ""
echo "▸ 关键进程检查"
check_process "codex" || true
check_process "claude" || true
check_process "hermes" || true
check_process "Orca" || true
check_process "python" || true

echo ""
echo "▸ 配置文件检查"
check_config "$HOME/.codex/config.toml" "Codex 桌面版" || ((errors++))
check_config "E:/龙虾AI主控中心/Codex/.codex/config.toml" "Codex 项目版" || ((errors++))
check_config "$HOME/.claude.json" "Claude Code" || ((errors++))
check_config "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py" "Anthropic 代理脚本" || ((errors++))
check_config "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py" "Codex 代理脚本" || ((errors++))

echo ""
echo "▸ Codex 配置一致性检查"
# 检查 Codex 桌面版 wire_api
if grep -q 'wire_api = "chat"' "$HOME/.codex/config.toml" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Codex 桌面版 wire_api = chat"
else
    echo -e "  ${RED}✗${NC} Codex 桌面版 wire_api 不是 chat（可能导致 401 错误）"
    ((errors++))
fi

# 检查 Codex 桌面版 base_url
if grep -q '127.0.0.1:15730' "$HOME/.codex/config.toml" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Codex 桌面版 base_url 指向 15730 代理"
else
    echo -e "  ${YELLOW}!${NC} Codex 桌面版 base_url 未指向 15730 代理"
fi

echo ""
echo "▸ API 连通性测试"
# 测试 15730 代理
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:15730/v1/models 2>/dev/null | grep -q "200"; then
    echo -e "  ${GREEN}✓${NC} 15730 代理响应正常 (HTTP 200)"
else
    echo -e "  ${RED}✗${NC} 15730 代理无响应或异常"
    ((errors++))
fi

# 测试 15721 代理
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:15721/health 2>/dev/null | grep -q "200"; then
    echo -e "  ${GREEN}✓${NC} 15721 代理响应正常 (HTTP 200)"
else
    echo -e "  ${YELLOW}!${NC} 15721 代理无 /health 端点或未运行"
fi

echo ""
echo "=========================================="
if [ $errors -eq 0 ]; then
    echo -e "  ${GREEN}✓ 所有检查通过，舰队状态健康${NC}"
else
    echo -e "  ${RED}✗ 发现 ${errors} 个问题，请检查上方详情${NC}"
fi
echo "=========================================="
