# 龙虾五步法案例 · ORCA 工作树可视化配置

> 案例来源：企业微信群定制接单项目 · ORCA 多 Agent 工作树可视化标注配置指令
> 对应规范：全域模板协议 #290《ORCA 多 Agent 工作树自动填充配置规范》
> 五步法锚点：lobster_task_standard_workflow_v2.7「ORCA 多 Agent 工作树配置子流程」

---

## 1. 任务背景

为已搭建三层舰队架构（`hermes/brain` · `codex/executor` · `claude/reviewer`）的项目，
制作 **3 张 ORCA 设置界面的可视化标注指南**（逐框箭头 + 填写内容），并沉淀「自动填充配置规范」，
使后续新建工作树可零手动输入、一键加载龙虾五步法环境。

---

## 2. 五步法逐步映射

### Step 1 · 精准备份（环境复制）
- 新建工作树时注入标准设置脚本（Step1 环境备份）
- 脚本负责：复制 `config/default_config.yaml` + `.env` → 工作树；`pip install -r requirements.txt`；
  `mklink /D obsidian_link` 绑定 G 盘 Obsidian；调用 `scripts/skill_auto_register.py` 注册当前分支技能
- 路径全部经环境变量解析，禁止写死 C 盘

### Step 2 · 根因诊断（规范校验）
- 校验分支名 ∈ 三层 Agent 分支
- 校验「工作树位置」已替换为 E 盘模板（非 ORCA 默认 C 盘）
- 校验三层目录与 Agent 权限隔离就位

### Step 3 · 无命令不修复（自动执行）
- 「何时跑步」＝【默认运行】，新建工作树自动执行设置脚本
- 「等待设置完成后再启动智能体」＝开启
- 仅修改全域模板核心规则 / 创建新工作树授权节点时，才请求人工确认

### Step 4 · 验证校验（生效检测）
- 检测 `obsidian_link` 软链指向 `OBSIDIAN_MAIN`
- 检测 `skill_registry.json` 已追加当前分支技能（幂等跳过）
- 检测 `requirements.txt` 依赖安装成功
- 失败回退：重跑设置脚本，不手动 patch 环境

### Step 5 · 沉淀归档（Step5 闭环）
- 注入标准存档脚本（Step5 沉淀），删除工作树前自动执行
- 备份 `logs/` 至 `LOBSTER_BACKUP_ROOT` → `git commit`
- 同步私有 Git 仓库 + Obsidian 双库，支持溯源回滚
- 沉淀本案例文档

---

## 3. 交付物清单

| 文件 | 说明 |
|------|------|
| `docs/可视化标注指南.html` | 3 页 ORCA 设置界面 SVG 箭头标注图（带逐框填写指引） |
| `docs/可视化标注指南.md` | 同上的 Markdown 版 + 手动对照表 |
| `docs/ORCA工作树自动填充配置规范.md` | 协议 #290 全文：脚本/路径/开关/变量映射 |
| `scripts/skill_auto_register.py` | 分支技能自动注册器（幂等，写入主仓库总 registry） |
| `.env` | 项目环境变量模板（OBSIDIAN_MAIN / LOBSTER_BACKUP_ROOT 等，无密钥） |
| `skill_registry.json` | 已含 `orca_codex_executor` 等三层技能条目（实测注册成功） |

---

## 4. 实测验证记录

- `skill_auto_register.py` 在 `codex/executor` 工作树运行 → `[OK] 已注册分支 codex/executor → 技能 orca_codex_executor`
- 二次运行 → `[OK] 分支 codex/executor 技能已注册，跳过`（幂等）
- 主仓库 `skill_registry.json` 条目：`knowledge_extraction_from_cloud_drive` / `orca_multi_agent_fleet` / `orca_codex_executor`
- 修复了 `skill_registry.json` 因历史编辑导致的缺逗号 JSON 错误

---

## 5. 复用指引

后续任何三层舰队项目：
1. 复制 `项目脚手架/orca_multi_agent_fleet_v1.0/` → 新项目
2. 运行 `init_orca_fleet.sh` 初始化三层分支
3. 在 ORCA 添加 3 个工作树，按本指南/规范自动填充设置脚本与存档脚本
4. 新建工作树时设置脚本自动注册技能，无需手动维护 registry
