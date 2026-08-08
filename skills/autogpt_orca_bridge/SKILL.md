---
skill_id: "autogpt_orca_bridge"
name: "AutoGPT 接单桥接"
description: "AutoGPT 融合 ORCA 全链路接单技能。自然语言任务 → 四赛道映射（网盘萃取/企业接单/闲鱼自动化/量化策略）→ 落地任务卡到 fleet_exchange → 调度 ORCA 工作流入口。触发词：AutoGPT接单、autogpt调度、自动拆解任务、一键接单。"
version: "1.0.0"
category: "龙虾舰队流水线 · 商单接单技能库"
triggers:
  - "AutoGPT接单"
  - "autogpt调度"
  - "自动拆解任务"
  - "一键接单"
  - "任务自动分发"
inputs:
  - "自然语言接单需求（客户需求 / 任务 JSON / Markdown）"
  - "赛道选择：网盘萃取 / 企业接单 / 闲鱼自动化 / 量化策略"
outputs:
  - "fleet_exchange/incoming/ 任务卡"
  - "四赛道工作流执行结果"
  - "SelfLearn_Record.md 自我净化记录"
capabilities:
  - "自然语言任务解析（JSON / Markdown / 纯文本）"
  - "四大赛道工作流映射与调度"
  - "任务卡自动落地 fleet_exchange（复用 Maris 投递格式）"
  - "超时保护 + 失败自我净化记录"
limitations:
  - "密钥零硬编码，一律从环境变量读取（CNB_TOKEN/GH_TOKEN/Cookie）"
  - "不直接操作 Windows 本地系统（E盘/Obsidian/schtasks 由 Marvis 本机执行）"
  - "AutoGPT 本地面板部署（E:/龙虾AI主控中心/AutoGPT-Agent）需在本地完成"
lobster_five_steps:
  step1: "精准备份 — 确认任务输入与目标赛道，不修改源文件"
  step2: "根因诊断 — 解析自然语言需求 → 映射四赛道入口脚本"
  step3: "无命令不执行 — 按 WORKFLOW_REGISTRY 参数模板调度，不擅自加步骤"
  step4: "验证修复 — 校验入口脚本存在性、执行结果 rc、超时保护"
  step5: "沉淀归档 — 任务卡入库 fleet_exchange + 写入 SelfLearn_Record.md"
entry_script: "scripts/auto_gpt_orca_bridge.py"
config_files:
  - "config/autogpt/triggers.yaml"
  - "config/autogpt/xianyu_config.yaml"
  - "config/autogpt/quant_config.yaml"
templates:
  - "templates/autogpt/lobster_five_step_autogpt_template.yaml"
local_exec_by: "Marvis（本机）"
---

# AutoGPT 接单桥接技能

## 1. 触发方式
当用户输入包含以下关键词时，自动激活本技能：
AutoGPT接单、autogpt调度、自动拆解任务、一键接单、任务自动分发。

## 2. 核心资产（CNB 云端仓库内，PR #21 落地）
| 文件 | 作用 |
|------|------|
| `scripts/auto_gpt_orca_bridge.py` | 桥接核心：AutoGPT 顶层入口 → 四赛道映射 → 调度 ORCA 工作流 |
| `scripts/auto_xianyu_scheduler.py` | 闲鱼自动化业务源码（定时上架/客服回复/爬虫轮询/风控限速，不含 schtasks） |
| `scripts/quant_scheduler.py` | 嘉盛/币安双仓巡检业务源码（双仓巡检/Marvis 三端一致性校验） |
| `scripts/auto_gpt_trigger_config.py` | 触发器配置解析/参数校验，输出结构化任务清单 JSON |
| `templates/autogpt/lobster_five_step_autogpt_template.yaml` | 龙虾五步法拖拽模板（5 节点 + 四赛道预设 + ≥80→PRODUCTION） |
| `config/autogpt/*.yaml` | 触发器/闲鱼/量化业务参数 |
| `local_job_queue.json` | 云端→本机任务清单（task_name/file_path/params） |

## 3. 执行流程（云端容器内可直接跑）
```
1. 解析任务输入（JSON / Markdown / 纯文本）
2. 映射四赛道工作流：
   网盘萃取 → auto_knowledge_extract.py
   企业接单 → maris_dispatch.sh
   闲鱼自动化 → auto_xianyu_scheduler.py
   量化策略  → quant_scheduler.py
3. 落地任务卡到 fleet_exchange/incoming/
4. 调度对应入口脚本（600s 超时保护）
5. 结果写入 SelfLearn_Record.md（自我净化）
```

## 4. 快速命令
```bash
# 状态检查（四赛道入口 + 环境变量存在性）
python3 scripts/auto_gpt_orca_bridge.py status

# 企业接单：自然语言需求直接调度
python3 scripts/auto_gpt_orca_bridge.py dispatch \
  --task '{"title":"客户LOGO设计","type":"设计","priority":"高"}' \
  --workflow 企业接单

# 定时触发器入口
python3 scripts/auto_gpt_orca_bridge.py trigger \
  --workflow 量化策略 --title "双仓巡检" --desc "每日巡检"
```

## 5. 云端 vs 本地边界
- **云端（CNB 容器）**：跑桥接脚本、落地任务卡、调度四赛道入口、产出源码/脚本/YAML/文档。
- **本地（Marvis）**：AutoGPT 面板部署（`E:/龙虾AI主控中心/AutoGPT-Agent`）、Windows 计划任务、E/G 双盘落盘、Obsidian 归档。
- 云端**不执行** schtasks、不访问 E 盘、不操作本地系统；待本地执行项统一写 `local_job_queue.json`。

## 6. 安全红线
- 密钥零硬编码：`CNB_TOKEN` / `GH_TOKEN` / 抖音/小红书 Cookie 一律环境变量注入，脚本只做存在性校验。
- 复用现有 DPAPI Cookie 解密与鉴权体系。

## 7. 关联
- 上游入口：AutoGPT 面板（本地自然语言顶层入口）
- 下游消费：fleet_exchange 接单流水线（5WorkBody舰队编排 / 企业接单群舰队编排）
- 文档：`docs/AutoGPT融合ORCA全链路验收文档.md`、`docs/云端产物交付清单.md`
