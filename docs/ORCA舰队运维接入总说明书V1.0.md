# ORCA 舰队运维接入总说明书 V1.0

> **版本**：V1.0 | **关联节点**：PR#5 合并 | **基座**：CNB 免费 DeepSeek-V4-Flash（有效期至 2026-12-31）
> **适用读者**：Maris（本地调度 Agent）/ Codex（代码执行 NPC）/ Claude Code（代码审计 NPC）/ CodeBuddy（终审 NPC）
> **核心目标**：打开本说明书即可定位路径、复制命令一键拉起、完成跨 NPC 协作全流程

---

## 目录

- [模块1：项目全局目录路径手册](#模块1项目全局目录路径手册)
- [模块2：分场景一键拉起命令手册](#模块2分场景一键拉起命令手册)
- [模块3：云原生 DeepSeek V4 适配专项答疑](#模块3云原生-deepseek-v4-适配专项答疑)
- [模块4：Maris ↔ CNB NPC ↔ CodeBuddy 跨主体协作链路](#模块4maris--cnb-npc--codebuddy-跨主体协作链路)
- [模块5：Maris 自主阅读适配设计](#模块5maris-自主阅读适配设计)
- [模块6：故障兜底附录](#模块6故障兜底附录)

---

## 模块1：项目全局目录路径手册

### 1.1 脚手架根目录结构总览

| 本地路径（Windows E 盘） | CNB 云端仓库路径 | 说明 |
|---|---|---|
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\` | `/`（仓库根目录） | 脚手架根路径 |
| `E:\...\config\` | `config/` | 配置文件（模型、舰队档案、系统提示词） |
| `E:\...\scripts\` | `scripts/` | 核心脚本（一键拉起、调度、健康检查等） |
| `E:\...\docs\` | `docs/` | 文档（说明书、指南、报告等） |
| `E:\...\fleet_exchange\` | `fleet_exchange/` | 任务交换区（四级流转） |
| `E:\...\worktrees\` | `worktrees/` | 三工作树（hermes/codex/claude） |
| `E:\...\templates\` | `templates/` | 输出模板（课程大纲、知识卡片等） |
| `E:\...\skills\` | `skills/` | 技能库（海报设计、画册排版、短视频等） |
| `E:\...\tools\` | `tools/` | 工具集 |
| `E:\...\msgbus\` | `msgbus/` | 消息总线（Agent 间通信） |
| `E:\...\snapshots\` | `snapshots/` | 三引擎快照存档 |
| `E:\...\tests\` | `tests/` | 自测样本 |
| `E:\...\.cnb\` | `.cnb/` | CNB 平台配置（settings.yml） |
| `E:\...\.orca\` | `.orca/` | ORCA IDE 自动就绪脚本 |

### 1.2 核心脚本物理绝对路径索引

| 脚本名称 | 本地路径 | 云端路径 | 功能 |
|---|---|---|---|
| **CNB云原生一键拉起** | `E:\...\scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat` | `scripts/一键拉起_CNB云原生DeepSeekV4Flash.bat` | CNB 云端链路一键启动 |
| **CNB云原生一键拉起(PS)** | `E:\...\scripts\一键拉起_CNB云原生DeepSeekV4Flash.ps1` | `scripts/一键拉起_CNB云原生DeepSeekV4Flash.ps1` | PowerShell 版本 |
| **Ollama本地一键拉起** | `E:\...\scripts\一键拉起_Ollama本地DeepSeekV4Flash.bat` | `scripts/一键拉起_Ollama本地DeepSeekV4Flash.bat` | Ollama 本地链路启动 |
| **Ollama本地一键拉起(PS)** | `E:\...\scripts\一键拉起_Ollama本地DeepSeekV4Flash.ps1` | `scripts/一键拉起_Ollama本地DeepSeekV4Flash.ps1` | PowerShell 版本 |
| **舰队自动就绪** | `E:\...\scripts\fleet_auto_ready.sh` | `scripts/fleet_auto_ready.sh` | 三 Agent 自动就绪检查 |
| **舰队自动就绪(Win)** | `E:\...\scripts\fleet_auto_ready.cmd` | `scripts/fleet_auto_ready.cmd` | Windows 版本 |
| **舰队自动恢复** | `E:\...\scripts\fleet_auto_restore.cmd` | `scripts/fleet_auto_restore.cmd` | 开机自启恢复 |
| **舰队健康检查** | `E:\...\scripts\fleet_health_check.sh` | `scripts/fleet_health_check.sh` | 全栈健康检查 |
| **舰队一键确保** | `E:\...\scripts\fleet_ensure.sh` | `scripts/fleet_ensure.sh` | 端口+shim+配置一键确保 |
| **舰队完成归档** | `E:\...\scripts\fleet_done.sh` | `scripts/fleet_done.sh` | 任务结果回写+归档 |
| **任务确认放行** | `E:\...\scripts\confirm_task.sh` | `scripts/confirm_task.sh` | 待确认→incoming 放行 |
| **MIMO一键拉起** | `E:\...\scripts\one_click_mimo_v25.sh` | `scripts/one_click_mimo_v25.sh` | MIMO V2.5 Pro 全栈启动 |
| **DeepSeek接入** | `E:\...\scripts\orca_connect_deepseek.sh` | `scripts/orca_connect_deepseek.sh` | DeepSeek API Key 配置 |
| **工作树初始化** | `E:\...\scripts\orca_setup_worktree.sh` | `scripts/orca_setup_worktree.sh` | 三工作树环境变量注入 |
| **项目自动就绪** | `E:\...\scripts\orca_project_startup.sh` | `scripts/orca_project_startup.sh` | Orca 打开项目时自动检查 |
| **目录结构创建** | `E:\...\scripts\创建目录结构.sh` | `scripts/创建目录结构.sh` | 标准目录骨架一键创建 |
| **目录结构创建(PS)** | `E:\...\scripts\创建目录结构.ps1` | `scripts/创建目录结构.ps1` | PowerShell 版本 |
| **Maris调度分发** | `E:\...\scripts\maris_dispatch.sh` | `scripts/maris_dispatch.sh` | Maris 任务投递调度（**待创建**） |
| **Maris文档生成** | `E:\...\scripts\maris_gen_readme.sh` | `scripts/maris_gen_readme.sh` | Maris 接入文档自动生成（**待创建**） |
| **工作树批量初始化** | `E:\...\scripts\orca_init_worktrees.sh` | `scripts/orca_init_worktrees.sh` | 三工作树批量初始化（**待创建**） |

### 1.3 fleet_exchange 四级任务流转路径

| 流转目录 | 本地路径 | 云端路径 | 用途 | 写入者 | 读取者 |
|---|---|---|---|---|---|
| **incoming**（待接单） | `E:\...\fleet_exchange\incoming\` | `fleet_exchange/incoming/` | 新任务卡落地 | Hermes / Maris | Codex |
| **doing**（执行中） | `E:\...\fleet_exchange\doing\` | `fleet_exchange/doing/` | Codex 正在处理 | Codex | Claude Code |
| **done**（已完成） | `E:\...\fleet_exchange\done\` | `fleet_exchange/done/` | Claude Code 审核通过 | Claude Code | CodeBuddy |
| **results**（归档输出） | `E:\...\fleet_exchange\results\` | `fleet_exchange/results/` | 最终交付物 | CodeBuddy | 客户 |

**云端同步规则**：
- `git push` 后自动同步到 CNB 云端仓库
- `incoming/` 中的任务卡通过 `git add + commit + push` 提交后，云端 NPC 可通过 Issue 评论读取
- `done/` 和 `results/` 通过 `fleet_done.sh` 自动归档并同步

**辅助目录**：

| 目录 | 本地路径 | 云端路径 | 用途 |
|---|---|---|---|
| **accepted** | `E:\...\fleet_exchange\accepted\` | `fleet_exchange/accepted/` | 已接单确认 |
| **orders** | `E:\...\fleet_exchange\orders\` | `fleet_exchange/orders/` | 订单元数据 |
| **parsed** | `E:\...\fleet_exchange\parsed\` | `fleet_exchange/parsed/` | 已解析订单 |
| **templates** | `E:\...\fleet_exchange\templates\` | `fleet_exchange/templates/` | 订单/设计模板 |

### 1.4 Maris 标准件 + 配套文档路径索引

| 文件 | 本地路径 | 云端路径 | 状态 |
|---|---|---|---|
| `maris_dispatch.sh` | `E:\...\scripts\maris_dispatch.sh` | `scripts/maris_dispatch.sh` | ⚠️ **待创建**（模板见模块2） |
| `maris_gen_readme.sh` | `E:\...\scripts\maris_gen_readme.sh` | `scripts/maris_gen_readme.sh` | ⚠️ **待创建**（模板见模块2） |
| `orca_init_worktrees.sh` | `E:\...\scripts\orca_init_worktrees.sh` | `scripts/orca_init_worktrees.sh` | ⚠️ **待创建**（模板见模块2） |
| `fleet_exchange/README.md` | `E:\...\fleet_exchange\README.md` | `fleet_exchange/README.md` | ⚠️ **待创建** |
| `docs/Maris调度接入说明.md` | `E:\...\docs\Maris调度接入说明.md` | `docs/Maris调度接入说明.md` | ⚠️ **待创建** |

### 1.5 关键配置文件路径

| 文件 | 本地路径 | 云端路径 | 用途 |
|---|---|---|---|
| `.cnb.yml` | `E:\...\.cnb.yml` | `.cnb.yml` | NPC 流水线配置（codex/claude-code 角色绑定） |
| `.cnb/settings.yml` | `E:\...\.cnb\settings.yml` | `.cnb/settings.yml` | NPC 角色人设 prompt |
| `config/model_config.yaml` | `E:\...\config\model_config.yaml` | `config/model_config.yaml` | 本地模型后端配置 |
| `config/default_config.yaml` | `E:\...\config\default_config.yaml` | `config/default_config.yaml` | 项目默认配置 |
| `config/fleet_profiles/mimo.env` | `E:\...\config\fleet_profiles\mimo.env` | `config/fleet_profiles/mimo.env` | MIMO V2.5 舰队档案 |
| `config/fleet_profiles/official_ds.env` | `E:\...\config\fleet_profiles\official_ds.env` | `config/fleet_profiles/official_ds.env` | CNB 云原生 DeepSeek 档案 |
| `config/fleet_profiles/ollama_ds.env` | `E:\...\config\fleet_profiles\ollama_ds.env` | `config/fleet_profiles/ollama_ds.env` | Ollama 本地 DeepSeek 档案 |
| `CODEX.md` | `E:\...\CODEX.md` | `CODEX.md` | Codex 工作树配置+自动恢复协议 |
| `CLAUDE.md` | `E:\...\CLAUDE.md` | `CLAUDE.md` | Claude Code 工作树配置+自动恢复协议 |

> **Maris 执行自检清单** ✅
> - [ ] 已确认本地项目根目录为 `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\`
> - [ ] 已确认 `fleet_exchange/incoming/doing/done/results` 四级目录存在
> - [ ] 已确认 `.cnb.yml` 和 `.cnb/settings.yml` 配置文件存在
> - [ ] 已确认三个舰队档案 `mimo.env`/`official_ds.env`/`ollama_ds.env` 存在

---

## 模块2：分场景一键拉起命令手册

### 2.1 场景一：脚手架批量部署

#### 单项目部署

<details>
<summary>📋 一键复制 — 单项目部署（Git Bash）</summary>

```bash
# 前置条件：已安装 Git Bash，已配置 CNB 账号
# 执行效果：克隆仓库 + 创建标准目录骨架 + 初始化工作树

# 1. 克隆仓库
git clone https://cnb.cool/TJF19770107/orca-jiedan.git
cd orca-jiedan

# 2. 创建标准目录骨架
bash scripts/创建目录结构.sh

# 3. 验证目录结构
ls -la fleet_exchange/ worktrees/ scripts/ config/
```

</details>

<details>
<summary>📋 一键复制 — 单项目部署（PowerShell）</summary>

```powershell
# 前置条件：已安装 Git，已配置 CNB 账号
# 执行效果：同上

# 1. 克隆仓库
git clone https://cnb.cool/TJF19770107/orca-jiedan.git
cd orca-jiedan

# 2. 创建标准目录骨架
powershell -ExecutionPolicy Bypass -File scripts\创建目录结构.ps1

# 3. 验证
Test-Path fleet_exchange, worktrees, scripts, config
```

</details>

#### 多项目批量部署

<details>
<summary>📋 一键复制 — 多项目批量部署（6个仓库）</summary>

```bash
# 前置条件：已配置 CNB 账号
# 执行效果：批量克隆龙虾舰队全部6个仓库

REPOS=(
  "orca-jiedan"       # 企业微信接单项目
  "orca-wangpan"      # 网盘萃取项目
  "orca-xianyu"       # 闲鱼自动化项目
  "orca-quant-jiasheng" # 量化嘉盛策略
  "orca-quant-binance"  # 量化币安策略
  "orca"              # 主空仓（调度中枢）
)

for repo in "${REPOS[@]}"; do
  echo "=== 克隆 ${repo} ==="
  git clone "https://cnb.cool/TJF19770107/${repo}.git"
  cd "${repo}"
  # 创建标准目录（如果脚本存在）
  [ -f scripts/创建目录结构.sh ] && bash scripts/创建目录结构.sh
  cd ..
done

echo "✅ 全部6个仓库已部署完成"
```

</details>

#### 全量默认部署

<details>
<summary>📋 一键复制 — 全量默认部署（CNB云原生链路）</summary>

```batch
:: 前置条件：Windows 环境，已安装 Git
:: 执行效果：人设蒸馏 + 流水线校验 + 浏览器唤起 + NPC调度就绪

cd E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts
一键拉起_CNB云原生DeepSeekV4Flash.bat
```

**报错排查**：
| 报错 | 原因 | 解决方案 |
|------|------|----------|
| `.cnb.yml 缺失` | 未配置流水线 | 脚本会自动创建，或手动创建 |
| `G盘未挂载` | 网盘未连接 | 挂载 G 盘后重试，或跳过镜像同步 |
| `Obsidian未找到` | 知识库路径不存在 | 检查 `E:\龙虾AI主控中心\Obsidian\` 是否存在 |

</details>

### 2.2 场景二：项目初始化

#### 三工作树初始化

<details>
<summary>📋 一键复制 — 三工作树初始化</summary>

```bash
# 前置条件：项目根目录已克隆，Git 已初始化
# 执行效果：创建 hermes/codex/claude 三个工作树并注入环境变量

# 在项目根目录执行
mkdir -p worktrees

# 1. 创建工作树目录
for role in hermes codex claude; do
  mkdir -p "worktrees/${role}"
  echo "✓ 已创建 worktrees/${role}"
done

# 2. 逐个注入环境变量（在每个工作树中执行）
cd worktrees/hermes && bash ../../scripts/orca_setup_worktree.sh && cd ../..
cd worktrees/codex  && bash ../../scripts/orca_setup_worktree.sh && cd ../..
cd worktrees/claude && bash ../../scripts/orca_setup_worktree.sh && cd ../..

# 3. 验证
for role in hermes codex claude; do
  [ -f "worktrees/${role}/.env" ] && echo "✓ ${role} .env 已注入" || echo "✗ ${role} .env 缺失"
done
```

</details>

#### 环境配置 + Maris 接入文档生成

<details>
<summary>📋 一键复制 — 环境配置 + Maris接入文档生成</summary>

```bash
# 前置条件：三工作树已初始化
# 执行效果：配置舰队档案 + 生成 Maris 接入文档

# 1. 确保舰队就绪（端口+shim+配置）
source scripts/fleet_ensure.sh

# 2. 健康检查
bash scripts/fleet_health_check.sh

# 3. 生成 Maris 接入文档（待创建脚本）
bash scripts/maris_gen_readme.sh

# 4. 生成 fleet_exchange/README.md
cat > fleet_exchange/README.md << 'EOF'
# Fleet Exchange — 任务交换区

## 四级流转说明

| 目录 | 状态 | 写入者 | 读取者 |
|------|------|--------|--------|
| `incoming/` | 待接单 | Hermes/Maris | Codex |
| `doing/` | 执行中 | Codex | Claude Code |
| `done/` | 已完成 | Claude Code | CodeBuddy |
| `results/` | 归档输出 | CodeBuddy | 客户 |

## 任务卡格式

```json
{
  "task_id": "YYYYMMDD_HHMMSS_N",
  "task_type": "海报|画册|PPT|视频|文案",
  "source": "企业微信群|Maris|手动",
  "title": "任务简述",
  "description": "详细需求",
  "priority": "高|中|低",
  "deadline": "YYYY-MM-DD",
  "created_at": "YYYY-MM-DD HH:MM:SS"
}
```

## 触发方式

1. Maris 本地运行 `maris_dispatch.sh` 写入任务卡到 `incoming/`
2. Codex 监听 `incoming/` 自动接单
3. Claude Code 审核后移入 `done/`
4. CodeBuddy 终审后归档 `results/`
EOF
```

</details>

#### 代码提交推送

<details>
<summary>📋 一键复制 — 代码提交推送</summary>

```bash
# 前置条件：已完成修改
# 执行效果：原子化提交 + 推送到 CNB 云端

git add -A
git commit -m "feat: 描述具体改动内容"
git push origin main

# 验证推送成功
git log --oneline -1
```

</details>

### 2.3 场景三：Maris 投递任务

#### 普通文案任务

<details>
<summary>📋 一键复制 — 普通文案任务投递</summary>

```bash
# 前置条件：Maris 已部署，fleet_exchange/incoming/ 目录存在
# 执行效果：生成任务卡到 incoming/，触发 Codex 自动接单

# 使用 maris_dispatch.sh（待创建脚本）
bash scripts/maris_dispatch.sh \
  --type "文案" \
  --title "产品宣传文案" \
  --desc "为XX产品撰写500字宣传文案，风格：科技感" \
  --priority "中"

# 手动投递（脚本不可用时的替代方案）
TASK_ID=$(date +%Y%m%d_%H%M%S)_0
cat > "fleet_exchange/incoming/${TASK_ID}__Maris_产品宣传文案.md" << 'EOF'
# 任务卡：产品宣传文案

- 任务ID: TASK_ID
- 类型: 文案
- 优先级: 中
- 来源: Maris

## 需求
为XX产品撰写500字宣传文案，风格：科技感

## 要求
- 中文输出
- 不超过500字
- 包含产品亮点3条
EOF

echo "✓ 任务已投递到 incoming/"
```

</details>

#### 指定类型结构化任务

<details>
<summary>📋 一键复制 — 海报/视频/文案结构化任务投递</summary>

```bash
# 海报设计任务
bash scripts/maris_dispatch.sh \
  --type "海报" \
  --title "餐饮露营海报" \
  --desc "朋友圈餐饮海报，露营风格，尺寸1080x1920" \
  --priority "高" \
  --deadline "2026-08-10"

# 视频制作任务
bash scripts/maris_dispatch.sh \
  --type "视频" \
  --title "产品宣传短视频" \
  --desc "15秒产品宣传短视频，含配音字幕" \
  --priority "高" \
  --deadline "2026-08-12"

# 画册折页任务
bash scripts/maris_dispatch.sh \
  --type "画册" \
  --title "英文三折页设计" \
  --desc "企业介绍三折页，英文内容，A4尺寸" \
  --priority "中"

# 手动结构化投递（JSON格式）
TASK_ID=$(date +%Y%m%d_%H%M%S)_0
cat > "fleet_exchange/incoming/PKT_${TASK_ID}.json" << 'EOF'
{
  "task_id": "TASK_ID",
  "task_type": "海报",
  "source": "Maris",
  "title": "餐饮露营海报",
  "description": "朋友圈餐饮海报，露营风格，尺寸1080x1920",
  "priority": "高",
  "deadline": "2026-08-10",
  "created_at": "2026-08-06 12:00:00",
  "attachments": [],
  "style_reference": "露营风格"
}
EOF
```

</details>

### 2.4 场景四：云原生 DeepSeek V4 一键接入 ORCA 舰队

<details>
<summary>📋 一键复制 — CNB云原生 DeepSeek V4-Flash 接入</summary>

```bash
# 前置条件：已拥有 CNB 账号（cnb.cool），已创建仓库
# 执行效果：NPC 流水线激活 + 人设蒸馏 + 三级链式调度就绪

# ===== 方式一：Windows BAT 一键拉起 =====
cd E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts
一键拉起_CNB云原生DeepSeekV4Flash.bat

# ===== 方式二：PowerShell 一键拉起 =====
cd E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts
powershell -ExecutionPolicy Bypass -File 一键拉起_CNB云原生DeepSeekV4Flash.ps1

# ===== 方式三：手动配置 =====

# 步骤1：确认 .cnb.yml 流水线配置
# 文件位置：项目根目录/.cnb.yml
# 关键字段：
#   image: docker.cnb.cool/npc/mtga:latest  （免费社区镜像）
#   codex:  issue.comment@npc / pull_request.comment@npc
#   claude-code: issue.comment@npc / pull_request.comment@npc

# 步骤2：确认 .cnb/settings.yml 角色人设
# 文件位置：项目根目录/.cnb/settings.yml
# 关键字段：
#   npc.roles[].name: codex / claude-code
#   npc.roles[].prompt: 角色人设描述

# 步骤3：推送配置到云端
git add .cnb.yml .cnb/settings.yml
git commit -m "feat: 配置CNB云原生DeepSeek-V4-Flash NPC流水线"
git push origin main

# 步骤4：验证
# 在 CNB 仓库 Issue 中评论：@codex 你好，请列出你的核心能力
# 确认 NPC 正常响应
```

**参数配置项说明**：

| 配置项 | 位置 | 当前值 | 说明 |
|--------|------|--------|------|
| NPC 镜像 | `.cnb.yml` → `image` | `docker.cnb.cool/npc/mtga:latest` | 以鹅传鹅-Pro 社区免费镜像 |
| codex 触发 | `.cnb.yml` → `codex` | `issue.comment@npc` / `pull_request.comment@npc` | Issue/PR 评论触发 |
| claude-code 触发 | `.cnb.yml` → `claude-code` | `issue.comment@npc` / `pull_request.comment@npc` | Issue/PR 评论触发 |
| codex 人设 | `.cnb/settings.yml` → `npc.roles[].prompt` | 代码执行官人设 | 可自定义 |
| claude-code 人设 | `.cnb/settings.yml` → `npc.roles[].prompt` | 代码审计官人设 | 可自定义 |

**执行前后校验**：

| 校验项 | 校验命令 | 预期结果 |
|--------|----------|----------|
| 流水线配置存在 | `cat .cnb.yml \| grep mtga` | 输出镜像地址 |
| 角色人设存在 | `cat .cnb/settings.yml \| grep codex` | 输出 codex 角色 |
| 代码已推送 | `git log --oneline -1` | 最新提交包含配置 |
| NPC 响应 | Issue 评论 `@codex 你好` | NPC 回复 |

</details>

> **Maris 执行自检清单** ✅
> - [ ] 已确认可执行 `一键拉起_CNB云原生DeepSeekV4Flash.bat` 或 `.ps1`
> - [ ] 已确认 `.cnb.yml` 中镜像为 `docker.cnb.cool/npc/mtga:latest`
> - [ ] 已确认 `.cnb/settings.yml` 中 codex + claude-code 角色已配置
> - [ ] 已在 Issue 中测试 NPC 响应正常
> - [ ] 已确认 `fleet_exchange/incoming/` 目录可写入任务卡
> - [ ] 已确认 `maris_dispatch.sh` 可用或已使用手动投递方式

---

## 模块3：云原生 DeepSeek V4 适配专项答疑

### 3.1 CNB 云原生 DeepSeek V4 是否可被本地 Codex/Claude Code 直接调用？

**结论：不能直接调用。**

| 维度 | CNB 云原生 DeepSeek V4 | 本地 Codex/Claude Code |
|------|----------------------|----------------------|
| 运行环境 | CNB Docker 容器（云端） | Windows 本地进程 |
| 触发方式 | Issue/PR 评论 @NPC | 本地命令行/API |
| 文件访问 | 仅仓库内文件 | 全盘文件系统 |
| 网络访问 | 容器内网 | 本地网络 |

**两者关系**：云端 NPC 是本地 Agent 的"分身"，通过人设蒸馏（`.cnb/settings.yml`）映射核心逻辑，但无法 1:1 同步。本地 Agent 使用 Ollama/DeepSeek API 作为推理后端，云端 NPC 使用 CNB mtga 镜像内置的 DeepSeek-V4-Flash。

### 3.2 云原生云端推理 vs Ollama 本地部署资源占用对比

| 维度 | CNB 云原生 DeepSeek V4 | Ollama 本地 DeepSeek V4 |
|------|----------------------|----------------------|
| **内存占用** | **0 MB**（云端运行） | **2-4 GB**（模型加载到内存） |
| **磁盘占用** | **0 MB**（云端存储） | **4-7 GB**（模型文件下载到本地） |
| **带宽消耗** | 仅文本 API 流量（<1MB/次） | 首次下载模型 ~4GB，之后零带宽 |
| **GPU/显存** | **0 MB**（云端 GPU） | **0-8 GB**（可选 GPU 加速，否则 CPU 推理） |
| **CPU 占用** | **0%**（云端计算） | **30-100%**（推理时 CPU 满载） |
| **启动速度** | 即时（评论即触发） | 30-60秒（模型加载） |
| **推理速度** | 中等（网络延迟+排队） | 快（本地推理，无网络延迟） |
| **并发能力** | 多任务并行（云端） | 单任务串行（本地） |
| **多模态** | ❌（需旁路 MIMO） | ❌（需旁路 MIMO） |
| **免费政策** | 至 2026-12-31 | 永久免费（5小时配额刷新） |
| **适用场景** | 零占用、大仓库、长周期 | 离线、低延迟、高频调用 |

**选择建议**：
- **系统内存 > 16GB**：Ollama 本地 + CNB 云端双链路并行
- **系统内存 < 8GB**：仅用 CNB 云原生（零本地占用）
- **需要离线工作**：Ollama 本地
- **需要多任务并行**：CNB 云原生

### 3.3 对接配置详解

#### API 密钥填写入口

| 接入方式 | 密钥入口 | 是否需要密钥 |
|---------|---------|-------------|
| **CNB 云原生** | 无需密钥，通过 Issue/PR 评论 @NPC 触发 | ❌ 不需要 |
| **Ollama 本地** | `config/model_config.yaml` → `ollama.base_url` | ❌ 不需要（本地服务） |
| **MIMO V2.5** | `config/fleet_profiles/mimo.env` → `API_KEY=${MIMO_API_KEY}` | ✅ 需要环境变量 |
| **DeepSeek 官方 API** | `scripts/orca_connect_deepseek.sh` → 读取 `~/.hermes/config.yaml` | ✅ 需要充值 |

#### 「替我上班」开发者权限操作步骤

1. 打开 CNB 仓库页面（如 `https://cnb.cool/TJF19770107/orca-jiedan`）
2. 进入 Issue 或 PR 页面
3. 在评论输入框中，找到 **「替我上班」** 开关
4. 点击开启 → NPC 获得读写权限（可提交代码、推送分支）
5. **关闭时** → NPC 仅只读（只能回答问题，不能修改代码）

> ⚠️ 未开启「替我上班」时，NPC 只能阅读仓库代码和回复评论，**无法提交 PR、推送代码**。

#### 报错排查清单

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| **401 Unauthorized** | Codex `wire_api` 配置错误（应为 `chat` 而非 `responses`） | 检查 `~/.codex/config.toml`，确保 `wire_api = "chat"` |
| **203 Non-Authoritative** | 代理端口 15721/15730 未启动 | 运行 `bash scripts/fleet_ensure.sh` 或 `bash scripts/fleet_auto_ready.sh` |
| **429 Too Many Requests** | Ollama Cloud 配额耗尽（5小时刷新） | 切换到 CNB 云原生（`official_ds`），或等待配额刷新 |
| **503 Service Unavailable** | Ollama 服务未运行 | 启动 Ollama：`ollama serve`，或运行 `一键拉起_Ollama本地DeepSeekV4Flash.bat` |
| **超时（Timeout）** | 模型推理时间过长或网络不稳定 | 增大 `config/model_config.yaml` 中的 `timeout` 值（默认 120s） |
| **MODULE_NOT_FOUND** | Codex CLI shim 缺失或损坏 | 运行 `bash scripts/fleet_ensure.sh` 自动重建 shim |
| **NPC 无响应** | `.cnb.yml` 未配置或镜像错误 | 确认 `image: docker.cnb.cool/npc/mtga:latest`，确认 `codex`/`claude-code` 角色已绑定 |
| **NPC 只读** | 未开启「替我上班」模式 | 在 Issue/PR 评论框中开启「替我上班」开关 |

### 3.4 DeepSeek V4 vs MIMO V2.5 能力对比

| 业务维度 | CNB 云原生 DeepSeek V4-Flash | MIMO V2.5 Pro | 推荐 |
|---------|--------------------------|---------------|------|
| **量化接单** | ✅ 优秀（逻辑推理强、长上下文） | ✅ 良好（但上下文窗口较小） | **DeepSeek V4** |
| **视频生成** | ❌ 不支持（纯文本模型） | ✅ 支持视觉解析（可看视频截图） | **MIMO V2.5** |
| **海报设计** | ❌ 不支持（纯文本模型） | ✅ 原生多模态（可看参考图） | **MIMO V2.5** |
| **文案撰写** | ✅ 优秀（中文写作能力强） | ✅ 良好 | **DeepSeek V4** |
| **代码生成** | ✅ 优秀（代码理解能力强） | ⚠️ 一般 | **DeepSeek V4** |
| **图片理解** | ❌ 不支持 | ✅ 原生多模态 | **MIMO V2.5** |
| **成本** | 免费至 2026-12-31 | 免费至 2026-08-14 | **DeepSeek V4** |
| **本地资源** | 零占用 | ~50-100MB | **DeepSeek V4** |

**最佳实践**：
- **文本任务**（文案/代码/策略）→ DeepSeek V4-Flash
- **视觉任务**（海报/视频/图片）→ MIMO V2.5 Pro
- **自动旁路**：Ollama/云原生 DeepSeek 链路已配置视觉路由，图片任务自动旁路到 MIMO

> **Maris 执行自检清单** ✅
> - [ ] 已确认 CNB 云原生 DeepSeek V4 不能被本地 Agent 直接调用（通过 NPC 触发）
> - [ ] 已确认本地内存不足时优先使用 CNB 云原生（零占用）
> - [ ] 已确认「替我上班」模式对 NPC 读写权限的影响
> - [ ] 已确认文本任务用 DeepSeek V4、视觉任务用 MIMO V2.5
> - [ ] 已确认 401/203/429/超时等报错的排查方案

---

## 模块4：Maris ↔ CNB NPC ↔ CodeBuddy 跨主体协作链路

### 4.1 文字版流转逻辑

```
Maris 本地运行 maris_dispatch.sh
  → 写入任务卡到 fleet_exchange/incoming/
    → Codex NPC 执行层处理（从 incoming 读取 → 移入 doing）
      → Claude Code NPC 审核校验（从 doing 读取 → 移入 done）
        → CodeBuddy NPC 兜底终审（从 done 读取 → 归档 results 输出成品）
```

**详细步骤**：

1. **Maris 投递**：Maris 在本地运行 `maris_dispatch.sh`，将任务卡（JSON/MD）写入 `fleet_exchange/incoming/`
2. **Codex 接单**：Codex NPC 监听 `incoming/`，发现新任务后自动读取并执行代码生成，将任务移入 `doing/`
3. **Claude Code 审核**：Claude Code NPC 从 `doing/` 读取执行结果，进行代码审计、质量校验，审核通过后移入 `done/`
4. **CodeBuddy 终审**：CodeBuddy NPC 从 `done/` 读取审核结果，进行兜底终审，归档到 `results/` 输出最终交付物

### 4.2 横向流程图

```mermaid
flowchart LR
    subgraph Maris本地
        M[Maris Agent] -->|maris_dispatch.sh| A[fleet_exchange/incoming/]
    end

    subgraph Codex执行层
        A -->|读取任务卡| B[fleet_exchange/doing/]
        C[@npc/codex] -->|代码生成+脚本执行| B
    end

    subgraph ClaudeCode审核层
        B -->|执行结果| D[fleet_exchange/done/]
        E["@npc/claude-code"] -->|代码审计+质量校验| D
    end

    subgraph CodeBuddy终审层
        D -->|审核结果| F[fleet_exchange/results/]
        G[@CodeBuddy] -->|兜底终审+归档| F
    end

    F -->|交付物| H[客户/Obsidian归档]

    style M fill:#f9f,stroke:#333
    style C fill:#4CAF50,stroke:#333,color:#fff
    style E fill:#2196F3,stroke:#333,color:#fff
    style G fill:#FF9800,stroke:#333,color:#fff
```

### 4.3 角色权责表格

| 角色 | 定位 | 权责边界 | 禁止越权事项 |
|------|------|----------|-------------|
| **Maris** | 本地调度 Agent | ① 投递任务卡到 `incoming/` ② 监控任务流转状态 ③ 触发本地脚本执行 | ❌ 不直接修改 `doing/done/results` 中的文件 ❌ 不代替 Codex 执行代码 ❌ 不代替 Claude Code 审核 |
| **Codex（@npc/codex）** | 代码执行 NPC | ① 从 `incoming/` 读取任务并执行 ② 代码生成/脚本编写/功能实现 ③ 将执行结果移入 `doing/` | ❌ 不跳过审核直接写入 `done/` ❌ 不修改 `.cnb.yml` 或 `.cnb/settings.yml` ❌ 不删除 `incoming/` 中的原始任务卡 |
| **Claude Code（@npc/claude-code）** | 代码审计 NPC | ① 从 `doing/` 读取执行结果 ② 代码安全/性能/质量审计 ③ 审核通过后移入 `done/` | ❌ 不重新执行代码（仅审计） ❌ 不修改原始任务卡 ❌ 不直接归档到 `results/` |
| **CodeBuddy** | 终审 NPC | ① 从 `done/` 读取审核结果 ② 兜底终审+方案建议 ③ 归档到 `results/` 输出交付物 | ❌ 不代替 Codex 执行代码 ❌ 不代替 Claude Code 审计 ❌ 不删除 `done/` 中的审核记录 |

### 4.4 消息互通规则

#### @召唤格式规范

| 召唤对象 | 格式 | 触发位置 | 生效前提 |
|---------|------|---------|---------|
| Codex NPC | `@codex` 或 `@npc/codex(Codex)` | Issue/PR 评论 | `.cnb.yml` 中 `codex` 角色已绑定 |
| Claude Code NPC | `@claude-code` 或 `@npc/claude-code(Claude Code)` | Issue/PR 评论 | `.cnb.yml` 中 `claude-code` 角色已绑定 |
| CodeBuddy | `@CodeBuddy` | Issue/PR 评论 | 系统内置 NPC，无需配置 |
| 多 NPC 联动 | `@codex @claude-code` | Issue/PR 评论 | 两个角色均已配置 |

#### 消息同步至本地 ORCA 舰队的机制

| 方向 | 同步方式 | 延迟 |
|------|---------|------|
| 云端 → 本地 | `git pull` 或 `scripts/fleet_pull.sh` | 手动触发 |
| 本地 → 云端 | `git push` 或 `scripts/orca_push_all.sh` | 手动触发 |
| 双向自动 | G 盘镜像 + Obsidian 归档 | 近实时（G盘挂载时） |

#### 跨端延迟处理办法

| 场景 | 延迟原因 | 解决方案 |
|------|---------|---------|
| NPC 响应慢 | 流水线排队 | 等待 1-2 分钟，或检查 `.cnb.yml` 镜像是否正确 |
| 代码未同步 | 本地未 pull | 执行 `git pull origin main` |
| 任务卡丢失 | Git 未提交 | 确认 `git add + commit + push` 已执行 |
| 评论区无回复 | NPC 未触发 | 检查 @ 格式是否正确，检查「替我上班」是否开启 |

> **Maris 执行自检清单** ✅
> - [ ] 已理解四级流转：incoming → doing → done → results
> - [ ] 已确认自身权责：仅投递任务卡，不越权执行/审核
> - [ ] 已确认 @召唤格式：@codex / @claude-code / @CodeBuddy
> - [ ] 已确认云端→本地同步方式：git pull
> - [ ] 已确认 NPC 响应慢时的排查步骤

---

## 模块5：Maris 自主阅读适配设计

### 5.1 设计原则

1. **结构化分层**：每章节独立，可按需跳转
2. **关键路径/命令加粗高亮**：所有可执行命令用 `**加粗**` 标记
3. **自检清单**：每章节末尾增加「Maris 执行自检清单」
4. **一键复制**：所有命令放在折叠区域，标注「一键复制」标识

### 5.2 Maris 快速启动路径

**Maris 首次阅读本说明书时，按以下顺序执行**：

1. **模块1** → 确认目录路径正确（5分钟）
2. **模块2 场景2** → 初始化三工作树（3分钟）
3. **模块2 场景3** → 投递第一个测试任务（2分钟）
4. **模块2 场景4** → 接入 CNB 云原生 DeepSeek V4（5分钟）
5. **模块4** → 理解跨 NPC 协作链路（5分钟）

### 5.3 Maris 命令速查卡

| 操作 | 命令 |
|------|------|
| **投递任务** | `bash scripts/maris_dispatch.sh --type "文案" --title "xxx"` |
| **查看任务状态** | `ls fleet_exchange/incoming/ doing/ done/ results/` |
| **确认任务放行** | `bash scripts/confirm_task.sh <task_id>` |
| **完成归档** | `bash scripts/fleet_done.sh "<working_file>" "<结果文本>"` |
| **舰队健康检查** | `bash scripts/fleet_health_check.sh` |
| **舰队一键确保** | `source scripts/fleet_ensure.sh` |
| **拉起云原生** | `scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat` |
| **拉起Ollama** | `scripts\一键拉起_Ollama本地DeepSeekV4Flash.bat` |
| **拉起MIMO** | `bash scripts/one_click_mimo_v25.sh` |
| **推送代码** | `git add -A && git commit -m "xxx" && git push origin main` |
| **拉取代码** | `git pull origin main` |
| **@codex** | 在 Issue/PR 评论中输入 `@codex` |
| **@claude-code** | 在 Issue/PR 评论中输入 `@claude-code` |
| **@CodeBuddy** | 在 Issue/PR 评论中输入 `@CodeBuddy` |

> **Maris 执行自检清单** ✅
> - [ ] 已按快速启动路径执行完毕
> - [ ] 已使用命令速查卡完成至少一次任务投递
> - [ ] 已确认云端 NPC 响应正常

---

## 模块6：故障兜底附录

### 6.1 赛博书屋 v1.5 实测问题

| 问题 | 原因 | 解决方案 | 关联命令 |
|------|------|----------|---------|
| **curl 抓取视频号失效** | 视频号反爬机制，Cookie 过期 | ① 手动在浏览器中打开视频号页面 ② 复制完整 Cookie ③ 重新执行 curl | `scripts/netdisk_stream_reader.py` |
| **B站未登录抓取受限** | B站需登录才能访问高清视频 | ① 登录 B站 ② 导出 Cookie ③ 配置到 `~/.bilibili_cookies.txt` | `scripts/netdisk_stream_reader.py` |
| **仓颉蒸馏需 Agent 介入** | 仓颉（Cangjie）语言蒸馏流程复杂，需人工审核 | ① 使用 Codex NPC 生成蒸馏脚本 ② 人工审核后执行 | `@codex 帮我写仓颉蒸馏脚本` |

### 6.2 常见故障速查表

| 故障 | 症状 | 排查步骤 | 解决命令 |
|------|------|---------|---------|
| **Codex 401 错误** | Codex CLI 报 Unauthorized | ① 检查 `~/.codex/config.toml` ② 确认 `wire_api = "chat"` | `sed -i 's/wire_api = "responses"/wire_api = "chat"/' ~/.codex/config.toml` |
| **端口 15721/15730 不可达** | `curl` 报 Connection refused | ① 检查代理进程 ② 重启代理 | `bash scripts/fleet_ensure.sh` |
| **Codex CLI 不可用** | `codex --version` 报错 | ① 检查 shim ② 重建 shim | `bash scripts/fleet_ensure.sh` |
| **NPC 无响应** | Issue 评论 @NPC 后无回复 | ① 检查 `.cnb.yml` ② 检查镜像地址 ③ 确认角色绑定 | `cat .cnb.yml` |
| **NPC 只读** | NPC 无法提交代码 | 未开启「替我上班」 | 在 Issue/PR 评论框开启「替我上班」 |
| **Ollama 429 限流** | 请求被拒绝 | 5小时配额耗尽 | 切换到 CNB 云原生：`scripts/一键拉起_CNB云原生DeepSeekV4Flash.bat` |
| **Ollama 模型不存在** | `ollama list` 无 DeepSeek | 模型未下载 | `ollama pull deepseek-v4-flash` |
| **Git push 失败** | 推送被拒绝 | ① 检查远程分支 ② 拉取最新代码 | `git pull origin main && git push origin main` |
| **fleet_exchange 目录缺失** | 任务卡无法写入 | 目录未创建 | `bash scripts/创建目录结构.sh` |
| **MIMO API Key 过期** | MIMO 请求报 401 | 免费期至 2026-08-14 | 切换到 DeepSeek V4 或更新 MIMO API Key |

### 6.3 紧急恢复流程

<details>
<summary>📋 一键复制 — 全栈紧急恢复</summary>

```bash
# 适用场景：三 Agent 全部不可用，需紧急恢复
# 执行效果：一键恢复端口+shim+配置+健康检查

# 1. 一键确保舰队就绪
source scripts/fleet_ensure.sh

# 2. 自动恢复（含守护进程）
bash scripts/fleet_auto_ready.sh

# 3. 健康检查
bash scripts/fleet_health_check.sh

# 4. 如果仍然失败，尝试 Windows 自动恢复
# scripts\fleet_auto_restore.cmd

# 5. 最后手段：重启 Ollama
# 一键拉起_Ollama本地DeepSeekV4Flash.bat
```

</details>

> **Maris 执行自检清单** ✅
> - [ ] 已确认 curl 抓取视频号需手动更新 Cookie
> - [ ] 已确认 B站需登录 Cookie 才能抓取
> - [ ] 已确认仓颉蒸馏需 Agent 介入
> - [ ] 已掌握紧急恢复流程

---

## 附录A：Marvis 追加确认事项答复

### Q1：当前 NPC 流水线的推理基座是什么？

**当前状态**：NPC 流水线使用 **mtga 社区免费镜像**（`docker.cnb.cool/npc/mtga:latest`），即「以鹅传鹅-Pro」社区 NPC 镜像。该镜像内置 **DeepSeek-V4-Flash** 作为推理基座。

**与 MIMO V2.5 的关系**：本地 Agent（Codex CLI / Claude Code）的推理基座仍为 **MIMO V2.5 Pro**（通过 `config/model_config.yaml` 的 `active_backend` 配置），但云端 NPC 已切换到 DeepSeek-V4-Flash。

**claude-code 构建失败**：与模型切换无关。更可能的原因是：
1. `.cnb.yml` 中镜像地址错误（之前使用过 `default-codebuddy-npc`、`cnbcool/default-npc:latest` 等不稳定镜像）
2. 当前已修正为 `docker.cnb.cool/npc/mtga:latest`（社区免费镜像，稳定）

### Q2：如何从 MIMO 切换到 CNB 免费 DeepSeek V4-Flash？

**需要修改的文件和字段**：

#### 文件1：`.cnb.yml`（云端 NPC 流水线）

```yaml
# 当前配置（已正确，无需修改）
.npc_task: &npc_task
  - stages:
      - name: npc respond
        image: docker.cnb.cool/npc/mtga:latest   # ← 已是 DeepSeek-V4-Flash 镜像

codex:
  issue.comment@npc: *npc_task
  pull_request.comment@npc: *npc_task

claude-code:
  issue.comment@npc: *npc_task
  pull_request.comment@npc: *npc_task
```

**无需修改**，当前已配置为 DeepSeek-V4-Flash 镜像。

#### 文件2：`.cnb/settings.yml`（NPC 角色人设）

```yaml
# 当前配置（已正确，无需修改）
npc:
  roles:
    - name: codex
      prompt: |
        # 角色：Codex（代码执行官）
        ...
    - name: claude-code
      prompt: |
        # 角色：Claude Code（代码审计官）
        ...
```

**无需修改**，人设已配置。

#### 文件3：`config/model_config.yaml`（本地 Agent 推理后端）

```yaml
# 当前配置
active_backend: "ollama"   # ← 本地 Agent 使用 Ollama

# 如果要切换本地 Agent 到 DeepSeek V4-Flash，修改为：
active_backend: "openai"
openai:
  base_url: "https://api.deepseek.com/v1"   # DeepSeek 官方 API
  api_key: "${env:DEEPSEEK_API_KEY}"
  model: "deepseek-v4-flash"
```

**注意**：本地 Agent 切换到 DeepSeek 官方 API 需要 API Key 和充值。**推荐保持 Ollama 本地 + CNB 云原生双链路并行**。

#### 文件4：`config/fleet_profiles/official_ds.env`（云原生舰队档案）

```bash
# 当前配置（已正确，无需修改）
FLEET_NAME=official_ds
MODEL_NAME=deepseek-v4-flash
FREE_UNTIL=2026-12-31
```

**总结**：**云端 NPC 已切换到 DeepSeek-V4-Flash，无需额外修改**。本地 Agent 推荐保持 Ollama 本地链路不变。

### Q3：切换后对已有功能的影响？

**结论：零破坏性影响。**

| 功能模块 | 影响 | 说明 |
|---------|------|------|
| **fleet_exchange 任务流转** | ✅ 无影响 | 任务流转基于文件系统，与模型无关 |
| **三工作树初始化** | ✅ 无影响 | `orca_setup_worktree.sh` 仅注入环境变量，不涉及模型 |
| **Maris 调度** | ✅ 无影响 | `maris_dispatch.sh` 仅写入任务卡，不涉及模型 |
| **MIMO 视觉旁路** | ✅ 无影响 | 视觉路由配置独立于主模型（`official_ds.env` 中 `VISION_PROVIDER=mimo`） |
| **本地 Agent** | ✅ 无影响 | 本地 Agent 使用 Ollama/MIMO，不受云端 NPC 切换影响 |
| **降级策略** | ✅ 无影响 | `ollama_ds.env` 中 `FALLBACK_TARGET=official_ds`，降级到云原生 |

**原因**：云端 NPC（`.cnb.yml`）和本地 Agent（`config/model_config.yaml`）是**完全独立的两个系统**，切换云端 NPC 镜像不影响本地 Agent 配置。

---

## 附录B：版本信息

| 项目 | 版本/值 |
|------|--------|
| 说明书版本 | V1.0 |
| 关联 PR | PR#5 |
| 基座模型 | CNB 免费 DeepSeek-V4-Flash |
| NPC 镜像 | `docker.cnb.cool/npc/mtga:latest` |
| 免费期限 | 至 2026-12-31 |
| 本地 Agent 基座 | Ollama + MIMO V2.5 Pro |
| 仓库地址 | `https://cnb.cool/TJF19770107/orca-jiedan` |

---

*文档生成：Codex（代码执行官）| ORCA 舰队运维接入总说明书 V1.0 | 2026-08-06*
