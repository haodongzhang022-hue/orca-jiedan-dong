# Claude-Code 云端 NPC：路径A vs 路径B（双模式对比）

> 版本：1.5.0 | 基座：CNB 内置免费 DeepSeek-V4-Flash（有效期至 2026-12-31，每月 1600 核时）
> 仓库：`TJF19770107/orca-jiedan` | 适用：`@claude-code` 云端 NPC 增强部署

---

## 一句话逻辑

> **路径A** = CNB 帮我们封装好的轻量化简化小程序（`npc:go` 内置运行时，开箱即用）；
> **路径B** = 我们自己打包完整原版 Claude-Code CLI 做成自定义镜像，每一次 NPC 任务拉起一个全新容器，原生 MCP/插件/Skill 能力全部保留。

---

## 一、A/B 模式总览

| 维度 | 路径A（默认，已启用） | 路径B（增强，本次落地） |
|------|----------------------|------------------------|
| **运行形态** | CNB 内置 `npc:go` 轻量化运行时 | 自定义 Docker 镜像 + 独立容器实例 |
| **镜像** | 平台默认 `cnbcool/default-npc:latest` | 自定义 `adapters/Dockerfile` 构建 → `claude-code-full:1.5.0` |
| **Claude-Code 能力** | 平台蒸馏/裁剪过，部分原生 MCP/插件丢失 | **完整原版 CLI**，不蒸馏、不裁剪原生 MCP/插件/Skill |
| **任务执行单元** | 内置 Agent，单容器内跑完 | 每次 `@claude-code` 触发 → 拉起独立容器实例，一次任务一容器 |
| **协议适配层** | 无（平台内部处理） | 容器内 `anthropic_to_cnb.py` 监听 `127.0.0.1:8787`，Anthropic→CNB 网关转译 |
| **鉴权/密钥** | 环境变量注入 | **全部环境变量注入，镜像零硬编码密钥** |
| **额度监控** | 无 | 镜像内置 `quota_monitor.py`（80% 告警 / 95% 降档保护） |
| **冷启动速度** | 快（轻量化） | 较慢（镜像体积更大，容器冷启动耗时） |
| **可移植性** | 与 CNB 平台耦合 | 与本地 Docker 使用逻辑完全对齐，可在容器内部署 MCP Server |
| **触发方式** | `@codex` / `@lobster` 等其它角色 | `@claude-code` |

> **切换说明**：本仓库 `.cnb.yml` 中 `claude-code` 角色顶层 key 覆盖 `$` 兜底 ——
> `@claude-code` 自动走路径B，其余角色走路径A，两套模式并存、无需改配置即切换。

---

## 二、架构图

```
用户 @claude-code（Issue / PR 评论）
   │
   ▼
CNB NPC 事件流水线（.cnb.yml → claude-code 角色 → 路径B）
   │  docker: ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.5.0
   ▼
┌─────────────────────────── 自定义镜像容器 ───────────────────────────┐
│  claude/entrypoint.sh（容器入口）                                    │
│    ├─ scripts/quota_monitor.py         额度监控（80%告警/95%降档）   │
│    ├─ anthropic_to_cnb.py              协议适配层                    │
│    │    监听 127.0.0.1:8787（ANTHROPIC_BASE_URL）                   │
│    │    Anthropic Messages → OpenAI Chat Completions 转译            │
│    │    → CNB 内置 AI 网关（免费 DeepSeek-V4-Flash）                 │
│    └─ Claude-Code CLI（完整原版，原生 MCP/插件/Skill 全保留）         │
└─────────────────────────────────────────────────────────────────────┘
   │  鉴权：CNB_TOKEN / ACC_PRODUCT_CONFIG_V2（环境变量注入，零硬编码）
   ▼
结果自动回写 Issue/PR 评论区（闭环）
```

---

## 三、端口与容器内部署说明

### 3.1 端口 `127.0.0.1:8787`

| 项 | 值 |
|----|----|
| 监听地址 | `127.0.0.1:8787`（仅容器内可达，不暴露公网） |
| 协议 | Anthropic Messages API（`/v1/messages`、`/v1/models`） |
| 消费方 | Claude-Code CLI（`ANTHROPIC_BASE_URL=http://127.0.0.1:8787`） |
| 上游 | CNB 内置 AI 网关（从 `ACC_PRODUCT_CONFIG_V2` 自动解析 + `CNB_AI_GATEWAY` 可显式覆盖） |
| 健康检查 | `GET /healthz` → `{"status":"ok","model":...,"gateway":...,"quota":"used/limit"}` |

### 3.2 容器内部署 MCP Server

路径B 容器 = 标准 Docker 镜像，可在镜像内追加 MCP Server 配置（如
`~/.claude.json` / 容器内启动脚本），复用 Claude-Code 原生 MCP 加载机制。

---

## 四、文件清单

| 文件 | 说明 |
|------|------|
| `adapters/Dockerfile` | 路径B 自定义镜像构建定义（完整 Claude-Code CLI + 适配层 + 额度监控 + 入口） |
| `adapters/anthropic_to_cnb.py` | 协议适配层：Anthropic → CNB 内置网关转译（零硬编码密钥） |
| `claude/entrypoint.sh` | 容器入口：额度监控 + 适配层(8787) + Claude-Code CLI 编排 |
| `scripts/quota_monitor.py` | 额度监控（1600 核时/月，80% 告警 / 95% 降档） |
| `.cnb.yml` | 主流水线：路径A（`$` 兜底 `npc:go`）+ 镜像构建 + include |
| `.ci/npc-full.yml` | 路径B 角色流水线（claude-code 顶层 key，自定义镜像容器） |
| `docs/claude_code_cloud_vs_local.md` | 本文档（A/B 对比） |

---

## 五、流水线配置要点

### 5.1 路径B 角色流水线（`.ci/npc-full.yml`）

```yaml
claude-code:
  issue.comment@npc: *npc_task_full_claude
  pull_request.comment@npc: *npc_task_full_claude
```

- 顶层 key `claude-code` 与 `.cnb/settings.yml` 中 `npc.roles[].name` 精确匹配；
- 被 @ 时命中该角色 → 走路径B 自定义镜像容器；
- 未命中角色（如 `@codex`）→ 走 `$` 兜底路径A。

### 5.2 镜像构建/推送（`.cnb.yml` `main.push`）

```bash
docker build -f adapters/Dockerfile -t ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.5.0 .
docker push ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.5.0
```

仅当 `adapters/Dockerfile`、`adapters/anthropic_to_cnb.py`、
`scripts/quota_monitor.py`、`claude/entrypoint.sh` 变更时触发重建（`ifModify`）。

### 5.3 环境变量注入（镜像零硬编码密钥）

| 变量 | 值 | 说明 |
|------|-----|------|
| `CNB_TOKEN` | 流水线自动注入 | 内置网关鉴权 |
| `ACC_PRODUCT_CONFIG_V2` | 平台自动注入 | 自动解析网关地址 + token |
| `CNB_AI_GATEWAY` | 可选 | 显式覆盖内置网关地址 |
| `CNB_MODEL` | `deepseek-v4-flash` | 强制免费基座 |
| `REASONING_EFFORT` | `high` | low/high/max |
| `QUOTA_LIMIT` | `1600` | 每月免费核时 |
| `QUOTA_USED` | 监控更新 | 已用额度 |

---

## 六、优缺点对比

### 路径B（本次落地）取舍

**✅ 优点**
- 与本地 Docker 使用逻辑完全对齐，心智负担低；
- 原生能力完整：MCP Server、插件、Skill 全部保留；
- 可在容器内部署 MCP Server，扩展灵活；
- 一次任务 = 一个独立容器，隔离性好。

**⚠️ 代价**
- 镜像体积更大（含完整 Claude-Code CLI + Node/Python 运行时）；
- 容器冷启动耗时高于路径A 轻量化模式；
- 需维护 Dockerfile / 适配层 / 入口脚本。

### 路径A（默认）取舍

**✅ 优点**：开箱即用、速度快、平台托管零运维。
**⚠️ 代价**：逻辑经蒸馏裁剪，部分原生 MCP/插件能力丢失。

---

## 七、安全红线

- 任何 Token/Key 只放 CNB 流水线「环境变量」或 secrets 仓库，**不提交 git**；
- 镜像**严禁写入任何密钥**，鉴权全部读取容器环境变量；
- 适配层凭据从 `ACC_PRODUCT_CONFIG_V2`（平台自动注入）读取，代码零硬编码；
- `scripts/export_to_github_and_mirror.sh` 打包前防御性过滤
  `.env/*.key/*.pem/secrets.*/.quota_state.json`。

---

## 八、验收核对项

- [ ] `adapters/Dockerfile` 可正常构建自定义镜像，内置完整原版 Claude-Code CLI，无蒸馏裁剪
- [ ] `.cnb.yml` / `.ci/npc-full.yml` 路径B 流水线存在，`claude-code` 角色不依赖内置 `npc:go` 轻量化运行时
- [ ] 触发 `@claude-code`，成功拉起自定义容器，容器内部 `127.0.0.1:8787` 端口正常监听
- [ ] 密钥全部环境变量注入，镜像无硬编码密钥
- [ ] MCP、插件在容器内可正常加载调用（Claude-Code 原生能力）
- [ ] A/B 两套模式完整写入本文档，同步脚手架模板仓库
- [ ] 额度监控 `quota_monitor.py` 正常工作（80% 告警 / 95% 降档）

> 龙虾五步法闭环：本文档已录入 Git；本地 E盘/G盘 镜像、Obsidian 知识库按四化迭代流程归档。
