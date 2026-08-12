# ============================================================
# CNB NPC 自定义Docker镜像 - 固化龙虾全套技能库
# 基于: cnbcool/default-codebuddy-npc
# 生成: docker.cnb.cool/TJF19770107/lobster-npc:latest
# ============================================================

FROM cnbcool/default-codebuddy-npc:latest

LABEL maintainer="TJF19770107"
LABEL description="龙虾NPC - 内置五步法/赛博书屋/Agnes视频生产全套技能"
LABEL version="v3.1"

# 环境变量
ENV NPC_MODEL=deepseek-v4-flash
ENV SKILL_HOT_RELOAD=true
ENV NPC_STARTUP_WAIT=5

# 创建技能库目录
RUN mkdir -p /app/skills/hermes \
    /app/skills/codex \
    /app/skills/claude-code \
    /app/skills/lobster \
    /app/templates

# ---- 层1: 全域模板（共享层） ----
COPY templates/skill_lib/global_templates/ /app/templates/

# ---- 层2: Hermes技能（策划沟通层） ----
COPY templates/skill_lib/lobster_workflow/ /app/skills/hermes/
COPY templates/skill_lib/cyber_book_house/ /app/skills/hermes/
COPY templates/skill_lib/双人口播数字人技能/ /app/skills/hermes/

# ---- 层3: Codex技能（执行调度层） ----
COPY templates/skill_lib/lobster_workflow/ /app/skills/codex/
COPY templates/skill_lib/agnes_video_auto/ /app/skills/codex/
COPY templates/skill_lib/cangjie-skill/ /app/skills/codex/

# ---- 层4: Claude Code技能（审核质检层） ----
COPY templates/skill_lib/lobster_workflow/ /app/skills/claude-code/
COPY templates/skill_lib/quality_check/ /app/skills/claude-code/

# ---- 层5: Lobster（全栈NPC层） ----
COPY templates/skill_lib/lobster_workflow/ /app/skills/lobster/
COPY templates/skill_lib/cyber_book_house/ /app/skills/lobster/
COPY templates/skill_lib/agnes_video_auto/ /app/skills/lobster/
COPY templates/skill_lib/cangjie-skill/ /app/skills/lobster/

# 启动脚本
COPY scripts/apply_scaffold.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/app/startup.sh"]
