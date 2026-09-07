---
title: Codex配置漂移溯源与守卫_SKILL
version: v1.0
author: 汤小龙（AI分身）
date: 2026-09-08
tags: [Codex, TeamoRouter, 成本红线, 漂移溯源, 二进制取证, 零积分]
cost_mode: P0-本地零积分
---

# Codex config.toml 模型漂移溯源与守卫 v1.0

> 一句话：**`config.toml` 的 model 每天被 TeamoRouter 客户端覆写，不是灵异事件；env 三件套才是真正兜底，守卫负责双保险。**

---

## 一、现象

每天巡检发现 `C:\Users\Administrator\.codex-orch\config.toml` 的 `model` 行变成陌生值，且**每天一个新名字**：

| 日期 | 被写入的 model | 真实后端 |
|---|---|---|
| 2026-08-29 | `gpt-5.6-terra` | 未知 |
| 2026-09-06 | `gpt-5.6-sol` | 未知 |
| 2026-09-07 08:55 | `gpt-6-astra` | 未知（不在白名单） |
| 2026-09-07 18:48 | `gpt-5.6-luna` | glm-5.3-flash-free（0.01折，安全） |

危险点：这些 slug **折率未知**，触碰「切换必报 / 付费须确认」成本红线。

---

## 二、根因（2026-09-08 查实，二进制取证）

### 写入者 A（主因）：TeamoRouter 桌面客户端

- 程序：`C:\Program Files\Teamo\teamorouter-desktop.exe`
- 铁证：在该 exe 二进制中同时检出三个特征串
  - `teamorouter-codex`（config.toml 里的标记块名 `# >>> teamorouter-codex`）
  - `model_catalog_json`
  - `backups_state`
  - 附近还有 Rust 源码路径 `src\codex\config.rs`、`src\codex\catalog.rs`、`src\codex\smoke.rs`
  - 关键日志串：`9 returned a model catalog without priority-capable models`
- 机制：客户端从服务端拉取当日模型目录，选一个 **priority 模型**写入 `# >>> teamorouter-codex` 标记块。供应商每天轮换免费额度 slug，于是每天一个新名字，**旧 slug 次日失效**。

### 写入者 B（次因）：Codex 桌面版升级

- 判据：一次改动里同时出现
  - `ChatGPT.exe` 版本 `26.901.5280.0` → `26.901.6511.0`
  - `cua_node` 运行时 hash 变化、`SKY_CUA_NATIVE_PIPE_DIRECTORY` 换新 UUID
  - `openai_base_url` 从 `https://api.teamorouter.cn/v1` 改回 `http://127.0.0.1:51427/v1`
- 性质：WindowsApps 版 Codex 自升级后重写整个 config，属正常行为，但会连带改动 base_url。

### 排除的嫌疑人

- `codex-plus-plus-manager.exe` / `codex-plus-plus.exe`（`E:\龙虾AI主控中心\tools\Codex++\`）：只检出 `backups_state`，**无** `teamorouter-codex` 标记块串 → 非写入者。

---

## 三、溯源方法论（可复用四步，零积分）

1. **备份序列差分**：`grep '^model = ' config.toml config.toml.bak*` + 按 mtime 排序 → 拿到漂移时间轴，识别命名规律（同一供应商 slug 体系）。
2. **整文件 diff**：`diff 昨日备份 当前` → 若同时出现 App 版本/cua_node hash 变化，判为「客户端升级重写」；若只变 model 行，判为「供应商轮换」。
3. **二进制搜证（决定性）**：在嫌疑程序里搜**标记块字符串本身**
   ```python
   needles=[b'teamorouter-codex', b'model_catalog_json', b'backups_state']
   # 谁同时含全部三个 = 写入者；只含部分 = 无关
   ```
   再取命中点 ±1200 字节，用 `re.findall(rb'[\x20-\x7e]{6,}', seg)` 提取可读串，能看到源码路径与日志文案。
4. **env 优先级核验**：`winreg` 读 `HKCU\Environment` → 确认 `CODEX_MODEL` / `CODEX_BASE_URL` / `CODEX_HOME` 是否仍正确。**env 优先级高于 config.toml**，env 正确时漂移不产生实际影响。

---

## 四、修复：守卫脚本

`E:\龙虾AI主控中心\MCP服务\codex_model_guard.py`（v1.0，纯标准库，零积分）

功能：
1. 白名单 = `backups_state/teamorouter-fast/model-catalog.json` 动态读取 **减去收费马甲**（`gpt-5.4`/`gpt-5.4-mini`/`gpt-5.5`）∪ 硬编码安全集
2. 命中收费红线或未知 slug → 备份 → 只改 `model` 行 → **绝不动 `wire_api` / `base_url`**（AGENTS.md 红线）
3. 漂移事件写入 `~/.codex-orch/model_drift_events.jsonl`（含时间/旧值/新值/原因），可统计频率
4. 同时校验 env 三件套，env 破了立即告警（此时漂移会真实生效）

用法：
```bash
python codex_model_guard.py          # 检查并修复
python codex_model_guard.py --check  # 只报告不改
```

已注册计划任务 `Lobster_CodexModelGuard`，每 30 分钟一次（Once + RepetitionInterval 30min）。

**实测记录**：注入 `gpt-6-astra` → 自动备份 `config.toml.bak_guard_20260908_061150` → 改回 `gpt-5.6-luna` → 复检通过。

---

## 五、踩坑清单

| # | 坑 | 解法 |
|---|---|---|
| 1 | 全盘 `os.walk` 搜 node_modules 卡死（4 分钟无输出） | 先 `dn[:]=[d for d in dn if d not in skip]` 剪枝；优先只扫嫌疑程序目录 |
| 2 | `wmic` 被安全策略禁用 | PowerShell `Get-Process -Id X \| Select Path,StartTime` |
| 3 | `Register-ScheduledTask` 用 `[TimeSpan]::MaxValue` 作 RepetitionDuration 报「任务 XML 包含格式不正确或超出范围的值」（P99999999DT…） | 改用 `New-TimeSpan -Days 3650` |
| 4 | Bash heredoc 把 `'E:\\x'` 的 `\\` 转成 `//` 导致 replace 失效 | 用 Write 工具落盘 .py 再执行 |
| 5 | 白名单直接信任 catalog 会把收费马甲算成安全 | `return wl - PAID_REDLINE` 显式剔除 |
| 6 | 误判「每天被恶意覆写」 | 实为供应商免费额度 slug 日轮换 + Codex 自升级，属正常机制，只需守卫不需对抗 |

---

## 六、结论与红线

- **不必对抗 TeamoRouter**：它的轮换是免费额度机制，硬改它的程序会造成链路断裂。
- **双保险策略**：env 三件套（优先级高）为第一道，`config.toml` 守卫为第二道。
- **红线不变**：只改 `model` 行；`wire_api`、`base_url` 永不碰；改前必备份。
