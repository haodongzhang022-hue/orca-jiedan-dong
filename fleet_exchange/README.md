# Fleet Exchange — 任务交换区

> 四级任务流转目录，Maris / Codex / Claude Code / CodeBuddy 跨主体协作核心

## 四级流转说明

| 目录 | 状态 | 写入者 | 读取者 | 说明 |
|------|------|--------|--------|------|
| `incoming/` | 待接单 | Hermes / Maris | Codex | 新任务卡落地 |
| `doing/` | 执行中 | Codex | Claude Code | Codex 正在处理的任务 |
| `done/` | 已完成 | Claude Code | CodeBuddy | Claude Code 审核通过的结果 |
| `results/` | 归档输出 | CodeBuddy | 客户 | 最终交付物 |

## 任务卡格式

### Markdown 格式

```markdown
# 任务卡：任务标题

- 任务ID: YYYYMMDD_HHMMSS_N
- 类型: 文案|海报|视频|画册|PPT
- 优先级: 高|中|低
- 来源: Maris|企业微信群|手动
- 截止日期: YYYY-MM-DD

## 需求
详细需求描述

## 要求
- 中文输出
- 按类型标准交付
```

### JSON 格式

```json
{
  "task_id": "YYYYMMDD_HHMMSS_N",
  "task_type": "海报",
  "source": "Maris",
  "title": "任务标题",
  "description": "详细需求",
  "priority": "高",
  "deadline": "2026-08-10",
  "created_at": "2026-08-06 12:00:00"
}
```

## 触发方式

1. **Maris 投递**：运行 `bash scripts/maris_dispatch.sh --type "文案" --title "xxx"`
2. **Codex 接单**：自动监听 `incoming/` 读取并执行
3. **Claude Code 审核**：从 `doing/` 读取执行结果，审核通过移入 `done/`
4. **CodeBuddy 终审**：从 `done/` 读取审核结果，归档到 `results/`

## 辅助目录

| 目录 | 用途 |
|------|------|
| `accepted/` | 已接单确认（含预览图） |
| `orders/` | 订单元数据（ORD-YYYYMMDD-NNN） |
| `parsed/` | 已解析订单分析报告 |
| `templates/` | 订单/设计模板脚本 |

## 云端同步

- `git push` 后自动同步到 CNB 云端仓库
- `incoming/` 中的任务卡提交后，云端 NPC 可通过 Issue 评论读取
- `done/` 和 `results/` 通过 `bash scripts/fleet_done.sh` 自动归档并同步

---

*Maris 投递 → Codex 执行 → Claude Code 审核 → CodeBuddy 终审 → 归档交付*
