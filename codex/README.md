# Codex 执行层 - 代码与自动化执行

> 所属分支：`codex/executor`  
> 角色定位：执行层 / 自动化实现

## 核心职责
- 脚本开发与维护
- 工具调用与集成
- 批量任务执行与数据处理
- 执行过程中的日志与断点续传
- 向 `hermes/brain` 反馈进度与异常

## 目录说明
- `scripts/`：可执行脚本、自动化流程
- `tools/`：工具封装、第三方 SDK 适配、本地模型调用
- `batch_tasks/`：批量任务配置、队列管理、并行执行策略

## 协作规则
1. 从 `hermes/brain` 接收任务清单；
2. 在 `scripts/` 或 `tools/` 实现功能；
3. 完成后提交到 `codex/executor` 分支；
4. 主动通知 `claude/reviewer` 进行审查。
