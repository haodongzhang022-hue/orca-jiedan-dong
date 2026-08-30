# 正常节点快照 · 基线索引（2026-08-25）

> 回滚基线：**`normal_node_20260825_193433.tar.gz`（当前最新）**
> 更新：2026-08-25 · Codex 执行 · 重新快照（15.67MB < 20M）· 一键回滚脚本补齐并实测（scripts/one-click-rollback.ps1 + scripts/create_snapshot.ps1）

## 快照清单

| 文件 | 大小 | 状态 | 说明 |
|------|------|------|------|
| `normal_node_20260825_193433.tar.gz` | 15.67MB | ✅ **当前回滚基线** | Codex 2026-08-25 重新快照，排除 .git/对话记录/msgbus/fleet_exchange/worktrees/logs/snapshots/tools/.workbuddy/__pycache__/node_modules/tests/backups/archive，tar 打包 16,430,853B <20M，859 条目完整性校验通过，三引擎节点备份 |

| 文件 | 大小 | 状态 | 说明 |
|------|------|------|------|
| 
ormal_node_20260825_193433.tar.gz | 15.67MB | ✅ **当前回滚基线** | Codex 2026-08-25 重新快照，排除 .git/对话记录/msgbus/fleet_exchange/worktrees/logs/snapshots/tools/.workbuddy/__pycache__/node_modules/tests/backups/archive，tar 打包 16,430,853B <20M，859 条目完整性校验通过，三引擎节点备份 |


| 文件 | 大小 | 状态 | 说明 |
|------|------|------|------|
| `normal_node_20260813_180341.tar.gz` | 10.0MB | ✅ **当前回滚基线** | hermes 大脑 1234 轻量快照（2026-08-13 18:04，排除 .git/worktrees/logs/snapshots/对话记录/fleet_exchange/msgbus/群聊库/__pycache__/tests/tools，tar 打包 11,116,285B <20M，max 防线四层终验：L1 catalog零max(34行=xhigh)+L2 源头JS index.js 8处xhigh拦截 max=0+备份5份(含guard_auto)+L3 双守护脚本实测运行+L4 双定时任务 Ready 日志每10分钟落盘，三引擎正常） |
| `normal_node_20260813_173935.tar.gz` | 16.5MB | ✅ 可用 | hermes 大脑 1234 轻量快照（2026-08-13 17:39，排除 .git/worktrees/logs/snapshots/对话记录/群聊库，tar 打包 16,501,732B <20M，max 防线独立复核+当前catalog零max+WatchCodexCatalog 17:35 结果0 实测，三引擎正常） |
| `normal_node_20260813_173255.tar.gz` | 10.8MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 17:32，排除 .git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools，tar 打包 11,332,228B <20M，max 防线终验+当前catalog零max+守护任务 17:34 实测运行，三引擎正常） |
| `normal_node_20260813_172421.tar.gz` | 9.5MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 17:24，排除 .git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools/*.zip，tar 打包 9,518,037B <20M，max 防线终验+当前catalog零max，三引擎正常） |
| `normal_node_20260813_170407.tar.gz` | 9.1MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 17:04，排除 .git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools/*.zip，tar 打包 9,516,403B <20M，含防覆盖固化收尾 463b908 及之后防线，三引擎正常节点） |
| `normal_node_20260813_165823.tar.gz` | 10.6MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 16:58，排除 .git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools，tar 打包 11,138,026B <20M，含防覆盖固化收尾 463b908） |
| `normal_node_20260813_164828.tar.gz` | 10.6MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 16:48，排除 .git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools，tar 打包 11,137,389B <20M，含防线根治提交 4fe8631） |
| `normal_node_20260813_163939.tar.gz` | 10.6MB | ✅ 可用 | codex 1234 轻量快照（2026-08-13 16:39，排除对话记录/msgbus/fleet_exchange/tools/worktrees/logs/snapshots，tar 打包 11,110,713B <20M） |
| `normal_node_20260813_161236.tar.gz` | 11.0MB | ✅ 可用 | codex 轻量快照重建（2026-08-13 16:12，排除对话记录/msgbus/worktrees/logs/snapshots，tarfile 校验通过） |
| `normal_node_20260813_160650.tar.gz` | 17.0MB | ✅ 可用 | 1234 调用触发·防线四层复核+三引擎正常运转后节点（2026-08-13 16:06，排除对话记录/msgbus/worktrees/logs/snapshots） |
| `normal_node_20260813_155724.tar.gz` | 16.9MB | ✅ 可用 | 根防线落实复核+守护任务 Ready 后节点（2026-08-13 15:57） |
| `normal_node_20260813_155209.tar.gz` | 10.7MB | ✅ 可用 | 防线端到端实测+3 catalog JSON全OK+守护任务真实运行后节点（2026-08-13 15:52） |
| `normal_node_20260813_155158.tar.gz` | 18.8MB | ⚠️ **已过期** | 19MB 接近上限，已被 155209 取代（未删除，删除权留 owner） |
| `normal_node_20260813_154312.tar.gz` | 10.3MB | ✅ 可用 | 1234 调用触发·防线四要素复核+当前会话 catalog 零 max 后节点（2026-08-13 15:43） |
| `normal_node_20260813_153640.tar.gz` | 15.0MB | ✅ 可用 | 1234 调用触发·防线三要素实测（源头index.js无max+守护任务上次结果0+启动兜底在库）后节点（2026-08-13 15:36） |
| `normal_node_20260813_152653.tar.gz` | 14.2MB | ✅ 可用 | 1234 调用触发·codex max根因防线终验（源头无max+2分钟巡检+启动兜底）后节点（2026-08-13 15:26） |
| `normal_node_20260813_150954.tar.gz` | 11.1MB | ✅ 可用 | 1234 调用触发·codex max防复发根治（max→xhigh + Lobster_CodexCatalogGuard 检修后）节点（2026-08-13 15:09） |
| `normal_node_20260813_150547.tar.gz` | 11.5MB | ✅ 可用 | codex max防线加固后节点（2026-08-13 15:05） |
| `normal_node_20260813_150118.tar.gz` | 11.0MB | ✅ 可用 | codex max防线加固 v1.2 + 定时任务改挂后重建（2026-08-13 15:01） |
| `normal_node_20260813_001709.tar.gz` | 13.5MB | ✅ 可用 | Step4 终验后重建的正常节点（2026-08-13 00:17） |
| `normal_node_20260812_235516.tar.gz` | 10.6MB | ✅ 可用 | 本批交付后节点（2026-08-12 23:55） |
| `normal_node_20260812_235511.tar.gz` | 18.4MB | ⚠️ **已过期** | 接近 20M 上限且被 235516 取代，建议清理或移出归档目录 |

## 恢复方法

```bash
tar -xzf snapshots/normal_node_20260813_150954.tar.gz -C <回滚目标目录>
```

回滚后按 HERMES.md 自动恢复协议拉起 15721/15730 代理，验证三引擎连通。

## 约定

- 每次「三引擎正常运转」状态确认后重建一份 normal_node 快照
- 体积须 < 20MB（排除 .git/对话记录/msgbus/worktrees/logs/snapshots）
- 过期快照标注于此表，删除动作由 owner 决定（避免误删回滚基线）
