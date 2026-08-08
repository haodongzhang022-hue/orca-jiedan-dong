# 《AutoGPT 融合 ORCA 全链路验收文档》

> 归属：炼虚合道接单体系 · AutoGPT 融合改造（Issue #10 任务）
> 版本：v1.1.0 ｜ 日期：2026-08-08
> 作者：CodeBuddy（CNB 云原生交付）
> 基座：CNB 内置免费 DeepSeek-V4-Flash（MoE 284B/激活13B，有效期至 2026-12-31）
> 说明：v1.1.0 纳入第二轮迭代（闲鱼/量化赛道入口脚本补齐、触发器脚本重构为仅配置解析+校验、云端产物交付清单）

---

## 一、任务背景

AutoGPT（开源 Python 自主智能体，18.5w+ Star）以自然语言驱动全自动任务拆解，支持可视化拖拽、定时触发器、本地自托管，兼容全系列大模型。本次任务将其融合进现有 ORCA 龙虾全链路，作为**上层任务调度入口**，升级自主智能体能力。

> 约束：**不改动现有成熟 NPC 链式链路**（Issue→codex 拆解→claude 审核→CodeBuddy 交付），AutoGPT 仅作为顶层调度入口叠加在链路上方。

## 二、融合改造总览（四化标准落地）

| 四化 | 落地内容 | 对应产物 |
|------|---------|---------|
| **智能化** | AutoGPT 自然语言任务解析作为顶层入口，无需人工编写分步指令，自主拆分多级子任务 | `auto_gpt_orca_bridge.py dispatch` |
| **定制化** | 基于龙虾五步法、道层五维过滤模型改造 AutoGPT 内置评分机制，≥80 分自动标记商用 PRODUCTION 技能 | `lobster_five_step_autogpt_template.yaml` scoring.pass_score=80 |
| **全自动化** | 融合 Marvis 定时调度，凭证过期巡检、爬虫静默轮询、三端同步全部交由 AutoGPT 后台托管 | `auto_gpt_trigger_config.py`（schtasks 触发器） |
| **自我净化** | AutoGPT 执行失败任务自动生成故障日志，赛博书屋自主学习踩坑方案，沉淀至 C 点进化知识库 | `SelfLearn_Record.md` + bridge 失败自动记录 |

## 三、半云半端架构

```
┌─ 半端（本地 · E:\龙虾AI主控中心\AutoGPT-Agent）──────────────┐
│  AutoGPT 可视化拖拽 / 任务拆解（自然语言 → 多级子任务）          │
│      │                                                        │
│      ▼  scripts/auto_gpt_orca_bridge.py                       │
└────────────────────────────────────────────────────────────────┘
      │ 子进程调度
      ▼
┌─ 半云（CNB 云端容器）─────────────────────────────────────────┐
│  仓颉蒸馏 / MCP 打包（mcp_packager.py）/ ORCA 部署流水线        │
│  （orca_deploy.py）· 现有 NPC 链式链路保持不变                   │
└────────────────────────────────────────────────────────────────┘
```

## 四、配套产出物清单

### 4.1 `scripts/auto_gpt_orca_bridge.py` — 桥接脚本 ⭐核心
打通 AutoGPT 与 `orca_deploy.py`、`mcp_packager.py` 及四大赛道入口：

| 工作流 | 入口脚本 | 说明 |
|--------|---------|------|
| 网盘萃取 | `auto_knowledge_extract.py` | 知识库沉淀需求 → 抓取/过滤/蒸馏/归档 |
| 企业接单 | `maris_dispatch.sh` | 客户需求 → 拆解/报价/方案/交付归档（替代手动 CNB Issue） |
| 闲鱼自动化 | `auto_xianyu_scheduler.py`（待补） | 定时上架/客服回复/数据统计 + 风控限速 |
| 量化策略 | `quant_scheduler.py`（待补） | 币安/嘉盛双仓巡检 + Marvis 三端校验 |

```bash
# 调度任务
python scripts/auto_gpt_orca_bridge.py dispatch --task <任务> --workflow <赛道>
# 状态检查
python scripts/auto_gpt_orca_bridge.py status
# 定时触发入口
python scripts/auto_gpt_orca_bridge.py trigger --workflow 企业接单 --title "客户需求"
```

### 4.2 `templates/autogpt/lobster_five_step_autogpt_template.yaml` — 可视化拖拽预制模板
- 龙虾五步法（精准备份→根因诊断→无命令不执行→验证修复→沉淀归档）蒸馏为 5 个 AutoGPT 可拖拽节点
- 内嵌四大赛道快速模板 + 4 个定时触发器预设
- AutoGPT 面板 → 创建 Agent → 导入工作流模板 → 一键生成

### 4.3 `scripts/auto_gpt_trigger_config.py` — 定时触发器配置脚本
- 将 AutoGPT 定时触发器同步为 Windows schtasks 计划任务
- 与 G 盘 schtasks 同步任务保持一致（G_DRIVE_ROOT 可配置）

```bash
python scripts/auto_gpt_trigger_config.py install   # 安装全部触发器
python scripts/auto_gpt_trigger_config.py list     # 查看
python scripts/auto_gpt_trigger_config.py dryrun   # 预演
```

| 触发器 | 频率 | 工作流 |
|--------|------|--------|
| AG_Xianyu_Post | 每日 09:00 | 闲鱼自动化 |
| AG_Credential_Check | 每日 00:00 | 通用（凭证巡检） |
| AG_Quant_DualCheck | 每 30 分钟 | 量化策略 |
| AG_Crawler_Poll | 每 10 分钟 | 闲鱼自动化（风控限速） |

### 4.4 本验收文档（`docs/AutoGPT融合ORCA全链路验收文档.md`）
- 纳入 `cnb_sync.bat` 同步范围（见下方 cnb_sync 段）

## 五、安全与鉴权（密钥零硬编码）

| 鉴权项 | 读取方式 |
|--------|---------|
| CNB 读写 Token | 环境变量 `CNB_TOKEN` |
| GitHub PAT | 环境变量 `GH_TOKEN` |
| 抖音 Cookie | 环境变量 `DOUYIN_COOKIE` |
| 小红书 Cookie | 环境变量 `XIAOHONGSHU_COOKIE` |
| DPAPI Cookie 解密 | 复用现有解密体系，桥接层不重复实现 |

> 桥接脚本 `_check_env_ready()` 仅做存在性校验，**绝不打印/回写密钥明文**。全部密钥经 CNB 流水线环境变量注入 / 本地 .env（不入 Git）。

## 六、cnb_sync.bat 同步范围纳入

`docs/AutoGPT融合ORCA全链路验收文档.md` 及以下文件纳入同步范围：
- `scripts/auto_gpt_orca_bridge.py`
- `scripts/auto_gpt_trigger_config.py`
- `scripts/auto_xianyu_scheduler.py`
- `scripts/quant_scheduler.py`
- `templates/autogpt/lobster_five_step_autogpt_template.yaml`
- `config/autogpt/triggers.yaml` + `xianyu_config.yaml` + `quant_config.yaml`
- `local_job_queue.json`（云端→本机任务清单）
- `docs/云端产物交付清单.md`
- `SelfLearn_Record.md`

> 同步脚本：`scripts/export_to_github_and_mirror.sh`（E/G 双盘 + Obsidian + CNB 五大仓库）

## 七、第二轮迭代（Issue #10 · 云端容器内交付）

> 边界（用户强制约定）：云端只做容器内工作，不操作 Windows 本地系统；不生成直接执行 schtasks、访问 E:\、读写本地 Obsidian 的执行逻辑；只产出源码/脚本/yaml/文档，全部提交 PR #21。Marvis 在本地拉取仓库文件后做本机执行。

### 7.1 第二轮新增/维护产出物

| # | 文件 | 变更 | 说明 |
|---|------|------|------|
| 1 | `scripts/auto_gpt_orca_bridge.py` | 维护 | 桥接核心确认：网盘萃取/企业接单链路保持实测可用逻辑不变；闲鱼/量化入口补齐 `--action` 参数模板 + `config` 引用 |
| 2 | `scripts/auto_xianyu_scheduler.py` | **新增** | 闲鱼自动化完整业务源码（定时上架/客服回复/数据统计/爬虫轮询+风控限速），不含 schtasks |
| 3 | `scripts/quant_scheduler.py` | **新增** | 嘉盛/币安双仓巡检业务源码（余额/持仓/挂单/回撤告警/Marvis 三端一致性校验），不含 schtasks |
| 4 | `templates/autogpt/lobster_five_step_autogpt_template.yaml` | 维护 | 四赛道预设补充 actions/config；触发器预设与 triggers.yaml 对齐（action 改为结构化值） |
| 5 | `scripts/auto_gpt_trigger_config.py` | **重构** | 仅封装配置解析+参数校验；**移除 schtasks install/uninstall/dryrun 执行代码**；新增 `validate/export/show` 子命令，输出结构化任务清单 JSON |
| 6 | `config/autogpt/triggers.yaml` | **新增** | 触发器配置统一入口（cron/schedule_human/workflow/params） |
| 7 | `config/autogpt/xianyu_config.yaml` | **新增** | 闲鱼赛道业务参数（时间窗/批次/限速/风控） |
| 8 | `config/autogpt/quant_config.yaml` | **新增** | 量化赛道业务参数（双仓/阈值/三端校验/回撤） |
| 9 | `local_job_queue.json` | **新增** | ⭐ 云端→本机任务清单：task_name/file_path/params 统一标记，供 Marvis 本地部署消费 |
| 10 | `docs/云端产物交付清单.md` | **新增** | 说明哪些文件需 Marvis 本机部署执行 |

### 7.2 触发器脚本重构要点

旧版 `auto_gpt_trigger_config.py` 直接生成并调用 schtasks（`install/uninstall/dryrun`）。重构后：

- ✅ 仅封装配置解析 + 参数校验（`validate`）
- ✅ 输出结构化任务清单 JSON 到 `local_job_queue.json`（`export`）
- ✅ 触发器参数/调度配置统一在 `config/autogpt/triggers.yaml`
- ❌ 已移除：schtasks /create、/delete、/sc 等全部直接执行代码

```bash
python scripts/auto_gpt_trigger_config.py validate   # 校验触发器配置
python scripts/auto_gpt_trigger_config.py export     # 生成 local_job_queue.json
python scripts/auto_gpt_trigger_config.py list       # 查看触发器摘要
```

## 八、验收核对项

- [x] 桥接脚本可运行（`status` / `dispatch` / `trigger` 三子命令验证）
- [x] 模板 YAML 通过解析校验（pyyaml safe_load）
- [x] 触发器脚本重构为仅配置解析+参数校验，输出结构化任务清单 JSON（validate/export 验证）
- [x] `local_job_queue.json` 已生成，标记 4 个待本地执行任务（task_name/file_path/params）
- [x] 闲鱼/量化赛道入口脚本补齐（`auto_xianyu_scheduler.py` / `quant_scheduler.py`）
- [x] 密钥零硬编码，全部环境变量注入
- [x] 不改动现有 NPC 链式链路（Issue→codex→claude→CodeBuddy 保持原样）
- [x] 不含任何 schtasks 创建命令 / E 盘 / 本地 Obsidian 访问逻辑（仅含配置与业务逻辑）
- [ ] 本地 AutoGPT 私有化部署（`E:\龙虾AI主控中心\AutoGPT-Agent`，需在本地 Windows 执行）
- [ ] G 盘 schtasks 同步 + Obsidian 录入（按 local_job_queue.json 由 Marvis 本地执行）

## 九、龙虾五步法闭环

| 五步法 | 本任务对应 |
|--------|-----------|
| Step1 精准备份 | 梳理现有 ORCA 全链路/四大赛道/五步法模板/环境变量体系 |
| Step2 根因诊断 | 识别 AutoGPT 融合点：上层调度入口 + 四大赛道映射 + 触发器 |
| Step3 无命令不执行 | 第二轮交付：闲鱼/量化入口脚本 + 触发器配置解析重构 + 云端产物交付清单 |
| Step4 验证修复 | pyyaml 校验 / 脚本语法检查 / validate+export 预演 / status 健康检查 |
| Step5 沉淀归档 | SelfLearn_Record.md + VERSION.md + docs 入库 + PR #21 提交 |

---

*本文档由 CodeBuddy 在 CNB 云端容器生成，全程使用 CNB 内置免费 DeepSeek-V4-Flash 基座，未调用外部付费 API。*
