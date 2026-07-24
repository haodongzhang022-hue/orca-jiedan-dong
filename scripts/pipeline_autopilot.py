#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 流水线自动驾驶 + 看板数据生成

职责：
1. 扫描 fleet_exchange / 项目 outputs / 企业微信群 deliverables 状态
2. 自动推进 PILOT-001 及后续任务：
   Hermes 完成 → 推 _Codex_ 任务
   Codex 完成 → 推 _CloudCode_ 任务
   CloudCode 完成 → 汇总最终交付物到 企业微信群/定制接单项目/deliverables/
3. 生成 dashboard/dashboard_data.json 供看板实时刷新

运行：
    python scripts/pipeline_autopilot.py

WorkBuddy 自动化建议：每 30 秒执行一次
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
HOME = Path("E:/龙虾AI主控中心/我的AI分身")
PROJECT = HOME / "企业微信群定制接单项目"
WECHAT = HOME / "企业微信群" / "定制接单项目"

FLEET = HOME / "多智能体舰队编排" / "fleet_exchange"
FLEET_IN = FLEET / "incoming"
FLEET_DOING = FLEET / "doing"
FLEET_RESULTS = FLEET / "results"
FLEET_LOGS = FLEET / "logs"

PENDING_DIR = PROJECT / "待分发任务"        # 当沙箱无法写 FLEET_IN 时 fallback
DASHBOARD_DIR = WECHAT / "任务看板"         # 看板 HTML + JSON 目录
OUTPUTS_DIR = PROJECT / "outputs"
DELIVERABLES_DIR = WECHAT / "deliverables"

LOG_FILE = PROJECT / "logs" / "pipeline_autopilot.log"

# 确保目录存在
for d in [PROJECT / "logs", PENDING_DIR, DASHBOARD_DIR, OUTPUTS_DIR, DELIVERABLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# 工具函数
# ============================================================
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_frontmatter(path: Path) -> dict:
    """读取 task 文件顶部的 YAML-like frontmatter"""
    text = ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = parts[1].strip()
    data = {}
    for line in fm.splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def list_tasks(directory: Path) -> list:
    """列出目录里的 .md 任务文件，按修改时间排序"""
    if not directory.exists():
        return []
    files = [f for f in directory.iterdir() if f.is_file() and f.suffix == ".md"]
    files.sort(key=lambda x: x.stat().st_mtime)
    return files


def agent_tag(filename: str) -> str | None:
    """从文件名识别 Agent：_Hermes_ / _Codex_ / _CloudCode_"""
    if "_Hermes_" in filename:
        return "Hermes"
    if "_Codex_" in filename:
        return "Codex"
    if "_CloudCode_" in filename:
        return "CloudCode"
    return None


def find_result_for_task(task_id: str, agent: str) -> Path | None:
    """在 results/ 找某 task_id + agent 的结果文件"""
    if not FLEET_RESULTS.exists():
        return None
    candidates = [f for f in FLEET_RESULTS.iterdir()
                  if f.is_file() and f.suffix == ".md"
                  and task_id in f.name and agent_tag(f.name) == agent]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def find_task_in_dirs(task_id: str, agent: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.suffix == ".md" and task_id in f.name and agent_tag(f.name) == agent:
                return f
    return None


def write_file_atomically(path: Path, content: str) -> bool:
    """写文件，失败返回 False"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        log(f"写文件失败: {path} -> {e}")
        return False


# ============================================================
# 任务模板
# ============================================================

def make_codex_task(task_id: str, design_brief_path: Path | str) -> str:
    return f"""---
task_id: {task_id}
from: WorkBuddy
to: Codex
priority: high
context: PILOT-001 企业微信群定制接单项目 · 执行层（由 Hermes design_brief 驱动）
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: true
real_order_min: 300
---

# 任务：{task_id} Codex 执行层 — 摇滚风宣传海报生成

> ⚠️ 模拟演练卡：仅内部跑通流水线，不对外交付成品。

## 输入
- Hermes 设计简报：`{design_brief_path}`
- 参考海报：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-791Z-6d054157.jpg`
- 需求截图：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-795Z-748564f5.png`

## 交付要求
1. 读取 design_brief 中的风格关键词、版式层级、文案槽位。
2. 生成 **2~3 版**海报方案：
   - 每版附文生图 prompt（中文或英文）
   - 尺寸（竖版 3:4 或 9:16，≥1024px 宽）
   - 生成消耗估算（token / 积分 / 时间）
3. 输出形式：
   - 可直接生成图片（若本地模型/多模态工具可用）
   - 或输出 HTML/SVG 排版稿 + 文案
4. 演练优先走低成本推理（mimo-bridge / ollama-bridge），不烧 Hy3 积分；若确需多模态生成，记录消耗。
5. 产出：
   - `poster_drafts.md` 落盘 `E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/pilot_task_001/`
   - 结果摘要写回 `fleet_exchange/results/{task_id}__Codex_...__result_<时间>.md`

## 合规红线
- 只借鉴风格（红黑/Grunge/电吉他/摇滚字体），禁止直接复制参考海报的素材、字体文件、乐队名、Logo。
- 演练产出标注「内部模拟，不对外交付」。

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" \
  "<WORKING_FILE>" \
  "Codex 海报方案已产出，等待 WorkBuddy 转交 CloudCode"
```
"""


def make_cloudcode_task(task_id: str, design_brief_path: str, codex_result_path: Path | str) -> str:
    return f"""---
task_id: {task_id}
from: WorkBuddy
to: CloudCode
priority: high
context: PILOT-001 企业微信群定制接单项目 · 终审核查（由 Codex 海报方案驱动）
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: true
real_order_min: 300
---

# 任务：{task_id} CloudCode 核查层 — 海报质量/合规/成本终审

> ⚠️ 模拟演练卡：仅内部跑通流水线，不对外交付成品。

## 输入
- Hermes 设计简报：`{design_brief_path}`
- Codex 海报方案：`{codex_result_path}`
- 参考海报：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-791Z-6d054157.jpg`

## 交付要求
1. 按设计简报逐项验收 Codex 产出。
2. 质量审查：
   - 风格还原度（红黑/Grunge/电吉他/摇滚字体感）
   - 构图、可读性、标题层级、文案槽位是否到位
   - 三版中择优，给出理由与修改建议
3. 合规审查：
   - 是否存在直接复制原海报素材、字体文件、乐队名、Logo 的侵权风险
   - 是否属于「风格借鉴」而非「素材复刻」
   - 是否需补充「原创设计，风格参考样例」声明
4. 成本审查：
   - 汇总 Hermes + Codex 实际消耗（token/积分/时间）
   - 与演练估值 ¥30~80 对比，给出毛利结论（模拟不计真实报价）
   - 对真实付费单（¥300 起）的成本覆盖建议
5. 产出：
   - `review_report.md` 落盘 `E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/pilot_task_001/`
   - 结果摘要写回 `fleet_exchange/results/{task_id}__CloudCode_...__result_<时间>.md`

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" \
  "<WORKING_FILE>" \
  "CloudCode 终审完成，等待 WorkBuddy 汇总"
```
"""


# ============================================================
# 主逻辑
# ============================================================

def main():
    log("=== pipeline_autopilot 启动 ===")

    # 1. 扫描所有任务
    incoming = list_tasks(FLEET_IN)
    doing = list_tasks(FLEET_DOING)
    results = list_tasks(FLEET_RESULTS)
    pending = list_tasks(PENDING_DIR)

    # 2. 任务状态表
    tasks = {}

    # 识别 PILOT-001（现有文件名缺 _Hermes_，但 frontmatter 有 to:Hermes）
    pilot_id = "20260725_014500_0"
    pilot_incoming = [f for f in incoming if pilot_id in f.name]
    if pilot_incoming:
        pilot_file = pilot_incoming[0]
        fm = read_frontmatter(pilot_file)
        tasks[pilot_id] = {
            "task_id": pilot_id,
            "title": "PILOT-001 摇滚风宣传海报（模拟演练）",
            "simulation": True,
            "incoming": [str(f) for f in pilot_incoming],
            "doing": [str(f) for f in doing if pilot_id in f.name],
            "results": {a: str(find_result_for_task(pilot_id, a)) if find_result_for_task(pilot_id, a) else None
                        for a in ["Hermes", "Codex", "CloudCode"]},
            "frontmatter": fm,
        }

    # 3. 自动推进：检查 Hermes 是否完成，若无 Codex 任务则创建
    state = tasks.get(pilot_id, {})
    hermes_done = state.get("results", {}).get("Hermes") is not None
    codex_task = find_task_in_dirs(pilot_id, "Codex", [FLEET_IN, FLEET_DOING, PENDING_DIR])
    cloudcode_task = find_task_in_dirs(pilot_id, "CloudCode", [FLEET_IN, FLEET_DOING, PENDING_DIR])

    design_brief_path = OUTPUTS_DIR / "pilot_task_001" / "design_brief.md"

    if hermes_done and not codex_task and not state.get("results", {}).get("Codex"):
        codex_filename = f"{pilot_id}__Codex_PILOT_企业微信群定制海报_摇滚风宣传海报.md"
        codex_path = FLEET_IN / codex_filename
        content = make_codex_task(pilot_id, design_brief_path)
        if write_file_atomically(codex_path, content):
            log(f"已创建 Codex 任务: {codex_path}")
        else:
            fallback = PENDING_DIR / codex_filename
            if write_file_atomically(fallback, content):
                log(f"FLEET_IN 写入失败，已写入待分发: {fallback}")

    codex_result = find_result_for_task(pilot_id, "Codex")
    if codex_result is not None and not cloudcode_task and not state.get("results", {}).get("CloudCode"):
        cloudcode_filename = f"{pilot_id}__CloudCode_PILOT_企业微信群定制海报_摇滚风宣传海报.md"
        cloudcode_path = FLEET_IN / cloudcode_filename
        content = make_cloudcode_task(pilot_id, str(design_brief_path), codex_result)
        if write_file_atomically(cloudcode_path, content):
            log(f"已创建 CloudCode 任务: {cloudcode_path}")
        else:
            fallback = PENDING_DIR / cloudcode_filename
            if write_file_atomically(fallback, content):
                log(f"FLEET_IN 写入失败，已写入待分发: {fallback}")

    # 4. CloudCode 完成 → 汇总交付物到企业微信群/deliverables
    cloudcode_result = find_result_for_task(pilot_id, "CloudCode")
    if cloudcode_result is not None:
        deliverable_dir = DELIVERABLES_DIR / "pilot_task_001"
        deliverable_dir.mkdir(parents=True, exist_ok=True)
        # 复制关键结果
        copied = []
        for src in [cloudcode_result, codex_result, find_result_for_task(pilot_id, "Hermes")]:
            if src and src.exists():
                dst = deliverable_dir / src.name
                try:
                    shutil.copy2(src, dst)
                    copied.append(dst.name)
                except Exception as e:
                    log(f"复制交付物失败: {src} -> {e}")
        # 复制生成的海报文件（假设 outputs/pilot_task_001/ 下有图片）
        pilot_out = OUTPUTS_DIR / "pilot_task_001"
        if pilot_out.exists():
            for f in pilot_out.iterdir():
                if f.is_file():
                    try:
                        shutil.copy2(f, deliverable_dir / f.name)
                        copied.append(f.name)
                    except Exception as e:
                        log(f"复制 outputs 失败: {f} -> {e}")
        if copied:
            log(f"已汇总交付物到 {deliverable_dir}: {copied}")

    # 5. 生成看板数据
    dashboard_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": str(PROJECT),
        "wechat_deliverables": str(DELIVERABLES_DIR),
        "fleet_incoming": [f.name for f in incoming],
        "fleet_doing": [f.name for f in doing],
        "fleet_results": [f.name for f in results],
        "pending_tasks": [f.name for f in pending],
        "pilot_001": {
            "task_id": pilot_id,
            "simulation": True,
            "hermes": {
                "done": hermes_done,
                "result_file": state.get("results", {}).get("Hermes"),
                "task_file": state.get("incoming", [None])[0],
            },
            "codex": {
                "task_exists": bool(codex_task),
                "done": codex_result is not None,
                "result_file": str(codex_result) if codex_result else None,
            },
            "cloudcode": {
                "task_exists": bool(cloudcode_task),
                "done": cloudcode_result is not None,
                "result_file": str(cloudcode_result) if cloudcode_result else None,
            },
            "deliverables_dir": str(DELIVERABLES_DIR / "pilot_task_001"),
        },
        "actions": []
    }

    # 6. 待分发任务提示
    if pending:
        dashboard_data["actions"].append({
            "level": "warning",
            "text": f"有 {len(pending)} 个任务卡在待分发目录（沙箱无法直接写 fleet_exchange/incoming），请运行同步脚本：bash scripts/sync_to_fleet.sh"
        })

    # 7. 保存 JSON
    json_path = DASHBOARD_DIR / "dashboard_data.json"
    try:
        json_path.write_text(json.dumps(dashboard_data, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"看板数据已生成: {json_path}")
    except Exception as e:
        log(f"看板数据生成失败: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)
