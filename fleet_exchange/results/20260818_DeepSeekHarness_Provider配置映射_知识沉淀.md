# DeepSeek-Harness Provider 配置界面字段映射 · 知识沉淀（Obsidian 回灌载体）

> 归属：四化迭代知识库 · 2026-08-18
> 执行：hermes 大脑 | 任务：用户全权授权把 Issue #43 配置界面字段一一对应映射到本地项目
> 用途：作为本地 `archive_obsidian_v1.6.0.sh` / `auto_sync_30min.sh` 同步回灌 Obsidian 的知识条目载体

---

## 归档目标（Obsidian 主库）

```
E:/龙虾AI主控中心/Obsidian/wiki/deepseek-harness-provider配置映射_20260818.md
E:/龙虾AI主控中心/Obsidian/副业变现/DeepSeekHarness免费用CNB免费V4Flash_20260818.md
```

## 知识要点（四化校准）

### 1. 核心字段映射（Harness「创建提供方」表单 ↔ 实际值）
| 界面字段 | 填写值 |
|---|---|
| Provider ID | `cnb-deepseek-v4-flash` |
| 显示名称/预设 | `CNB 免费 DeepSeek-V4-Flash` / 自定义提供方 |
| API 协议 | `openai-completions` |
| API 地址 | `https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai`（不带 /chat/completions，Harness 自动追加） |
| API 密钥 | `CNB_TOKEN`（环境变量 / CNB 个人设置·访问令牌） |
| 模型 | `deepseek-v4-flash`（必须精确，不是 pro） |

### 2. 三路径选择
- ① 直连 CNB：`.../-/ai`（最稳）
- ② 本机 3081 网关：`http://127.0.0.1:3081/v1`（需先启动 gateway_3080.py）
- ③ 云端 8080 网关：`http://<云端>:8080/v1`

### 3. 铁律（勿再犯）
- Base URL 填完整端点 `.../chat/completions` 会 404（自动追加变双重）
- `Failed to fetch` = 本机 3081 网关没启动
- 弹窗不点"获取可用模型"（CNB 无 /models 接口必 404）
- 保存后完全退出客户端重启 + 新建会话
- `400 code 11101` = 非流式，平台仅支持流式

## 反向赋能（从知识库回灌脚手架）
已同步：脚手架四文件（AGENTS/HERMES/CODEX/CLAUDE）快速指令表 + 数字快捷手册 Harness配置触发词 + SelfLearn_Record.md
