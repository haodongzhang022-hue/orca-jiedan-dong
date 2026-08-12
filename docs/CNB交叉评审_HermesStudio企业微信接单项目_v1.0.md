# CNB 云原生 × CodeBuddy 交叉评审报告 — Hermes Studio「企业微信群定制接单项目」

> 评审者：CodeBuddy（CNB 云原生底层视角）
> 评审对象：`TJF19770107/orca-jiedan` 仓库 · Hermes Studio 多智能体接单项目
> 评审日期：2026-08-13 ｜ 评审基线：commit `3202391`（main）
> 评审性质：独立交叉评价（对照会话日志、脚本、配置做实证评审，非主观想象）
> 当前阶段：**多智能体接单初级门槛 → 定向补齐短板 → 向高度自动化推进**

---

## 〇、整体现状打分与结论

### 综合评分：**7.0 / 10**

| 维度 | 评分 | 说明 |
|---|---|---|
| 架构设计 | 8.0 | 双路径 A/B、四角色矩阵、云原生+本地双通道设计成熟 |
| 基础链路跑通 | 8.0 | Hermes/Codex/Claude-Code 群聊协同、接单流转已实测跑通 |
| 免费基座接入 | 8.5 | deepseek-v4-flash 免费网关 A/B 双配置完备，0 外部付费 |
| 安全基线 | 5.5 | **存在 P0 明文密钥泄露**（历史会话日志），需立即处置 |
| 知识库闭环 | 5.0 | 同步链路存在明显断点（记忆三卡片缺失、反馈阻断） |
| 故障自愈 | 5.5 | 降级/重试策略有雏形但不完整，错误处理不均 |
| 自动化程度 | 6.0 | 定时任务已注册，但仍是「初阶自动化」，离高度自动化有差距 |

### 已达成能力（实证）

1. **多智能体群聊协同基础链路已跑通**：Hermes=大脑、Codex=执行、Claude-Code=核查，任务状态机（已接单→执行中→待审核→已放行→已归档）已在脚手架三文件（CLAUDE.md/CODEX.md/HERMES.md）落地。
2. **CNB 免费网关双路径完备**：方式B手动（GUI 建 Provider）+ 方式A脚本（`switch_to_cnb_gateway.sh` / `one_click_cnb_gateway.sh`）幂等兜底；`base_url` 带 `s` 后缀、model 锁定 `deepseek-v4-flash`（非 pro 防扣费）、Token 走环境变量 `%CNB_TOKEN%` 不落盘。
3. **云上复刻 WebGUI 已交付**：`.ide/Dockerfile`（基于 `ekkoye8888/hermes-web-ui:v0.6.39`）+ `vscode` 事件 + 适配层（127.0.0.1:8787），6060 端口映射已验证可达。
4. **四角色栈一键自检**：`one_click_npc_stack.sh` 可探活 CLI/适配层/基座锁定/额度。
5. **真实商单闭环**：夜星空01 设计单（PSD+网页+Word）已交付，SelfLearn 复盘已回灌。
6. **定时任务真实注册**：`Lobster_AutoSync_30min`（每30分钟双推+Obsidian增量）、`Lobster_DailyLearn_0900` schtasks 验证通过。

### 当前所处阶段
**初阶门槛（Level 1）**：基础链路通、能接单、能交付，但「自动化→高度自动化」之间还有三座山：**密钥安全红线、知识库闭环断点、故障自愈不均**。

---

## 一、P0 阻断缺陷（必须立即修复，否则有泄漏/停机风险）

### P0-1 🔴 明文 API 密钥已入库（安全红线）
- **现象**：`对话记录/历史会话/20260803_2000_20260803.md` 第351行存在明文 `DEEPSEEK_API_KEY=[REDACTED-SECRET]`。
- **根因**：历史会话日志把 `.env`/环境变量内容整段复制进 Markdown 落库，且该文件在 `.gitignore` 白名单之外被正常提交。
- **影响**：仓库若为私有则风险可控，但一旦误公开/被 fork/共享，密钥即泄露；且该 key 是第三方 OpenModel 的（非 CNB 平台 token），属外部资产泄露，风险更高。
- **修复建议**：
  1. 立即**吊销/轮换**该 key（若仍有效）；
  2. 从 git 历史清除：`git filter-repo` 或 `git filter-branch` 移除该文件/该行；
  3. `.gitignore` 增加 `对话记录/**/*.md` 中对 `sk-`/`DEEPSEEK_API_KEY` 的防御，或在 `export_to_github_and_mirror.sh` 打包时对该目录做密钥扫描过滤；
  4. 新增提交前钩子（pre-commit）扫描 `sk-[A-Za-z0-9]{20,}` 与 `(api[_-]?key|token)\s*[:=]\s*['"]?[A-Za-z0-9]{20,}` 阻断入库。

### P0-2 🔴 多 Agent「互相等待卡死」无超时熔断
- **现象**：群聊链路 Hermes→Codex→Claude-Code 依赖任务卡状态机流转，但 `.cnb.yml` 中 `options.maxTurns: 12` 只限制单 Agent 轮次，**没有跨 Agent 的等待超时/重试熔断机制**；若 Codex 中途失败未回写任务卡，Hermes 侧无看门狗主动打回，整单可能悬挂。
- **根因**：状态机是「事件驱动回写」，缺「超时巡检」兜底。
- **影响**：真实商单卡死在"待审核"状态时，无自动恢复。
- **修复建议**：给 `pipeline_autopilot_daemon.py` 加**超时巡检**（如任务卡在「执行中」超过 N 小时且无回写 → 自动打回/告警），并把巡检结果写 `msgbus/inbox/echo_wall/`。

### P0-3 🟠 云端 WebGUI 回收机制误读为"常驻"的风险
- **现象**：`.ide/` 与 `.cnb.yml` 已正确声明回收机制（10分钟无操作/最长18h/凌晨4-6点强制），但**文档层面仍存在"云上复刻=常驻服务"的潜在误导**（`docs/一键操作手册` 等处）。
- **根因**：云原生开发环境本质是"出差兜底"，非 7×24 服务；用户若长期依赖云端 WebGUI 会踩到回收断连。
- **影响**：中低（文档已声明），但影响体验预期管理。
- **修复建议**：在 README/操作手册显著位置标注"云端 WebGUI 非 7×24，日常编排以本地桌面版为准"，并给出"断连后一键重建"的命令。

---

## 二、P1 重要优化（不阻断，但显著影响稳定与体验）

### P1-1 🟠 Obsidian 知识库闭环存在断点——「三份记忆卡片」未打通
- **现象**：评审指令特别点名的「我的笔记、用户画像、灵魂」三份记忆卡片，在仓库中**未找到对应资产**（`grep` 仅在历史会话/快照中出现，非独立记忆卡）。知识库同步脚本（`archive_obsidian_v1.6.0.sh`、`auto_sync_30min.sh`）只做**文档资产单向复制**，没有「记忆修改→归档→反向赋能智能体执行」的反馈回路。
- **根因**：
  1. 记忆卡体系定义了但未落地为仓库内可版本化的结构化文件；
  2. 同步是"单向 push 到 Obsidian"，缺"Obsidian 编辑→拉回仓库→注入 agent prompt"的**反向闭环**；
  3. `auto_sync_30min.sh` 的 Obsidian 同步是 `robocopy /MIR`（从 E→G），**未覆盖"Obsidian 反哺仓库"**。
- **影响**：知识库沦为"只读归档"，无法反向赋能，与「四化-自我进化」目标背离。
- **修复建议**：
  1. 在仓库 `docs/记忆卡片/` 下建三份结构化记忆卡（`我的笔记.md`/`用户画像.md`/`灵魂.md`），随脚手架三文件一起版本化；
  2. 扩展 `auto_sync_30min.sh`：加一段"Obsidian 记忆卡 → 仓库"的反向同步（`robocopy` 或 `cp` 回流 + 冲突用 git 管理）；
  3. 在 HERMES.md/CLAUDE.md 的 agent 系统提示中，显式声明"启动时读取三份记忆卡"。

### P1-2 🟠 MIMO 到期降级预案"有声明、无自动执行"
- **现象**：`fleet_start_mimo.bat` 标注「到期 2026-08-14」；`adapters/anthropic_to_cnb.py` 有 `quota_available()` 额度降级（超限返回429），但**没有"MIMO 到期→自动切换 CNB"的自动执行脚本**——目前切换依赖 `switch_to_cnb_gateway.sh` 手动/半自动跑。
- **根因**：降级保护只覆盖"额度超限"（quota），未覆盖"模型端点失效/到期"（MIMO 到期是端点级，非额度级）。
- **影响**：2026-08-14 后若仍有 Agent 走 MIMO 端点，会直接 4xx/5xx 失败，除非手动切。
- **修复建议**：给 `switch_to_cnb_gateway.sh` 加 `--auto-failover`：探测 MIMO 端点健康，若不可用自动把 provider 指到 CNB，并把切换结果写痕迹墙。

### P1-3 🟠 适配层错误处理不均——重试/退避策略缺失
- **现象**：`adapters/anthropic_to_cnb.py` 对上游 HTTP 错误只返回状态码（404→404、403→403、超限→429、其它→502），**没有指数退避重试**；一次性 `urlopen(timeout=300)`，网络抖动即失败。
- **根因**：适配层定位为"转发代理"，未内建重试语义（重试交给上层 Agent 的 maxTurns，但 Agent 未必重试）。
- **影响**：评审指令提到的"API 重试失败"问题即源于此——非流式长响应在 300s 超时或偶发网络错误时直接失败，不自动重试。
- **修复建议**：在 `_proxy()` 加 2-3 次指数退避重试（对 429/5xx/超时），对 4xx 不重试；重试次数用环境变量可配。

### P1-4 🟠 WinError 206 / 文件名过长（Windows 路径限制）
- **现象**：评审指令明确记录"WinError 206 文件名过长报错"；仓库大量使用超长中文路径（如 `E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/01_正在执行实单/【20260812_夜星空01_...】`），极易触发 Windows MAX_PATH(260) 限制。
- **根因**：中文长目录 + 深嵌套 + 长文件名叠加超限。
- **影响**：脚本/归档/同步在 Windows 侧偶发路径过长失败。
- **修复建议**：全局启用 `\\?\` 长路径前缀，或在脚本里加 `WinError 206` 检测并降级到短路径别名（junction）；归档脚本对目标文件长度做校验截断。

### P1-5 🟠 `gh auth login` 阻塞是 GitHub 三通道全阻的根因，且无自动兜底
- **现象**：SelfLearn 记录 GitHub 三通道全阻塞（GCM 非交互 `/dev/tty` 报错 + ssh 无公钥）。CNB(origin) 主链路正常，但 `auto_sync_30min.sh` 的 `git push direct` 持续失败。
- **根因**：需 owner 手动跑 `gh auth login` 打通 GCM 非交互凭据；非网络问题。
- **影响**：GitHub 镜像同步持续失败（体验级，CNB 主链路不受影响）。
- **修复建议**：文档化 `gh auth login` 一次性打通步骤；`auto_sync_30min.sh` 对 GitHub 失败做静默重试+告警，不阻塞 CNB 主链路（已部分实现）。

### P1-6 🟠 快照/分支治理需固化「基线索引」
- **现象**：已有 `snapshots/normal_node_20260812_235516.tar.gz` 与 `001709.tar.gz` 基线，且 git log 有"快照基线索引"提交（标注 001709 为回滚基线）。但 `snapshots/` 被 `.gitignore` 排除（仅本地，云端无备份），存在"本地盘损坏则基线全丢"风险。
- **根因**：快照含敏感/大文件不便入库，故排除，但失去云端冗余。
- **影响**：回滚基线仅存本地单点。
- **修复建议**：快照 tar.gz 上传 CNB 制品库/附件（或私有对象存储），云端留存一份基线。

---

## 三、P2 远期改善

### P2-1 🟡 云端实时群聊不可行——痕迹墙已是务实方案，但可增强
- 现状已正确声明"云端 NPC 一次性容器不支持常驻实时群聊"，用 `msgbus/inbox/echo_wall/` 痕迹墙做等价可见。远期可：让 Hermes Studio 桌面版定时拉取痕迹墙并渲染成"群聊时间线"视图，接近实时体验。

### P2-2 🟡 三份记忆卡迭代自动化
- 远期将"记忆卡"纳入 `auto_knowledge_extract.py` 萃取管线，商单复盘自动更新用户画像/我的笔记，实现"每单闭环自动进化"。

### P2-3 🟡 多 Agent 长任务分片并行度不足
- 当前主要是串行接力（Hermes→Codex→Claude），长任务分片并行（多 Codex 并行写不同模块）仅在脚本/文档层面提及，实际并行调度未成熟。远期引入 Worktree 并行分支 + 一键 PR 合并。

### P2-4 🟡 错误码标准化与可观测性
- 适配层/脚本错误码不统一，建议统一 JSON 错误结构 + 汇总到 `logs/` + 痕迹墙，便于自动巡检。

---

## 四、逐维度核验结果（对应评审指令 1-7）

### 1. 多智能体角色分工校验 ✅（基本清晰，有卡死风险见 P0-2）
- Hermes=大脑/总控、Codex=执行层、Claude-Code=核查校验层，分工边界在 CLAUDE.md/CODEX.md/HERMES.md 明确。
- 越权/重复执行：未发现明显越权；重复执行风险集中在无超时熔断时的人工重试。
- 长任务分片并行：**逻辑生效但实际并行度不足**（P2-3）。

### 2. DeepSeek-v4-flash 免费网关链路评审 ⚠️（链路完备，容错不均）
- 方式B/方式A 双配置：✅ 完备（见一键操作手册）。
- base_url `completions` 后缀、`%CNB_TOKEN%` 环境变量：✅ 正确；禁止明文写入：✅（脚本只写 `api_key_env: CNB_TOKEN`）。**但历史会话有第三方明文 key（P0-1）**。
- MIMO 到期降级预案：⚠️ 有额度降级，**缺端点失效自动切换**（P1-2）。
- 云端 WebGUI 构建脚本/回收机制：✅ 已实现且文档声明；风险见 P0-3。
- 报错容错/403/404/500/重试：⚠️ 有 404/429/502 处理，**缺指数退避重试**（P1-3）。

### 3. 龙虾体系落地核验 ✅（已真正加载生效）
- 龙虾五步法 §14 五部分执行指令、全域模板 #301 三载体联动：已在脚手架三文件落地（CLAUDE.md/CODEX.md/HERMES.md 均含"五部分执行指令默认加载 + 联动迭代三载体"）。
- 项目脚手架/龙虾AI分身技能库：✅ 引用正常（skill_registry.json、templates/skill_lib）。
- 四化迭代：智能化✅、个性化⚠️（用户画像卡缺失）、自动化✅、自我进化⚠️（知识库反哺断点，P1-1）。

### 4. Obsidian 知识库闭环专项评审 🔴（重点短板，P1-1）
- 记忆资产同步链路：**单向**（仓库→Obsidian），缺反向（Obsidian→仓库赋能执行）。
- 软链接/E盘G盘 mklink：✅ `create_junction_links.ps1` 已实现。
- 定时同步脚本：✅ `auto_sync_30min.sh`（含 Obsidian 增量）+ `run_daily_learn_0900.cmd`。
- 任务复盘/群聊日志/技能产出物自动回流：⚠️ 复盘回灌 SelfLearn 有做，但**群聊日志/技能产出物的自动化回流未形成稳定链路**。
- 三份记忆卡片迭代更新：🔴 **未打通**（P1-1 根因）。

### 5. Git/CNB 仓库与安全评审 🔴（P0-1 密钥 + P1-5/6）
- `gh auth login` 阻塞影响范围：仅 GitHub 镜像，CNB 主链路正常（P1-5）。
- Token 环境变量：✅ 脚本层合规；**历史会话有明文第三方 key**（P0-1）。
- 提交链 ff7d7e44 快照、skill-workflow-v4.0 分支：✅ 均存在（`git cat-file` 验证 commit 存在，`origin/skill-workflow-v4.0` 分支在）。
- 脚本备份 bak 时间戳机制：✅ `switch_to_cnb_gateway.sh` 用 `*.bak.<时间戳>` 可回滚。

### 6. 接单业务全链路评审 ✅（链路完整，细节可优化）
- Issue录入→codex拆解→五维过滤→审核报价→交付→权益统计→归档：✅ 状态机 + route_1/2/3 三路线 + autopilot 已落地。
- 成本复盘/接单核对清单：✅ 有 `docs/接单策略与分层报价规范.md`。
- token 消耗/工具冗余/耗时：⚠️ 有 quota_monitor 监控，但"工具调用冗余"优化空间大（适配层无重试、长任务串行）。

### 7. 故障与历史问题复盘 ✅（记录充分，处置有沉淀）
- API 重试失败：根因=适配层无重试（P1-3）。
- WinError 206 文件名过长：根因=Windows MAX_PATH（P1-4）。
- 待办分级：P0 密钥泄漏、任务卡悬挂；P1 记忆卡闭环、MIMO 到期切换、错误重试、路径过长、GitHub 凭据；P2 群聊可视化、分片并行、可观测性。

---

## 五、可直接执行的修复清单（按优先级）

### 🔴 立即执行（今天）
1. **吊销并清除明文 key**：
```bash
# 1) 从 git 历史移除含 key 的文件（用 filter-repo 或 filter-branch）
cd /path/to/repo
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch '对话记录/历史会话/20260803_2000_20260803.md'" \
  --prune-empty --tag-name-filter cat -- --all
# 2) 强制推送（若私有仓库且确信无 clone）
git push origin --force --all
# 3) 吊销原 key（去 OpenModel 控制台）
```
2. **pre-commit 密钥扫描钩子**：`scripts/secret_scan_precommit.sh`，扫描 `sk-[A-Za-z0-9]{20,}` 与 `(api[_-]?key|token)\s*[:=]\s*['"]?[A-Za-z0-9]{20,}`，命中即拒绝提交。

### 🟠 本周内
3. **适配层加指数退避重试**（`adapters/anthropic_to_cnb.py` `_proxy`）。
4. **MIMO 到期自动切换**：`switch_to_cnb_gateway.sh --auto-failover`。
5. **建三份记忆卡**：`docs/记忆卡片/{我的笔记,用户画像,灵魂}.md`，并接入 `auto_sync_30min.sh` 反向同步。
6. **autopilot 加任务卡悬挂巡检**（超时打回）。

### 🟡 远期
7. WinError 206 长路径防护、GitHub 凭据打通文档、快照上云、痕迹墙时间线渲染。

---

## 六、验收核对清单（供 MARVIS 后续自检）

> 每跑一轮接单任务，对照此清单自检，防旧故障复现。

### A. 安全红线
- [ ] 提交前执行 `bash scripts/secret_scan_precommit.sh` 无密钥命中
- [ ] `git log --all -S "sk-"` 无明文密钥残留
- [ ] 所有 Token 走环境变量（`%CNB_TOKEN%`），无 `api_key: 明文`

### B. 网关与模型
- [ ] `switch_to_cnb_gateway.sh --check-only` 显示 `✅ provider 'cnb-deepseek-v4-flash' 已注册`
- [ ] 会话右上角模型 = `deepseek-v4-flash`（非 MiMo，防扣费）
- [ ] base_url 末尾为 `completions`（带 s），非 `completion`/`completiong`
- [ ] MIMO 到期后已自动 failover 到 CNB（无 4xx/5xx 端点失败）

### C. 群聊链路与任务状态
- [ ] 任务卡状态机正常流转：已接单→执行中→待审核→已放行→已归档
- [ ] 无任务卡在「执行中/待审核」悬挂超过阈值（autopilot 巡检生效）
- [ ] 痕迹墙 `msgbus/inbox/echo_wall/` 有当轮 Agent 交流记录

### D. 知识库闭环
- [ ] 三份记忆卡（我的笔记/用户画像/灵魂）存在且已随本轮更新
- [ ] `auto_sync_30min.sh` 双向同步（仓库↔Obsidian）成功，无断点
- [ ] 复盘已回灌 SelfLearn_Record.md + Obsidian

### E. 快照与备份
- [ ] 快照基线已更新并留存（本地 + 云端冗余）
- [ ] 脚本变更均带 `.bak.<时间戳>` 备份
- [ ] CNB(origin) 主链路同步成功，GitHub 镜像尽力而为不阻塞

### F. 稳定性
- [ ] 适配层重试策略生效（429/5xx/超时自动退避重试）
- [ ] 无 WinError 206 文件名过长报错
- [ ] 云端 WebGUI 断连后一键重建可用

---

## 附：评审依据（实证材料）
- 会话日志：`对话记录/历史会话/20260803_*.md`（含明文 key 实证）
- 网关脚本：`scripts/switch_to_cnb_gateway.sh`、`scripts/one_click_cnb_gateway.sh`
- 适配层：`adapters/anthropic_to_cnb.py`（额度降级 + 错误处理实证）
- 知识库：`scripts/archive_obsidian_v1.6.0.sh`、`scripts/auto_sync_30min.sh`
- 脚手架：`CLAUDE.md`/`CODEX.md`/`HERMES.md`/`SKILL.md`（五步法/全域模板落地实证）
- 云上复刻：`.ide/Dockerfile`、`.cnb.yml`（vscode 事件 + 回收机制）
- 快照/分支：`git cat-file ff7d7e44`（存在）、`origin/skill-workflow-v4.0`（存在）
- 复盘：`SelfLearn_Record.md`（gh auth / 路径 / 定时任务实证）

---

*本报告已按评审指令要求：定位 P0/P1/P2 分级、给出可执行修复、附验收清单；并将在提交后同步到 Obsidian 知识库与脚手架文档，完成四化迭代闭环。*
