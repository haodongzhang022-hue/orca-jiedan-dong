# DeepSeek Harness · CNB 免费 DeepSeek-V4-Flash 模型配置指南

> 目标：让 DeepSeek Harness 能正常调用 CNB 云原生免费 **DeepSeek-V4-Flash** 模型。
> 适用场景：在模型配置界面（如 Hermes Studio / CodeBuddy / 桌面 AI 客户端的 Provider 管理页）中添加 Provider 信息。

---

## 一、免费网关地址（Base URL）

CNB 为每个仓库自动注入免费 AI 网关，地址格式：

```
https://api.cnb.cool/{组织名}/{仓库名}/-/ai/chat/completions
```

本项目实际地址：

```
https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions
```

> ✅ 已验证：流式调用返回 HTTP 200，模型回复正常（`deepseek-v4-flash`，免费 0 积分）。
> ⚠️ 注意：**平台硬约束——仅支持流式（stream=true）**，非流式会返回 400 code 11101。DeepSeek Harness 网关已内置自动聚合处理，客户端无需关心。

---

## 二、模型配置字段填写表（对照你截图里的界面）

下面按界面字段一一对应填写：

| 界面字段 | 填写值 | 说明 |
|---------|--------|------|
| **Provider ID** | `cnb-deepseek-v4-flash` | 任意命名，用于识别，建议英文+数字 |
| **Agent Hub / 预设** | 选「自定义提供方」 | 不选任何预设，直接自定义 |
| **协议类型** | `openai-completions` | OpenAI Chat Completions 协议 |
| **Base URL / API 地址** | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions` | CNB 免费网关 |
| **API Key** | 粘贴 `CNB_TOKEN` 值 | 从环境变量获取（见下方 §三） |
| **Model / 模型名** | `deepseek-v4-flash` | 必须精确填写，不能带前缀 |
| **Stream** | ✅ 开启 | 平台仅支持流式 |
| **Max Tokens** | `4096` 或默认 | 可选 |

---

## 三、API Key（CNB_TOKEN）获取方法

### 方法 1：从环境变量读取（推荐，云端自动注入）

在 CNB 云原生容器 / NPC 容器中，`CNB_TOKEN` 环境变量已自动注入：

```bash
echo "CNB_TOKEN 前缀: ${CNB_TOKEN:0:8}..."
# 输出示例：CNB_TOKEN 前缀: 00367Weh...
```

### 方法 2：从 ACC_PRODUCT_CONFIG_V2 解析（无需手动查找）

`ACC_PRODUCT_CONFIG_V2` 环境变量中包含完整的网关配置和鉴权 token：

```bash
# 在容器内执行
python3 -c "
import json, os
cfg = json.loads(os.environ['ACC_PRODUCT_CONFIG_V2'])
tok = cfg['authentication']['attributes']['token']
print('Token:', tok)
print('Endpoint:', cfg['endpoint'])
"
```

### 方法 3：在 CNB 控制台手动获取

1. 打开 CNB 仓库 → 右上角头像 → **个人设置** → **访问令牌（Access Tokens）**
2. 创建一个新 token，复制即可

> ⚠️ **安全**：Token 只在本地配置文件中使用，**严禁**提交到 git 仓库。

---

## 四、DeepSeek Harness 网关自身的配置方式

DeepSeek Harness（`harness_proxy.py`）**不需要额外配置**，它会自动从环境变量解析网关地址和鉴权：

```
环境变量：
  CNB_TOKEN              → 鉴权 Token（容器自动注入）
  ACC_PRODUCT_CONFIG_V2  → 网关地址自动解析（容器自动注入）
  CNB_MODEL              → 模型名，默认 deepseek-v4-flash
  CNB_AI_GATEWAY         → 显式指定网关地址（可选，默认自动解析）
  HARNESS_PORT           → 监听端口，默认 8080
```

启动方式：

```bash
# 云端容器内（环境变量自动注入）
bash deepseek-harness/run_harness.sh

# 本地调试（需手动设置环境变量）
CNB_TOKEN=你的token python3 deepseek-harness/harness_proxy.py --port 8080
```

---

## 五、验证是否配置成功

### 1. 健康检查

```bash
curl -s http://127.0.0.1:8080/health
# 预期返回：{"status":"ok","model":"deepseek-v4-flash",...}
```

### 2. 模型列表

```bash
curl -s http://127.0.0.1:8080/v1/models
# 预期：deepseek-v4-flash / deepseek-r1 / qwen3-235b-a22b（均免费）
```

### 3. 实际对话（流式）

```bash
curl -sN -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好，测试一下"}],"stream":true}'
```

### 4. 非流式（自动聚合）

```bash
curl -s -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好，测试一下"}],"stream":false}'
```

---

## 六、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `400 code 11101` | 非流式请求 | 改用 `stream:true`，或让 Harness 网关自动聚合 |
| `401 Unauthorized` | Token 错误/未注入 | 检查 `CNB_TOKEN` 是否设置，重新从环境变量获取 |
| `404 model not found` | 模型名拼错 | 必须精确填 `deepseek-v4-flash`（不是 pro） |
| 网关连接失败 | 仓库 slug 不对 | 确认仓库路径 `TJF19770107/orca-jiedan` 正确 |
| Provider 配置后不生效 | 未重启/未新建会话 | 保存配置后**完全退出客户端**再重启，**新建会话** |

---

## 七、与 Hermes Web UI 并行共存

DeepSeek Harness（8080）与 Hermes Web UI（6060）已配置为**并行存在、互相独立**：

| 方案 | 端口 | 访问地址 | 镜像 |
|------|------|---------|------|
| Hermes Web UI | 6060 | `https://{id}-6060.cnb.run` | ekkoye8888/hermes-web-ui:v0.6.39 |
| DeepSeek Harness | 8080 | `https://{id}-8080.cnb.run` | python:3.11-slim（<100MB） |

两个服务由同一个 `.ide/Dockerfile` 构建，`start.sh` 同时拉起，互不干扰。
