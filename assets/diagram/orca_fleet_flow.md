# ORCA 舰队跨主体协作流程图

> 此文件为 Mermaid 源码，可在 GitHub/CNB 上直接渲染

## 横向流程图

```mermaid
flowchart LR
    subgraph Maris本地
        M[Maris Agent] -->|maris_dispatch.sh| A[fleet_exchange/incoming/]
    end

    subgraph Codex执行层
        A -->|读取任务卡| B[fleet_exchange/doing/]
        C["@npc/codex"] -->|代码生成+脚本执行| B
    end

    subgraph ClaudeCode审核层
        B -->|执行结果| D[fleet_exchange/done/]
        E["@npc/claude-code"] -->|代码审计+质量校验| D
    end

    subgraph CodeBuddy终审层
        D -->|审核结果| F[fleet_exchange/results/]
        G["@CodeBuddy"] -->|兜底终审+归档| F
    end

    F -->|交付物| H[客户/Obsidian归档]

    style M fill:#f9f,stroke:#333
    style C fill:#4CAF50,stroke:#333,color:#fff
    style E fill:#2196F3,stroke:#333,color:#fff
    style G fill:#FF9800,stroke:#333,color:#fff
```

## 角色权责表

| 角色 | 定位 | 权责 | 禁止事项 |
|------|------|------|---------|
| Maris | 本地调度 | 投递任务卡到 incoming/ | 不修改 doing/done/results |
| Codex | 代码执行 | 读取 incoming → 执行 → 移入 doing | 不跳过审核直接写入 done |
| Claude Code | 代码审计 | 读取 doing → 审计 → 移入 done | 不重新执行代码 |
| CodeBuddy | 终审归档 | 读取 done → 终审 → 归档 results | 不代替 Codex/Claude Code |
```
