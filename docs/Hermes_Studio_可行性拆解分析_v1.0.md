# Hermes Studio 可行性拆解分析报告

> 任务来源：Issue #27（全域模板 + 龙虾五步法）
> 执行角色：CodeBuddy ｜ 生成日期：2026-08-09 ｜ 基座：CNB 内置免费 DeepSeek-V4-Flash
> 方法：龙虾五步法（识别 → 映射 → 规划 → 执行 → 沉淀）｜ 版本：v1.0
> 边界声明：本报告所有"CNB 平台限制"均基于 CNB 官方文档（docs.cnb.cool）如实引用，不臆造、不粉饰。

---

## 〇、执行摘要（结论先行）

| # | 关键问题 | 一句话结论 |
|---|----------|-----------|
| 1 | Hermes Studio 与本地 ORCA / CCGUI 的关系 | 三者**不是同类**：Hermes Studio=本地桌面编排 IDE（含多 Agent 群聊/Worktree/GUI）；本地 ORCA 调度=自建三 Agent 双实例六入口舰队（msgbus+fleet_exchange 文件总线）；CCGUI=CC-Switch 统一模型/仓库切换器。**可共存、可桥接，不适合互相替换** |
| 2 | CNB 云端 NPC 能否桥接到本地 Hermes Studio | ✅ **技术上可桥接但非"桌面直连"**：当前成熟路径是"本地 Hermes 桌面端把模型端点指向 CNB AI 网关（OpenAI 兼容端点）"，或在云原生开发环境中跑 Hermes Studio Web 端；NPC 事件容器（路径B）是一次性执行单元，**无法被桌面端实时拉活** |
| 3 | 端口/容器/镜像/密钥全链路 | CNB NPC 容器内网监听 `127.0.0.1:8787` **不暴露公网**；云原生开发环境才开放 `0.0.0.0` 端口映射（`https://xxx-{{port}}.cnb.run`）+ VS Code/Cursor 端口转发；镜像走 `docker.cnb.cool/${slug}:tag` 制品库，密钥走环境变量 `CNB_TOKEN` / `ACC_PRODUCT_CONFIG_V2` / imports / 个人环境变量，**镜像零硬编码** |
| 4 | 路径B 打包 Hermes Studio 进 CNB 容器 | ✅ **已部分成立**：本项目 `adapters/Dockerfile` 已把**原生 Hermes CLI（NousResearch/hermes-agent）**打进自定义镜像（1.6.0，1.60GB）；但"桌面可视化 GUI（Studio 图形界面）"需要**云原生开发环境**承载（code-server/WebIDE），与 NPC 一次性容器是两条路 |
| 5 | 内置 Agent 群聊 vs 飞书机器人 | Hermes Studio 群聊=本地编排原生能力（实时、免外网 webhook、可调试）；飞书机器人=企业侧通知/触达（适合对外交付通知、客户触达）。**两者职责不同，建议并存** |
| 6 | 6 仓库对接 | 6 个 orca 仓库（jiedan/wangpan/xianyu/quant-jiasheng/quant-binance/orca）**标准脚手架一致**，Hermes Studio 原生 Git Worktree + 分支隔离可直接套用；但量化两仓含 API 密钥与交易链路，**严禁云端容器访问**，须本机运行 |
| 7 | MIMO-V2.5 调度移除风险 | 现有 `scripts/one_click_mimo_v25.sh`、`fleet_start_mimo.bat`、代理脚本(15721/15730) 大量硬编码 `mimo-v2.5-pro`；**直接移除会引发 Codex/Claude/Hermes 三引擎同时哑火**。建议"先接 CNB 网关替代、再灰度、后归档"，不做删除 |
| 8 | 推荐落地路线 | **不替换、做桥接**：① 本地 Hermes Studio 模型端点切 CNB 免费网关；② 云端 NPC 角色流水线维持路径B；③ 云原生开发环境跑 Hermes Studio Web 可视化管理；④ 6 仓走统一脚手架增量迭代（`upgrade_incremental.sh`，非破坏） |

---

## 一、基础对比维度：三者底层架构完整差异表

> 术语对齐：**Hermes Studio** = Hermes 桌面编排套件（含 TUI/Web GUI/多 Agent 群聊/工作树管理/网关）；**本地 ORCA 调度体系** = 本项目自建三 Agent 舰队（Hermes 大脑+Codex 执行+Claude 审查，msgbus+fleet_exchange+双实例六入口）；**CCGUI** = CC-Switch（Orca IDE 的模型/仓库切换 GUI，含多引擎统一入口）。

| 维度 | Hermes Studio（桌面端） | 本地 ORCA 调度体系（自建舰队） | CCGUI / CC-Switch |
|------|------------------------|------------------------------|-------------------|
| **底层架构** | Hermes Agent 官方套件：Python `hermes-agent` + TUI/Web GUI + Gateway（Telegram/Feishu/Slack/DingTalk/WeCom 多通道）；State DB 持久化会话 | 自研脚手架：三 Agent（Hermes/Codex/Claude）+ `msgbus/` 文件 JSON 消息总线（OMF v1.0）+ `fleet_exchange/` 四级任务流转 + `pipeline_autopilot.py` | CC-Switch 桌面程序：多引擎 API 切换器（Claude/Codex/Hermes/Marvis），管理 `AppData/Roaming/Orca/orca-data.json` 仓库配置 |
| **协作模式** | 群聊式多 Agent 编排（同一项目多 Agent 对话/任务分派/进度跟踪）；Gateway 对接 IM | 链式编排：Hermes 拆单 → Codex 执行 → Claude 审查 → CodeBuddy 终审；任务卡经 `fleet_exchange/incoming→doing→done→results` | 手动切换引擎；进程级管理（不参与业务编排逻辑） |
| **Git Worktree** | 原生支持（多分支多工作树可视化，分支=Agent 隔离） | 自建 `worktrees/{hermes,codex,claude}` 三工作树 + `scripts/orca_setup_worktree.sh` 角色环境注入（.env） | 仅管仓库路径映射，不维护工作树内容 |
| **模型调度** | `hermes model` 切换任意 OpenAI 兼容端点；`.env` / `~/.hermes/config.yaml` | 三套代理：Anthropic 代理(15721)/Codex 代理(15730)/Hermes Gateway(8642)，上游 `mimo-v2.5-pro`（8/14 到期）→ 已迁移方向为 CNB `deepseek-v4-flash` | 多 provider 切换（aicodeswitch 4567），模型名自动转换/降级 |
| **端口占用** | Hermes Gateway 8642；Fleet GUI 15800；TUI 无固定端口；桌面 Web GUI 默认动态 | 15721(Anthropic Proxy)、15730(Codex Proxy)、4567(aicodeswitch)、57330(Claude Serve)、57361-57368(CLI/GUI)、15800-15802(Fleet GUI)、57364(msgbus)、11434(Ollama 可选) | 57320/57321（Orca IDE 相关）；CC-Switch GUI 进程不绑定端口（仅进程管理） |
| **容器运行逻辑** | 本地原生进程（非容器）；官方自带 Dockerfile 但桌面端为桌面进程 | 本地原生进程 + Windows 计划任务/守护（fleet_guardian）；云端侧为 CNB 路径B 容器（见第三节） | 本地原生进程 |
| **持久化** | `AppData/Local/hermes/state.db` 会话持久化 + 对话导出脚本 | `对话记录/` + `msgbus/context/` + Obsidian 知识库 | 配置文件级 |
| **多模态** | 需视觉路由 MCP 补齐（文本强、图片弱） | MiMo 原生多模态（8/14 前）；Ollama 本地多模态 + 视觉路由 MCP | 由所选引擎决定 |
| **当前状态** | 运行时已装（venv+hermes-agent），桌面版 Hermes-Setup.exe 已下载未安装，GUI 15800 常驻 | v1.7.1 运行中：双实例六入口 + AutoGPT 融合 + 四赛道（接单/闲鱼/量化×2/网盘） | 已装，作为多引擎切换入口 |
| **本项目定位** | 商单调度的"决策大脑"桌面前端 | 舰队调度骨架 + 云端 NPC 舰队（路径A/B） | 本地模型/仓库切换工具 |

**差异结论**：
1. **Hermes Studio 是"编排前端"**：它不该替代 ORCA 舰队的 msgbus/fleet_exchange 业务总线，而是作为**可视化入口**挂接到总线之上（读 `fleet_exchange/`、调 `scripts/`）。
2. **CCGUI 与 Hermes Studio 不冲突**：CCGUI 管"模型切到哪个引擎"，Hermes Studio 管"Agent 怎么协作"，本地 ORCA 管"业务流怎么跑"——三者正交，可同时运行。
3. **端口隔离是硬约束**：本地端口全表见附录 A，任何新增服务必须先查表，严禁抢占 15721/15730/8642/4567/11434。

---

## 二、云原生联动需求分析

### 2.1 ① 能否把 CNB 云端 NPC（Hermes/Codex/Claude-Code，DeepSeek-V4-Flash 免费基座）桥接到本地 Hermes Studio 桌面端调用？

**结论：两种"桥接"语义，能力完全不同，务必区分：**

#### 语义 A：把 CNB 的免费模型网关（deepseek-v4-flash）作为 Hermes Studio 的模型后端
- ✅ **可行且推荐**。Hermes Studio 的 `hermes model` 支持任意 OpenAI 兼容端点。
- 模型端点指向 CNB 内置 AI 网关：`https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions`（本项目 `adapters/anthropic_to_cnb.py` 已验证该网关格式）。
- 鉴权：个人访问令牌（CNB Token）放入 Hermes `.env` / `~/.hermes/config.yaml`（**本机文件，不入库**）。
- 优点：免费 1600 核时/月、零本地显存、年底前不过期；缺点：网关鉴权需要有效 Token，属云 API 调用（与 NPC 事件无关）。

#### 语义 B：让"CNB NPC 事件容器"里的 Hermes/Codex/Claude-Code 角色被本地桌面端实时调用
- ⚠️ **不可行（按 CNB 平台机制如实说明）**：
  1. NPC 事件（`issue.comment@npc` / `pull_request.comment@npc`）由 `@提及` 触发，**每次触发拉起一个一次性独立容器**，任务结束即销毁，不存在"常驻云端服务"可供桌面端连接。
  2. 容器内适配层 `127.0.0.1:8787` 是**容器内网监听**，不暴露公网、无固定入口 IP/域名。
  3. NPC 流水线 `CNB_TOKEN` **仅限访问当前仓库**（见官方文档"安全限制"），无法充当对外 API 网关。
  4. 云原生开发环境才有端口映射能力，但那属于"云 IDE"，不是 NPC 事件容器（见 2.3）。

**落地建议**：桌面端桥接走**语义 A**（模型网关桥接），NPC 舰队维持 Issue/PR 评论触发（语义 B 的本职场景），两者通过仓库（git push/PR）汇合，形成"本地 Studio 编排 + 云端 NPC 执行 + PR 闭环"双轨。

### 2.2 ② 端口、容器网络、镜像权限、环境密钥读取全链路可行性（如实说明）

#### 端口全链路

| 环节 | 端口/地址 | 可达性 | 平台限制（官方文档依据） |
|------|-----------|--------|--------------------------|
| NPC 事件容器内适配层 | `127.0.0.1:8787` | 仅容器内 | 平台不对外暴露 NPC 容器端口 |
| 云原生开发 WebIDE 端口映射 | `https://{实例ID}-{{port}}.cnb.run` | 公网可访问 | 服务必须监听 `0.0.0.0`；`localhost/127.0.0.1` 无法映射（`business-preview.md`） |
| VS Code/Cursor 端口转发 | 本地转发到远端容器 | 本地可访问 | 需安装客户端 + Remote-SSH（`vscode-likes.md`） |
| 云原生开发环境 SSH | 22/openssh-server | 需自定义镜像预装 | 见 `vscode-likes.md` 自定义环境配置 |
| 本地桌面端 | 15721/15730/8642/15800 等 | 仅本机 | 无云端依赖 |

#### 容器网络
- NPC 事件容器：一次性任务单元，网络出口开放（可访问外网拉包），**入站端口不开放**。
- 云原生开发容器：支持端口映射/转发，但**有回收机制**——10 分钟无操作回收、最大保持 18 小时、使用超 8 小时且凌晨 4-6 点强制回收（`workspace-recycling.md`）。**不能当常驻服务器用**。

#### 镜像权限
- 构建/推送：`docker.cnb.cool/${CNB_REPO_SLUG_LOWERCASE}:tag`，流水线内用 `CNB_TOKEN` 自动鉴权（`artifact/docker.md`）。
- 拉取：NPC 事件流水线 `docker.image` 引用自定义镜像（本项目已验证 1.6.0 拉取成功）。
- 私有镜像认证：非同名/私有制品需 `dockerUser/dockerPassword` 环境变量（`grammar.md` imports 示例）。
- 本项目镜像 `orca-jiedan:1.6.0` 已验证：linux/amd64、1.60GB、构建溯源 `has_provenance:true`。

#### 环境密钥读取（全链路现状）
| 密钥/配置 | 注入方式 | 生效范围 | 限制 |
|-----------|----------|----------|------|
| `CNB_TOKEN` | 流水线自动注入 | NPC/构建事件 | NPC 事件仅限当前仓库；最大角色=触发用户角色；sandbox 模式下**无效** |
| `ACC_PRODUCT_CONFIG_V2` | 平台自动注入 | NPC/构建/开发容器 | 自动解析内置 AI 网关地址+token（本项目适配层已验证） |
| `CNB_AI_GATEWAY` | 显式 env | 容器 | 可覆盖网关地址（本项目适配层支持） |
| imports（密钥仓库文件） | `imports:` 引用 | 流水线/开发环境 | 需引用鉴权（allow_slugs/pull 权限） |
| 个人环境变量 | 个人设置 > 云原生开发 | **仅云原生开发环境** | `use_in_slugs` 白名单必填，防泄密 |
| 本地 Token（MiMo/GH/闲鱼 Cookie） | 本机环境变量 | 本机进程 | 不入云端，云端仅校验存在性 |

**如实说明的当前 CNB 开放限制**：
1. **没有"公网可连的常驻 NPC 容器"**；NPC 是一次性事件执行单元。
2. **云原生开发环境有强回收策略**，不适合跑 7×24 服务。
3. **NPC 事件 CNB_TOKEN 权限收窄**（仅当前仓库），跨仓库操作需拆到各仓库各自的 NPC 事件或使用仓库内允许的 imports。
4. **端口映射需服务监听 0.0.0.0**，本项目适配层默认 `127.0.0.1:8787`，在云原生开发环境里需要改绑 `0.0.0.0` 才能走 WebIDE 端口映射。
5. **密钥注入仅限受信仓库/白名单**，量化等敏感仓不应放云端密钥。

### 2.3 ③ 能否基于路径B 自定义 Docker 镜像，把 Hermes Studio 打包进 CNB 容器，实现云端算力、本地可视化操作？

**结论：可行，但要分两个容器形态实现，且"本地可视化"有取舍：**

#### 形态一：NPC 执行容器（路径B，已有 80%）
- 已打包：原生 Hermes CLI（`hermes-agent`）、Codex CLI、Claude-Code CLI + 8787 适配层 + 额度监控。
- 局限：**无 GUI**，只能被 `@hermes` 触发跑任务，不能提供"桌面可视化"。

#### 形态二：云原生开发环境容器（WebIDE/VS Code/Cursor 承载）
- 在 `.cnb.yml` 配置 `vscode` 事件 + 自定义镜像（`.ide/Dockerfile` 或 `docker.image`），把 Hermes Studio 的 **Web GUI（`hermes gui --port`）** 装进开发环境容器，用 WebIDE 端口映射访问。
- "本地可视化"体验：浏览器打开云 GUI（延迟取决于网络）；或用 VS Code/Cursor Remote-SSH 连入，本地看到远端工作区。
- **代价（如实说明）**：
  - 端口映射要求服务监听 `0.0.0.0`，且 URL 形如 `https://{id}-{port}.cnb.run`（长随机子域）；
  - 环境回收机制（10min 闲置回收/18h 上限/凌晨强制回收）会**中断长会话**；
  - 云端运行 Hermes Studio 与本地 `AppData/Local/hermes/state.db` 会话**不共享**，需通过 git 同步产物；
  - 本地桌面端体验优于云端 GUI（TUI 响应、剪贴板、拖拽均依赖本地）。

#### 推荐组合（"云端算力 + 本地可视化"的最优解）
```
本地 Hermes Studio 桌面端（可视化编排入口）
   │  模型端点
   ▼
CNB 内置 AI 网关（deepseek-v4-flash 免费算力）← ACC_PRODUCT_CONFIG_V2 / 个人 Token
   │
   ▼
云原生开发容器（可选）：WebIDE 看板/端口映射跑轻量 Web 服务
   │
   ▼
CNB NPC 事件容器（路径B）：@hermes/@codex/@claude-code 执行重活 → PR 闭环
```
即：**模型算力上云（免费）、编排入口留本地（Hermes Studio）、重活执行上云（NPC 容器）、可视化兜底（云原生开发 WebIDE）**。

---

## 三、群组协同能力核验

### 3.1 ① Hermes Studio 内置 Agent 群聊模式 vs 旧方案飞书机器人

| 维度 | Hermes Studio Agent 群聊 | 飞书机器人（旧方案/企业侧） |
|------|--------------------------|------------------------------|
| 运行位置 | 本地进程（离线可用） | 云端 webhook 服务（需外网+回调） |
| 实时性 | 本地毫秒级（无网络 RTT） | 受 webhook 延迟+飞书 API 限流影响 |
| 多 Agent 协作 | 原生：同项目内多 Agent 群聊、任务分派、进度跟踪、上下文共享 | 弱：单机器人单会话，多 Agent 需自建路由（本项目 msgbus 承接） |
| 调试能力 | 本地日志 + TUI 全量输出 | 回调调试困难（签名/重放/超时） |
| 会话持久化 | `state.db` 本地库 + 对话导出 | 飞书云端会话（需翻墙/合规注意） |
| 触达能力 | 无对外触达（仅本地） | ✅ **对外触达**：客户群通知、交付提醒、报价推送 |
| 鉴权/安全 | 本地 Token，无外部暴露面 | 需 webhook 密钥；易被刷/被注入 |
| 适用 | **内部编排**：商单拆解、物料制作、审核接力 | **对外交付**：客户确认、结果通知、结算提醒 |

**结论**：**不是二选一，是两段**。Hermes Studio 群聊做"内部舰队编排"（替代/增强现有 msgbus 手工窗口），飞书/企业微信机器人做"对外交付触达"（保留现有 `wework_group_listener.py` 群监听 + 交付打包）。建议：Hermes Studio 群聊 → 产出交付物 → 企业微信机器人/飞书机器人通知客户。

### 3.2 ② 原生群聊 + Git Worktree 双模式是否可直接对接 orca 系列 6 个仓库？

**6 仓盘点（已核实仓库存在）**：

| 仓库 | 赛道 | 云端/本机边界 |
|------|------|--------------|
| `orca-jiedan` | 企业微信接单 | 云端 NPC 主战场（当前仓库），可全程云端 |
| `orca-wangpan` | 网盘萃取 | 可云端解析脚本；**网盘 Cookie 本机** |
| `orca-xianyu` | 闲鱼自动化 | **本机强约束**：Cookie/DPAPI/风控，严禁云端 |
| `orca-quant-jiasheng` | 量化·嘉盛 | **本机强约束**：交易凭证/API 密钥 |
| `orca-quant-binance` | 量化·币安 | **本机强约束**：BINANCE_API_KEY/SECRET |
| `orca` | 主空仓/调度中枢 | 可云端，但涉及密钥注入需白名单 |

**对接可行性**：
- ✅ **Git Worktree 模式天然适配**：6 仓统一脚手架（`scripts/sync_scaffold_to_all.sh` 列表已含 8 个本地项目，CNB 侧 6 仓路径已核实），Hermes Studio 打开任一仓库即可加工作树，分支隔离逻辑与现有 `worktrees/{hermes,codex,claude}` 完全一致。
- ✅ **群聊模式适配**：Hermes Studio 群聊内可同时挂 6 仓任务卡，任务分发到对应仓库的 Agent 工作树。
- ⚠️ **量化/闲鱼两仓的"云端访问"受限**：CNB NPC 事件 `CNB_TOKEN` 仅限当前仓库，跨仓 Fork PR 仅限公开仓；**交易/闲鱼凭证不应进云端**。建议：量化/闲鱼业务**只本机执行**，云端只做"脚本审核+PR 合并+文档沉淀"。

**一键落地动作**（本报告已核验，可直接执行）：
```bash
# 本地批量拉 6 仓（脚本已存在：docs/ORCA舰队运维接入总说明书V1.0.md 模块2）
REPOS=(orca-jiedan orca-wangpan orca-xianyu orca-quant-jiasheng orca-quant-binance orca)
for r in "${REPOS[@]}"; do
  git clone "https://cnb.cool/TJF19770107/${r}.git" && cd "$r" \
    && [ -f scripts/创建目录结构.sh ] && bash scripts/创建目录结构.sh && cd ..
done
```

### 3.3 ③ 多 Agent 并行开发自动隔离分支、一键 PR 流水线是否兼容现有脚手架 `apply_scaffold.sh`？

**如实说明：仓库中不存在名为 `apply_scaffold.sh` 的脚本。** 现有脚手架治理机制实际是：

| 实际脚本 | 职责 |
|----------|------|
| `scripts/orca_scaffold_check.sh` | 版本治理：比对 `scaffold_version`，一致即静默通过；不一致强制交互确认（Y 增量迭代 / N 版本分叉） |
| `scripts/upgrade_incremental.sh` | 增量迭代：只新增缺失文件、**绝不覆盖已存在文件**；保护 `.env database conversations skills logs outputs backups scaffold_version` |
| `scripts/sync_scaffold_to_all.sh` | 脚手架同步：把模板通用部分同步到全部 Orca 项目 |

**兼容性核验**：

| Hermes Studio 能力 | 与现有脚手架兼容性 | 说明 |
|--------------------|--------------------|------|
| 多 Agent 并行 + 分支自动隔离 | ✅ 兼容 | Hermes Studio 的 Worktree 与现有 `worktrees/` 分支模型同构；云端 NPC 舰队已用独立容器+独立分支（PR 源分支）实现自动隔离 |
| 一键 PR 流水线 | ✅ 兼容 | 现有 `.ci/{npc-full,hermes,codex}.yml` 已是"触发即执行、执行即 PR/评论闭环"；Hermes Studio 侧 `git push` → CNB `main.push` 镜像构建流水线自动触发 |
| 脚手架版本治理 | ⚠️ 需对齐 | Hermes Studio 引入的新文件应纳入 `scaffold_version` 治理；升级用 `upgrade_incremental.sh`（**非破坏**），不要手动覆盖 |
| 保护目录 | ✅ 兼容 | `.env` 等受保护目录不会被云端 NPC 触碰（镜像内也无密钥） |

**结论**：多 Agent 并行+一键 PR 流水线**与现有脚手架兼容**；`apply_scaffold.sh` 不存在，实际请用 `orca_scaffold_check.sh`（校验）+ `upgrade_incremental.sh`（增量），并把 Hermes Studio 相关文件增量并入脚手架模板 `templates/cnb_npc_path_b_scaffold/`。

---

## 四、风险前置排查

### 4.1 ① 本地桌面端连云端容器的四类风险

| 风险类别 | 具体问题 | 规避方案 |
|----------|----------|----------|
| **端口冲突** | ① 本地 Hermes GUI 15800 与 Codex++/Fleet GUI 端口重叠；② 57365-57367 落在 Windows 动态端口保留区（49152-65535）→ `WinError 10013`；③ 云端端口映射要求 `0.0.0.0`，适配层默认 `127.0.0.1` 不生效 | 端口全表（附录 A）先查后启；GUI 端口迁到 <49152（15800-15802 已实测）；云端服务显式绑 `0.0.0.0`；本地 57361-57368 预留段与云端互不共享 |
| **鉴权报错** | ① `wire_api`/`base_url` 被改 → 401（Codex 历史坑）；② CNB Token 过期 → 网关 401；③ NPC 事件 Token 仅限当前仓库 → 跨仓 403 | 遵守"禁止修改 ~/.codex/config.toml 的 wire_api/base_url"铁律；Token 用个人访问令牌注入 Hermes `.env`；跨仓操作按仓库拆分 NPC 事件；云端 Token 一律 `imports`/个人环境变量注入，**不进仓库** |
| **模型转发延迟** | 本地→CNB 网关的 RTT（公网），流式推理首 token 延迟 + 每条消息 ~0.5-2s 不等；本地 MiMo 走 15721 代理也有转发但本地 RTT 低 | 文本重活走云端免费基座（延迟可接受）；**交互式群聊**建议本地模型（Ollama/MiMo 8/14 前）；量化实时告警必须本机低延迟链路；启用 `REASONING_EFFORT` 降档控制成本 |
| **文件同步** | ① 云端容器/工作区有 100MB 备份上限（`file-keeper.md`）；② NPC 容器一次性、产物需 git push 才能回本地；③ 云原生开发环境销毁自动备份可能覆盖未提交代码 | 大文件一律 `.gitignore`；云端产物统一 git push → 本地 pull（`fleet_pull.sh`）；敏感文件（.env/密钥/会话 DB）不落云端；工作树修改及时 commit+push，避免依赖环境自动备份 |

### 4.2 ② 原有 MIMO-V2.5 调度代码彻底移除后的兼容风险

**现状盘点（已 grep 核实）**：`mimo-v2.5-pro` 硬编码出现在：`config/model_config.yaml`、`scripts/one_click_mimo_v25.sh`、`scripts/fleet_start_mimo.bat`、`scripts/fleet_restore.sh`、`scripts/fleet_auto_restore.cmd`、`scripts/pipeline_ab_video_test.py`、`scripts/workbody_fleet_check.py`、`scripts/一键拉起_Ollama本地DeepSeekV4Flash.bat`、以及本地代理脚本（15721/15730）与快照目录。

**直接移除的连锁风险（按影响面排序）**：

| # | 风险 | 影响 | 规避 |
|---|------|------|------|
| 1 | **三引擎同时哑火**：Claude 走 15721、Codex 走 15730、Hermes 走 8642，全部上游 mimo-v2.5-pro；移除后无模型可用 | 接单/量化/闲鱼全停 | **先接 CNB 网关替代，再灰度，最后归档**——禁止一步删除 |
| 2 | **多模态能力回退**：MiMo 原生识图（K 线截图/海报图）无替代 | 量化看盘/海报审核降级 | 视觉路由 MCP（图片→本地 Ollama 多模态/MiMo 到期前）+ CNB 网关文本推理，分层兜底 |
| 3 | **降级链断裂**：`model_config.yaml` 降级链 `mimo→openai→mock` 移除 mimo 后 openai 无 base_url | 知识萃取摘要失效 | 把 CNB 网关注册为 openai 兼容 provider（base_url 填网关），降级链改 `cnb→ollama→mock` |
| 4 | **启动脚本引用失效**：`fleet_start_mimo.bat`/`one_click_mimo_v25.sh` 若被计划任务/守护引用，删除报错 | 舰队自动恢复失败 | 保留脚本但改为"CNB 网关模式"入口（改上游 UPSTREAM 一行），或重命名归档 |
| 5 | **快照回滚失效**：`snapshots/` 内代理脚本硬编码 mimo，回滚会拉回旧链路 | 故障回滚变慢 | 快照迁移为"CNB 网关+本地兜底"双链路版本后再归档旧快照 |
| 6 | **量化/闲鱼依赖本机模型**：`quant_scheduler.py`/`auto_xianyu_scheduler.py` 的模型调用若指向 mimo | 巡检/回复中断 | 业务脚本统一读 `config/model_config.yaml`（改一处全生效），不直接写模型名 |

**推荐迁移顺序（龙虾五步法 Step3 无命令不执行 + 灰度）**：
```
Phase 0（本报告）：CNB 网关=唯一云端免费基座，全部新代码引用 config/model_config.yaml
Phase 1：本地代理上游改 CNB 网关（15721/15730 只改 UPSTREAM，一行）
Phase 2：灰度验证 3 天（接单/量化/闲鱼链路全绿）
Phase 3：mimo 相关脚本标记 deprecated（保留可回滚），快照双链路化
Phase 4：VERSION.md 升级 + SelfLearn_Record.md 沉淀 + 脚手架同步
```

---

## 五、输出交付物汇总

### 5.1 三者架构差异完整表格
见第一节（8 维度 × 3 系统差异表）。

### 5.2 云端 ↔ 本地桥接两种方案优劣对比

| 维度 | 方案 A：纯云端容器运行（NPC 路径B + 云原生开发） | 方案 B：本地桌面连云端算力（Hermes Studio 桌面端 + CNB 网关） |
|------|-----------------------------------------------|--------------------------------------------------------------|
| 形态 | 全部在 CNB：Issue/PR @NPC 触发容器执行；云原生 WebIDE 可视化 | 本地 Hermes Studio 桌面端 + 模型端点指向 CNB AI 网关 |
| 本地资源占用 | 零（浏览器除外） | 需本机进程（Hermes/代理/GUI） |
| 可视化 | 云 WebIDE/VS Code Remote（延迟受网络） | ✅ 原生桌面 TUI/Web GUI（低延迟、剪贴板/拖拽友好） |
| 算力 | ✅ CNB 免费 1600 核时/月 | ✅ 同样用 CNB 免费基座 |
| 会话持久化 | 云环境有回收机制（18h/凌晨回收），长会话易断 | ✅ 本地 state.db，永续 |
| 密钥安全 | 云端 Token 需白名单/imports，量化仓不宜 | ✅ 本地 Token 零外泄，量化/闲鱼链路安全 |
| 多 Agent 群聊 | 群聊在云端（Issue 评论式） | ✅ 原生群聊（实时、可调试） |
| 大文件/重资产 | ⚠️ 100MB 备份上限，Docker 构建吃核时 | ✅ 本地磁盘/G 盘，无限制 |
| 适用 | 云端交付、跨仓协作、脚本审核、免费算力跑重活 | 日常接单编排、量化/闲鱼本机业务、多 Agent 群聊 |
| 综合推荐 | 作为 B 的**补充执行通道** | **主通道（推荐起步）** |

> **结论**：方案 B 为日常主通道（本地编排 + 云端免费算力），方案 A 为云端交付/重活执行通道。两者通过 git push / PR 汇合，不互斥。

### 5.3 端口、容器、镜像适配详细说明

#### 端口适配表（新增/调整建议）
| 服务 | 当前 | 建议 | 依据 |
|------|------|------|------|
| Hermes Studio Web GUI | 15800（已常驻） | 保留 15800 | 实测可用，<49152 避开保留区 |
| Hermes Gateway | 8642 | 保留 | 本地模型网关 |
| CNB 网关（云端） | `https://api.cnb.cool/{slug}/-/ai/chat/completions` | 新增为 Hermes provider | OpenAI 兼容端点（适配层已验证） |
| 云原生开发端口映射 | 无 | 需 `0.0.0.0` 监听 + `https://{id}-{port}.cnb.run` | `business-preview.md` |
| NPC 容器 8787 | 127.0.0.1（容器内） | 保持容器内 | 平台不暴露 NPC 容器端口 |
| 57365-57367 GUI | 保留区 | 迁移 15800-15802 | `WinError 10013` 历史坑（registry.json 已记录） |

#### 容器适配说明
- **NPC 一次性容器**：路径B 已成型（`adapters/Dockerfile` + `.ci/*.yml`），镜像 `orca-jiedan:1.6.0` 拉取/构建已验证。如需新增"Studio 完整桌面"能力 → 走云原生开发容器（`.cnb.yml` `vscode` 事件 + `.ide/Dockerfile`），两者分离，不混用。
- **云原生开发容器**：预装 openssh-server + code-server 即可单容器模式；Web GUI 服务需绑 `0.0.0.0` 才能端口映射。

#### 镜像适配说明
- 新增依赖（Hermes Studio 桌面相关）：在 `adapters/Dockerfile` 追加 `RUN`（如 hermes gui 所需 web 依赖）；**保持"镜像零硬编码密钥"红线**。
- 构建/推送：`main.push` + `ifModify` 命中 Dockerfile 等文件时触发（现有流水线已配）；变量口径用 `CNB_REPO_SLUG_LOWERCASE`（NPC 事件下 `CNB_NPC_SLUG_LOWERCASE` 不注入——已在 1.6.0 修订）。
- 体积控制：1.60GB 镜像冷启动较慢（构建 354s），云原生开发环境建议拆分更轻的 dev 镜像。

### 5.4 落地前置风险清单与规避方案

| 优先级 | 风险 | 规避 |
|--------|------|------|
| P0 | 量化/闲鱼凭证上云 → 资金/风控风险 | 两仓业务**仅本机**执行；云端只做脚本审核/文档；密钥仓库 `use_in_slugs` 精确到信任仓 |
| P0 | MIMO 直接移除 → 三引擎哑火 | 按第四节 Phase 0-4 灰度迁移；保留回滚脚本 |
| P0 | 云原生开发环境回收 → 长任务中断 | 关键任务用 NPC 一次性容器（执行完即交付）；云 IDE 仅做短时可视化 |
| P1 | 端口冲突（保留区/多服务） | 附录 A 端口表先查后启；新增服务登记 registry.json |
| P1 | 云端文件同步丢未提交代码 | 工作树及时 commit+push；大文件 `.gitignore`；不依赖云备份 |
| P1 | 跨仓 NPC Token 受限 | 跨仓任务在目标仓库各自触发；Fork PR 仅公开仓 |
| P2 | Hermes Studio 与 msgbus 双总线并存混乱 | 定位：Studio=编排前端，msgbus=业务总线；Studio 读写 `fleet_exchange/` 不另建总线 |
| P2 | 脚手架分叉 | 新增文件走 `upgrade_incremental.sh`；版本号同步 `scaffold_version` |
| P2 | 中文编码/模型名兼容 | Hermes provider 用 `deepseek-v4-flash`；适配层负责模型名锁定；严禁改 `wire_api`/`base_url` 铁律 |

---

## 六、落地路线图（建议 Phase）

| Phase | 内容 | 验收标准 | 工作量 |
|-------|------|----------|--------|
| P0（本周） | 安装 Hermes-Setup.exe 桌面版；本地 provider 注册 CNB 网关 | 桌面端 `hermes model` 指向 CNB 网关，对话返回 deepseek-v4-flash | 0.5 天 |
| P1 | 代理上游切 CNB 网关（15721/15730 改 UPSTREAM）；`model_config.yaml` 注册 cnb provider | 三引擎均走免费基座，`milli_credit=0` | 0.5 天 |
| P2 | 6 仓批量拉取 + 脚手架增量同步；Hermes Studio 挂 6 仓 Worktree | 6 仓工作树可用，量化/闲鱼标记本机执行 | 1 天 |
| P3 | 云原生开发环境（`.ide/Dockerfile`）跑 Hermes Web GUI 验证 | WebIDE 端口映射可访问 Studio GUI | 1 天 |
| P4 | MIMO 脚本 deprecated + 快照双链路化 + VERSION.md 升级 + 知识库沉淀 | 回滚演练通过，全链路文档归档 | 0.5 天 |

---

## 附录 A：本地端口全表（先查后启）

| 端口 | 服务 | 备注 |
|------|------|------|
| 4567 | aicodeswitch（AI 模型路由） | 共享基础设施 |
| 15721 | Anthropic 代理（Claude Code） | 铁律：禁止改端口 |
| 15730 | Codex 工具代理 | 铁律：禁止改端口 |
| 8642 | Hermes Gateway | 本地模型网关 |
| 11434 | Ollama | 本地推理 |
| 5230 | Memos | 笔记服务 |
| 57320/57321 | CC-Switch / Orca IDE | GUI |
| 57330 | Claude Code Serve | API |
| 57361 | Hermes CLI（本项目） | 动态端口区，注意 |
| 57362 | Codex CLI（本项目） | 动态端口区，注意 |
| 57363 | Claude Chat（本项目） | 动态端口区，注意 |
| 57364 | msgbus 内部 | 动态端口区 |
| 57365-57367 | GUI 面板 | ⚠️ 曾 WinError 10013，迁 15800-15802 |
| 15800 | Hermes Fleet GUI | 已实测常驻 |
| 15801/15802 | Codex/Claude Fleet GUI（沙箱替代） | 已实测 |

## 附录 B：CNB 平台限制原文引用（docs.cnb.cool）

1. `build/npc.md`：NPC 事件 = Issue/PR 评论 @提及触发；一次最多触发 10 个 NPC 事件；评论 >100 条不再触发；`CNB_TOKEN` 仅限访问当前仓库；NPC 事件中最大角色=触发用户在仓库中的角色。
2. `build/internal-steps.md`：`npc:go` 在指定 Docker 镜像中执行 AI 任务，一次性执行单元。
3. `workspaces/business-preview.md`：服务需监听 `0.0.0.0` 才能 WebIDE 端口映射；`localhost/127.0.0.1` 不可用。
4. `workspaces/workspace-recycling.md`：10 分钟无操作回收；最大保持 18 小时；使用超 8 小时且凌晨 4-6 点强制回收。
5. `workspaces/file-keeper.md`：单文件/总备份 >100MB 不备份；工作区代码自动备份但每分支仅保留一份。
6. `build/build-in-env.md`：`CNB_TOKEN` 按可信/不可信事件分级；sandbox 模式下 `CNB_TOKEN` 无效。
7. `workspaces/personal-envs.md`：个人环境变量仅云原生开发环境生效；`use_in_slugs` 白名单必填。
8. `build/grammar.md`：`sandbox:true` 时 `CNB_TOKEN` 无效；`imports` 引用需鉴权。
9. `build/trigger-rule.md`：不可信事件（含 `pull_request.comment@npc`、`issue.comment@npc`）的 `CNB_TOKEN` 权限受限。

---

*本报告由 CodeBuddy 在 CNB 云端容器生成，全程使用 CNB 内置免费 DeepSeek-V4-Flash 基座，未调用外部付费 API。*
*建议归档：Obsidian 知识库 + `docs/` + 脚手架模板 `templates/cnb_npc_path_b_scaffold/docs/`。*
