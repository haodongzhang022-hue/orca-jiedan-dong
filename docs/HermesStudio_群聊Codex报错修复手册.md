# Hermes Studio 群聊 Codex 报错修复手册（unknown variant max）

> 版本：v1.0 ｜ 日期：2026-08-10 ｜ 关联：Issue #27（Hermes Studio 落地排障）
> 执行者：汤嘉锋 或 MARVIS（本地 Windows 本机）

---

## 一、报错现象（图2 实测原话）

```
Error: Codex exited with code 1: Error: failed to parse model_catalog json
path c:\users\administrator\.hermes-web-ui\coding-agent\model\default\xiaomi\codex\
group-chat\<房间ID>\<会话ID>\codex-model-catalog.json as JSON:
unknown variant max, expected one of none, minimal, low, medium, high, xhigh
```

**结论一句话**：Hermes Studio 给群聊 Codex 生成的模型目录里把**推理强度写成了 `max`**，而内置 Codex 只认 `none / minimal / low / medium / high / xhigh` 六档，`max` 不在枚举里，JSON 解析失败 → Codex 直接退出。

---

## 二、为什么会这样（不怪你）

- Hermes Studio（hermes-studio.ai v0.6.39）群聊功能会自动给每个会话房间生成一个 `codex-model-catalog.json`，用来描述 Codex 在群聊里可用的模型与推理档位；
- 生成器把 `default_reasoning_level` / `supported_reasoning_levels[].effort` 写成了 `max`；
- 但群聊内置的 Codex CLI 版本枚举里**没有 `max`**，只有六档 → 解析即失败。

**影响范围**：只影响 **Hermes Studio 群聊里的 Codex Agent** 启动；Hermes 主 Agent、Claude 群聊、以及本地其它 Codex 终端不受影响。

---

## 三、修复方式（二选一）

### 方式 A：一键脚本（推荐，MARVIS 可全自动）

在 Git Bash / WSL 里执行：

```bash
bash scripts/fix_codex_model_catalog.sh                 # 全自动修复所有 catalog
bash scripts/fix_codex_model_catalog.sh --dry-run       # 只扫描不修改，先看结果
bash scripts/fix_codex_model_catalog.sh --clear-cache   # 修复后同时清理损坏的群聊缓存
```

脚本动作（全部只动 `~/.hermes-web-ui` 下的 JSON，零密钥）：

1. 扫描 `~/.hermes-web-ui` 下所有 `codex-model-catalog.json`（含历史群聊房间）；
2. 把推理档位 `max` 改写为 `xhigh`（合法档位中最接近 max 语义）；
3. 自动备份原文件为 `*.bak.<时间戳>`，可回滚；
4. `--clear-cache` 额外清掉 `group-chat` 下的损坏缓存（重新拉起时自动重建）。

### 方式 B：手动改（不想跑脚本）

1. 打开文件管理器，进入 `C:\Users\Administrator\.hermes-web-ui\coding-agent\model\default\xiaomi\codex\group-chat\`；
2. 找到报错里提示的那个 `codex-model-catalog.json`（也可全目录搜索 `codex-model-catalog.json`）；
3. 用记事本打开，把文件里所有 `"max"` 改成 `"xhigh"`（注意别改其它值）；
4. 保存后，回到 Hermes Studio 群聊重新拉起 Codex。

---

## 四、修复后验证

1. Hermes Studio 群聊房间里重新 `@Codex`（或点房间里的 Codex 卡片）；
2. 不再出现 `unknown variant max` 报错，Codex 正常进入群聊；
3. 若房间反复报错：先执行 `--clear-cache` 清理一次，再重开房间。

---

## 五、预防 & 长期对策

| 层面 | 动作 |
|------|------|
| 立即可做 | 脚本已入库 `scripts/fix_codex_model_catalog.sh`，MARVIS 计划任务可定期跑一次（幂等） |
| 群聊建模 | 建议 Hermes Studio 群聊 Codex 使用 `xhigh` 或 `high`，不要手工选 `max` |
| 上报官方 | 该问题属于 Hermes Studio v0.6.39 群聊生成器的 bug（产出非法枚举），可向 hermes-studio.ai 提 issue 要求生成合法档位 |
| 与云上无关 | 云端 NPC（@codex）走的是 CNB 一次性容器路径B，不经过本机 `~/.hermes-web-ui`，**不受此问题影响**，本修复只针对本地桌面版群聊 |

---

## 六、本机修复记录（回滚入口）

- 备份文件：`<catalog>.bak.<时间戳>`，与修复文件同目录；
- 回滚：把 `.bak` 改回原名即可（或 `cp` 覆盖回去）。
