# 路径B：Claude-Code 自定义镜像容器 NPC — 脚手架增强模板（可选）

> 归属：`orca-cnb-project-template` 脚手架 · 可选增强方案
> 版本：1.5.0 | 基座：CNB 内置免费 DeepSeek-V4-Flash
> 用途：把【完整原版 Claude-Code CLI】打包进自定义 Docker 镜像，作为 CNB NPC
>       执行单元；每次 `@claude-code` 触发拉起独立容器，原生 MCP/插件/Skill 全保留。

---

## 一、模板内容（同步清单）

将以下文件同步到脚手架仓库 `orca-cnb-project-template`（或直接复制到新项目）：

| 文件 | 说明 |
|------|------|
| `adapters/Dockerfile` | 路径B 自定义镜像构建定义 |
| `adapters/anthropic_to_cnb.py` | 协议适配层（Anthropic → CNB 网关） |
| `claude/entrypoint.sh` | 容器入口（额度监控 + 适配层 8787 + Claude-Code CLI） |
| `scripts/quota_monitor.py` | 额度监控（80% 告警 / 95% 降档） |
| `.cnb.yml` | 主流水线（路径A `$` + include + 镜像构建） |
| `.ci/npc-full.yml` | 路径B 角色流水线（claude-code 顶层 key） |
| `docs/claude_code_cloud_vs_local.md` | A/B 双模式对比文档 |

## 二、启用步骤

1. 复制上述文件到新项目；
2. 在 `.cnb/settings.yml` 定义 `claude-code` 角色（name 与 `.ci/npc-full.yml` 顶层 key 一致）；
3. 提交并推送 main → 触发镜像构建流水线（`main.push` + `ifModify` 命中 Dockerfile 等文件）；
4. 构建成功后，Issue/PR 评论 `@claude-code` → 自动拉起自定义镜像容器（路径B）；
   `@codex` 等其它角色 → 走 `$` 兜底路径A（npc:go 轻量化）。

## 三、镜像构建命令（亦可手动执行）

```bash
docker build -f adapters/Dockerfile -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.5.0 .
docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:1.5.0
```

> ⚠️ **变量口径**：镜像构建在 `main.push`（非 NPC 事件）执行，`CNB_NPC_SLUG_LOWERCASE` 不注入，
> 必须用 `CNB_REPO_SLUG_LOWERCASE`。NPC 事件侧引用仍用 `CNB_NPC_SLUG_LOWERCASE`，
> 同仓库场景两者相等，指向同一镜像。

> ⭐ **免费基座约束**：镜像/流水线全链路强制绑定 CNB 内置免费 `deepseek-v4-flash`
> （有效期至 2026-12-31，1600核时/月免费配额），`NPC_MODEL` 与 `options.model` 双保险锁定，
> 禁止默认切换其它付费模型；额度超限仅降级 `reasoning_effort`，不切付费模型。

## 四、安全红线

- 镜像严禁写入任何密钥，鉴权全部读取容器环境变量（CNB 流水线注入）；
- 适配层凭据从 `ACC_PRODUCT_CONFIG_V2` 自动解析，代码零硬编码；
- 导出/打包脚本防御性过滤 `.env/*.key/*.pem/secrets.*/.quota_state.json`。

## 五、验收核对

- [x] Dockerfile 可构建，镜像含完整原版 Claude-Code CLI（无蒸馏裁剪）
- [x] `.ci/npc-full.yml` 路径B 流水线存在，`claude-code` 角色使用自定义镜像容器
- [x] 镜像 `ENTRYPOINT` 自动拉起适配层，容器内 `127.0.0.1:8787` 正常监听
- [x] 密钥全环境变量注入，镜像零硬编码
- [x] MCP/插件/Skill 在容器内可正常加载
- [x] 本文档同步至脚手架仓库 `orca-cnb-project-template`（模板目录即同步源）
