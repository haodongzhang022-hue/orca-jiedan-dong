# TeamoRouter 供应商接入日志

> 执行：汤小龙（Codex） ｜ 日期：2026-08-29 ｜ 供应商ID：`teamorouter_codex_0829`

## 结果摘要

| 项 | 结果 |
|---|---|
| Chat Completions 自检（glm-5.3-flash-free） | HTTP 200，响应 `ok` |
| Responses API 自检（deepseek-v4-flash-free） | HTTP 200，响应 `ok` |
| Codex 端到端（deepseek-v4-flash-free） | 通过，响应 `ok`，消耗 1978 tokens |
| 配置文件 | `C:\Users\Administrator\.codex-orch\config.toml` |
| 密钥 | 环境变量 `TEAMOROUTER_API_KEY`（setx 用户级） |
| Marvis 介入 | 否（直接读写配置文件，无需 UI） |

## 关键发现

1. Codex 0.144.6 已移除 `wire_api = "chat"`，仅支持 `responses`。
2. `glm-5.3-flash-free` 仅支持 Chat Completions，无法直连 Codex；Codex 端免费模型改用 `deepseek-v4-flash-free`。
3. 现有本地代理（`127.0.0.1:51427`）与直连供应商并存，互不影响。

## 接入参数

- 供应商ID：`teamorouter_codex_0829`
- base_url：`https://teamorouter.cn/v1`
- wire_api：`responses`
- env_key：`TEAMOROUTER_API_KEY`
