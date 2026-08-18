# =============================================================================
# CNB 云原生开发环境 · 双方案并行（Hermes Web UI + DeepSeek Harness）
# =============================================================================
# 用途：
#   在 CNB「云原生开发」工作区中同时部署两个方案，**并行存在，都能正常工作**：
#
#   A. Hermes Studio Web GUI（hermes-web-ui）   → 端口 6060
#      官方镜像 ekkoye8888/hermes-web-ui:v0.6.39（约 1.49GB）
#      node dist/server/index.js → 打开 https://{id}-6060.cnb.run
#
#   B. DeepSeek Harness 云端超 Agent 运行时       → 端口 8080
#      纯 Python 轻量实现（python:3.11-slim），零外部依赖
#      harness_proxy.py → 打开 https://{id}-8080.cnb.run
#
# 两者共享同一环境变量（CNB_TOKEN / ACC_PRODUCT_CONFIG_V2）解析免费网关，
# 基座同为 CNB 内置免费 DeepSeek-V4-Flash，互不冲突、互不干扰。
#
# 安全红线：
#   - 镜像【严禁写入任何密钥】；模型网关鉴权全部来自环境变量注入（CNB_TOKEN）
# =============================================================================

# ---- 基础镜像：官方 Hermes Web UI（含 node 运行时 + Web 控制台）----
# ⚠️ tag 必须带 v 前缀：Docker Hub 上仓库 tag 为 v0.6.39（0.6.39 不存在，404）
FROM ekkoye8888/hermes-web-ui:v0.6.39

# ---- 1. 基础工具链 + Python3（deepseek-harness 需要）----
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl wget unzip git git-lfs openssh-server \
       python3 python3-pip procps ripgrep jq \
       fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install || true

# ---- 2. CNB CLI / Skills 运行时 ----
RUN npm install -g @cnbcool/cnb-cli skills \
    && npx skills add https://cnb.cool/cnb/skills/cnb-skill.git -g -y || true

# ---- 3. CNB 内置免费网关适配层（Hermes Studio provider 可指向本层）----
COPY adapters/anthropic_to_cnb.py /usr/local/bin/anthropic_to_cnb.py
RUN chmod +x /usr/local/bin/anthropic_to_cnb.py

# ---- 4. 部署 DeepSeek Harness 运行时（路径A，独立于 Hermes Web UI）----
WORKDIR /opt/deepseek-harness
COPY deepseek-harness/harness_proxy.py .
COPY deepseek-harness/harness_agent.py .
COPY deepseek-harness/web_console.html .
COPY deepseek-harness/harness_skills.json .
COPY deepseek-harness/run_harness.sh .
RUN chmod +x harness_proxy.py harness_agent.py run_harness.sh

# ---- 5. Hermes Web UI 环境配置（6060 端口）----
ENV PORT=6060
ENV BIND_HOST=0.0.0.0
ENV HERMES_HOME=/home/agent/.hermes
ENV HERMES_WEB_UI_MANAGED_GATEWAY=1
ENV HERMES_WEB_UI_XAI_CALLBACK_BIND_HOST=0.0.0.0
ENV HERMES_ALLOW_ROOT_GATEWAY=1
ENV PATH=/opt/hermes/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# ---- 6. 端口：6060(Hermes Web UI) + 8080(DeepSeek Harness) ----
EXPOSE 6060 8651 56121 8080

# ---- 7. 启动入口：同时拉起两个服务 ----
COPY .ide/start.sh /usr/local/bin/cnb-start.sh
RUN chmod +x /usr/local/bin/cnb-start.sh

ENTRYPOINT ["/usr/local/bin/cnb-start.sh"]
CMD []
