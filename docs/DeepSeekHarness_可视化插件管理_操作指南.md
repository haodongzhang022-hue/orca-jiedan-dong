# DeepSeek-Harness 可视化插件管理 · 操作指南

> 作者：Hermes（大脑层·全域模板调度）｜日期：2026-08-18｜关联：#43
> 涉及：`deepseek-harness/harness_proxy.py`（新增 /plugins 可视化 API）· `deepseek-harness/web_console.html`（插件面板 UI）
> 背景：`gateway_3080_mcp` 已写入 `config/harness_mcp_registry.json`，命令行 `harness_mcp_loader.py` 运行正常，但 Web 图形界面【插件列表】搜不到自定义 MCP 条目。本方案补齐前端插件列表渲染，并支持可视化启用/禁用、状态标签、模型清单展示。

---

## 1. 需求清单（对照）

| # | 需求 | 实现位置 | 状态 |
|---|------|---------|------|
| 1 | 前端插件列表渲染，读取 `config/harness_mcp_registry.json` 的 `services`，把 `gateway_3080_mcp` 显示在 UI 插件列表 | `web_console.html` 新增「🧩 MCP 插件管理」面板 + `harness_proxy.py` `/plugins` 接口 | ✅ |
| 2 | UI 支持启用/禁用 `gateway_3080_mcp` 双模式 MCP 插件 | 插件面板开关 `POST /plugins/<name>/toggle` | ✅ |
| 3 | UI 增加小状态标签：当前 MCP 运行模式（mcp/http）、健康状态 | 插件卡片顶部标签（双模式/模式/健康） | ✅ |
| 4 | UI 插件详情页展示当前生效模型列表 deepseek-v4-flash、z-ai/glm-5.2 | 插件「详情/模型」展开区 | ✅ |
| 5 | 补充可视化操作文档 | 本文档 | ✅ |
| 6 | 保持向后兼容，不改动现有命令行调用链路 | 只新增端点，`harness_mcp_loader.py`/`harness_plugin_loader.py` 零改动 | ✅ |

---

## 2. 访问入口

浏览器打开 DeepSeek-Harness 控制台：

- 云端容器：`https://{id}-8080.cnb.run`
- 本地：`http://127.0.0.1:8080`

在控制台最下方新增 **「🧩 MCP 插件管理」** 面板，自动读取注册中心 `services` 并渲染全部插件/服务。

---

## 3. 图形界面操作步骤

### 3.1 查看插件列表

打开控制台后，插件面板默认加载：

- **插件名**：如 `双模式 MCP 插件 · 本机 3080 网关（gateway_3080.py）`
- **启用/禁用** 状态标签（蓝色=启用 / 灰=禁用）
- **双模式** 标签（仅 `gateway_3080_mcp`）
- **运行模式** 标签（`mcp` 或 `http`）
- **健康状态** 标签（正常=绿 / 不可达=红 / 禁用=灰）
- 右上角 **开关**（toggle）用于启用/禁用

### 3.2 启用/禁用插件

点插件右上角的滑块开关：

1. 开关从灰变蓝 = **启用**（写入注册中心 `enabled: true`，同步更新 `spawn_kill_matrix`）
2. 开关从蓝变灰 = **禁用**（写入注册中心 `enabled: false`）

> 切换即时写回 `config/harness_mcp_registry.json`，与命令行 `harness_mcp_loader.py` 读取的是同一份文件，**天然向后兼容**，命令行链路零改动。

### 3.3 查看插件详情 + 生效模型

点插件行内「详情/模型」按钮，展开详情区：

- **生效模型清单**：`deepseek-v4-flash`（CNB 免费）、`z-ai/glm-5.2`（NVIDIA）
- **健康详情**：MCP 模式显示「stdin/stdout」；HTTP 模式显示「HTTP 端口是否可达」
- **工具列表**：`chat_completions / get_models / health`

---

## 4. 新增后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/plugins` | GET | 列出注册中心全部服务/插件（含模式、健康、模型） |
| `/plugins/<name>` | GET | 单个插件详情 |
| `/plugins/<name>/toggle` | POST | body `{"enabled": true|false}`，写回注册中心 |

### 4.1 curl 验证

```bash
# 列表
curl -s http://127.0.0.1:8080/plugins

# 启用 gateway_3080_mcp
curl -s -X POST http://127.0.0.1:8080/plugins/gateway_3080_mcp/toggle \
  -H "Content-Type: application/json" -d '{"enabled":true}'

# 禁用
curl -s -X POST http://127.0.0.1:8080/plugins/gateway_3080_mcp/toggle \
  -H "Content-Type: application/json" -d '{"enabled":false}'
```

---

## 5. 如何查看日志确认实际调用模型

### 5.1 后端服务日志

控制台启动时输出：

```
[DeepSeek-Harness] 免费模型基座: deepseek-v4-flash
[DeepSeek-Harness] CNB 免费网关: https://api.cnb.cool/.../ai/chat/completions
```

### 5.2 gateway_3080 MCP 插件运行日志

启动 `harness_mcp_loader.py` 或插件自身时，向 stderr 输出：

- MCP 模式：
  ```
  [GW3080] MCP 模式已启动（stdin/stdout）· 供 Codex/Hermes-Still/DeepSeek-Harness 加载
  [GW3080] 出站目标: https://api.cnb.cool/...  · 可用工具: chat_completions/get_models/health
  ```
- HTTP 模式：
  ```
  [GW3080] HTTP 网关兼容模式已启动（出站）: http://127.0.0.1:3080
  [GW3080] 出站目标: https://api.cnb.cool/...
  ```

### 5.3 确认实际调用模型的三种方法

1. **`get_models` 工具**：返回 `deepseek-v4-flash`、`z-ai/glm-5.2` 两个模型（与 UI 详情页一致）。
2. **`curl /v1/models`**（HTTP 模式）：
   ```bash
   curl -s http://127.0.0.1:3080/v1/models
   # → {"object":"list","data":[{"id":"deepseek-v4-flash",...},{"id":"z-ai/glm-5.2",...}]}
   ```
3. **对话响应体 `model` 字段**：发起一次 `chat/completions`，返回 JSON 里的 `model` 字段即实际调用模型名。

### 5.4 出站连通性/鉴权排查

插件 `/health` 返回：

```json
{"ok": true, "mode": "outbound", "model": "deepseek-v4-flash",
 "gateway": "https://api.cnb.cool/...", "token_present": true,
 "token_prefix": "cnb_****..."}
```

- `token_present: false` → 检查 `CNB_TOKEN` 环境变量是否注入
- 看门狗自愈：异常自动重试（指数退避），stderr 打 `[GW3080][看门狗]` 日志

---

## 6. 架构与向后兼容说明

```
浏览器 Web 控制台
  └─ fetch /plugins（新增）
        ▼
harness_proxy.py（新增可视化 API，只读/写注册中心）
        │
        ├─ config/harness_mcp_registry.json  ← 唯一状态源
        │
        └─ harness_mcp_loader.py（命令行，零改动，读同一份注册中心）
```

- **唯一状态源**：`config/harness_mcp_registry.json`
- **命令行链路**：`harness_mcp_loader.py` / `harness_plugin_loader.py` **未做任何改动**
- **只新增端点**：`/plugins`（GET）、`/plugins/<name>`（GET）、`/plugins/<name>/toggle`（POST）
- **前端**：`web_console.html` 仅新增「MCP 插件管理」面板，原接单/编排功能保持不变

> 安全性：本可视化接口仅暴露在 DeepSeek-Harness 容器内网/控制台，不涉及任何密钥明文；密钥仍只从环境变量 `CNB_TOKEN` 读取。

---

## 7. 文件变更清单

| 文件 | 变更 |
|------|------|
| `deepseek-harness/harness_proxy.py` | 新增 `MCP_REGISTRY` 常量、`_read_registry/_write_registry/_gateway_mode/_http_health/_plugin_health/_list_plugins/_toggle_plugin`，新增 `/plugins` 端点（GET 列表/详情、POST toggle） |
| `deepseek-harness/web_console.html` | 新增「🧩 MCP 插件管理」面板 + 插件卡片渲染 + 状态标签 + 开关切换 + 详情/模型展开 |
| `docs/DeepSeekHarness_可视化插件管理_操作指南.md` | 本文档 |
