# =============================================================================
# Claude-Code CNB NPC 自定义运行镜像（路径B：Claude-Code 真身嵌入）
# =============================================================================
# 用途：
#   将 Claude-Code CLI 装入 NPC 运行镜像，并把 Claude-Code 原生 Anthropic 请求
#   通过 adapters/anthropic_to_cnb.py 转发到 CNB 内置免费 DeepSeek-V4-Flash 网关。
#
# 构建与推送（在 CNB 流水线中）：
#   docker build -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:latest .
#   docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:latest
#
# 然后 .cnb.yml 中 docker.image 改为引用该镜像。
# 注意：路径A（npc:go + options.model=deepseek-v4-flash）无需本镜像即可用，
#       本镜像是为"必须在容器内跑 Claude-Code CLI"的场景准备的增强方案。
# =============================================================================

FROM node:22-bookworm-slim

# 基础工具链 + CNB CLI/Skills 运行时
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git git-lfs curl jq ripgrep python3 python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install \
    && npm install -g @cnbcool/cnb-cli skills \
    && npx skills add https://cnb.cool/cnb/skills/cnb-skill.git -g -y

# 适配层（从仓库复制，避免 RUN 中依赖未挂载源码）
COPY adapters/anthropic_to_cnb.py /usr/local/bin/anthropic_to_cnb.py
RUN chmod +x /usr/local/bin/anthropic_to_cnb.py

WORKDIR /workspace

# 默认启动适配层（Claude-Code 通过 ANTHROPIC_BASE_URL=http://127.0.0.1:8787 接入）
ENV ANTHROPIC_BASE_URL=http://127.0.0.1:8787
ENV ADAPTER_HOST=127.0.0.1
ENV ADAPTER_PORT=8787
EXPOSE 8787

CMD ["python3", "/usr/local/bin/anthropic_to_cnb.py"]
