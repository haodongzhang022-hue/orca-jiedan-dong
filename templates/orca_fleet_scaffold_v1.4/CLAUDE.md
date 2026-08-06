# {project_name} · Claude Code 配置

## 自动恢复协议（每次会话启动时执行）

**你进入此项目时，必须先执行以下恢复检查，不需要用户手动输入任何命令：**

```bash
# 1. 检查代理服务是否运行
for port in 15721 15730; do
  if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
    echo "端口 $port 未运行，正在拉起..."
    if [ "$port" = "15721" ]; then
      start //min "AutoRestore-15721" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
    elif [ "$port" = "15730" ]; then
      start //min "AutoRestore-15730" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"
    fi
    sleep 3
  fi
done

# 2. 验证 API 连通
curl -s http://127.0.0.1:15721/health && echo " Anthropic Proxy OK"
curl -s http://127.0.0.1:15730/health && echo " Codex Proxy OK"
```

## 项目约定

- **模型**：mimo-v2.5-pro（通过 xiaomimimo20260612 provider）
- **Anthropic 代理端口**：15721
- **Codex 代理端口**：15730
- **代理脚本位置**：E:\龙虾AI主控中心\MCP服务\

## 禁止事项

- 禁止直接修改代理脚本端口号
- 禁止跳过自动恢复直接开始任务

## 快速指令（中文关键词自动触发）

| 用户输入 | 执行命令 | 说明 |
|----------|----------|------|
| 一键恢复 | `bash .orca/setup.sh` | 检查代理+自动恢复 |
| 三引擎状态 | `bash scripts/orca_project_startup.sh` | 查看端口/health/配置 |

## CNB 云上 NPC（可选）

本仓库已配置 CNB 平台 NPC（codex / claude-code），在 CNB Issue/PR 评论区用
`@TJF19770107/{repo}(claude-code)` 即可召唤云上 Claude Code 角色。
