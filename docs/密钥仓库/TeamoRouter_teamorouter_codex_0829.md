# 本地密钥仓库 · TeamoRouter

> 创建：汤小龙（Codex） ｜ 日期：2026-08-29 ｜ 供应商ID：	eamorouter_codex_0829

## 凭证

| 项 | 值 |
|---|---|
| 供应商 | TeamoRouter |
| 供应商ID | 	eamorouter_codex_0829 |
| API Base URL | https://teamorouter.cn/v1 |
| 协议 | OpenAI Responses API（Codex 0.144.6 仅支持该协议） |
| 密钥 | 存环境变量 TEAMOROUTER_API_KEY（setx 用户级，未落明文） |
| 密钥掩码 | sk-teamo-d346...13fb |

## 可用模型（Responses API，Codex 可直连）

- deepseek-v4-flash-free（免费，推荐）
- deepseek-v4-flash
- deepseek-v4-pro-free
- deepseek-v4-pro
- kimi-k3

## 协议限制

- glm-5.3-flash-free / glm-5.3-flash 仅支持 Chat Completions API，Codex 0.144.6 无法直连。
- Chat Completions 自检已通过（HTTP 200），但接入 Codex 需换用上表 Responses 兼容模型。

## 安全

- 密钥全文仅存于 Windows 用户环境变量，符合项目 P0 红线「脱敏禁入四端」。
- 本文件记录掩码与指针，不含明文，可安全入仓。