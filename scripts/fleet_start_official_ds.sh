#!/bin/bash
# ============================================
# 舰队一键启动脚本：CNB云原生 DeepSeek-V4-Flash
# 平台：cnb.cool → @CodeBuddy NPC
# 免费到2026年12月底，无需API Key，零本地占用
# ============================================

set -e

echo "[龙虾舰队] 启动 CNB云原生模式..."
echo

# [1/3] 检查代理端口
echo "[1/3] 检查代理端口..."
for port in 15721 15730; do
    if netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
        echo "   端口 $port: 运行中 ✓"
    else
        echo "   端口 $port: 未运行，正在启动..."
        if [ "$port" = "15721" ]; then
            start //min "AutoRestore-15721" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
        elif [ "$port" = "15730" ]; then
            start //min "AutoRestore-15730" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"
        fi
        sleep 3
    fi
done

# [2/3] 设置环境变量
echo "[2/3] 设置环境变量..."
export CNB_PLATFORM=cnb.cool
export CNB_MODEL=deepseek-v4-flash
export CNB_FREE_UNTIL=2026-12-31
echo "   CNB_PLATFORM=$CNB_PLATFORM"
echo "   CNB_MODEL=$CNB_MODEL"

# [3/3] 完成
echo
echo "============================================"
echo "[完成] CNB云原生 DeepSeek-V4-Flash 已启动"
echo "- 平台: cnb.cool"
echo "- 使用: @CodeBuddy NPC"
echo "- 免费到: 2026年12月底"
echo "- API Key: 不需要"
echo "- 本地占用: 零内存/显存"
echo "- 视觉任务: 自动旁路MIMO"
echo "============================================"
echo
