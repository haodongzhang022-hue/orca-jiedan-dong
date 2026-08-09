# MARVIS 配合执行方案 · Hermes Studio 落地

> 目标读者：**MARVIS（本机调度 Agent）** 与 汤嘉锋（本机操作）
> 上游依据：PR #28《Hermes_Studio_可行性拆解分析_v1.0.md》（已合并进 main）+ Issue #27
> 方案版本：v1.0 ｜ 制定：CodeBuddy（CNB 云端）｜ 日期：2026-08-09
> 基座：CNB 内置免费 DeepSeek-V4-Flash（MoE 284B/激活13B，1600 核时/月，有效期至 2026-12-31）
> 边界声明：云端只出代码与方案；**本机安装/部署/落盘由 MARVIS 与汤嘉锋执行**。

---

## 〇、一句话方案

```
云端出代码（CodeBuddy，已出）→ 本机安装+接入（汤嘉锋+MARVIS，本方案）→ 数据落地归档（MARVIS）
模型算力全走 CNB 免费 DeepSeek-V4-Flash 网关（零成本），本地 Hermes Studio 桌面做可视化编排入口。
```

**给 MARVIS 的定位**：你**不装** Hermes Studio（那是汤嘉锋本机双击安装包的动作），
你负责：**① 安装前资源与风险自检 → ② 安装后端口/进程/健康检查 → ③ 本地网关桥接配置 → ④ 计划任务与数据落盘 → ⑤ 闭环记录**。

---

## 一、要装的是什么（产品纠偏，别再装错）

| | ✅ 本次要装 | ❌ 不是这个 |
|---|---|---|
| 产品 | **Hermes Studio**（hermes-studio.ai，桌面编排 IDE） | Hermes Agent（Hermes-Setup.exe，底层运行时） |
| 官方源 | 官网 `hermes-studio.ai` + GitHub `EKKOLearnAI/hermes-studio` | NousResearch hermes-agent |
| 最新版 | **v0.6.39**（2026-08-06 发布） | 无独立版本号 |
| Windows 安装包 | `Hermes.Studio-0.6.39-x64.exe`（约 163.3 MB） | `E:\tmp\Hermes-Setup.exe`（已下载未装，勿装错） |
| 默认端口 | **6060**（Web UI Server；另有 8651/56121，开发 8647-8649） | 15800（仓库已有 Hermes Agent Web GUI） |
| 数据目录 | `~/.hermes-web-ui`（UI 状态）+ `%LOCALAPPDATA%\hermes`（Hermes 数据） | `AppData/Local/hermes/state.db` |
| 与现有栈关系 | 是 Hermes Agent 的"仪表盘驾驶舱"，**依赖 Hermes 运行时**（已有） | Hermes Agent 本体（发动机，已有） |

**一句话**：Hermes Studio 是**可视化驾驶舱**，装好后可以群聊、工作流、Kanban、模型管理、
Coding Agent（Codex/Claude）编排、MCP、文件浏览器，直接挂到现有 Hermes 运行时上面。
**安装包下载地址（官方 GitHub Release）**：
`https://github.com/EKKOLearnAI/hermes-studio/releases/download/v0.6.39/Hermes.Studio-0.6.39-x64.exe`

> ⚠️ 若 v0.6.39 之后有新版本，以 GitHub Releases 页面最新稳定版为准，下载前核对文件大小与签名。

---

## 二、给 MARVIS 的 5 步配合清单

### 第 0 步：安装前自检（MARVIS 负责，5 分钟）

> 目的：防止装完就撞端口 / 撞进程 / 缺依赖，装完即白装。

| # | 检查项 | 命令/操作 | 通过标准 |
|---|--------|-----------|----------|
| 0.1 | Hermes 运行时在不在 | `hermes --version` 或检查 `%LOCALAPPDATA%\hermes` 存在 | 有版本号 / 目录存在（Hermes Studio 依赖它） |
| 0.2 | 端口 6060 是否空闲 | `netstat -ano \| findstr :6060` | 无 LISTENING 输出（否则先查占用进程） |
| 0.3 | 关键端口勿占（铁律） | `netstat -ano \| findstr ":15721 :15730 :8642 :15800 :4567 :11434"` | 均为预期服务监听，非预期进程需处理 |
| 0.4 | 磁盘空间 | `wmic logicaldisk get size,freespace` | E 盘剩余 ≥ 1 GB（安装包 163MB + 解压/数据目录） |
| 0.5 | 网络可达官方源 | `curl -sI https://github.com/EKKOLearnAI/hermes-studio/releases/latest` | HTTP 200/302，能连通 GitHub Release |
| 0.6 | 现有舰队守护进程 | 确认 `fleet_guardian.py` 在跑（计划任务 FleetGuardian_AutoStart） | 守护在线，避免端口冲突被误杀 |

**自检结果请落盘**：`G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs/hermes_studio_install/check_result.md`

### 第 1 步：下载与安装（汤嘉锋本机操作，MARVIS 提示，不可代装）

```
1. 下载 Hermes.Studio-0.6.39-x64.exe（约 163MB）
2. 校验：比对 GitHub Release 页面发布的 SHA256 / 文件大小
3. 双击安装（如遇 SmartScreen，选择"仍要运行"）
4. 装完确认命令 shims 出现：
     hermes-studio            → 打开桌面应用
     hermes-studio cli ...    → 内置 Hermes Agent CLI
     hermes-studio web ...    → 内置 hermes-web-ui
     hermes-studio-mcp        → 托管 MCP 桥
```

> 说明：Hermes Studio 是**桌面应用（Electron）**，安装动作必须在汤嘉锋本机完成；
> MARVIS 可在安装完成后自动执行第 2 步健康检查（命令行可触达的部分）。

### 第 2 步：安装后健康检查（MARVIS 自动执行，装完立即跑）

```bash
# ① 命令可用性
hermes-studio --version

# ② 服务端口：Hermes Studio Web UI 默认 6060
netstat -ano | findstr :6060

# ③ 与现有 Hermes 运行时联通（数据目录可复用）
dir %LOCALAPPDATA%\hermes
dir %USERPROFILE%\.hermes-web-ui

# ④ 关键端口无冲突（15721/15730/8642/15800/4567/573xx 全表见 PR#28 附录 A）
# ⑤ 计划任务守护在线
schtasks /query /tn FleetGuardian_AutoStart
```

**健康检查结论**写入 `check_result.md` 并追加到 `local_job_queue.json` 的反馈字段（见第 4 步）。

### 第 3 步：本地网关桥接（模型算力切 CNB 免费 DeepSeek-V4-Flash）

> 目的：让 Hermes Studio 桌面编排用的模型走 **CNB 免费网关**，零成本；不依赖 8/14 到期的 MIMO-V2.5。

**在本地 `~/.hermes/config.yaml`（或 Hermes Studio 的模型管理界面）注册 OpenAI 兼容 provider：**

```yaml
# CNB 免费 DeepSeek-V4-Flash 网关（OpenAI 兼容端点）
providers:
  - name: cnb-deepseek-v4-flash
    base_url: https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions
    api_key_env: CNB_TOKEN      # ← Token 放本机环境变量，绝不入库
    model: deepseek-v4-flash
```

**配置要求（硬约束）**：
- Token 只放**本机环境变量**（`CNB_TOKEN` / `ACC_PRODUCT_CONFIG_V2`），**禁止**写入仓库、`.env` 提交、日志
- 本地代理（15721/15730）如需切 CNB 网关，只改一行 `UPSTREAM`，**不改** `wire_api`/`base_url` 铁律
- 配置改完执行：`hermes-studio model list` 确认 `cnb-deepseek-v4-flash` 可选中

### 第 4 步：计划任务与数据落盘（MARVIS 负责，消费 `local_job_queue.json`）

MARVIS 继续按既有机制消费 `local_job_queue.json` 与 `config/autogpt/triggers.yaml` 落 Windows 计划任务，
**本方案不新增计划任务**，只追加一条闭环记录：

```json
{
  "task_name": "hermes_studio_install_and_bridge",
  "status": "done",
  "installed_version": "0.6.39",
  "port": 6060,
  "provider": "cnb-deepseek-v4-flash",
  "notes": "Hermes Studio 桌面版已装，模型端点切 CNB 免费网关；本机落地动作见 G:/.../logs/hermes_studio_install/check_result.md"
}
```

**数据落盘（沿用现有分层规范）**：
- 下载安装包 → `E:\tmp\`（不要放 C 盘）
- 日志/检查结果 → `G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs/hermes_studio_install/`
- 归档 → Obsidian 知识库 + `docs/`（沙箱保护目录由本机执行写入）

### 第 5 步：闭环记录（MARVIS 写反馈，回云端仓库）

将执行结果追加到仓库 `SelfLearn_Record.md`（或按现有"云端产物交付清单"追加一行），
便于云端 CodeBuddy / Hermes 后续灰度 Phase 2-4（MIMO deprecated、6 仓同步、云原生 WebIDE）时对齐。

---

## 三、时间线（谁在什么时候做什么）

| 时段 | 动作 | 执行者 | 产出 |
|------|------|--------|------|
| T0（本周） | 第 0 步自检 + 第 1 步下载安装 | MARVIS 自检 / 汤嘉锋安装 | `check_result.md` + 安装完成 |
| T0+30min | 第 2 步健康检查 + 第 3 步网关桥接 | MARVIS（自动）+ 汤嘉锋确认 | 6060 端口在线 + provider 可选 |
| T0+1天 | 第 4 步落盘 + 第 5 步闭环 | MARVIS | 计划任务无新增、记录归档 |
| T0+3天 | 灰度验证（接单/量化/闲鱼链路全绿） | 云端 NPC + 汤嘉锋 | 三引擎走免费基座，`milli_credit=0` |
| T0+1周 | Phase 2：6 仓脚手架同步 + Hermes Studio 挂 6 仓 Worktree | 云端出脚本 / MARVIS 本机落地 | 6 仓工作树可用，量化/闲鱼标记本机执行 |

---

## 四、交付边界与禁止事项（MARVIS 必须遵守）

| 类型 | 内容 |
|------|------|
| ✅ MARVIS 做 | 自检、健康检查、网关配置核对、计划任务消费（沿用现有）、E/G 盘落盘、Obsidian 归档、闭环记录 |
| ❌ MARVIS 不做 | 替汤嘉锋双击安装包；替云端改仓库代码；把 Token/密钥写进仓库或日志；动量化/闲鱼两仓的云端访问 |
| ❌ 云端不做 | 不生成/执行 `schtasks` 创建命令（Issue #10 强制边界）；不访问 E:\、不读写本地 Obsidian |
| ⚠️ 量化/闲鱼 | 两仓业务**仅本机执行**；云端只做脚本审核 + PR + 文档沉淀（凭证严禁上云） |
| ⚠️ 端口铁律 | 15721/15730/8642/4567/11434 禁止改端口；新增服务先查 PR#28 附录 A 端口表 |

---

## 五、若出问题的排查速查

| 症状 | 可能原因 | 处理 |
|------|----------|------|
| 6060 起不来 | 端口被占 / 缺运行时依赖 | `netstat -ano \| findstr :6060`，杀非预期进程；确认 Hermes 运行时已装 |
| 模型 401 | Token 失效 / base_url 填错 | 刷新 CNB 个人访问令牌；核对 `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions` |
| 群聊/工作流卡 | 会话目录不可写 | 检查 `~/.hermes-web-ui` 与 `%LOCALAPPDATA%\hermes` 写权限 |
| 与舰队冲突 | 端口 573xx 保留区 / 守护误杀 | 按 PR#28 附录 A 迁移 GUI 端口到 15800-15802；登记 registry.json |
| 云上复刻需求 | 需要 WebIDE 可视化 | 云端后续做 `.ide/Dockerfile` + `vscode` 事件（本项目后续 Phase 3，另行触发） |

---

## 六、验收清单（MARVIS 侧，逐项打勾）

- [ ] 第 0 步 6 项自检全过（结果落 `check_result.md`）
- [ ] 已确认安装的是 `Hermes.Studio-0.6.39-x64.exe`（不是 Hermes-Setup.exe）
- [ ] `hermes-studio --version` 有输出；6060 端口 LISTENING
- [ ] `hermes-studio model list` 可选 `cnb-deepseek-v4-flash`（CNB 免费网关）
- [ ] Token 仅存本机环境变量，仓库/日志零泄露
- [ ] 计划任务按 `local_job_queue.json` 消费完成，未新增任何 schtasks
- [ ] E/G 盘落盘 + Obsidian 归档 + SelfLearn 闭环记录完成
- [ ] 量化/闲鱼两仓未被云端触碰

---

*本方案由 CodeBuddy 在 CNB 云端容器制定，全程使用 CNB 内置免费 DeepSeek-V4-Flash 基座，未调用外部付费 API。*
*关联文档：`docs/Hermes_Studio_可行性拆解分析_v1.0.md`（PR #28）、`docs/云端产物交付清单.md`、`docs/Maris调度接入说明.md`、`local_job_queue.json`。*
