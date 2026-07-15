# 舰队 WorkTree 任务交换区 · 协议 v2.0

> **v2.0 升级要点**：目录迁移至 Git 仓库内、新增自动轮询模式、WorkBuddy 主动推送、取消人工粘贴中转
> 用途：消除 WorkBuddy（视觉大脑）与 ORCA 三 Agent（Hermes / Codex / Claude Code）之间的人工中转
> **新位置**：`E:\龙虾AI主控中心\我的AI分身\多智能体舰队编排\fleet_exchange\`
> **旧位置**：`E:\fleet_exchange\`（已废弃，保留只读副本）

## 一、目录结构

| 目录 | 写入方 | 读取方 | 含义 |
|------|--------|--------|------|
| `incoming/` | WorkBuddy (fleet_push.sh) | Agent (fleet_pull.sh) | 新任务待认领 |
| `doing/` | Agent (fleet_pull.sh) | — | 进行中（排他，时间戳唯一） |
| `done/` | Agent (fleet_done.sh) | — | 已完成归档 |
| `results/` | Agent (fleet_done.sh) | WorkBuddy | 结构化执行结果 |
| `logs/` | 双方 | 双方 | 操作日志 + 审计追踪 |

## 二、任务文件格式（UTF-8 `.md`）

```markdown
---
task_id: 20260716_001
from: WorkBuddy
to: any              # any | Hermes | Codex | ClaudeCode
priority: normal     # low | normal | high
context: 黄金黑马策略回测
created: 2026-07-16 00:35:00
---

# 任务：<中文标题>

<中文指令：要做什么、输入参数、交付物、验收标准>

## 验收标准
- [ ] 执行无报错
- [ ] 结果写回 results/
- [ ] 符合预期输出
```

## 三、状态流转

```
                    ┌─────────────────────────────┐
                    │   WorkBuddy (fleet_push.sh)   │
                    │   写 incoming/               │
                    └──────────┬──────────────────┘
                               │
                               ▼
                    ┌─────────────────────────────┐
         ┌─────────│     incoming/ (任务池)        │◄──┐
         │         └──────────┬──────────────────┘   │
         │  fleet_pull.sh    │ fleet_pull.sh auto    │ 重试耗尽退回
         │  (手动单次)       │ (自动轮询,默认30s)     │ 标记 priority=high
         │                    │                       │
         ▼                    ▼                       │
  ┌──────────────┐   ┌──────────────────┐            │
  │   doing/     │   │  Agent 认领并执行  │────────────┘
  │   (排他锁)    │   └────────┬─────────┘
  └──────────────┘            │
          │                   │
          │  fleet_done.sh    │ 失败→写results错误摘要
          ▼                   │ 留doing/等待重试(≤3次)
  ┌──────────────┐   ┌────────▼─────────┐
  │   done/      │◄──│  results/         │
  │   (归档)      │   │  (结构化结果)      │
  └──────────────┘   └────────▲─────────┘
                              │
                     WorkBuddy 自动轮询汇总 → 迭代下发
```

## 四、协作规则（v2.0 锁死升级版）

### 4.1 基础规则（继承 v1.0）
1. **WorkBuddy 是唯一写 `incoming/` 的角色**；Agent 只做"拉取 → 执行 → 回写"，不直接互发消息。
2. Agent 空闲时执行 `fleet_pull.sh auto` 进入后台自动轮询（默认30秒间隔），认领**最旧**任务（FIFO）。
3. 执行结果写入 `results/`（同名 `__result_时间戳.md`），WorkBuddy 轮询 `results/` 汇总。
4. **异常**：Agent 执行失败 → 错误摘要写 `results/` 同名文件 → 任务留 `doing/` 等重试（最多3次）→ 超限退回 `incoming/` 标 `priority=high`。
5. 任务一旦进入 `doing/` 即排他（文件名含时间戳天然唯一），其他 Agent 不重复认领。

### 4.2 v2.0 新增自动化规则

| 规则 | 说明 |
|------|------|
| **自动轮询** | Agent 启动时运行 `bash fleet_pull.sh auto 30 600`，每30s扫描一次，空闲10分钟自动退出 |
| **主动推送** | WorkBuddy 通过 `fleet_push.sh` 一行命令写入 incoming/，无需手动创建 `.md` |
| **零人工中转** | 全流程无需复制粘贴 bash 命令；保留手动单条模式仅用于调试 |
| **审计日志** | 每次 push/pull/done 操作自动追加到 `logs/ops_YYYYMMDD.log` |

## 五、命令参考（v2.0 完整版）

| 操作 | 命令 | 使用者 |
|------|------|--------|
| **推送任务** | `bash fleet_push.sh "标题" "目标Agent" "优先级" "指令内容"` | WorkBuddy |
| **拉取任务(单次)** | `bash fleet_pull.sh` | Agent |
| **拉取任务(自动)** | `bash fleet_pull.sh auto [间隔s] [空闲超时s]` | Agent |
| **回写结果** | `bash fleet_done.sh "<WORKING_FILE>" "<结果摘要>"` | Agent |
| **扫描Marvis** | `bash marvis_scan.sh` | WorkBuddy/Hermes |

## 六、Git 工作树绑定

本交换区位于 AI 分身 Git 仓库内（`E:\龙虾AI主控中心\我的AI分身\` 为 git root）：

```bash
cd "E:/龙虾AI主控中心/我的AI分身"
git add 多智能体舰队编排/fleet_exchange/
git commit -m "fleet: migrate to repo + auto-poll v2.0"
```

支持快照、分支切换、历史版本回溯。
