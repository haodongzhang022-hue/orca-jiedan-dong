# Hermes 大脑层 - 战略调度与流程控制

> 所属分支：`hermes/brain`  
> 角色定位：大脑层 / 战略调度

## 核心职责
- 项目总控与需求拆解
- 多 Agent 协调与任务分配
- 流程编排与状态机管理
- 知识库联动与记忆同步
- 与 Codex / Claude 分支的接口契约定义

## 目录说明
- `flow_control/`：流程编排、状态机、工作流定义
- `orchestration/`：多 Agent 调度协议、任务路由、负载均衡
- `knowledge_sync/`：知识库同步规则、记忆压缩、跨层信息传递

## 协作规则
1. 接收高层需求后，先在 `orchestration/` 生成任务清单；
2. 将可执行子任务分配给 `codex/executor`；
3. 将需校验的交付物路由给 `claude/reviewer`；
4. 最终确认无误后，发起合并到 `master` 的申请。
