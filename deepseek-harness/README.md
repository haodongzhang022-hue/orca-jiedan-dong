# DeepSeek Harness · 云端超级 Agent 运行时

> **非 Hermes Studio** — 独立自研的 DeepSeek 超 Agent 编排 harness，云端容器内纯 Python 运行。
> 基座：CNB 内置免费 **DeepSeek-V4-Flash**（MoE 284B/激活13B，免费至 2026-12-31）。
> 定位：企业微信群定制接单 · 规划→委派→执行→汇总 全自动闭环。
>
> 🧭 本目录同时作为 **CNB NPC 角色 `@deepseek-harness`**（路径B 自定义镜像容器）的运行时：
> 在 Issue/PR 评论中 `@deepseek-harness` 即可召唤，与 Hermes/Codex/Claude Code 并列。
> 详见 `docs/DeepSeekHarness_CNB_NPC角色_接入指南.md`。

---

## 一、这是什么

传统上云上复刻用的是 Hermes Studio Web GUI（`ekkoye8888/hermes-web-ui` 镜像，1.49GB 重型）。
本方案改为**轻量、免费、独立**的 DeepSeek Harness：

| 维度 | 旧：Hermes Studio Web GUI | 新：DeepSeek Harness |
|------|--------------------------|----------------------|
| 镜像 | 1.49GB hermes-web-ui | python:3.11-slim（<100MB） |
| 入口 | node dist/server/index.js | python3 harness_proxy.py |
| 模型 | 需手动配 provider | 内置免费 deepseek-v4-flash |
| 接单 | 无 | `/v1/orders` 企微派单建档 |
| 编排 | 单会话聊天 | 规划→委派→执行→汇总 |

## 二、云端部署（点击「云原生开发」自动构建）

- `Dockerfile` 构建 → 容器内置 Harness 网关
- 端口映射 → 浏览器打开 `https://{id}-8080.cnb.run` 即控制台
- 回收机制：10 分钟无操作 / 最长 18h / 凌晨 4-6 点强制回收（出差/兜底可视化）

## 三、文件清单

| 文件 | 作用 |
|------|------|
| `harness_proxy.py` | OpenAI 兼容网关：免费 V4Flash 流式 + 非流式聚合 + 企微接单 |
| `harness_agent.py` | 超 Agent 编排：规划器→子 Agent 委派→记忆→汇总 |
| `web_console.html` | 云端操作控制台（接单 + 编排对话） |
| `harness_skills.json` | 技能索引（design/web/code/research/wechat_order） |
| `harness_mcp_loader.py` | **MCP 统一加载器**：读取 `config/harness_mcp_registry.json` 按需 spawn/kill MCP 子进程，调用双模式插件工具 |
| `harness_plugin_loader.py` | **角色插件加载器**：读取 `config/harness_plugins.json` 按需加载 Hermes/Codex/Claude-Code |
| `config/harness_mcp_registry.json` | MCP 统一注册中心（已登记 `gateway_3080_mcp` 双模式插件） |
| `config/harness_plugins.json` | 角色插件清单（enabled 开关 + 技能绑定） |
| `config/model_layer.json` | 模型层映射（DeepSeek-V4-Flash / GLM-5.2 / Qwen3-VL） |
| `plugins/gateway_3080/gateway_3080.py` | 双模式 MCP 插件安装位置（MCP stdin/stdout + HTTP 兼容） |
| `install_mcp_plugin.sh` | 一键安装 + 集成 + 冒烟验证脚本（源：`scripts/install_mcp_plugin.sh`） |
| `harness_orders/` | 企微派单 → 任务卡（运行时生成） |
| `harness_memory/` | 会话记忆 JSONL（运行时生成） |

## 四、端点一览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查（模型/网关/token前缀） |
| `/v1/models` | GET | 可用免费模型列表 |
| `/v1/chat/completions` | POST | OpenAI 兼容（`stream=true/false` 均支持，内部自动聚合） |
| `/v1/orders` | POST | 企业微信派单 → 任务卡建档 |
| `/v1/orders/list` | GET | 已接订单列表 |
| `/harness` | POST | 编排 Agent：规划→委派→执行→汇总 |
| `/console` | GET | Web 操作控制台 |

## 五、快速本地测试

```bash
# 1. 启动网关（需 CNB_TOKEN 环境变量，云端容器自动注入）
CNB_TOKEN=$CNB_TOKEN python3 harness_proxy.py --port 8080

# 2. 健康检查
curl -s http://127.0.0.1:8080/health

# 3. 免费模型对话（流式）
curl -sN -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}],"stream":true}'

# 4. 企业微信派单 → 任务卡
curl -s -X POST http://127.0.0.1:8080/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"customer":"汤嘉锋","category":"海报","demand":"1080x1080暗黑科技风","spec":"PSD+PNG","settle":"支付宝128"}'

# 5. 编排 Agent
curl -s -X POST http://127.0.0.1:8080/harness \
  -H "Content-Type: application/json" \
  -d '{"session":"s1","task":"设计一张企业宣传单"}'
```

## 六、关键设计：免费网关「仅支持流式」处理

CNB 免费网关硬约束：**非流式请求直接 400（code 11101）**。
Harness 网关内统一处理：

```
客户端 stream=false  → 代理内部强制 stream=true → 拉全量 → 聚合为 OpenAI 完整响应返回
客户端 stream=true   → 代理直通流式 SSE
```

> 实测：非流式聚合与流式均已在此容器内端到端跑通 ✅

## 七、企业微信接单闭环

```
企业微信群派单（截图/文字）
  ▼ /v1/orders 或控制台「接单并建档任务卡」
  ▼ 生成任务卡 harness_orders/{时间}_{客户}_任务卡.md
  ▼ /harness 编排 Agent 规划执行（免费 V4Flash）
  ▼ 交付结论回写控制台 → 对接交付/上传流水线
```

## 八、模型配置指南（免费 DeepSeek-V4-Flash）

DeepSeek Harness **无需手动配置模型**——启动时自动从环境变量解析 CNB 免费网关和鉴权 Token。

### 自动解析的环境变量

| 环境变量 | 作用 | 默认值 |
|---------|------|--------|
| `CNB_TOKEN` | 鉴权 Token | 容器自动注入 |
| `ACC_PRODUCT_CONFIG_V2` | 网关地址自动解析 | 容器自动注入 |
| `CNB_MODEL` | 模型名 | `deepseek-v4-flash` |
| `CNB_AI_GATEWAY` | 显式网关地址（可选） | 自动从配置解析 |
| `HARNESS_PORT` | 监听端口 | `8080` |

### 免费网关地址（手动配置时使用）

```
https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions
```

- **Provider ID**：`cnb-deepseek-v4-flash`
- **协议**：`openai-completions`
- **API Key**：从环境变量 `CNB_TOKEN` 获取
- **Model**：`deepseek-v4-flash`（必须精确，不是 pro）
- **Stream**：必须开启（平台仅支持流式，Harness 网关内置非流式自动聚合）

> 详细配置见 `docs/DeepSeekHarness_CNB免费V4Flash_配置指南.md`

### 验证命令

```bash
# 健康检查
curl -s http://127.0.0.1:8080/health

# 模型列表
curl -s http://127.0.0.1:8080/v1/models

# 对话（流式）
curl -sN -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}],"stream":true}'
```

---

## 九、与 Hermes Web UI 并行共存

本方案与 Hermes Studio Web GUI（`hermes-web-ui` 镜像）**并行存在，互不干扰**：

| 方案 | 端口 | 访问地址 | 镜像体积 |
|------|------|---------|---------|
| Hermes Web UI | 6060 | `https://{id}-6060.cnb.run` | ~1.49GB |
| **DeepSeek Harness** | **8080** | `https://{id}-8080.cnb.run` | **<100MB** |

两个服务由同一个 `.ide/Dockerfile` 构建，`start.sh` 同时拉起，共用 CNB 免费网关。

---

## 十、安全

- 密钥零落盘：`CNB_TOKEN` / `ACC_PRODUCT_CONFIG_V2` 全部来自流水线环境变量注入
- 镜像不含任何明文 Token
- 编排过程全程免费 DeepSeek-V4-Flash，不调用外部付费 API
