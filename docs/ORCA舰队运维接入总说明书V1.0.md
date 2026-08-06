# ORCA 舰队运维接入总说明书 V1.0

> **版本**：V1.0 | **关联 PR**：#5 | **基座**：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> **仓库**：TJF19770107/orca-jiedan | **适用**：orca-jiedan 企业微信群定制接单项目
> **阅读主体**：Maris（自动化调度主体）+ 人类运维者
> **更新日期**：2026-08-06

---

## 目录

- [模块1：项目全局目录路径手册（本地+云端对照）](#模块1项目全局目录路径手册本地云端对照)
- [模块2：分场景一键拉起命令手册](#模块2分场景一键拉起命令手册)
- [模块3：云原生 DeepSeek V4 适配专项答疑](#模块3云原生-deepseek-v4-适配专项答疑)
- [模块4：Maris ↔ CNB NPC ↔ CodeBuddy 跨主体协作链路](#模块4maris--cnb-npc--codebuddy-跨主体协作链路)
- [模块5：Maris 自主阅读适配设计](#模块5maris-自主阅读适配设计)
- [模块6：故障兜底附录](#模块6故障兜底附录)

---

# 模块1：项目全局目录路径手册（本地+云端对照）

## 1.1 脚手架根路径

| 维度 | 路径 |
|------|------|
| **Windows 本地** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\` |
| **CNB 云端仓库** | `https://cnb.cool/TJF19770107/orca-jiedan` |
| **云端 Git** | `https://cnb.cool/TJF19770107/orca-jiedan.git` |

## 1.2 子目录与核心脚本路径对照

### 代码调度层

| 本地绝对路径 | 云端仓库相对路径 | 用途 |
|-------------|----------------|------|
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\` | `config/` | 配置文件（模型、默认、双实例） |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\default_config.yaml` | `config/default_config.yaml` | 项目默认配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\model_config.yaml` | `config/model_config.yaml` | 模型后端配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\dual_instance.yaml` | `config/dual_instance.yaml` | 双实例架构配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\orca\` | `config/orca/` | ORCA 角色系统提示词 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\orca\claude_system_prompt.md` | `config/orca/claude_system_prompt.md` | Claude Code 系统提示词 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\orca\codex_system_prompt.md` | `config/orca/codex_system_prompt.md` | Codex 系统提示词 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\orca\hermes_system_prompt.md` | `config/orca/hermes_system_prompt.md` | Hermes 系统提示词 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\fleet_profiles\` | `config/fleet_profiles/` | 舰队环境配置文件 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\fleet_profiles\mimo.env` | `config/fleet_profiles/mimo.env` | MIMO V2.5 Pro 配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\fleet_profiles\official_ds.env` | `config/fleet_profiles/official_ds.env` | CNB 云原生 DeepSeek 配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\fleet_profiles\ollama_ds.env` | `config/fleet_profiles/ollama_ds.env` | Ollama 本地 DeepSeek 配置 |

### 核心脚本层

| 本地绝对路径 | 云端仓库相对路径 | 用途 |
|-------------|----------------|------|
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat` | `scripts/一键拉起_CNB云原生DeepSeekV4Flash.bat` | **CNB 云原生一键拉起** |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\一键拉起_CNB云原生DeepSeekV4Flash.ps1` | `scripts/一键拉起_CNB云原生DeepSeekV4Flash.ps1` | CNB 云原生 PowerShell 版 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\一键拉起_Ollama本地DeepSeekV4Flash.bat` | `scripts/一键拉起_Ollama本地DeepSeekV4Flash.bat` | **Ollama 本地一键拉起** |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\一键拉起_Ollama本地DeepSeekV4Flash.ps1` | `scripts/一键拉起_Ollama本地DeepSeekV4Flash.ps1` | Ollama 本地 PowerShell 版 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\maris_dispatch.sh` | `scripts/maris_dispatch.sh` | **Maris 任务投递** |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\maris_gen_readme.sh` | `scripts/maris_gen_readme.sh` | **Maris 生成 README** |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\orca_init_worktrees.sh` | `scripts/orca_init_worktrees.sh` | **三工作树初始化** |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\orca_setup_worktree.sh` | `scripts/orca_setup_worktree.sh` | 工作树环境注入 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\orca_connect_deepseek.sh` | `scripts/orca_connect_deepseek.sh` | DeepSeek 接入配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\orca_project_startup.sh` | `scripts/orca_project_startup.sh` | 项目自动就绪检查 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\confirm_task.sh` | `scripts/confirm_task.sh` | 待确认任务放行 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\fleet_done.sh` | `scripts/fleet_done.sh` | 任务完成归档 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接顿项目\scripts\fleet_auto_ready.sh` | `scripts/fleet_auto_ready.sh` | 舰队自动就绪 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\fleet_health_check.sh` | `scripts/fleet_health_check.sh` | 舰队健康检查 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\fleet_restore.sh` | `scripts/fleet_restore.sh` | 舰队恢复 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\one_click_mimo_v25.sh` | `scripts/one_click_mimo_v25.sh` | MIMO V2.5 一键拉起 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\创建目录结构.sh` | `scripts/创建目录结构.sh` | 项目目录结构创建 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\创建目录结构.ps1` | `scripts/创建目录结构.ps1` | 项目目录结构创建（PS版） |

### 角色工作树

| 本地绝对路径 | 云端仓库相对路径 | 角色 |
|-------------|----------------|------|
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\worktrees\hermes\` | `worktrees/hermes/` | 大脑层（战略调度） |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\worktrees\codex\` | `worktrees/codex/` | 执行层（代码编写） |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\worktrees\claude\` | `worktrees/claude/` | 审核层（质量守护） |

### CNB 配置

| 本地绝对路径 | 云端仓库相对路径 | 用途 |
|-------------|----------------|------|
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.cnb.yml` | `.cnb.yml` | NPC 流水线配置 |
| `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.cnb\settings.yml` | `.cnb/settings.yml` | NPC 角色人设配置 |

## 1.3 fleet_exchange 四级任务流转路径

| 流转目录 | 本地绝对路径 | 云端仓库相对路径 | 用途 | 云端同步规则 |
|---------|-------------|----------------|------|------------|
| **incoming/** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\fleet_exchange\incoming\` | `fleet_exchange/incoming/` | 待接单任务 | `git push` 同步，NPC 可读 |
| **doing/** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\fleet_exchange\doing\` | `fleet_exchange/doing/` | 执行中任务 | `git push` 同步 |
| **done/** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\fleet_exchange\done\` | `fleet_exchange/done/` | 已完成任务 | `git push` 同步 |
| **results/** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\fleet_exchange\results\` | `fleet_exchange/results/` | 终审归档成品 | `git push` 同步，G盘镜像 |

> **云端同步规则**：所有 `fleet_exchange/` 下的文件变更通过 `git add → git commit → git push` 同步到云端。NPC 通过读取仓库文件获取任务状态。本地 G 盘镜像由 `fleet_done.sh` 自动同步。

## 1.4 Maris 标准件 + 配套文档精准路径索引

| 标准件/文档 | 本地绝对路径 | 云端仓库相对路径 |
|-----------|-------------|----------------|
| **maris_dispatch.sh** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\maris_dispatch.sh` | `scripts/maris_dispatch.sh` |
| **maris_gen_readme.sh** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\maris_gen_readme.sh` | `scripts/maris_gen_readme.sh` |
| **orca_init_worktrees.sh** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\orca_init_worktrees.sh` | `scripts/orca_init_worktrees.sh` |
| **fleet_exchange/README.md** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\fleet_exchange\README.md` | `fleet_exchange/README.md` |
| **Maris调度接入说明.md** | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\docs\Maris调度接入说明.md` | `docs/Maris调度接入说明.md` |

### Maris 执行自检清单 — 模块1

- [ ] 能定位脚手架根路径（本地 E 盘 + CNB 云端）
- [ ] 能找到 fleet_exchange 四级目录的本地与云端位置
- [ ] 能找到 5 个 Maris 标准件的精准路径
- [ ] 知道云端同步规则：`git push` 即同步

---

# 模块2：分场景一键拉起命令手册

## 2.1 脚手架批量部署场景

### 2.1.1 单项目部署（orca-jiedan）

<details>
<summary>📋 一键复制 — Windows 本地部署</summary>

```batch
:: 一键复制 ↓
cd /d E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
scripts\一键拉起_Ollama本地DeepSeekV4Flash.bat
```

**前置条件**：Ollama 已安装，磁盘剩余 ≥10GB
**执行效果**：启动本地 Ollama + Codex + Claude Code 三层链路
**报错排查**：Ollama 未找到 → 安装 https://ollama.com/download/windows

</details>

<details>
<summary>📋 一键复制 — CNB 云端部署</summary>

```batch
:: 一键复制 ↓
cd /d E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat
```

**前置条件**：CNB 仓库已创建，`.cnb.yml` 已配置
**执行效果**：蒸馏人设到云端 NPC，打开 CNB 仓库页面
**报错排查**：`.cnb/settings.yml` 不存在 → 脚本自动提示

</details>

### 2.1.2 多项目批量部署

<details>
<summary>📋 一键复制 — PowerShell 全量部署（6仓）</summary>

```powershell
# 一键复制 ↓
$repos = @("orca-jiedan","orca-wangpan","orca-xianyu","orca-quant-jiasheng","orca-quant-binance","orca")
foreach ($repo in $repos) {
    Write-Host "部署 $repo ..." -ForegroundColor Cyan
    $projectDir = "E:\龙虾AI主控中心\我的AI分身\$repo"
    if (Test-Path "$projectDir\scripts\一键拉起_CNB云原生DeepSeekV4Flash.ps1") {
        & "$projectDir\scripts\一键拉起_CNB云原生DeepSeekV4Flash.ps1"
    } else {
        Write-Host "  ⚠ $repo 未找到一键拉起脚本" -ForegroundColor Yellow
    }
}
```

**前置条件**：各仓库已 clone 到本地
**执行效果**：逐一蒸馏人设并打开 CNB 仓库
**报错排查**：某仓库跳过 → 检查该仓库是否已部署脚本

</details>

### 2.1.3 全量默认部署

<details>
<summary>📋 一键复制 — 脚手架同步全项目</summary>

```bash
# 一键复制 ↓
bash scripts/sync_scaffold_to_all.sh
```

**前置条件**：当前项目脚手架已更新到最新版本
**执行效果**：将脚手架变更同步到全部 8 个 ORCA 项目
**报错排查**：权限不足 → 检查 Git 凭证

</details>

## 2.2 项目初始化场景

### 2.2.1 三工作树初始化

<details>
<summary>📋 一键复制 — 三工作树初始化 + 环境注入</summary>

```bash
# 一键复制 ↓
# 步骤1：初始化三工作树
bash scripts/orca_init_worktrees.sh

# 步骤2：各工作树环境注入
cd worktrees/hermes && bash ../../scripts/orca_setup_worktree.sh
cd ../../worktrees/codex && bash ../../scripts/orca_setup_worktree.sh
cd ../../worktrees/claude && bash ../../scripts/orca_setup_worktree.sh

# 步骤3：验证
for role in hermes codex claude; do
  echo "[$role] $(cat worktrees/$role/.env | grep AGENT_ROLE)"
done
```

**前置条件**：Git 仓库已初始化，`main` 分支存在
**执行效果**：创建 `hermes/brain`、`codex/executor`、`claude/reviewer` 分支，注入 `.env`
**报错排查**：分支已存在 → 脚本自动跳过

</details>

### 2.2.2 环境配置 + Maris 接入文档生成

<details>
<summary>📋 一键复制 — 环境配置 + 文档生成</summary>

```bash
# 一键复制 ↓
# 步骤1：生成 fleet_exchange 状态 README
bash scripts/maris_gen_readme.sh

# 步骤2：验证目录结构
bash scripts/fleet_health_check.sh

# 步骤3：创建业务目录结构
bash scripts/创建目录结构.sh
```

**前置条件**：三工作树已初始化
**执行效果**：fleet_exchange 状态就绪，业务目录创建完成
**报错排查**：`fleet_health_check.sh` 报错 → 按提示修复

</details>

### 2.2.3 代码提交推送

<details>
<summary>📋 一键复制 — 提交推送</summary>

```bash
# 一键复制 ↓
git add -A
git commit -m "chore: 初始化三工作树 + Maris 接入标准件"
git push origin main
```

**前置条件**：Git 远程仓库可访问
**执行效果**：变更推送到 CNB 云端
**报错排查**：`push rejected` → `git pull --rebase origin main` 后重试

</details>

## 2.3 Maris 投递任务场景

### 2.3.1 普通文案任务

<details>
<summary>📋 一键复制 — 文案任务投递</summary>

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --type 文案 --title "朋友圈餐饮海报文案" --desc "露营风格，5条文案，带emoji"
```

**前置条件**：`fleet_exchange/incoming/` 目录存在
**执行效果**：任务卡写入 `fleet_exchange/incoming/`
**报错排查**：目录不存在 → `mkdir -p fleet_exchange/incoming`

</details>

### 2.3.2 指定类型结构化任务

<details>
<summary>📋 一键复制 — 海报任务</summary>

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --type 海报 --title "摇滚风演出海报" --desc "A3尺寸，黑底金字，含乐队名和日期"
```

</details>

<details>
<summary>📋 一键复制 — 视频任务</summary>

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --type 视频 --title "产品宣传短视频" --desc "30秒，口播+字幕，MP4格式"
```

</details>

### 2.3.3 从文件投递任务

<details>
<summary>📋 一键复制 — 文件投递</summary>

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --file /tmp/my_task_card.md
```

**前置条件**：任务卡文件存在
**执行效果**：文件复制到 `fleet_exchange/incoming/`
**报错排查**：文件不存在 → 检查路径

</details>

## 2.4 云原生 DeepSeek V4 模型一键接入 ORCA 舰队

<details>
<summary>📋 一键复制 — CNB 云原生 DeepSeek V4 接入</summary>

```bash
# 一键复制 ↓
# 方式1：Windows 批处理（推荐）
cd /d E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
scripts\一键拉起_CNB云原生DeepSeekV4Flash.bat

# 方式2：PowerShell
.\scripts\一键拉起_CNB云原生DeepSeekV4Flash.ps1

# 方式3：Linux/Git Bash
bash scripts/fleet_start_official_ds.sh
```

</details>

### 参数配置项

| 配置项 | 位置 | 值 | 说明 |
|--------|------|-----|------|
| **NPC 镜像** | `.cnb.yml` → `image` | `docker.cnb.cool/npc/mtga:latest` | 免费社区镜像 |
| **NPC 角色人设** | `.cnb/settings.yml` → `npc.roles` | codex / claude-code | 两个 NPC 角色 |
| **模型基座** | `config/fleet_profiles/official_ds.env` | `MODEL_NAME=deepseek-v4-flash` | V4 Flash MoE |
| **视觉旁路** | `config/fleet_profiles/official_ds.env` | `VISION_PROVIDER=mimo` | 图片走 MIMO |

### 执行前后校验

| 校验项 | 命令 | 预期结果 |
|--------|------|---------|
| `.cnb.yml` 存在 | `cat .cnb.yml` | 包含 `codex:` 和 `claude-code:` 配置 |
| `.cnb/settings.yml` 存在 | `cat .cnb/settings.yml` | 包含 codex + claude-code 人设 |
| CNB 仓库可访问 | 浏览器打开 `https://cnb.cool/TJF19770107/orca-jiedan` | 仓库页面正常 |
| NPC 可触发 | Issue 中输入 `@npc/codex 你好` | NPC 回复 |
| 免费期限 | 查看 `VERSION.md` | `base_model_valid_until: 2026-12-31` |

### Maris 执行自检清单 — 模块2

- [ ] 能执行单项目本地部署（`一键拉起_Ollama本地DeepSeekV4Flash.bat`）
- [ ] 能执行 CNB 云端部署（`一键拉起_CNB云原生DeepSeekV4Flash.bat`）
- [ ] 能初始化三工作树（`orca_init_worktrees.sh`）
- [ ] 能投递任务（`maris_dispatch.sh`）
- [ ] 能生成状态报告（`maris_gen_readme.sh`）
- [ ] 知道 DeepSeek V4 参数配置项和校验方式

---

# 模块3：云原生 DeepSeek V4 适配专项答疑

## 3.1 CNB 云原生 DeepSeek V4 是否可直接被本地 Codex/Claude Code 调用？

**结论：不能直接调用。**

| 维度 | 说明 |
|------|------|
| **CNB 云原生 NPC** | 运行在 CNB Docker 容器内，通过 Issue/PR 评论 `@` 触发，**不暴露 API 端口**给本地 |
| **本地 Codex/Claude Code** | 通过本地 Ollama（`127.0.0.1:11434`）或 MIMO API 调用，**无法直连 CNB 容器** |
| **正确用法** | 本地用 Ollama DeepSeek V4 Flash；云端用 CNB NPC；两者通过 Git 仓库（`fleet_exchange/`）桥接 |

> **一句话总结**：本地走 Ollama，云端走 CNB NPC，两者通过 Git 仓库文件桥接，**不是 API 级别的直连**。

## 3.2 云原生云端推理 vs Ollama 本地部署 — 资源占用差异

| 资源维度 | CNB 云原生 DeepSeek V4 | Ollama 本地 DeepSeek V4 Flash |
|---------|----------------------|-------------------------------|
| **内存（RAM）** | 0（云端消耗） | ~8GB（模型加载） |
| **磁盘** | 0（云端存储） | ~8GB（模型文件） |
| **GPU 显存** | 0（云端算力） | 推荐 8GB+（无 GPU 可 CPU 推理，极慢） |
| **网络带宽** | 仅 Git 仓库同步 | 仅首次拉取模型 ~8GB |
| **CPU 占用** | 0（云端计算） | 推理时 100%（CPU 模式） |
| **持续性** | 事件触发（每次评论独立） | 常驻后台进程 |
| **成本** | 免费（至 2026-12-31） | 免费（本地算力） |
| **响应延迟** | 冷启动 30-60s，热缓存 5-10s | 本地推理 2-10s |

> **选择建议**：日常开发/实时任务 → 本地 Ollama；PR 审查/Issue 问答/远程调度 → CNB 云端

## 3.3 对接配置

### 3.3.1 API 密钥填写入口

| 链路 | 密钥 | 填写位置 | 说明 |
|------|------|---------|------|
| **CNB 云原生** | 不需要 | — | mtga 镜像内置，零配置 |
| **MIMO V2.5** | `MIMO_API_KEY` | 环境变量或 `~/.hermes/config.yaml` | 视觉旁路必需 |
| **Ollama 本地** | 不需要 | — | 本地运行，无 API Key |
| **DeepSeek 官方** | `DEEPSEEK_API_KEY` | 环境变量 | 可选，用于官方 API |

### 3.3.2 权限勾选要求

| 操作 | 权限要求 | 设置位置 |
|------|---------|---------|
| NPC 读取仓库 | 自动（仓库成员即可） | CNB 仓库设置 |
| NPC 写入 Issue/PR | **开启「替我上班」模式** | Issue/PR 页面右上角 → 替我上班 |
| NPC 提交代码 | **开启「替我上班」+ 写权限** | 仓库 Settings → 协作者 |

### 3.3.3 「替我上班」开发者权限操作步骤

1. 打开 CNB 仓库 → Issues（或 Pull Requests）
2. 找到目标 Issue/PR
3. 点击右上角 **「替我上班」** 按钮（或「替我上啦」）
4. 确认 NPC 可代替你执行操作
5. 验证：在评论区输入 `@npc/codex 你好`，NPC 应回复

### 3.3.4 报错排查清单

| 报错 | 原因 | 解决方案 |
|------|------|---------|
| **401 Unauthorized** | NPC 未获得写权限 | 开启「替我上班」模式 |
| **403 Forbidden** | 仓库权限不足 | 检查仓库 Settings → 协作者权限 |
| **203 Non-Authoritative** | NPC 镜像冷启动中 | 等待 30-60s 后重试 |
| **Timeout** | NPC 执行超时 | 简化任务，减少单次执行量 |
| **429 Too Many Requests** | Ollama Cloud 配额耗尽 | 切换到 CNB 云原生链路 |
| **NPC 无回复** | `.cnb.yml` 配置错误 | 检查 `codex:` 和 `claude-code:` 配置 |
| **NPC 回复乱码** | 镜像编码问题 | 确认使用 `mtga:latest` 镜像 |

## 3.4 DeepSeek V4 vs MIMO V2.5 能力差异对比

| 能力维度 | DeepSeek V4-Flash | MIMO V2.5-Pro | 优势方 |
|---------|-------------------|---------------|--------|
| **量化接单** | 优秀：长上下文理解、策略生成、代码编写 | 良好：短文本策略、数值计算 | DeepSeek V4 |
| **视频生成** | 不支持：无原生视频生成能力 | 不支持：仅文本+图片理解 | 两者均需外部工具 |
| **海报设计** | 不支持：无原生识图能力 | **优秀**：图片理解、视觉推理、风格识别 | MIMO V2.5 |
| **文案生成** | **优秀**：长文案、结构化输出、创意 | 良好：短文案、社交媒体 | DeepSeek V4 |
| **代码编写** | **优秀**：多语言、长上下文、逻辑推理 | 良好：简单脚本 | DeepSeek V4 |
| **图片理解** | 不支持 | **优秀**：OCR、场景识别、K线图 | MIMO V2.5 |
| **成本** | 免费（至 2026-12-31） | 免费（至 2026-08-14） | DeepSeek V4 |
| **上下文长度** | 128K | 32K | DeepSeek V4 |

> **最佳实践**：DeepSeek V4 为主力（文本/代码/策略），MIMO V2.5 为视觉旁路（图片/海报/OCR），两者互补。

### Maris 执行自检清单 — 模块3

- [ ] 知道 CNB 云原生 NPC 不能被本地直连（通过 Git 仓库桥接）
- [ ] 知道本地 Ollama 需 ~8GB 内存/磁盘，CNB 云端零占用
- [ ] 知道 CNB 云原生不需要 API Key，MIMO 需要 `MIMO_API_KEY`
- [ ] 知道「替我上班」模式是 NPC 写入权限的必要条件
- [ ] 知道 401/203/Timeout 的排查方案
- [ ] 知道 DeepSeek V4 适合文本/代码，MIMO 适合图片/视觉

---

# 模块4：Maris ↔ CNB NPC ↔ CodeBuddy 跨主体协作链路

## 4.1 文字版流转逻辑

```
Maris 本地运行 maris_dispatch.sh → 写入任务卡到 incoming/
    ↓
Codex 执行层处理 → 移入 doing/
    ↓
Claude Code 审核校验 → 移入 done/
    ↓
CodeBuddy 兜底终审 → 归档 results/ 输出成品
```

**详细步骤**：

1. **Maris** 本地运行 `scripts/maris_dispatch.sh`，将任务卡写入 `fleet_exchange/incoming/`
2. **Codex**（本地或 NPC）从 `incoming/` 取任务，执行代码/生成物料，将任务文件移入 `doing/`
3. **Claude Code**（本地或 NPC）从 `doing/` 取产出，审核校验（代码质量/合规/安全），通过后移入 `done/`
4. **CodeBuddy**（CNB 系统NPC）从 `done/` 终审，确认无遗漏，归档到 `results/`，同时镜像到 G 盘
5. **Maris** 可通过 `maris_gen_readme.sh` 查看流转状态

## 4.2 横向流程图

```
┌──────────┐    maris_dispatch.sh    ┌────────────┐    Codex 执行    ┌──────────┐
│  Maris   │ ──────────────────────→ │  incoming/ │ ──────────────→ │  doing/  │
│ (调度中枢)│                         │  (待接单)   │                  │ (执行中)  │
└──────────┘                         └────────────┘                  └──────────┘
     │                                                                     │
     │  maris_gen_readme.sh                                               │
     │  (状态监控)                                                          │
     ↓                                                                     ↓
┌──────────┐    CodeBuddy 终审      ┌────────────┐    Claude 审核     ┌──────────┐
│ results/ │ ←──────────────────── │   done/    │ ←────────────── │  doing/  │
│ (成品归档)│                        │  (已完成)   │                  │ (审核中)  │
└──────────┘                        └────────────┘                  └──────────┘
     │
     ↓
┌──────────┐
│  G盘镜像  │  fleet_done.sh 自动同步
│  Obsidian│  知识库归档
└──────────┘
```

**角色与脚本对应**：

| 流转节点 | 触发主体 | 对应脚本 | 触发条件 |
|---------|---------|---------|---------|
| → incoming/ | Maris | `maris_dispatch.sh` | 手动或自动投递 |
| → doing/ | Codex | 本地 Codex CLI 或 `@npc/codex` | incoming/ 有新任务 |
| → done/ | Claude Code | 本地 Claude CLI 或 `@npc/claude-code` | doing/ 有待审核产出 |
| → results/ | CodeBuddy | `fleet_done.sh` 或 `@CodeBuddy` | done/ 有已审核产出 |

## 4.3 角色权责表格

| 角色 | 权责边界 | 可执行操作 | 禁止越权事项 |
|------|---------|-----------|-------------|
| **Maris** | 调度中枢：任务投递、状态监控、归档管理 | 投递任务到 `incoming/`、刷新 README、触发 G 盘镜像 | 禁止直接修改 `doing/` 内容、禁止跳过审核直接归档 |
| **Codex** | 执行层：代码编写、脚本执行、物料生成 | 从 `incoming/` 取任务、执行写入 `doing/`、修复代码 | 禁止自审自通过、禁止直接移入 `done/` |
| **Claude Code** | 审核层：代码审计、质量守护、合规检查 | 从 `doing/` 取产出、审核校验、移入 `done/` | 禁止修改产出内容（仅审核/退回）、禁止直接归档 |
| **CodeBuddy** | 终审层：兜底终审、归档、PR 提交 | 从 `done/` 终审、归档 `results/`、提交 PR | 禁止重新执行任务、禁止修改原始产出 |

## 4.4 消息互通规则

### 4.4.1 @召唤格式规范

| 召唤对象 | 格式 | 生效前提 | 适用场景 |
|---------|------|---------|---------|
| Codex NPC | `@npc/codex` | CNB Issue/PR 评论区 | 代码执行、脚本编写 |
| Claude Code NPC | `@npc/claude-code` | CNB Issue/PR 评论区 | 代码审计、质量审查 |
| CodeBuddy | `@CodeBuddy` | CNB Issue/PR 评论区 | 终审、方案建议 |
| 全部 NPC | `@npc/codex @npc/claude-code @CodeBuddy` | CNB Issue/PR 评论区 | 联合调度 |

### 4.4.2 触发生效前提

1. **仓库已配置 `.cnb.yml`**：包含 `codex:` 和 `claude-code:` NPC 流水线
2. **仓库已配置 `.cnb/settings.yml`**：包含 NPC 角色人设
3. **已开启「替我上班」模式**：NPC 才能写入 Issue/PR
4. **评论在 Issue/PR 中发布**：普通代码评论不触发 NPC

### 4.4.3 消息同步至本地 ORCA 舰队

| 方向 | 机制 | 延迟 |
|------|------|------|
| 云端 → 本地 | `git pull origin main` | 手动或定时（5min cron） |
| 本地 → 云端 | `git push origin main` | 实时 |
| NPC 产出 → 本地 | `fleet_exchange/results/` + `git pull` | 手动或定时 |

### 4.4.4 跨端延迟处理办法

| 延迟场景 | 处理办法 |
|---------|---------|
| NPC 回复慢（>60s） | 等待冷启动完成，后续响应更快 |
| git push 冲突 | `git pull --rebase origin main` 后重试 |
| 本地文件未同步 | `bash scripts/fleet_pull.sh` 强制拉取 |
| G 盘镜像失败 | 检查 G 盘挂载，手动 `cp -r` |

### Maris 执行自检清单 — 模块4

- [ ] 理解四级流转：incoming → doing → done → results
- [ ] 知道每个流转节点的触发主体和对应脚本
- [ ] 知道四角色的权责边界和禁止越权事项
- [ ] 知道 @召唤格式和生效前提
- [ ] 知道「替我上班」是 NPC 写入权限的必要条件
- [ ] 知道跨端延迟处理办法

---

# 模块5：Maris 自主阅读适配设计

## 5.1 结构化分层

本说明书按六大模块组织，每个模块包含：
- **路径表格**：本地 + 云端双向对照
- **命令清单**：`<details>` 折叠，标注「一键复制」
- **自检清单**：每章节末尾，Maris 读完可逐项自检

## 5.2 关键路径/命令高亮

- **加粗**：关键路径、关键命令、关键结论
- **代码块**：所有可执行命令
- **表格**：对照信息、配置项、报错排查

## 5.3 Maris 全局执行自检清单

完成全文阅读后，Maris 应能：

- [ ] 定位脚手架根路径（本地 E 盘 + CNB 云端）
- [ ] 找到 fleet_exchange 四级目录的本地与云端位置
- [ ] 找到 5 个 Maris 标准件的精准路径
- [ ] 执行单项目本地部署（`一键拉起_Ollama本地DeepSeekV4Flash.bat`）
- [ ] 执行 CNB 云端部署（`一键拉起_CNB云原生DeepSeekV4Flash.bat`）
- [ ] 初始化三工作树（`orca_init_worktrees.sh`）
- [ ] 投递任务（`maris_dispatch.sh --type 文案 --title "xxx" --desc "xxx"`）
- [ ] 生成状态报告（`maris_gen_readme.sh`）
- [ ] 知道 CNB 云原生 NPC 不能被本地直连
- [ ] 知道 DeepSeek V4 适合文本/代码，MIMO 适合图片/视觉
- [ ] 知道「替我上班」是 NPC 写入权限的必要条件
- [ ] 知道四级流转：incoming → doing → done → results
- [ ] 知道四角色权责边界和禁止越权事项
- [ ] 知道 401/203/Timeout 的排查方案
- [ ] 独立完成任务投递、模型接入、跨 NPC 协作全流程

---

# 模块6：故障兜底附录

## 6.1 赛博书屋 v1.5 实测问题

| 问题 | 影响范围 | 解决方案 | 关联命令 |
|------|---------|---------|---------|
| **curl 抓取视频号失效** | 视频号内容无法下载 | 使用 `yt-dlp` 替代 `curl`，添加 `--cookies-from-browser` 参数 | `yt-dlp --cookies-from-browser chrome <URL>` |
| **B 站未登录抓取受限** | B 站视频/图文无法完整获取 | 使用 `yt-dlp --cookies-from-browser chrome` 传入登录态 | `yt-dlp --cookies-from-browser chrome <B站URL>` |
| **仓颉蒸馏需 Agent 介入** | 仓颉模型输出需人工校验 | 配置 `confirm_task.sh` 放行机制，人工审核后自动继续 | `bash scripts/confirm_task.sh <task_id>` |

## 6.2 通用故障排查

| 故障现象 | 可能原因 | 排查步骤 | 解决方案 |
|---------|---------|---------|---------|
| Ollama 启动失败 | 未安装 / 路径异常 | `which ollama` 或搜索安装目录 | 安装 https://ollama.com/download |
| Codex CLI 不可用 | shim 缺失 / npm 路径错误 | `codex --version` | `bash scripts/orca_project_startup.sh` 自动修复 |
| 代理端口 15721/15730 不通 | 代理脚本未运行 | `netstat -ano \| grep 15721` | `bash scripts/fleet_auto_restore.cmd` |
| git push 失败 | 凭证过期 / 网络问题 | `git remote -v` → 测试连通 | 更新 `.git/.git-credentials` |
| NPC 无回复 | `.cnb.yml` 配置错误 | 检查 `codex:` 和 `claude-code:` 配置 | 参照本文模块2.4 参数配置项 |
| MIMO API 报错 | API Key 过期 | `echo $MIMO_API_KEY` | 重新申请 Key |
| G 盘未挂载 | 盘符未分配 | `ls G:/` | 手动挂载或检查磁盘管理 |
| 磁盘空间不足 | 模型文件过大 | `df -h` | 清理旧模型或使用 CNB 云端链路 |

## 6.3 紧急恢复命令

<details>
<summary>📋 一键复制 — 紧急恢复</summary>

```bash
# 一键复制 ↓
# 完整恢复（含快照）
bash scripts/fleet_restore.sh --snapshot

# 只检查不修复
bash scripts/fleet_health_check.sh

# Windows 一键恢复
scripts\fleet_auto_restore.cmd

# 三引擎状态
bash scripts/fleet_auto_ready.sh

# 代理端口拉起
bash scripts/orca_project_startup.sh
```

</details>

## 6.4 版本关联

| 版本 | 日期 | 关联 PR | 说明 |
|------|------|--------|------|
| V1.0 | 2026-08-06 | PR#5 | 初始版本，基座切换 DeepSeek-V4-Flash |

---

> **文档版本**：V1.0
> **基座标识**：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> **维护者**：龙虾AI主控中心 · Marvis 运维组
> **四化闭环**：标准化 → 流程化 → 自动化 → 智能化
