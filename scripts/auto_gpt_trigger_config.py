#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_gpt_trigger_config.py — AutoGPT 定时触发器「配置解析 + 参数校验」脚本
归属：AutoGPT 融合 ORCA 全链路（Issue #10 · 第二迭代 · 配套产出物 ④）
版本：v2.0.0

职责（重构后边界，Issue #10 强制约定）：
  - 仅封装「配置解析」与「参数校验」逻辑
  - 【已移除】不再生成/调用任何 Windows schtasks 指令（install/uninstall/schtasks 命令已删除）
  - 输出结构化任务清单 JSON（local_job_queue.json + stdout），供 Marvis 在本机消费部署

四化对应：
  - 智能化：触发器定义集中在 config/autogpt/triggers.yaml，本脚本只做解析校验
  - 全自动化：输出标准任务清单，Marvis 本地按清单落 Windows 计划任务
  - 自我净化：校验失败/告警回写 SelfLearn_Record.md

安全约束：
  - 零硬编码密钥；CNB_TOKEN / GH_TOKEN / 抖音/小红书 Cookie 仅从环境变量读取
  - 不生成/不打印任何密钥明文

用法：
  python scripts/auto_gpt_trigger_config.py validate   # 校验触发器配置合法性
  python scripts/auto_gpt_trigger_config.py export     # 输出结构化任务清单 JSON（默认写 local_job_queue.json）
  python scripts/auto_gpt_trigger_config.py list       # 打印触发器摘要
  python scripts/auto_gpt_trigger_config.py show       # 展示 export 结果明细
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "autogpt"
TRIGGERS_FILE = CONFIG_DIR / "triggers.yaml"
LOCAL_QUEUE_FILE = PROJECT_ROOT / "local_job_queue.json"
SELF_LEARN_RECORD = PROJECT_ROOT / "SelfLearn_Record.md"

# 允许的 workflow（与 auto_gpt_orca_bridge.py WORKFLOW_REGISTRY 保持一致）
ALLOWED_WORKFLOWS = {"网盘萃取", "企业接单", "闲鱼自动化", "量化策略", "通用"}

# 允许的动作（各赛道业务脚本 action）
ALLOWED_ACTIONS = {
    "闲鱼自动化": {"post", "reply", "stats", "crawler_poll"},
    "量化策略": {"dual_check", "binance", "jiasheng", "marvis_verify"},
    "通用": {"dispatch", "status", "trigger", "credential_check"},
    "网盘萃取": {"extract"},
    "企业接单": {"dispatch"},
}

# cron 5 段正则
_CRON_RE = re.compile(r"^(\*|(\d+|\*/\d+)(-\d+)?)(\s+(\*|(\d+|\*/\d+)(-\d+)?)){4}$")


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{level}] {msg}", flush=True)


def _append_self_learn(record: str):
    try:
        if not SELF_LEARN_RECORD.exists():
            SELF_LEARN_RECORD.write_text(
                "# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）\n\n",
                encoding="utf-8",
            )
        with SELF_LEARN_RECORD.open("a", encoding="utf-8") as f:
            f.write(record + "\n")
    except Exception as e:  # noqa: BLE001
        _log(f"写 SelfLearn_Record 失败: {e}", "WARN")


def _validate_cron(cron: str) -> bool:
    """校验 cron 表达式是否合法（覆盖本项目用到的模式）。"""
    if not cron or not _CRON_RE.match(cron.strip()):
        return False
    parts = cron.split()
    if len(parts) != 5:
        return False
    minute, hour, dom, mon, dow = parts
    # 分钟/小时支持 * 、*/n 、数字；简单范围校验
    for field, limit in ((minute, 59), (hour, 23)):
        if field.isdigit():
            if int(field) > limit:
                return False
        elif field.startswith("*/"):
            n = field[2:]
            if not n.isdigit() or int(n) <= 0 or int(n) > limit:
                return False
    return True


def _validate_trigger(name: str, info: Dict[str, Any]) -> List[str]:
    """校验单个触发器，返回错误列表。"""
    errors: List[str] = []

    cron = info.get("cron", "")
    if not _validate_cron(cron):
        errors.append(f"{name}: cron 表达式非法 ({cron!r})")

    workflow = info.get("workflow", "")
    if workflow not in ALLOWED_WORKFLOWS:
        errors.append(f"{name}: workflow 非法 ({workflow!r})，允许 {sorted(ALLOWED_WORKFLOWS)}")

    params = info.get("params", {}) or {}
    action = params.get("action", "")
    allowed = ALLOWED_ACTIONS.get(workflow, set())
    if action and allowed and action not in allowed:
        errors.append(f"{name}: action 非法 ({action!r})，{workflow} 允许 {sorted(allowed)}")

    file_path = params.get("file_path", "")
    if file_path and not (PROJECT_ROOT / file_path).exists():
        # file_path 可能为脚本相对路径；存在性校验仅告警
        errors.append(f"{name}: file_path 对应脚本不存在 ({file_path})")

    if not info.get("desc"):
        errors.append(f"{name}: 缺少 desc 描述")

    return errors


def validate(config: Dict[str, Any]) -> int:
    """校验整个触发器配置。返回 0=通过，1=有错误。"""
    triggers = config.get("triggers", {})
    _log(f"校验触发器配置: {TRIGGERS_FILE}（{len(triggers)} 个触发器）")
    all_errors: List[str] = []
    for name, info in triggers.items():
        errs = _validate_trigger(name, info)
        if errs:
            all_errors.extend(errs)
            for e in errs:
                _log(f"❌ {e}", "ERROR")
        else:
            _log(f"✅ {name}: 校验通过")

    if all_errors:
        _append_self_learn(
            f"- [{datetime.now():%Y-%m-%d %H:%M:%S}] 触发器配置校验失败 {len(all_errors)} 项"
        )
        return 1
    _log("全部触发器配置校验通过")
    return 0


def build_job_queue(config: Dict[str, Any]) -> Dict[str, Any]:
    """构造结构化任务清单 JSON（供 Marvis 本地消费部署）。"""
    triggers = config.get("triggers", {})
    scheduler = config.get("scheduler", {})
    jobs = []
    for name, info in triggers.items():
        params = info.get("params", {}) or {}
        jobs.append({
            "task_name": params.get("task_name", name),
            "file_path": params.get("file_path", "scripts/auto_gpt_orca_bridge.py"),
            "params": {
                "trigger_name": name,
                "cron": info.get("cron", ""),
                "schedule_human": info.get("schedule_human", ""),
                "workflow": info.get("workflow", ""),
                "action": params.get("action", ""),
                "desc": info.get("desc", ""),
            },
        })
    queue = {
        "generated_at": datetime.now().isoformat(),
        "generated_by": "scripts/auto_gpt_trigger_config.py",
        "source_config": str(TRIGGERS_FILE),
        "scheduler": scheduler,
        "note": "本文件仅含结构化任务清单，不含任何 Windows 计划任务命令；由 Marvis 在本机按 params 部署。",
        "jobs": jobs,
    }
    return queue


def export(queue_file: Path = LOCAL_QUEUE_FILE, print_out: bool = True) -> int:
    """输出任务清单 JSON 到 local_job_queue.json（根目录）+ stdout。"""
    config = load_yaml(TRIGGERS_FILE)
    rc = validate(config)
    queue = build_job_queue(config)

    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"任务清单已写出: {queue_file}")

    if print_out:
        print(json.dumps(queue, ensure_ascii=False, indent=2))
    return rc


def list_triggers(config: Dict[str, Any]) -> int:
    """打印触发器摘要。"""
    print("已配置的 AutoGPT 定时触发器（来自 config/autogpt/triggers.yaml）：")
    for name, info in config.get("triggers", {}).items():
        params = info.get("params", {})
        print(
            f"  - {name:<22} cron={info.get('cron',''):<14} "
            f"工作流={info.get('workflow',''):<6} {info.get('desc','')}"
            f"{'  action=' + str(params.get('action','')) if params.get('action') else ''}"
        )
    print(f"\n桥接入口: python scripts/auto_gpt_orca_bridge.py trigger --workflow <工作流> --title <标题>")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="AutoGPT 定时触发器配置解析与参数校验（不含 Windows 计划任务调用）"
    )
    parser.add_argument("--config", default=str(TRIGGERS_FILE), help="触发器配置文件路径")
    parser.add_argument("--out", default=str(LOCAL_QUEUE_FILE), help="任务清单 JSON 输出路径")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("validate", help="校验触发器配置合法性")
    sub.add_parser("export", help="输出结构化任务清单 JSON（写 local_job_queue.json）")
    sub.add_parser("list", help="打印触发器摘要")
    sub.add_parser("show", help="展示任务清单明细（等价 export 不写文件）")

    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        _log(f"配置文件不存在: {cfg_path}", "ERROR")
        return 1
    config = load_yaml(cfg_path)

    if args.cmd == "validate":
        return validate(config)
    if args.cmd == "export":
        return export(Path(args.out), print_out=True)
    if args.cmd == "show":
        queue = build_job_queue(config)
        print(json.dumps(queue, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "list":
        return list_triggers(config)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
