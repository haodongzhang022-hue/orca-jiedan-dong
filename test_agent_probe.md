# Claude-Code CNB NPC 基座探测

Claude-Code CNB NPC 基座探测通过（deepseek-v4-flash）

- 探测时间：CNB 云端容器
- 基座型号：CNB 内置免费 deepseek-v4-flash（MoE 284B / 激活 13B）
- 链路：Claude-Code CLI → 本地适配层(127.0.0.1:8787) → CNB 内置 AI 网关（api.cnb.cool，免费配额）
- 外部付费 API：未调用（无 api.deepseek.com / api.anthropic.com / api.openai.com 域名）
