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
- **Codex 代理端口**：15730（codex_tool_proxy.py v8，Responses API 直接透传）
- **Anthropic 代理端口**：15721（anthropic_proxy_15721.py）
- **代理脚本位置**：E:\\龙虾AI主控中心\\MCP服务\\
- **三引擎快照**：E:\\龙虾AI主控中心\\MCP服务\\snapshots\\three_engine_snapshot_*.tar.gz（含一键恢复脚本）
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

## 快速指令（中文关键词自动触发）

当用户输入以下中文关键词时，**立即执行对应的 bash 命令**，不要问"你确定吗"：

| 用户输入 | 执行命令 | 说明 |
|----------|----------|------|
| 一键恢复 | `lobster-cmd 一键恢复` | 检查三引擎+自动恢复+自动快照 |
| 龙虾五步法 | `lobster-cmd 一键恢复` | 同上 |
| 全域模板 | `lobster-cmd 全域模板` | 显示模板路径+指令说明 |
| 三引擎状态 | `lobster-cmd 状态` | 查看端口/health/配置 |
| 快照 | `lobster-cmd 快照` | 创建轻量快照 <20MB |
| 迭代 | `lobster-cmd 迭代` | 龙虾五步法+全域模板+四化→知识库+脚手架 |
| 四化 | `lobster-cmd 四化` | 显示四化校准+执行自我进化 |
| 设计单/接单 | 打开 `docs/设计类商单流水线.md` | 自动唤起设计类商单流水线，开始 Step1 接单解析 |
| 网页设计 | 打开 `docs/设计类商单流水线.md` 第三节 | 唤起网页设计专项（HTML+CSS） |
| 交付/上传 | `git push origin main && git push direct main` | 双仓库上传：CNB云原生+GitHub |

**重要**：执行完命令后，将输出结果直接返回给用户。如果代理已正常运行，命令会自动跳过恢复步骤，不影响任何对话和任务数据。

## 四化校准（核心哲学）

| 维度 | 定义 | 执行标准 |
|------|------|----------|
| **智能化** | AI员工自主工作（不是辅助） | 不问用户，自主决策执行 |
| **定制化** | 蒸馏思维方式 | 从订单逆向工程→知识沉淀 |
| **全自动化** | 一公司一人 | 所有流程一键触发，零人工干预 |
| **自我净化** | 自我进化（不是缓存清理） | 每次迭代优化脚手架+知识库 |

### 迭代触发流程

当用户说"迭代"时，自动执行：
1. **龙虾五步法**：识别→映射→规划→执行→沉淀
2. **全域模板**：对齐 E:\龙虾AI主控中心\我的AI分身\技能库\龙虾全域官方模板-最终版.md
3. **四化校准**：检查智能化/定制化/全自动化/自我净化
4. **知识库更新**：迭代到 Obsidian 主库
5. **脚手架同步**：更新项目脚手架（通用部分同步全部项目）

### 系统自愈方案（v2）

**守护进程**：`E:\龙虾AI主控中心\MCP服务\fleet_guardian.py`
- 开机自启：计划任务 `FleetGuardian_AutoStart`
- 崩溃自动重启：30秒检测一次
- 端口冲突检测：自动杀死占用端口的非预期进程（如Marvis）
- 日志：`E:\龙虾AI主控中心\MCP服务\logs\guardian_*.log`

**手动操作**：
```bash
# 启动守护进程
python "E:/龙虾AI主控中心/MCP服务/fleet_guardian.py"

# 查看日志
tail -20 "E:/龙虾AI主控中心/MCP服务/logs/guardian_$(date +%Y%m%d).log"

# 手动注册计划任务
schtasks /create /tn "FleetGuardian_AutoStart" /tr "python fleet_guardian.py --daemon" /sc onlogon /f
```

## 龙虾知识库（第二大脑）

- **Obsidian主库**：E:\龙虾AI主控中心\Obsidian\（junction→G盘）
- **知识库宪法**：E:\龙虾AI主控中心\Obsidian\AGENTS.md
- **Wiki索引**：E:\龙虾AI主控中心\Obsidian\wiki\index.md
- **技能库**：E:\龙虾AI主控中心\我的AI分身\技能库\

### 知识库工作流

1. **查知识**：先查 wiki/ 层，必要时回看 raw/ 层
2. **学新知**：丢链接 → Hermes提取 → raw/入档 → wiki/蒸馏
3. **沉淀技能**：wiki/成熟后 → 蒸馏到 技能库/课程知识技能/xx领域/SKILL.md
4. **引用知识**：在代码和文档中用 `[[笔记名]]` 双向链接

### 龙虾五步法与知识库

| 五步法 | 知识库操作 |
|--------|----------|
| Step1 识别 | 检查 wiki/ 是否有相关知识 |
| Step2 映射 | 从 wiki/ 提取方法论 |
| Step3 规划 | 参考 项目交付/项目规范总览 |
| Step4 执行 | 执行过程中记录到 daily/ |
| Step5 沉淀 | 蒸馏到 wiki/ + SKILL.md |
