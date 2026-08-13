# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）

> 归属：自我净化闭环 · 每次迭代沉淀踩坑方案，供赛博书屋自主学习。
> 来源：scripts/auto_gpt_trigger_config.py / scripts/auto_gpt_orca_bridge.py

---

## 2026-08-13 17:04 · codex max防线复核 + 新基线快照 170407（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖+长期稳定"）

### 本轮新增事实（区别于 16:58 条，本轮为新基线快照 + 防线存活再实测）
- **身份澄清（答"不是ATOMCODE吗"）**：运行载体是 AtomCode（127.0.0.1:13460 代理 → deepseek-v4-flash，HTTP 200 双模型在线）；我是 codex 执行 Agent，本次修复由 hermes 改 catalog + 守护脚本兜底 + 本轮复核落新基线
- **新回滚基线**：`snapshots/normal_node_20260813_170407.tar.gz`（9.1MB < 20M，9,516,403B，tar 校验 OK），BASELINE.md 已更新为当前基线（165823 降为可用）
- **防线存活再实测**：`codex_catalog_guard.py` 单次巡检「修复 0 文件/0 处 + 生成源已带补丁无需重打」；定时任务双注册（Lobster_CodexCatalogGuard 17:07 + WatchCodexCatalog 17:15 均就绪）；index.js 含 xhigh×8 零 max、`index.js.bak_guard_auto_20260813_162548` 在盘
- **长期稳定确认**：三引擎（hermes/codex/CLAUDE CODE）全部正常应答；13460 代理健康；CNB 待本轮提交推送后同步
- **踩坑要点**：轻量快照排除项（.git/snapshots/对话记录/msgbus/worktrees/logs/fleet_exchange/tools/*.zip）保证 <20M；防覆盖四层独立存活，任何单层被 Hermes 更新覆盖其余层仍拦截

## 2026-08-13 16:58 · codex max防线防覆盖收尾复核 + 新基线快照 165823（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖+长期稳定"）

### 本轮新增事实（区别于 16:48 条，本轮为防线复核确认 + 最新基线）
- **身份澄清（再答"不是ATOMCODE吗"）**：修复动作归属 hermes（大脑）手动改 catalog + 守护脚本自动兜底；运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——动作归 hermes/codex、载体是 AtomCode，两种说法都对
- **防覆盖复核全通过（本轮实测，防线未被 16:53 提交 463b908 覆盖）**：①生成源 `Hermes Studio\resources\webui\dist\server\index.js` `effort:"max"` 计数 0、合法六档齐全 ②7 份 .bak 备份在库（1430/1525_ultra/max_fix/guard_auto×4）③`Lobster_CodexCatalogGuard` 就绪（每 5 分钟），`catalog_guard.log` 16:09→16:55 连续 16 条全部 `fixed 0` = 防线生效 ④`fleet_auto_restore.cmd:158-164` 第 5.5 步启动兜底在库 ⑤双脚本独立存活（guard v1.1 精确正则防误报）
- **新回滚基线**：`snapshots/normal_node_20260813_165823.tar.gz`（10.6MB < 20M，11,138,026B，tar 校验 OK），BASELINE.md 已更新为当前基线，164828 降为可用
- **长期稳定确认**：13460 代理 HTTP 200（deepseek-v4-flash + Qwen3-VL-8B 双模型在线）；CNB 远端 HEAD=463b908=本地零差异
- **踩坑要点**：防覆盖四层独立存活（源头净化/定时巡检/启动兜底/入库备份），任何单层被 Hermes 更新覆盖其余层仍拦截——「不要被覆盖」= 脚本入库（git）+ 备份在库（.bak）+ 云端推送（CNB）三重锚点

## 2026-08-13 16:48 · codex max防线四层复核 + 新基线快照 164828（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖+长期稳定"）

### 本轮新增事实（区别于 16:40 条，本轮为防线四层独立复核 + 云端推送补缺）
- **身份澄清（再答"不是ATOMCODE吗"）**：修复动作归属 hermes（大脑）手动改 catalog + 守护脚本自动兜底；运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——动作归 hermes/codex、载体是 AtomCode，两种说法都对
- **防线四层独立复核全通过（本轮实测）**：①源头 `Hermes Studio\resources\webui\dist\server\index.js` 合法六档（none/minimal/low/medium/high/xhigh）零 `effort:max` 残留，7 份 .bak 备份在库 ②`Lobster_CodexCatalogGuard` 每 5 分钟巡检（16:25/16:27/16:35/16:45 连续日志，fixed 0 catalog = 防线生效）③`fleet_auto_restore.cmd` 第 5.5 步启动兜底在库（watch_codex_catalog.py --once）④guard 脚本精确正则（`has_bad_effort` + 三种 effort:max 形态替换）防误报
- **新回滚基线**：`snapshots/normal_node_20260813_164828.tar.gz`（10.6MB < 20M，11,137,389B），BASELINE.md 已更新为当前基线，163939 降为可用
- **云端推送补缺（关键）**：并行会话防线根治提交 `4fe8631` 此前仅本地 HEAD、远端停在 e9ca715——本轮确认后推送 CNB，实现"防覆盖"的云端备份闭环（被覆盖可从远端恢复）
- **长期稳定确认**：13460 双模型在线（deepseek-v4-flash + Qwen3-VL-8B）、15721 健康、15730 旧代理未监听但现役链路走 13460 不受影响、3 个 catalog 零 max
- **踩坑要点**：防覆盖不仅要本地多层防线，还要**推送远端**——本地文件被 Hermes 更新覆盖时，远端提交 + 快照 tar.gz 是最后恢复锚点

## 2026-08-13 16:40 · codex max防生成根防线落实 + 防覆盖固化（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖+长期稳定"）

### 本次新增事实（区别于 16:06 条，本轮为防覆盖固化 + 新基线）
- **身份澄清（回答"不是ATOMCODE吗"）**：修复动作归属 hermes（大脑）+ 守护脚本（codex_catalog_guard.py），运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——动作归 hermes/codex，载体是 AtomCode，两种说法都对
- **guard 检测误报修复（本轮实修）**：`codex_catalog_guard.py` 原用裸 `"max"` 字符串判断 index.js 是否被 Hermes 更新覆盖 → minified 代码中任何含 max 的字符串都误触发备份。已改为 `has_bad_effort()` 精确正则（仅匹配 `effort:"max"` 形态），修复后巡检输出「生成源已带补丁（无 effort:max 残留），无需重打」，不再冗余备份
- **新回滚基线**：`snapshots/normal_node_20260813_163939.tar.gz`（10.6MB < 20M，11,110,713B），BASELINE.md 已更新；首包 24.3M 超限（未排除 fleet_exchange/tools 5M+2.8M），排除后达标
- **防覆盖四层实锤**：①生成源 index.js 合法六档无 max ②`Lobster_CodexCatalogGuard` 每 5 分钟巡检（16:25/16:32/16:36 连续日志）③fleet_auto_restore.cmd 第 5.5 步启动兜底 ④4+ 份 .bak 备份（含 bak_guard_auto 自动备份）
- **长期稳定确认**：13460 代理健康（deepseek-v4-flash + Qwen3-VL-8B 在线）、15721 健康、15730 旧代理未监听但现役链路走 13460 不受影响、3 个 catalog 零 max
- **踩坑要点**：①打包必须排除 fleet_exchange/（5M 会话交换）+tools/（2.8M），否则超 20M ②guard 检测判断要用精确正则防误报——「防覆盖」的代码本身也要防 bug

## 2026-08-13 16:06 · codex max防线本轮复核 + 新基线快照 160650（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖"）

### 本轮新增事实（区别于 16:00 条，本轮为收尾复核 + 新基线）
- **身份澄清（回答"不是ATOMCODE吗"）**：修复动作归属 hermes（大脑），运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——两种说法都对，动作归 hermes、载体是 AtomCode
- **新回滚基线**：`snapshots/normal_node_20260813_160650.tar.gz`（17.0MB < 20M），BASELINE.md 已更新为新基线；快照踩坑：`--exclude=./xxx` 需带 `./` 前缀且须排除 `对话记录/`（32M 聊天备份，属外部备份非项目状态）
- **防线四层复核全通过**：①源头 `Hermes Studio\resources\webui\dist\server\index.js` grep max = 0 ②`Lobster_CodexCatalogGuard` 就绪（10 分钟周期，catalog_guard.log 15:45-16:05 连续输出）③`fleet_auto_restore.cmd` 第 5.5 步启动兜底在库 ④3 个 catalog JSON 全合法（none/minimal/low…，零 max）
- **踩坑要点**：打包时 `对话记录/` 目录会膨胀快照体积（本次首包 25.9M 超限，排除后 17M），与 BASELINE 约定（排除 .git/对话记录/msgbus/worktrees/logs/snapshots）一致；防线核查四层独立存活，任何单层被 Hermes 更新覆盖其余层仍拦截

## 2026-08-13 16:00 · codex max根防线落实复核 + 新基线快照（codex 执行 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖"）

### 本次新增事实（区别于 15:56 条，本轮为根防线落实）
- **身份澄清**：修复动作归属 hermes（大脑）手动改 catalog，运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——"不是ATOMCODE吗"的答案是：载体是 AtomCode，动作是 hermes 做的，两种说法都对
- **新回滚基线**：`snapshots/normal_node_20260813_155724.tar.gz`（16.9MB < 20M），BASELINE.md 已更新
- **防生成根防线实锤**：index.js 档位集合无 max（xhigh 8 处+合法集合）+ 3 份 .bak 防覆盖；`Lobster_CodexCatalogGuard` 守护任务 Ready（10 分钟巡检）；fleet_auto_restore.cmd 第 5.5 步启动兜底在库；当前 catalog 第 34 行 effort=xhigh 零 max 残留
- **踩坑要点**：核查防线要看四层（源头 index.js / 守护任务 / 启动兜底 / 脚本双副本），单层被 Hermes 更新覆盖时其余层仍拦截——「防生成拦截写入」由源头无 max + 模板自愈写回机制落实

## 2026-08-13 15:56 · codex max防线端到端实测 + 新基线快照（codex 执行 · 1234 调用 · 用户点名"不是ATOMCODE吗+防生成勿被覆盖"）

### 本次新增事实（区别于 15:43 条，本轮为端到端实测）
- **新回滚基线**：`snapshots/normal_node_20260813_155209.tar.gz`（10.7MB < 20M），tar 完整性 OK（710 文件）
- **身份澄清**：修复动作归属 hermes（大脑），运行载体是 AtomCode（13460 代理 → deepseek-v4-flash）——"谁修的"两种说法都对
- **端到端实测**：`watch_codex_catalog.py --once` 输出 `fixed 0 catalog(s), template_self_heal=False`（源头已净，无需修复）；3 个 catalog JSON 校验全 OK；全目录零 effort-max 残留（state_5.sqlite 内为会话历史文本，非 catalog，不影响解析）
- **定时任务真实运行**：catalog_guard.log 15:54/15:55 连续输出，`Lobster_CodexCatalogGuard` 10 分钟周期存活
- **踩坑要点**：排查残留时 grep 命中 state_5.sqlite（SQLite 会话库）里的旧报错文本，需区分"catalog JSON"与"会话历史库"——只有前者影响 codex 解析

## 2026-08-13 15:43 · codex max防线四要素复核 + 新基线快照（codex 执行 · 1234 调用 · 用户点名"长期稳定+防生成勿被覆盖"）

### 本次新增事实（区别于 15:36 条，本轮为独立复核）
- **新回滚基线**：`snapshots/normal_node_20260813_154312.tar.gz`（10.3MB < 20M），BASELINE.md 已更新为该基线
- **防线五要素复核全通过**：①index.js 档位数组无 max（仅 1 处 JS 变量校验，备份 4 份在库）②`Lobster_CodexCatalogGuard` 上次运行 15:39 结果 **0=成功** ③`fleet_auto_restore.cmd:160-164` 启动兜底在库 ④脚本双副本 6468B 一致 ⑤当前会话 catalog effort 档位零 max、全目录零残留
- **`--once` 实测**：`fixed 0 catalog(s), template_self_heal=False`——无需修复即防线生效的最强证据
- **长期稳定结论**：四层防线独立存活 + 五要素复核通过，任何单层被 Hermes 更新覆盖其余层仍可拦截
- wiki 沉淀：`E:\龙虾AI主控中心\Obsidian\wiki\舰队运维\codex_max档位防复发根治_20260813.md` 新增「15:43 防线四要素复核」章节

---

## 2026-08-13 15:36 · codex max防生成根防线四要素实测 + 新基线快照（codex 执行 · 1234 调用 · 用户点名"防生成拦截写入勿被覆盖"）

### 本次新增事实（区别于上一条防线终验）
- **新回滚基线**：`snapshots/normal_node_20260813_153640.tar.gz`（15.0MB < 20M），BASELINE.md 已更新
- **防生成四要素逐项实测**：①源头 `Hermes Studio\resources\webui\dist\server\index.js` grep `"max"` = **0**（档位数组无 max，备份 4 份）②`Lobster_CodexCatalogGuard` 每 10 分钟 **上次结果 0=成功**，日志 `logs/catalog_guard.log` 15:29-15:35 连续输出 ③`fleet_auto_restore.cmd:158-163` 启动兜底第 5.5 步在库 ④脚本双副本（接单项目 + AtomCode 各 6468B 一致，git 版本化）
- **防生成原理**：`watch_codex_catalog.py` 模板自愈支持对象/数组/顺序颠倒/数组尾部四变体正则剔除，Hermes 更新覆盖 index.js 后每 10 分钟自动写回剔除——拦截于生成源头而非仅事后修 catalog
- **防覆盖三重机制**：写回自愈 + 多备份（index.js 4 份 + catalog .bak_20260813_max_fix）+ 脚本双副本
- wiki 沉淀：`E:\龙虾AI主控中心\Obsidian\wiki\舰队运维\codex_max档位防复发根治_20260813.md` 新增「15:36 防生成根防线实测」章节



### 本次亮点
- **根因防线终验实锤（防生成非事后修复）**：用户明确要求"根本防线是防生成（拦截写入）而非事后修复，不要被覆盖"。逐层核验：①生成源头 `Hermes Studio\resources\webui\dist\server\index.js`（8.78MB，14:40 更新后）档位数组实测 `["default","none","minimal","low","medium","high","xhigh"]` **无 max**；模板中唯一 `"max"` 为 dryRun 参数校验（`ZE(l.max,"max",...)`），与 effort 档位无关——勿误修 ②当前 catalog `grep '"effort": "max"'` = **0 残留** ③`Lobster_CodexCatalogGuard` 定时任务实测**每 2 分钟**重复（日志 15:10→15:31 连续 10 次 clean，`template_self_heal=False` 表明源头已干净无需再自愈）④`fleet_auto_restore.cmd:160-164` 启动预修复第 5.5 步挂接 `watch_codex_catalog.py --once`
- **防覆盖承诺固化**：三重防线相互独立（源头模板无 max + watch_codex_catalog.py 模板自愈正则 + 2分钟巡检 + 启动兜底），即使 Hermes 更新覆盖 index.js，自愈脚本会自动再剔除 max；本记录即"不要被覆盖"的持久凭证
- **新基线快照**：`snapshots/normal_node_20260813_152653.tar.gz`（14.2M < 20M），BASELINE.md 更新为当前回滚基线

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| 模板 grep `"max"` 命中 1 处疑似残留 | JS 变量校验 `ZE(l.max,"max",zRe)`（dryRun/failureLimit 参数），非档位数组 | grep 上下文确认形态再动手，档位数组以 `new Set(["default",...,"xhigh"])` 为准 |
| 定时任务"每10分钟"与实测不符 | 首版注册间隔 10 分钟，检修后已改 2 分钟 | 以 `schtasks /query /xml` 的 `<Interval>` 与日志时间戳为准，勿信旧文档 |

### 沉淀位置
- Obsidian wiki：`E:\龙虾AI主控中心\Obsidian\wiki\codex_max_防生成拦截根治_20260813.md`（本次终验追加段）
- 复盘镜像：`docs\技能沉淀\20260813_codex_max防线加固_复盘.md`（按需同步）

---

## 2026-08-13 · codex max防线检修实锤 + 启动预修复 + 新基线快照（codex 执行 · 1234 调用触发）

### 本次亮点
- **守护任务检修实锤**：`Lobster_CodexCatalogGuard` XML 确认每 10 分钟重复（`<Interval>PT10M</Interval>`）；手工 `/run` 触发成功（15:12:13 日志落盘 `logs/catalog_guard.log`）——"上次运行 1999/11/30"系注册后未到首跑点，非失效，勿误判为任务坏了
- **启动预修复补位**：`scripts/fleet_auto_restore.cmd` 新增第 5.5 步（`watch_codex_catalog.py --once`），舰队每次启动先修一次——三重防线齐备（模板自愈 + 10 分钟巡检 + 启动兜底）
- **防覆盖约定固化**：防线三层独立存在，已写入 CODEX.md「Codex max 防线」章节；迭代脚手架不得删除 `Lobster_CodexCatalogGuard` 任务与防线说明
- **新基线快照**：`snapshots/normal_node_20260813_150954.tar.gz`（11.1MB < 20M），BASELINE.md 已更新为当前回滚基线

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| schtasks "上次运行 1999/11/30 / 结果 267011" 疑似失效 | 任务注册后未到首跑点（15:07 注册、15:17 首跑），schtasks 显示默认值 | 查 XML `<Repetition><Interval>` 确认调度，`schtasks /run` 手工触发验证，以日志落盘为准 |
| 模板 index.js 仍有 1 处 "max" | 是 JS 变量校验（`ZE(l.max,"max",...)`），非档位数组 | grep 上下文确认形态，勿误修；档位数组 `["default",...,"xhigh"]` 实测无 max |

### 沉淀位置
- Obsidian wiki：`E:\龙虾AI主控中心\Obsidian\wiki\舰队运维\codex_max档位防复发根治_20260813.md`（15:09 防覆盖固化更新段）
- 复盘镜像：`docs\技能沉淀\20260813_codex_max防线加固_复盘.md`（第六节补充）

---

## 2026-08-13 · codex max防生成拦截根治（根本防线）+ 新快照 + 守护双任务注册（#307 · 1234机制调用）

### 本次亮点
- **根本防线落地（防生成非事后修复）**：用户明确要求"防生成拦截写入而非事后修复，不要被覆盖"。落实四层：①index.js 档位数组已无 max（`["default","none","minimal","low","medium","high","xhigh"]` 实测）②`watch_codex_catalog.py` v1.2 模板自愈（Hermes 更新带回 max 自动剔除，正则覆盖对象/数组/顺序变体）③`Lobster_CodexCatalogGuard` 每 10 分钟巡检兜底 ④日志落盘防静默失效
- **守护机制加固**：`FleetGuardian_AutoStart` 开机自启（onlogon）已注册——之前 fleet_guardian 只有脚本无计划任务，8/8 后无日志，属潜在空转
- **新快照**：`snapshots/normal_node_20260813_150547.tar.gz`（11MB < 20M）——排除 02_候选设计稿/PNG/PSD/zip 等大文件后达标，作为当前回滚基线

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| 修复后仍复发（第4次） | Hermes 更新覆盖 index.js 带回 max，事后修复治标不治本 | 防生成拦截（模板剔除+自愈正则）+ 巡检定时任务双保险 |
| fleet_guardian 无计划任务 | 只有脚本未注册 onlogon | `schtasks /create /tn FleetGuardian_AutoStart /sc onlogon` |
| 快照超 20M（24MB） | 未排除 02_候选设计稿 及 PNG/PSD/zip 产物 | tar 排除大产物目录+通配符，压缩到 11MB |

### 沉淀位置
- Obsidian wiki：`E:\龙虾AI主控中心\Obsidian\wiki\codex_max_防生成拦截根治_20260813.md`
- 脚本：`scripts\watch_codex_catalog.py`（v1.2）+ `.bat`；守护：`MCP服务\fleet_guardian.py`

---

## 2026-08-13 · codex max防线加固 v1.2 + 正常节点快照（三载体联动 #306 · 1234机制调用）

### 本次亮点
- **防覆盖实锤 + 定时任务静默失效根因**：`WatchCodexCatalog` 原任务指向已不存在的 Python312（`No such file or directory`）——14:40 Hermes 更新覆盖 index.js 模板后，自动防线实际静默失败，仅靠手动运行修复；已 `/change` 改挂 `.workbuddy 3.13.12` + 接单项目版本化脚本，`/run` 手动触发成功
- **脚本升级 v1.2**：`scripts/watch_codex_catalog.py` 模板自愈支持对象/数组/顺序变体正则（`"xhigh","max"` / `"max","xhigh"` / `,"max"]`）+ 日志落盘 `logs/catalog_guard.log`——日志成为"定时任务是否真实执行"的验收依据（避免此前的静默失败重演）
- **双目录同步**：接单项目 `scripts/`（git 版本化）+ AtomCode `scripts/`（原位置）双副本，防单点丢失
- **正常节点快照**：`snapshots/normal_node_20260813_150118.tar.gz`（11MB < 20M）为当前回滚基线

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| 定时任务静默失效 | 任务指向的 Python312 已被卸载/迁移 | schtasks `/change` 改指 .workbuddy 3.13.12（bat 回退链同款） |
| 模板被更新覆盖 | Hermes 更新重写 index.js 带回 max | 守护脚本模板自愈正则化 + 日志留痕，可验证每轮真实执行 |
| 无法确认任务是否跑 | 无日志无输出 | v1.2 起每次运行写 `logs/catalog_guard.log`，验收先看日志 |

### 沉淀位置
- 五步法 §15 + 全域模板 #305/#306 + 脚手架三文件触发行（codex掉线/max报错/调用1234修复）
- 脚本：`企业微信群定制接单项目\scripts\watch_codex_catalog.py`（v1.2）+ `.bat`

---

## 2026-08-13 · codex max档位防复发根治（三载体联动 #305 · 1234机制调用）

### 本次亮点
- **codex 掉线根治（三层根因链）**：①模板源头 `Hermes Studio\resources\webui\dist\server\index.js` 档位数组含 max（`["default","none","minimal","low","medium","high","xhigh","max"]`）→ 备份后剔除；②自愈失效：`watch_codex_catalog.py` 自愈函数只查对象格式 `{effort:"max"}`，而模板实际是数组格式 `"xhigh","max"` → 新增 `TEMPLATE_ARRAY_MAX` 数组剔除；③执行环境：`watch_codex_catalog.bat` Python 回退链漏 .workbuddy，系统默认 python 是损坏 VNPY（`_socket` 缺失）→ bat 首选 .workbuddy 3.13.12
- **防复发机制**：`WatchCodexCatalog` 定时任务 + 30秒轮询扫描全部 catalog，实测全 coding-agent 目录无活跃 max 残留

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| codex 反复报 unknown variant max | Hermes 新会话重新生成 catalog 带出模板 max | 根治模板数组 + 自愈函数支持数组格式 |
| 守护脚本从未生效 | 自愈函数查对象格式，模板是数组格式 | TEMPLATE_ARRAY_MAX 数组剔除 |
| 定时任务跑不通 | bat Python 回退链漏 .workbuddy，系统 python 是坏 VNPY | bat 首选 .workbuddy 3.13.12 |

### 沉淀位置
- 五步法 §15 + 全域模板 #305 + 脚手架三文件触发行（codex掉线/max报错/调用1234修复）
- 脚本：（v1.1 数组自愈版）

---

## 2026-08-13 · 双雄思维蒸馏 + 磁盘清理定时任务 + 对话框保存确认（三载体联动 #302）

### 本次亮点
- **马斯克×巴菲特思维蒸馏 Skill v1.0 落地**：`技能库\马斯克巴菲特思维蒸馏_SKILL.md`——第一性原理（创造）+能力圈（取舍）双雄合流，接单研判→能力圈三问、报价→成本×安全边际、复盘→失败即数据+复利回灌
- **磁盘清理定时任务真实注册**：`Lobster_DiskCleanup_Daily`（每日03:00，schtasks 实测成功），脚本 `scripts\cleanup_disk.cmd`（GBK+CRLF 编码防 cmd 中文乱码）首跑效果：E盘 1.1G→3.9G、回收站全清
- **对话框保存机制确认**：群聊实时落盘 `C:\Users\Administrator\.hermes-web-ui\hermes-web-ui.db`（SQLite+WAL），附件在 group-chat\attachments\；知识沉淀仍需任务卡+SelfLearn+Obsidian 回灌
- **三载体注册完成**：五步法 §11.3 新增「思维蒸馏/磁盘清理」触发词两行 + 全域模板 #302 + 脚手架三文件触发行

### 踩坑
- **cmd 批处理中文路径乱码**：.cmd 脚本含中文路径且 UTF-8 无 BOM 会被 cmd 按 GBK 解析乱码（报「找不到路径」）——必须用 GBK 编码 + CRLF 行尾 + 纯 ASCII 命令体
- **schtasks 注册**：Git Bash 下 `//create` 无效，需 `MSYS_NO_PATHCONV=1 schtasks /create /tn ... /tr "完整路径" /sc daily /st 03:00 /f`

---

## 2026-08-13 · 夜星空01 Step4终验放行 + Step5闭环（任务卡状态机→已放行）

### 本次亮点
- **状态机走通**：已接单→执行中→待审核→**已放行**；任务卡头部状态更新 + Step2/3/4 待办全勾；CLAUDE CODE 四轮终验（review_report.md 附2/3/4）零回归 FINAL PASS
- **快照基线确认**：`snapshots/normal_node_20260812_235516.tar.gz`（10.6M）在盘但被 .gitignore 排除——**glob 工具跳过被忽略文件，核查快照必须用 `ls -la snapshots/`**
- **新快照更新**：`snapshots/normal_node_20260813_001709.tar.gz`（13M<20M）覆盖终验后正常节点，打包到 /tmp 再 mv 回避免自包含
- **GitHub 三通道持续阻塞根因**：GCM 非交互环境报 `/dev/tty: No such device or address`（凭据管理器无终端可交互）+ ssh 无公钥——非网络问题，需 owner 跑 `gh auth login` 打通；CNB（origin）主链路已同步 e6d36e5

## 2026-08-12 · 夜星空01 设计三件套交付闭环（PSD+网页+Word）

### 本次亮点
- **三件套一键贯通**：Logo/Banner/海报（1920px·72PPI）PNG+PSD 由 `generate_design_v1.py`（PIL 绘制 + psd_tools frompil 封 PSD）生成；Word 交付说明由 `generate_delivery_doc.py`（python-docx）生成，零积分全本地
- **同 VI 多载体**：style.css 与 PSD 共享配色令牌（#0b1026/#1a2350/#f5e9c8/#ffb84d），平面+网页风格锁死
- **CNB 推送成功**：`8bf36fc..5cbe62e main -> main`；GitHub 直连被中止 + gh-proxy token 失效 + ssh 无公钥，交由 `Lobster_AutoSync_30min` 自动重试兜底
- 复盘已回灌 `docs/技能沉淀/` + Obsidian/副业变现

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| E:\VNPY python 无 pip/docx/psd_tools | 统一走 `.workbuddy/binaries/python/versions/3.13.12/python.exe`（PIL/docx/psd_tools 齐全） |
| Word 脚本路径错位（`../最终交付文件` 落到工程源文件下） | 修正为 `../..` 向上两级到任务卡根 |
| GitHub 三条通道全阻塞（443 中止/代理 token 失效/无 ssh key） | CNB 主链路闭环 + 30 分钟同步任务自动重试，不阻塞交付 |

### 待办（下一迭代）
- PSD 升级多图层（背景/星点/文字分层）便于客户编辑
- 客户真实品牌资料到位后一键替换占位文案重跑

---

## 2026-08-12 · 设计类商单流水线落地 + 定时任务真实注册 + 夜星空01首单

### 本次亮点
- `docs/设计类商单流水线.md` v1.0 落地（五步闭环 + 网页专项 + 双仓库 + 自我进化 + 关键词触发）
- CLAUDE.md 注册触发：`设计单/接单` `网页设计` `交付/上传`
- 定时任务 **schtasks 真实注册成功**：`Lobster_DailyLearn_0900`（每日09:00学习对标）+ `Lobster_AutoSync_30min`（每30分钟双推+Obsidian增量）
- 夜星空01（task08121841139602）任务卡建档 + 网页骨架交付（web/index.html + style.css）
- CNB 云原生推送成功：c132f1b→acd6597

### 踩坑与解法（定时任务注册）
| 坑 | 解法 |
|----|------|
| 之前只有 .sh 脚本没真实注册计划任务（schtasks 查询不到） | 建 `.cmd` 包装脚本指向 git-bash，`schtasks /create /sc daily /st 09:00` 与 `/sc minute /mo 30` 注册成功 |
| git-bash 调 schtasks 时 `/query` `/tr` 被 MSYS 路径转换破坏 | 加 `MSYS_NO_PATHCONV=1` 前缀，路径双反斜杠+引号包裹 |
| GitHub 直连 443 超时（网络中断） | 交由 30 分钟同步任务自动重试 `git push direct main`，不阻塞交付 |

### 待办（下一迭代）
- Step3 设计执行：PSD（Logo/Banner/海报 1920px·72PPI）+ Word 交付文档
- Step4 审核验收：CLAUDE CODE review_report.md
- GitHub 推送：网络恢复后由 Lobster_AutoSync_30min 兜底

### 四化状态
- [x] 智能化：流水线自动唤起，接单即建档
- [x] 定制化：客户风格蒸馏为设计偏好模板（Obsidian/副业变现）
- [x] 全自动化：定时学习对标 + 双同步托管
- [x] 自我进化：沉淀即进化，本记录 + wiki 案例回灌

---

## 2026-08-08 · AutoGPT 融合 ORCA 全链路（Issue #10 首轮交付）

### 本次亮点
- 桥接脚本 `auto_gpt_orca_bridge.py` 打通 AutoGPT 与四大赛道入口，任务卡自动落地 `fleet_exchange/incoming/`
- 五步法蒸馏为 AutoGPT 可视化节点模板（5 节点 + 4 赛道预设 + 4 触发器预设）
- 触发器脚本 `auto_gpt_trigger_config.py` 同步 schtasks，全自动化托管

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| YAML 块序列后紧跟 mapping key 报 `expected <block end>` | 将 `node_3_execute(entry=...)` 改为 `"node_3_execute(entry=...)"` 引号包裹 / 重构为规范 `nodes:` 子列表 |
| `info[chr(100)...]` 动态 key 可读性差 | 直接 `info["desc"]`，代码可读性优先 |
| 环境变量缺失（GH_TOKEN/Cookie） | 桥接 `_check_env_ready()` 仅做存在性校验，不打印明文；缺失只告警不阻断 |

### 待办（下一迭代）
- 本地 Windows 执行 `E:\龙虾AI主控中心\AutoGPT-Agent` 私有化部署（云端容器无法直连 E 盘）
- 本地执行 G 盘 schtasks 同步 + Obsidian 录入归档
- ~~补齐 `auto_xianyu_scheduler.py` / `quant_scheduler.py` 两赛道入口脚本~~ → 已由第二轮完成

### 四化状态
- [x] 智能化：AutoGPT 自然语言顶层入口 + 自主拆解
- [x] 定制化：≥80 分自动标记 PRODUCTION 商用技能
- [x] 全自动化：触发器配置统一在 config/autogpt/triggers.yaml，Marvis 本地部署
- [x] 自我净化：SelfLearn_Record.md 持续沉淀 + 失败自动记录

---

## 2026-08-08 · 第二轮迭代（Issue #10 · 云端容器内交付）

> 边界：云端只做容器内工作，不操作 Windows 本地系统；不生成 schtasks/E盘/Obsidian 执行逻辑；只产出源码/脚本/yaml/文档，全部提交 PR #21。

### 本次交付
- 新增 `scripts/auto_xianyu_scheduler.py`（闲鱼自动化业务源码，不含 schtasks）
- 新增 `scripts/quant_scheduler.py`（嘉盛/币安双仓巡检业务源码，不含 schtasks）
- 重构 `scripts/auto_gpt_trigger_config.py`：**移除 schtasks 直接执行代码**，仅封装配置解析+参数校验，新增 `validate/export/show` 子命令，输出结构化任务清单 `local_job_queue.json`
- 新增 `config/autogpt/` 三份配置（triggers.yaml / xianyu_config.yaml / quant_config.yaml）
- 新增 `docs/云端产物交付清单.md`（标注 Marvis 需本机部署的文件）
- 维护 `auto_gpt_orca_bridge.py`（网盘萃取/企业接单链路不变，闲鱼/量化补 --action 参数模板）与五步法模板

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| 旧触发器脚本直接生成 schtasks 命令，违反云端边界 | 重构为仅配置解析+参数校验，输出结构化任务清单 JSON，由 Marvis 本地消费 |
| 闲鱼/量化入口 args_template 为空导致 bridge 只能传任务标题 | 改为 `["--action", "{action}"]`，从任务卡 JSON 的 action 字段驱动业务动作 |
| 触发器配置散落模板/脚本多处 | 统一收口到 `config/autogpt/triggers.yaml`，脚本/模板/队列三处引用对齐 |

### 待办（下一迭代 / Marvis 本地）
- Marvis 依据 `local_job_queue.json` 在本机落 Windows 计划任务（云端不生成 schtasks 命令）
- 本地 E/G 双盘 + Obsidian 录入（`scripts/export_to_github_and_mirror.sh`）

---

*本记录由 CodeBuddy 维护，供赛博书屋双向自学习使用。*

---

## 2026-08-08 · 第三轮迭代（Issue #10 · 45元订单整改复盘）

> 触发：45元金榜题名海报订单需求误判（NPC 仅产出两张纯色渐变空白背景图，遗漏图文核心元素，PR#23 稿件作废）
> 整改命令：汤嘉锋（cnb.bMwxU6vpAHA）强制执行，永久禁止 NPC 绕过 AutoGPT 链路直接接单出稿。

### 整改措施（已执行）
1. ✅ **回滚 PR#23**：删除 8 个误判文件（两张空白渐变 SVG/PNG 各版本 + 交付说明 + 旧任务卡），提交 `582f1b0` 推送到 main
2. ✅ **订单重新经 AutoGPT 桥接调度**：`auto_gpt_orca_bridge.py dispatch --workflow 企业接单`，任务卡 `20260808_222347_AG`
3. ✅ **桥接脚本加固**：
   - `_parse_task`：requirement/desc/description 归一化，杜绝需求要素漏传
   - `_build_cmd`：flag+占位符成对处理，priority/deadline 缺省不悬空（修复 unbound variable）
   - 新增 `_parse_elements`：AutoGPT 结构化需求拆解清单（插画/文字/配色/装饰/尺寸/交付格式/工期），先核验再出稿
4. ✅ **完整海报出稿**：`gen_jinbang_guofeng_poster.py` 产出图文结构完整的国风海报（红调主视觉/古风人物/灯笼烟花/金榜题名书法大字/版式排版），SVG 矢量源兼容 CDR 导出，归档至 `01_正在执行实单/【20260808_背景图设计_类似参考_45元】`
5. ✅ **Marvis 落地闭环**：`local_job_queue.json` 追加一次性落地任务 `jinbang45_poster_delivery`（客户确认后替换占位符/SVG转CDR/交付客户）

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| NPC 跳过 AutoGPT 直接解析群单出稿 → 整张海报误判为纯色背景 | 永久规则：企业接单群订单一律复制群原文 → AutoGPT 结构化拆解 → 核验要素清单 → 再启动出稿 |
| 桥接脚本 requirement 字段未传递（desc 变标题）、优先级丢失 | `_parse_task` 归一化 requirement/desc/description；`_build_cmd` 成对处理 flag+值 |
| --deadline 无值时悬空导致 unbound variable | 占位符值缺省跳过整对 flag，由下游默认值兜底 |
| 出稿无图文结构验证 | 交付说明附验收对照清单（8 要素逐项核验），仅图文完整匹配才可合并 PR |

### 验收清单（写入快照，供后续订单复用）
- [x] 回滚误判稿 + 清空物料目录
- [x] AutoGPT 拆单链路（任务卡含结构化拆解清单）
- [x] 核验需求要素齐全（8 项：红调主视觉/古风人物插画/灯笼/烟花/书法大字/国风版式/版式排版/CDR源文件）
- [x] 完整海报 SVG 源文件 + PNG 预览归档
- [x] Marvis 监听 local_job_queue.json 落地闭环登记
- [ ] 客户确认后由 Marvis 替换占位信息/转 CDR/交付（本机侧）

### 永久规则（公示）
> 企业接单群所有订单统一流程：**复制群内原文 → 触发 AutoGPT 接单技能自动拆解 → 核验需求 → Marvis 协同落地交付**，永久禁止 NPC 绕过链路直接接单出稿。偏差稿件直接回滚重跑。

---

## 2026-08-12 · 三引擎正常节点快照 + 任务卡协作机制固化

### 本次亮点
- **正常节点确认**：hermes/codex/CLAUDE CODE 三引擎全部正常运转（deepseek-v4-flash 经 127.0.0.1:13460 代理），此前三类反复故障（doubao-proxy stdio/url 冲突、max 非法档位、代理 502）全部修复
- **轻量快照**：`snapshots/normal_node_20260812_235516.tar.gz`（11M < 20M，排除 .git/对话记录/msgbus/fleet_exchange/worktrees/logs），备份回滚基线
- **任务卡交流机制固化**：CLAUDE.md / CODEX.md / HERMES.md（新建）/ hermes/system_prompt.md 四处写入「任务卡五段结构 + 状态机（已接单→执行中→待审核→已放行→已归档）+ 三Agent交接规则」
- **四化迭代**：wiki 入库 `Obsidian/wiki/舰队运维/三引擎正常节点快照与任务卡机制_20260812.md` + 复盘 `docs/技能沉淀/20260812_三引擎正常节点快照与任务卡机制_复盘.md`

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| tar 打包时快照文件自身被读入（file changed as we read it） | 先打包到 /tmp 再 mv 回 snapshots/，避免自包含 |
| HERMES.md 脚手架缺失（此前只有 CLAUDE.md/CODEX.md） | 新建 HERMES.md，与 hermes/system_prompt.md 双轨对齐 |
| Obsidian 归档路径此前审核未落地 | 确认 E:\龙虾AI主控中心\Obsidian\wiki\ 实际存在，直接入库舰队运维/ |

### 永久规则
> 每个订单以「任务卡」为唯一交流/分配中枢，群聊只做触发与汇报；快照统一命名 `snapshots/normal_node_*.tar.gz` 且 <20M。

---

## 自动追加区（桥接脚本实时写入）

- [20260808_201532_AG] 企业接单 执行成功：20260808_201532_AG__AutoGPT_企业接单.md
- [20260808_222211_AG] 企业接单 执行成功：20260808_222211_AG__AutoGPT_企业接单.md
- [20260808_222323_AG] 企业接单 执行成功：20260808_222323_AG__AutoGPT_企业接单.md
- [20260808_222331_AG] 企业接单 执行失败 rc=1，踩坑：/workspace/scripts/maris_dispatch.sh: line 28: $2: unbound variable

- [20260808_222347_AG] 企业接单 执行成功：20260808_222347_AG__AutoGPT_企业接单.md
- [20260808_225321_AG] 企业接单 执行成功：20260808_225321_AG__AutoGPT_企业接单.md
- [20260808_230405_AG] 企业接单 执行成功：20260808_230405_AG__AutoGPT_企业接单.md
