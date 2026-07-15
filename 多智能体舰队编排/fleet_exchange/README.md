# 🚀 多智能体舰队编排 · Fleet Exchange v2.0

> **龙虾五步法 v2.6 + 全域模板驱动交付** | 2026-07-16 00:35~00:50
> **位置**：`E:\龙虾AI主控中心\我的AI分身\多智能体舰队编排\fleet_exchange\`

## 一、架构总览

```
┌─────────────────────────────────────────────────────┐
│                  用户 / 截图 / 语音                    │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              WorkBuddy (视觉中枢 + 调度中枢)           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ Ollama 视觉  │  │ fleet_push  │  │ 结果汇总迭代  │ │
│  │ (本地零成本) │  │   (推送任务) │  │  (results/)  │ │
│  └─────────────┘  └──────┬──────┘  └──────┬───────┘ │
└────────────────────────────┼─────────────────┼──────┘
                             │                 │
                    incoming/ (任务池)    results/ (结果)
                             │                 ▲
              ┌──────────────┼───────────────┘
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  Hermes    │  │   Codex    │  │ Claude Code│
     │ (BASH执行) │  │ (量化开发) │  │ (代码审计)  │
     │ auto轮询   │  │ auto轮询   │  │ auto轮询    │
     └────────────┘  └────────────┘  └────────────┘
```

## 二、目录索引

| 文件/目录 | 说明 | 版本 |
|-----------|------|------|
| `PROTOCOL.md` | 任务交换区协议（含流转图、规则、命令参考） | v2.0 |
| `fleet_push.sh` | WorkBuddy 一行命令推送任务 | v2.0 🆕 |
| `fleet_pull.sh` | Agent 拉取任务（支持 auto 自动轮询） | v2.0 ↑ |
| `fleet_done.sh` | Agent 回写结果（含审计日志） | v2.0 ↑ |
| `marvis_scan.sh` | 局域网端点自动扫描工具 | v1.0 🆕 |
| `vision_config.json` | 视觉中枢切换配置（Ollama/HY3/Marvis） | v1.0 🆕 |
| `角色分工与自动调度规则.md` | 四角色权责矩阵 + 调度优先级表 | v2.0 ↑ |
| `模式C闭环测试说明书.md` | 全自动(A)/半自动(B)双模式测试指南 | v2.0 ↑ |
| `视觉中枢降本测评.md` | Ollama部署手册 + 对比测评模板 | v2.0 ↑ |
| `迁移实施报告.md` | 完整迁移步骤、路径替换、校验记录 | v1.0 🆕 |
| `incoming/` | 任务池（待 Agent 认领） | — |
| `doing/` | 进行中（排他锁） | — |
| `done/` | 已归档 | — |
| `results/` | 结构化执行结果 | — |
| `logs/` | 操作日志（ops_YYYYMMDD.log） | — |

## 三、v1.0 → v2.0 升级清单

| 能力 | v1.0 (旧 E:\fleet_exchange\) | v2.0 (新路径) |
|------|---------------------------|--------------|
| 目录位置 | E:\fleet_exchange\ (独立) | AI分身Git仓库内 (统一版本管控) |
| 任务推送 | 手动写 .md 文件 | `fleet_push.sh` 一行命令 |
| Agent 拉取 | 手动粘贴 bash 命令 | `fleet_pull.sh auto` 自动轮询 |
| 审计追踪 | 无 | `logs/ops_YYYYMMDD.log` 自动记录 |
| 视觉解析 | 仅 HY3（付费） | Ollama 本地零成本（主力）+HY3备援 |
| Marvis 接入 | 无 | `marvis_scan.sh` 自动扫描 |
| 视觉切换 | 不支持 | `vision_config.json` 一键切换 |

## 四、快速启动

```bash
# 1. WorkBuddy 推送任务
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_push.sh" "任务名" "目标Agent" "normal" "指令内容"

# 2. Agent 启动自动轮询（Hermes 示例）
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 30 600

# 3. 扫描 Marvis 端点
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/marvis_scan.sh"

# 4. 检查 Ollama 已安装模型
"E:/龙虾AI主控中心/Ollama_030/ollama.exe" list
```

## 五、当前环境状态（2026-07-16 00:50 快照）

| 组件 | 状态 | 备注 |
|------|------|------|
| 交换区新路径 | ✅ 就绪 | Git untracked，待 commit |
| 全链路闭环 | ✅ 验证通过 | push→pull→done→results 测试 OK |
| Ollama 服务 | ✅ 在线 | 127.0.0.1:11434 |
| Ollama 已有模型 | qwen3.5:2b(vision✅), qwen3:0.6b, gpt-4o-mini, kimi-k2.6(cloud), minimax-m2.7(cloud) | |
| MiniCPM-V | 🔄 拉取中 | 6%, ~43min 剩余 |
| Qwen2.5-VL-7B | 🔄 拉取中 | 5%, ~61min 剩余 |
| Hermes (8642) | ✅ 在线 | Marvis 扫描确认 |
| Codex (G盘配置) | ✅ 配置完好 | GUI 待用户重开验证 |
| Claude Code | ✅ ORCA 内在线 | — |
| Git 仓库 | ✅ main 分支 | 多智能体舰队编排/ 待提交 |
| 旧 E:\fleet_exchange\ | ⚠️ DEPRECATED | 保留只读副本 |

## 六、下一步

- [x] ~~目录迁移~~
- [x] ~~脚本升级到 v2.0~~
- [x] ~~全链路闭环验证~~
- [x] ~~Ollama 启动 + 视觉模型拉取~~ (进行中)
- [x] ~~Marvis 端点扫描~~ (进行中)
- [ ] Git commit 提交到仓库
- [ ] 用户重开 ORCA 验证 Codex GUI 标签页
- [ ] 用实际截图跑 Ollama 视觉解析对比 HY3
- [ ] 填写完整测评矩阵
