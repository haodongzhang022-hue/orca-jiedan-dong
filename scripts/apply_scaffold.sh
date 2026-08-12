#!/bin/bash
# ============================================================
# CNB NPC 脚手架脚本 v2.0
# 新增：Skill技能库自动挂载 + 热重载
# 龙虾五步法 V3.3 | 2026-08-08
# ============================================================

set -euo pipefail

SKILL_LIB_DIR="templates/skill_lib"
CONTAINER_SKILL_DIR="/app/skills"
NPC_ROLES=("hermes" "codex" "claude-code" "lobster")
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")"

echo "[apply_scaffold v2.0] 技能库自动挂载启动..."

# ========== 1. 检查技能库目录 ==========
if [ ! -d "${REPO_ROOT}/${SKILL_LIB_DIR}" ]; then
    echo "[WARN] ${SKILL_LIB_DIR} 目录不存在，跳过技能挂载"
else
    echo "[OK] 检测到技能库目录: ${SKILL_LIB_DIR}"
    ls -la "${REPO_ROOT}/${SKILL_LIB_DIR}/"
fi

# ========== 2. 按角色分层挂载技能 ==========
# Hermes: 客户沟通、需求拆解、策划类技能
declare -A ROLE_SKILL_MAP
ROLE_SKILL_MAP["hermes"]="lobster_workflow global_templates cyber_book_house 双人口播数字人 龙虾AI短剧剧本"
ROLE_SKILL_MAP["codex"]="lobster_workflow global_templates agnes_video_auto cangjie-skill script_splitter ffmpeg_merger"
ROLE_SKILL_MAP["claude-code"]="lobster_workflow global_templates content_review quality_check compliance"
ROLE_SKILL_MAP["lobster"]="lobster_workflow global_templates cyber_book_house cangjie-skill agnes_video_auto"

for role in "${NPC_ROLES[@]}"; do
    ROLE_SKILL_DIR="${CONTAINER_SKILL_DIR}/${role}"
    mkdir -p "${ROLE_SKILL_DIR}"

    echo "[${role}] 挂载技能: ${ROLE_SKILL_MAP[$role]}"
    for skill in ${ROLE_SKILL_MAP[$role]}; do
        SKILL_SRC="${REPO_ROOT}/${SKILL_LIB_DIR}/${skill}"
        if [ -d "${SKILL_SRC}" ]; then
            cp -r "${SKILL_SRC}"/* "${ROLE_SKILL_DIR}/" 2>/dev/null || true
            echo "  + ${skill} (目录)"
        elif [ -f "${SKILL_SRC}.md" ]; then
            cp "${SKILL_SRC}.md" "${ROLE_SKILL_DIR}/"
            echo "  + ${skill}.md (文件)"
        else
            echo "  - ${skill} (未找到，跳过)"
        fi
    done
done

# ========== 3. 预加载技能库 ==========
echo "[预加载] 各角色NPC启动时自动读取技能..."
for role in "${NPC_ROLES[@]}"; do
    PRELOAD_FILE="${CONTAINER_SKILL_DIR}/${role}/_preload.txt"
    ls "${CONTAINER_SKILL_DIR}/${role}/" 2>/dev/null > "${PRELOAD_FILE}" || true
    echo "[${role}] 预加载完成: $(wc -l < "${PRELOAD_FILE}" 2>/dev/null || echo 0) 个技能"
done

# ========== 4. CNB NPC启动配置 ==========
echo "[NPC启动] 写入启动参数..."
cat > /app/npc_startup.json << 'EOF'
{
  "model": "deepseek-v4-flash",
  "skill_preload": true,
  "skill_hot_reload": true,
  "skill_poll_interval": 60,
  "cors_enabled": true,
  "api_auth_required": true
}
EOF

echo "[apply_scaffold v2.0] 完成！"
echo "技能已分层挂载，各NPC就绪:"
for role in "${NPC_ROLES[@]}"; do
    echo "  @npc/${role}: $(ls "${CONTAINER_SKILL_DIR}/${role}/" 2>/dev/null | wc -l) 个技能文件"
done
