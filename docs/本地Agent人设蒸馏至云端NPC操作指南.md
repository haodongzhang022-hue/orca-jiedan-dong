# 本地Agent人设蒸馏至云端NPC操作指南

> 版本：1.4.1 | 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> 适用仓库：orca-jiedan / orca-wangpan / orca-xianyu / orca-quant-jiasheng / orca-quant-binance
> 前置条件：已创建 CNB 仓库，已配置 .cnb.yml + .cnb/settings.yml

---

## 一、核心概念：本地 Agent vs 云端 NPC 分身

| 维度 | 本地 Agent（原生） | 云端 NPC（分身） |
|------|-------------------|------------------|
| 运行环境 | Windows 本地 | CNB Docker 容器 |
| 模型基座 | Ollama DeepSeek-V4-Flash | CNB mtga 镜像内置 |
| 代码执行 | 原生 Python/Node.js/Shell | Docker 沙箱内执行 |
| 文件系统 | 本地目录完整访问 | 仅仓库内文件 |
| 消息驱动 | 企业微信群实时监听 | Issue/PR 评论 @ 触发 |
| 人设来源 | worktrees/codex/SKILL.md 等 | .cnb/settings.yml prompt |
| 持续性 | 常驻后台进程 | 每次评论触发一次流水线 |
| 成本 | 本地算力 | CNB 免费（至2026-12-31） |

**关键约束**：云端 NPC 无法 1:1 同步本地 Agent 的全部能力（本地文件系统、GUI 操作、常驻监听等），
需要通过人设蒸馏将核心逻辑映射到 NPC prompt 中。

---

## 二、蒸馏流程（三步走）

### 2.1 第一步：提取本地 Agent 人设

本地 Agent 的人设分散在以下文件中，需要逐一提取核心逻辑：

| 文件路径 | 内容 | 蒸馏要点 |
|---------|------|---------|
| `codex/SKILL.md` | Codex 核心能力与工作流 | 提取工作原则、输出格式、代码规范 |
| `codex/README.md` | Codex 使用说明 | 提取接口规范、常用命令 |
| `claude/SKILL.md` | Claude Code 审计规则 | 提取审计标准、严重等级分类 |
| `hermes/SKILL.md` | Hermes 消息路由规则 | 提取事件绑定、消息分发逻辑 |
| `scripts/` | 本地业务脚本 | 提取关键业务流程逻辑 |
| `config/` | 本地配置文件 | 提取必要环境变量 |

### 2.2 第二步：将人设转换为 NPC Prompt

> **原则**：NPC prompt 本质是"在 Docker 容器中运行的系统提示词"，必须自包含、无需外部依赖。

**转换模板**：

```yaml
# .cnb/settings.yml
npc:
  roles:
    - name: codex
      prompt: |
        # 角色：[从 codex/SKILL.md 的 title 提取]
        
        ## 核心能力
        [从 codex/SKILL.md 的核心能力列表蒸馏]
        
        ## 工作原则
        [从 codex/SKILL.md 的工作原则蒸馏，去掉本地路径依赖]
        
        ## 输出格式
        [保留原始输出格式要求]
        
        ## 仓库结构认知
        [简述当前仓库的目录结构，帮助 NPC 理解上下文]

    - name: claude-code
      prompt: |
        # 角色：[从 claude/SKILL.md 的 title 提取]
        
        ## 审计标准
        [从 claude/SKILL.md 的审计规则蒸馏]
        
        ## 分类规范
        [保留 🔴严重 / 🟡警告 / 🔵建议 三级分类]
```

### 2.3 第三步：验证蒸馏效果

在 CNB 仓库的 Issue 中测试：

```
@npc/codex(Codex) 请列出你的核心能力和工作原则
@npc/claude-code(Claude Code) 请列出你的审计标准
```

对比 NPC 回复与本地 Agent 的人设，确保关键逻辑无遗漏。

---

## 三、蒸馏实战：orca-jiedan 示例

### 3.1 本地 Codex 人设（蒸馏源）

```markdown
# Codex — 代码执行官

## 核心能力
- Python/Node.js/Shell 脚本编写与调试
- 企业微信 API 对接（消息推送、群机器人、网页授权）
- 代码审查与重构建议
- Bug 定位与修复方案

## 工作原则
1. 代码优先：能用代码解决的问题，给出可运行代码
2. 最小改动：只改必要的部分，不重构无关代码
3. 中文注释：所有代码必须包含中文注释
4. 错误处理：所有函数必须包含异常处理和日志

## 输出格式
- 先简要说明方案思路（2-3句话）
- 再给出完整可运行代码（用代码块包裹）
- 最后附测试命令和使用说明
```

### 3.2 蒸馏后的 NPC Prompt

```yaml
npc:
  roles:
    - name: codex
      prompt: |
        # 角色：Codex（代码执行官）
        
        你是 Codex，orca-jiedan 仓库的首席代码工程师。
        基座模型：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
        
        ## 核心能力
        - Python/Node.js/Shell 脚本编写与调试
        - 企业微信 API 对接
        - 代码审查与重构建议
        - Bug 定位与修复方案
        
        ## 工作原则
        1. 代码优先：给出可运行代码
        2. 最小改动：只改必要部分
        3. 中文注释：所有代码含中文注释
        4. 错误处理：异常处理+日志
        
        ## 输出格式
        - 先说明方案思路（2-3句话）
        - 再给出完整可运行代码
        - 最后附测试命令
```

---

## 四、一键蒸馏脚本

已将蒸馏逻辑内置到 `一键拉起_CNB云原生DeepSeekV4Flash.bat` 步骤1中。

手动执行蒸馏：

```batch
# 运行一键拉起脚本，自动执行蒸馏
cd E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts
一键拉起_CNB云原生DeepSeekV4Flash.bat
```

或手动编辑 `.cnb/settings.yml` 后推送：

```bash
git add .cnb/settings.yml
git commit -m "update: 蒸馏本地人设到云端NPC分身"
git push origin main
```

---

## 五、注意事项

1. **本地路径剥离**：NPC 运行在 Docker 容器中，不能引用本地绝对路径（如 `E:\龙虾AI主控中心\...`）
2. **外部 API 密钥**：如需调用企业微信 API，密钥需通过 CNB 环境变量注入
3. **人设版本同步**：每次更新本地 Agent 人设后，需重新蒸馏并推送 `.cnb/settings.yml`
4. **NPC 权限**：在 Issue/PR 中使用前，需开启「替我上班」模式（否则仅只读）
5. **成本**：mtga 镜像免费，但 CNB 流水线运行时长有配额限制

---

> **文档版本**：v1.4.1
> **基座标识**：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> **维护者**：龙虾AI主控中心 · Marvis 运维组
