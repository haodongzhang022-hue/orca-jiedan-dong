---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: cf54d54c59baa0ada35a5ecb7c73a584_66ee3c0c914511f1a102525400826444
    ReservedCode1: yA2BwoGkktF7VuqH3wtblNcwV1IwqPKOBuI7YQg7PC/QGLwkezy34a1DaiH6qSQ7Wd4mAJJZmxJJlL3ZB4aJnOp6JvQsUApYwwsedSGcAOihWt2sKFr74O2wj094FgDvk9P9RpIBS4Kc5LBhB12NU8WLw2xCM7T+MdrE9MfuFS1Lq4/4xoNpnyAXbqQ=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: cf54d54c59baa0ada35a5ecb7c73a584_66ee3c0c914511f1a102525400826444
    ReservedCode2: yA2BwoGkktF7VuqH3wtblNcwV1IwqPKOBuI7YQg7PC/QGLwkezy34a1DaiH6qSQ7Wd4mAJJZmxJJlL3ZB4aJnOp6JvQsUApYwwsedSGcAOihWt2sKFr74O2wj094FgDvk9P9RpIBS4Kc5LBhB12NU8WLw2xCM7T+MdrE9MfuFS1Lq4/4xoNpnyAXbqQ=
---

# DeepSeek双架构脚手架完整验收报告

> 版本：1.4.1 | 更新日期：2026-08-06
> 基座：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> 覆盖仓库：orca-jiedan / orca-wangpan / orca-xianyu / orca-quant-jiasheng / orca-quant-binance / orca（主空仓）

---

## 一、架构全景

```
                        ┌─────────────────────────┐
                        │   企业微信群接单需求     │
                        └───────────┬─────────────┘
                                    │
                        ┌───────────▼─────────────┐
                        │    Hermes 消息监听层     │
                        │    (事件绑定 / 任务卡分流)│
                        └─────┬─────────────┬─────┘
                              │             │
              ┌───────────────▼──┐   ┌──────▼──────────────┐
              │  本地 Ollama 链路 │   │  CNB 云原生链路      │
              │  (bat#1 一键拉起) │   │  (bat#2 一键拉起)    │
              └───────┬──────────┘   └──────┬──────────────┘
                      │                     │
    ┌─────────────────▼──────┐    ┌─────────▼──────────────────┐
    │ Layer1: Codex 代码执行  │    │ @npc/codex (mtga镜像)      │
    │ Layer2: Claude 代码审计 │    │ @npc/claude-code (mtga镜像)│
    │ Layer3: MIMO 多模态旁路  │    │ @CodeBuddy (系统NPC终审)   │
    └─────────────────────────┘    └────────────────────────────┘
                      │                     │
                      └──────────┬──────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Marvis 双向调度中枢       │
                    │  ├─ Obsidian 知识库归档    │
                    │  ├─ G盘镜像目录同步        │
                    │  └─ 四化闭环标准          │
                    └──────────────────────────┘
```

---

## 二、双架构对比

| 维度 | 本地 Ollama 链路 | CNB 云原生链路 |
|------|------------------|----------------|
| **模型基座** | Ollama DeepSeek-V4-Flash | CNB mtga 镜像内置 V4-Flash |
| **运行环境** | Windows 本地 + Ollama 进程 | CNB Docker 容器 |
| **代码执行** | 原生 Python/Node.js/Shell | Docker 沙箱内执行 |
| **文件访问** | 本地完整文件系统 | 仅仓库内文件 |
| **持续性** | 常驻后台进程（Hermes监听） | 事件触发（Issue/PR评论） |
| **多模态** | MIMO v2.5-Pro 旁路解析 | DeepSeek 无原生识图（需本地MIMO补充） |
| **成本** | 本地GPU/CPU算力 | CNB 免费（至2026-12-31） |
| **人设管理** | worktrees/ 本地文件 | .cnb/settings.yml prompt |
| **版本控制** | 本地 .git | CNB 仓库 |
| **团队协作** | 单机 | 多用户 @ 触发 |

---

## 三、适用场景矩阵

| 场景 | 推荐链路 | 原因 |
|------|---------|------|
| 企业微信群接单 → 代码生成 | 本地 Ollama | 实时监听、完整文件系统 |
| PR 代码审查 | CNB 云端 | 自动触发、多人可见 |
| Issue 问答/方案建议 | CNB 云端 | 公开透明、存档可查 |
| 海报/漫剧图片识别 | 本地 Ollama + MIMO | DeepSeek 无原生识图 |
| 批量文件整理/重命名 | 本地 Ollama | 需要完整文件系统 |
| 多仓库统一配置更新 | CNB 云端 | 跨仓库流水线 |
| 离线环境 | 本地 Ollama | 不依赖网络 |
| 移动端远程调度 | CNB 云端 | 浏览器即可操作 |

---

## 四、全仓库批量更新清单

| 仓库 | 更新内容 | 状态 |
|------|---------|------|
| orca-jiedan | 基座 mimo-v2.5-pro → deepseek-v4-flash | ✅ 已完成 |
| orca-wangpan | 基座 mimo-v2.5-pro → deepseek-v4-flash | ⏳ 待执行 |
| orca-xianyu | 基座 mimo-v2.5-pro → deepseek-v4-flash | ⏳ 待执行 |
| orca-quant-jiasheng | 基座 mimo-v2.5-pro → deepseek-v4-flash | ⏳ 待执行 |
| orca-quant-binance | 基座 mimo-v2.5-pro → deepseek-v4-flash | ⏳ 待执行 |
| orca（主空仓） | 基座配置初始化 | ⏳ 待执行 |

**更新约束**：
- 仅替换基座模型标识，不动业务架构
- Hermes/Codex/Claude 三层分工 → 保留
- 事件绑定（issue.comment@npc / pull_request.comment@npc）→ 保留
- 三工作树（worktrees/）→ 保留
- fleet_exchange 任务流转 → 保留
- Marvis 分发逻辑 → 保留

---

## 五、交付物清单

| 序号 | 交付物 | 路径 | 类型 |
|------|-------|------|------|
| 1 | 一键拉起_Ollama本地DeepSeekV4Flash.bat | scripts/ | Windows 批处理脚本 |
| 2 | 一键拉起_CNB云原生DeepSeekV4Flash.bat | scripts/ | Windows 批处理脚本 |
| 3 | 本地Agent人设蒸馏至云端NPC操作指南.md | docs/ | 操作文档 |
| 4 | .cnb.yml（NPC流水线） | 仓库根目录 | CNB 配置 |
| 5 | .cnb/settings.yml（NPC角色） | .cnb/ | CNB 配置 |
| 6 | DeepSeek双架构脚手架完整验收报告.md | docs/ | 本文档 |

---

## 六、限制与已知问题

| 问题 | 影响范围 | 缓解方案 |
|------|---------|---------|
| DeepSeek 无原生识图能力 | 云端 NPC 无法处理图片 | 本地 MIMO 旁路解析 → 文本传给 DeepSeek |
| Ollama 未在 PATH 中 | 本地链路启动失败 | 脚本内置多路径智能扫描 |
| Claude Code CLI 未安装 | 本地 Claude 链缺失 | 脚本自动降级提示 npx 安装方式 |
| G盘未挂载 | 云端产出无法镜像到本地 | 脚本检测后提示手动挂载 |
| NPC 流水线首次冷启动慢 | 首次 @ 触发需 30-60s | 正常现象，后续热缓存更快 |
| mtga 社区镜像配额 | 大量并发调用可能限流 | 控制 @ 频率，高峰期用本地链路 |

---

## 七、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.4.0 | 2026-08-04 | 初始脚手架 orca_fleet_scaffold_v1.4 |
| 1.4.1 | 2026-08-06 | 基座切换 DeepSeek-V4-Flash；拆分双架构链路；新增NPC蒸馏指南 |

---

> **基座标识**：CNB免费DeepSeek-V4-Flash（有效期至2026-12-31）
> **维护者**：龙虾AI主控中心 · Marvis 运维组
> **四化闭环**：标准化 → 流程化 → 自动化 → 智能化
*（内容由AI生成，仅供参考）*
