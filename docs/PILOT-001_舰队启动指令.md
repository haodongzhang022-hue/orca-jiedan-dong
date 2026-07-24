# PILOT-001 舰队启动指令（ORCA 三工作树）

> 项目：`E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目`  
> 总线：`E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange`  
> 协议：舰队 WorkTree 任务交换区 v2.1（`fleet_pull.sh` 只认文件名含 `_Hermes_` / `_Codex_` / `_CloudCode_` 的真实任务）  
> 本指令：2026-07-25 | 调度中枢：WorkBuddy

---

## 一、当前状态

| Agent | 工作树 | 分支 | 已就绪 |
|---|---|---|---|
| Hermes | `worktrees/hermes` | `hermes/brain` | ✅ 见截图 |
| Codex | `worktrees/codex` | `codex/executor` | ✅ 见截图 |
| Claude Code | `worktrees/claude` | `claude/reviewer` | ✅ 见截图 |

首单任务卡已落在总线：

```
E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/incoming/20260725_014500_0__PILOT_企业微信群定制海报_摇滚风宣传海报.md
```

⚠️ **文件名缺 `_Hermes_` 标记**：`fleet_pull.sh` v2.1 的自动轮询只认文件名含 `_Hermes_` / `_Codex_` / `_CloudCode_` 的任务，因此本卡不会自动被拉取。  
**两种启动方式**（任选其一）：

### 方式 A：让 Hermes 手动读任务卡（推荐先跑通这一单）
直接在 Hermes 终端里粘贴下面的命令：

```bash
cat "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/incoming/20260725_014500_0__PILOT_企业微信群定制海报_摇滚风宣传海报.md"
```
然后让 Hermes 按任务卡里的「🧠 Hermes（hermes/brain 分支 · 大脑层）」章节执行，产出 `design_brief.md` 到 `fleet_exchange/results/`。

### 方式 B：改成自动轮询文件名（后续批量用）
在你本机（Hermes 所在的同一台机器）运行一次：

```bash
cd "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/incoming"
mv "20260725_014500_0__PILOT_企业微信群定制海报_摇滚风宣传海报.md" \
   "20260725_014500_0__Hermes_PILOT_企业微信群定制海报_摇滚风宣传海报.md"
```

然后 Hermes 终端运行：

```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh"
```

> 注：沙箱刚才被拦截了对该 incoming 文件的改名，所以这一步需要你本机手动执行；一次改好，后续任务卡我会在文件名里直接带 `_Hermes_` 前缀，自动拉取就通了。

---

## 二、三段式标准流程（手动读模式）

### Step 1 — Hermes 产出 design_brief

在 Hermes 终端（ORCA 中 `worktrees/hermes`）执行：

```bash
mkdir -p "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/pilot_task_001"
cat "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/incoming/20260725_014500_0__PILOT_企业微信群定制海报_摇滚风宣传海报.md"
```

然后告诉 Hermes：
> 你是本单大脑层。请按任务卡「🧠 Hermes」章节要求，把客户需求拆成结构化设计简报，并产出 `design_brief.md` 到 `E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/results/`。注意：这是内部模拟演练，不对外交付。

Hermes 完成后，让 Hermes 回写完成：

```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" \
  "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/doing/20260725_014500_0__Hermes_PILOT_企业微信群定制海报_摇滚风宣传海报.md" \
  "design_brief 已产出，等待 WorkBuddy 转交 Codex"
```

> 如果是自动轮询模式，Hermes 拉取任务后会自动把文件 mv 到 `doing/`，并在屏幕上打印 `[WORKING_FILE] ...`，直接把那个路径复制到上面的 `fleet_done.sh` 即可。

Hermes 完成后，**通知 WorkBuddy**（或我自行轮询 `results/`）。

---

### Step 2 — WorkBuddy 转交 → Codex 生成海报

Hermes 的 `design_brief` 写回 `fleet_exchange/results/` 后，WorkBuddy 会新建并推送一个 `_Codex_` 任务到 `incoming/`。  
（模板已预存在项目 `docs/draft_task_Codex_PILOT-001.md`）。

在 Codex 终端（ORCA 中 `worktrees/codex`）执行：

```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh"
```

然后告诉 Codex：
> 你是执行层。读取 design_brief，按任务要求生成 2~3 版海报方案（文生图 prompt + 生成结果），附每版 prompt / 尺寸 / 积分消耗。演练走本地/低成本模型，不烧 Hy3 积分。结果写回 `fleet_exchange/results/`，然后执行 `fleet_done.sh`。

---

### Step 3 — WorkBuddy 转交 → Claude Code 核查

Codex 完成后，WorkBuddy 会推送一个 `_CloudCode_` 任务到 `incoming/`。  
（模板已预存在 `docs/draft_task_CloudCode_PILOT-001.md`）。

在 Claude 终端（ORCA 中 `worktrees/claude`）执行：

```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh"
```

然后告诉 Claude：
> 你是核查层。审查 Codex 产出，给出质量/合规/成本三项结论，重点核验是否直接复制原海报素材、Logo、字体。产出 `review_report.md` 到 `fleet_exchange/results/`，然后执行 `fleet_done.sh`。

---

## 三、自动轮询模式（三 Agent 都挂上）

如果 PILOT-001 手动跑通，后续批量可以三 Agent 各自挂机自动轮询：

| Agent | 命令 |
|---|---|
| Hermes | `bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 30 600` |
| Codex | `bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 30 600` |
| Claude | `bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 30 600` |

`30 600` 表示每 30 秒扫描一次，连续 10 分钟无任务自动退出。WorkBuddy 会按 Hermes→Codex→Claude 顺序推送 `_Hermes_` / `_Codex_` / `_CloudCode_` 任务。

---

## 四、WorkBuddy 中转规则

1. **Agent 间不直接对话**。Hermes 完成 → 我读取 `results/` → 写 `_Codex_` 任务到 `incoming/`；Codex 完成 → 我读取 → 写 `_CloudCode_` 任务；Claude 完成 → 我汇总。
2. **命名铁律**：每张云任务卡文件名必须含 `_Hermes_` / `_Codex_` / `_CloudCode_`，否则 `fleet_pull.sh` 视为非任务文件跳过。
3. **模拟演练边界**：所有产出仅落盘 `results/` 和项目 `outputs/`；不截图、不发客户、不产生商业交付。

---

## 五、需要用户确认/操作的节点

1. **修改 PILOT 文件名**（方式 B 需要）：在 Hermes 本机运行上面「方式 B」的 `mv` 命令。
2. **沙箱权限**：如果后续任务卡也让我直接写 `fleet_exchange/incoming/`，需要放开该目录的写权限；否则由你本地复制/移动，WorkBuddy 准备 `docs/draft_task_*.md` 模板。
3. **通知 WorkBuddy**：Hermes / Codex / Claude 每步完成后，在 WorkBuddy 对话里说一声「Hermes 完了」，或我每 30s 轮询 `results/` 自己检测。

---

*本指令由 WorkBuddy 生成，归档于 `docs/PILOT-001_舰队启动指令.md`，随 PILOT-001 跑通后迭代为通用模板。*
