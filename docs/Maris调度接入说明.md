# Maris 调度接入说明 · orca-jiedan

> 本文档说明 Maris（调度端）以及其他协作者如何调用本项目脚手架、向舰队投递任务并协作。
> 更新：2026-08-06

---

## 一、脚手架在哪？怎么调用？

项目脚手架模板位于仓库内：

```
templates/orca_fleet_scaffold_v1.4/
├── .cnb.yml                  # CNB NPC 事件绑定（codex / claude-code / $ 兜底）
├── .cnb/settings.yml         # NPC 角色定义
├── .orca/setup.sh            # ORCA 打开项目自动就绪（代理拉起）
├── CODEX.md / CLAUDE.md      # 本机 Codex / Claude Code 会话自动恢复指令
├── scaffold_version          # 脚手架版本号（当前 1.4.0）
├── 脚手架README.md           # 脚手架说明
├── fleet_exchange/           # 任务卡流转区模板
└── scripts/
    ├── apply_scaffold.sh     # ★ 一键批量部署脚本（给其他项目用）
    ├── orca_setup_worktree.sh    # 工作树环境注入
    ├── orca_project_startup.sh   # 项目自动就绪检查
    ├── orca_init_worktrees.sh    # 三工作树一键初始化
    ├── maris_dispatch.sh         # Maris 任务卡投递
    └── maris_gen_readme.sh       # 生成 Maris 接入说明
```

### 用法一：给新项目/其他仓库批量部署脚手架

```bash
# 在本机 Git Bash（或 ORCA 终端），从任意克隆了本仓库的目录执行：
bash templates/orca_fleet_scaffold_v1.4/scripts/apply_scaffold.sh \
    "E:/龙虾AI主控中心/我的AI分身/你的新项目"

# 一次部署多个项目：
bash templates/orca_fleet_scaffold_v1.4/scripts/apply_scaffold.sh \
    "E:/.../项目A" "E:/.../项目B"

# 部署脚本内置的默认项目列表：
bash templates/orca_fleet_scaffold_v1.4/scripts/apply_scaffold.sh --all
```

> 脚本是幂等的：已存在的文件一律 `[SKIP]` 跳过，不会覆盖已有配置。

### 用法二：新项目一键初始化三工作树 + Maris 接入

```bash
cd <项目根目录>

# 1. 初始化三工作树（hermes/brain + codex/executor + claude/reviewer）
bash scripts/orca_init_worktrees.sh

# 2. 在每个工作树「添加设置脚本」框粘贴一行命令
bash ../../scripts/orca_setup_worktree.sh

# 3. 生成 Maris 接入说明（本仓库已有 docs/Maris调度接入说明.md）
bash scripts/maris_gen_readme.sh

# 4. 提交并推送
git add -A && git commit -m "feat: 配置 CNB NPC + ORCA 多 Agent 脚手架"
git push
```

---

## 二、Maris 如何投递任务？（任务卡协议）

**本仓库已内置 `scripts/maris_dispatch.sh`**，Maris / 任意调度端 / 协作者都可一键把任务写进 `fleet_exchange/incoming/`，舰队自动接单：

```bash
# 在项目根目录执行
bash scripts/maris_dispatch.sh "朋友圈餐饮海报，露营烤肉套餐198元"
bash scripts/maris_dispatch.sh --type poster --desc "开业大吉" --price 300
```

脚本会生成带 frontmatter 的任务卡（`task_id / from: maris / to: fleet / pipeline / type / price`）到 `fleet_exchange/incoming/TASK-YYYYMMDD-HHMMSS.md`，流转路径：

```
incoming → accepted → doing → done → results → logs
```

| 目录 | 含义 |
|------|------|
| `incoming/` | 新任务卡（Maris/手动投递入口） |
| `accepted/` | 已被 Agent 领取 |
| `doing/` | 执行中（Codex 产出初稿） |
| `done/` | 已完成（待审核/已审核） |
| `results/` | 最终交付物 |
| `logs/` | 处理日志 |

---

## 三、其他人在 CNB 平台如何召唤 NPC？

在 CNB 仓库的 Issue / PR 评论区 @（**必须用完整格式，简写不生效**）：

```text
@TJF19770107/orca-jiedan(codex) 帮我写一个 Python 脚本...
@TJF19770107/orca-jiedan(claude-code) 请审计上面的代码
@CodeBuddy 做最终审查
```

> 记得勾选评论区下方「替我上班」（需仓库开发者及以上权限）。

各角色分工：

| 层 | 角色 | 分支 | 职责 |
|----|------|------|------|
| 大脑 | Hermes | hermes/brain | 需求拆解、任务编排 |
| 执行 | Codex | codex/executor | 代码实现、物料生成 |
| 审核 | Claude | claude/reviewer | 质量校验、合规把关 |
| 调度 | Maris | -（任务卡） | 接单群→舰队任务卡投递 |
| 兜底 | CodeBuddy | -（CNB 云上） | 平台默认 NPC，执行/审查/汇总 |

---

## 四、协作总览图

```
Maris(调度) ──投递任务卡──▶ fleet_exchange/incoming/
                              │
                              ▼
            CodeBuddy / Codex / Claude Code（CNB 云上 NPC / 本机工作树）
                              │
                              ▼
            fleet_exchange/done → results/（交付物）
```

---

## 五、版本治理提示

- 当前脚手架版本：`1.4.0`（`scaffold_version`）
- 一致即静默：`bash scripts/orca_scaffold_check.sh` 版本一致直接通过，不弹窗
- 不一致才询问：Y=增量迭代（只补新增文件，不覆盖），N=版本分叉（新旧并行）
