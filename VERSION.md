# 版本信息
version: 1.8.1
release_date: 2026-08-09
base_model: CNB内置免费DeepSeek-V4-Flash (MoE 284B/激活13B)
base_model_valid_until: 2026-12-31
changes:
  - 【配额/容器/可视化文档】Issue#27 交付 docs/配额与消耗查询图文操作手册.md + docs/配额容器可视化三问速查小抄.md（官方定价文档+构建记录实测，v1.8.0→1.8.1）
  - 【Hermes Studio 全自动落地 v2.0】Issue#27 全权授权 MARVIS 零操作：docs/Marvis配合执行方案_HermesStudio全自动_v2.0.md（v1.0→v2.0，下载校验+静默安装+桥接全自动）
  - 【云上复刻】.ide/Dockerfile + .ide/start.sh + .cnb.yml vscode 事件：把 Hermes Studio Web GUI(6060) 打进 CNB 云原生开发环境，浏览器 https://{id}-6060.cnb.run 直接访问，后台拉起 CNB 免费网关适配层(127.0.0.1:8787)
  - 【群聊痕迹墙】scripts/cnb_echo_ping.sh + docs/Hermes_Studio_群聊痕迹墙_接入说明.md：云端 NPC(hermes/codex/claude-code)交流写痕迹到 msgbus/inbox/echo_wall/，Hermes Studio 桌面版可见；各角色 prompt 追加 echo 规则（.cnb/settings.yml）
  - 【一键技能】skills/hermes-studio-cnb/SKILL.md + scripts/one_click_cnb_gateway.sh：一键接入 CNB 免费基座 deepseek-v4-flash，本地 Hermes Studio 桌面编排→CNB 免费网关，0 成本；skill_registry.json 注册 v1.0.0
  - 【AutoGPT融合·第二轮】Issue#10 云端容器内交付：新增闲鱼/量化两赛道入口脚本 + 触发器脚本重构为仅配置解析+校验 + 云端产物交付清单（v1.7.0 → 1.7.1）
  - 【AutoGPT融合·第二轮】scripts/auto_xianyu_scheduler.py 闲鱼自动化业务源码（定时上架/客服回复/数据统计/爬虫轮询+风控限速，不含 schtasks）
  - 【AutoGPT融合·第二轮】scripts/quant_scheduler.py 嘉盛/币安双仓巡检业务源码（余额/持仓/挂单/回撤告警/Marvis 三端一致性校验，不含 schtasks）
  - 【AutoGPT融合·第二轮】scripts/auto_gpt_trigger_config.py 重构：移除 schtasks 直接执行代码，仅封装配置解析+参数校验，输出结构化任务清单 JSON（validate/export/show）
  - 【AutoGPT融合·第二轮】config/autogpt/ 新增 triggers.yaml + xianyu_config.yaml + quant_config.yaml（触发器/业务参数统一收口）
  - 【AutoGPT融合·第二轮】local_job_queue.json 云端→本机任务清单（task_name/file_path/params 供 Marvis 部署消费）
  - 【AutoGPT融合·第二轮】docs/云端产物交付清单.md 新增（标注需 Marvis 本机部署执行的文件）
  - 【AutoGPT融合】Issue#10 新任务：AutoGPT 融合 ORCA 全链路，升级自主智能体能力（版本 1.6.1 → 1.7.0）
  - 【AutoGPT融合】scripts/auto_gpt_orca_bridge.py 桥接脚本（AutoGPT×四大赛道，密钥零硬编码）
  - 【AutoGPT融合】templates/autogpt/lobster_five_step_autogpt_template.yaml 五步法可视化拖拽模板
  - 【AutoGPT融合】scripts/auto_gpt_trigger_config.py 定时触发器配置（schtasks 同步 G 盘）→ v1.7.1 重构为仅配置解析+校验（见上）
  - 【AutoGPT融合】docs/AutoGPT融合ORCA全链路验收文档.md + SelfLearn_Record.md 自我净化闭环
  - Claude-Code封装为CNB云端NPC（@claude-code触发）
  - 接口适配层 adapters/anthropic_to_cnb.py：Anthropic协议→CNB内置AI网关
  - npc:go options.model=deepseek-v4-flash 显式绑定免费基座
  - 额度监控与降级保护 scripts/quota_monitor.py（1600核时/月）
  - GitHub私有仓库导出包 + E盘/G盘镜像清单脚本
  - Issue#10 实测通过：@claude-code 唤起Agent完成文件创建+PR提交+评论回写
  - 【路径B增强】自定义Docker镜像容器模式：完整原版Claude-Code CLI + 适配层(127.0.0.1:8787)
  - 【路径B】.ci/npc-full.yml claude-code角色流水线（覆盖$兜底，独立容器执行）
  - 【路径B】adapters/Dockerfile 构建镜像 + main.push 自动构建推送流水线
  - 【路径B】docs/claude_code_cloud_vs_local.md A/B双模式对比文档
  - 【路径B·修订】Dockerfile 改为 ENTRYPOINT+CMD：容器启动后台拉起适配层监听 127.0.0.1:8787
  - 【路径B·修订】镜像构建流水线变量修正：main.push 用 CNB_REPO_SLUG_LOWERCASE（NPC变量不注入）
  - 【路径B·修订】.ci/npc-full.yml NPC_MODEL 与 options.model 双保险强制锁定 deepseek-v4-flash
  - 【路径B·修订】脚手架模板 templates/cnb_npc_path_b_scaffold 补齐全部文件（Dockerfile/适配层/entrypoint/quota/docs）
  - 【v1.6.0·新增】GitHub 原生 Hermes CLI（NousResearch/hermes-agent）接入 CNB NPC 舰队
  - 【v1.6.0·新增】.ci/hermes.yml hermes 角色路径B流水线（@hermes 触发，独立容器执行）
  - 【v1.6.0·新增】hermes/entrypoint.sh + adapters/hermes_entry.sh 原生 hermes 安装/入口
  - 【v1.6.0·新增】.cnb/settings.yml 注册 hermes 角色（大脑层·战略调度人设）
  - 【v1.6.0·修订】adapters/Dockerfile 内置 hermes CLI + claude/hermes 双入口
  - 【v1.6.0·修订】镜像版本 1.5.0 → 1.6.0，构建/推送流水线同步
  - 【v1.6.0·同步】templates/cnb_npc_path_b_scaffold 脚手架模板整体升级
  - 【v1.6.0·新增】原生 Codex CLI（@openai/codex，bin=codex.js，linux-x64 二进制）打包进镜像
  - 【v1.6.0·新增】.ci/codex.yml codex 角色路径B流水线（@codex 触发，独立容器执行）
  - 【v1.6.0·修订】codex 角色从路径A（$ 兜底 npc:go 轻量化）升级为路径B（自定义镜像+原生完整 CLI）
  - 【v1.6.0·修订】路径B 三个角色（claude-code/hermes/codex）maxTurns 24 → 60，修复
    "Agent aborted: reached maxTurns limit (24)" 导致 @claude-code/@hermes 执行失败问题
  - 【v1.6.0·同步】脚手架模板同步 codex 路径B流水线 + Dockerfile 双 CLI 内置
  - 【v1.6.0·新增】scripts/one_click_npc_stack.sh 四角色栈一键自检（Codex/Hermes/Claude-Code 版本校验 + 8787 端口探活 + 基座锁定确认）
  - 【v1.6.0·修订】docs/claude_code_cloud_vs_local.md 更新四角色矩阵 + 全链路拓扑（claude-code/hermes/codex 路径B + lobster 路径A）
  - 【v1.6.0·闭环】Issue#10 分阶段执行验收：PR#13/14/15 合并 + 镜像 orca-jiedan:1.6.0 构建推送（cnb-e88 success）
  - 【v1.6.0·闭环】实测证据：@claude-code（cnb-1mo）AI用量审计 39请求/milli_credit=0；@codex（cnb-4b5）触发 success，基座 deepseek-v4-flash
  - 【v1.6.0·新增】docs/四角色矩阵_验收报告_v1.6.0_20260807.md 分阶段执行闭环验收报告
  - 【v1.6.0·新增】docs/双盘备份与Obsidian归档清单_v1.6.0.md + scripts/archive_obsidian_v1.6.0.sh（E/G双盘+Obsidian 归档）
  - 【v1.6.0·修订】skill_registry.json CNB_ClaudeCode_NPC 1.5.0 → 1.6.0（四角色矩阵）
  - 【v1.6.0·修订】scripts/export_to_github_and_mirror.sh 版本 1.5.0→1.6.0 + 四角色栈复制（hermes/codex 资产入库）
  - 【v1.6.1·修订】Hermes 调度改版：全域模板全英文调度 → 全域模板调度（中文），强化多 Agent 任务编排（hermes/system_prompt.md、.cnb/settings.yml、config/orca、脚手架模板、docs 矩阵同步）
  - 【v1.6.1·修复】路径B 三角色（claude-code/hermes/codex）maxTurns 60 → 100：跨仓库编排任务
    （合并PR→等镜像构建→逐仓克隆验收→触发NPC）单次消耗轮次超 60，构建 cnb-p0o-1jvgj2pvt 实证
    "Agent aborted: reached maxTurns limit (60)"；脚手架模板同步
  - 【v1.6.1·修复】docs/claude_code_cloud_vs_local.md 补充 maxTurns 调优说明
