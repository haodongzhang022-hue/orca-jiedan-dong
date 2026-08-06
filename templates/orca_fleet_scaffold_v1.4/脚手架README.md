# {project_name} · ORCA 多 Agent 舰队脚手架

> 版本：1.4.0 ｜ 用途：多 Agent 舰队（Codex / Claude Code / Hermes / Maris）统一脚手架

## 一、这是什么

本目录为 ORCA 多 Agent 舰队**标准化脚手架**，让项目开箱即具备：

1. **CNB 云上 NPC**：`@TJF19770107/{repo}(codex)` 与 `@TJF19770107/{repo}(claude-code)` 可直接召唤
2. **本机三 Agent 工作树**：hermes/brain + codex/executor + claude/reviewer
3. **Maris 调度接入**：一键投递任务卡到 `fleet_exchange/incoming/`
4. **自动恢复**：代理端口 15721/15730 自动拉起，Codex/Claude Code 即开即用

## 二、快速使用

```bash
# 1. 初始化三工作树（新项目执行一次）
bash scripts/orca_init_worktrees.sh

# 2. 在每个工作树「添加设置脚本」粘贴
bash ../../scripts/orca_setup_worktree.sh

# 3. 生成 Maris 接入说明
bash scripts/maris_gen_readme.sh

# 4. 一键投递任务（Maris 或手动）
bash scripts/maris_dispatch.sh "任务需求描述"
```

## 三、文件清单

| 文件 | 作用 |
|------|------|
| `.cnb.yml` | CNB NPC 事件绑定（codex / claude-code / `$` 兜底） |
| `.cnb/settings.yml` | NPC 角色定义（Codex=执行 / Claude Code=审核） |
| `.orca/setup.sh` | ORCA 打开项目自动就绪（代理拉起） |
| `CODEX.md` / `CLAUDE.md` | 本机 Codex / Claude Code 会话自动恢复指令 |
| `scripts/orca_setup_worktree.sh` | 工作树环境注入（角色识别） |
| `scripts/orca_project_startup.sh` | 项目自动就绪检查 |
| `scripts/orca_init_worktrees.sh` | 三工作树一键初始化 |
| `scripts/maris_dispatch.sh` | Maris 任务卡投递 |
| `scripts/maris_gen_readme.sh` | 生成 Maris 接入说明 |
| `config/orca/*_system_prompt.md` | 三层 Agent 中文角色提示词 |
| `fleet_exchange/` | 任务卡流转区（incoming→doing→done→results） |

## 四、CNB 平台召唤规则

- 完整格式：`@TJF19770107/{repo}(codex)` / `@TJF19770107/{repo}(claude-code)`
- 简写 `@codex` 不生效（平台按 `仓库路径(角色名)` 匹配）
- 需勾选「替我上班」（仓库开发者及以上权限）
