#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 实单归档工具
版本：v1.0

将「01_正在执行实单」下已交付完成、尾款结清的项目文件夹，
移动到「02_已完结归档实单」对应品类目录（海报类/画册排版类/PPT制作类/视频图文类/其他类）。

用法：
   python scripts/archive_order.py <文件夹名或task_id> [--category 海报类]
   python scripts/archive_order.py "【20260725_科技折页画册】" --category 画册排版类

也可用 business_folders.py archive 子命令（二者等价）。
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
REAL_BASE = PROJECT_ROOT / "01_正在执行实单"
ARCHIVE_BASE = PROJECT_ROOT / "02_已完结归档实单"

ARCHIVE_CATEGORY_MAP = {
    "海报": "海报类", "画册": "画册排版类", "折页": "画册排版类",
    "ppt": "PPT制作类", "短视频": "视频图文类", "视频": "视频图文类",
    "钥匙扣": "其他类", "周边": "其他类", "包装": "其他类", "logo": "其他类",
}


def detect_category_key(name: str) -> str:
    t = name.lower()
    for k in ARCHIVE_CATEGORY_MAP:
        if k.lower() in t:
            return k
    return "其他"


def archive(name: str, category: str = None):
    target = None
    if (REAL_BASE / name).is_dir():
        target = REAL_BASE / name
    else:
        for d in REAL_BASE.iterdir():
            if d.is_dir() and name in d.name:
                target = d
                break
    if target is None:
        return False, f"在 01_正在执行实单 未找到匹配「{name}」的文件夹"
    if category is None:
        cat_key = detect_category_key(target.name)
        category = ARCHIVE_CATEGORY_MAP.get(cat_key, "其他类")
    dest = ARCHIVE_BASE / category / target.name
    os.makedirs(str(dest.parent), exist_ok=True)
    shutil.move(str(target), str(dest))
    return True, f"已归档到 02_已完结归档实单/{category}/{target.name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--category", default=None)
    args = ap.parse_args()
    ok, msg = archive(args.name, category=args.category)
    print(f"[{'OK' if ok else 'FAIL'}] {msg}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
