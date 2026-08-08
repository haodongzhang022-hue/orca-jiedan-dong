#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_gpt_trigger_config.py — AutoGPT 定时触发器配置脚本
归属：AutoGPT 融合 ORCA 全链路（Issue #10 任务 · 配套产出物 #3）
版本：v1.0.0

职责：
  将 AutoGPT 定时触发器（闲鱼定时上架 / 凭证过期巡检 / 量化双仓巡检 / 爬虫静默轮询）
  统一生成为 Windows schtasks 计划任务，并与 G 盘 schtasks 同步任务保持一致。

四化对应：
  - 智能化：自然语言调度为顶层入口，本脚本仅负责触发器落盘
  - 全自动化：凭证过期巡检、爬虫静默轮询、三端同步全部交由 AutoGPT 后台托管，不再弹窗询问人工
  - 自我净化：每次触发器执行结果回写 SelfLearn_Record.md

安全约束：
  - 零硬编码密钥；CNB_TOKEN / GH_TOKEN / 抖音/小红书 Cookie 仅从环境变量读取
  - 不生成/不打印任何密钥明文

用法：
  python scripts/auto_gpt_trigger_config.py install        # 安装/更新全部触发器（schtasks）
  python scripts/auto_gpt_trigger_config.py uninstall      # 卸载全部触发器
  python scripts/auto_gpt_trigger_config.py list           # 列出已注册触发器
  python scripts/auto_gpt_trigger_config.py dryrun         # 仅打印将生成的 schtasks 命令（不执行）
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SELF_LEARN_RECORD = PROJECT_ROOT / "SelfLearn_Record.md"
BRIDGE = PROJECT_ROOT / "scripts" / "auto_gpt_orca_bridge.py"

# 触发器注册表：name -> (cron表达式, workflow, 描述)
# 与 templates/autogpt/lobster_five_step_autogpt_template.yaml 的 triggers 保持一致
TRIGGERS = {
    "AG_Xianyu_Post": {
        "cron": "0 9 * * *",
        "workflow": "闲鱼自动化",
        "desc": "闲鱼定时上架 + 客服回复 + 数据统计",
    },
    "AG_Credential_Check": {
        "cron": "0 0 * * *",
        "workflow": "通用",
        "desc": "凭证过期巡检（CNB Token / GH PAT / Cookie）",
    },
    "AG_Quant_DualCheck": {
        "cron": "*/30 * * * *",
        "workflow": "量化策略",
        "desc": "币安/嘉盛双仓巡检 + Marvis 三端一致性校验",
    },
    "AG_Crawler_Poll": {
        "cron": "*/10 * * * *",
        "workflow": "闲鱼自动化",
        "desc": "爬虫静默轮询 + 风控限速逻辑",
    },
}

SELF_LEARN_HEADER = """# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）

> 归属：自我净化闭环 · 每次迭代沉淀踩坑方案，供赛博书屋自主学习。
> 来源：scripts/auto_gpt_trigger_config.py / scripts/auto_gpt_orca_bridge.py

"""


def _log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{level}] {msg}", flush=True)


def _append_self_learn(record: str):
    try:
        if not SELF_LEARN_RECORD.exists():
            SELF_LEARN_RECORD.write_text(SELF_LEARN_HEADER, encoding="utf-8")
        with SELF_LEARN_RECORD.open("a", encoding="utf-8") as f:
            f.write(record + "\n")
    except Exception as e:  # noqa: BLE001
        _log(f"写 SelfLearn_Record 失败: {e}", "WARN")


def _cron_to_schtask(cron: str) -> tuple[str, str]:
    """把 cron 表达式转成 schtasks 参数（仅覆盖本项目用到的几种常见模式）。"""
    parts = cron.split()
    minute, hour = parts[0], parts[1]
    # 简化映射：每日定点 / 每N分钟
    if minute.startswith("*/") and hour == "*":
        interval = minute.strip("*/")
        return "/sc minute", f"/mo {interval}"
    if hour.isdigit():
        return "/sc daily", f"/st {hour.zfill(2)}:{minute.zfill(2)}"
    return "/sc daily", "/st 00:00"


def _build_schtask_cmd(name: str, info: dict, python: str) -> list[str]:
    """构造 schtasks 注册命令。任务体通过桥接脚本的 trigger 子命令执行。"""
    sch_task, sch_freq = _cron_to_schtask(info["cron"])
    workflow = info["workflow"]
    # 注意：schtasks 的 /tr 内容用双引号包住，内部命令用单引号包裹 Python 参数
    action = (
        f'"{python}" "{BRIDGE}" trigger --workflow "{workflow}" '
        f'--title "AutoGPT定时-{name}" --desc "{info["desc"]}"'
    )
    return [
        "schtasks", "/create", "/tn", name, "/tr", action,
        sch_task, sch_freq, "/f",
    ]


def _find_python() -> str:
    cand = os.environ.get("PYTHON_EXE", "")
    if cand and Path(cand).exists():
        return cand
    sysp = shutil.which("python") or shutil.which("python3") or sys.executable
    return sysp


def install(dryrun: bool = False) -> int:
    python = _find_python()
    _log(f"安装 AutoGPT 触发器（schtasks），Python: {python}")
    _log(f"桥接脚本: {BRIDGE}")
    ok, fail = 0, 0
    for name, info in TRIGGERS.items():
        cmd = _build_schtask_cmd(name, info, python)
        if dryrun:
            print("[DRYRUN]", " ".join(cmd))
            ok += 1
            continue
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0 or "already exists" in (proc.stdout + proc.stderr):
                _log(f"✅ 触发器注册成功: {name} ({info['desc']})")
                ok += 1
            else:
                _log(f"❌ 触发器注册失败: {name} -> {proc.stderr.strip()[:300]}", "WARN")
                fail += 1
        except Exception as e:  # noqa: BLE001
            _log(f"❌ 触发器注册异常: {name} -> {e}", "WARN")
            fail += 1

    _log(f"安装完成：成功 {ok}，失败 {fail}")
    if not dryrun:
        _append_self_learn(
            f"- [{datetime.now():%Y-%m-%d %H:%M:%S}] AutoGPT 触发器安装：成功 {ok} / 失败 {fail}"
        )
    return 0 if fail == 0 else 1


def uninstall() -> int:
    _log("卸载 AutoGPT 触发器")
    ok, fail = 0, 0
    for name in TRIGGERS:
        try:
            proc = subprocess.run(
                ["schtasks", "/delete", "/tn", name, "/f"],
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0:
                ok += 1
            else:
                fail += 1
        except Exception:  # noqa: BLE001
            fail += 1
    _log(f"卸载完成：成功 {ok}，失败 {fail}")
    return 0 if fail == 0 else 1


def list_triggers() -> int:
    print("已配置的 AutoGPT 定时触发器：")
    for name, info in TRIGGERS.items():
        print(f"  - {name:<22} cron={info['cron']:<14} 工作流={info['workflow']:<6} {info['desc']}")
    print(f"\n桥接入口: python {BRIDGE} trigger --workflow <工作流> --title <标题>")
    return 0


def main():
    parser = argparse.ArgumentParser(description="AutoGPT 定时触发器配置（schtasks 同步 G 盘任务）")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("install", help="安装/更新触发器")
    sub.add_parser("uninstall", help="卸载触发器")
    sub.add_parser("list", help="列出触发器")
    sub.add_parser("dryrun", help="仅打印 schtasks 命令")
    args = parser.parse_args()

    if args.cmd == "install":
        return install()
    if args.cmd == "dryrun":
        return install(dryrun=True)
    if args.cmd == "uninstall":
        return uninstall()
    if args.cmd == "list":
        return list_triggers()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
