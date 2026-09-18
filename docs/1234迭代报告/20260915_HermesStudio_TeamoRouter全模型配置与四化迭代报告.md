# 2026-09-15 · Hermes Studio 接入 TeamoRouter 全模型与四化迭代报告

> 执行时间：2026-09-15 00:34:38  
> 触发：启用汤小龙 + 调用 1234 + 四化迭代知识库 + 轻量快照  
> 结论：Hermes Studio 已新增 TeamoRouter 全模型 provider；默认模型为免费 `deepseek-v4-flash-free`；原配置已备份，YAML 校验通过。

## 一、模型配置结果

- 新增 provider：`teamorouter-all-models`
- 增补专用 provider：`deepseek-v4.1-flash-free`，默认模型 `deepseek-flash-free`，用于在 Hermes Studio 下拉框中直接暴露 DeepSeek V4.1 Flash福利版
- Base URL：`https://teamorouter.cn/v1`
- 认证方式：`api_key_env: TEAMOROUTER_API_KEY`
- 默认模型：`deepseek-v4-flash-free`
- 模型总数：41 个
- 成本排序：免费/福利版优先，其次 0.01 折福利版，然后按可用性纳入付费与多模态备用模型
- 配置落点：`C:\Users\Administrator\.hermes\config.yaml`

### 关键模型顺序

1. `deepseek-v4-flash-free` — DeepSeek V4 Flash福利版（免费，默认）
2. `deepseek-flash-free` — DeepSeek V4.1 Flash福利版（免费）
3. `glm-5.3-flash-free` — GLM 5.3 Flash福利版（0.01 折）
4. `deepseek-flash` — DeepSeek V4.1 Flash（付费）
5. `deepseek-v4-flash` — DeepSeek V4 Flash（付费）
6. `deepseek-v4-flash-vision-exp` — DeepSeek V4 Flash Vision Exp
7. `deepseek-v4-pro` — DeepSeek V4 Pro
8. 其余 GLM / Kimi / GPT / Claude / Gemini / Grok / 图像模型已一并纳入备用

## 二、验证结果

| 项目 | 结果 |
|---|---|
| YAML 语法 | PASS |
| provider 存在 | PASS |
| 默认模型存在 | PASS |
| `deepseek-v4-flash-free` 出字探针 | PASS |
| `deepseek-flash-free` 探针 | PASS，64-token 探针正常出字 |
| `glm-5.3-flash-free` 探针 | PASS，64-token 探针正常出字 |
| `deepseek-v4-pro-free` 探针 | HTTP 400，不纳入 |
| 本地 15740 / 18091 / 15721 / 15730 | PASS |
| Hermes Studio 原有 provider | 未改动 |
| Hermes Studio 重载 | PASS，2026-09-15 01:28:51 后进程已重启加载新配置 |

## 三、安全与回滚

- 修改前备份：`C:\Users\Administrator\.hermes\config.yaml.bak_teamorouter_20260915_002200`
- 备份 SHA256：`8C5F6EE58BE3D1338DDCC75AD3645B7ED3C847FB82D259F65DE6DF2BF4D8449A`
- 修改原则：只新增 provider，不覆盖原有 provider；密钥不入脚本与报告。
- 回滚方式：用上述备份文件覆盖 `C:\Users\Administrator\.hermes\config.yaml`，重启 Hermes Studio。

## 四、四化落地

| 维度 | 结果 |
|---|---|
| 标准化 | 使用 1234 v2.2 标准执行包；模型清单、排序、回滚路径和验证口径固定 |
| 模块化 | TeamoRouter 独立 provider，不影响原有 AtomCode / CNB / DeepSeek / MiMo provider |
| 自动化 | `TEAMOROUTER_API_KEY` 走用户环境变量；后续可由守卫脚本校验 provider 与默认模型 |
| 智能化 | 默认锁定免费模型，避免误用高折率模型；付费模型仅作显式备用 |

## 五、六端归档状态

| 端 | 状态 | 说明 |
|---|---|---|
| Obsidian | PASS | 快照包与说明页已落盘 |
| IMA | PENDING | 已获用户授权，待连接器在线后上传报告或快照摘要 |
| 乐享 | PENDING | 已获用户授权，待连接器在线后上传报告或快照摘要 |
| CNB | PASS | 报告已推送至干净分支 `codex/hermes-studio-teamorouter-20260915` |
| GitHub | PENDING | 直连两次 `Connection was reset`，代理通道 403；分支待复推 |
| WorkBuddy | PASS | 本地记忆层已补记配置、快照与校验结果 |

## 六、技能回馈报告

1. **积分消耗**：本地配置与验证为主，仅 TeamoRouter 少量免费/福利模型探针，估算 0 积分；不包含外部计费模型推理。
2. **解决问题**：把 TeamoRouter 免费福利版、0.01 折模型和截图中的 DeepSeek V4.1 / V4 / GLM / Kimi 等模型统一接入 Hermes Studio，并锁定免费默认。
3. **沉淀技能**：本报告 + 轻量快照 + 回滚说明 + 后续可复用的 provider 配置口径。
4. **主要技能**：`20260825_1234快捷体系_官方定义卡.md` 与 `四化迭代六端归档铁律_SKILL.md`。
5. **未用技能**：`分身之眼企微接单全自动化`、`仓颉Skill知识蒸馏技能`、`赛博书屋`；因为本次不是接单、不是新书蒸馏，也不是全网页资料萃取，走 1234-4 运维沉淀更短。

## 七、快照

### 快照产物

- 路径：`G:\龙虾AI主控中心\Obsidian\snapshots\HermesStudio_TeamoRouter_20260915\HermesStudio_TeamoRouter_20260915.zip`
- 大小：`17635658` bytes（16.82 MB）
- 大小：`17636283` bytes（16.82 MB）
- SHA256：`8CC9312BC0045DA021535440FF7C6BBD0F49A226E2E40B963D1CDE79509E5F04`
- 内容范围：
  - 企业微信群定制接单项目 Git 已跟踪文件基线
  - Hermes Studio 当前配置与修改前备份
  - 1234 v2.2 官方定义卡
  - 本次四化迭代报告
  - `PROJECTS_INDEX.txt`
  - `RESTORE.py`
  - `MANIFEST.json`

### 回滚校验

```powershell
python RESTORE.py --verify
```

实测结果：`PASS`，包内清单文件逐项哈希一致。

### 回滚步骤

```powershell
python RESTORE.py --rollback
```

该命令会先把当前 Hermes 配置另存为 `.before_rollback`，再恢复修改前配置。若需要项目文件回滚，再解压包内 `project_tracked_baseline.tar.gz`。
