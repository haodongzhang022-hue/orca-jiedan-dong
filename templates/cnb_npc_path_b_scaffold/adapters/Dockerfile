# =============================================================================
# Claude-Code CNB NPC 自定义运行镜像（路径B：完整 Claude-Code CLI + 容器模式）
# =============================================================================
# 用途：
#   将【完整原版 Claude-Code CLI】装入 NPC 运行镜像（不蒸馏、不裁剪原生
#   MCP/插件/Skill 能力），并把 Claude-Code 原生 Anthropic 请求通过
#   adapters/anthropic_to_cnb.py 转发到 CNB 内置免费 DeepSeek-V4-Flash 网关。
#   同时内置【GitHub 原生 Hermes CLI（NousResearch/hermes-agent）】供 @hermes
#   大脑层角色使用（路径B 容器模式，模型端点同样指向 CNB 免费基座）。
#
# 与路径A（npc:go 内置蒸馏轻量化 NPC）的区别：
#   - 路径A：CNB 平台封装好的轻量化简化小程序，开箱即用、速度快
#   - 路径B：本镜像打包完整原版 Claude-Code CLI，每次 NPC 任务拉起一个
#            独立容器执行单元，原生 MCP/插件/Skill 全部保留
#
# 构建与推送（在 CNB 流水线中执行，见 .cnb.yml main.push 镜像构建块）：
#   docker build -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.6.0 .
#   docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.6.0
#
# 然后在 .cnb.yml 的 claude-code 角色（路径B）docker.image 中引用该镜像。
#
# 安全红线：
#   - 镜像【严禁写入任何密钥】，鉴权全部读取容器环境变量（CNB 流水线注入）
#   - CNB_TOKEN / ACC_PRODUCT_CONFIG_V2 / QUOTA_* 均来自运行环境，不在镜像内
# =============================================================================

FROM node:22-bookworm-slim

# ---- 1. 基础工具链 + CNB CLI/Skills 运行时 ----
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git git-lfs curl jq ripgrep python3 python3-pip procps \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install \
    && npm install -g @cnbcool/cnb-cli skills \
    && npx skills add https://cnb.cool/cnb/skills/cnb-skill.git -g -y

# ---- 2. 安装【完整原版 Claude-Code CLI】（不蒸馏、不裁剪原生 MCP/插件/Skill）----
# 官方推荐：通过 claude-agent-sdk 或 npm 全局包安装完整 CLI。
# 此处安装官方 @anthropic-ai/claude-code 全局包；若网络受限可改用
# `npm install -g claude-agent-sdk`（SDK 亦包含完整 CLI 二进制）。
RUN npm install -g @anthropic-ai/claude-code || \
    (echo "[Dockerfile] @anthropic-ai/claude-code 安装失败，回退 claude-agent-sdk" \
     && npm install -g claude-agent-sdk)
RUN claude --version 2>/dev/null || true

# ---- 3. 协议适配层（Anthropic → CNB 内置 AI 网关）----
COPY adapters/anthropic_to_cnb.py /usr/local/bin/anthropic_to_cnb.py
RUN chmod +x /usr/local/bin/anthropic_to_cnb.py

# ---- 4. 额度监控脚本（打包进镜像）----
COPY scripts/quota_monitor.py /usr/local/bin/quota_monitor.py
RUN chmod +x /usr/local/bin/quota_monitor.py

# ---- 5. 原生 Codex CLI（@openai/codex · 真·原生完整 CLI）----
# 官方 npm 包 @openai/codex（bin=codex.js，内含 linux-x64 二进制），可直接打包进镜像。
RUN npm install -g @openai/codex || \
    (echo "[Dockerfile] @openai/codex 安装失败，尝试 pnpm/二进制回退" \
     && npm install -g codex-cli 2>/dev/null || true)
RUN codex --version 2>/dev/null | head -1 || true

# ---- 6. 原生 Hermes CLI（GitHub NousResearch/hermes-agent · 大脑层引擎）----
# 通过 adapters/hermes_entry.sh 安装（pip install hermes-agent 或官方 install.sh）
COPY adapters/hermes_entry.sh /usr/local/bin/hermes_entry.sh
RUN chmod +x /usr/local/bin/hermes_entry.sh \
    && bash /usr/local/bin/hermes_entry.sh || true
RUN hermes --version 2>/dev/null | head -1 || true

# ---- 7. 容器入口：拉起适配层 + Claude-Code CLI / Codex / Hermes 服务 ----
COPY claude/entrypoint.sh /usr/local/bin/claude-npc-entrypoint.sh
RUN chmod +x /usr/local/bin/claude-npc-entrypoint.sh

COPY hermes/entrypoint.sh /usr/local/bin/hermes-npc-entrypoint.sh
RUN chmod +x /usr/local/bin/hermes-npc-entrypoint.sh

WORKDIR /workspace

# ---- 8. 默认环境（鉴权全部来自运行环境变量注入，镜像零硬编码密钥）----
ENV ANTHROPIC_BASE_URL=http://127.0.0.1:8787
ENV ADAPTER_HOST=127.0.0.1
ENV ADAPTER_PORT=8787
ENV CNB_MODEL=deepseek-v4-flash
ENV REASONING_EFFORT=high
ENV QUOTA_LIMIT=1600
EXPOSE 8787

# ---- 9. 容器入口（ENTRYPOINT + CMD 组合）----
# 设计说明：
#   - NPC 事件由平台 npc:go 内置任务在【本镜像容器】内驱动，评论内容自动作为 prompt；
#   - 为使容器内始终有可用的协议适配层（127.0.0.1:8787，Anthropic → CNB 内置网关），
#     ENTRYPOINT 在后台拉起适配层并保持前台存活，npc:go 在同一容器内执行 AI 任务时
#     可随时通过 ANTHROPIC_BASE_URL=http://127.0.0.1:8787 接入原版 Claude-Code CLI 能力；
#   - @claude-code → claude 入口（claude-npc-entrypoint.sh）
#   - @hermes     → hermes 入口（hermes-npc-entrypoint.sh，原生 hermes CLI）
#   - 默认入口保持 claude 适配层（兼容既有 claude-code 角色）。
ENTRYPOINT ["/usr/local/bin/claude-npc-entrypoint.sh"]
CMD ["python3", "/usr/local/bin/anthropic_to_cnb.py"]
