# Maris 调度接入说明

> **版本**：V1.0 | **基座**：CNB 免费 DeepSeek-V4-Flash（有效期至 2026-12-31）
> **适用读者**：Maris 本地调度 Agent

---

## 一、Maris 是什么？

Maris 是 ORCA 舰队的本地调度 Agent，负责：
1. 从企业微信群接收商单需求
2. 将需求结构化为任务卡
3. 投递到 `fleet_exchange/incoming/` 触发自动流水线
4. 监控任务流转状态

## 二、快速启动（3步）

### 步骤1：投递任务

```bash
# 文案任务
bash scripts/maris_dispatch.sh --type "文案" --title "产品宣传文案" --desc "500字科技感文案"

# 海报任务
bash scripts/maris_dispatch.sh --type "海报" --title "餐饮露营海报" --priority "高" --deadline "2026-08-10"

# 视频任务
bash scripts/maris_dispatch.sh --type "视频" --title "产品宣传短视频" --desc "15秒短视频"
```

### 步骤2：监控状态

```bash
# 查看各目录任务数
echo "incoming: $(ls fleet_exchange/incoming/*.md 2>/dev/null | wc -l) 个待接单"
echo "doing:    $(ls fleet_exchange/doing/*.md 2>/dev/null | wc -l) 个执行中"
echo "done:     $(ls fleet_exchange/done/*.md 2>/dev/null | wc -l) 个已完成"
echo "results:  $(ls fleet_exchange/results/*.md 2>/dev/null | wc -l) 个已归档"
```

### 步骤3：获取结果

```bash
# 查看最新交付物
ls -lt fleet_exchange/results/ | head -5
```

## 三、任务流转规则

| 目录 | 状态 | 写入者 | 读取者 | Maris 权限 |
|------|------|--------|--------|-----------|
| `incoming/` | 待接单 | **Maris** | Codex | ✅ 可读写 |
| `doing/` | 执行中 | Codex | Claude Code | ❌ 只读 |
| `done/` | 已完成 | Claude Code | CodeBuddy | ❌ 只读 |
| `results/` | 归档输出 | CodeBuddy | 客户 | ❌ 只读 |

**重要**：Maris 只写入 `incoming/`，不得修改其他目录的文件。

## 四、任务卡格式

### Markdown 格式（推荐）

```markdown
# 任务卡：任务标题

- 任务ID: YYYYMMDD_HHMMSS_N
- 类型: 文案|海报|视频|画册|PPT
- 优先级: 高|中|低
- 来源: Maris
- 截止日期: YYYY-MM-DD

## 需求
详细需求描述

## 要求
- 中文输出
- 按类型标准交付
```

### JSON 格式（程序化消费）

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

## 五、云端 NPC 协作

| NPC | 触发方式 | 职责 |
|-----|---------|------|
| @codex | Issue/PR 评论 `@codex` | 代码执行、脚本生成 |
| @claude-code | Issue/PR 评论 `@claude-code` | 代码审计、质量校验 |
| @CodeBuddy | Issue/PR 评论 `@CodeBuddy` | 终审、方案建议 |

## 六、故障排查

| 问题 | 解决方案 |
|------|---------|
| 任务投递失败 | 检查 `fleet_exchange/incoming/` 目录是否存在 |
| NPC 无响应 | 检查 `.cnb.yml` 配置是否正确 |
| 代码未同步 | 执行 `git pull origin main` |
| 端口不可达 | 执行 `bash scripts/fleet_ensure.sh` |

## 七、自检清单

- [ ] 已确认 `fleet_exchange/incoming/` 目录可写入
- [ ] 已使用 `maris_dispatch.sh` 投递至少一个测试任务
- [ ] 已确认任务卡格式正确（Markdown + JSON 双格式）
- [ ] 已确认不修改 `doing/done/results` 目录中的文件
- [ ] 已确认云端 NPC 可通过 Issue 评论触发

---

*文档版本：V1.0 | 2026-08-06 | 关联 PR#5*
