# 企业微信群定制接单项目 · Claude Code 配置

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

# 2. 检查 Codex CLI shim（MODULE_NOT_FOUND 修复）
if [ ! -f ~/AppData/Roaming/npm/codex ]; then
  echo "Codex CLI shim 缺失，正在创建..."
  cat > ~/AppData/Roaming/npm/codex << 'SHIM'
#!/bin/sh
exec node "I:/npm/node_modules/@openai/codex/bin/codex.js" "$@"
SHIM
  chmod +x ~/AppData/Roaming/npm/codex
fi

# 3. 同步 Codex 运行时配置
cp ~/.codex/config.toml ~/AppData/Roaming/Orca/codex-runtime-home/home/config.toml 2>/dev/null

# 4. 验证 API 连通
curl -s http://127.0.0.1:15730/health && echo " Codex Proxy OK"
curl -s http://127.0.0.1:15721/health && echo " Anthropic Proxy OK"

# 5. 完整就绪检查（可选，需要更多时间）
# bash scripts/fleet_auto_ready.sh
```

## 项目约定

- **模型**：mimo-v2.5-pro（通过 xiaomimimo20260612 provider）
- **Codex 代理端口**：15730（codex_tool_proxy.py）
- **Anthropic 代理端口**：15721（anthropic_proxy_15721.py）
- **代理脚本位置**：E:\龙虾AI主控中心\MCP服务\
- **启动脚本**：scripts/fleet_auto_restore.cmd（开机自启计划任务 LobsterFleet_AutoRestore）
- **一键启动**：`bash scripts/launch_all_agents.sh`（三Agent同时拉起）
- **全项目同步**：`bash scripts/sync_scaffold_to_all.sh`（脚手架变更后同步全部8个Orca项目）

## 分支结构

| 分支 | 用途 | Worktree 路径 |
|------|------|---------------|
| master | 主分支（Hermes 工作） | 项目根目录 |
| claude/reviewer | Claude Code 工作 | worktrees/claude |
| codex/executor | Codex 工作 | worktrees/codex |
| hermes/brain | Hermes 辅助 | worktrees/hermes |

## 禁止事项

- **禁止修改 ~/.codex/config.toml 的 wire_api 和 base_url**（会导致 401 错误）
- **禁止直接修改代理脚本端口号**（会导致端口冲突）
- **禁止跳过自动恢复直接开始任务**（可能导致代理未就绪）
