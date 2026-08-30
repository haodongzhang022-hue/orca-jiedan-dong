---
title: 2026-08-30_1234四化迭代·Codex成本优化·TeamoRouter免费模型接入
summary: 针对Codex Desktop高额扣费（glm-5.3 6.5折）问题，执行1234方法论与四化迭代，将TeamoRouter免费/0.01折模型（deepseek-v4-flash-free、glm-5.3-flash-free等）接入Codex，沉淀标准化配置与自动化切换脚本。
tags: [1234, 四化迭代, Codex, TeamoRouter, 成本优化, 免费模型, AI分身]
source: IMA 001aa1cd10007026 + 乐享 d3e2fdd1f0864e8a895407746a223771 + 本地.config.toml/.grok/config.toml
distilled_by: 龙虾五步法V3.6 + 全域模板#321 + 仓颉蒸馏 + 赛博书屋v1.5
distilled_at: 2026-08-30
version: v1.0
---

# 2026-08-30 · 1234四化迭代 · Codex成本优化 · TeamoRouter免费模型接入

> **执行人格**：汤小龙（已加载 SOUL.md v3.0）
> **问题**：TeamoRouter账单显示 Codex Desktop 大量调用 `glm-5.3`（6.5折），而同源 `glm-5.3-flash-free` 仅 0.01折；`deepseek-v4-flash-free` 免费可用但未出现在 Codex 模型列表。
> **目标**：把 TeamoRouter 免费/0.01折模型全部接入 Codex，默认走最低价模型，可手动切换回付费模型。

---

## 一、1234 总览执行

| 键 | 名称 | 本次执行内容 | 状态 |
|---|---|---|---|
| **1** | **一人一公司** | 触发「运维/成本优化」角色；由 WorkBuddy（汤小龙）执行，Hermes 规划、Claude Code 审核（按需） | ✅ |
| **2** | **马斯克×巴菲特** | 第一性原理：Codex扣费高→根因是请求走了高价模型；能力圈：只改配置不改代理架构，不碰 CC-Switch 复杂路由 | ✅ |
| **3** | **三载体×三引擎** | 载体：五步法 + 全域模板 + 项目脚手架；引擎：WorkBuddy 执行配置修改 + Codex CLI 实测 | ✅ |
| **4** | **四化×四大库** | 四化沉淀成本优化 SOP；四大库：仓颉蒸馏（配置模板）+ 全域模板（协议登记）+ 五步法（流程）+ 赛博书屋（知识回流） | ✅ |

---

## 二、问题诊断（五步法 Step2）

### 2.1 链路现状

```
Codex Desktop / Codex CLI
 → C:\Users\Administrator\.codex\config.toml
   → model_provider = "custom"
   → base_url = http://127.0.0.1:15721/v1  （CC-Switch，仅配了 MiMo）
   → model = "z-ai/glm-5.2"
 → CC-Switch 日志显示 fallback 到 15721 自身，形成回环或走 MiMo
 → TeamoRouter 账单出现 glm-5.3（6.5折）
```

### 2.2 根因

- `.codex/config.toml` 的 custom provider 指向本地 15721，未直连 TeamoRouter。
- CC-Switch 的 `fs-db/vendors.json` 只注册了 MiMo，没有 TeamoRouter；`routes.json` 把所有请求映射到 `mimo-v2.5-pro`。
- `.grok/config.toml` 已有很多 `ocx-teamo-*` 模型，但缺少 `glm-5.3-flash-free`，且 OpenCodex 服务（10100）未启动，这些模型对 Codex Desktop 不可见。

### 2.3 TeamoRouter 可用免费/低价模型（实测）

| 模型 | 协议 | 折扣 | Codex 直连 |
|---|---|---|---|
| `deepseek-v4-flash-free` | Responses | 免费 | ✅ 实测通过 |
| `deepseek-v4-pro-free` | Chat Completions | 免费 | ⚠️ 需 Chat Completions |
| `glm-5.3-flash-free` | Chat Completions | 0.01折 | ⚠️ 需 Chat Completions |
| `gpt-5.4-fast` 等 `-fast` | Responses | 0.01折 | ✅ 已配置在 .grok |

---

## 三、修复动作（五步法 Step3-4）

### 3.1 备份

- `C:\Users\Administrator\.codex\config.toml.bak.20260830_teamo`
- `C:\Users\Administrator\.grok\config.toml.bak.20260830_teamo`

### 3.2 修改 `.codex/config.toml`（主修复）

```toml
model_provider = "custom"
model = "deepseek-v4-flash-free"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers]
[model_providers.custom]
name = "teamorouter"
wire_api = "responses"
requires_openai_auth = true
base_url = "https://teamorouter.cn/v1"
api_key = "sk-teamo-..."   # 本地明文，同现有 GitHub token/cookie 处理方式
```

### 3.3 补充 `.grok/config.toml`（Codex++ Grok 配置）

新增：

```toml
[model.ocx-teamo-glm-5-3-flash-free]
model = "teamo/glm-5.3-flash-free"
base_url = "http://127.0.0.1:10100/v1"
api_backend = "chat_completions"
api_key = "opencodex-loopback"
name = "OCX teamo/glm-5.3-flash-free [0.01折]"
extra_headers = { "x-opencodex-grok" = "1" }
```

### 3.4 重启验证

- kill 旧 Codex/Codex++ 进程 → 启动 `G:\CodexPlusPlus-1.2.56\codex-plus-plus-manager.exe`
- Codex CLI 实测：`codex exec --model deepseek-v4-flash-free "只回答两个字：正常"`
- 结果：返回 **正常**，tokens used 817，配置生效。

---

## 四、四化迭代沉淀

### 4.1 标准化

- **默认模型规则**：零成本任务默认 `deepseek-v4-flash-free`；付费模型仅用于明确需要高质量输出的任务。
- **配置备份命名**：`config.toml.bak.YYYYMMDD_场景`（例：`.20260830_teamo`）
- **密钥存放**：本地 `config.toml` 可明文（与现有 GitHub token/cookie 同标准）；同步产物必须脱敏。

### 4.2 模块化

- **成本优化配置包**：`configs/codex_teamorouter_free_models/` 包含：
  - `config.toml.teamorouter`（主配置）
  - `config.toml.ccswitch`（原 CC-Switch 配置，回滚用）
  - `grok_config_snippet.toml`（Codex++ Grok 模型片段）
- **切换脚本**：`switch_codex_provider.bat` / `.sh`（TeamoRouter ↔ CC-Switch）

### 4.3 自动化

- **一键切换脚本**：`scripts/switch_codex_model.bat <model>`，自动备份当前配置、修改默认模型、重启 Codex++。
- **每日成本巡检**：从 TeamoRouter 控制台读取前一日消费，若高价模型占比 > 20% 自动告警。
- **默认模型守卫**：Codex 启动时校验 `model` 是否以 `-free` 或 `-fast` 结尾，否则弹窗提醒。

### 4.4 智能化

- **任务分级路由**：简单问答/代码审查 → `deepseek-v4-flash-free`；复杂架构设计 → `gpt-5.5`/`claude-sonnet-5`（付费）；一键切换。
- **消费监控**：TeamoRouter 账单自动解析，识别异常高价调用并回灌画像（“成本红线”）。

---

## 五、Gap 与下一步

| 优先级 | 事项 | 验收标准 |
|---|---|---|
| P0 | 用户确认 Codex Desktop 模型下拉框出现 `deepseek-v4-flash-free` | 截图验证 |
| P0 | 下一笔 Codex 调用走 TeamoRouter 免费模型 | TeamoRouter 账单出现 `deepseek-v4-flash-free` |
| P1 | 编写 `switch_codex_model.bat` 一键切换脚本 | 可切换默认模型并重启 |
| P1 | 补全 `.grok/config.toml` 中其他 0.01折模型（已大部分存在） | Grok 配置页显示完整 |
| P2 | 修复 CC-Switch TeamoRouter  vendor 注册（可选） | CC-Switch 可替代直连方案 |
| P2 | 每日成本巡检脚本 | 自动输出前一日高价模型占比 |

---

## 六、红线与回滚

- **回滚**：若 TeamoRouter 直连出现 401/429/503，立即恢复备份 `config.toml.bak.20260830_teamo`。
- **不改动**：`wire_api` 保持 `responses`；未改 CC-Switch 端口；未改 `~/.codex/config.toml` 的 MCP 配置。
- **成本监控**：未来 24h 内观察 TeamoRouter 账单，确认无 `glm-5.3` 高价调用来自 Codex Desktop。

---

## 七、执行后记（实时进化3问）

1. **新偏好/决策模式**：汤哥对成本极度敏感，未来任何 Codex/AI 工具配置变更默认先评估免费/低价模型。
2. **新技能/踩坑**：Codex CLI `exec` 子命令可用于非交互式验证模型配置；`--model` 参数可强制指定模型，即使下拉框未显示。
3. **差距变化**：成本优化能力 +1；对 TeamoRouter/CC-Switch/Codex++ 三层链路理解加深。

---

*汤小龙 · 2026-08-30 · 成本优先，万法皆空，因果不空。*
