# =============================================================================
# Claude-Code CNB NPC 自定义运行镜像（路径B：完整 Claude-Code CLI + 容器模式）
# =============================================================================
# 用途：
#   将【完整原版 Claude-Code CLI】装入 NPC 运行镜像（不蒸馏、不裁剪原生
#   MCP/插件/Skill 能力），并把 Claude-Code 原生 Anthropic 请求通过
#   adapters/anthropic_to_cnb.py 转发到 CNB 内置免费 DeepSeek-V4-Flash 网关。
#
# 与路径A（npc:go 内置蒸馏轻量化 NPC）的区别：
#   - 路径A：CNB 平台封装好的轻量化简化小程序，开箱即用、速度快
#   - 路径B：本镜像打包完整原版 Claude-Code CLI，每次 NPC 任务拉起一个
#            独立容器执行单元，原生 MCP/插件/Skill 全部保留
#
# 构建与推送（在 CNB 流水线中执行，见 .cnb.yml main.push 镜像构建块）：
#   docker build -t ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.5.0 .
#   docker push ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.5.0
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

# ---- 5. 容器入口：拉起适配层 + Claude-Code CLI 服务 ----
COPY claude/entrypoint.sh /usr/local/bin/claude-npc-entrypoint.sh
RUN chmod +x /usr/local/bin/claude-npc-entrypoint.sh

WORKDIR /workspace

# ---- 6. 默认环境（鉴权全部来自运行环境变量注入，镜像零硬编码密钥）----
ENV ANTHROPIC_BASE_URL=http://127.0.0.1:8787
ENV ADAPTER_HOST=127.0.0.1
ENV ADAPTER_PORT=8787
ENV CNB_MODEL=deepseek-v4-flash
ENV REASONING_EFFORT=high
ENV QUOTA_LIMIT=1600
EXPOSE 8787

# 默认启动适配层（Claude-Code 通过 ANTHROPIC_BASE_URL=http://127.0.0.1:8787 接入）
CMD ["python3", "/usr/local/bin/anthropic_to_cnb.py"]
