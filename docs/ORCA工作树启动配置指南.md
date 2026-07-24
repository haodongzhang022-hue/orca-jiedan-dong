# ORCA 工作树启动与 Agent 绑定配置指南（全域模板 #290）

> 目标：让 `hermes/brain`、`codex/executor`、`claude/reviewer` 三个工作树打开后，自动注入环境变量并进入中文角色状态，无需反复点击运行或手动填参数。

---

## 一、痛点与解决

| 痛点 | 解决方案 |
|------|----------|
| 只显示工作树名称，没有 ORCA_ROOT_PATH / AGENT_ROLE 等参数 | 使用统一的 `scripts/orca_setup_worktree.sh` 注入 `.env` |
| 每个工作树要单独写脚本，反复点运行 | 三个工作树贴同一行命令，脚本自动按目录名识别角色 |
| Agent 启动后无中文角色上下文 | 提供 `config/orca/hermes_system_prompt.md` 等角色提示词，粘贴后生效 |
| GitHub 推送搁置，受死代理影响 | 提供 `scripts/orca_push_all.sh`，走 `gh-proxy` 并强制绕过系统代理 |

---

## 二、ORCA 中贴入设置脚本（每工作树 5 秒）

1. 在 ORCA 左侧工作树列表中，依次点开：
   - `hermes/brain` → `worktrees/hermes`
   - `codex/executor` → `worktrees/codex`
   - `claude/reviewer` → `worktrees/claude`
2. 找到底部「添加设置脚本」输入框。
3. 粘贴同一行命令（已在 `config/orca/setup_one_liner.txt` 中备好）：

   ```bash
   bash ../../scripts/orca_setup_worktree.sh
   ```

4. 点击「配置」保存。
5. 关闭当前工作树终端，重新打开。脚本自动执行，输出：

   ```
   ✅ Hermes / 大脑层 已就绪
      工作目录：E:\...\worktrees\hermes
      项目：企业微信群定制接单项目
      ...
   📦 环境注入完成，.env 已写入...
   ```

---

## 三、Agent 角色绑定（中文交互式）

环境注入只是第一步。进入 Agent 对话窗口后，把对应角色提示词的第一段粘贴发送，Agent 即以中文角色身份开始工作：

- `config/orca/hermes_system_prompt.md` → Hermes 大脑层
- `config/orca/codex_system_prompt.md` → Codex 执行层
- `config/orca/claude_system_prompt.md` → Claude 审核层

> 提示词中使用了 `${ORCA_WORKSPACE_NAME}` 等变量，实际粘贴前已被 `.env` 中的具体值替换，或手动替换为当前项目名。

---

## 四、一键推送全部分支

在**项目根目录**（非工作树）运行：

```bash
bash scripts/orca_push_all.sh [github用户名] [token]
```

默认推送到 `TJF19770107/项目名.git`，分支 `master` + `hermes/brain` + `codex/executor` + `claude/reviewer` 全部推送。

若 token 已缓存于 Windows 凭据管理器，可省略第二个参数：

```bash
bash scripts/orca_push_all.sh
```

---

## 五、非破坏性快照

随时保存三个工作树的完整副本：

```bash
bash scripts/orca_backup.sh
```

快照保存到 `backups/archive_YYYYMMDD_HHMMSS/`，不提交 Git，可随时删除。

---

## 六、三层 Agent 分工速查

| 工作树 | Agent | 角色 | 默认输出位置 |
|--------|-------|------|--------------|
| `worktrees/hermes` | Hermes | 大脑层：方案、架构、需求 | `docs/` / `hermes/` |
| `worktrees/codex` | Codex | 执行层：脚本、批量萃取 | `scripts/` / `outputs/` / `logs/` |
| `worktrees/claude` | Claude Code | 审核层：合规、安全、报告 | `docs/审核报告.md` |

---

## 七、与静默脚手架的关系

新项目使用 `init_orca_silent.sh` 生成时，上述 ORCA 配置文件会自动复制到项目内。开箱后只需在 ORCA 中贴一行命令，三个工作树即可具备环境变量与角色上下文，真正做到「项目脚手架搭建 → ORCA 直接工作」一步闭环。
