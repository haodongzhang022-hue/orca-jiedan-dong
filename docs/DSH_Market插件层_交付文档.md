# DSH Market 插件层 · 交付文档

> 版本：v1.0 | 日期：2026-08-23 | 归属：DeepSeek-Harness「一切皆插件」能力插件层
> 目标：为 DeepSeek-V4-Flash（纯文本基座）补齐视觉 / 长期记忆 / 任务看板 / 电脑操作，跨框架全链路自动调用。
> 核心原则：**底层模型不变**，能力全部在插件代理层完成；**基座 harness_proxy.py / harness_agent.py 固定不动**，仅加了防御式路由钩子。

---

## 一、交付物清单

| 文件 | 作用 |
|------|------|
| `deepseek-harness/settings.yaml` | 五个插件唯一开关 + 路由规则来源（密钥仅占位符） |
| `deepseek-harness/config/dsh_market.json` | 插件市场目录（元数据 + 依赖 + 强制安装顺序） |
| `deepseek-harness/dsh_market.py` | DSH-Market 插件市场管理器（list/install/uninstall/backup） |
| `deepseek-harness/dsh_router.py` | 跨框架自动路由中间层（输入类型识别 → 自动追加能力） |
| `deepseek-harness/dsh_common.py` | 公共设施（YAML 解析 / 环境变量解析 / settings 备份 / 插件基类） |
| `deepseek-harness/plugins/hindsight/hindsight.py` | Hindsight 长期记忆插件 |
| `deepseek-harness/plugins/modlens/modlens.py` | ModLens 视觉能力插件（Gemini 后端） |
| `deepseek-harness/plugins/dsh_kanban/kanban.py` | DSH-Kanban 任务看板插件 |
| `deepseek-harness/plugins/dsh_computer_use/computer_use.py` | DSH-Computer-Use 电脑操作插件 |
| `deepseek-harness/tests/test_dsh_plugins.py` | 验证测试脚本（18 项断言） |
| `deepseek-harness/harness_proxy.py` | 基座（仅加了 3 行防御式路由钩子，不影响原链路） |

---

## 二、安装顺序（强制）

① DSH-Market → ② Hindsight → ③ ModLens → ④ DSH-Kanban → ⑤ DSH-Computer-Use

依赖校验：非 Market 插件都声明依赖 `dsh_market`，Market 未启用时其余插件拒绝安装。顺序固化在 `install_order` 字段。

```bash
# 用 workbuddy Python（勿用系统默认 python，缺 ssl 会崩）
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# 一键按顺序安装全部
"$PY" deepseek-harness/dsh_market.py install-all

# 查看插件清单
"$PY" deepseek-harness/dsh_market.py list

# 单个安装 / 卸载 / 开关（每次变更前自动备份 settings.yaml）
"$PY" deepseek-harness/dsh_market.py install hindsight
"$PY" deepseek-harness/dsh_market.py uninstall hindsight
"$PY" deepseek-harness/dsh_market.py disable modlens
"$PY" deepseek-harness/dsh_market.py enable modlens
```

---

## 三、settings.yaml 配置片段（交付物 1）

```yaml
version: "1.0.0"
base_model: "deepseek-v4-flash"          # 底层模型不变

plugins:
  dsh_market:       { enabled: true, install_order: 0 }
  hindsight:        { enabled: true, install_order: 1, memory_dir: "${HARNESS_MEMORY_DIR:-./harness_memory}" }
  modlens:          { enabled: true, install_order: 2, backend: "gemini", api_key: "${env:GEMINI_API_KEY}", model: "gemini-2.0-flash" }
  dsh_kanban:       { enabled: true, install_order: 3, board_dir: "${HARNESS_BOARD_DIR:-./harness_kanban}" }
  dsh_computer_use: { enabled: true, install_order: 4, confirm_high_risk: true, timeout_seconds: 60 }

routing:
  image_input: "modlens"
  project_memory: "hindsight"
  task_management: "dsh_kanban"
  local_operation: "dsh_computer_use"
  memory_auto_inject: true
  image_auto_ocr: true
```

密钥红线：`modlens.api_key` 只写 `${env:GEMINI_API_KEY}` 占位符，运行时从环境变量读取，**禁止明文写入 yaml**。CNB_TOKEN 同理沿用现有基座的环境变量注入。

---

## 四、跨框架自动路由规则（交付物 2）

所有框架（Codex / WorkBuddy / Hermes / Claude Code / CNB 云端）调用 DeepSeek-V4-Flash 时，`dsh_router.DshRouter.route()` 自动识别输入类型并追加能力，业务侧无需手动调用插件：

| 输入类型 | 触发判定 | 自动动作 |
|----------|----------|----------|
| 输入含图片 | 消息 content 含 `image_url` / `data:image/` | ModLens 解析图片 → 文本送入基座 |
| 会话属于已有项目 | 传入 `session` / `project` | Hindsight 自动加载项目记忆注入 system prompt |
| 任务属于项目管理 | 文本含「看板/kanban」或 meta.tool=kanban | 唤起 DSH-Kanban，直接返回板操作结果（不调模型） |
| 需要本地操作电脑 | 文本含「打开网页/执行命令…」或 meta.tool=computer_use | 触发 DSH-Computer-Use，高危操作弹确认 |

调用形态（走 `harness_proxy.py` 的 `/v1/chat/completions`，自动被路由钩子拦截）：

```json
{
  "model": "deepseek-v4-flash",
  "messages": [{"role": "user", "content": "创建任务"}],
  "session": "企业微信群接单项目",
  "plugins": {"tool": "kanban", "action": "create", "title": "黄金黑马策略海报"}
}
```

返回两类结果：`handled=true`（插件层已直接产出，如看板/电脑操作）或 `handled=false`（返回被增强的 messages + 注入的 system，交给基座推理）。

---

## 五、验证测试（交付物 3）

```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
"$PY" deepseek-harness/tests/test_dsh_plugins.py
```

覆盖六类连通性验收（18 项断言，零网络零密钥）：

1. 市场清单（5 插件 + 安装顺序 0..4 + 基座模型不变）
2. 记忆读写（Hindsight 写 / 读 / 键值 / 注入 prompt）
3. 任务看板（DSH-Kanban 建卡 / 移动 / 列表）
4. 图片输入（ModLens 图片提取 + 无 GEMINI_API_KEY 优雅降级）
5. 电脑操作（高危识别 + 未确认拦截 + 安全命令可执行）
6. 跨框架路由（图片→ModLens / 记忆→Hindsight / 任务→Kanban / 本地→ComputerUse）

实测结果：**18 / 18 通过**；基座 `/health` + 看板路由端到端已打通（无需 CNB_TOKEN 也能走插件层直接返回结果）。

---

## 六、安全与约束

- 密钥零明文：`GEMINI_API_KEY` / `CNB_TOKEN` 全部环境变量注入，settings.yaml 只存 `${env:...}` / `${...:-...}` 占位符。
- 高危确认：DSH-Computer-Use 默认 `confirm_high_risk=true`，删除 / 格式化 / 改注册表 / `git reset --hard` 等未确认一律拦截，不执行。
- 独立开关：每个插件可单独卸载，不破坏整套配置；`dsh_market.py` 每次变更前自动备份 settings.yaml（毫秒级时间戳去重）。
- 降级兜底：ModLens 缺密钥或网络失败走 Pillow 本地元数据兜底，不阻断接单主链路；路由钩子 try/except 包裹，插件缺失不影响基座。

---

## 七、四化对齐

| 四化 | 对齐点 |
|------|--------|
| 智能化 | 输入类型自动识别自动路由，无需业务侧手动调插件 |
| 定制化 | 从「纯文本模型缺能力」痛点逆向工程出 5 个能力插件层 |
| 全自动化 | 市场一键 install-all + 自动备份 + 自动路由，零人工干预 |
| 自我净化 | 插件独立开关可热拔插，故障可单独卸载不污染整套配置 |
