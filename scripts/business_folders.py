#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 业务目录脚手架
版本：v1.0

职责：
1. 根据任务卡 frontmatter 判定「模拟演练」vs「真实付费单」：
   - simulation: true                      -> 模拟
   - real_order_min >= 300（且非 simulation）-> 真实付费单
   - 其余（<300 的低价需求）              -> 模拟（仅内部跑通流水线，不接真实交易）
2. 按品类把新需求落库到对应业务目录：
   - 模拟 -> 00_模拟演练案例库/<品类>/
   - 真实 -> 01_正在执行实单/
3. 每个独立需求生成一个【日期_简述】项目文件夹，内部标配：
   聊天记录 / 参考原图 / 需求确认文档 / 工程源文件 / 各版本稿件 / 最终交付文件
4. 提供 archive_order() 将「正在执行」移动到「已完结归档」对应品类。

运行：
   python scripts/business_folders.py scaffold <任务卡.md> [--date 20260725]
   python scripts/business_folders.py archive  <【日期_简述】文件夹名或task_id> [--category 海报类]

被 pipeline_autopilot.py 调用时，仅做目录创建（失败静默返回 None，不中断主流程）。
"""
import argparse
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
PROJECT_ROOT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
SIM_BASE = PROJECT_ROOT / "00_模拟演练案例库"
REAL_BASE = PROJECT_ROOT / "01_正在执行实单"
ARCHIVE_BASE = PROJECT_ROOT / "02_已完结归档实单"

# 品类 -> 模拟案例子目录
SIM_CATEGORY_MAP = {
    "海报": "海报设计案例",
    "画册": "画册折页案例",
    "折页": "画册折页案例",
    "ppt": "PPT修改排版案例",
    "短视频": "短视频物料案例",
    "视频": "短视频物料案例",
    "钥匙扣": "其他品类案例",
    "周边": "其他品类案例",
    "包装": "其他品类案例",
    "logo": "其他品类案例",
}
# 品类 -> 归档子目录
ARCHIVE_CATEGORY_MAP = {
    "海报": "海报类",
    "画册": "画册排版类",
    "折页": "画册排版类",
    "ppt": "PPT制作类",
    "短视频": "视频图文类",
    "视频": "视频图文类",
    "钥匙扣": "其他类",
    "周边": "其他类",
    "包装": "其他类",
    "logo": "其他类",
}

# 单需求项目文件夹标配子目录
STD_SUBFOLDERS = ["聊天记录", "参考原图", "需求确认文档", "工程源文件", "各版本稿件", "最终交付文件"]


# ============================================================
# 工具函数
# ============================================================
def read_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = {}
    for line in parts[1].strip().splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def classify(fm: dict) -> tuple:
    """返回 (kind, reason)。kind in {'sim','real'}"""
    sim_flag = str(fm.get("simulation", "false")).lower() in ("1", "true", "yes", "on")
    try:
        price = int(str(fm.get("real_order_min", "300")).strip())
    except Exception:
        price = 300
    if sim_flag:
        return "sim", "simulation=true（标记为模拟）"
    if price >= 300:
        return "real", f"real_order_min={price} >= 300（达实单门槛）"
    return "sim", f"real_order_min={price} < 300（低价需求，按模拟演练处理）"


def detect_category_key(title: str) -> str:
    t = (title or "").lower()
    for key in SIM_CATEGORY_MAP:
        if key.lower() in t:
            return key
    return "其他"


def make_brief_from_title(title: str) -> str:
    """从任务卡文件名/标题提取可读简述"""
    brief = title
    brief = re.sub(r"^.*?__Hermes_", "", brief)
    brief = re.sub(r"^.*?__", "", brief)
    brief = re.sub(r"\.md$", "", brief)
    brief = brief.replace("_", " ").strip()
    return brief or "未命名需求"


def scaffold_order(task_id: str, title: str, fm: dict, date_str: str = None, copy_card: Path = None):
    """创建业务项目文件夹。成功返回 (proj_dir: Path, kind, reason)，失败返回 (None, kind, error_msg)"""
    kind, reason = classify(fm)
    if date_str is None:
        m = re.match(r"(\d{8})", task_id)
        date_str = m.group(1) if m else datetime.now().strftime("%Y%m%d")
    brief = make_brief_from_title(title)
    folder_name = f"【{date_str}_{brief}】"

    if kind == "real":
        proj_dir = REAL_BASE / folder_name
    else:
        cat_key = detect_category_key(title)
        cat_dir = SIM_CATEGORY_MAP.get(cat_key, "其他品类案例")
        proj_dir = SIM_BASE / cat_dir / folder_name

    try:
        for sf in STD_SUBFOLDERS:
            os.makedirs(str(proj_dir / sf), exist_ok=True)
        # 把原始需求卡副本放进「需求确认文档」
        if copy_card and Path(copy_card).exists():
            try:
                shutil.copy2(str(copy_card), str(proj_dir / "需求确认文档" / Path(copy_card).name))
            except Exception:
                pass
    except Exception as e:
        return None, kind, str(e)
    return proj_dir, kind, reason


def archive_order(folder_name_or_taskid: str, category: str = None):
    """将 01_正在执行实单 下的项目文件夹移动到 02_已完结归档实单/<品类>/。
    品类可由 --category 指定，否则从名称推断。"""
    # 在 REAL_BASE 下查找匹配文件夹
    target = None
    if (REAL_BASE / folder_name_or_taskid).is_dir():
        target = REAL_BASE / folder_name_or_taskid
    else:
        for d in REAL_BASE.iterdir():
            if d.is_dir() and folder_name_or_taskid in d.name:
                target = d
                break
    if target is None:
        return False, f"在 01_正在执行实单 未找到匹配「{folder_name_or_taskid}」的文件夹"

    if category is None:
        cat_key = detect_category_key(target.name)
        category = ARCHIVE_CATEGORY_MAP.get(cat_key, "其他类")
    dest = ARCHIVE_BASE / category / target.name
    try:
        os.makedirs(str(dest.parent), exist_ok=True)
        shutil.move(str(target), str(dest))
    except Exception as e:
        return False, f"归档失败: {e}"
    return True, f"已归档到 02_已完结归档实单/{category}/{target.name}"


# ============================================================
# CLI
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="业务目录脚手架")
    sub = ap.add_subparsers(dest="cmd")

    sp = sub.add_parser("scaffold", help="脚手架一个新需求项目文件夹")
    sp.add_argument("task_card", help="任务卡 .md 路径")
    sp.add_argument("--date", default=None, help="日期前缀，默认从 task_id 取")

    sa = sub.add_parser("archive", help="归档已完结实单")
    sa.add_argument("name", help="文件夹名或 task_id")
    sa.add_argument("--category", default=None, help="归档品类（海报类/画册排版类/PPT制作类/视频图文类/其他类）")

    args = ap.parse_args()
    if args.cmd == "scaffold":
        card = Path(args.task_card)
        if not card.exists():
            print(f"[ERROR] 任务卡不存在: {card}")
            sys.exit(1)
        fm = read_frontmatter(card)
        task_id = fm.get("task_id", card.stem.split("_")[0])
        proj_dir, kind, info = scaffold_order(task_id, card.name, fm, date_str=args.date, copy_card=card)
        if proj_dir is None:
            print(f"[FAIL] {info}")
            sys.exit(1)
        print(f"[OK] 类型={kind} 原因={info}")
        print(f"     路径={proj_dir}")
        print(f"     标配子目录={STD_SUBFOLDERS}")
    elif args.cmd == "archive":
        ok, msg = archive_order(args.name, category=args.category)
        print(f"[{'OK' if ok else 'FAIL'}] {msg}")
        sys.exit(0 if ok else 1)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
