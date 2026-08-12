# 双盘备份与 Obsidian 归档清单（v1.6.0 · 四角色矩阵闭环）

> 任务编号：Issue #10 ｜ 执行角色：CodeBuddy ｜ 版本：1.6.0
> 归档对象：CNB NPC 四角色栈（claude-code / hermes / codex / lobster）
> 基座：CNB 内置免费 DeepSeek-V4-Flash（1600 核时/月，有效期至 2026-12-31）

---

## 一、E盘 / G盘 双盘备份目录

| 盘 | 目录 | 内容 |
|----|------|------|
| E盘（龙虾AI主控中心） | `E:/龙虾AI主控中心/我的AI分身/技能库/CNB_ClaudeCode_NPC` | 四角色 NPC 适配层/流水线/入口/文档 |
| E盘（龙虾AI主控中心） | `E:/龙虾AI主控中心/我的AI分身/技能库/CNB_HermesCodex_NPC` | hermes/codex 原生 CLI 接入资产 |
| G盘（镜像目录） | `G:/龙虾AI主控中心/我的AI分身/技能库/CNB_ClaudeCode_NPC` | E盘技能库完整镜像 |
| G盘（ORCA 数据） | `G:/龙虾AI主控中心/ORCA数据/orca-jiedan` | 仓库源码镜像 + 归档清单 |

### 备份清单（核心文件）

```
.cnb/settings.yml                    # 四角色人设（全域模板，基座锁定）
.cnb.yml                             # NPC 事件流水线（A/B 双路径 + 镜像构建）
.ci/npc-full.yml                     # 路径B · claude-code 角色流水线
.ci/hermes.yml                       # 路径B · hermes 角色流水线
.ci/codex.yml                        # 路径B · codex 角色流水线
adapters/Dockerfile                  # 自定义镜像（三 CLI + 适配层 + 额度监控）
adapters/anthropic_to_cnb.py         # 协议适配层（监听 127.0.0.1:8787）
adapters/hermes_entry.sh             # 原生 hermes 安装辅助
claude/entrypoint.sh                 # claude-code 容器入口
hermes/entrypoint.sh                 # hermes 容器入口
hermes/CLI_INTEGRATION.md            # hermes 原生 CLI 接入说明
scripts/quota_monitor.py             # 额度监控（超限仅降级）
scripts/one_click_npc_stack.sh       # 四角色栈一键自检
docs/claude_code_cloud_vs_local.md   # A/B 双模式对比 + 四角色矩阵
docs/四角色矩阵_验收报告_v1.6.0_20260807.md  # 分阶段执行闭环验收报告
templates/cnb_npc_path_b_scaffold/   # 脚手架模板（同步 orca-cnb-project-template）
VERSION.md / scaffold_version        # 版本 1.6.0
```

## 二、双盘同步脚本

```bash
# 1. 在 CNB 云端生成导出包 + 镜像清单（自动过滤密钥）
bash scripts/export_to_github_and_mirror.sh --skip-github

# 2. 本地 E/G 双盘落盘
bash artifacts/sync_to_e_g.sh                # E盘/G盘技能库镜像

# 3. Obsidian 归档（本报告新增）
bash scripts/archive_obsidian_v1.6.0.sh      # 同步到 Obsidian 主库 + wiki 索引
```

## 三、Obsidian 知识库归档

| 项 | 位置 |
|----|------|
| Obsidian 主库 | `E:/龙虾AI主控中心/Obsidian/`（junction→G盘） |
| 归档子目录 | `ORCA数据/orca-jiedan/CNB四角色NPC_v1.6.0/` |
| wiki 索引 | `wiki/index.md`（追加条目「CNB四角色NPC_v1.6.0」） |
| 知识库宪法 | `AGENTS.md`（遵守既有规范） |

### 归档内容

1. `四角色矩阵_验收报告_v1.6.0_20260807.md`（本闭环验收报告）
2. `claude_code_cloud_vs_local.md`（A/B 双模式 + 四角色矩阵拓扑）
3. `脚手架升级_v1.6.0_接入原生HermesCLI_20260807.md`
4. `验收报告_Claude-Code_CNB云端NPC_DeepSeekV4Flash_20260807.md`
5. `templates/cnb_npc_path_b_scaffold/`（脚手架模板完整快照）

## 四、龙虾五步法闭环核对

- [x] Step1 意图识别：四角色矩阵 + 分阶段执行 + 红线约束
- [x] Step2 能力映射：路径A/B 双路径 + 原生 CLI 三件套 + 免费基座锁定
- [x] Step3 执行实施：PR#13/14/15 合并 + 镜像 1.6.0 构建推送 + @claude-code/@codex 实测
- [x] Step4 验收反思：39 请求 AI 用量审计 `milli_credit=0`，0 外部付费
- [x] Step5 归档进化：Git 提交 + E/G 双盘 + Obsidian 录入 + skill_registry v1.6.0

## 五、待办提醒

- [ ] main 最新（fe559fe）上再触发一次 `@hermes` / `@codex`，确认路径B 容器实际路由与 `hermes --version` / `codex --version` 输出（配置已就绪，触发即验证）

---

—— CodeBuddy（orca-jiedan）2026-08-07
