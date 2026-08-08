#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_gpt_orca_bridge.py — AutoGPT 与 ORCA 全链路桥接脚本
归属：AutoGPT 融合 ORCA 全链路（Issue #10 任务 · 私有化本地部署）
版本：v1.0.0

职责：
  打通 AutoGPT（本地 AI 主控中心 · 自然语言任务调度顶层入口）与
  ORCA 全链路（orca_deploy.py / mcp_packager.py / 四大赛道工作流 / CNB 云原生流水线）。

半云半端架构：
  ┌─ 半端（本地 AutoGPT 面板）────────────────────────────┐
  │  AutoGPT 可视化拖拽 / 任务拆解 → auto_gpt_orca_bridge.py  │
  └──────────────────────────────────────────────────────┘
                             │ 子进程 / HTTP
                             ▼
  ┌─ 半云（CNB 云端容器 / 本地 ORCA 引擎）────────────────┐
  │  orca_deploy.py（部署流水线）                         │
  │  mcp_packager.py（MCP 打包）                          │
  │  四大赛道：网盘萃取 / 企业接单 / 闲鱼自动化 / 量化策略  │
  └──────────────────────────────────────────────────────┘

安全约束（全域模板 / 四化）：
  - 密钥零硬编码：CNB_TOKEN / GH_TOKEN / 抖音/小红书 Cookie 一律从环境变量读取
  - 复用现有 DPAPI Cookie 解密与鉴权体系，不重复造轮子
  - 全部学习迭代记录写入 SelfLearn_Record.md（自我净化闭环）

用法：
  python scripts/auto_gpt_orca_bridge.py dispatch --task <任务JSON或Markdown路径> [--workflow 网盘萃取|企业接单|闲鱼自动化|量化策略]
  python scripts/auto_gpt_orca_bridge.py status
  python scripts/auto_gpt_orca_bridge.py trigger --workflow 企业接单 --title "客户需求" [--desc "..."]
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

# ============================================================
# 常量 / 路径（不硬编码密钥，仅路径常量）
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CONFIG_DIR = PROJECT_ROOT / "config" / "autogpt"
FLEET_DIR = PROJECT_ROOT / "fleet_exchange"
FLEET_IN = FLEET_DIR / "incoming"
FLEET_DOING = FLEET_DIR / "doing"
FLEET_DONE = FLEET_DIR / "done"
FLEET_RESULTS = FLEET_DIR / "results"
SELF_LEARN_RECORD = PROJECT_ROOT / "SelfLearn_Record.md"
AUTOGPT_DIR = Path(os.environ.get("AUTOGPT_HOME", "E:/龙虾AI主控中心/AutoGPT-Agent"))
AUTOGPT_TASKS_DIR = AUTOGPT_DIR / "tasks"

# 兼容 G 盘同步（G_DRIVE_ROOT 环境变量，缺省走默认）
G_DRIVE_ROOT = Path(os.environ.get("G_DRIVE_ROOT", "G:/WorkBuddy-Cache/企业微信群定制接单项目"))

# 四大赛道 → 入口脚本/方法 映射
WORKFLOW_REGISTRY = {
    "网盘萃取": {
        "entry": SCRIPTS_DIR / "auto_knowledge_extract.py",
        "desc": "自然语言输入知识库沉淀需求 → 自动拆解抓取/过滤/蒸馏/归档 → 联动赛博书屋技能入库",
        "args_template": ["--input", "{input}", "--output", "{output}"],
    },
    "企业接单": {
        "entry": SCRIPTS_DIR / "maris_dispatch.sh",
        "desc": "外部客户需求一键丢入 → 自动拆解需求→成本报价→方案生成→交付归档（替代手动 CNB Issue）",
        "args_template": ["--type", "{type}", "--title", "{title}", "--desc", "{desc}", "--priority", "{priority}", "--deadline", "{deadline}"],
    },
    "闲鱼自动化": {
        "entry": SCRIPTS_DIR / "auto_xianyu_scheduler.py",
        "desc": "定时上架/客服回复/数据统计 → AutoGPT 触发器 + 爬虫风控限速逻辑",
        "args_template": ["--action", "{action}"],
        "config": CONFIG_DIR / "xianyu_config.yaml",
    },
    "量化策略": {
        "entry": SCRIPTS_DIR / "quant_scheduler.py",
        "desc": "币安/嘉盛双仓巡检、策略回测定时调度 → 联动 Marvis 三端一致性校验",
        "args_template": ["--action", "{action}"],
        "config": CONFIG_DIR / "quant_config.yaml",
    },
}

# ============================================================
# 工具函数
# ============================================================
def _env(name: str, default: str = "") -> str:
    """读取环境变量，绝不打印/回写密钥明文。"""
    return os.environ.get(name, default)


def _log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def _append_self_learn(record: str):
    """自我净化：把本次执行/踩坑写入 SelfLearn_Record.md（幂等追加）。"""
    try:
        if not SELF_LEARN_RECORD.exists():
            SELF_LEARN_RECORD.write_text(
                "# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）\n\n"
                "> 归属：自我净化闭环 · 每次迭代沉淀踩坑方案，供赛博书屋自主学习。\n\n",
                encoding="utf-8",
            )
        with SELF_LEARN_RECORD.open("a", encoding="utf-8") as f:
            f.write(record + "\n")
    except Exception as e:  # noqa: BLE001
        _log(f"写 SelfLearn_Record 失败（不阻断主流程）: {e}", "WARN")


def _resolve_entry(workflow: str) -> tuple[Path, list]:
    """按工作流解析入口脚本与参数模板。未知工作流 → 降级为通用 dispatch。"""
    info = WORKFLOW_REGISTRY.get(workflow)
    if not info:
        return SCRIPTS_DIR / "dispatch_task.py", []
    return info["entry"], info["args_template"]


def _check_env_ready() -> list:
    """校验关键环境变量是否存在（只查存在性，不打印值）。"""
    needed = ["CNB_TOKEN", "GH_TOKEN", "DOUYIN_COOKIE", "XIAOHONGSHU_COOKIE"]
    missing = [n for n in needed if not _env(n)]
    return missing


# ============================================================
# 核心动作
# ============================================================
def dispatch(task_input: str, workflow: str, verbose: bool = False) -> int:
    """AutoGPT 顶层入口：接收自然语言任务 → 映射四大赛道 → 调度 ORCA 脚本。"""
    _log(f"AutoGPT 收到任务调度，工作流映射: {workflow or '通用'}")
    missing = _check_env_ready()
    if missing:
        _log(f"环境变量缺失(存在性校验): {', '.join(missing)} —— 请检查 .env / 平台注入", "WARN")

    # 1) 解析任务输入（JSON / Markdown / 纯文本）
    task_data = _parse_task(task_input)
    _log(f"任务标题: {task_data.get('title', '(未命名)')}")

    # 2) 落地任务卡到 fleet_exchange（企业接单复用 Maris 投递格式）
    os.makedirs(str(FLEET_IN), exist_ok=True)
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_AG"
    task_card = FLEET_IN / f"{task_id}__AutoGPT_{workflow or 'generic'}.md"
    # 结构化拆解：AutoGPT 把需求要素抽成清单，防止整单误判（如海报误判为纯色背景）
    elements = _parse_elements(task_data)
    elem_lines = "\n".join(f"- {k}: {v}" for k, v in elements.items() if v)
    task_card.write_text(
        f"# 任务卡：{task_data.get('title', 'AutoGPT 调度任务')}\n\n"
        f"- 任务ID: {task_id}\n"
        f"- 类型: {workflow or '通用'}\n"
        f"- 来源: AutoGPT\n"
        f"- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 优先级: {task_data.get('priority', '中')}\n\n"
        f"## 需求\n{task_data.get('description', task_input)}\n\n"
        f"## AutoGPT 结构化拆解清单（先核验再出稿）\n{elem_lines}\n\n"
        f"## 要求\n- 中文输出\n- 按 ORCA 全链路标准交付\n- 成品必须对齐需求要素清单，杜绝需求误判\n",
        encoding="utf-8",
    )
    _log(f"任务卡已落地: {task_card}")

    # 3) 调度对应工作流入口
    entry, args_tpl = _resolve_entry(workflow)
    if not entry.exists():
        _log(f"入口脚本不存在: {entry} —— 已落地任务卡，交由流水线接管", "WARN")
        _append_self_learn(f"- [{task_id}] 入口脚本缺失 {entry}，任务卡兜底入库，待补脚本")
        return 0

    cmd = _build_cmd(entry, args_tpl, task_data)
    _log(f"执行: {' '.join(cmd)}")
    if verbose:
        _log("→ verbose 模式：展示命令细节（不含任何密钥）")

    # 4) 执行（超时保护，失败不致命，走自我净化记录）
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode == 0:
            _log(f"工作流执行成功: {workflow} (rc=0)")
            _append_self_learn(f"- [{task_id}] {workflow} 执行成功：{task_card.name}")
        else:
            _log(f"工作流执行异常 rc={proc.returncode}: {proc.stderr[-800:]}", "WARN")
            _append_self_learn(
                f"- [{task_id}] {workflow} 执行失败 rc={proc.returncode}，踩坑：{proc.stderr[-300:]}"
            )
        return proc.returncode
    except subprocess.TimeoutExpired:
        _log("执行超时（600s）—— 已记录，任务卡保留待人工/后续调度", "WARN")
        _append_self_learn(f"- [{task_id}] {workflow} 超时 600s")
        return 124
    except Exception as e:  # noqa: BLE001
        _log(f"调度异常: {e}", "ERROR")
        _append_self_learn(f"- [{task_id}] {workflow} 调度异常: {e}")
        return 1


def _parse_task(task_input: str) -> dict:
    """解析任务输入：优先 JSON，其次 Markdown frontmatter，最后纯文本。
    归一化字段：requirement/desc/description → description，priority/deadline 原样保留。
    """
    s = task_input.strip()
    if s.startswith("{") or s.startswith("["):
        try:
            data = json.loads(s)
            if isinstance(data, list):
                data = data[0] if data else {}
            data = dict(data)
            # 关键：requirement/desc/description 统一归一到 description，避免要素漏传
            if "requirement" in data and "description" not in data:
                data["description"] = data.pop("requirement")
            if "desc" in data and "description" not in data:
                data["description"] = data.pop("desc")
            return data
        except json.JSONDecodeError:
            pass
    # Markdown 或纯文本：取首行非空作为标题
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    title = lines[0][:120] if lines else "AutoGPT 调度任务"
    return {"title": title, "description": s[:2000], "priority": "中"}


def _parse_elements(task_data: dict) -> dict:
    """AutoGPT 结构化需求拆解：从任务 JSON 中抽取设计要素清单。
    关键防线：防止整张海报被误判为纯色背景等局部特征。
    """
    desc = task_data.get("description") or task_data.get("requirement") or ""
    d = str(desc)
    elements = {}
    # 直接字段优先
    for key in ("插画", "文案", "文字", "配色", "装饰", "尺寸", "交付格式", "工期", "风格", "主视觉"):
        v = task_data.get(key)
        if v:
            elements[key] = str(v)
    # 从需求描述中按关键词抽取（存在即登记，供人工核验）
    kw_map = {
        "人物": "古风人物插画",
        "插画": "人物/古风插画",
        "灯笼": "灯笼装饰",
        "烟花": "烟花装饰",
        "书法": "书法标题（金榜题名大字）",
        "红": "红调主视觉",
        "国风": "国风喜庆版式",
        "CDR": "可编辑 CDR 源文件",
        "海报": "完整海报（图文结构）",
        "版式": "版式排版",
    }
    for kw, label in kw_map.items():
        if kw in d and label not in elements.values():
            elements.setdefault(label.split("（")[0], label)
    if not elements:
        elements["需求原文"] = d[:200]
    return elements


def _build_cmd(entry: Path, args_tpl: list, task_data: dict) -> list:
    """按参数模板组装命令；模板占位符缺省则直接传任务标题。
    flag(--xx) 与占位符({xx})成对处理：值缺省时跳过整对，避免出现悬空 flag。
    """
    cmd = [str(entry)]
    if not args_tpl:
        cmd.append(task_data.get("title", ""))
        return [c for c in cmd if c]

    def _val(key: str) -> str:
        # desc 占位符优先取 description，其次 requirement，再回退标题
        if key in ("desc", "description"):
            return task_data.get("description") or task_data.get("requirement") or task_data.get("title", "")
        # 优先级/工期缺省时不传（由下游默认值兜底），避免误把标题当工期
        if key in ("priority", "deadline"):
            return task_data.get(key, "")
        return task_data.get(key, task_data.get("title", ""))

    i = 0
    while i < len(args_tpl):
        tpl = args_tpl[i]
        # flag + 占位符成对（如 --desc {desc}）
        if tpl.startswith("--") and i + 1 < len(args_tpl) and "{" in args_tpl[i + 1]:
            val = _val(args_tpl[i + 1].strip("{}"))
            if val:
                cmd.append(tpl)
                cmd.append(val)
            i += 2
        else:
            val = _val(tpl.strip("{}"))
            if val:
                cmd.append(tpl if "{" not in tpl else val)
            i += 1
    return cmd


def status() -> int:
    """健康检查：AutoGPT 目录 / 桥接可调度的脚本 / 环境变量存在性。"""
    print("=" * 60)
    print("AutoGPT × ORCA 桥接 · 状态检查")
    print("=" * 60)
    print(f"AutoGPT 目录 (AUTOGPT_HOME): {AUTOGPT_DIR}  ->  {'存在' if AUTOGPT_DIR.exists() else '不存在(本地私有化部署后生效)'}")
    print(f"AutoGPT 任务目录: {AUTOGPT_TASKS_DIR}  ->  {'存在' if AUTOGPT_TASKS_DIR.exists() else '不存在'}")
    print("-" * 60)
    for name, info in WORKFLOW_REGISTRY.items():
        entry = info["entry"]
        mark = "✅" if entry.exists() else "⚠️ 待补"
        print(f"[{mark}] {name:<6} -> {entry.name}")
    print("-" * 60)
    missing = _check_env_ready()
    if missing:
        print(f"环境变量缺失(存在性): {', '.join(missing)}")
    else:
        print("环境变量: CNB_TOKEN/GH_TOKEN/抖音/小红书 Cookie 均就绪（仅校验存在性）")
    print("=" * 60)
    return 0


def trigger_workflow(workflow: str, title: str, desc: str) -> int:
    """AutoGPT 定时触发器入口：构造任务卡并 dispatch。"""
    task = {"title": title, "description": desc or title, "priority": "中"}
    return dispatch(json.dumps(task, ensure_ascii=False), workflow)


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="AutoGPT × ORCA 全链路桥接")
    sub = parser.add_subparsers(dest="cmd")

    p_dispatch = sub.add_parser("dispatch", help="调度任务")
    p_dispatch.add_argument("--task", required=True, help="任务 JSON/Markdown/纯文本")
    p_dispatch.add_argument("--workflow", choices=list(WORKFLOW_REGISTRY.keys()) + [""], default="",
                            help="四大赛道工作流")
    p_dispatch.add_argument("--verbose", action="store_true")

    sub.add_parser("status", help="状态检查")

    p_trigger = sub.add_parser("trigger", help="AutoGPT 定时触发器入口")
    p_trigger.add_argument("--workflow", required=True, choices=list(WORKFLOW_REGISTRY.keys()))
    p_trigger.add_argument("--title", required=True)
    p_trigger.add_argument("--desc", default="")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return 0

    if args.cmd == "dispatch":
        return dispatch(args.task, args.workflow or "", args.verbose)
    if args.cmd == "status":
        return status()
    if args.cmd == "trigger":
        return trigger_workflow(args.workflow, args.title, args.desc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
