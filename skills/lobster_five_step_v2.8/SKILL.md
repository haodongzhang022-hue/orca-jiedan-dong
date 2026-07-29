---
name: "lobster_task_standard_workflow_v2.8"
description: "龙虾五步法 V2.8 增量版：在V2.7基础上，叠加自动恢复机制、防退化铁律、Codex桌面版401根治方案。解决'每次打开项目都要手动恢复'的系统性问题。"
version: "2.8"
date: "2026-07-29"
updated: "2026-07-29 (升级自V2.7：新增自动恢复机制、防退化铁律、计划任务自启)"
merged_from: ["v2.7 增量版", "Codex桌面版401根治实战", "多代理自动恢复机制设计"]
sync_mode: "bidirectional"
primary_path: "E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v2.7\SKILL.md"
---

# 龙虾标准五步法 V2.8 增量版

技能名称：龙虾标准五步法（V2.8增量版·自动恢复·防退化·零手动干预）
适用范围：全域任务（代码/配置/容器/流程/文档/排障/迭代/量化策略开发/Orca多Agent协作/工作树管理/会话恢复）
执行口径：严格按五步顺序执行，不许跳步；不删规则；不覆盖旧配置；只合并叠加
版本号：v2.8（在v2.7基础上，叠加自动恢复机制与防退化铁律）
更新时间：2026-07-29
生效范围：全域 / 永久 / Codex + Hermes + Claude Code + OpenCode + OpenClaw + Marvis + WorkBuddy 统一

---

## 继承声明

本版本**完整继承** V2.7 增量版的全部内容，包括：
- 四大铁律（精准备份/无命令不修复/全存E盘/禁止后台扫描）
- 快照触发体系（手动确认/阈值自动/故障前置）
- 第三方云端免费额度前置校验（#293.8）
- Orca多Agent工作树运维规范
- 会话持久化保障规则
- 双实例调度标准流程

**以下仅列出 V2.8 新增内容，原有规则不重复、不覆盖。**

---

## 新增：自动恢复机制（V2.8 核心 · 对应全域模板 #287.5）

> **历史痛点**：每次打开 Orca 项目，Codex/Claude Code 代理服务可能未运行，用户需要手动输入命令逐个拉起。Codex 桌面版 `~/.codex/config.toml` 的 `wire_api` 偶尔被外部工具覆盖为 `"responses"`，导致 401 Unauthorized。这种"退化-手动恢复"循环浪费大量时间。
>
> **本机制的目标**：打开项目即恢复，不需要手动输入任何命令。

### 1. 自动恢复架构

```
用户登录 Windows
       ↓
计划任务 LobsterFleet_AutoRestore（开机自启）
       ↓
fleet_auto_restore.cmd 自动执行：
  ├─ 检查端口 15721/15730 → 未运行则自动拉起
  ├─ 校验 ~/.codex/config.toml → wire_api/base_url 错误则自动修复
  ├─ 同步各 worktree 分支到 master
  └─ 验证 API 连通性
       ↓
用户打开 Orca 项目
       ↓
Claude Code 读取 CLAUDE.md → 自动执行恢复检查
Codex 读取 CODEX.md → 自动执行恢复检查
       ↓
所有服务就绪，用户直接开始工作
```

### 2. 端口分配表（强制·不可修改）

| 服务 | 端口 | 代理脚本 | 用途 |
|------|------|---------|------|
| Anthropic Proxy | 15721 | anthropic_proxy_15721.py | Claude Code API 转换 |
| Codex Tool Proxy | 15730 | codex_tool_proxy.py | Codex 系列 API 代理 |
| Hermes Gateway | 8642 | hermes gateway | Hermes 桌面版 |
| Memos | 5230 | memos.exe | 笔记服务 |

**铁律**：端口分配写死，禁止随意修改。新增服务必须先检查端口冲突。

### 3. Codex 配置铁律

#### 3.1 Codex 桌面版（~/.codex/config.toml）

```toml
model_provider = "mimo-v2.5-pro"
model = "mimo-v2.5-pro"
wire_api = "chat"                    # 必须是 chat，不能是 responses
base_url = "http://127.0.0.1:15730/v1"  # 必须走代理，不能直连上游
api_key = "从config.toml读取"         # 代理会自动注入
```

**禁止项**：
- ❌ `wire_api = "responses"` → MiMo API 不支持，导致 401
- ❌ `base_url = "https://token-plan-cn.xiaomimimo.com/v1"` → 直连上游绕过代理
- ❌ `requires_openai_auth = true` → Codex++ 可能覆盖 base_url

#### 3.2 Codex 项目版（E:/龙虾AI主控中心/Codex/.codex/config.toml）

```toml
model = "mimo-v2.5-pro"
model_provider = "xiaomi-mimo"
OPENAI_BASE_URL = "http://127.0.0.1:15730/v1"
```

### 4. 恢复脚本清单

| 脚本 | 作用 | 运行方式 |
|------|------|---------|
| `scripts/fleet_auto_restore.cmd` | Windows 一键恢复（开机自启） | 计划任务 / 手动双击 |
| `scripts/fleet_restore.sh` | 完整恢复（含快照管理） | `bash scripts/fleet_restore.sh --snapshot` |
| `scripts/fleet_health_check.sh` | 健康检查（只读） | `bash scripts/fleet_health_check.sh` |
| `scripts/fleet_startup.cmd` | 代理启动（旧版，保留兼容） | 手动 |
| `CLAUDE.md` | Claude Code 自动恢复指令 | 自动读取 |
| `codex/CODEX.md` | Codex 自动恢复指令 | 自动读取 |

### 5. 防退化铁律（新增·强制执行）

| # | 铁律 | 原因 | 违反后果 |
|---|------|------|---------|
| D1 | 禁止手动修改 `~/.codex/config.toml` 的 wire_api 和 base_url | 恢复脚本会自动校验并修复，手动改可能被覆盖 | 401 Unauthorized |
| D2 | 每次会话开始必须先执行恢复检查 | 代理可能在会话间被关闭 | 无法调用 API |
| D3 | 快照 ≤20MB，只保留最近 2 份 | 磁盘空间有限 | 磁盘满 |
| D4 | 恢复脚本有幂等性，多次运行无副作用 | 安全重复执行 | 无 |
| D5 | 新增服务必须先检查端口冲突 | 端口冲突导致服务不可用 | 代理崩溃 |
| D6 | 代理脚本修改后必须更新快照 | 快照是回滚的唯一依据 | 无法回滚 |

### 6. 401 错误根治案例

**问题**：Codex 桌面版打开后报 `401 Unauthorized: Invalid API Key`

**根因**：
- `~/.codex/config.toml` 中 `wire_api = "responses"`
- MiMo API 的 `/v1/responses` 端点返回 401
- Codex++ 或其他工具可能在更新时覆盖此配置

**修复**：
1. 改 `wire_api` 为 `"chat"`
2. 确保 `base_url` 指向 `127.0.0.1:15730`（代理端口）
3. 移除 `requires_openai_auth = true`
4. 注册计划任务自动执行恢复脚本

**预防**：
- 恢复脚本每次运行都会校验配置
- CLAUDE.md 和 CODEX.md 写入恢复指令
- 计划任务开机自启

---

## 与 V2.7 的差异总结

| 维度 | V2.7 | V2.8 |
|------|------|------|
| 恢复方式 | 手动执行命令 | 自动恢复（计划任务 + 项目指令） |
| Codex 配置 | 需要手动检查 | 自动校验 + 自动修复 |
| 分支同步 | 手动 merge | 自动同步到 master |
| 快照管理 | 手动创建 | 自动清理 + 按需创建 |
| 防退化 | 无 | 6 条铁律 + 自动校验 |
| 用户干预 | 每次打开项目需手动拉起服务 | 零干预，打开即用 |

---

> 版本：v2.8（自动恢复·防退化·零手动干预）
> 更新时间：2026-07-29
> 维护者：龙虾 AI 主控中心
