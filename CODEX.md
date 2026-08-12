# {project_name} · Codex 配置

## 自动恢复协议（每次会话启动时执行）

**你进入此项目时，必须先执行以下恢复检查：**

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
curl -s http://127.0.0.1:15730/health && echo " Codex Proxy OK"
curl -s http://127.0.0.1:15721/health && echo " Anthropic Proxy OK"
```

## 项目约定

- **模型**：mimo-v2.5-pro（通过 aicodeswitch provider）
- **Codex 代理端口**：15730
- **Anthropic 代理端口**：15721
- **代理脚本位置**：E:\龙虾AI主控中心\MCP服务\

## 禁止事项

- 禁止修改 ~/.codex/config.toml 的 wire_api 和 base_url
- 禁止直接修改代理脚本端口号
- 禁止跳过自动恢复直接开始任务

## 快速指令（中文关键词自动触发）

当用户输入以下中文关键词时，**立即执行对应的 bash 命令**，不要问"你确定吗"：

| 用户输入 | 执行命令 | 说明 |
|----------|----------|------|
| 一键恢复 | `lobster-cmd 一键恢复` | 检查三引擎+自动恢复+自动快照 |
| 龙虾五步法 | `lobster-cmd 一键恢复` | 同上 |
| 全域模板 | `lobster-cmd 全域模板` | 显示模板路径+指令说明 |
| 三引擎状态 | `lobster-cmd 状态` | 查看端口/health/配置 |
| 快照 | `lobster-cmd 快照` | 创建轻量快照 <20MB |
| 设计单/接单 | 打开 `docs/设计类商单流水线.md` | 自动唤起设计类商单流水线，开始 Step1 接单解析 |
| 网页设计 | 打开 `docs/设计类商单流水线.md` 第三节 | 唤起网页设计专项（HTML+CSS） |
| 交付/上传 | `git push origin main && git push direct main` | 双仓库上传：CNB云原生+GitHub |

**重要**：执行完命令后，将输出结果直接返回给用户。如果代理已正常运行，命令会自动跳过恢复步骤，不影响任何对话和任务数据。


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
