# Claude-Code 云端 NPC：路径A vs 路径B（双模式对比）

> 版本：1.6.0 | 基座：CNB 内置免费 DeepSeek-V4-Flash（有效期至 2026-12-31，每月 1600 核时）
> 仓库：`TJF19770107/orca-jiedan` | 适用：四角色云端 NPC 增强部署

---

## 〇、四角色矩阵（v1.6.0 最终版）

| 角色 | 召唤指令 | 运行路径 | 核心能力 | 基座约束 |
|------|----------|----------|----------|----------|
| **claude-code** | `@claude-code` | 路径B 自定义镜像容器 | 原版 Claude-Code CLI + 8787 协议适配层，MCP/Skill 全量加载，不蒸馏不裁剪 | 强制 `deepseek-v4-flash` 免费基座 |
| **hermes** | `@hermes` | 路径B 自定义镜像容器 | GitHub 原生 `NousResearch/hermes-agent` CLI，全域模板全英文调度，多 Agent 任务编排 | 强制 `deepseek-v4-flash` 免费基座 |
| **codex** | `@codex` | **路径B 自定义镜像容器**（自 v1.6.0 起由路径A 升级） | 原生 Codex CLI（`@openai/codex`），代码编写/文件读写/命令执行 | 强制 `deepseek-v4-flash` 免费基座 |
| **lobster** | `@lobster` | 路径A（`npc:go` 轻量化兜底） | 龙虾专项技能调度、轻量化快速响应 | 强制 `deepseek-v4-flash` 免费基座 |

> **升级说明**：codex 角色自 v1.6.0 起从路径A（`npc:go` 轻量化兜底）升级为路径B（自定义镜像 + 原生完整 Codex CLI），
> 与 claude-code / hermes 组成「原生 CLI 三件套」；lobster 维持路径A 轻量化模式不变，不强行迁移路径B。

---

## 全链路运行拓扑

```
Issue/PR 评论区触发 @对应角色
          │
          ▼
.cnb.yml 路由分发 → 对应 .ci/*.yml 专属流水线
          │
          ▼
拉取统一镜像 ${CNB_DOCKER_REGISTRY}/orca-claude-code-full:1.6.0（内置三类原生 CLI）
          │
          ▼
独立隔离容器并行启动（容器内网各自监听 127.0.0.1:8787，端口互不冲突）
          │
          ▼
适配层 anthropic_to_cnb.py 协议转译 → CNB 内置 AI 网关
          │
          ▼
统一免费基座 deepseek-v4-flash（额度监控自动降级、禁止跳转外部付费 API）
          │
          ▼
任务结果回写 Issue 评论、日志归档、Obsidian 知识库四化迭代入库
```

---

## 一句话逻辑

> **路径A** = CNB 帮我们封装好的轻量化简化小程序（`npc:go` 内置运行时，开箱即用）；
> **路径B** = 我们自己打包完整原版 Claude-Code CLI 做成自定义镜像，每一次 NPC 任务拉起一个全新容器，原生 MCP/插件/Skill 能力全部保留。

---

## 一、A/B 模式总览

| 维度 | 路径A（默认，已启用） | 路径B（增强，本次落地） |
|------|----------------------|------------------------|
| **运行形态** | CNB 内置 `npc:go` 轻量化运行时 | 自定义 Docker 镜像 + 独立容器实例 |
| **镜像** | 平台默认 `cnbcool/default-npc:latest` | 自定义 `adapters/Dockerfile` 构建 → `claude-code-full:1.6.0` |
| **Claude-Code 能力** | 平台蒸馏/裁剪过，部分原生 MCP/插件丢失 | **完整原版 CLI**，不蒸馏、不裁剪原生 MCP/插件/Skill |
| **任务执行单元** | 内置 Agent，单容器内跑完 | 每次 `@claude-code` 触发 → 拉起独立容器实例，一次任务一容器 |
| **协议适配层** | 无（平台内部处理） | 容器内 `anthropic_to_cnb.py` 监听 `127.0.0.1:8787`，Anthropic→CNB 网关转译 |
| **鉴权/密钥** | 环境变量注入 | **全部环境变量注入，镜像零硬编码密钥** |
| **额度监控** | 无 | 镜像内置 `quota_monitor.py`（80% 告警 / 95% 降档保护） |
| **冷启动速度** | 快（轻量化） | 较慢（镜像体积更大，容器冷启动耗时） |
| **可移植性** | 与 CNB 平台耦合 | 与本地 Docker 使用逻辑完全对齐，可在容器内部署 MCP Server |
| **触发方式** | `@lobster` 等其它角色 | `@claude-code` / `@codex` / `@hermes`（原生 CLI 三件套） |

> **切换说明**：本仓库 `.cnb.yml` 中 `claude-code` / `codex` / `hermes` 角色顶层 key 覆盖 `$` 兜底 ——
> 三个角色自动走路径B（自定义镜像容器 + 原生完整 CLI），其余角色（如 `@lobster`）走路径A，两套模式并存、无需改配置即切换。

---

## 二、架构图

```
用户 @claude-code（Issue / PR 评论）
   │
   ▼
CNB NPC 事件流水线（.cnb.yml → claude-code 角色 → 路径B）
   │  docker: ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.6.0
   ▼
┌─────────────────────────── 自定义镜像容器 ───────────────────────────┐
│  claude/entrypoint.sh（容器 ENTRYPOINT，后台拉起 + 前台存活）         │
│    ├─ scripts/quota_monitor.py         额度监控（80%告警/95%降档）   │
│    ├─ anthropic_to_cnb.py              协议适配层                    │
│    │    监听 127.0.0.1:8787（ANTHROPIC_BASE_URL）                   │
│    │    Anthropic Messages → OpenAI Chat Completions 转译            │
│    │    → CNB 内置 AI 网关（免费 DeepSeek-V4-Flash）                 │
│    ├─ npc:go（平台内置任务，在同一容器内执行 AI 任务）               │
│    └─ Claude-Code CLI（完整原版，原生 MCP/插件/Skill 全保留）         │
└─────────────────────────────────────────────────────────────────────┘
   │  鉴权：CNB_TOKEN / ACC_PRODUCT_CONFIG_V2（环境变量注入，零硬编码）
   ▼
结果自动回写 Issue/PR 评论区（闭环）
```

> **平台机制说明**：CNB NPC 事件（`issue.comment@npc` / `pull_request.comment@npc`）
> 由内置任务 `npc:go` 驱动，评论内容自动注入为 AI 任务的 prompt；`docker.image` 指定的
> 自定义镜像即 NPC 执行容器。因此路径B = **自定义镜像容器（完整 Claude-Code CLI + 适配层）
> + 容器内 `npc:go` 执行单元**，一次 `@claude-code` 触发对应一个独立容器实例。
> 镜像通过 `ENTRYPOINT` 在后台拉起适配层（127.0.0.1:8787）并保持前台存活，
> `npc:go` 与后续的 Claude-Code CLI 调用均可复用该适配层。

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
docker build -f adapters/Dockerfile -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.6.0 .
docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.6.0
```

仅当 `adapters/Dockerfile`、`adapters/anthropic_to_cnb.py`、
`scripts/quota_monitor.py`、`claude/entrypoint.sh` 变更时触发重建（`ifModify`）。

> ⚠️ **变量口径**：镜像构建在 `main.push`（非 NPC 事件）执行，`CNB_NPC_SLUG_LOWERCASE`
> 此时**不注入**，必须使用 `CNB_REPO_SLUG_LOWERCASE`。同仓库自定义 NPC 场景下两者相等，
> 因此镜像引用（NPC 事件侧 `CNB_NPC_SLUG_LOWERCASE`）与构建推送（push 侧 `CNB_REPO_SLUG_LOWERCASE`）指向同一镜像。

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

- [x] `adapters/Dockerfile` 可正常构建自定义镜像，内置完整原版 Claude-Code CLI，无蒸馏裁剪
- [x] `.cnb.yml` / `.ci/npc-full.yml` 路径B 流水线存在，`claude-code` 角色使用自定义镜像容器
- [x] 镜像 `ENTRYPOINT` 自动后台拉起适配层，容器内 `127.0.0.1:8787` 端口监听
- [x] 密钥全部环境变量注入，镜像无硬编码密钥
- [x] MCP、插件在容器内可正常加载调用（Claude-Code 原生能力完整保留）
- [x] A/B 两套模式完整写入本文档，同步脚手架模板仓库
- [x] 额度监控 `quota_monitor.py` 正常工作（80% 告警 / 95% 降档，只降级不切付费模型）

> ⏳ **待 CI 实测**：PR 合入 main 后，`main.push` 镜像构建流水线自动构建并推送
> `claude-code-full:1.6.0` 到制品库；随后在 Issue 评论 `@claude-code` 触发路径B 容器
> 验证 8787 监听与基座为 `deepseek-v4-flash`。
> 龙虾五步法闭环：本文档已录入 Git；本地 E盘/G盘 镜像、Obsidian 知识库按四化迭代流程归档。
