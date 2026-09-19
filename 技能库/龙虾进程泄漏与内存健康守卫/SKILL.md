---
name: lobster-mem-guard
description: 龙虾进程泄漏与内存健康守卫。一键扫描物理内存压力、进程实例堆积、单进程内存巨兽，输出红黄绿报告与「只生成不执行」的安全清理 bat；支持趋势采样识别泄漏累积。触发词：卡顿、内存满、进程泄漏、僵尸进程、GptBrowser 太多、内存巡检、机器卡、mem guard、进程清理。
version: 1.0.0
agent_created: true
created: 2026-09-20
source: 2026-09-19「卡顿真凶 = 进程泄漏堆积」实证蒸馏（GptBrowser 78 实例/11.88GB，内存 90%）
distilled_by: 龙虾五步法 V3.6 + 每日自主学习·自进化闭环（第 10 次）
tags: [memory, process-leak, health-guard, zero-cost, windows, stdlib]
---

# 龙虾进程泄漏与内存健康守卫 v1.0

> **触发词**：卡顿 / 内存满 / 进程泄漏 / 僵尸进程 / GptBrowser 太多 / 内存巡检 / 机器卡 / 进程清理
> **成本**：零积分（纯 stdlib：ctypes 取内存 + `tasklist /FO CSV` 取进程）
> **铁律**：**默认只读，绝不自动杀进程**

---

## 一、为什么需要它（2026-09-19 实证）

反复卡顿排查了两轮：先怀疑 G 盘掉盘（Event 153 确实爆发），17:11 复测风暴已停但机器依然卡 ——
**真凶是进程泄漏堆积把内存压到 90%**：

| 进程 | 实例数 | 占用 |
|---|---|---|
| GptBrowser.exe | 78 | 11.88 GB（单进程最高 4.5GB） |
| WorkBuddy.exe | 18 | 2.76 GB |
| 物理内存 | — | 28.6/31.7 GB ≈ 90% |

根因找到了，却**没有工具化**，下一条还得重查一遍。本守卫把这个洞补上。

## 二、与 `ai-workstation-morning-check` 的边界（不重复）

| | morning-check | 本守卫 |
|---|---|---|
| 问的问题 | 组件**在不在**（磁盘/端口/MCP/Chrome/运行时） | 系统**扛不扛得住**（内存压力/泄漏/僵尸实例） |
| 维度 | 七维广度扫描 | 内存+进程纵深 |
| 动作 | 报告 | 报告 + 清理计划 + 趋势采样 |

两者互补：晨检发现「组件缺失」，本守卫发现「资源被吃光」。

---

## 三、快速使用

```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
S="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/scripts/lobster_mem_guard.py"

"$PY" "$S"                      # 体检报告（默认，只读）
"$PY" "$S" --json               # 机器可读，接 guard_receipt
"$PY" "$S" --plan               # 生成清理 bat（不执行）
"$PY" "$S" --trend              # 只看历史趋势
"$PY" "$S" --watch 5 --interval 60   # 采样 5 次判泄漏累积
"$PY" "$S" --apply --i-know-what-i-am-doing   # 真清理（双保险）
```

退出码：`0`=绿/黄，`1`=红（可接告警），`2`=采集失败，`3`=安全闸门拒绝。

---

## 四、判级规则

**内存**：占用率 ≥90% 或 可用 ≤2GB → 🔴；≥80% 或 可用 ≤4GB → 🟡；否则 🟢

**进程实例数**（每进程可配 `yellow / red / keep / killable`）：

| 进程 | 黄 | 红 | 清理保留 | 可杀 |
|---|---|---|---|---|
| GptBrowser.exe | 12 | 30 | 3 | ✅ |
| 360se.exe | 8 | 20 | 2 | ✅ |
| Doubao.exe | 8 | 18 | 2 | ✅ |
| chrome.exe / msedge.exe | 15/12 | 40/30 | 3/2 | ✅ |
| **WorkBuddy.exe** | 12 | 25 | — | ❌ 宿主自身 |
| **python/pythonw/node** | 10 | 25 | — | ❌ MCP 服务 |
| 未登记进程 | 15 | 40 | — | ❌ 只观察 |

**单进程巨兽**：≥1.5GB 点名，≥3GB 判红。

---

## 五、三条安全红线（不容协商）

1. **默认只读**。`--apply` 才动手，且**必须再叠 `--i-know-what-i-am-doing`**，否则硬拒绝（exit 3）。
2. **白名单永不杀**：`WorkBuddy / python / pythonw / node / bash / git / ssh / explorer / svchost / csrss / lsass …`
   （杀宿主 = 自杀式打断会话，09-19 已定性）
3. **保留策略**：按内存降序保留 Top-`keep` 个（视为主窗口/在用标签页），其余判为重复或僵尸。
   ⚠️ 这是启发式，不是保证 —— 首次使用务必先 `--plan` 人工核对 PID 清单。

## 六、系统噪声豁免（防误报）

`svchost.exe / conhost.exe / RuntimeBroker.exe / dllhost.exe / WUDFHost.exe / taskhostw.exe / MsMpEng.exe …`
**天生多实例，一律强制判绿、不参与总评**。

> **踩坑实录**：v1.0 初版把 `svchost.exe` 81 实例判成 🔴，导致总评永远红。
> **守卫一旦误报就没人信了** —— 噪声豁免是守卫可信度的生命线。

---

## 七、踩坑与修复（本次开发实证）

| # | 坑 | 修法 |
|---|---|---|
| 1 | 系统进程多实例 → 误报红 | `SYSTEM_NOISE` 集合强制判绿 |
| 2 | bat 行尾被文本模式二次转换 → 实际落盘 `\r\r\n` | `open(..., newline="\r\n")` + `"\n".join()` |
| 3 | bat 注释含中文 → GBK 控制台乱码/静默失效 | bat 全 ASCII 输出 |
| 4 | 演示 bat 含 71 条真实 `taskkill` PID | 用完立即删除，禁止留在 `backups/` |

## 八、常驻化（建议）

Windows 计划任务，每 30 分钟跑一次 `--json` 并把结果喂 `guard_receipt.py`：

- 任务名 `Lobster_MemGuardProbe`
- 触发：AtLogOn + 每 30 分钟
- 动作：`python.exe scripts\lobster_mem_guard.py --json > logs\mem_guard_$(date).json`
- 连续 3 次 RED → 弹窗告警（`guard_alert.py`）

## 九、实测记录

2026-09-20 06:05 首跑：内存 74%（可用 8.1GB，🟢），进程 312 个 / 90 种，
**GptBrowser 54 实例 5.84GB 🔴（单进程 2.27GB）**，WorkBuddy 18 实例 3.25GB 🟡，
清理计划预计释放 **1.87GB**（61 个进程）。趋势采样 4 次 load 73→74%，判定平稳。
