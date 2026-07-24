# ORCA 多 Agent 工作树可视化搭建指南

> 项目：`企业微信群定制接单项目`  
> 适用架构：大脑层（Hermes）- 执行层（Codex）- 核查层（Claude）三层舰队
> 版本：v1.0.0

---

## 1. 在 ORCA 中打开项目

1. 启动 ORCA，进入 **工作区（Workspace）** 视图。
2. 选择「打开项目」或「添加项目」。
3. 路径选择：
   ```
   E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\
   ```
4. 确认 ORCA 识别到 Git 仓库，主分支为 `master`（与当前 ORCA 项目绑定一致）。

---

## 2. 添加三个独立工作树

每个 Agent 层对应一个 Git 分支，并在 ORCA 中作为独立工作树打开，实现并行隔离协作。

### 2.1 Hermes 大脑层工作树

1. 在项目根节点右键 → **添加工作树（Add Worktree）**。
2. 选择或输入：
   - 分支：`hermes/brain`
   - 工作树路径：`E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\hermes`
   - 显示名称：`Hermes · 大脑层`
3. ORCA 左侧项目栏会出现新的工作树入口。

### 2.2 Codex 执行层工作树

1. 再次右键项目根节点 → **添加工作树**。 
2. 选择或输入：
   - 分支：`codex/executor`
   - 工作树路径：`E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\codex`
   - 显示名称：`Codex · 执行层`

### 2.3 Claude 核查层工作树

1. 右键项目根节点 → **添加工作树**。 
2. 选择或输入：
   - 分支：`claude/reviewer`
   - 工作树路径：`E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\claude`
   - 显示名称：`Claude · 核查层`

---

## 3. 配置多 Agent 分工规则

| 工作树 | 默认打开目录 | 负责 Agent | 核心职责 |
|--------|-------------|-----------|----------|
| `hermes/` | `hermes/flow_control/` | Hermes | 流程编排、需求拆解、任务分配、知识库联动 |
| `codex/` | `codex/scripts/` | Codex | 脚本开发、工具实现、批量任务执行、数据处理 |
| `claude/` | `claude/review_checks/` | Claude | 代码审查、输出校验、边界测试、合规审核 |

> 提示：在 ORCA 中可以同时打开三个窗口/标签页，分别锁定对应工作树，避免操作串层。

---

## 4. 多 Agent 协作流程（标准 SOP）

```mermaid
graph LR
    A[需求输入] --> H[Hermes 大脑层<br/>需求拆解 & 流程编排]
    H --> C[Codex 执行层<br/>脚本开发 & 批量执行]
    C --> Cl[Claude 核查层<br/>审查 & 校验 & 合规]
    Cl -->|不通过| C
    Cl -->|通过| M[合并到 master<br/>稳定发布]
```

### 详细步骤

1. **Hermes 接收需求**
   - 在 `hermes/orchestration/` 创建任务卡：`任务_<序号>_<简称>.md`
   - 拆解子任务，明确交付物、验收标准、负责 Agent
   - 将可执行子任务分配给 Codex

2. **Codex 执行开发**
   - 切到 `codex/executor` 分支
   - 在 `codex/scripts/` 或 `codex/tools/` 实现功能
   - 提交代码：`feat(<模块>): <描述>`
   - 完成后通知 Claude 审查（可在 PR 描述或任务卡中 @Claude）

3. **Claude 审查校验**
   - 切到 `claude/reviewer` 分支
   - 在 `claude/review_checks/` 输出审查报告：`review_<任务序号>.md`
   - 在 `claude/validation/` 补充边界测试用例
   - 在 `claude/compliance/` 确认版权/隐私/安全合规
   - 结论：通过 / 有条件通过 / 不通过

4. **合并到 master**
   - 三方确认后，由 Hermes 发起合并申请
   - 合并到 `master` 并打标签，如 `v1.0.x`
   - 如需同步 GitHub，执行 `git push origin master hermes/brain codex/executor claude/reviewer --tags`

---

## 5. 分支与目录速查表

| 分支名 | 目录 | 初始提交 | 合并策略 |
|--------|------|----------|----------|
| `master` | 项目根目录 | `feat: init knowledge extraction project` | 最终稳定版本 |
| `hermes/brain` | `hermes/` | `feat: init hermes brain layer` | 合并到 master 前需 Codex/Claude 双确认 |
| `codex/executor` | `codex/` | `feat: init codex executor layer` | 需 Claude 审查后合并 |
| `claude/reviewer` | `claude/` | `feat: init claude reviewer layer` | 不直接合并到 master，仅产出审查报告 |

---

## 6. 在 ORCA 中提交与切换的注意事项

1. **工作树隔离**：三个工作树基于同一仓库的不同分支，目录内容相同但 HEAD 不同。在某一层工作树中提交，不会影响其他层。
2. **不要在 master 工作树直接修改 codex 代码**：应在对应分支工作树中修改，再合并。
3. **合并顺序**：建议先合并 `codex/executor` 的功能实现，再合并 `hermes/brain` 的流程编排，最后把 `claude/reviewer` 的审查报告作为质量记录归档。
4. **标签管理**：每次完整发布到 master 后，应打标签：`git tag -a "v1.x.x" -m "xxx"`

---

## 7. 快速命令速查

```bash
# 查看当前分支
 cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
 git status

# 切换到某一层分支
 git checkout hermes/brain
 git checkout codex/executor
 git checkout claude/reviewer
 git checkout master

# 合并三层分支到 master（在 master 上执行）
 git checkout master
 git merge --no-ff hermes/brain codex/executor claude/reviewer

# 推送所有分支与标签到 GitHub
 git remote add origin https://github.com/TJF19770107/side-project-knowledge-base.git
 git push -u origin master hermes/brain codex/executor claude/reviewer --tags
```

---

## 8. 常见问题

### Q1：ORCA 中没有「添加工作树」选项？
A：确保项目根目录是 Git 仓库，且 ORCA 版本支持 Git 工作树。也可使用 Git Bash 手动创建：
```bash
 git worktree add ./hermes hermes/brain
 git worktree add ./codex codex/executor
 git worktree add ./claude claude/reviewer
```

### Q2：三个分支内容完全一样？
A：初始阶段三个分支共享 `master` 的历史，只是后续各自只在自己目录下新增内容。这是设计预期，便于 ORCA 多工作树独立操作。

### Q3：如何防止跨层目录误提交？
A：`.gitignore` 中已排除日志、输出、备份、临时文件。建议在 `hermes/`、`codex/`、`claude/` 各目录中只负责本目录文件，合并到 master 时自然聚合。

---

> 最后更新：2026-07-19  
> 维护者：龙虾 AI 主控中心 · 多 Agent 舰队编排体系
