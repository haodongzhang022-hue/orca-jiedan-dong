# DeepSeek Harness · CNB NPC 角色接入指南（@deepseek-harness · 路径B 容器模式）

> 目标：把 DeepSeek Harness 云端超 Agent 运行时，像 Hermes / Codex / Claude Code 一样，
> 以独立 NPC 角色接入 CNB 云原生平台（路径B 自定义镜像容器），复用 CNB 内置免费
> **DeepSeek-V4-Flash** 基座，免费用云原生模型 + 接企业微信群商单。
>
> 非 Hermes Studio——这是 DeepSeek Harness 专属超 Agent 编排引擎的云端分身。

---

## 一、角色接入总览（参照项目脚手架三件套）

| 脚手架文件 | 作用 | 本次新增/修改 |
|-----------|------|--------------|
| `.cnb/settings.yml` | 定义 NPC 角色（name/slogan/prompt 人设） | ➕ 新增 `deepseek-harness` 角色 |
| `.ci/deepseek-harness.yml` | 路径B 自定义镜像容器流水线（顶层 key 匹配角色） | ➕ 新增 |
| `.cnb.yml` | include 合并 + main.push 镜像构建 + 免费基座绑定 | ✏️ include 加入 + ifModify 加入 harness |
| `adapters/Dockerfile` | 把运行时打包进镜像 + 语法自检 | ✏️ 加入 harness 运行时层 |
| `deepseek-harness/entrypoint.sh` | 容器内启动 Harness 网关（8080） | ➕ 新增 |

---

## 二、@deepseek-harness 怎么被召唤

在 **Issue / PR 评论**中 `@deepseek-harness`（或 `@TJF19770107/orca-jiedan(deepseek-harness)`），
CNB 自动拉起该角色，走路径B 自定义镜像容器（独立 Docker 容器，像 dock 里的容器一样），
内部启动 Harness 网关并注入超 Agent 编排任务，回写评论。

**它与 Hermes/Codex/Claude Code 完全并列**，是舰队里第 5 个独立 NPC 角色：

| 角色 | 端口 | 执行引擎 | 基座 |
|------|------|---------|------|
| claude-code | 8787(适配层) | 完整原版 Claude-Code CLI | deepseek-v4-flash |
| codex | - | 原生 @openai/codex CLI | deepseek-v4-flash |
| hermes | - | 原生 hermes-agent CLI | deepseek-v4-flash |
| **deepseek-harness** | **8080(网关)** | harness_proxy + harness_agent 超Agent编排 | **deepseek-v4-flash** |

---

## 三、云端容器（云原生开发）

点仓库分支页「**云原生开发**」→ `.ide/Dockerfile` 构建 → WebIDE PORTS 面板转发 **8080**：

```
https://{实例ID}-8080.cnb.run   → DeepSeek Harness 云端控制台
```

控制台两大功能卡：
- 左卡「接单并建档任务卡」：填客户/品类/需求/规格/结算 → 生成任务卡
- 右卡「规划 → 委派 → 执行 → 汇总」：让 Harness 拆单、子 Agent 接力、汇总结论

> ⚠️ 云原生环境有回收机制（10 分钟无操作 / 最长 18h / 凌晨 4-6 点强制回收），
> 每次重开地址会变，需重新从 PORTS 转发并复制新地址。

---

## 四、免费 DeepSeek-V4-Flash 基座（无需手动配置）

Harness 网关 `harness_proxy.py` 启动时**自动从环境变量解析** CNB 免费网关和鉴权 Token：

| 环境变量 | 作用 | 默认值 |
|---------|------|--------|
| `CNB_TOKEN` | 鉴权 Token | 容器自动注入 |
| `ACC_PRODUCT_CONFIG_V2` | 网关地址自动解析 | 容器自动注入 |
| `CNB_MODEL` | 模型名 | `deepseek-v4-flash` |
| `HARNESS_PORT` | 网关监听端口 | `8080` |

平台硬约束「仅支持流式」：网关内置**非流式自动聚合**，客户端无需关心。

---

## 五、验证命令

```bash
# 在容器内
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/v1/models

# 免费模型对话（流式）
curl -sN -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}],"stream":true}'

# 企业微信派单 → 任务卡
curl -s -X POST http://127.0.0.1:8080/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"customer":"汤嘉锋","category":"海报","demand":"1080x1080暗黑科技风","settle":"支付宝128"}'
```

---

## 六、安全

- 密钥零落盘：`CNB_TOKEN` / `ACC_PRODUCT_CONFIG_V2` 全部来自流水线环境变量注入
- 镜像不含任何明文 Token
- 全程免费 DeepSeek-V4-Flash，不调用外部付费 API
