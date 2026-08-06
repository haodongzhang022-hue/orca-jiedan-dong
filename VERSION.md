# 版本信息
version: 1.5.0
release_date: 2026-08-07
base_model: CNB内置免费DeepSeek-V4-Flash (MoE 284B/激活13B)
base_model_valid_until: 2026-12-31
changes:
  - Claude-Code封装为CNB云端NPC（@claude-code触发）
  - 接口适配层 adapters/anthropic_to_cnb.py：Anthropic协议→CNB内置AI网关
  - npc:go options.model=deepseek-v4-flash 显式绑定免费基座
  - 额度监控与降级保护 scripts/quota_monitor.py（1600核时/月）
  - GitHub私有仓库导出包 + E盘/G盘镜像清单脚本
  - Issue#10 实测通过：@claude-code 唤起Agent完成文件创建+PR提交+评论回写
  - 【路径B增强】自定义Docker镜像容器模式：完整原版Claude-Code CLI + 适配层(127.0.0.1:8787)
  - 【路径B】.ci/npc-full.yml claude-code角色流水线（覆盖$兜底，独立容器执行）
  - 【路径B】adapters/Dockerfile 构建镜像 + main.push 自动构建推送流水线
  - 【路径B】docs/claude_code_cloud_vs_local.md A/B双模式对比文档
