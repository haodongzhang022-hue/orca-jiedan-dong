# 协议 #290：ORCA 多 Agent 工作树自动填充配置规范

> 归属：龙虾全域官方模板 · 新增协议 #290
> 关联：#287 Orca 工作树管理、#289 ORCA 多 Agent 舰队搭建规范
> 闭环：本规范定义的「设置脚本 / 存档脚本 / 路径约束 / 开关默认值」被 #289 的 ORCA 工作树配置流程直接引用，形成「搭建→填充→归档」全链路。

---

## 1. 适用范围

所有在 ORCA 中以多 Agent 舰队形式协作、且需要为各工作树自动注入统一环境配置的项目。
典型：复刻「黄金黑马策略」三层架构（hermes/brain · codex/executor · claude/reviewer）的项目。

---

## 2. 环境变量映射（禁止写死绝对路径）

| 变量名 | 含义 | 来源 | 默认值（回退） |
|--------|------|------|----------------|
| `ORCA_ROOT_PATH` | 项目根目录（主仓库） | ORCA 运行时注入 | `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目` |
| `ORCA_WORKTREE_PATH` | 当前工作树绝对路径 | ORCA 运行时注入 | — |
| `ORCA_WORKSPACE_NAME` | 工作树/项目名 | ORCA 运行时注入 | — |
| `OBSIDIAN_MAIN` | Obsidian 主知识库（G 盘） | 项目根 `.env` | `G:\龙虾知识库主库` |
| `LOBSTER_BACKUP_ROOT` | 统一备份根目录（E 盘） | 项目根 `.env` | `E:\龙虾AI主控中心\我的AI分身\backups` |
| `GITHUB_PRIVATE_REPO` | 私有 GitHub 仓库 | 项目根 `.env` | `TJF19770107/side-project-knowledge-base` |

> 规则：设置脚本 / 存档脚本一律引用上述变量；项目根 `.env` 随设置脚本复制进每个工作树，确保离线可读。

---

## 3. 标准设置脚本（龙虾五步法 Step1 环境备份）

新建工作树**前置自动执行**（页面1「设置脚本」框 / 页面2「设置脚本」框）。

```bash
# ORCA多Agent工作树自动初始化脚本 | 龙虾五步法Step1环境备份
cp "$ORCA_ROOT_PATH/config/default_config.yaml" "$ORCA_WORKTREE_PATH/config/"
cp "$ORCA_ROOT_PATH/.env" "$ORCA_WORKTREE_PATH/.env"
pip install -r "$ORCA_ROOT_PATH/requirements.txt"
mklink /D "$ORCA_WORKTREE_PATH/obsidian_link" "$OBSIDIAN_MAIN"
python "$ORCA_ROOT_PATH/scripts/skill_auto_register.py" --tree "$ORCA_WORKTREE_PATH"
echo "✅ 工作树初始化完成，龙虾五步法环境加载完毕"
```

职责分解：
1. 复制全局配置 `config/default_config.yaml` → 工作树
2. 复制 `.env`（含 OBSIDIAN_MAIN / LOBSTER_BACKUP_ROOT）→ 工作树
3. 安装龙虾舰队统一依赖 `requirements.txt`
4. 绑定 Obsidian 主知识库软链接（G 盘，不占本地/GitHub 存储）
5. 自动注册当前分支技能至 `skill_registry.json`

---

## 4. 标准存档脚本（龙虾五步法 Step5 沉淀归档）

删除工作树**前自动执行**（页面2「存档脚本」框）。

```bash
# 工作树归档清理脚本 | 龙虾五步法Step5沉淀
echo "开始归档工作树：$ORCA_WORKSPACE_NAME"
cp -r "$ORCA_WORKTREE_PATH/logs" "$LOBSTER_BACKUP_ROOT/$ORCA_WORKSPACE_NAME"
cd "$ORCA_WORKTREE_PATH"
git add .
git commit -m "auto archive: $ORCA_WORKSPACE_NAME 工作树归档"
echo "✅ 工作树归档沉淀完成，同步至私有Git仓库"
```

职责分解：
1. 备份日志 / 输出物至统一备份目录（E 盘，禁 C 盘）
2. 提交工作树变更到 Git（私有仓库）
3. 完成 Step5 沉淀，支持溯源与回滚

---

## 5. 路径约束（铁律）

- 工作树位置模板：`E:\龙虾AI主控中心\我的AI分身\${ORCA_WORKSPACE_NAME}`
- **禁止**使用 ORCA 默认 `C:\Users\...\AppData\...` 路径
- Obsidian 软链指向 `G:\龙虾知识库主库`（G 盘）
- 备份指向 `E:\龙虾AI主控中心\我的AI分身\backups\`（E 盘）
- `.gitignore` 已排除日志 / 输出 / 备份 / 模型缓存 / 视频 / 压缩包

---

## 6. 开关与运行时机默认值

| 控件 | 默认值 | 说明 |
|------|--------|------|
| 何时跑步（设置脚本） | 【默认运行】 | 每次新建工作树自动执行 |
| 何时跑步（存档脚本） | 【默认运行】 | 删除工作树前自动执行 |
| 等待设置完成后再启动智能体 | **开启** | 确保环境就绪再启动 Agent |
| 跟随主分支（默认工作树基础） | 开启 | 主分支填 `master` |

---

## 7. 全自动自动填充逻辑（首次新建项目）

1. 新建 ORCA 项目、生成 3 个 Agent 工作树时，系统读取全域模板内置配置
2. 一次性填充：设置脚本、存档脚本、工作树位置、运行规则
3. 用户仅确认授权，零手动输入
4. 自动校验：
   - 覆盖 ORCA 默认 C 盘路径 → E 盘统一根目录
   - 注入两段标准脚本
   - 开启「等待设置完成再启动智能体」开关
   - 绑定 Obsidian 软链 + 技能自动注册

---

## 8. 触发关键词（全域模板自动调用）

出现以下关键词时，自动加载本规范模板：
`ORCA 工作树` · `添加工作树` · `Hermes 分支` · `Codex 执行分支` · `Claude 核查分支` · `设置脚本` · `存档脚本` · `自动填充`

---

## 9. 软连接联动规则

检测到项目为多 Agent 舰队项目（存在 `hermes/` `codex/` `claude/` 三层目录）时，
自动加载本套配置模板，无需重复编写脚本；设置脚本统一绑定 `obsidian_link` 软链至 `OBSIDIAN_MAIN`。

---

## 10. 关联文件

- 可视化标注指南：`docs/可视化标注指南.html` / `docs/可视化标注指南.md`
- 设置脚本依赖：`scripts/skill_auto_register.py`（分支技能自动注册）
- 环境变量模板：项目根 `.env`
- 五步法案例：`docs/龙虾五步法案例-ORCA工作树可视化配置.md`
