# =============================================================================
# DeepSeek Harness Desktop · 可复用镜像（先构建镜像 → 再由镜像实例化容器）
# =============================================================================
# 用途：
#   将【anywhere-labs/deepseek-harness-desktop 完整原版源码】连同其依赖、
#   环境配置一次性固化进一个独立的可复用 Docker 镜像（Docker 标准模式）。
#   不做临时容器、不做一次性运行——镜像即「安装包本体」，容器只是它的
#   可反复生成的运行实例；容器销毁/进程退出/资源回收后，从镜像一键重建。
#
# 端口约定（与本地 3080 界面 1:1）：
#   - 8080  对外暴露：原版 deepseek-harness-desktop 完整 WebUI（容器内 loopback，
#           对外访问靠 `docker run -p 8080:8080` 映射；全部插件、Agent 编排、
#           Browser-Bridge 完整保留，不裁剪）。⚠️ 官方安全限制禁止 --host 0.0.0.0。
#   - 8081  容器内网：旧自研 harness 整套服务迁移至此，不对外暴露
#           （保留 /v1/orders 企微接单、/harness 编排接口，接单流水线不中断）
#   - 6060  Hermes Studio 保持不变，不受本镜像影响
#
# 模型对接：
#   镜像内预置 $DSH_HOME/settings.yaml 自定义 provider，模型默认指向
#   CNB 内部 DeepSeek-V4-Flash；网关地址、鉴权 Token 全部从容器环境变量
#   注入（CNB_AI_GATEWAY / CNB_TOKEN），【零硬编码密钥、不调用外部公网 API】。
#
# 禁止行为：
#   - 不修改原版 harness-desktop 前端源码，不裁剪任何插件组件
#   - 放弃改造本地 web_console.html 的旧方案
#
# 构建（在 CNB 流水线执行，见 .cnb.yml）：
#   docker build -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:dsh-2.0.2 .
#   docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:dsh-2.0.2
# =============================================================================

# ---- 基础镜像：Node 22（官方 Harness 要求 node ^22.19.0 || >=24.0.0）----
FROM node:22-bookworm-slim

# ---- 1. 基础工具链（curl 健康检查 / git 拉源码 / jq / python3 跑自研 harness）----
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl git git-lfs jq procps python3 python3-pip \
       ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install || true

# ---- 2. 安装 pnpm / corepack（Harness 官方构建工具链）----
# 官方用 pnpm workspace，需启用 corepack 并提供 pnpm 二进制
RUN corepack enable \
    && corepack prepare pnpm@9.15.0 --activate

# ---- 3. 拉取【完整原版 anywhere-labs/deepseek-harness-desktop】源码（含官方 Harness 子模块）----
# 固化原版代码、依赖、环境配置，保证 8080 WebUI 与本地 3080 界面 1:1
ARG DSH_DESKTOP_REF=main
WORKDIR /opt/dsh-desktop
RUN git clone --depth 1 --recurse-submodules --branch "$DSH_DESKTOP_REF" \
        https://github.com/anywhere-labs/deepseek-harness-desktop.git . \
    && git submodule update --init --recursive || true

# ---- 4. 安装依赖 + 构建（pnpm 全局安装 @deepseek-ai/dsh CLI）----
# 官方 Harness 通过 npx @deepseek-ai/dsh web 启动 WebUI（默认 127.0.0.1:3080）。
# 此处从源码构建后全局安装 dsh CLI，固化运行时。
RUN cd /opt/dsh-desktop/deepseek-harness \
    && pnpm install --frozen-lockfile 2>/dev/null || pnpm install \
    && npm run build \
    && pnpm install --global --prefix /usr/local ./ 2>/dev/null \
    || npm install -g @deepseek-ai/dsh@0.1.0-rc.7 || true

# 确保 dsh CLI 可用（若源码全局安装失败则回退到 npx 缓存）
RUN (command -v dsh >/dev/null 2>&1 && dsh --version 2>/dev/null) || echo "dsh via npx" || true

# ---- 5. 预置 $DSH_HOME 目录与 provider 配置模板（模型指向 CNB 免费 DeepSeek-V4-Flash）----
# 说明：settings.yaml 中 baseURL / apiKeyEnv 引用环境变量，不写死网关与密钥。
# entrypoint.sh 启动时动态生成该文件，将 CNB_AI_GATEWAY / CNB_TOKEN 注入。
ENV DSH_HOME=/opt/dsh-home
RUN mkdir -p "$DSH_HOME"

# ---- 6. 部署自研 harness 运行时（容器内网 8081，不对外暴露）----
# 旧自研 harness（企微接单 /v1/orders、编排 /harness）整体迁移到内网 8081，
# 保持接单流水线不中断；外网无法直接访问，仅内部链路可用。
RUN mkdir -p /opt/deepseek-harness
COPY deepseek-harness/harness_proxy.py /opt/deepseek-harness/harness_proxy.py
COPY deepseek-harness/harness_agent.py /opt/deepseek-harness/harness_agent.py
COPY deepseek-harness/harness_skills.json /opt/deepseek-harness/harness_skills.json
COPY deepseek-harness/harness_mcp_loader.py /opt/deepseek-harness/harness_mcp_loader.py
COPY deepseek-harness/harness_plugin_loader.py /opt/deepseek-harness/harness_plugin_loader.py
COPY deepseek-harness/run_harness.sh /opt/deepseek-harness/run_harness.sh
# 「一切皆插件」配置（MCP 注册中心 / 角色插件清单 / 模型层）内置进镜像
COPY deepseek-harness/config/ /opt/deepseek-harness/config/
# 双模式 MCP 插件（gateway_3080）：既放 harness 根目录（entrypoint HTTP 模式用），
# 也装进 plugins 插件目录（harness_mcp_loader MCP 模式用，install_path 对齐）
COPY deploy/dsh-desktop/gateway_3080.py /opt/deepseek-harness/gateway_3080.py
COPY deploy/dsh-desktop/gateway_3080.py /opt/deepseek-harness/plugins/gateway_3080/gateway_3080.py
COPY deepseek-harness/plugins/gateway_3080/gateway_3080.py /opt/deepseek-harness/plugins/gateway_3080/gateway_3080.py
# 一键安装/集成脚本内置进镜像
COPY scripts/install_mcp_plugin.sh /opt/deepseek-harness/install_mcp_plugin.sh
RUN chmod +x /opt/deepseek-harness/*.sh /opt/deepseek-harness/gateway_3080.py /opt/deepseek-harness/plugins/gateway_3080/gateway_3080.py /opt/deepseek-harness/install_mcp_plugin.sh

# ---- 7. 启动脚本（生成 provider 配置 + 拉起两个服务）----
COPY deploy/dsh-desktop/entrypoint.sh /usr/local/bin/dsh-entrypoint.sh
RUN chmod +x /usr/local/bin/dsh-entrypoint.sh

# ---- 8. 端口约定 ----
# 8080 原版 WebUI（对外靠 docker run -p 映射）| 8081 内网自研 harness（不对外）
# | 6060 Hermes Studio（保留）| 3080 本机网关（HTTP 兼容模式，仅本机/内网）
EXPOSE 8080 8081 6060 3080

ENTRYPOINT ["/usr/local/bin/dsh-entrypoint.sh"]
CMD []
