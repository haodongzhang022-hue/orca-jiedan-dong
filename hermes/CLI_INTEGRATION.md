# Hermes 原生 CLI 接入说明（脚手架 v1.6.0）

> 归属：`orca-jiedan` · 脚手架 v1.6.0 新增能力
> 定位：把 **GitHub 原生 Hermes CLI** 接入 CNB NPC 舰队，作为「大脑层 / 战略调度」执行单元

---

## 一、结论先行：npm 上为什么没有对的包

| 候选 | 结论 | 原因 |
|------|------|------|
| `@hermesai/cli` | ❌ 404 | npm 上不存在该包名 |
| `hermes-cli` (1.0.0) | ❌ 无关 | 是一个「巴西旅行社搜索」CLI，与 AI 编排完全无关 |
| `hermes` (0.4.4) | ❌ 无关 | Segment 的古早聊天机器人脚手架，与 AI 调度无关 |
| **GitHub `NousResearch/hermes-agent`** | ✅ **原生** | 官方仓库，Python 包名 `hermes-agent`，安装后命令行即 `hermes`，与「编排/调度/战略大脑」定位完全一致 |

> 结论：**原生 Hermes CLI = GitHub `NousResearch/hermes-agent`**（⭐226k · MIT · Python 包 `hermes-agent`）。
> 它不是通过 npm 分发的，而是 `curl .../install.sh | bash` 或 `pip install hermes-agent`，命令为 `hermes`。

---

## 二、原生 Hermes CLI 关键信息（调研快照）

| 项 | 值 |
|----|----|
| 官方仓库 | https://github.com/NousResearch/hermes-agent |
| PyPI 包 | `hermes-agent`（当前 0.19.0 / 0.20.0） |
| 安装命令 | `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash`（Linux/macOS/WSL）<br>`iex (irm https://hermes-agent.nousresearch.com/install.ps1)`（Windows 原生 PowerShell）<br>`pip install hermes-agent`（容器内直装） |
| CLI 入口 | `hermes`（TUI 交互） / `hermes model` / `hermes tools` / `hermes gateway` / `hermes cron` / `hermes doctor` |
| 语言 | Python（>=3.11,<3.14） |
| 模型接入 | 任意 OpenAI 兼容端点，`hermes model` 切换；`.env` / `~/.hermes/config.yaml` 配置 |
| 官方容器 | 自带 `Dockerfile` + `docker/docker-compose.yml` |

**为什么「编排/调度」就该用它**：Hermes 原生能力 = 多 Agent 编排、子 Agent 并行、cron 定时调度、
跨平台消息网关（Telegram/Discord/微信类）、技能自进化闭环。这与本仓库 `hermes/` 目录
「大脑层 · 战略调度」的定位完全同构。

---

## 三、本仓库接入方案（CNB NPC 舰队 · 路径B 容器模式）

沿用 claude-code 已验证的 **路径B（自定义镜像容器）** 模式，新增 `hermes` 角色：

```
用户 @hermes（Issue / PR 评论）
   │
   ▼
CNB NPC 事件流水线（.cnb.yml → .ci/hermes.yml 顶层角色 key）
   │  docker: ${CNB_DOCKER_REGISTRY}/${CNB_NPC_SLUG_LOWERCASE}:1.6.0
   ▼
┌─────────────────────────── 自定义镜像容器 ───────────────────────────┐
│  hermes/entrypoint.sh（容器 ENTRYPOINT）                              │
│    ├─ scripts/quota_monitor.py      额度监控（80%告警/95%降档）      │
│    ├─ hermes 原生 CLI（pip install hermes-agent）                    │
│    │    模型指向 CNB 内置免费 DeepSeek-V4-Flash 网关                  │
│    └─ npc:go（平台内置任务，同一容器内执行 AI 任务）                  │
└─────────────────────────────────────────────────────────────────────┘
   │  鉴权：CNB_TOKEN / ACC_PRODUCT_CONFIG_V2（环境变量注入，零硬编码）
   ▼
结果自动回写 Issue/PR 评论区（闭环）
```

### 文件清单（本次新增）

```
hermes/
├─ README.md                    # 既有大脑层说明（保留）
├─ CLI_INTEGRATION.md           # 【新增】原生 CLI 接入说明（本文件）
├─ system_prompt.md             # 【新增】hermes 角色 CNB 云端人设
└─ entrypoint.sh                # 【新增】容器入口（额度监控→hermes CLI 就绪→前台存活）
adapters/
└─ hermes_entry.sh              # 【新增】原生 hermes 安装/启动辅助（Dockerfile 复用）
scripts/
└─ quota_monitor.py             # 既有额度监控（复用）
.ci/
└─ hermes.yml                   # 【新增】hermes 角色路径B流水线（顶层 key）
.cnb/settings.yml               # 【修改】新增 hermes 角色定义
.cnb.yml                        # 【修改】include .ci/hermes.yml；镜像构建流水线改 1.6.0
templates/cnb_npc_path_b_scaffold/  # 【同步】脚手架模板全部更新至 v1.6.0
VERSION.md                      # 【修改】1.5.0 → 1.6.0
scaffold_version                # 【修改】1.2.0 → 1.6.0
```

> ⚠️ 注意：本仓库 `hermes/` 目录为**大脑层目录**（既有 `README.md`），本次新增的是把
> **原生 hermes CLI** 接入 CNB 的集成文件，两者不冲突：原生 CLI 作为大脑层执行引擎，
> 既有目录说明继续作为角色职责文档。

---

## 四、模型基座强制约束

- 与 claude-code 一致：**强制绑定 CNB 内置免费 `deepseek-v4-flash`**（有效期至 2026-12-31，
  每月 1600 核时免费配额）；
- 原生 hermes 的模型端点改写为 CNB 内置 AI 网关（OpenAI 兼容，`ACC_PRODUCT_CONFIG_V2` 自动解析）；
- 严禁 fallback 到任何外部付费模型；
- 密钥零硬编码：`CNB_TOKEN` / `ACC_PRODUCT_CONFIG_V2` 均由 CNB 流水线环境变量注入。

---

## 五、验证方式

1. `@hermes` 触发 → 确认走自定义镜像容器（路径B）；
2. 容器内确认 `hermes --version` 输出原生版本号；
3. 审计日志确认模型 = `deepseek-v4-flash`（CNB 免费基座）；
4. 额度监控脚本正常工作（超限仅降级、不切付费模型）。
