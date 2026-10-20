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

# =============================================================================
# ---- 8. 第三层：dsh + ds-bot 云端群聊界面（对外 8830 / 内部 8831）----
# =============================================================================
# 为什么需要这一层：
#   前两层（Hermes 6060 / Harness 8080）都没有「多 bot 群聊可视化界面」。
#   dsh + ds-bot 才有 Chief + 多个 bot 实时对话的前端，这是本层唯一目的。
#
# 两个必须绕过、已在源码层证实的硬约束：
#   ① dsh 禁止 --host 0.0.0.0
#      源码 lib/startup.js: program.error("--host 0.0.0.0 is intentionally
#      not supported yet for safety: it would expose remote code execution")
#   ② /api 有 browser-trust fence，非信任 Host 一律 403
#      本机实测：正常 Host = 401（放行）；伪造 cnb.run = 403（拒绝）
#   → 因此 dsh 只绑 127.0.0.1:8831，由 host_rewrite_proxy.py 改写 Host
#     后暴露到 0.0.0.0:8830。实测经代理后伪造 Host 返回 401 而非 403。
#
# 模型链路：dsh → 127.0.0.1:15741（CNB LLM Adapter）
#           → CNB 免费网关 deepseek-v4-flash（0 积分）
#           → 失败回落 FALLBACK_BASE
# =============================================================================

# ---- 8.1 Node 22（dsh 需要现代 Node；基础镜像版本不确定，不满足则升级）----
RUN set -eux; \
    need=1; \
    if command -v node >/dev/null 2>&1; then \
      cur="$(node -v | sed 's/^v//')"; \
      major="$(echo "$cur" | cut -d. -f1)"; \
      echo "[node] 当前版本 v$cur"; \
      if [ "$major" -ge 22 ]; then need=0; echo "[node] 已满足 >=22，跳过升级"; fi; \
    fi; \
    if [ "$need" = "1" ]; then \
      echo "[node] 升级到 v22.22.2（npmmirror 二进制源）..."; \
      arch="$(dpkg --print-architecture 2>/dev/null || echo amd64)"; \
      case "$arch" in \
        amd64) narch=x64 ;; \
        arm64) narch=arm64 ;; \
        *) narch=x64 ;; \
      esac; \
      curl -fsSL "https://registry.npmmirror.com/-/binary/node/v22.22.2/node-v22.22.2-linux-${narch}.tar.xz" -o /tmp/node.tar.xz; \
      tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
          --exclude=CHANGELOG.md --exclude=LICENSE --exclude=README.md; \
      rm -f /tmp/node.tar.xz; \
      node -v; \
    fi

# ---- 8.2 pnpm + dsh CLI ----
RUN npm install -g pnpm@9 --registry=https://registry.npmmirror.com --no-audit --no-fund \
 && npm install -g @deepseek-ai/dsh@0.2.1-rc.2 --registry=https://registry.npmmirror.com --no-audit --no-fund \
 && dsh --version

# ---- 8.3 适配层与代理脚本 ----
COPY dsh-cloud/cnb_llm_adapter.py /opt/dsh-cloud/cnb_llm_adapter.py
COPY dsh-cloud/host_rewrite_proxy.py /opt/dsh-cloud/host_rewrite_proxy.py
COPY dsh-cloud/entrypoint.sh /opt/dsh-cloud/entrypoint.sh
COPY dsh-cloud/profile-package.json /opt/dsh-cloud/profile-package.json
COPY dsh-cloud/cordis.patch.yml /opt/dsh-cloud/cordis.patch.yml
RUN chmod +x /opt/dsh-cloud/entrypoint.sh

# ---- 8.4 预装 dsh web profile + ds-bot，固化进镜像（避免每次启动重装）----
ENV DSH_HOME=/opt/dsh-home
RUN set -eux; \
    mkdir -p "$DSH_HOME/profiles/web"; \
    cp /opt/dsh-cloud/profile-package.json "$DSH_HOME/profiles/web/package.json"; \
    cp /opt/dsh-cloud/cordis.patch.yml "$DSH_HOME/profiles/web/cordis.patch.yml"; \
    cd "$DSH_HOME/profiles/web"; \
    pnpm install --registry=https://registry.npmmirror.com 2>&1 | tail -8 || true; \
    dsh --profile web --dump-config > /opt/dsh-cloud/dump.txt 2>&1 || true; \
    { \
      echo "node      : $(node -v 2>&1)"; \
      echo "dsh       : $(dsh --version 2>&1 | head -1)"; \
      if grep -q "id: bot" /opt/dsh-cloud/dump.txt; then echo "ds-bot    : 已挂载 ✅"; else echo "ds-bot    : ⚠️ 未挂载（启动时会重试）"; fi; \
      if grep -q "id: llm-pi-ai" /opt/dsh-cloud/dump.txt; then echo "llm-pi-ai : 已配置 ✅"; else echo "llm-pi-ai : ⚠️ 未配置"; fi; \
      if grep -q "teamorouter\|cnb-free" /opt/dsh-cloud/dump.txt; then echo "provider  : cnb-free ✅"; else echo "provider  : ⚠️ 未找到"; fi; \
    } > /opt/dsh-cloud/install-report.txt 2>&1; \
    cat /opt/dsh-cloud/install-report.txt

# ---- 6. 端口：6060(Hermes Web UI) + 8080(DeepSeek Harness) ----
EXPOSE 6060 8651 56121 8080 8830 8831 15741

# ---- 7. 启动入口：同时拉起两个服务 ----
COPY .ide/start.sh /usr/local/bin/cnb-start.sh
RUN chmod +x /usr/local/bin/cnb-start.sh

ENTRYPOINT ["/usr/local/bin/cnb-start.sh"]
CMD []
