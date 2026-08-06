# fleet_exchange · 任务卡流转区

多 Agent 舰队（Codex / Claude Code / Hermes / Maris / CodeBuddy）共享任务交换区。

## 目录流转

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

## 任务卡格式

```markdown
---
task_id: TASK-20260806-103000
from: maris
to: fleet
pipeline: route_1_auto_pipeline
simulation: false
created_at: 2026-08-06 10:30:00
type: poster
price: 300
---

# TASK-20260806-103000

## 需求描述
...

## 期望交付物
- [ ] 初稿（doing/）
- [ ] 审核通过（done/）
- [ ] 最终结果（results/）
```

## 一键投递

```bash
bash scripts/maris_dispatch.sh "任务需求描述"
bash scripts/maris_dispatch.sh --type poster --desc "开业海报" --price 300
```
