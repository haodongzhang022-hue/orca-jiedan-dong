# DeepSeek Harness Desktop · 可复用镜像部署规范

> **模式**：Docker 标准模式——**先构建镜像，再由镜像实例化容器**（与 Hermes / OpenClaw 工程打法一致）。
> **仓库**：`anywhere-labs/deepseek-harness-desktop`（含官方 `deepseek-ai/deepseek-harness` 子模块）。
> **基座**：CNB 内置免费 **DeepSeek-V4-Flash**（MoE 284B/激活13B，免费至 2026-12-31）。

---

## 一、核心逻辑（镜像=安装包，容器=运行实例）

1. **镜像即安装包本体**：把原版 DeepSeek-Harness-Desktop 整套代码、依赖、环境配置一次性固化进镜像，永久存放在镜像仓库。
2. **容器即运行实例**：每次启动都是从镜像「复制一份出来跑」。容器销毁 / 进程退出 / 资源回收，只要镜像还在，一键就能重新生成全新容器，状态隔离。
3. **融合进脚手架**：镜像构建步骤并入 `orca-jiedan` 的 `.cnb.yml` 流水线，跟随项目统一版本迭代、快照备份、同步 CNB 私有仓库。
4. **业务隔离**：`8080` 给原版 Harness 前台界面；旧的企微接单逻辑挪到容器内网 `8081`，外网碰不到，但内部链路照常工作，不打断接单。

---

## 二、端口分配（保持不变）

| 端口 | 用途 | 对外暴露 |
|------|------|---------|
| **8080** | 原版 deepseek-harness-desktop 完整 WebUI（与本地 3080 界面 1:1，全部插件/Agent 编排/Browser-Bridge 完整保留） | ✅ 靠 `docker run -p 8080:8080` 映射 |
| **8081** | 旧自研 harness 整套服务（`/v1/orders` 企微接单、`/harness` 编排接口） | ❌ 容器内网 `127.0.0.1:8081`，不对外 |
| **6060** | Hermes Studio | ✅ 保持不变，不受本构建影响 |

> ⚠️ **安全约束**：官方 Harness **禁止 `--host 0.0.0.0`**（会暴露远程代码执行，`startup.ts` 明确拒绝）。因此容器内 WebUI 以 `127.0.0.1:8080` 运行，对外访问由 Docker 端口映射 `-p 8080:8080` 完成——这正是「镜像→容器」标准模式的正确用法。

---

## 三、镜像命名规范与版本标签规则

### 3.1 命名规范

```
<registry>/<org>/<repo>:<组件>-<版本>
```

| 字段 | 取值 |
|------|------|
| registry | `${CNB_DOCKER_REGISTRY}`（流水线自动注入，如 `docker.cnb.cool`） |
| org | 仓库所属组织/用户（如 `TJF19770107`） |
| repo | 仓库名（如 `orca-jiedan`） |
| 组件前缀 | `dsh-`（DeepSeek Harness Desktop） |
| 版本 | 对齐上游 `2.0.1`（DSH Desktop 版本，见 `upstream.json` / `package.json`） |

**示例完整镜像名**：
```
docker.cnb.cool/TJF19770107/orca-jiedan:dsh-2.0.3
```

### 3.2 版本标签规则

- **标签格式**：`dsh-<desktop版本>`，其中 `<desktop版本>` 取自 `anywhere-labs/deepseek-harness-desktop` 根 `package.json` 的 `version`（当前 `2.0.1`）。
- **跟随上游升级**：上游发新版 → 更新镜像 tag → 重新构建推送，容器升级只需 `docker run` 用新 tag。
- **与既有 NPC 镜像共存**：现有 `:1.6.0` 是 NPC 运行镜像（claude-code/codex/hermes/deepseek-harness 角色），本 `dsh-2.0.3` 是独立可复用 WebUI 镜像，两者互不冲突、可并行存在。

---

## 四、镜像构建命令

在 CNB 流水线中由 `.cnb.yml` 自动执行（`main.push` 触发）。手动构建命令：

```bash
# 在仓库根目录执行（需 Docker + buildx）
DOCKER_REGISTRY=docker.cnb.cool
REPO_SLUG=TJF19770107/orca-jiedan
TAG=dsh-2.0.3

docker build \
  -f deploy/dsh-desktop/Dockerfile \
  -t ${DOCKER_REGISTRY}/${REPO_SLUG}:${TAG} \
  .

# 推送制品库
docker push ${DOCKER_REGISTRY}/${REPO_SLUG}:${TAG}
```

> 流水线内实际使用 `${CNB_DOCKER_REGISTRY}` / `${CNB_REPO_SLUG_LOWERCASE}` 环境变量，无需手动指定。

---

## 五、从镜像启动容器（完整命令）

### 5.1 标准启动（对外暴露 8080 + 内网 8081）

```bash
IMG=docker.cnb.cool/TJF19770107/orca-jiedan:dsh-2.0.3

docker run -d \
  --name dsh-desktop \
  -p 8080:8080 \
  -e CNB_TOKEN="${CNB_TOKEN}" \
  -e CNB_AI_GATEWAY="${CNB_AI_GATEWAY:-https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions}" \
  -e CNB_MODEL="deepseek-v4-flash" \
  -e DSH_WEB_PORT=8080 \
  -e HARNESS_PORT=8081 \
  --restart unless-stopped \
  "${IMG}"
```

| 环境变量 | 作用 |
|---------|------|
| `CNB_TOKEN` | CNB 网关鉴权 Token（必填，运行时注入，镜像零硬编码） |
| `CNB_AI_GATEWAY` | CNB 免费网关地址（默认自动生成该仓库的网关 URL） |
| `CNB_MODEL` | 模型名（默认 `deepseek-v4-flash`，CNB 内置免费） |
| `DSH_WEB_PORT` | 原版 WebUI 监听端口（默认 `8080`） |
| `HARNESS_PORT` | 自研 harness 监听端口（默认 `8081`） |

### 5.2 仅内网自研 harness（不暴露 8080）

```bash
docker run -d \
  --name dsh-harness-internal \
  --network none \
  -e CNB_TOKEN="${CNB_TOKEN}" \
  -e CNB_AI_GATEWAY="${CNB_AI_GATEWAY}" \
  "${IMG}" \
  sh -c 'DSH_WEB_PORT=8080 HARNESS_PORT=8081 /usr/local/bin/dsh-entrypoint.sh'
```

---

## 六、容器重建操作步骤（镜像存在 → 一键重建）

> **关键**：镜像持久化在制品库，容器随时可销毁重建，业务不丢。

```bash
# 1. 停止并删除旧容器（镜像仍在，数据可持久化卷另行挂载）
docker stop dsh-desktop && docker rm dsh-desktop

# 2. （可选）确保本地有最新镜像
docker pull docker.cnb.cool/TJF19770107/orca-jiedan:dsh-2.0.3

# 3. 从镜像重新实例化一个全新容器（见 5.1 完整命令）
#    容器重建后状态隔离、干净启动，接单链路 / 编排能力自动恢复

# 4. 验证 8080 WebUI 可达 + V4Flash 模型正常（见第七节）
curl -s http://127.0.0.1:8080/
```

---

## 七、验证命令（2 条 curl）

### ① 校验 8080 原版 WebUI 服务可达

```bash
curl -s -o /dev/null -w "HTTP %{http_code} · %{time_total}s\n" http://127.0.0.1:8080/
# 期望：HTTP 200 或 302（Harness WebUI 首页可访问，含完整插件/Agent 编排界面）
```

### ② 校验原版 Harness 内部调用 CNB 的 DeepSeek-V4-Flash 模型正常返回

> 走容器内原版 WebUI 网关链路，验证 provider（`cnb-deepseek-v4-flash`）已正确对接 CNB 免费网关。

```bash
curl -s -X POST http://127.0.0.1:8080/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"请回复'OK'两个字符"}],"stream":false}'
# 期望：返回含 "content":"OK" 的 JSON（证明 V4Flash 经 CNB 免费网关正常响应）
```

> 注：官方 Harness 通过其内部 `/api/*` 网关路由转发模型请求，实际端点以容器内 `dsh web` 打印的 URL 为准；也可在 WebUI「设置 → 模型」中选择 `cnb-deepseek-v4-flash` 发起会话验证。

---

## 七·A、双模式 MCP 插件安装与集成（gateway_3080）

`gateway_3080.py` 已升级为**统一可安装 MCP 插件（双模式架构）**，并安装进 DeepSeek Harness，随镜像内置。

### 安装路径

| 项 | 路径 |
|---|---|
| 插件源文件 | `deploy/dsh-desktop/gateway_3080.py` |
| 插件安装位置（harness 内） | `deepseek-harness/plugins/gateway_3080/gateway_3080.py` |
| MCP 统一加载器 | `deepseek-harness/harness_mcp_loader.py` |
| 角色插件加载器 | `deepseek-harness/harness_plugin_loader.py` |
| MCP 注册中心 | `deepseek-harness/config/harness_mcp_registry.json`（已登记 `gateway_3080_mcp` 服务） |
| 角色插件清单 | `deepseek-harness/config/harness_plugins.json` |
| 模型层映射 | `deepseek-harness/config/model_layer.json` |
| 一键安装/集成脚本 | `scripts/install_mcp_plugin.sh` |

### 两种模式

| 模式 | 启动参数 | 协议 | 适用 |
|---|---|---|---|
| **模式一 标准 MCP** | 无参数（默认） | MCP stdin/stdout | Codex / Hermes / DeepSeek-Harness 作为插件加载 |
| **模式二 HTTP 兼容** | `--http --port 3080` | OpenAI `/v1` | 老工具表单填 `base_url=http://127.0.0.1:3080` |

### 一键安装与集成（镜像内已内置，也可手动跑）

```bash
bash scripts/install_mcp_plugin.sh   # 安装 + 语法校验 + 注册中心校验 + 冒烟验证 health
```

### 调用示例（免费 DeepSeek-V4-Flash）

```bash
# 模式一 MCP：对话
python3 deepseek-harness/harness_mcp_loader.py --tool chat_completions \
  --args '{"messages":[{"role":"user","content":"你好"}],"model":"deepseek-v4-flash"}' --mode mcp

# 模式一 MCP：健康自检
python3 deepseek-harness/harness_mcp_loader.py --tool health --mode mcp

# 模式二 HTTP：对话
python3 deepseek-harness/harness_mcp_loader.py --tool chat_completions \
  --args '{"messages":[{"role":"user","content":"你好"}],"model":"deepseek-v4-flash"}' --mode http

# 角色插件清单
python3 deepseek-harness/harness_plugin_loader.py --list
```

### 已验证（本仓库云端容器内）

- ✅ 模式一 MCP：`health` + `chat_completions` 均返回免费模型结果
- ✅ 模式二 HTTP：`/health`、`/v1/models`、`/v1/chat/completions` 均正常
- ✅ 全部走 CNB 免费 `deepseek-v4-flash`，密钥零明文（仅读 `CNB_TOKEN` 环境变量）

---

## 八、文件清单

| 文件 | 作用 |
|------|------|
| `deploy/dsh-desktop/Dockerfile` | 专门构建 deepseek-harness-desktop 可复用镜像 |
| `deploy/dsh-desktop/entrypoint.sh` | 容器启动：生成 provider 配置 + 拉起 8080 原版 WebUI + 8081 内网自研 harness |
| `.cnb.yml` | 脚手架：把镜像构建纳入项目流水线（`main.push` 触发） |

---

## 九、安全红线

- **零硬编码密钥**：`CNB_TOKEN` / `CNB_AI_GATEWAY` 全部来自容器环境变量注入，镜像内无任何明文 Token。
- **不调用外部公网 API**：模型默认指向 CNB 内部 `deepseek-v4-flash`，读取容器环境变量拿网关地址。
- **不修改原版源码**：不修改 harness-desktop 前端源码、不裁剪插件组件；放弃改造本地 `web_console.html` 的旧方案。
