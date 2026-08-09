# 免费基座 DeepSeek-V4-Flash 切换图文手册（Hermes Studio / 本地三引擎）

> 归属：orca-jiedan 舰队 · CodeBuddy（B）出品
> 版本：v1.0 ｜ 日期：2026-08-10 ｜ 关联：Issue #27（Hermes Studio 落地 + 模型切换）
> 执行者：汤嘉锋 或 MARVIS（本地 Windows 本机）
> 目标：**把本地 Hermes Studio 正在跑的 Xiaomi MiMo（mimo-v2.5-pro，积分 0.31%）彻底切到 CNB 免费 DeepSeek-V4-Flash 网关，0 成本。**

---

## 〇、一句话结论

```
你现在 Hermes Studio 里跑的是 mimo-v2.5-pro（Xiaomi）→ 正在烧 MiMo 积分（剩 0.31%）。
数据库里把 Agent 切到 deepseek-v4-flash 的改动，GUI 层面没生效。
解决办法 = 在 Hermes Studio「模型管理」GUI 里手动切一次 + 重启 Hermes Studio（见第 2 节）。
```

> 💡 云端 NPC（@hermes / @codex / @claude-code）**早已**全部走 CNB 免费基座（`milli_credit=0`），
> 不受影响；要切的是你**本地 Hermes Studio 桌面版**。

---

## 一、"deepseek-v4-flash"和"DeepSeek v4.0"是什么关系？

| 名字 | 含义 | 在哪用 |
|---|---|---|
| **deepseek-v4-flash** | CNB 内置免费网关上的**模型标识**（MoE 284B/激活13B，Flash 快速档） | CNB 云端 NPC 全部用它，免费至 2026-12-31 |
| DeepSeek V4 / v4.0 | 同一条 DeepSeek 模型线的**宣传名**（官方定价文档里 V4-Flash 免费档） | 即上面那个，只是叫法不同 |
| mimo-v2.5-pro | Xiaomi MiMo 模型（**付费/积分**，你本地正在用） | ❌ 要停用 |

**切过去之后你会看到**：Hermes Studio 会话右上角模型显示 `deepseek-v4-flash`，不再显示 `mimo-v2.5-pro`。

---

## 二、最关键的 5 步（GUI 手动切换 · 必须做）

> 为什么不能只改数据库？—— 实测：DB 已改 `cnb-codebuddy/deepseek-v4-flash`，但 Hermes Studio
> 当前会话仍显示 `You are powered by the model mimo-v2.5-pro`。GUI 层的 provider/model 选择
> **没有跟着 DB 变**，必须手动在 GUI 里切一次 + 重启才真正生效。

```
① 打开 Hermes Studio（桌面版）
② 进「设置 → 模型管理 / Providers」（就是你截图里显示 Xiaomi MiMo 的那个面板）
③ Provider 选  cnb-deepseek-v4-flash
   （若列表里没有：先点「添加 Provider」→ 填 ↓ 表，然后刷新列表）
④ Model 选  deepseek-v4-flash
⑤ 保存 → 完全退出 Hermes Studio（含托盘）→ 重新打开
   → 新建一个会话，确认右上角 = deepseek-v4-flash ✅
```

**手动添加 Provider 的参数表**（如果列表里没有现成的 `cnb-deepseek-v4-flash`）：

| 字段 | 填什么 |
|---|---|
| name | `cnb-deepseek-v4-flash` |
| base_url | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions` |
| api_key | `%CNB_TOKEN%`（引用本机环境变量；或直接在 Hermes 环境变量里配 `CNB_TOKEN`） |
| model | `deepseek-v4-flash` |

> ⚠️ **Token 铁律**：`CNB_TOKEN` 只放本机环境变量，**绝不**把明文 Token 写进配置文件/仓库/截图。
> 仓库里 `scripts/one_click_cnb_gateway.sh` 和 `scripts/switch_to_cnb_gateway.sh` 都只写
> `api_key_env: CNB_TOKEN`，不写明文。

---

## 三、可选：一键脚本（省得手填，MARVIS 可全自动）

在 Git Bash / WSL 里执行：

```bash
# 方式A：一键脚本（写 provider 到 ~/.hermes/config.yaml，幂等、自动备份）
bash scripts/switch_to_cnb_gateway.sh

# 方式B：原来的接入脚本（同效果）
bash scripts/one_click_cnb_gateway.sh

# 先只读自检，不改任何文件
bash scripts/switch_to_cnb_gateway.sh --check-only

# 只打印将写入内容，不落盘
bash scripts/switch_to_cnb_gateway.sh --dry-run
```

脚本会做的动作（全部零密钥、自动备份 `*.bak.<时间戳>`、不改端口铁律）：

| # | 动作 |
|---|------|
| 1 | 在 `~/.hermes/config.yaml` 注册 `cnb-deepseek-v4-flash` provider（幂等） |
| 2 | 输出 GUI 手动切换 + 验证 + 回滚指引 |

> ⚠️ **脚本无法替你点 GUI**。写 provider 只是让 GUI 下拉里**有得选**，
> 最后一步"选它 + 保存 + 重启 Hermes Studio"仍要在 GUI 完成（第 2 节）。
> 若要彻底替代 MiMo 代理，可再把本地 Claude 15721 / Codex 15730 代理的
> `UPSTREAM` 指到 CNB 网关（见附录），但先确保 GUI 切换成功再说。

---

## 四、验证是否真的切过去了（3 个检查点）

| # | 检查 | 通过标准 |
|---|------|---------|
| 1 | Hermes Studio 会话右上角模型 | 显示 `deepseek-v4-flash`（不是 `mimo-v2.5-pro`） |
| 2 | 群聊/会话环境信息 | `You are powered by the model deepseek-v4-flash.` |
| 3 | 命令或网页试调用 | 返回 200 / 正常流式输出（见下） |

**命令行试调用（Git Bash）**：

```bash
curl -N https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions \
  -H "Authorization: Bearer $CNB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","stream":true,"messages":[{"role":"user","content":"ping"}]}'
```

看到 `"model":"deepseek-v4-flash"` 的流式 chunk 即网关连通 ✅（`code:11101` 表示端点对、
但非流式请求不支持，加 `"stream":true` 即可）。

---

## 五、切过去之后：MiMo 积分不再消耗了吗？

| 场景 | 是否还烧 MiMo 积分 |
|---|---|
| Hermes Studio 新会话用 `cnb-deepseek-v4-flash` | ❌ 不烧（走 CNB 免费额度） |
| 旧会话还开着、没重启、仍显示 mimo-v2.5-pro | ⚠️ 仍烧 —— **务必重启并开新会话** |
| 本地 Claude Code / Codex 桌面版直连 MiMo（15721/15730 代理） | ⚠️ 仍烧 —— 见附录 |
| 云端 NPC（@hermes/@codex/@claude-code） | ❌ 不烧（早已全走 CNB 免费基座） |

> MiMo 积分 0.31% 不恢复。切过去后**不要再把模型切回 mimo**，旧会话用完即关。

---

## 六、回滚（万一要切回来）

```bash
# 脚本已自动备份
ls ~/.hermes/config.yaml.bak.*
cp ~/.hermes/config.yaml.bak.<时间戳> ~/.hermes/config.yaml

# 或手动：把 Hermes Studio GUI 里的 Provider 切回 Xiaomi MiMo（不推荐）
```

---

## 附录：本地 Claude/Codex 桌面版也一起切（可选，更彻底）

当前本地三引擎（Claude 15721 / Codex 15730 / Hermes 8642）默认走 Xiaomi MiMo 代理。
**只切 Hermes Studio GUI 后，Claude/Codex 桌面版仍可能烧 MiMo**。要彻底断掉：

```powershell
# 1) 找到本地代理脚本（仓库文档记录的路径）
E:\龙虾AI主控中心\MCP服务\anthropic_proxy_15721.py
E:\龙虾AI主控中心\MCP服务\codex_tool_proxy.py

# 2) 把脚本里的 UPSTREAM 指到 CNB 免费网关
UPSTREAM = "https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions"
#   并在脚本环境里配置 CNB_TOKEN（只放环境变量，不写死）

# 3) 重启代理：python anthropic_proxy_15721.py + python codex_tool_proxy.py
# 4) 各 config.toml 的 model 改为 deepseek-v4-flash（如适用）
```

> ⚠️ 别动端口铁律 15721/15730/8642/4567/11434（改端口不如改上游）。
> 量化/闲鱼两仓仅本机执行，凭证严禁上云。

---

## 七、FAQ

| 问题 | 答案 |
|------|------|
| 切换后要重启吗？ | **必须**。DB 改了但 GUI 没生效就是因为没重启；切完一定要完全退出（含托盘）再开 |
| 为什么加了 provider 列表里还是没有？ | 刷新列表 / 确认 `~/.hermes/config.yaml` 有 `cnb-deepseek-v4-flash` 段 / 重启 Hermes Studio |
| CNB_TOKEN 在哪拿？ | 你本人登录 CNB → 个人令牌；只放本机环境变量，绝不入库/截图 |
| 云端 NPC 要不要也切？ | 不用，云端早已全走免费基座（`milli_credit=0` 实证） |
| MiMo 积分还能恢复吗？ | 不能，属消耗型。切到 CNB 免费基座后不再消耗即可 |

---

*本手册由 CodeBuddy 在 CNB 云端容器生成，网关端点与模型名均实测连通（流式 200），无密钥；不含 MiMo Token 等敏感信息。*
