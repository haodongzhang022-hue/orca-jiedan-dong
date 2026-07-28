# 龙虾舰队轻量快照 - 2026-07-28

## 快照信息
- 创建时间：2026-07-28 21:44
- 大小：44KB（远低于20MB限制）
- 用途：服务恢复 + 技能备份 + 配置备份

## 恢复方法

### 一键恢复（推荐）
```bash
# 解压快照
tar -xzf fleet_snapshot_*.tar.gz

# 注册计划任务（开机自启）
cd fleet_snapshot_*/
cmd.exe /c register_scheduled_tasks.cmd

# 立即启动服务
cmd.exe /c fleet_startup.cmd
```

### 手动恢复
```bash
# 1. 启动 Anthropic 代理（Claude Code 依赖）
python anthropic_proxy_15721.py

# 2. 启动 Codex 工具代理
python codex_tool_proxy.py
```

## 包含内容
| 文件 | 用途 |
|------|------|
| anthropic_proxy_15721.py | Anthropic→OpenAI协议转换代理 |
| codex_tool_proxy.py | Codex工具代理 v5 |
| fleet_startup.cmd | 一键启动脚本 |
| register_scheduled_tasks.cmd | 计划任务注册 |
| registry.json | 项目注册表 |
| lobster_five_step_v2.7_SKILL.md | 龙虾五步法 v2.7 |
| self-skill_01_龙虾全域蒸馏引擎_v2.7_R66.txt | 全域蒸馏引擎 |
| self-skill-龙虾五步法_v2.7_R66.md | 龙虾五步法 R66 |
| 六实例融合改造方案.md | 架构方案 |
| .claude_mcp_config.json | Claude MCP配置 |
| .codex_mcp_config.json | Codex MCP配置 |
| codex_config.toml | Codex完整配置 |

## 端口映射
| 服务 | 端口 | 依赖方 |
|------|------|--------|
| Anthropic 代理 | 15721 | Claude Code |
| Codex 工具代理 | 15730 | Codex CLI |
| CC-Switch | 57320/57321 | Orca IDE |
