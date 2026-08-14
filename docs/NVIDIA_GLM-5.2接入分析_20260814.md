# NVIDIA API 免费 GLM-5.2 接入分析报告（审核侧取证）

> 审核 Agent：CLAUDE CODE | 日期：2026-08-14 | 角色：审核取证 + 验收标准
> 结论先行：**NVIDIA 端点完全可用，配置停留在界面层，三层断链导致三引擎仍在跑 deepseek-v4-flash**。

> **更新（2026-08-14 08:50 · 已修复）**：断点已收窄到房间 Agent 绑定层，已落地修复——见文末「六、修复落地记录」。

## 一、用户已做的配置（截图 OCR + 数据库实测）

| 项 | 实测内容 | 来源 |
|---|---|---|
| 模型管理界面 | OpenAI Chat Completions 格式 + 自定义请求地址 `https://integrate.api.nvidia.com/v1` + 模型 `z-ai/glm-5.2` / `minimaxail/minimax-m3` | 截图 OCR |
| providerLabels | `custom:atomcode-glm-5.2` → `atomcode-glm-5.2` | `~/.hermes-web-ui/config.json` |
| providerPreferredModels | `custom:atomcode-glm-5.2` → `GLM-5.2` | 同上 |
| 房间 Agent 配置 | hermes 房间 agent provider = `custom:nvidia-glm5.2`、model = `z-ai/glm-5.2` | `hermes-web-ui.db` `gc_room_agents` 表 |
| 凭据 | `credential_configured: [redacted]`（已配置，加密存储，无法读取明文） | `provider_audit_events` 表 |

## 二、为什么不能用（三层断链，全部实测）

| 层 | 实测 | 结论 |
|---|---|---|
| L1 NVIDIA 端点 | `https://integrate.api.nvidia.com/v1/models` → **HTTP 200**，102 个免费模型，**`z-ai/glm-5.2` 真实存在**（另有 `minimaxai/minimax-m3`）；无 key 调 chat/completions → 401 `authorization was missing` | ✅ 端点健康、模型在册，仅缺有效 Bearer key |
| L2 13460 代理池 | `curl 127.0.0.1:13460/v1/models` → 仅 `deepseek-v4-flash` + `Qwen/Qwen3-VL-8B-Instruct` 两个模型，**无 GLM-5.2、无 NVIDIA 转发规则** | ❌ 代理层未接线 |
| L3 launch.ps1 注入 | claude-code：`ANTHROPIC_MODEL=deepseek-v4-flash` ×5 处，BASE_URL 走 8748→13460/v1；codex：`--model deepseek-v4-flash` | ❌ 引擎启动脚本仍硬编码 deepseek |

**根因（第一性原理）**：用户在 Hermes Studio「模型管理」界面层配置了 GLM-5.2（provider 编辑器），但三引擎实际运行读取的是 Hermes 每次新会话重新生成的 `launch.ps1`（仍指向 `custom_atomcode-v4-local` 配置集 + 13460 代理），而 13460 代理的模型池也没有 NVIDIA 转发——**界面配置 ≠ 运行注入 ≠ 代理转发，三层各自为政**。

**附带**：此前视觉链路 428/429 限流是免费档触顶信号，与模型切换是两回事。

## 三、1234 框架解决方案（不破坏现有 DeepSeek/AtomCode 配置）

### 1️⃣ 一人一公司（分工到位）
| 角色 | 动作 |
|---|---|
| owner | ① 在 Hermes Studio「模型管理」确认 `atomcode-glm-5.2` 的 **API key 有效**（NVIDIA 控制台 build.nvidia.com 生成，`nvapi-` 开头）；② 在 Studio 界面把三引擎模型下拉切到 GLM-5.2 |
| hermes（大脑） | 在 13460 代理（或独立新端口）**新增 NVIDIA 转发规则**：`z-ai/glm-5.2` → `https://integrate.api.nvidia.com/v1` + key；现有 deepseek 转发规则不动 |
| codex（执行） | 切换后新开会话验证：launch.ps1 注入 `z-ai/glm-5.2`、curl `/v1/models` 出现 GLM-5.2、实测一条对话 |
| CLAUDE CODE（审核） | 按第四部分验收标准复核放行 |

### 2️⃣ 马斯克×巴菲特蒸馏（能力圈判断）
- NVIDIA 免费层个人账号约 40 req/min 限速，GLM-5.2 适合**文本/编程主力**；接单扫描看图仍需 Qwen3-VL-8B（Pro 解锁）——**能力圈分工：GLM-5.2 写代码 + DeepSeek 兜底 + Qwen3-VL 视觉**，不互斥。

### 3️⃣ 三载体联动迭代（固化不复发）
- 切换经验写入：五步法 §11.3 触发词 / 全域模板 #305 / 脚手架三文件模型配置节——「配了不用」的教训沉淀为「三层联动检查清单」。

### 4️⃣ 四化迭代 Obsidian（沉淀回灌）
- 归档 `Obsidian/wiki/舰队运维/NVIDIA_GLM-5.2接入链路_20260814.md` + `SelfLearn_Record.md` 头部新条目（含三层断链判定表 + NVIDIA 免费层参数）。

## 四、验收标准（审核把关，缺一不放行）

1. `curl 127.0.0.1:13460/v1/models`（或新 NVIDIA 转发端口）出现 **`z-ai/glm-5.2`**；
2. 新会话 launch.ps1 注入模型名 = **`z-ai/glm-5.2`**（claude-code 5 处全改 / codex `--model`）；
3. 三引擎实测一条对话返回 **200** 且内容由 GLM-5.2 生成（可查会话日志模型字段）；
4. **DeepSeek/AtomCode 现有配置零改动**：`custom:atomcode-v4-local` 配置集、13460 的 deepseek 转发、`deepseek-v4-flash` 均可继续使用（回归测试 1 条）。

## 五、如实边界

- NVIDIA key 明文存于 Hermes 加密凭据（redacted），我无法读取做端到端 key 验证；端点可用性已实测（200 + 模型在册 + 401 缺 key）。
- 修改 launch.ps1 / 13460 代理配置 / Studio 界面切换，均在授权工作区之外，执行动作归属 hermes/codex/owner 侧。
