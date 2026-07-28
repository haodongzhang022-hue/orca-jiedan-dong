---
name: "lobster_task_standard_workflow_v2.7"
description: "龙虾五步法 V2.7 增量版：在V2.5规则锁定版基础上，叠加Orca多Agent工作树运维经验、Git分支幂等机制、Codex端口适配方案、会话持久化保障规则。适用于全域任务的标准化执行流程。"
version: "2.7"
date: "2026-07-19"
updated: "2026-07-19 (升级自V2.6：新增强制迭代触发器、修正15721代理矛盾规则、沉淀cc-switch 404案例)"
merged_from: ["v2.5 规则锁定版", "黄金黑马策略项目工作树运维实战", "Codex端口与MIMO后端切换实战", "会话丢失排查与恢复实战"]
sync_mode: "bidirectional"
primary_path: "E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v2.7\SKILL.md"
---

# 龙虾标准五步法 V2.7 增量版

技能名称：龙虾标准五步法（V2.7增量版·四大铁律·Orca工作树运维·会话持久化保障）
适用范围：全域任务（代码/配置/容器/流程/文档/排障/迭代/量化策略开发/Orca多Agent协作/工作树管理/会话恢复）
执行口径：严格按五步顺序执行，不许跳步；不删规则；不覆盖旧配置；只合并叠加
版本号：v2.7（在v2.5规则锁定版基础上，叠加Orca工作树运维实战经验）
更新时间：2026-07-08
生效范围：全域 / 永久 / Codex + Hermes + Claude Code + OpenCode + OpenClaw + Marvis + WorkBuddy 统一

---

## 继承声明

本版本**完整继承** V2.5 规则锁定版的全部内容，包括：
- 四大铁律（精准备份/无命令不修复/全存E盘/禁止后台扫描）
- 快照触发体系（手动确认/阈值自动/故障前置）
- 四大服务修复分支（Marvis/WorkBuddy/Codex/Claude Code）
- MT5量化MCP对接运维子流程
- MT5双环境隔离子流程

**以下仅列出 V2.7 新增内容，原有规则不重复、不覆盖。**

---

---

## 新增：第三方云端免费额度前置校验（V2.7 追加 · 对应全域模板 #293.8）

> **历史痛点（2026-07-19 截图实证）**：接入腾讯云混元3(hy3-preview)时未发现「10亿免费Token仅限小程序SDK/云函数调用」的硬性限制，原方案设计为本地直连，实际会产生**付费扣费风险**。
> **本步骤为五步法 Step1 之前的第0步前置校验**，任何涉及第三方云端模型接入任务必须先执行。

### 触发条件
当任务涉及以下场景时，**必须**先执行本步骤：
- 接入任何「免费额度」的云端模型（腾讯云/阿里云/百度云等）
- 看到「小程序成长计划」「免费资源包」「赠送额度」等字样
- 需要配置新的 API endpoint 指向非自有基础设施

### 校验清单（逐项确认，任一不通过则停止并标注风险）

| # | 校验项 | 确认方法 | 不通过处理 |
|---|--------|---------|-----------|
| Q1 | 免费额度的**合法调用通道**是什么？ | 控制台帮助文档 / 客服咨询 | 若仅限SDK/云函数 -> 设计中转方案 |
| Q2 | **本地直调是否触发付费？** | 控制台提示 / 测试小额调用后查账单 | 若是 -> **禁止直连，必须中转** |
| Q3 | 免费额度总量与到期日 | 控制台用量仪表盘 | 记录到方案文档 |
| Q4 | 超出免费后的计费单价 | 定价表 | 写入成本风险评估 |
| Q5 | 是否有即将下线的依赖模型 | 版本公告 | 制定替代时间线 |
| Q6 | 当前舰队日均消耗 x 可用周期测算 | 历史日志统计 | 若<30天 -> 必须限流 |

### 标准输出
校验完成后输出 QUOTA_CHECK_REPORT：
```
PASS / WARNING(含风险项) / BLOCKED(不可行)
模型: hy3-preview
免费总额度: 10亿 tokens
合法通道: 仅小程序SDK + 云函数
本地直调付费: 是 (WARNING)
可用周期: 17~33天 (全舰队模式)
推荐方案: A(云函数中转) + B(本地降级兜底)
```

### 关联技能
`lobster_fleet_tencent_hy3_cloud_bridge` - 本校验的标准落地案例

---

## 🔴🔴🔴 强制迭代触发器（V2.7 新增·补齐Step5自动化的生产者侧）

> **历史痛点**：本五步法 Step5「迭代沉淀」长期只是一段描述性文字，无任何可执行触发器。
> 导致 `state/issues_tracker.json.resolved` 自 2026-07-13 起为空，固化引擎
> (`lobster_skill_solidify.py` 每日00:10) 无料可吃，同类故障(如 cc-switch 404)反复从零排查。

### 铁律：任何任务/故障/商单交付完成后，必须执行 `lobster_auto_iterate` 流水线
顺序不可跳过（详见 `我的AI分身\技能库\lobster_auto_iterate\SKILL.md`）：

1. **Step1 问题闭环校验** → 调用 `record_iteration.py` 写入 `state/issues_tracker.json.resolved`
   （不写视为任务未完成，禁止仅临时修复不固化）
2. **Step2 重复判定检索** → 检索技能库/Obsidian/Git，相似度≥80%直接调用存量技能(场景C)，
   历史同类则覆盖迭代(场景B)，全新则生成技能包(场景A)
3. **Step3 软连接绑定** → 在 `skill_knowledge/INDEX.jsonl` 与技能库总索引追加一行，不复制文件
4. **Step4 双端沉淀** → 写入 Obsidian 双库 + 私有 Git 仓库，生成故障标签与触发词索引
5. **Step5 多Agent同步** → 更新各 Agent 的 AGENTS.md/SOUL.md 引用指向最新技能版本

### 迭代回执标准（每次任务收尾自动生成）
- [ ] `issues_tracker.json.resolved` 已写入
- [ ] 重复判定场景(A/B/C)已标注
- [ ] 索引文件已追加
- [ ] Obsidian双库 + Git 已写入
- [ ] 多Agent引用已更新
- [ ] 固化引擎下次00:10将自动消费

---

## 新增：Orca 工作树运维子流程（V2.7）

### 触发条件
当任务涉及以下场景时，自动激活本子流程：
- 在 Orca IDE 中创建/管理 Git worktree 分支
- 配置多Agent协作分支架构
- 排查 Agent 端口/连接问题
- 恢复丢失的会话历史
- 切换模型后端

### Step 1: 目标定义
- 确认项目仓库路径、分支数量、Agent绑定方案
- 确认模型后端（MIMO/Ollama/OpenAI）及API Key来源

### Step 2: 环境诊断
```bash
# 进程检查
tasklist | grep -iE "orca|codex|hermes"
# 端口检查
netstat -ano | grep LISTENING
# 标记文件检查
ls .git/.orca_initialized.*
# 数据库完整性
sqlite3 state.db "PRAGMA integrity_check"
```

### Step 3: 方案落地
1. **仓库初始化**：git init → .gitignore → 首次提交
2. **分支创建**：git branch + git worktree add
3. **钩子配置**：写入幂等 post-checkout 钩子
4. **Agent绑定**：每个分支分配唯一Agent
5. **后端配置**：更新 OPENAI_BASE_URL 到实际模型后端

### Step 4: 结果验证
- 标记文件生成验证
- 幂等跳过验证（二次运行应跳过）
- 端口监听验证
- API连通性测试（curl /v1/models）
- 会话检索验证（session_search）

### Step 5: 迭代沉淀
- 归档报告到 Doc/ 目录
- 更新 memory 中的环境信息
- 如发现新坑，更新本技能文档

---

## 新增：会话持久化保障规则（V2.7）

### 规则 1: state.db 是唯一真相源
- Hermes 的所有会话存储在 `state.db`（SQLite），实时落盘
- 会话数据不因 Orca 重启、Agent 重启、分支切换丢失

### 规则 2: Orca UI 面板限制的应对
- `workspaceSessionsByHostId` 重启后清空 → UI 面板空白
- 应对：输入「查看历史会话」从 state.db 检索
- 备选：将会话导出为 Markdown 文件存入 Doc/

### 规则 3: 检索指令标准化
```
查看历史会话                          → 最近10条会话
查找 <关键词> 的历史对话              → 关键词检索
查看 <日期> 的会话                    → 按日期筛选
```

---

## 新增：Codex 端口与后端适配规则（V2.7，V2.7 已修正）

### ⚠️ V2.7 修正（此前规则已过时，曾导致 cc-switch 404 反复故障）
**本机实际生效的 Codex++ 链路并非"直连 MiMO"，而是经过本地重写代理：**
```
Codex++ GUI (模型锁 gpt-5.5)
   → cc-switch :15721  (E:\龙虾AI主控中心\CC-Switch\cc-switch.exe)
   → AI Code Switch :4567  (E:\aicodeswitch_v5 → G盘 Junction, 负责 gpt-5.5→mimo-v2.5-pro 重写)
   → MiMO 后端
```
**cc-switch 的 provider baseURL 必须带 /v1 前缀**（拼接逻辑 = baseURL + "/responses"），
即 `http://127.0.0.1:4567/v1`，否则拼出 `4567/responses` → 404。

### 规则 1: cc-switch 代理端口是**常驻固定**的，不是临时分配
- 15721 是 cc-switch 总网关（不可改），4567 是 AI Code Switch 代理（协议转换）
- Codex++ 通过 15721 通信，**必须依赖此代理链路**，不能直连 MiMO（否则 gpt-5.5 被 MiMO 拒收）

### 规则 2: provider baseURL 规范（V2.7 修正）
| 场景 | baseURL | 说明 |
|------|---------|------|
| Codex++ 经 cc-switch 转发 | `http://127.0.0.1:4567/v1` | **带 /v1**，4567 负责模型重写 |
| 直接调用 MiMO(绕过代理) | `https://token-plan-cn.xiaomimimo.com/v1` | 仅当不用 gpt-5.5 模型名时 |
| Ollama | `http://127.0.0.1:11434/v1` | 需确保 Ollama 运行 |

### 规则 3: 修复技能包
- `cc_switch_4567_autofix`：404/400/502/断连一键修复
- `cc_switch_precheck`：启动前校验所有 4567 地址带 /v1 前缀，异常自动修复

### 规则 4: API Key 管理
- Key 存储在 `.env`，配置文件引用
- 禁止在日志/报告中输出完整 Key

---

## 新增：cc-switch 404 链路故障案例（V2.7 沉淀）

### 触发场景
Codex++ 桌面版开机报错，常见报错：
- `stream disconnected before completion: error sending request for url (http://127.0.0.1:4567/responses)`
- `unexpected status 404 Not Found: {"error":"Not Found"}, url http://127.0.0.1:4567/responses`

### 根因（两步法定位）
1. **4567 宕机**（Type-B/D）：`netstat` 查 4567 不在 LISTENING → 清 `server.pid` 僵尸 + 重启 AI Code Switch
2. **baseURL 缺 /v1**（Type-C，核心）：cc-switch 拼路径 = baseURL + "/responses"，
   若 baseURL=`http://127.0.0.1:4567`(无/v1) → 拼出 `4567/responses` → 404

### 修复（完整技能见 `cc_switch_4567_autofix`）
```sql
-- cc-switch 停止后执行
UPDATE providers SET settings_config =
  REPLACE(settings_config, 'base_url":"http://127.0.0.1:4567"',
                       'base_url":"http://127.0.0.1:4567/v1"')
  WHERE id='xiaomimimo20260612';   -- Codex++ 实际用的 provider
UPDATE providers SET settings_config =
  REPLACE(settings_config, 'http://127.0.0.1:4567"', 'http://127.0.0.1:4567/v1"')
  WHERE settings_config LIKE '%127.0.0.1:4567"%' AND settings_config NOT LIKE '%127.0.0.1:4567/v1%';
UPDATE provider_endpoints SET url='http://127.0.0.1:4567/v1' WHERE id IN (15,21);
```
修复后必须**重启 cc-switch**（窗口模式 `start "" cc-switch.exe`），否则内存缓存旧配置。

### 防复发
- 启动前跑 `cc_switch_precheck` 自动校验所有 4567 地址带 /v1
- 一键修复：`codex_fullchain_fix_v2.1.bat`（双击）

---

## 快速参考

| 操作 | 命令 |
|------|------|
| 检查Orca进程 | `tasklist \| grep orca` |
| 检查端口监听 | `netstat -ano \| grep LISTENING` |
| 检查标记文件 | `ls .git/.orca_initialized.*` |
| 测试MIMO连通 | `curl <URL>/models -H "Authorization: Bearer <KEY>"` |
| 检索历史会话 | 对话中输入「查看历史会话」 |
| 强制重新初始化 | `rm .git/.orca_initialized.*` |

---

完整 V2.5 原版内容见：`E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v2.5_locked\SKILL.md`
本 V2.7 增量版路径：`E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v2.7\SKILL.md`

---

## 新增：ORCA 多 Agent 舰队搭建子流程（V2.7 追加）

> 触发条件：新建 ORCA 多 Agent 项目、复刻黄金黑马策略三层架构、沉淀通用项目脚手架。

### Step 1: 目标定义
- 明确项目根目录与主分支名（推荐沿用 ORCA 已绑定分支，如 `master`）
- 确定三层角色：
  - `hermes/brain`：大脑层 / 战略调度
  - `codex/executor`：执行层 / 代码实现
  - `claude/reviewer`：核查层 / 质量把关

### Step 2: 环境诊断
```bash
# 进入项目根目录
cd "E:/龙虾AI主控中心/我的AI分身/你的项目"
# 确认当前分支与提交状态
git status && git branch -a && git log --oneline -n 3
# 确认 ORCA 已打开该项目
```

### Step 3: 方案落地
1. **初始化主分支**：如尚未提交，执行 `git add -A && git commit -m "feat: init project"`
2. **创建三层分支**：
   ```bash
   git checkout -b hermes/brain
   git checkout -b codex/executor
   git checkout -b claude/reviewer
   git checkout master
   ```
3. **创建各层专属目录**：
   - `hermes/flow_control/`、`hermes/orchestration/`、`hermes/knowledge_sync/`
   - `codex/scripts/`、`codex/tools/`、`codex/batch_tasks/`
   - `claude/review_checks/`、`claude/validation/`、`claude/compliance/`
4. **生成 ORCA 工作树指南**：在 `docs/ORCA多Agent工作树搭建指南.md` 中记录添加工作树、配置分工、协作流程
5. **沉淀通用脚手架**：将本项目结构复制到 `E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0\`，并编写 `init_orca_fleet.sh`
6. **合并到主分支**：
   ```bash
   git checkout master
   git merge --no-ff hermes/brain codex/executor claude/reviewer
   git tag -a "v1.0.0-orca-fleet" -m "ORCA 多 Agent 舰队架构 V1.0.0"
   ```

### Step 4: 结果验证
- 检查三层分支是否存在：`git branch -a`
- 检查各层目录是否已合并到 master：`ls hermes/ codex/ claude/`
- 检查 ORCA 工作树指南是否完整可读
- 测试脚手架一键初始化脚本是否能成功生成新项目
- 检查 git 标签是否生成：`git tag -n`

### Step 5: 迭代沉淀
- 将搭建过程写入 `docs/龙虾五步法案例-ORCA多Agent舰队搭建.md`
- 在「龙虾全域官方模板」中追加协议 #289「ORCA多Agent舰队搭建规范」
- 更新本 SKILL.md 的迭代回执校验清单
- 同步到 Obsidian 双库与私有 Git 仓库

---

## 新增：ORCA 多 Agent 工作树配置子流程（V2.7 追加 · 对应全域模板 #290）

> 触发条件：在 ORCA 中为三层舰队项目配置/添加工作树、填写设置脚本与存档脚本、开启自动填充。
> 完整规范见 `网盘课程资源知识萃取与沉淀体系重建/docs/ORCA工作树自动填充配置规范.md` 与 `docs/可视化标注指南.md`。

### Step 1: 精准备份（环境复制）
- 在 ORCA「设置脚本」框注入标准初始化脚本（龙虾五步法 Step1 环境备份）
- 脚本动作：复制 `config/default_config.yaml` 与 `.env` 至工作树 → `pip install -r requirements.txt` → `mklink /D obsidian_link` 绑定 G 盘 Obsidian → 调用 `scripts/skill_auto_register.py --tree` 注册当前分支技能
- 所有路径经环境变量（`ORCA_ROOT_PATH`/`ORCA_WORKTREE_PATH`/`OBSIDIAN_MAIN`/`LOBSTER_BACKUP_ROOT`）解析，**禁止写死 C 盘绝对路径**

### Step 2: 根因诊断（规范校验）
- 新建工作树前校验：分支名 ∈ {`hermes/brain`, `codex/executor`, `claude/reviewer`}
- 校验「工作树位置」是否已替换为 E 盘模板 `E:\龙虾AI主控中心\我的AI分身\${ORCA_WORKSPACE_NAME}`（非 ORCA 默认 C 盘）
- 校验三层目录 `hermes/` `codex/` `claude/` 与 Agent 权限隔离是否就位

### Step 3: 无命令不修复（自动执行）
- 「何时跑步」设为【默认运行】，新建工作树时**自动执行**设置脚本，禁止手动逐机改环境
- 「等待设置完成后再启动智能体」开关＝**开启**
- 仅当用户修改全域模板核心规则 / 创建新工作树授权节点时，才请求人工确认

### Step 4: 验证校验（生效检测）
- 检测 `obsidian_link` 软链是否指向 `OBSIDIAN_MAIN`
- 检测 `skill_registry.json` 是否已追加当前分支技能条目（幂等，重复运行跳过）
- 检测 `requirements.txt` 依赖是否安装成功
- 失败时回退：重跑设置脚本，不手动 patch 环境

### Step 5: 沉淀归档（Step5 闭环）
- 在 ORCA「存档脚本」框注入标准归档脚本（龙虾五步法 Step5 沉淀）
- 删除工作树前自动执行：备份 `logs/` 至 `LOBSTER_BACKUP_ROOT/$ORCA_WORKSPACE_NAME` → `git add . && git commit -m "auto archive: ..."`
- 归档产物同步至私有 Git 仓库与 Obsidian 双库，支持溯源与回滚
- 将本次配置流程沉淀为案例 `docs/龙虾五步法案例-ORCA工作树可视化配置.md`

---

## 新增：ORCA 多 Agent 舰队项目脚手架落地案例（V2.7 追加 · 2026-07-20）

> 项目名称：`网盘课程资源知识萃取与沉淀体系建设`  
> 项目路径：`E:\龙虾AI主控中心\我的AI分身\网盘课程资源知识萃取与沉淀体系建设`  
> 脚手架来源：`E:\龙虾AI主控中心\我的AI分身\项目脚手架\orca_multi_agent_fleet_v1.0`  
> 落地分支：`master` + `hermes/brain` + `codex/executor` + `claude/reviewer`

### 复现命令（可直接复制到 ORCA 底部 bash 区执行）
```bash
# Step 1: 用 v1.0 脚手架一键创建项目
bash "E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/init_orca_fleet.sh" \
    "E:/龙虾AI主控中心/我的AI分身/网盘课程资源知识萃取与沉淀体系建设"

# Step 2: 进入项目并确认三层分支
cd "E:/龙虾AI主控中心/我的AI分身/网盘课程资源知识萃取与沉淀体系建设"
git branch -a

# Step 3: ORCA 中添加三个工作树（按 docs/可视化标注指南.md 填写）
# 分支 hermes/brain    → 目录 hermes/
# 分支 codex/executor  → 目录 codex/
# 分支 claude/reviewer → 目录 claude/
```

### 关键交付物
- 项目根已配置 `.gitignore`、`.gitattributes`、`.env`
- 三层目录 `hermes/` `codex/` `claude/` 已就位并合并到 `master`
- 技能注册器 `scripts/skill_auto_register.py`（幂等写入主仓库 `skill_registry.json`）
- 可视化配置指南：`docs/可视化标注指南.md` / `.html`
- 自动填充规范：`docs/ORCA工作树自动填充配置规范.md`

### 与全域模板关联
- 协议 #289「ORCA 多 Agent 舰队搭建规范」
- 协议 #290「ORCA 多 Agent 工作树自动填充配置规范」
- 知识萃取类任务触发规则（项目入口已指向本项目）

---

## 新增：脚手架版本校验节点（V2.7 追加 · 2026-07-20 · 对应全域模板 #290.10 / #291）

> 插入位置：五步法「环境初始化 / 脚手架加载」环节（建议放在「加载脚手架」步骤内，git 初始化前后均可）。
> 对应脚手架：`orca_multi_agent_fleet_v1.0`（`scripts/orca_scaffold_check.sh` / `scripts/upgrade_incremental.sh`）。
> 核心原则：**不自动升级旧项目 · 版本不一致才询问 · 支持长期分叉 · 保护目录永不覆盖**。

### 节点：版本校验 & 交互式确认（非冗余，仅版本不一致触发）

#### 1. 比对
- 读取：`项目根/scaffold_version`（当前项目脚手架版本）
- 读取：`项目脚手架/scaffold_version`（全域最新脚手架版本）

#### 2. 一致 → 直接启动
- 版本相同：**不弹窗**，直接进入后续步骤（避免冗余打扰，根治「老点运行」）。

#### 3. 不一致 → 弹出固定话术（强制，不可跳过 / 不可静默升级）
```
检测到脚手架版本不一致：
当前项目：vX.X.X
全域最新：vY.Y.Y

是否使用新版脚手架对本项目进行【增量迭代】？
- 仅补充新参数、新技能、新配置
- 原有数据库、会话、自定义功能全部保留

[Y] 是，执行增量迭代
[N] 否，保留旧版本，版本分叉独立运行
```

#### 4. 分支流程
- **选 Y｜增量迭代**
  - 执行 `upgrade_incremental.sh`：只新增项目中不存在的文件，已存在文件**不覆盖、不修改**。
  - 跳过保护目录：`.env` `database` `conversations` `skills` `logs`。
  - 完成后把项目 `scaffold_version` 写回最新版。
- **选 N｜版本分叉**
  - 写入 `fork_version.log`（fork_version / forked_from_latest / 时间戳）。
  - 永久沿用旧脚手架，新旧长期并行、各自迭代。

#### 5. 非交互环境兜底
- 无 TTY（CI / 管道）时**不自动决策**，输出手动命令后退出（exit 2），杜绝静默升级。

#### 6. 全程日志
- 记录：版本号、选择结果、变更文件清单（`.upgrade_changelog.txt`），便于回溯。

### 配套原则（写进五步法总则）
- **不自动升级旧项目**：任何模板/脚手架更新，旧项目保持原状。
- **版本不一致才询问，一致直接跑**：防冗余。
- **支持长期分叉**：新旧脚手架可同时维护、分别迭代。
- **数据绝对安全**：保护目录永远不覆盖。

---

## 新增：Type-H 双实例接入初始化分支（V2.7 追加 · 2026-07-27）

> **补丁类型**：新增 **Type-H（双实例接入）** 分支
> **绑定技能**：`orca_dual_instance_gui_keli`
> **生效条件**：新建ORCA项目时用户选择「启用双实例模式」
> **合并日期**：2026-07-27

### 触发条件
- 用户在脚手架交互弹窗中选择「启用双实例模式」
- 或手动调用技能 `orca_dual_instance_gui_keli`

### 五步法适配（Type-H专用流程）

| 步骤 | 标准动作 | Type-H特化动作 |
|------|---------|---------------|
| **Step1 诊断** | 全链路端口/进程/配置扫描 | **额外**：扫描目标端口(4567/57321/57330/57331/57332)冲突；检测E盘技能库路径可达性 |
| **Step2 分析** | 根因定位 | **额外**：确认各Agent GUI/CLI二进制文件存在；验证Git worktree命令可用 |
| **Step3 修复** | 执行修复 | **替换为**：执行双实例初始化流程（见下方）|
| **Step4 验证** | 功能验证 | **额外**：7项校验清单全通过（端口/worktree/快照/技能库/login/脚本/模型标识）|
| **Step5 沉淀** | 技能迭代/快照 | **额外**：生成 `_ORCA_BASE_SNAP/` 基线快照；写入 `registry.json` 端口注册表 |

### Step3 特化：双实例初始化子流程

```
3.1 创建项目目录结构
    ├── 【项目名】/              (master主干)
    │   ├── login.md            (凭证模板)
    │   ├── CODEX.md            (身份声明)
    │   └── logs/msgbus/        (消息总线目录)
    ├── 【项目名】.hermes/       (hermes worktree)
    ├── 【项目名】.codex/        (codex worktree)
    ├── 【项目名】.claude/       (claude worktree)
    └── _ORCA_BASE_SNAP/        (全局快照池)

3.2 Git仓库 + Worktree初始化
    git init + checkout -b master
    git worktree add .hermes -b hermes
    git worktree add .codex -b codex
    git worktree add .claude -b claude

3.3 端口冲突校验(netstat) → 冲突则递增备选端口

3.4 生成6个启动脚本(3Agent × 2实例):
    hermes_gui.cmd / hermes_cli.cmd
    codex_gui.cmd / codex_cli.cmd
    claude_serve_57330.cmd / claude_chat.cmd

3.5 Codex特殊处理:
    codex_gui.cmd 内嵌 codex_self_heal.py --fix (前置自愈)

3.6 Claude Code特殊处理:
    claude_serve_57330.cmd 使用独立端口57330(与OCR内置隔离)

3.7 生成 registry.json (端口注册表)

3.8 执行7项校验清单 → 全✅才交付
```

### 与既有故障类型的协作关系

| 已有类型 | 与Type-H的关系 |
|----------|--------------|
| Type-F (config覆盖) | Type-H的Codex GUI启动脚本**自动调用** Type-F的自愈逻辑 |
| Type-G (沙盒权限) | Type-H的Codex GUI启动脚本**自动调用** Type-G的沙盒修复逻辑 |
| Type-E (舰队核验Q1-Q5) | Type-H初始化完成后**自动触发** Type-E的5维健康度检查 |

> **设计原则**：Type-H是"容器型"分支，内部聚合调用F/G/E等已有修复逻辑，不重复实现。

### 故障类型分类表追加

```
| Type-H | 双实例接入初始化 | orca_dual_instance_gui_keli | 新建ORCA项目启用GUI+CLI双实例模式 |
```

### Type-H 分支入口（插入Step1之后）
当检测到 `--dual-instance` 参数或脚手架弹窗选择「启用」时：
  → 跳转至 Type-H 专用子流程（见上方表格）
  → 初始化完成后自动触发 Type-E 舰队核验

---

## Type-H 落地实装（V2.7 追加 · 2026-07-28 · 对应全域模板v3.120-R42 协议#294）

> Type-H 由「方案态」升级为「实装态」：中央运行时 dual_core 七件套已落地脚手架 v1.3.0，三试点项目验证 7/7·100% 通过。

### 中央运行时（唯一真源，项目仅引用不复制）
```
E:/龙虾AI主控中心/我的AI分身/项目脚手架/orca_multi_agent_fleet_v1.0/dual_core/
├── omf.py                    ← OMF v1.0 消息协议库（六窗口/三消息类型/防丢防重/G盘追溯）
├── orca_msgbus_router.py     ← 六窗口全互联路由器（--watch常驻/链式流转/路由表）
├── orca_switch.py            ← 双实例一键切换（上下文快照/校验/自动回滚）
├── orca_dispatch.py          ← Workbody外部调度（list/send/status/result/权限分级）
├── gui_server.py             ← GUI桌面端服务（Edge --app承载/MiMO V2.5绑定）
├── fleet_gui.html            ← GUI面板（发消息/切换/收件箱/上下文）
├── orca_full_validation.py   ← 全量验证T1-T7 + Type-F自愈重试3次
├── init_orca_dual_mode.py    ← A/B/C三模式生成器（交互式弹窗）
└── create_shortcuts.vbs      ← 桌面+开始菜单快捷方式（热键Ctrl+Alt+H/K/L）
```

### 双实例调度标准流程（五步法嵌入）
```
Step1 检查 → orca_dispatch.py status -p <项目>（六窗口消息积压检查）
Step2 分析 → 读 registry.json 端口矩阵 + routing_table.json 路由表
Step3 修复 → switch.cmd 切换实例 / router 重启 / Type-F自愈
Step4 迭代 → orca_full_validation.py --project <根>（必须7/7通过）
Step5 沉淀 → 报告自动落 G:/…/ORCA数据/reports/ + 技能orca_fleet_dual_control更新
```

### 互调验证标准（新增强制项）
1. **六窗互发**：6×5=30条两两互发消息，投递率100%方可验收；
2. **链式闭环**：standard_loop 至少3跳自动转发成功；
3. **切换同步**：3 Agent dry-run切换后 context 快照必须存在；
4. **权限校验**：readonly send 必须被拒绝（DENY），否则调度器判定失效；
5. **已知边界**：Hermes/Claude 无官方GUI exe → Web面板方案为标准实现（非降级）。

