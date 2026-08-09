# =============================================================================
# CNB 云原生开发环境 · Hermes Studio Web GUI 云上复刻
# =============================================================================
# 用途：
#   在 CNB「云原生开发」工作区中复刻 Hermes Studio 的 Web 控制台（hermes-web-ui），
#   浏览器直接打开 → 本地桌面版的效果，纯云端算力 + CNB 免费 DeepSeek-V4-Flash 网关。
#
# 原料（官方已验证，2026-08-09 核验）：
#   - 官方镜像 ekkoye8888/hermes-web-ui:0.6.39（约 1.57GB，基于 nousresearch/hermes-agent）
#   - 官方 Dockerfile：ENTRYPOINT node dist/server/index.js，EXPOSE 6060
#   - docker-compose 端口：6060(Web UI) / 8651(预览前端) / 56121(OAuth 回调)
#
# 与 NPC 一次性容器的区别：
#   - NPC 路径B 容器：事件触发即用即毁，无 GUI
#   - 云原生开发工作区：可常驻（有回收机制，见下），WebIDE 端口映射直达 6060
#
# 回收机制（CNB 平台文档确认）：
#   - 10 分钟无操作自动回收 / 最长保持 18 小时 / 凌晨 4-6 点强制回收
#   → 本工作区定位为「出差/兜底可视化」，日常编排仍以本地桌面版为主
#
# 安全红线：
#   - 镜像【严禁写入任何密钥】；模型网关鉴权全部来自环境变量/个人环境变量注入
# =============================================================================

# 官方 Hermes Web UI 镜像（含 Hermes Agent 运行时 + 完整 Web 控制台）
FROM ekkoye8888/hermes-web-ui:0.6.39

# ---- 1. 基础工具链（云原生开发环境常规需求）----
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl wget unzip git git-lfs openssh-server \
       python3 python3-pip procps ripgrep jq \
       fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install || true

# ---- 2. CNB CLI / Skills 运行时（便于在工作区直接操作仓库/NPC）----
RUN npm install -g @cnbcool/cnb-cli skills \
    && npx skills add https://cnb.cool/cnb/skills/cnb-skill.git -g -y || true

# ---- 3. CNB 内置免费网关适配层（Hermes Studio 的 provider 可指向本层，复用仓库已验收协议）----
COPY adapters/anthropic_to_cnb.py /usr/local/bin/anthropic_to_cnb.py
RUN chmod +x /usr/local/bin/anthropic_to_cnb.py

# ---- 4. 端口与监听地址 ----
# Hermes Web UI 需监听 0.0.0.0 才能被 CNB 端口映射 {id}-{{port}}.cnb.run 访问
ENV PORT=6060
ENV BIND_HOST=0.0.0.0
ENV HERMES_HOME=/home/agent/.hermes
ENV HERMES_WEB_UI_MANAGED_GATEWAY=1
ENV HERMES_WEB_UI_XAI_CALLBACK_BIND_HOST=0.0.0.0
ENV HERMES_ALLOW_ROOT_GATEWAY=1
ENV PATH=/opt/hermes/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

EXPOSE 6060 8651 56121

# ---- 5. 启动入口：后台拉起 CNB 免费网关适配层 + 前台跑 Hermes Web UI ----
COPY .ide/start.sh /usr/local/bin/cnb-hermes-studio-start.sh
RUN chmod +x /usr/local/bin/cnb-hermes-studio-start.sh

# 官方镜像入口是 node dist/server/index.js；此处改为包裹脚本以同时拉起适配层
ENTRYPOINT ["/usr/local/bin/cnb-hermes-studio-start.sh"]
CMD []
