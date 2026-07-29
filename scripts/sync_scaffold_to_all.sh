#!/bin/bash
# =====================================================
# 龙虾舰队 · 全项目脚手架同步脚本
# 用途：将脚手架模板的最新版本同步到所有 Orca 项目
# 用法：bash scripts/sync_scaffold_to_all.sh
# =====================================================

set -e

# 脚手架模板源
SCAFFOLD="E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0"

# 全部 Orca 项目列表
PROJECTS=(
    "E:/龙虾AI主控中心/我的AI分身"
    "E:/龙虾AI主控中心"
    "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/嘉盛/黄金黑马策略"
    "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/嘉盛/黄金黑马策略/ORCA20260708"
    "E:/龙虾AI主控中心/我的AI分身/CODEX量化策略20260615/币安/我的黑马策略"
    "E:/龙虾AI主控中心/我的AI分身/网盘课程资源知识萃取与沉淀体系建设"
    "E:/龙虾AI主控中心/我的AI分身/赛事预测分析系统"
    "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
)

# 需要同步的文件
SYNC_FILES=(
    ".orca/setup.sh"
    "CODEX.md"
    "scripts/launch_all_agents.sh"
    "scripts/launch_all_agents.cmd"
    "scripts/orca_project_startup.sh"
    "scripts/orca_project_startup.cmd"
    "scripts/fleet_auto_ready.sh"
)

echo ""
echo "========================================="
echo "  🦞 龙虾舰队 · 全项目脚手架同步"
echo "  源: $SCAFFOLD"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""

# 检查源目录
if [ ! -d "$SCAFFOLD" ]; then
    echo "[FAIL] 脚手架源目录不存在: $SCAFFOLD"
    exit 1
fi

TOTAL=0
UPDATED=0
SKIPPED=0
FAILED=0

for PROJECT in "${PROJECTS[@]}"; do
    NAME=$(basename "$PROJECT")
    
    # 跳过非 git 项目
    if [ ! -d "$PROJECT/.git" ]; then
        echo "[SKIP] $NAME (非 git 项目)"
        SKIPPED=$((SKIPPED+1))
        continue
    fi
    
    echo "▸ $NAME"
    
    for SYNC_FILE in "${SYNC_FILES[@]}"; do
        TOTAL=$((TOTAL+1))
        SRC="$SCAFFOLD/$SYNC_FILE"
        DST="$PROJECT/$SYNC_FILE"
        
        # 源文件不存在则跳过
        if [ ! -f "$SRC" ]; then
            continue
        fi
        
        # 创建目标目录
        DST_DIR=$(dirname "$DST")
        mkdir -p "$DST_DIR" 2>/dev/null
        
        # 比较内容，相同则跳过
        if [ -f "$DST" ] && diff -q "$SRC" "$DST" >/dev/null 2>&1; then
            continue
        fi
        
        # 复制
        if cp "$SRC" "$DST" 2>/dev/null; then
            echo "  [OK] $SYNC_FILE"
            UPDATED=$((UPDATED+1))
        else
            echo "  [FAIL] $SYNC_FILE"
            FAILED=$((FAILED+1))
        fi
    done
done

echo ""
echo "========================================="
echo "  同步完成"
echo "  项目: ${#PROJECTS[@]} | 更新: $UPDATED | 跳过: $SKIPPED | 失败: $FAILED"
echo "========================================="
echo ""
