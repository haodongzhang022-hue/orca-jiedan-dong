# Fleet Exchange — 任务流转目录

> 自动生成时间：2026-08-06
> 生成脚本：scripts/maris_gen_readme.sh

## 目录结构

| 目录 | 用途 | 当前任务数 |
|------|------|-----------|
| **incoming/** | 待接单任务（Maris 投递 / 外部写入） | 5 |
| **doing/** | 执行中（Codex 执行层处理） | 0 |
| **done/** | 已完成（Claude Code 审核通过） | 2 |
| **results/** | 最终成品（CodeBuddy 终审归档） | 5 |

## 流转规则

1. **Maris** → 写入任务卡到 `incoming/`
2. **Codex** → 从 `incoming/` 取任务 → 执行 → 移入 `doing/`
3. **Claude Code** → 从 `doing/` 审核校验 → 通过 → 移入 `done/`
4. **CodeBuddy** → 从 `done/` 终审 → 归档到 `results/`

## 任务卡格式

```markdown
# 任务卡
- task_id: YYYYMMDD_HHMMSS_N
- source: Maris | Codex | Hermes
- type: 文案 | 海报 | 视频 | 通用
- title: <任务标题>
- status: incoming | doing | done | results
```

## 手动操作

```bash
# 投递新任务
bash scripts/maris_dispatch.sh --type 文案 --title "任务标题" --desc "描述"

# 确认待放行任务
bash scripts/confirm_task.sh <task_id>

# 完成任务并归档
bash scripts/fleet_done.sh "<doing/任务文件>" "<结果摘要>"

# 刷新 README 状态
bash scripts/maris_gen_readme.sh
```

## 云端同步规则

| 操作 | 本地路径 | 云端路径 | 同步方式 |
|------|---------|---------|---------|
| 投递任务 | `fleet_exchange/incoming/` | `fleet_exchange/incoming/` | `git push` |
| 查看结果 | `fleet_exchange/results/` | `fleet_exchange/results/` | `git pull` |
| 状态刷新 | 本地运行 `maris_gen_readme.sh` | `fleet_exchange/README.md` | `git push` |
