---
name: hermes-studio-cnb
description: 一键接入 CNB 免费基座（需求④）：把本地 Hermes Studio 桌面编排的模型端点指向 CNB 免费网关 deepseek-v4-flash，0 成本。同时配套云端云原生开发环境的 Web GUI 复刻与群聊痕迹墙联动。触发词：一键接入CNB、免费基座、CNB免费网关、deepseek-v4-flash、Hermes Studio 接CNB、零成本算力。
version: 1.0.0
agent_created: true
category: 龙虾舰队流水线 · 云原生NPC技能库
triggers:
  - "一键接入CNB"
  - "免费基座"
  - "CNB免费网关"
  - "deepseek-v4-flash"
  - "Hermes Studio 接CNB"
  - "零成本算力"
  - "云上复刻"
  - "群聊痕迹墙"
inputs:
  - "本地 ~/.hermes/config.yaml（Hermes Studio provider 配置）"
  - "CNB 访问令牌（本机环境变量 CNB_TOKEN，不入库）"
outputs:
  - "Hermes Studio 模型端点切到 CNB 免费网关 deepseek-v4-flash"
  - "云端云原生开发环境 Hermes Studio Web GUI（.ide/Dockerfile + vscode 事件）"
  - "群聊痕迹墙双向可见（msgbus/inbox/echo_wall/）"
capabilities:
  - "自动注册 cnb-deepseek-v4-flash provider 到 Hermes Studio"
  - "一键生成 CNB 免费网关 base_url + 环境变量注入规范"
  - "云上复刻 Hermes Studio Web GUI（浏览器打开）"
  - "群聊痕迹墙：云端 NPC 交流写痕迹，桌面端可见"
limitations:
  - "Token 只放本机环境变量，绝不写仓库/日志"
  - "量化/闲鱼两仓凭证严禁上云"
  - "云端实时群聊不可行（平台无常驻容器），用痕迹墙替代"
entry_script: "scripts/one_click_cnb_gateway.sh"
project_root: "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
base_model: "CNB内置免费DeepSeek-V4-Flash"
---

# Hermes Studio 一键接入 CNB 免费基座

## 一句话

```
本地 Hermes Studio 桌面编排（可视化调度入口，在你 Windows 本机）
   └─模型端点指向→ CNB 免费网关 deepseek-v4-flash（免费算力，0 成本）
```

## 执行入口（Windows 本机 / MARVIS）

```powershell
# 方式A：脚本一键（自动写 ~/.hermes/config.yaml provider + 环境变量指引）
bash scripts/one_click_cnb_gateway.sh

# 方式B：手动（Hermes Studio 模型管理界面添加 provider）
#   name      = cnb-deepseek-v4-flash
#   base_url  = https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions
#   api_key   = %CNB_TOKEN%（本机环境变量，不落盘）
#   model     = deepseek-v4-flash
```

## 网关信息（OpenAI Chat Completions 兼容）

| 项 | 值 |
|---|---|
| base_url | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions` |
| model | `deepseek-v4-flash` |
| 免费至 | 2026-12-31 |
| 额度 | 云原生开发 1600 核时/月 + AI Credits 500/月（CNB 官方定价文档） |
| 鉴权 | `Bearer <CNB_TOKEN>`，Token 只存本机环境变量 |

## 云端配套（本技能三件套）

1. **云上复刻 Web GUI**：仓库点「云原生开发」→ `.ide/Dockerfile` 构建 → 浏览器打开
   `https://{id}-6060.cnb.run`（Hermes Studio Web 控制台，出差/兜底用）
2. **群聊痕迹墙**：云端 NPC 交流写入 `msgbus/inbox/echo_wall/`，桌面版文件浏览器可见
3. **免费网关适配层**：`adapters/anthropic_to_cnb.py`（云端/容器内 127.0.0.1:8787）

## 安全红线

- Token/Key 仅本机环境变量，禁止入仓库/日志/痕迹
- 量化/闲鱼两仓仅本机执行，凭证严禁上云
- 端口铁律 15721/15730/8642/4567/11434 禁改

## 验收

- [ ] `hermes-studio model list` 可选 `cnb-deepseek-v4-flash` 且一次调用 200
- [ ] 云原生开发按钮能拉起 Hermes Web UI（6060 映射可访问）
- [ ] 云端 NPC 任务后 `msgbus/inbox/echo_wall/` 有痕迹
