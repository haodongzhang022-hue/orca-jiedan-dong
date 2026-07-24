#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 流水线自动驾驶 + 看板数据生成

职责：
1. 扫描项目本地 fleet_exchange 各队列
2. 自动推进任意 Hermes 任务：
   Hermes 完成 → 推 _Codex_ 任务
   Codex 完成 → 推 _CloudCode_ 任务
   CloudCode 完成 → 汇总交付物到 企业微信群/定制接单项目/deliverables/<task_id>/
3. 生成 dashboard_data.json 供看板实时刷新

运行：
    python scripts/pipeline_autopilot.py

WorkBuddy 守护进程：
    python scripts/pipeline_autopilot_daemon.py
"""
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
HOME = Path("E:/龙虾AI主控中心/我的AI分身")
PROJECT = HOME / "企业微信群定制接单项目"
WECHAT = HOME / "企业微信群" / "定制接单项目"

FLEET = PROJECT / "fleet_exchange"
FLEET_IN = FLEET / "incoming"
FLEET_DOING = FLEET / "doing"
FLEET_RESULTS = FLEET / "results"
FLEET_LOGS = FLEET / "logs"
for d in [FLEET_IN, FLEET_DOING, FLEET_RESULTS, FLEET_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

PENDING_DIR = PROJECT / "待分发任务"
PENDING_DIR.mkdir(parents=True, exist_ok=True)

OUTPUTS_DIR = PROJECT / "outputs"
DASHBOARD_DIR = WECHAT / "任务看板"
DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
DELIVERABLES_DIR = WECHAT / "deliverables"
DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = PROJECT / "logs" / "pipeline_autopilot.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


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
    text = ""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {"content": text}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"content": text}
    data = {"content": parts[2].strip()}
    for line in parts[1].strip().splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def list_tasks(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files = [f for f in directory.iterdir() if f.is_file() and f.suffix == ".md"]
    files.sort(key=lambda x: x.stat().st_mtime)
    return files


def agent_tag(filename: str) -> str | None:
    if "_Hermes_" in filename:
        return "Hermes"
    if "_Codex_" in filename:
        return "Codex"
    if "_CloudCode_" in filename or "_Claude_" in filename:
        return "CloudCode"
    return None


def find_task_in_dirs(task_id: str, agent: str, dirs: list[Path]) -> Path | None:
    for d in dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.suffix == ".md" and task_id in f.name and agent_tag(f.name) == agent:
                return f
    return None


def find_result_for_task(task_id: str, agent: str) -> Path | None:
    if not FLEET_RESULTS.exists():
        return None
    candidates = [f for f in FLEET_RESULTS.iterdir()
                  if f.is_file() and f.suffix == ".md"
                  and task_id in f.name and agent_tag(f.name) == agent]
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]


def write_file(path: Path, content: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        log(f"写文件失败: {path} -> {e}")
        return False


# ============================================================
# 任务模板生成
# ============================================================

def make_codex_task(hermes_task: Path, design_brief_path: Path | str) -> str:
    fm = read_frontmatter(hermes_task)
    task_id = fm.get("task_id", hermes_task.stem.split("_")[0])
    original_path = str(hermes_task).replace("\\", "/")
    return f"""---
task_id: {task_id}
from: WorkBuddy
to: Codex
priority: {fm.get('priority', 'high')}
context: {fm.get('context', '企业微信群定制接单项目 · 执行层')}
project: {fm.get('project', str(PROJECT).replace('\\', '/'))}
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: {fm.get('simulation', 'false')}
real_order_min: {fm.get('real_order_min', '300')}
---

# 任务：{task_id} Codex 执行层 — 由 Hermes design_brief 驱动

> 原始需求卡：`{original_path}`  
> 设计简报：`{design_brief_path}`  
> ⚠️ simulation 标志：{fm.get('simulation', 'false')}，请遵守对应口径。

## 输入
1. 请先读取原始需求卡（上面的路径），理解客户完整需求、风格、交付范围、报价档。
2. 读取 Hermes 产出的设计简报：{design_brief_path}

## 交付要求
1. 按设计简报和原始需求，产出 **2~3 版** 设计方案（海报/画册内页/短视频物料等，根据原始需求确定）。
2. 每版方案附带：
   - 生成 prompt（如用文生图）或排版说明（如用 HTML/SVG）
   - 尺寸/格式
   - 消耗估算（token / 积分 / 时间）
3. 低成本优先：演练任务走 mimo-bridge / ollama-bridge，不烧 Hy3 积分；真实付费单按需使用多模态。
4. 产出：
   - 所有方案文件 / 图片 / 文案落盘 `E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/{task_id}/`
   - 结果摘要写回 `fleet_exchange/results/{task_id}__Codex_...__result_<时间>.md`（项目本地总线）

## 合规红线
- 只借鉴风格，禁止直接复制客户提供参考图的素材、字体、Logo、第三方标识。
- 模拟演练产出标注「内部模拟，不对外交付」；真实付费单产出标注授权范围。

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/scripts/fleet_done.sh" \
  "<WORKING_FILE>" \
  "Codex 方案已产出，等待 WorkBuddy 转交 CloudCode"
```
"""


def make_cloudcode_task(hermes_task: Path, design_brief_path: Path | str, codex_result_path: Path | str) -> str:
    fm = read_frontmatter(hermes_task)
    task_id = fm.get("task_id", hermes_task.stem.split("_")[0])
    original_path = str(hermes_task).replace("\\", "/")
    return f"""---
task_id: {task_id}
from: WorkBuddy
to: CloudCode
priority: {fm.get('priority', 'high')}
context: {fm.get('context', '企业微信群定制接单项目 · 核查层')}
project: {fm.get('project', str(PROJECT).replace('\\', '/'))}
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: {fm.get('simulation', 'false')}
real_order_min: {fm.get('real_order_min', '300')}
---

# 任务：{task_id} CloudCode 核查层 — 质量/合规/成本终审

> 原始需求卡：`{original_path}`  
> Hermes 设计简报：`{design_brief_path}`  
> Codex 方案：`{codex_result_path}`  
> ⚠️ simulation 标志：{fm.get('simulation', 'false')}，请遵守对应口径。

## 交付要求
1. 读取原始需求卡、设计简报、Codex 方案。
2. 质量审查：
   - 风格还原度、构图、可读性、层级是否符合简报
   - 三版中择优，给出理由与修改建议
3. 合规审查：
   - 是否存在直接复制参考图素材、字体、Logo、第三方标识的侵权风险
   - 是否属于「风格借鉴」而非「素材复刻」
   - 是否需补充授权声明
4. 成本审查：
   - 汇总 Hermes + Codex 实际消耗（token/积分/时间）
   - 与报价档对比，给出毛利结论
5. 产出：
   - 终审报告落盘 `E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/{task_id}/review_report.md`
   - 结果摘要写回 `fleet_exchange/results/{task_id}__CloudCode_...__result_<时间>.md`（项目本地总线）

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/scripts/fleet_done.sh" \
  "<WORKING_FILE>" \
  "CloudCode 终审完成，等待 WorkBuddy 汇总"
```
"""


# ============================================================
# 主逻辑
# ============================================================

def process_task(hermes_task: Path):
    fm = read_frontmatter(hermes_task)
    task_id = fm.get("task_id", hermes_task.stem.split("_")[0])
    log(f"处理任务 {task_id}: {hermes_task.name}")

    design_brief_path = OUTPUTS_DIR / task_id / "design_brief.md"

    hermes_result = find_result_for_task(task_id, "Hermes")
    codex_task = find_task_in_dirs(task_id, "Codex", [FLEET_IN, FLEET_DOING, PENDING_DIR])
    codex_result = find_result_for_task(task_id, "Codex")
    cloudcode_task = find_task_in_dirs(task_id, "CloudCode", [FLEET_IN, FLEET_DOING, PENDING_DIR])
    cloudcode_result = find_result_for_task(task_id, "CloudCode")

    # 1. Hermes 完成 -> 推 Codex
    if hermes_result and not codex_task and not codex_result:
        codex_filename = f"{task_id}__Codex_{hermes_task.stem}.md"
        codex_path = FLEET_IN / codex_filename
        content = make_codex_task(hermes_task, design_brief_path)
        if write_file(codex_path, content):
            log(f"  -> 已创建 Codex 任务: {codex_path.name}")
        else:
            fallback = PENDING_DIR / codex_filename
            if write_file(fallback, content):
                log(f"  -> FLEET_IN 写入失败，已写入待分发: {fallback.name}")

    # 2. Codex 完成 -> 推 CloudCode
    if codex_result and not cloudcode_task and not cloudcode_result:
        cloudcode_filename = f"{task_id}__CloudCode_{hermes_task.stem}.md"
        cloudcode_path = FLEET_IN / cloudcode_filename
        content = make_cloudcode_task(hermes_task, design_brief_path, codex_result)
        if write_file(cloudcode_path, content):
            log(f"  -> 已创建 CloudCode 任务: {cloudcode_path.name}")
        else:
            fallback = PENDING_DIR / cloudcode_filename
            if write_file(fallback, content):
                log(f"  -> FLEET_IN 写入失败，已写入待分发: {fallback.name}")

    # 3. CloudCode 完成 -> 汇总交付物
    if cloudcode_result:
        deliverable_dir = DELIVERABLES_DIR / task_id
        deliverable_dir.mkdir(parents=True, exist_ok=True)
        copied = []
        for src in [cloudcode_result, codex_result, hermes_result]:
            if src and src.exists():
                try:
                    shutil.copy2(src, deliverable_dir / src.name)
                    copied.append(src.name)
                except Exception as e:
                    log(f"  -> 复制结果失败: {src} -> {e}")
        out_dir = OUTPUTS_DIR / task_id
        if out_dir.exists():
            for f in out_dir.iterdir():
                if f.is_file():
                    try:
                        shutil.copy2(f, deliverable_dir / f.name)
                        copied.append(f.name)
                    except Exception as e:
                        log(f"  -> 复制 outputs 失败: {f} -> {e}")
        if copied:
            log(f"  -> 已汇总交付物到 {deliverable_dir}: {len(copied)} 文件")


def main():
    log("=== pipeline_autopilot 启动 ===")

    incoming = list_tasks(FLEET_IN)
    doing = list_tasks(FLEET_DOING)
    results = list_tasks(FLEET_RESULTS)
    pending = list_tasks(PENDING_DIR)

    # 收集所有 Hermes 原始任务（incoming + doing + 历史归档 done 就算了，只看活跃）
    hermes_tasks = []
    for d in [FLEET_IN, FLEET_DOING]:
        for f in list_tasks(d):
            if f.suffix == ".md":
                fm = read_frontmatter(f)
                tag = agent_tag(f.name)
                to_field = fm.get("to", "")
                if tag == "Hermes" or to_field == "Hermes":
                    hermes_tasks.append(f)

    # 去重（按文件名）
    seen = set()
    unique_tasks = []
    for f in hermes_tasks:
        if f.name not in seen:
            seen.add(f.name)
            unique_tasks.append(f)

    for f in unique_tasks:
        try:
            process_task(f)
        except Exception as e:
            log(f"处理 {f.name} 出错: {e}")

    # 生成看板数据
    dashboard_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": str(PROJECT),
        "wechat_deliverables": str(DELIVERABLES_DIR),
        "fleet_incoming": [f.name for f in incoming],
        "fleet_doing": [f.name for f in doing],
        "fleet_results": [f.name for f in results],
        "pending_tasks": [f.name for f in pending],
        "tasks": []
    }

    for f in unique_tasks:
        fm = read_frontmatter(f)
        task_id = fm.get("task_id", f.stem.split("_")[0])
        hermes_result = find_result_for_task(task_id, "Hermes")
        codex_task = find_task_in_dirs(task_id, "Codex", [FLEET_IN, FLEET_DOING, PENDING_DIR])
        codex_result = find_result_for_task(task_id, "Codex")
        cloudcode_task = find_task_in_dirs(task_id, "CloudCode", [FLEET_IN, FLEET_DOING, PENDING_DIR])
        cloudcode_result = find_result_for_task(task_id, "CloudCode")
        dashboard_data["tasks"].append({
            "task_id": task_id,
            "title": f"{task_id} {f.name}",
            "simulation": fm.get("simulation", "false"),
            "real_order_min": fm.get("real_order_min", "300"),
            "hermes": {"done": bool(hermes_result), "result_file": str(hermes_result) if hermes_result else None},
            "codex": {"task_exists": bool(codex_task), "done": bool(codex_result), "result_file": str(codex_result) if codex_result else None},
            "cloudcode": {"task_exists": bool(cloudcode_task), "done": bool(cloudcode_result), "result_file": str(cloudcode_result) if cloudcode_result else None},
            "deliverables_dir": str(DELIVERABLES_DIR / task_id),
        })

    if pending:
        dashboard_data.setdefault("actions", []).append({
            "level": "warning",
            "text": f"有 {len(pending)} 个任务卡在待分发目录，请运行：bash scripts/sync_to_fleet.sh"
        })

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
