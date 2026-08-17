# =============================================================================
# CNB 云原生开发环境 · DeepSeek Harness 云端控制台（替代 Hermes Studio 方案）
# =============================================================================
# 用途：
#   在 CNB「云原生开发」工作区中部署独立自研的 DeepSeek Harness 云端运行时，
#   浏览器直接打开 → 企业微信接单控制台 + 免费 DeepSeek-V4-Flash 编排 Agent。
#
# ❌ 非 Hermes Studio：本镜像【不】使用 ekkoye8888/hermes-web-ui，而是
#    自带轻量 Python 运行时（harness_proxy + harness_agent + web_console），
#    零外部依赖、零积分、免费 DeepSeek-V4-Flash 基座。
#
# 与旧 Hermes Web UI 方案的区别：
#   - 旧：1.49GB hermes-web-ui 镜像 + node dist/server/index.js（重，回收即失）
#   - 新：纯 Python HTTP 网关 + 编排 Agent + 静态控制台（轻，<100MB 基础镜像）
#
# 安全红线：
#   - 镜像【严禁写入任何密钥】；模型网关鉴权全部来自环境变量注入（CNB_TOKEN）
# =============================================================================

FROM python:3.11-slim

# ---- 1. 基础工具链 ----
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl wget git procps jq fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# ---- 2. 复制 DeepSeek Harness 运行时 ----
WORKDIR /opt/deepseek-harness
COPY deepseek-harness/harness_proxy.py .
COPY deepseek-harness/harness_agent.py .
COPY deepseek-harness/web_console.html .
RUN chmod +x harness_proxy.py harness_agent.py

# ---- 3. CNB CLI / Skills（便于在云端容器内操作仓库/NPC/接单流水线）----
RUN pip install --no-cache-dir --quiet \
    && npm install -g @cnbcool/cnb-cli skills 2>/dev/null || true

# ---- 4. 端口 ----
# HARNESS_PORT=8080：控制台 + OpenAI 兼容网关 + 企微接单入口
EXPOSE 8080

# ---- 5. 启动入口 ----
COPY .ide/start.sh /usr/local/bin/cnb-harness-start.sh
RUN chmod +x /usr/local/bin/cnb-harness-start.sh
ENTRYPOINT ["/usr/local/bin/cnb-harness-start.sh"]
CMD []
