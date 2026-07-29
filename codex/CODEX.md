# Codex 项目配置 · 自动恢复指令

## 自动恢复协议

**你进入此项目时，必须先检查代理服务状态：**

1. 检查端口 15730 是否在 LISTENING
2. 如未运行，执行：`python "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"`
3. 验证：`curl http://127.0.0.1:15730/health`

## 项目约定

- 模型：mimo-v2.5-pro
- 代理：127.0.0.1:15730（Codex Tool Proxy v6）
- wire_api：chat（不要改为 responses，会导致 401）
