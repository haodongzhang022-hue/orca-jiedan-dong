# ORCA 多 Agent 舰队通用项目脚手架 v1.0

> 位置：`E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\`  
> 用途：后续所有 ORCA 多 Agent 项目可直接从此脚手架一键生成。

---

## 脚手架内容

本目录包含一个完整的、可运行的 ORCA 多 Agent 项目模板：

- `config/`：默认配置与模型配置
- `templates/`：标准化输出模板（课程大纲、知识卡片、思维导图、商单交付）
- `scripts/`：一键启动脚本示例
- `hermes/`：大脑层目录（战略调度）
- `codex/`：执行层目录（脚本实现）
- `claude/`：核查层目录（质量审查）
- `docs/`：项目文档、ORCA 搭建指南、五步法案例
- `tests/`：测试样本
- `outputs/` / `logs/` / `backups/`：运行时目录（空）
- `README.md` / `SKILL.md` / `skill_registry.json`：项目说明与技能注册
- `.gitignore` / `.gitattributes`：Git 配置
- `init_orca_fleet.sh`：**一键初始化脚本**

---

## 快速使用

### 方式一：一键初始化新项目（推荐）

```bash
bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/init_orca_fleet.sh" "E:/龙虾AI主控中心/我的AI分身/你的新项目"
```

脚本会自动：
1. 复制完整项目结构到目标目录
2. 初始化 Git 仓库
3. 创建初始提交
4. 创建 `hermes/brain`、`codex/executor`、`claude/reviewer` 三层分支
5. 切回 `master`

### 方式二：手动复制

若需要手工定制，可：
```bash
cp -r "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0" "E:/龙虾AI主控中心/我的AI分身/你的新项目"
# 然后手动 git init 并按需求调整
```

> 注意：手动复制会同时复制本目录的 `.git`（如果存在），建议排除。

---

## ORCA 工作树自动配置（全域模板 #290）

本脚手架已内置 ORCA 多 Agent 工作树的环境注入与角色绑定脚本：

- `scripts/orca_setup_worktree.sh`：工作树环境变量注入（自动识别 hermes/codex/claude）
- `config/orca/setup_one_liner.txt`：贴入 ORCA「添加设置脚本」框的一行命令
- `config/orca/hermes_system_prompt.md` / `codex_system_prompt.md` / `claude_system_prompt.md`：三层 Agent 中文角色提示词
- `docs/ORCA工作树启动配置指南.md`：完整配置图文说明
- `scripts/orca_push_all.sh`：一键推送全部分支到 GitHub（走 gh-proxy）
- `scripts/orca_backup.sh`：非破坏性快照三个工作树到 `backups/`

一键初始化新项目（静默、零交互）：

```bash
bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/init_orca_silent.sh" "你的新项目名"
```

该脚本会自动生成三层分支与三层工作树，并复制上述 ORCA 配置文件。开箱后只需在 ORCA 中每工作树贴一行命令，即可进入中文角色交互状态。

---

## 与本项目的关系

本脚手架由 `企业微信群定制接单项目` 项目沉淀而来，复刻了「黄金黑马策略」的三层 Agent 舰队架构：

- **Hermes（大脑层）**：战略调度、流程编排、需求拆解
- **Codex（执行层）**：代码实现、脚本开发、批量执行
- **Claude（核查层）**：代码审查、质量校验、合规把关

后续任何需要多 Agent 协作的项目，都应优先使用此脚手架生成，确保标准统一。

---

## 版本治理（全域模板 #290 / 龙虾五步法 v2.7）

脚手架自带版本号（`scaffold_version` 文件）。**绝不自动升级旧项目**，只在「项目脚手架版本 ≠ 全域最新脚手架版本」时触发一次交互确认，且日常一致时零打扰。

### 核心规则
- **一致即静默**：`bash scripts/orca_scaffold_check.sh` 比对版本，一致直接通过，不弹窗（防冗余）。
- **不一致即询问（不可跳过、不可静默升级）**：
  - **Y｜增量迭代**：仅补充新参数/技能/配置，已存在文件不覆盖。
  - **N｜版本分叉**：保留旧版，写入 `fork_version.log`，新旧长期并行、互不干扰。
- **保护目录永远不覆盖**：`.env` `database` `conversations` `skills` `logs`（见 `scripts/upgrade_incremental.sh`）。
- **非交互环境**（无 TTY）拒绝静默决策，输出手动命令后退出，绝不偷偷升级。

### 用法
```bash
# 在「已有项目」根目录执行，按版本是否一致决定是否增量迭代 / 分叉
bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/scripts/orca_scaffold_check.sh"

# 或显式执行增量迭代（仅新增缺失文件，跳过保护目录）
bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/scripts/upgrade_incremental.sh" "<项目根路径>"
```

> 新项目用 `init_orca_silent.sh` 创建时直接带最新 `scaffold_version`，故无需治理弹窗。

---

## 维护与更新

当模板结构发生改进时，应同步更新本脚手架，并记录版本：
- `v1.0`：初始版本，基于知识萃取项目沉淀
- `v1.1`：集成 ORCA 工作树自动配置（#290）、推送与快照脚本
- `v1.2`：新增版本治理（一致性校验 + 交互式确认 Y 增量 / N 分叉 + 保护目录），对齐全域模板 #290/#291 与龙虾五步法 v2.7

---

> 最后更新：2026-07-20  
> 维护者：龙虾 AI 主控中心
