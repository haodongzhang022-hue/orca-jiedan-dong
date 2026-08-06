# Maris 调度接入说明

> 版本：1.0 | 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> 适用：orca-jiedan 企业微信群定制接单项目
> 阅读主体：Maris（自动化调度主体）+ 人类运维者

---

## 一、Maris 是什么

Maris 是 ORCA 舰队的本地调度中枢，负责：
1. 接收企业微信群商单需求
2. 生成结构化任务卡
3. 投递到 `fleet_exchange/incoming/`
4. 监控任务流转状态
5. 归档最终产出物

## 二、Maris 标准件清单

| 标准件 | 路径 | 用途 |
|--------|------|------|
| **maris_dispatch.sh** | `scripts/maris_dispatch.sh` | 投递任务卡到 incoming/ |
| **maris_gen_readme.sh** | `scripts/maris_gen_readme.sh` | 生成 fleet_exchange/README.md 状态报告 |
| **orca_init_worktrees.sh** | `scripts/orca_init_worktrees.sh` | 初始化三工作树（hermes/codex/claude） |
| **fleet_exchange/README.md** | `fleet_exchange/README.md` | 任务流转目录状态说明 |

## 三、Maris 投递任务

### 3.1 普通文案任务

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --type 文案 --title "朋友圈餐饮海报文案" --desc "露营风格，5条文案，带emoji"
```

### 3.2 指定类型结构化任务

```bash
# 海报任务
bash scripts/maris_dispatch.sh --type 海报 --title "摇滚风演出海报" --desc "A3尺寸，黑底金字，含乐队名和日期"

# 视频任务
bash scripts/maris_dispatch.sh --type 视频 --title "产品宣传短视频" --desc "30秒，口播+字幕，MP4格式"

# 通用任务
bash scripts/maris_dispatch.sh --type 通用 --title "数据整理" --desc "将Excel数据转为Markdown表格"
```

### 3.3 从文件投递

```bash
# 一键复制 ↓
bash scripts/maris_dispatch.sh --file /tmp/my_task_card.md
```

## 四、任务流转监控

```bash
# 刷新 fleet_exchange 状态
bash scripts/maris_gen_readme.sh

# 查看各目录任务数
ls fleet_exchange/incoming/ | wc -l   # 待接单
ls fleet_exchange/doing/    | wc -l   # 执行中
ls fleet_exchange/done/     | wc -l   # 已完成
ls fleet_exchange/results/  | wc -l   # 已归档
```

## 五、三工作树初始化

```bash
# 一键复制 ↓
bash scripts/orca_init_worktrees.sh

# 然后在每个工作树中完善环境
cd worktrees/hermes && bash ../../scripts/orca_setup_worktree.sh
cd worktrees/codex  && bash ../../scripts/orca_setup_worktree.sh
cd worktrees/claude && bash ../../scripts/orca_setup_worktree.sh
```

## 六、Maris ↔ CNB NPC 协作

### 6.1 云端触发

Maris 投递任务后，可通过 CNB Issue 评论触发 NPC 接力：

```
@npc/codex 请处理 fleet_exchange/incoming/ 下的最新任务
@npc/claude-code 请审核 fleet_exchange/doing/ 下的产出
@CodeBuddy 请终审并归档 fleet_exchange/done/ 下的结果
```

### 6.2 本地触发

```bash
# Codex 执行
cd worktrees/codex && codex "处理 fleet_exchange/incoming/ 下的任务"

# Claude Code 审核
cd worktrees/claude && claude "审核 fleet_exchange/doing/ 下的产出"

# 归档
bash scripts/fleet_done.sh "fleet_exchange/doing/<任务文件>" "审核通过，产出正常"
```

## 七、Maris 执行自检清单

- [ ] `scripts/maris_dispatch.sh` 可执行（`chmod +x scripts/maris_dispatch.sh`）
- [ ] `fleet_exchange/incoming/` 目录存在且可写
- [ ] `fleet_exchange/doing/` 目录存在
- [ ] `fleet_exchange/done/` 目录存在
- [ ] `fleet_exchange/results/` 目录存在
- [ ] Git 远程仓库可推送（`git push origin main`）
- [ ] CNB 仓库可访问（`https://cnb.cool/TJF19770107/orca-jiedan`）
- [ ] `.cnb.yml` 已配置 NPC 流水线
- [ ] `.cnb/settings.yml` 已配置 NPC 角色人设
- [ ] 任务卡格式符合规范（含 task_id / type / title / status）

---

> **文档版本**：v1.0
> **基座标识**：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> **维护者**：龙虾AI主控中心 · Marvis 运维组
