# MARVIS 全自动落地方案 · Hermes Studio 全链路 v2.0

> 版本：v2.0 ｜ 制定：CodeBuddy（CNB 云端）｜ 日期：2026-08-09
> 升级自 v1.0（PR #29）：**用户零操作，全权授权 MARVIS 自动完成安装 → 桥接 → 云上复刻 → 群聊痕迹墙 → 技能一键接入**。
> 上游依据：PR #28《Hermes_Studio_可行性拆解分析_v1.0.md》、PR #29 v1.0 方案、Issue #27 用户 4 点需求。
> 基座：CNB 内置免费 DeepSeek-V4-Flash（OpenAI Chat Completions 兼容网关，免费至 2026-12-31）。

---

## 〇、一句话方案（v2.0 相比 v1.0 的变化）

```
v1.0：云端出代码 → 汤嘉锋双击安装 → MARVIS 自检/健康检查/落盘
v2.0：云端出代码 + 出安装器 → MARVIS【全权自动】下载/静默安装/桥接/云上复刻/痕迹墙/技能，汤嘉锋零操作
      模型算力全走 CNB 免费 DeepSeek-V4-Flash 网关（0 成本）
```

| 对比项 | v1.0 | v2.0 |
|--------|------|------|
| 安装动作 | 汤嘉锋本机双击 `.exe` | **MARVIS 静默安装**（命令行 `--silent` 全自动） |
| 授权方式 | MARVIS 只做检查 | **全权授权**（明确动作清单 + 静默参数 + 回滚点） |
| 云上复刻 | 仅列 Phase 3 待办 | **本次一并交付** `.ide/Dockerfile` + `vscode` 事件 |
| 云端看群聊 | 不可见 | **本次交付** 群聊痕迹墙（Hermes Studio ↔ 云端 NPC 互见） |
| 一键技能 | 无 | **本次交付** `hermes-studio-cnb` 技能 + 一键接入脚本 |

**一句话**：你这次什么都不用点，MARVIS 全自动装好 → 我这边云端把 Web GUI、群聊可见、一键技能全部落地，两边通过 git 接力。

---

## 一、要装的是什么（产品确认，避免再装错）

| | ✅ 要装 | ❌ 不要装 |
|---|---|---|
| 产品 | **Hermes Studio 桌面版**（hermes-studio.ai，Electron 桌面应用） | Hermes Agent 本体（Hermes-Setup.exe，已是底层运行时） |
| 官方源 | GitHub `EKKOLearnAI/hermes-studio` Release | NousResearch hermes-agent |
| 版本 | **v0.6.39**（2026-08-06 发布，已核验 GitHub Releases API） | 无版本号 |
| Windows 安装包 | `Hermes.Studio-0.6.39-x64.exe`（**171,264,040 字节 ≈ 163.3 MB**） | `E:\tmp\Hermes-Setup.exe`（勿再误装） |
| 默认端口 | **6060**（Web UI Server；另有 8651/56121，开发 8647-8649） | 15800（Hermes Agent Web GUI） |
| 数据目录 | `~/.hermes-web-ui` + `%LOCALAPPDATA%\hermes`（复用现有 Hermes 数据） | 独立目录 |
| 桌面命令 shims | `hermes-studio` / `hermes-studio cli` / `hermes-studio web` / `hermes-studio-mcp` | 无 |
| 云上复刻原料 | 官方 Dockerfile + docker-compose（`EXPOSE 6060`，`BIND_HOST=0.0.0.0`，镜像约 1.57GB） | — |

> ⚠️ 安装前核对 SHA256（GitHub Release 发布 `Hermes.Studio-0.6.39-x64.exe.sha256` 在 releases 元数据内），防止供应链篡改。

---

## 二、MARVIS 全自动执行清单（全权授权 · 6 步全自动）

> **授权范围**：本方案视为汤嘉锋对 MARVIS 的**全权委托**。MARVIS 可自动执行下载、校验、静默安装、
> 桥接配置、健康检查、数据落盘、闭环回写；**唯一例外**：不触碰 Token 明文（只写本机环境变量）、
> 不改云端代码、不新增 schtasks 命令（沿用现有消费机制）。

### 第 1 步：自动下载 + SHA256 校验（MARVIS）

```powershell
# 下载目录：E:\tmp\（按 E盘/G盘 分层规范，不落 C 盘）
$url  = "https://github.com/EKKOLearnAI/hermes-studio/releases/download/v0.6.39/Hermes.Studio-0.6.39-x64.exe"
$sha  = "从 GitHub Release 元数据读取（安装前自动核对，异常即中止）"
$out  = "E:\tmp\Hermes.Studio-0.6.39-x64.exe"
Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
$hash = (Get-FileHash $out -Algorithm SHA256).Hash
if ($hash -ne $sha) { throw "SHA256 校验失败，中止安装" }
```

**通过标准**：文件存在 + 163.3MB ±1MB + SHA256 匹配。

### 第 2 步：静默安装（MARVIS，替代"汤嘉锋双击"）

```powershell
Start-Process -FilePath $out -ArgumentList "--silent","/S" -Wait
# Electron 安装包（NSIS/Squirrel 类）静默参数以官方 latest.yml 说明为准；
# 若不支持 --silent，则降级 /S 或 使用安装器自带 silent 开关，二选一验证。

# 装后确认命令 shims
hermes-studio --version
hermes-studio cli --version        # 内置 Hermes Agent CLI
hermes-studio web --version        # 内置 hermes-web-ui
```

**通过标准**：`hermes-studio --version` 有输出；`hermes-studio web --version` 有输出。

### 第 3 步：健康检查 + 端口核验（MARVIS）

```powershell
# ① Web UI Server 默认 6060（web 模式需显式启动，桌面版首次启动自动拉起）
netstat -ano | findstr :6060
# ② 关键端口铁律无冲突
netstat -ano | findstr ":15721 :15730 :8642 :15800 :4567 :11434 :57321 :57362 :57368"
# ③ Hermes 数据目录可复用
Test-Path "$env:LOCALAPPDATA\hermes"
Test-Path "$env:USERPROFILE\.hermes-web-ui"
# ④ 守护进程在跑
schtasks /query /tn FleetGuardian_AutoStart
```

**通过标准**：6060 监听（或桌面应用已持有）；铁律端口均为预期服务；守护在线。

### 第 4 步：网关桥接（MARVIS，模型端点指 CNB 免费网关）

写 `~/.hermes/config.yaml`（Hermes Studio 模型管理界面同效）新增 OpenAI 兼容 provider：

```yaml
# CNB 免费 DeepSeek-V4-Flash 网关（OpenAI Chat Completions 兼容，本机已验证格式）
providers:
  - name: cnb-deepseek-v4-flash
    base_url: https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions
    api_key_env: CNB_TOKEN        # ← Token 只放本机环境变量，绝不入库/日志
    model: deepseek-v4-flash
```

**通过标准**：`hermes-studio model list` 可选 `cnb-deepseek-v4-flash`；一次 200 试调用成功。

### 第 5 步：数据落盘 + 计划任务消费（MARVIS）

- 安装包 → `E:\tmp\`
- 日志/检查结果 → `G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs/hermes_studio_install/`
- 闭环记录 → `local_job_queue.json` 追加（见第 6 步）+ Obsidian 归档 + SelfLearn_Record.md
- **不新增 schtasks**，沿用现有消费机制

### 第 6 步：闭环回写（MARVIS → 云端仓库）

```json
{
  "task_name": "hermes_studio_fullauto_v2",
  "status": "done",
  "installed_version": "0.6.39",
  "install_mode": "silent-fullauto",
  "port": 6060,
  "provider": "cnb-deepseek-v4-flash",
  "cloud_ide": ".ide/Dockerfile + vscode 事件已合并",
  "group_chat_wall": "docs/Hermes_Studio_群聊痕迹墙_接入说明.md",
  "skill": "skills/hermes-studio-cnb/SKILL.md",
  "notes": "汤嘉锋零操作，MARVIS 全自动闭环"
}
```

---

## 三、时间线（MARVIS 全自动，汤嘉锋零操作）

| 时段 | 动作 | 执行者 | 产出 |
|------|------|--------|------|
| T0（自动） | 下载+校验+静默安装 | MARVIS | 安装完成 + SHA256 报告 |
| T0+10min | 健康检查 + 网关桥接 | MARVIS | 6060 在线 + `cnb-deepseek-v4-flash` 可选 |
| T0+30min | 落盘 + 闭环回写 | MARVIS | `local_job_queue.json` 记录 + Obsidian |
| T0+1天 | 云端验证云上复刻 + 痕迹墙 + 技能 | 云端 NPC | 灰度三链路全绿 |
| T0+1周 | 6 仓 Worktree 挂载（量化/闲鱼仅本机） | MARVIS + 云端 | 6 仓工作树可用 |

---

## 四、与云端交付物的对接（本 PR 同步交付）

| 需求 | 云端交付物 | 对接方式 |
|------|-----------|----------|
| ② 云上复刻 | `.ide/Dockerfile` + `.cnb.yml` `vscode` 事件 | 点仓库「云原生开发」按钮，浏览器打开 Hermes Studio Web GUI（6060 端口映射） |
| ③ 云端看群聊 | `docs/Hermes_Studio_群聊痕迹墙_接入说明.md` + `scripts/cnb_echo_ping.py` | 云端 NPC 每轮 echo 一条痕迹，Hermes Studio 群聊 @ 可见；本机也可反向投递 |
| ④ 一键技能 | `skills/hermes-studio-cnb/SKILL.md` + `scripts/one_click_cnb_gateway.sh` | 本地一条命令把 Hermes Studio 模型端点切到 CNB 免费网关 |

---

## 五、硬边界（MARVIS 必须遵守）

- ✅ 做：下载/校验/静默安装/健康检查/网关桥接/落盘/闭环
- ❌ 不做：触碰 Token 明文入库；改云端代码；新增 schtasks；动量化/闲鱼两仓云端访问
- ⚠️ 量化/闲鱼两仓**仅本机执行**；15721/15730/8642/4567/11434 端口铁律禁改
- ⚠️ 若静默安装被 SmartScreen/杀软拦截：记录错误 → 写回 `local_job_queue.json` 标记 `need_human_click`，暂停（不进死循环）

---

## 六、验收清单（全自动闭环后逐项打勾）

- [ ] SHA256 校验通过，安装包在 `E:\tmp\`
- [ ] `hermes-studio --version` 有输出；6060 端口监听
- [ ] `cnb-deepseek-v4-flash` provider 可选且试调用 200
- [ ] Token 仅本机环境变量，仓库/日志零泄露
- [ ] 云端 `.ide/Dockerfile` + `vscode` 事件已合并（本 PR）
- [ ] 群聊痕迹墙脚本已入库（本 PR）
- [ ] `hermes-studio-cnb` 技能已注册（本 PR）
- [ ] `local_job_queue.json` 闭环记录已回写
- [ ] 汤嘉锋零手动操作

---

*本方案由 CodeBuddy 在 CNB 云端容器制定，全程使用 CNB 内置免费 DeepSeek-V4-Flash 基座，未调用外部付费 API。*
*关联文档：`docs/Hermes_Studio_可行性拆解分析_v1.0.md`、`docs/Hermes_Studio_群聊痕迹墙_接入说明.md`、`skills/hermes-studio-cnb/SKILL.md`。*
