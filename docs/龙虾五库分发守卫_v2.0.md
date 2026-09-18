---
name: 龙虾五库分发守卫
description: 五库（Obsidian/IMA/乐享/CNB/GitHub）一键分发的编排器与门禁。解决分发链路上的死凭据挂起、误推错仓、临时目录损坏假阳性、通道单一下线即挂、漏端无追踪。触发词：五库分发、四端同步、六端归档、推送分发、分发预检、补发队列、假成功第7形态、目录损坏、cnb 令牌。
version: 2.0.0
updated: 2026-09-19
agent_created: true
cost_mode: zero_credit
---

# 龙虾五库分发守卫 v2.0

> 纯 stdlib、零积分。把每天重复的「五落点归档」从手搓变成**可预检、可回退、可追踪**的脚本。
> 主脚本：`scripts/five_lib_dispatch.py`（同时落 `技能库/龙虾零成本运维守卫/scripts/`）

## 1. 什么时候用

- 每日自进化闭环的 Step3「五库分发」
- 任何技能/报告产出后要落到 Obsidian / IMA / 乐享 / CNB / GitHub
- 怀疑某个端「推了但没上」或「推错仓库」

## 2. ★ 假成功第 7 形态：目录「可写但不可列举」

**2026-09-19 实证，`G:\tmp` 八项检查六项全绿、只有列举崩：**

| 检查 | 结果 |
|---|---|
| `os.path.exists` | ✅ True |
| `os.path.isdir` | ✅ True |
| `os.access(W_OK)` | ✅ True |
| `os.makedirs(exist_ok=True)` | ✅ |
| `open(...,'w').write()` | ✅ |
| **`os.listdir`** | ❌ `OSError [WinError 1392] 文件或目录损坏且无法读取` |
| **`os.scandir`** | ❌ 同上 |
| `os.stat` | ✅ |

**危害**：`TMP=G:\tmp` 时，前置门禁（存在/可写）全部放行，代码跑起来才在 `listdir`/`glob`/`walk`/`rmtree` 处炸——
属于「环境自检全绿但环境是坏的」，比前 6 形态更隐蔽。

**判活铁律**：判定目录健康**必须包含列举探针**，只查 exists/isdir/可写 = 假阳性。

```python
from five_lib_dispatch import probe_dir_health, pick_healthy_tmp
probe_dir_health(r"G:\tmp")["healthy"]   # False
pick_healthy_tmp()                        # -> 第一个 6 项全绿的候选
```

候选顺序：`G:\WorkBuddy_Data\tmp` → `G:\temp` → `E:\temp` → `%LOCALAPPDATA%\Temp`。
脚本内所有子进程临时文件都落在**探针确认健康**的目录上，不再盲信 `TMP`。

## 3. CNB 通道：三通道回退（清掉长期挂起待办）

`~/.cnb/token` 长令牌**已死**。唯一活凭据 = `cnb git-credential get` 现签 27 位短令牌。

**坑（2026-09-19 实测）**：`which cnb` 能找到 `/g/.../cli-connector-packages/cnb`，
但那只是 **423 字节的 Git Bash sh shim**，Python `subprocess` 调它直接 `FileNotFoundError`。
**必须用 node 直调真身**：

```
node "G:\WorkBuddy_Data\binaries\node\cli-connector-packages\node_modules\@cnbcool\cnb-cli\bin\cnb.js" git-credential get
```

脚本内 `_cnb_launchers()` 回退链：`node:nodejs → node:managed → node:PATH → shim:cnb → cmd:cnb.cmd`。

三通道（推时逐条实测，谁通谁上并回报通道名）：

| 通道 | 做法 |
|---|---|
| A 令牌内嵌 | `https://cnb:<27位>@cnb.cool/...` + `-c credential.helper=` + 清代理 |
| B askpass | 干净 URL（不带 user@）+ `GIT_ASKPASS` + CLI 登录态 |
| C env 注入 | 干净 URL + `CNB_TOKEN` 环境变量 |

**必须清代理**：`-c http.proxy= -c https.proxy=`（全局 `http.proxy=127.0.0.1:7897` 在 7897 DOWN 时会让直连也失败）。

## 4. ★ 目标远端必须从仓库自身解析（血案）

**2026-09-19 事故**：脚本把 CNB 目标 URL 硬编码成 `lobster-knowledge-base.git`，
拿「接单项目」仓库跑分发 → **把项目提交推进了知识库仓，凭空多出一个 `main` 分支**。
（`--dry-run` 当时还挡不住 push，两坑叠加。）

**修复后的铁律**：
1. 目标 URL = `git remote get-url origin` 的实际输出，**禁止用全局常量当推送目标**；
2. 无 `origin` 远端 → 直接 FAIL「拒绝盲推」，不猜；
3. `--dry-run` 同时阻断 **commit 和 push**；`--no-push` 只挡 push（**仍会 commit**）。

误推善后：`git push <url> --delete <branch>` 删掉凭空出现的分支，再 `ls-remote` 复核。

## 5. GitHub 通道：三级自适应选路

v1.0 硬编码 `socks5://127.0.0.1:1081`，1081 一挂就卡死。v2.0 自动选：

| 序 | 条件 | 通道 |
|---|---|---|
| 1 | `1081` LISTENING | `socks5://127.0.0.1:1081` |
| 2 | `github.com:443` 直连 3/3 通 | 直连 + **清代理**（remote=`direct`） |
| 3 | 否则 `gh-proxy.com:443` 通 | 镜像 remote=`github` |
| 4 | 全断 | BLOCKED + 入队，**不挂起** |

**GFW 抖动判据**：单次 `create_connection` 成功不可信，必须 **3/3 全通**才算窗口可用。

## 6. 安全闸门 --only（防 146 文件误推）

仓库常有上百个 untracked 订单目录。默认行为：

- 给 `--only a,b,c` → 只提交这些路径前缀；
- 不给 → **只放行已跟踪文件的修改，untracked 一律不碰**，并打印告警；
- 提交后残留检查只核对「本次纳入范围」，不会把主动排除的 untracked 误报成 FAIL。

**绝不 `git add -A`**（假删除 3652 文件险情）。

## 7. 待补发队列（解决 IMA/乐享 连续阻断无追踪）

失败/BLOCKED 的端自动写入 `待分发任务/pending_queue.json`：

```bash
python five_lib_dispatch.py --pending          # 查看
python five_lib_dispatch.py --retry-pending    # 一键补发（MCP 端需 Agent 先调 MCP）
```

MCP 端（乐享/IMA）脚本无法自证，只做「生成载荷 + 入队 + 记回执」：

```bash
python five_lib_dispatch.py --record-receipt lexiang --url https://lexiangla.com/pages/xxx
```

## 8. 标准作业流程

```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"

# ① 先预检（绿/黄/红）
$PY scripts/five_lib_dispatch.py --precheck

# ② 干跑确认范围（不 commit 不 push）
$PY scripts/five_lib_dispatch.py --all --dry-run --src <技能目录> --repo <仓> --branch main

# ③ 真推（用 --only 限定范围）
$PY scripts/five_lib_dispatch.py --target cnb    --repo <仓> --branch main --only docs,scripts,技能库
$PY scripts/five_lib_dispatch.py --target github --repo <仓> --branch main --only docs,scripts,技能库

# ④ 看队列
$PY scripts/five_lib_dispatch.py --pending
```

## 9. 五端当前诚实边界（2026-09-19）

| 端 | 自动化程度 | 现状 |
|---|---|---|
| ① Obsidian | 全自动 | ✅ 落盘后回读条数核实 |
| ② 乐享 | 半自动 | MCP 未挂载时入队待补 |
| ③ IMA | 半自动 | 同上，推荐 `import_urls` 导乐享已发布页 |
| ④ CNB | 全自动 | ✅ 三通道回退 + ls-remote 回查 |
| ⑤ GitHub | 全自动 | ✅ 三级选路 + 回查 |

## 10. 红线

1. 推送目标**只能来自仓库自身远端**，禁止硬编码他仓 URL。
2. 目录健康**必须含列举探针**。
3. 临时文件落**探针确认健康**的目录。
4. 不 `add -A`；`--dry-run` 必须真的什么都不改。
5. 密钥脱敏：令牌只在本进程 env / URL 内嵌中使用，不写进任何同步产物与 git。
6. 远端见 404 先打身份探针（`api.<host>/user`），401 = 令牌失效，绝不判「仓库被删」。
