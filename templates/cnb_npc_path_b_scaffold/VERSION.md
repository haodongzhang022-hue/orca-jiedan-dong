# 版本信息
version: 1.6.0
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
  - 【路径B·修订】Dockerfile 改为 ENTRYPOINT+CMD：容器启动后台拉起适配层监听 127.0.0.1:8787
  - 【路径B·修订】镜像构建流水线变量修正：main.push 用 CNB_REPO_SLUG_LOWERCASE（NPC变量不注入）
  - 【路径B·修订】.ci/npc-full.yml NPC_MODEL 与 options.model 双保险强制锁定 deepseek-v4-flash
  - 【路径B·修订】脚手架模板 templates/cnb_npc_path_b_scaffold 补齐全部文件（Dockerfile/适配层/entrypoint/quota/docs）
  - 【v1.6.0·新增】GitHub 原生 Hermes CLI（NousResearch/hermes-agent）接入 CNB NPC 舰队
  - 【v1.6.0·新增】.ci/hermes.yml hermes 角色路径B流水线（@hermes 触发，独立容器执行）
  - 【v1.6.0·新增】hermes/entrypoint.sh + adapters/hermes_entry.sh 原生 hermes 安装/入口
  - 【v1.6.0·新增】.cnb/settings.yml 注册 hermes 角色（大脑层·战略调度人设）
  - 【v1.6.0·修订】adapters/Dockerfile 内置 hermes CLI + claude/hermes 双入口
  - 【v1.6.0·修订】镜像版本 1.5.0 → 1.6.0，构建/推送流水线同步
  - 【v1.6.0·同步】templates/cnb_npc_path_b_scaffold 脚手架模板整体升级
  - 【v1.6.0·新增】原生 Codex CLI（@openai/codex，bin=codex.js，linux-x64 二进制）打包进镜像
  - 【v1.6.0·新增】.ci/codex.yml codex 角色路径B流水线（@codex 触发，独立容器执行）
  - 【v1.6.0·修订】codex 角色从路径A（$ 兜底 npc:go 轻量化）升级为路径B（自定义镜像+原生完整 CLI）
  - 【v1.6.0·修订】路径B 三个角色（claude-code/hermes/codex）maxTurns 24 → 60，修复
    "Agent aborted: reached maxTurns limit (24)" 导致 @claude-code/@hermes 执行失败问题
  - 【v1.6.0·同步】脚手架模板同步 codex 路径B流水线 + Dockerfile 双 CLI 内置
