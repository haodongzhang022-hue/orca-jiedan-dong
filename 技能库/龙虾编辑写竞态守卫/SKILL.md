---
name: lobster-edit-race-guard
description: 龙虾编辑写竞态守卫 v1.0。解决「同一文件多处修改时改动静默丢失/EBUSY 抢锁失败」——即「假成功」第 6 形态。提供 edit_guard.py：把 N 处修改收敛为一次内存替换 + 一次原子落盘 + 一次回读逐项断言。零积分、纯 stdlib、Windows 优先。触发词：并行编辑、Edit 丢失、改动没生效、EBUSY、写竞态、假成功、回读校验、原子写入。
version: 1.0.0
agent_created: true
cost_mode: zero
---

# 龙虾编辑写竞态守卫 v1.0

> 汤小龙自研 · 2026-09-16 · 零积分（纯 Python stdlib）
> 脚本：`scripts/edit_guard.py`

## 一、这个技能解决什么

**症状（假成功 第 6 形态）**：
- 对**同一个文件**连续/并行发多个编辑调用
- 工具**全部返回 success**，但回读发现**部分改动没落盘**
- 或其中某个报 `EBUSY: resource busy or locked`，且**不会自动重试**

**根因**：编辑是 read-modify-write 三步，非原子。
多个写者并发时：后写的基于旧副本覆盖先写的（静默丢失），或抢锁失败（显式 EBUSY）。
这两种都不算崩、不算错，所以自动化里最容易被当成「已完成」。

**实测证据（2026-09-16 受控实验）**：

| 实验 | 结果 |
|---|---|
| 同一文件并行发 4 个编辑 | 1 个 `EBUSY` 失败（`version` 未改），3 个成功落地 |
| 改用 edit_guard 一次原子应用 4 处 | **4/4 全部落地**，回读断言全通过，EXIT=0 |
| patch 中故意放 1 条不匹配的 old | **拒绝写盘**，原文件 sha256 未变，EXIT=1 |
| 对已丢改动的文件跑 verify | 检出 `new_present: false`，EXIT=1 |

## 二、铁律（强制）

1. **同一文件的多处修改，必须串行单发，发完 Read 回读核实。**
2. **更优解：不要用多次编辑，改用 `edit_guard.py apply --patch patch.json` 一次搞定。**
3. 凡「改完就说完成」的动作，**必须有回读断言**，不能只看工具返回值。
4. 写前必备份（`--no-backup` 仅在你确认可丢时才用）。
5. `old` 文本必须与磁盘**逐字节一致**（空格/换行/全半角）——不一致就在内存阶段拦下，不写盘。

## 三、用法

```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
GUARD="G:/WorkBuddy_Data/skills/lobster-edit-race-guard/scripts/edit_guard.py"

# 1) 原子应用多处修改（推荐，替代连续多次 Edit）
"$PY" "$GUARD" apply <file> --patch patch.json

# 2) 只回读校验（不写盘）
"$PY" "$GUARD" verify <file> --patch patch.json

# 3) 指纹（sha256/行数/编码/换行）
"$PY" "$GUARD" fingerprint <file>

# 4) 探测文件是否被占用
"$PY" "$GUARD" locktest <file>
```

### patch.json 格式

```json
{
  "edits": [
    {"old": "version: 0.0.0", "new": "version: 1.0.0"},
    {"old": "alpha: AAAA",    "new": "alpha: ALPHA", "count": 1}
  ],
  "assert_old_absent": true
}
```

- `count`：期望替换次数，默认 1；**0 = 替换所有**。
- `assert_old_absent`：默认 true，断言 old 文本已消失。

### 常用开关

| 开关 | 作用 |
|---|---|
| `--no-backup` | 不建 `.bak_时间戳` 备份（默认建） |
| `--force` | 文件被占用时仍强制 `os.replace`（通常仍成功） |
| `--partial` | 允许部分条目未匹配也写盘（默认拒绝，保护原文件） |
| `--report <path>` | 把 JSON 报告落盘，供自动化判定 |

### 退出码

| 码 | 含义 |
|---|---|
| 0 | 全部断言通过 |
| 1 | 有断言未通过（**改动没落地或部分丢失**） |
| 2 | 用法/文件错误 |

## 四、设计要点（为什么它不会丢改动）

1. **单次落盘**：所有替换在内存一次性完成，只 write 一次 → 从根上消灭竞态。
2. **原子替换**：同目录临时文件 + `os.replace()`（Windows 原子）。
3. **写前锁探测**：`os.open(O_RDWR)` 探 5 次，被占用则先报，不硬撞。
4. **回读逐项断言**：写后重新读盘，逐条校验 `new` 在、`old` 不在。
5. **编码/换行保持**：自动检测 BOM（utf-8-sig / utf-8 / gbk 兜底）与 CRLF/LF，写回保持一致
   —— 顺带防住「编辑工具把 LF 悄悄改成 CRLF」这类换行风格漂移。

## 五、什么时候不要用它

- 改动**互相依赖**（前一条的 new 是后一条的 old）时，patch 里的 old 要写**磁盘原文**，不是中间态。
- 超大文件（>100MB）全量读写较慢，改用流式方案。
- 二进制文件不适用。

## 六、与其他守卫的关系

| 守卫 | 防的形态 |
|---|---|
| `python_runtime_guard.py` | 假成功 第 4 形态（Python 崩，任务空转） |
| `guard_receipt.py` | 假成功 通用回执（跑没跑、结果如何） |
| **`edit_guard.py`（本技能）** | **假成功 第 6 形态（改动静默丢失 / EBUSY）** |

## 七、版本历史

- **v1.0.0**（2026-09-16）：首版。apply / verify / fingerprint / locktest 四命令；
  原子写 + 备份 + 回读断言 + 编码换行保持；受控实验四场景全通过。
