# DeepSeek-Harness Provider 配置界面字段·一一对应映射表

> 版本：v1.0 | 更新：2026-08-18 | 归属：龙虾五步法 §11.3 + 全域模板 #303 + 脚手架三文件
> 用途：把 DeepSeek-Harness WebUI（`http://127.0.0.1:3080`）「创建自定义提供方」表单里**每个界面字段**，
> 一一对应映射到「实际该填什么值」+「值从哪里拿」+「填错会怎样」。**照抄即可，无需凭记忆。**
>
> 一句话总纲：**让 DeepSeek-Harness 免费用 CNB 云原生 DeepSeek-V4-Flash**，能接企业群商单，云端正常工作。
> 本文是 Issue #43 全流程收敛到本地、方便查找使用的最终映射表。

---

## 〇、触发词（说这些词就打开本文）

`DeepSeek Harness 配置` / `怎么填` / `Provider 字段` / `配置映射` / `创建提供方` / `添加模型` / `deepseek harness 免费`

---

## 一、界面字段 ↔ 实际填写值 一一对应映射（核心表）

> 在 Harness WebUI「创建自定义提供方」表单里，从上到下依次是这些字段。**对照着填：**

| # | 界面字段 | 填什么值 | 值从哪里拿 | 填错会怎样 |
|---|---------|---------|-----------|-----------|
| 1 | **Provider ID** | `cnb-deepseek-v4-flash` | 自己命名（建议英文+数字，唯一标识） | 重名会冲突；红色校验提示忽略即可 |
| 2 | **显示名称 / 预设** | `CNB 免费 DeepSeek-V4-Flash`（预设选「自定义提供方」） | 自由命名；预设不选任何内置 | 选错预设会套用错误协议 |
| 3 | **API 协议** | `openai-completions` | 固定值 | 填错无法解析请求体 → 400/500 |
| 4 | **API 地址 / Base URL** | 见下方「四、API地址双路径」 | CNB 免费网关 / 本机 3081 网关 | 缺 slug → 404 Resource not found |
| 5 | **API 密钥** | 你的 `CNB_TOKEN`（见「五、API密钥获取」） | CNB 访问令牌，环境变量 | 空/错 → 401 Unauthorized |
| 6 | **模型 / Model** | `deepseek-v4-flash`（**必须精确，不是 pro**） | 固定值 | 拼错 → 404 model not found |

---

## 二、直接照抄的两种完整配置（三选一即可，推荐①）

### 方案① 直连 CNB 云端（最稳，不依赖本机网关）

```
Provider ID : cnb-deepseek-v4-flash
显示名称     : CNB 免费 DeepSeek-V4-Flash
API 地址     : https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai
API 协议     : openai-completions
API 密钥     : <你的 CNB 访问令牌>
模型         : deepseek-v4-flash
```

> ⚠️ **Base URL 用 `.../-/ai`（不带 /chat/completions）**。因为 Harness 会自动在末尾追加 `/chat/completions`，
> 拼出来正好是 `.../-/ai/chat/completions`（能用）。若你填了完整端点会变 `.../chat/completions/chat/completions` → 404。

### 方案② 本机 3081 网关（需先启动网关，解决 Failed to fetch）

```
Provider ID : cnb-gateway-local
显示名称     : CNB本地网关(DeepSeekV4+GLM5.2)
API 地址     : http://127.0.0.1:3081/v1    ⚠️ 需先双击 scripts/start_gateway_3080.bat 启动
API 协议     : openai-completions
API 密钥     : local（占位即可，网关内部自动读 CNB_TOKEN）
模型         : deepseek-v4-flash
```

### 方案③ DeepSeek-Harness 自研网关（云端 8080）

```
Base URL : http://<你的云端地址>:8080/v1   （我们搭的网关，端口 8080）
API Key  : 任意占位（代理内部自动取 CNB_TOKEN 上送）
模型     : deepseek-v4-flash
```

---

## 三、操作顺序铁律（必看）

```
1. 填写 Provider ID / 显示名称 / API 地址 / API 协议 / API 密钥 / 模型
2. ⚠️ 弹窗里【不要点"获取可用模型"】——CNB 网关无 /models 接口，点必 404（预期现象）
3. 直接右下角【创建提供方】保存
4. 保存完回到列表页，再点"获取可用模型"即可看到模型
5. 保存后【完全退出客户端再重启】+【新建会话】→ 右上角确认 deepseek-v4-flash
```

> 一键修复：`bash scripts/fix_dsh_provider.sh`（校验网关地址 + 自动修正缺 slug + 流式冒烟测试）

---

## 四、API 地址双路径详解

| 路径 | 完整地址 | 适用 | 依赖 |
|------|---------|------|------|
| **直连 CNB** | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai`（表单填这个，自动补成 `.../ai/chat/completions`） | 云端/本机均可，最稳 | CNB_TOKEN 有效 |
| **本机 3081** | `http://127.0.0.1:3081/v1` | 本机 Harness 桌面端 | 需先启动 `gateway_3080.py` |

> 端口约定：**3080 = DeepSeek-Harness WebUI(HTML)｜3081 = gateway_3080.py 中转网关(JSON)**
> 判断网关起没起：`curl http://127.0.0.1:3081/health` 返回 JSON `{"ok":true}` 才算起来。

---

## 五、API 密钥（CNB_TOKEN）获取三种方法

### 方法1：容器/云端环境变量自动注入（推荐）
```bash
echo "前缀: ${CNB_TOKEN:0:8}..."
# 或解析完整配置
python3 -c "import json,os; cfg=json.loads(os.environ['ACC_PRODUCT_CONFIG_V2']); print(cfg['authentication']['attributes']['token'])"
```

### 方法2：CNB 网页手动创建
CNB → 右上角头像 → **个人设置 → 访问令牌** → 新建一个（带 `repo-code:r` 权限）→ 复制粘贴

> 🔒 **安全**：Token 只在本地配置文件使用，**严禁**提交到 git 仓库。本映射表不写明文 Token。

---

## 六、常见报错对照（填错了怎么办）

| 报错 | 原因 | 解决 |
|------|------|------|
| `404 Resource not found` / `没有创建成提供方` | API 地址缺仓库 slug | 一键修复 `bash scripts/fix_dsh_provider.sh`；确认地址为 `.../-/ai` |
| `Failed to fetch` | **本机 3081 网关没启动**（网络层连不上，不是404） | 先双击 `scripts/start_gateway_3080.bat` 起网关 → `curl 3081/health` 返回 JSON → 再创建提供方 |
| `/models answered 404` | CNB 网关**没有 /models 接口**（预期现象） | **不要点"获取可用模型"**，直接手动在模型栏填 `deepseek-v4-flash` |
| `400 code 11101` | 非流式请求（平台仅支持流式） | 用 `stream:true`，或让 Harness 网关自动聚合（`harness_proxy.py` 已内置） |
| `401 Unauthorized` | Token 错误/未注入 | 检查 `CNB_TOKEN`，重新从环境变量获取 |
| `404 model not found` | 模型名拼错 | 必须精确填 `deepseek-v4-flash`（不是 pro） |
| Provider ID 红色提示 | 实时校验提示 | 忽略弹窗，直接【创建提供方】保存 |
| 配置后不生效 | 未重启/未新建会话 | 保存后**完全退出客户端再重启** + **新建会话** |

---

## 七、DeepSeek-Harness 自身无需配置（重点）

`harness_proxy.py` 启动时**自动从环境变量解析**免费网关和鉴权 Token，无需手动配置：

```bash
# 云端容器内一键启动（CNB_TOKEN 自动注入）
bash deepseek-harness/run_harness.sh

# 手动
python3 deepseek-harness/harness_proxy.py --port 8080
```

实测通过：
```
✅ /health               → {"status":"ok","model":"deepseek-v4-flash"}
✅ /v1/models            → deepseek-v4-flash / deepseek-r1 / qwen3-235b-a22b（均免费）
✅ /v1/chat/completions  → 流式 200 正常返回
✅ /v1/orders 派单        → 生成任务卡（企微接单）
```

---

## 八、四化对齐（本映射表如何落地四化）

| 维度 | 对齐点 |
|------|--------|
| 智能化 | 说触发词自动打开本文，AI 员工自主执行，不反复问 |
| 定制化 | 从 Issue #43 逆向工程出"界面字段↔值"蒸馏成集中表，避免重复踩坑 |
| 全自动化 | 一键修复脚本 `fix_dsh_provider.sh` + 触发词直达文档，零人工找路径 |
| 自我净化 | 每次配置报错回灌本文§六对照表，反哺脚手架+知识库 |

---

## 九、相关资源索引（方便查找）

| 资源 | 路径 |
|------|------|
| 本文（映射表） | `docs/DeepSeekHarness_Provider配置界面字段一一对应映射表_20260818.md` |
| 配置指南（完整版） | `docs/DeepSeekHarness_CNB免费V4Flash_配置指南.md` |
| 本机3081网关路径详解 | `docs/方案B_本机3081网关启动路径详解_20260818.md` |
| 一键修复脚本 | `scripts/fix_dsh_provider.sh` |
| 模型层映射配置 | `deepseek-harness/config/model_layer.json` |
| Harness 网关本体 | `deepseek-harness/harness_proxy.py` |
| Harness Agent 编排 | `deepseek-harness/harness_agent.py` |
| Harness 启动脚本 | `deepseek-harness/run_harness.sh` |
| Web 控制台 | `deepseek-harness/web_console.html` |
