# 龙虾舰队共享记忆

> 此文件由 Hermes Agent 维护，Codex/Claude Code 可读取。
> 最后更新：2026-07-28

## 项目概况
- 项目：企业微信群定制接单项目
- 路径：E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目
- 分支：master + hermes/brain + codex/executor + claude/reviewer（已同步至 0da8369）

## 代理服务
- Anthropic 代理：端口 15721，脚本 E:\龙虾AI主控中心\MCP服务\anthropic_proxy_15721.py
- Codex 工具代理：端口 15730，脚本 E:\龙虾AI主控中心\MCP服务\codex_tool_proxy.py
- 一键启动：scripts/fleet_startup.cmd
- 计划任务：AnthropicProxy_AutoStart + CodexToolProxy_AutoStart（开机自启）
- 系统 Python：C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe

## 技能库位置
- 龙虾五步法 v2.7：E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v2.7\SKILL.md
- 全域蒸馏引擎 v2.7 R66：E:\龙虾AI主控中心\我的AI分身\技能库\self-skill\self-skill_01_龙虾全域蒸馏引擎_v2.7_R66.txt
- 龙虾五步法 R66：E:\龙虾AI主控中心\我的AI分身\技能库\self-skill-龙虾五步法_v2.7_R66.md

## 模型配置
- 三个 Agent 均使用 MiMo v2.5 Pro（xiaomimimo）
- MiMo 中文好、价格低，量化/复杂推理中等，关键决策可切 GPT-5.5

## 快照
- 位置：snapshots/fleet_snapshot_*.tar.gz（44KB）
- 内容：代理脚本 + 启动脚本 + 计划任务注册 + 配置 + 技能文件

## 重要经验
- 代理服务必须用系统 Python（3.13.12），不用 Hermes venv
- 工作树分支合并用 git merge master --no-edit（fast-forward）
- 文件共享通过 git merge 实现，不通过复制粘贴
