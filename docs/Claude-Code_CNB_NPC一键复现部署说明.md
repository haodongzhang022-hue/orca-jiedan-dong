# Claude-Code CNB 云端 NPC — 一键复现部署包

> 目标：把 Claude-Code 封装为 CNB 可 `@` 调用的自定义 NPC，
> 底层基座强制绑定 **CNB 内置免费 DeepSeek-V4-Flash**（不调用外部付费 API，不触发本地 Ollama）。
> 仓库：`TJF19770107/orca-jiedan`（CNB）· 镜像推送目标 `TJF19770107/claude-code-cnb-npc`（GitHub 私有）

## 文件清单

| 文件 | 说明 |
|------|------|
| `.cnb/settings.yml` | NPC 角色定义：`claude-code`、`codex`（人设 + 硬性约束） |
| `.cnb.yml` | NPC 事件流水线：`issue.comment@npc` / `pull_request.comment@npc` 触发，`npc:go` 显式绑定 `deepseek-v4-flash` |
| `adapters/anthropic_to_cnb.py` | Claude-Code Anthropic 协议 → CNB 内置网关转发层（密钥零硬编码） |
| `adapters/Dockerfile` | 路径B 自定义 NPC 运行镜像（内嵌适配层 + cnb-cli/skills） |
| `scripts/quota_monitor.py` | 免费额度监控 + 降级保护（1600 核时/月，80% 告警 / 95% 降级） |
| `scripts/export_to_github_and_mirror.sh` | 导出可发布源码包 + E盘/G盘 镜像清单生成 |

## 部署三步走

### 1. CNB 仓库已就绪（本仓库）
`.cnb/settings.yml` + `.cnb.yml` 已提交到默认分支 `main`，NPC 角色即时生效。

### 2. 推送 GitHub 私有仓库（含适配层，无密钥）
```bash
cd artifacts/claude-code-cnb-npc
git init && git add . && git commit -m "Claude-Code CNB NPC 适配层 (DeepSeek-V4-Flash)"
git remote add origin git@github.com:TJF19770107/claude-code-cnb-npc.git
git push -u origin main
```

### 3. 在 CNB 流水线配置「环境变量」注入（不在代码存放 key）
| 变量 | 值 | 说明 |
|------|-----|------|
| `CNB_AI_GATEWAY` | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai-ide` | 内置网关（也可自动解析） |
| `CNB_MODEL` | `deepseek-v4-flash` | 强制基座 |
| `REASONING_EFFORT` | `high` | 推理档位 low/high/max |
| `QUOTA_LIMIT` | `1600` | 每月免费核时 |
| `QUOTA_USED` | `0` | 已用额度（监控更新） |

## 使用
在 Issue / PR 评论：
```text
@claude-code 请审计 xxx 文件并输出修复建议
@TJF19770107/orca-jiedan(claude-code) 帮我完成 xxx 任务
@codex 实现 xxx 功能
```
Agent 自动运行并回写评论，底层走 CNB 免费 DeepSeek-V4-Flash。

## 安全红线
- 本包不含任何密钥明文；`.gitignore` 已排除 `.env`/`*.key`/`*.pem`/`secrets.*`。
- 密钥一律 CNB 流水线环境变量注入。
- 额度监控脚本输出 `.quota_state.json`（已 .gitignore 排除）。
