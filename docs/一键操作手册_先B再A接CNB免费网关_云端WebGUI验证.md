# 一键操作手册 · 先 B 再 A 接 CNB 免费网关 + 云端 WebGUI 验证

> 归属：orca-jiedan 舰队 · CodeBuddy（B）出品
> 版本：v1.0 | 日期：2026-08-12 | 关联：Issue #27（Hermes Studio 落地 + 免费基座）
> 执行者：汤嘉锋 / MARVIS（本地 Windows 本机）
> 目标：**把本地 Hermes Studio 桌面版接上 CNB 免费 DeepSeek-V4-Flash 网关（0 成本），并验证云端 Web GUI（https://{id}-6060.cnb.run）可打开。**
> 状态：**两处验收项已由用户确认通过 ✅**（方式A config.yaml 已注册 ✅；云端 6060 能看到 Hermes Web UI ✅）。本文档把「先 B 再 A + 云端验证」固化成可重复的一键操作手册，供 MARVIS / 汤嘉锋按步骤执行并闭环记录。

---

## 〇、一句话结论

```
本地 Hermes Studio 桌面编排（可视化调度入口，在你 Windows 本机）
   └─模型端点指向→ CNB 免费网关 deepseek-v4-flash（免费算力，0 成本）
云端 WebGUI = 出差/兜底可视化（https://{id}-6060.cnb.run，有回收机制）
```

**执行顺序固定「先 B 再 A」**：
- **方式 B（手动，先做）**：在 Hermes Studio GUI 里手动建 Provider → 建立连接（这一步不建立，A 脚本写进去了 GUI 也选不生效）；
- **方式 A（脚本，兜底/自动）**：`switch_to_cnb_gateway.sh` 一键把 provider 固化进 `~/.hermes/config.yaml`（幂等、自动备份、不落 Token 明文）。

---

## 一、当前已确认状态（用户实测 ✅）

| 验收项 | 状态 | 证据 |
|---|---|---|
| 本地 Hermes Studio 桌面版 | ✅ 已装 | Windows 本机桌面编排主入口 |
| 方式 A 脚本 `switch_to_cnb_gateway.sh` 运行后 config.yaml 已注册 | ✅ | `--check-only` 显示 `✅ Hermes provider 'cnb-deepseek-v4-flash' 已注册` |
| 云端点「云原生开发」→ 浏览器打开 `https://{id}-6060.cnb.run` 能看到 Hermes Web UI | ✅ | 6060 端口映射可达，Hermes Web UI 正常显示 |

> 说明：`{id}` 是平台每次启动生成的随机小写字母（如 `fjisdofi21`），**必须**从 WebIDE 的 PORTS 面板复制真实地址，不能手打占位符（否则报「没有找到该 URL」）。

---

## 二、方式 B · 手动配置 Provider（先做，建立连接）

打开 Hermes Studio 桌面版 → **设置 → 模型管理 / Providers** → 添加 Provider，按表填：

| 字段 | 填什么 |
|---|---|
| **name** | `cnb-deepseek-v4-flash` |
| **base_url** | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions` |
| **api_key** | `%CNB_TOKEN%`（引用本机环境变量，不落盘） |
| **model** | `deepseek-v4-flash`（**不是 pro**，pro 会扣费） |
| Provider 类型 | 选 **DeepSeek 预设**（不要自定义） |
| API 模式 | 选 **chat_completions**（OpenAI 兼容） |

**填表避坑（全是踩过的）**：
- Base URL 末尾必须是 `completions`（**带 s**），写成 `completion`/`completiong` 会 404；
- 保存后**必须完全退出（含托盘）→ 重启**，再**新建会话**，右上角确认显示 `deepseek-v4-flash`（不是 `MiMo #NN`，否则仍烧 MiMo 积分）。

---

## 三、方式 A · 脚本一键固化（后做，兜底/自动）

在 Git Bash / WSL 里跑（幂等，只写 `api_key_env: CNB_TOKEN`，不写明文）：

```bash
# 1) 只读自检（确认现状，应显示 ✅）
bash scripts/switch_to_cnb_gateway.sh --check-only

# 2) 一键写入 provider 到 ~/.hermes/config.yaml（自动备份 *.bak.<时间戳>）
bash scripts/switch_to_cnb_gateway.sh

# 3) 亦可走原接入脚本（同效果）
bash scripts/one_click_cnb_gateway.sh
```

> 方式 A 只是让 GUI 下拉里**有得选**；最后「选它 + 保存 + 重启 + 新建会话」这步仍需在 GUI 完成。**这就是「先 B 后 A」的顺序原因**：B 建立连接，A 固化配置。

---

## 四、云端 Web GUI 验证（https://{id}-6060.cnb.run）

链路（已交付并实测）：

```
点仓库「云原生开发」按钮
   → 用 .ide/Dockerfile 构建（FROM ekkoye8888/hermes-web-ui:v0.6.39）
   → start.sh 拉起 ① CNB 免费网关适配层(127.0.0.1:8787) + ② Hermes Web UI(6060)
   → WebIDE PORTS 面板 → 复制真实地址 https://{id}-6060.cnb.run
   → 浏览器打开 → Hermes Studio 云端控制台（模型走免费 deepseek-v4-flash）
```

**若打不开（两个最常见的坑，已写进操作图 `docs/操作图_云上Hermes云端控制台打开.html`）**：

| 现象 | 原因 | 处理 |
|---|---|---|
| `undefined/-/workspace/err...` +「迷失在代码的海洋」 | 工作区被平台**回收**（10 分钟无操作 / 最长 18h / 凌晨 4-6 点强制回收），或点了失效链接 | 关掉 → 回仓库 → 切 main → 重新点「云原生开发」→ 从 PORTS 面板拿**新**地址（{id} 每次都会变，别存旧书签） |
| `connection refused` | 访问的是**旧工作区**（修复 PR #38 之前启动，没装 Hermes Web UI） | 个人主页 → 云原生开发环境列表 → 删除旧工作区 → 回仓库重新点「云原生开发」（见 `docs/云上Hermes6060_connection_refused排查记录.md`） |

---

## 五、验收清单（做完对照打勾）

- [ ] 方式 B 手动：Provider `cnb-deepseek-v4-flash` 已填对（base_url 带 s / model=flash / chat_completions）
- [ ] 重启 + 新建会话，右上角 = `deepseek-v4-flash` ✅
- [ ] 方式 A 脚本：`switch_to_cnb_gateway.sh` 运行后 `config.yaml` 已注册（`--check-only` 显示 ✅）
- [ ] 云端：点「云原生开发」→ 浏览器打开 `https://{id}-6060.cnb.run` 能看到 Hermes Web UI
- [ ] 云端容器终端 `curl http://127.0.0.1:8787/health` → 返回 `model=deepseek-v4-flash`（免费网关适配层在跑）

---

## 六、MARVIS 闭环记录清单

| # | MARVIS 动作 | 落点 |
|---|---|---|
| 1 | 按上方「方式 B → 方式 A」执行并把输出写入本地 | `local_job_queue.json` 标记对应任务完成 |
| 2 | 云端验证 WebGUI 可达后，写一条痕迹 | `msgbus/inbox/echo_wall/`（`scripts/cnb_echo_ping.sh`） |
| 3 | E/G 盘 + Obsidian 归档本文档 | 按 `scripts/export_to_github_and_mirror.sh` 流程 |
| 4 | 闭环记录回写 | `SelfLearn_Record.md` |

> 红线：Token/密钥只走本机环境变量，**绝不**写入仓库/日志/痕迹；量化/闲鱼两仓仅本机执行。

---

## 七、回滚（万一要切回）

```bash
# 恢复 config.yaml 到切换前备份
cp ~/.hermes/config.yaml.bak.<时间戳> ~/.hermes/config.yaml
# 重启 Hermes Studio → 新建会话 → 确认模型回到原 provider
```

---

## 附：相关文档索引

- `docs/免费基座DeepSeekV4Flash切换图文手册.md`（切换细节）
- `docs/操作手册_云上复刻HermesWebGUI可视化说明书.md` + `docs/操作图_云上Hermes云端控制台打开.html`（云端 WebGUI 图解）
- `docs/云上Hermes6060_connection_refused排查记录.md`（旧工作区根因与重建）
- `docs/Marvis配合执行方案_HermesStudio全自动_v2.0.md`（MARVIS 全自动安装）
- `skills/hermes-studio-cnb/SKILL.md`（一键接入技能）
