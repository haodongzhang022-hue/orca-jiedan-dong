# ORCA 工作树设置脚本（全域模板 #290）

> 本目录包含 ORCA 多 Agent 工作树的快速启动配置，解决「只显示名称、无参数填充」「反复点运行」的痛点。

## 一、贴入 ORCA 的设置脚本（每个工作树都贴同一行）

打开 ORCA 左侧工作树面板 → 选中 `hermes/brain` / `codex/executor` / `claude/reviewer` 中任意一个 → 在底部「添加设置脚本」输入框里粘贴：

```bash
bash ../../scripts/orca_setup_worktree.sh
```

点击「配置」保存。关闭当前工作树终端，重新打开后脚本自动运行，当前工作树根目录会生成 `.env`：

```env
ORCA_ROOT_PATH=E:\龙虾AI主控中心\我的AI分身\你的项目名称
ORCA_WORKTREE_PATH=E:\...\worktrees\hermes
ORCA_WORKSPACE_NAME=你的项目名称
AGENT_ROLE=hermes
GH_PROXY=https://gh-proxy.com
```

## 二、为什么只需要同一行命令

`scripts/orca_setup_worktree.sh` 会根据当前工作树目录名自动识别角色：

- 在 `worktrees/hermes` 里运行 → `AGENT_ROLE=hermes`
- 在 `worktrees/codex` 里运行 → `AGENT_ROLE=codex`
- 在 `worktrees/claude` 里运行 → `AGENT_ROLE=claude`

因此同一个脚本同时适用于三个工作树，无需维护三份脚本。

## 三、各 Agent 角色提示（中文交互式启动）

进入对应工作树后，把 `config/orca/hermes_system_prompt.md` / `codex_system_prompt.md` / `claude_system_prompt.md` 的第一段复制到 Agent 对话窗口作为开场 system prompt，即可让 Agent 以中文角色身份开始工作。

## 四、配套脚本

- `scripts/orca_setup_worktree.sh`：工作树环境注入（本配置核心）
- `scripts/orca_push_all.sh`：一键推送全部分支到 GitHub（走 gh-proxy）
- `scripts/orca_backup.sh`：非破坏性快照三个工作树到 `backups/`

## 五、故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| `.env` 路径变成 `\\c\\...` | 使用了 Git Bash `/c/` 写法 | 脚本已用 `cygpath -w` 归一化，无需处理 |
| 角色识别错误 | 当前目录不是 `worktrees/hermes` 等 | 确认 ORCA 终端启动目录为工作树根 |
| 重新打开未自动执行 | 设置脚本未保存 | 重新粘贴并点「配置」 |
