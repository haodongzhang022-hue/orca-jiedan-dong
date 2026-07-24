# 龙虾五步法案例 — ORCA 多 Agent 舰队搭建

> 项目名称：企业微信群定制接单项目  
> 案例类型：基础设施 / 多 Agent 协作架构  
> 记录时间：2026-07-19  
> 对应技能：`lobster_task_standard_workflow_v2.7` + `龙虾全域官方模板 v3.112` 协议 #289

---

## 一、需求背景

为让「企业微信群定制接单项目」项目具备企业级交付能力，需要复刻「黄金黑马策略」的 ORCA 多 Agent 舰队架构：
- 大脑层（Hermes）负责战略调度
- 执行层（Codex）负责代码实现
- 核查层（Claude）负责质量把关

通过 Git 分支与工作树实现三层隔离，使多 Agent 可在 ORCA 中独立协作，最终沉淀为通用项目脚手架。

---

## 二、龙虾五步法执行记录

### Step 1 精准备份
- 确认项目根目录：`E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\`
- 确认项目已存在且 ORCA 已绑定该目录（截图显示 `master [主要]`）
- 没有修改原始课程资源，仅对项目结构进行操作
- 保留 Git 提交历史，后续操作均可回滚

### Step 2 根因诊断
- 当前分支为 `master`，尚未提交
- 无远程仓库，需要后续配置 GitHub
- 目标：建立三层分支 + 专属目录 + ORCA 工作树指南 + 通用脚手架
- 环境限制：rsync 不可用，改用 cp 复制；`.git` 目录需排除

### Step 3 无命令不执行（按规范执行）
1. 在 `master` 分支上创建初始提交：`feat: init knowledge extraction project`
2. 创建三层分支：
   - `hermes/brain`：创建 `hermes/flow_control/`、`hermes/orchestration/`、`hermes/knowledge_sync/`
   - `codex/executor`：创建 `codex/scripts/`、`codex/tools/`、`codex/batch_tasks/`
   - `claude/reviewer`：创建 `claude/review_checks/`、`claude/validation/`、`claude/compliance/`
3. 每个分支添加 `README.md`，明确职责与协作规则
4. 合并到 `master`：
   ```bash
   git checkout master
   git merge --no-ff hermes/brain codex/executor claude/reviewer
   git tag -a "v1.0.0-orca-fleet" -m "ORCA 多 Agent 舰队架构 V1.0.0"
   ```
5. 编写 `docs/ORCA多Agent工作树搭建指南.md`
6. 沉淀通用脚手架到 `E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\`
7. 编写 `init_orca_fleet.sh` 一键初始化脚本并自测

### Step 4 验证修复
- 检查三层分支存在：`git branch -a` 显示 `hermes/brain`、`codex/executor`、`claude/reviewer`
- 检查各层目录已合并到 master：`ls hermes/ codex/ claude/` 均存在
- 检查 ORCA 工作树指南完整可读
- 测试脚手架脚本：在临时目录中成功生成新项目，包含 24 个文件、4 个分支
- 检查 git 标签：`git tag -n` 显示 `v1.0.0-orca-fleet`

### Step 5 沉淀归档
- 在 `lobster_task_standard_workflow_v2.7/SKILL.md` 中新增「ORCA 多 Agent 舰队搭建子流程」
- 在「龙虾全域官方模板-最终版.md」中新增协议 #289「ORCA 多 Agent 舰队搭建规范」
- 编写本案例文件：`docs/龙虾五步法案例-ORCA多Agent舰队搭建.md`
- 待 GitHub 远程配置后，推送所有分支与标签

---

## 三、关键产出

| 产出物 | 路径 | 状态 |
|--------|------|------|
| 三层分支 | `hermes/brain`、`codex/executor`、`claude/reviewer` | ✅ 已创建 |
| 各层目录与 README | `hermes/`、`codex/`、`claude/` | ✅ 已合并到 master |
| Git 标签 | `v1.0.0-orca-fleet` | ✅ 已打标 |
| ORCA 工作树指南 | `docs/ORCA多Agent工作树搭建指南.md` | ✅ 已编写 |
| 通用项目脚手架 | `E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\` | ✅ 已生成 |
| 一键初始化脚本 | `init_orca_fleet.sh` | ✅ 已自测 |
| 五步法技能更新 | `lobster_task_standard_workflow_v2.7/SKILL.md` | ✅ 已追加 |
| 全域模板更新 | `龙虾全域官方模板-最终版.md` | ✅ 已追加 |
| 本案例文档 | `docs/龙虾五步法案例-ORCA多Agent舰队搭建.md` | ✅ 已编写 |

---

## 四、后续行动

1. 在 ORCA 中按 `docs/ORCA多Agent工作树搭建指南.md` 添加三个工作树。
2. 配置 GitHub 私有仓库并推送：
   ```bash
   cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
   git remote add origin https://github.com/TJF19770107/side-project-knowledge-base.git
   git push -u origin master hermes/brain codex/executor claude/reviewer --tags
   ```
3. 后续新项目使用脚手架一键生成：
   ```bash
   bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/init_orca_fleet.sh" \
       "E:/龙虾AI主控中心/我的AI分身/新项目"
   ```

---

## 五、经验总结

- **主分支名沿用 ORCA 绑定**：本项目 ORCA 已绑定 `master`，因此保留 `master` 作为主分支，避免工作区 confusion。
- **分支目录不重复**：三层分支基于同一历史，仅在各自目录下新增内容，合并时自然聚合。
- **脚手架排除运行时数据**：复制时排除 `.git/`、`outputs/`、`logs/`、`backups/`，确保新项目干净。
- **一键脚本自测**：在临时目录中跑通脚本，确认能生成完整结构与三层分支。
- **文档先行**：先写 `docs/ORCA多Agent工作树搭建指南.md`，再沉淀技能与模板，确保流程可复现。
