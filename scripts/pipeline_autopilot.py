#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 流水线自动驾驶 + 看板数据生成
版本：v2.1

职责：
1. 扫描项目本地 fleet_exchange 各队列（E 盘项目源码区）
2. 自动推进任意 Hermes 原始任务：
   Hermes 完成 → 推 _Codex_ 任务
   Codex 完成 → 推 _CloudCode_ 任务
   CloudCode 完成 → 汇总交付物到 企业微信群/定制接单项目/deliverables/<task_id>/
3. 生成 dashboard_data.json 供看板实时刷新

目录策略：
- E 盘：项目源码、舰队总线、任务卡、看板 HTML、最终交付物入口
- G 盘：所有运行时产物（outputs/ 缓存、图片素材、logs/ 日志）
  通过 G_DRIVE_ROOT 环境变量配置，默认 G:/WorkBuddy-Cache/企业微信群定制接单项目

运行：
    python scripts/pipeline_autopilot.py

守护进程：
    python scripts/pipeline_autopilot_daemon.py
    # 确认模式（Codex/CloudCode 先放 待确认/ 等人工放行）
    CONFIRM_MODE=true python scripts/pipeline_autopilot_daemon.py
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
E_PROJECT_ROOT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
E_HOME = Path("E:/龙虾AI主控中心/我的AI分身")
E_WECHAT = E_HOME / "企业微信群" / "定制接单项目"

# G 盘运行时缓存根目录（可配置）
G_DRIVE_ROOT = Path(os.environ.get(
    "G_DRIVE_ROOT",
    "G:/WorkBuddy-Cache/企业微信群定制接单项目"
))
G_PROJECT_ROOT = G_DRIVE_ROOT
G_OUTPUTS_DIR = G_PROJECT_ROOT / "outputs"
G_LOGS_DIR = G_PROJECT_ROOT / "logs"
G_DELIVERABLES_DIR = G_PROJECT_ROOT / "deliverables"  # 备用 G 盘交付镜像

# E 盘项目源码 / 总线 / 看板
FLEET = E_PROJECT_ROOT / "fleet_exchange"
FLEET_IN = FLEET / "incoming"
FLEET_DOING = FLEET / "doing"
FLEET_RESULTS = FLEET / "results"
FLEET_LOGS = FLEET / "logs"
PENDING_DIR = E_PROJECT_ROOT / "待分发任务"
CONFIRM_DIR = E_PROJECT_ROOT / "待确认"
DASHBOARD_DIR = E_WECHAT / "任务看板"
DELIVERABLES_DIR = E_WECHAT / "deliverables"
E_LEGACY_OUTPUTS = E_PROJECT_ROOT / "outputs"  # 旧 E 盘 outputs，用于迁移

for d in [FLEET_IN, FLEET_DOING, FLEET_RESULTS, FLEET_LOGS, PENDING_DIR, CONFIRM_DIR, DASHBOARD_DIR, DELIVERABLES_DIR]:
    try:
        os.makedirs(str(d), exist_ok=True)
    except Exception as e:
        print(f"[WARN] 创建 E 盘目录失败 {d}: {e}", file=sys.stderr)

for d in [G_OUTPUTS_DIR, G_LOGS_DIR, G_DELIVERABLES_DIR]:
    try:
        os.makedirs(str(d), exist_ok=True)
    except Exception as e:
        print(f"[WARN] 创建 G 盘目录失败 {d}: {e}。请检查 G_DRIVE_ROOT 是否可写。", file=sys.stderr)

LOG_FILE = G_LOGS_DIR / "pipeline_autopilot.log"

CONFIRM_MODE = os.environ.get("CONFIRM_MODE", "").lower() in ("1", "true", "yes", "on")

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
        # 如果 G 盘日志失败，尝试写 E 盘项目日志兜底
        try:
            fallback = E_PROJECT_ROOT / "logs" / "pipeline_autopilot.log"
            os.makedirs(str(fallback.parent), exist_ok=True)
            with fallback.open("a", encoding="utf-8") as f:
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
        os.makedirs(str(path.parent), exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        log(f"写文件失败: {path} -> {e}")
        return False


def migrate_legacy_outputs(task_id: str) -> bool:
    """将旧 E 盘 outputs/任务ID/ 下的文件迁移到 G 盘。"""
    src_dir = E_LEGACY_OUTPUTS / task_id
    if not src_dir.exists():
        return False
    dst_dir = G_OUTPUTS_DIR / task_id
    try:
        os.makedirs(str(dst_dir), exist_ok=True)
    except Exception as e:
        log(f"  -> 创建 G 盘 outputs/{task_id} 失败: {e}")
        return False
    migrated = []
    for f in src_dir.iterdir():
        if f.is_file():
            try:
                shutil.copy2(f, dst_dir / f.name)
                migrated.append(f.name)
            except Exception as e:
                log(f"  -> 迁移失败: {f} -> {e}")
    if migrated:
        log(f"  -> 已从 E 盘迁移 {len(migrated)} 个文件到 G 盘 outputs/{task_id}: {migrated}")
        # 迁移成功后，可选删除 E 盘源文件（默认保留，需用户确认）
        return True
    return False


# ============================================================
# 任务模板生成
# ============================================================
G_OUTPUTS_STR = str(G_OUTPUTS_DIR).replace("\\", "/")
G_LOGS_STR = str(G_LOGS_DIR).replace("\\", "/")


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
project: {fm.get('project', str(E_PROJECT_ROOT).replace('\\', '/'))}
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: {fm.get('simulation', 'false')}
real_order_min: {fm.get('real_order_min', '300')}
outputs_root: {G_OUTPUTS_STR}/{task_id}
logs_root: {G_LOGS_STR}
---

# 任务：{task_id} Codex 执行层 — 由 Hermes design_brief 驱动

> 原始需求卡：`{original_path}`  
> 设计简报：`{design_brief_path}`  
> ⚠️ simulation 标志：{fm.get('simulation', 'false')}，请遵守对应口径。

## 输入
1. 请先读取原始需求卡（上面的路径），理解客户完整需求、风格、交付范围、报价档。
2. 读取 Hermes 产出的设计简报：{design_brief_path}
3. 客户参考图位置：{G_OUTPUTS_STR}/{task_id}/客户参考截图.*（如存在）

## 交付要求
1. 按设计简报和原始需求，产出 **2~3 版** 设计方案（海报/画册内页/短视频物料/钥匙扣矢量等，根据原始需求确定）。
2. 每版方案附带：
   - 生成 prompt（如用文生图）或排版说明（如用 HTML/SVG/AI）
   - 尺寸/格式
   - 消耗估算（token / 积分 / 时间）
3. 低成本优先：演练任务走 mimo-bridge / ollama-bridge，不烧 Hy3 积分；真实付费单按需使用多模态。
4. 产出：
   - 所有方案文件 / 图片 / 文案统一落盘 **G 盘**：`{G_OUTPUTS_STR}/{task_id}/`
   - 禁止写入 E 盘 outputs/ 目录（避免占用 E 盘空间）
   - 结果摘要写回 `fleet_exchange/results/{task_id}__Codex_...__result_<时间>.md`（项目本地总线）

## 合规红线
- 只借鉴风格，禁止直接复制客户提供参考图的素材、字体、Logo、第三方标识。
- 模拟演练产出标注「内部模拟，不对外交付」；真实付费单产出标注授权范围。

## 完成后
执行：
```bash
bash "{str(E_PROJECT_ROOT).replace('\\', '/')}/scripts/fleet_done.sh" \
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
project: {fm.get('project', str(E_PROJECT_ROOT).replace('\\', '/'))}
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: {fm.get('simulation', 'false')}
real_order_min: {fm.get('real_order_min', '300')}
outputs_root: {G_OUTPUTS_STR}/{task_id}
logs_root: {G_LOGS_STR}
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
   - 终审报告统一落盘 **G 盘**：`{G_OUTPUTS_STR}/{task_id}/review_report.md`
   - 结果摘要写回 `fleet_exchange/results/{task_id}__CloudCode_...__result_<时间>.md`（项目本地总线）

## 完成后
执行：
```bash
bash "{str(E_PROJECT_ROOT).replace('\\', '/')}/scripts/fleet_done.sh" \
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

    # 确保 G 盘 outputs/任务ID 存在，并尝试迁移旧 E 盘数据
    g_task_outputs = G_OUTPUTS_DIR / task_id
    try:
        os.makedirs(str(g_task_outputs), exist_ok=True)
    except Exception as e:
        log(f"  -> 警告：无法创建 G 盘 outputs/{task_id}: {e}")
    migrate_legacy_outputs(task_id)

    design_brief_path = g_task_outputs / "design_brief.md"

    hermes_result = find_result_for_task(task_id, "Hermes")
    codex_task = find_task_in_dirs(task_id, "Codex", [FLEET_IN, FLEET_DOING, PENDING_DIR, CONFIRM_DIR])
    codex_result = find_result_for_task(task_id, "Codex")
    cloudcode_task = find_task_in_dirs(task_id, "CloudCode", [FLEET_IN, FLEET_DOING, PENDING_DIR, CONFIRM_DIR])
    cloudcode_result = find_result_for_task(task_id, "CloudCode")

    # 1. Hermes 完成 -> 推 Codex
    if hermes_result and not codex_task and not codex_result:
        codex_filename = f"{task_id}__Codex_{hermes_task.stem}.md"
        if CONFIRM_MODE:
            codex_path = CONFIRM_DIR / codex_filename
            target_name = "待确认"
        else:
            codex_path = FLEET_IN / codex_filename
            target_name = "incoming"
        content = make_codex_task(hermes_task, design_brief_path)
        if write_file(codex_path, content):
            log(f"  -> 已创建 Codex 任务（{target_name}）: {codex_path.name}")
        else:
            fallback = PENDING_DIR / codex_filename
            if write_file(fallback, content):
                log(f"  -> {target_name} 写入失败，已写入待分发: {fallback.name}")

    # 2. Codex 完成 -> 推 CloudCode
    if codex_result and not cloudcode_task and not cloudcode_result:
        cloudcode_filename = f"{task_id}__CloudCode_{hermes_task.stem}.md"
        if CONFIRM_MODE:
            cloudcode_path = CONFIRM_DIR / cloudcode_filename
            target_name = "待确认"
        else:
            cloudcode_path = FLEET_IN / cloudcode_filename
            target_name = "incoming"
        content = make_cloudcode_task(hermes_task, design_brief_path, codex_result)
        if write_file(cloudcode_path, content):
            log(f"  -> 已创建 CloudCode 任务（{target_name}）: {cloudcode_path.name}")
        else:
            fallback = PENDING_DIR / cloudcode_filename
            if write_file(fallback, content):
                log(f"  -> {target_name} 写入失败，已写入待分发: {fallback.name}")

    # 3. CloudCode 完成 -> 汇总交付物
    if cloudcode_result:
        deliverable_dir = DELIVERABLES_DIR / task_id
        g_deliverable_dir = G_DELIVERABLES_DIR / task_id
        try:
            os.makedirs(str(deliverable_dir), exist_ok=True)
        except Exception as e:
            log(f"  -> 创建交付目录失败: {deliverable_dir}: {e}")
        try:
            os.makedirs(str(g_deliverable_dir), exist_ok=True)
        except Exception as e:
            log(f"  -> 创建 G 盘交付目录失败: {g_deliverable_dir}: {e}")

        copied = []
        for src in [cloudcode_result, codex_result, hermes_result]:
            if src and src.exists():
                try:
                    shutil.copy2(src, deliverable_dir / src.name)
                    shutil.copy2(src, g_deliverable_dir / src.name)
                    copied.append(src.name)
                except Exception as e:
                    log(f"  -> 复制结果失败: {src} -> {e}")
        # 汇总 G 盘 outputs/任务ID 下所有产物
        if g_task_outputs.exists():
            for f in g_task_outputs.iterdir():
                if f.is_file():
                    try:
                        shutil.copy2(f, deliverable_dir / f.name)
                        shutil.copy2(f, g_deliverable_dir / f.name)
                        copied.append(f.name)
                    except Exception as e:
                        log(f"  -> 复制 outputs 失败: {f} -> {e}")
        # 兜底：E 盘旧 outputs 仍存在时，也复制一份
        if E_LEGACY_OUTPUTS.exists():
            e_task_outputs = E_LEGACY_OUTPUTS / task_id
            if e_task_outputs.exists():
                for f in e_task_outputs.iterdir():
                    if f.is_file() and (deliverable_dir / f.name).exists() is False:
                        try:
                            shutil.copy2(f, deliverable_dir / f.name)
                            shutil.copy2(f, g_deliverable_dir / f.name)
                            copied.append(f.name)
                        except Exception as e:
                            log(f"  -> 复制旧 E 盘 outputs 失败: {f} -> {e}")
        if copied:
            log(f"  -> 已汇总交付物到 E 盘: {deliverable_dir} ({len(copied)} 文件)")
            log(f"  -> 已镜像交付物到 G 盘: {g_deliverable_dir}")


def main():
    log("=== pipeline_autopilot 启动 ===")
    log(f"G_DRIVE_ROOT={G_DRIVE_ROOT}")
    log(f"CONFIRM_MODE={CONFIRM_MODE}")

    incoming = list_tasks(FLEET_IN)
    doing = list_tasks(FLEET_DOING)
    results = list_tasks(FLEET_RESULTS)
    pending = list_tasks(PENDING_DIR)
    confirms = list_tasks(CONFIRM_DIR)

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
        "project": str(E_PROJECT_ROOT),
        "g_drive_root": str(G_DRIVE_ROOT),
        "confirm_mode": CONFIRM_MODE,
        "wechat_deliverables": str(DELIVERABLES_DIR),
        "g_deliverables": str(G_DELIVERABLES_DIR),
        "fleet_incoming": [f.name for f in incoming],
        "fleet_doing": [f.name for f in doing],
        "fleet_results": [f.name for f in results],
        "pending_tasks": [f.name for f in pending],
        "confirm_tasks": [f.name for f in confirms],
        "tasks": []
    }

    for f in unique_tasks:
        fm = read_frontmatter(f)
        task_id = fm.get("task_id", f.stem.split("_")[0])
        hermes_result = find_result_for_task(task_id, "Hermes")
        codex_task = find_task_in_dirs(task_id, "Codex", [FLEET_IN, FLEET_DOING, PENDING_DIR, CONFIRM_DIR])
        codex_result = find_result_for_task(task_id, "Codex")
        cloudcode_task = find_task_in_dirs(task_id, "CloudCode", [FLEET_IN, FLEET_DOING, PENDING_DIR, CONFIRM_DIR])
        cloudcode_result = find_result_for_task(task_id, "CloudCode")
        dashboard_data["tasks"].append({
            "task_id": task_id,
            "title": f.name,
            "simulation": fm.get("simulation", "false"),
            "real_order_min": fm.get("real_order_min", "300"),
            "hermes": {"done": bool(hermes_result), "result_file": str(hermes_result) if hermes_result else None},
            "codex": {"task_exists": bool(codex_task), "done": bool(codex_result), "result_file": str(codex_result) if codex_result else None},
            "cloudcode": {"task_exists": bool(cloudcode_task), "done": bool(cloudcode_result), "result_file": str(cloudcode_result) if cloudcode_result else None},
            "deliverables_dir": str(DELIVERABLES_DIR / task_id),
            "g_deliverables_dir": str(G_DELIVERABLES_DIR / task_id),
        })

    warnings = []
    if pending:
        warnings.append({
            "level": "warning",
            "text": f"有 {len(pending)} 个任务卡在待分发目录，请运行：bash scripts/sync_to_fleet.sh"
        })
    if confirms:
        warnings.append({
            "level": "info",
            "text": f"有 {len(confirms)} 个任务在待确认目录，请运行：bash scripts/confirm_task.sh <task_id> 放行"
        })
    if warnings:
        dashboard_data["actions"] = warnings

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
