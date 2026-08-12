# Claude-Code 云端 NPC 集成（CNB 内置免费 DeepSeek-V4-Flash 基座）

> 版本：1.5.0 | 基座：CNB 内置免费 DeepSeek-V4-Flash（有效期至 2026-12-31）
> 对接：ORCA 链式 `@npc/codex → @npc/claude-code → @CodeBuddy`

## 一、架构

```
用户 @claude-code（Issue/PR 评论）
   │
   ▼
CNB NPC 事件流水线（.cnb.yml → issue.comment@npc）
   │  docker: cnbcool/default-npc:latest
   │  stage: npc:go  options.model = deepseek-v4-flash   ← 基座绑定
   ▼
AI Agent（读取 .cnb/settings.yml 中 claude-code 角色 prompt）
   │  需要写代码/执行命令时使用仓库内 skills + cnb-cli
   ▼
结果自动回写 Issue/PR 评论区（闭环）
```

## 二、两条实现路径（按需二选一）

| 路径 | 说明 | 配置 |
|------|------|------|
| **A（默认，已启用）** | CNB `npc:go` 内置 Agent，`options.model` 直接绑定 `deepseek-v4-flash`，零外部依赖 | `.cnb.yml` 已配置，无需额外镜像 |
| **B（增强）** | 自定义镜像内嵌 Claude-Code CLI + `adapters/anthropic_to_cnb.py` 适配层，把 Anthropic 请求转发 CNB 内置网关 | `adapters/Dockerfile` 构建后改 `docker.image` |

### 路径B 适配层核心逻辑
`adapters/anthropic_to_cnb.py`：
1. 监听 `ANTHROPIC_BASE_URL`（默认 `http://127.0.0.1:8787`），实现 `/v1/messages` 端点；
2. 把 Claude-Code 的 Anthropic Messages 请求转译为 OpenAI Chat Completions；
3. 转发到 CNB 内置 AI 网关（`https://api.cnb.cool/<org>/<repo>/-/ai-ide`，从 `ACC_PRODUCT_CONFIG_V2` 自动解析鉴权）；
4. 强制 `model=deepseek-v4-flash`，支持 `reasoning_effort=low/high/max`；
5. 额度超限（`QUOTA_USED>=QUOTA_LIMIT`）自动 429 降级，绝不 fallback 到外部付费 API。

## 三、密钥安全（硬性约束）
- 任何 Token/Key 只放 CNB 流水线「环境变量」或 secrets 仓库，**不提交 git**；
- 适配层凭据从 `ACC_PRODUCT_CONFIG_V2`（平台自动注入）读取，代码零硬编码；
- `scripts/export_to_github_and_mirror.sh` 打包前防御性过滤 `.env/*.key/*.pem/secrets.*`.

## 四、额度监控与降级
`scripts/quota_monitor.py`：
- 每月 1600 核时免费额度（`QUOTA_LIMIT`）；
- ≥80% 告警（`QUOTA_STATUS=warn`）；
- ≥95% 强制降级（`QUOTA_STATUS=exceeded`，降档为 `deepseek-v4-flash@low`，不切外部付费模型）；
- 输出 `.quota_state.json` 与 `quota.env` 供流水线后续 stage 消费。

## 五、ORCA 链式调用
```text
@npc/codex        → 代码实现（先产出）
@npc/claude-code  → 审计复核（质量把关）
@CodeBuddy        → 平台系统 NPC 兜底/汇总
```
三者均可独立 @ 触发，链式依赖由 Issue 内任务拆分顺序保证。
