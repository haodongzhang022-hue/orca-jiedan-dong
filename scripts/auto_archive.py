#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 自动归档助手（v2.1）

职责：
1. 为新任务自动创建 G 盘 outputs/<task_id>/ 目录
2. 归档客户参考截图到 G 盘任务输出目录
3. 从 fleet_exchange/results/ 同步产出到 G 盘 outputs/
4. 从 G 盘 outputs/ 聚合到 E 盘 deliverables/（完成态入口）

目录策略：
- E 盘：项目源码、舰队总线、任务卡、看板 HTML、最终交付物入口
- G 盘：所有运行时产物（outputs/ 缓存、图片素材、logs/ 日志）
  通过 G_DRIVE_ROOT 环境变量配置，默认 G:/WorkBuddy-Cache/企业微信群定制接单项目

用法：
    python scripts/auto_archive.py init <任务卡路径>       # 初始化任务目录
    python scripts/auto_archive.py screenshot <任务ID> <图片路径>  # 归档截图到 G 盘
    python scripts/auto_archive.py sync <任务ID>           # 同步 results -> G 盘 outputs
    python scripts/auto_archive.py deliver <任务ID>        # 聚合到 E 盘 deliverables
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

E_PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
E_HOME = Path("E:/龙虾AI主控中心/我的AI分身")
E_WECHAT = E_HOME / "企业微信群" / "定制接单项目"

G_DRIVE_ROOT = Path(os.environ.get(
    "G_DRIVE_ROOT",
    "G:/WorkBuddy-Cache/企业微信群定制接单项目"
))
# 兼容镜像路径
G_MIRROR_ROOT = Path("G:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
if not G_DRIVE_ROOT.exists() and G_MIRROR_ROOT.exists():
    G_DRIVE_ROOT = G_MIRROR_ROOT
G_PROJECT = G_DRIVE_ROOT
G_OUTPUTS = G_PROJECT / "outputs"
G_LOGS = G_PROJECT / "logs"
G_DELIVERABLES = G_PROJECT / "deliverables"

FLEET = E_PROJECT / "fleet_exchange"
FLEET_IN = FLEET / "incoming"
FLEET_DOING = FLEET / "doing"
FLEET_RESULTS = FLEET / "results"
FLEET_DONE = FLEET / "done"

E_DELIVERABLES = E_WECHAT / "deliverables"
DASHBOARD = E_WECHAT / "任务看板"

E_LEGACY_OUTPUTS = E_PROJECT / "outputs"  # 旧 E 盘 outputs，兼容迁移

LOG_FILE = G_LOGS / "archive.log"


def ensure_dirs():
    for d in [G_OUTPUTS, G_LOGS, G_DELIVERABLES, E_DELIVERABLES, DASHBOARD]:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[WARN] 创建目录失败 {d}: {e}", file=sys.stderr)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # 兜底：E 盘项目日志
        try:
            fallback = E_PROJECT / "logs" / "archive.log"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            with fallback.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def extract_task_id(task_card_path: Path) -> str:
    """从任务卡提取 task_id"""
    try:
        text = task_card_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("task_id:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    name = task_card_path.stem
    m = re.match(r"(\d{8}_\d{6}_\d+)", name)
    return m.group(1) if m else name.split("__")[0]


def init_task(task_card_path: str):
    """初始化任务目录结构（G 盘）"""
    tc = Path(task_card_path)
    if not tc.exists():
        log(f"ERROR: 任务卡不存在: {tc}")
        sys.exit(1)

    task_id = extract_task_id(tc)
    out_dir = G_OUTPUTS / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 复制任务卡
    dest = out_dir / "任务卡.md"
    if not dest.exists():
        shutil.copy2(tc, dest)
        log(f"已归档任务卡: {dest}")

    # 创建子目录
    for sub in ["参考图", "产出方案", "审核报告"]:
        (out_dir / sub).mkdir(exist_ok=True)

    log(f"任务目录已初始化: {out_dir}")
    print(f"[TASK_DIR] {out_dir}")
    return task_id


def archive_screenshot(task_id: str, image_path: str):
    """归档客户参考截图到 G 盘"""
    src = Path(image_path)
    if not src.exists():
        log(f"ERROR: 图片不存在: {src}")
        sys.exit(1)

    out_dir = G_OUTPUTS / task_id / "参考图"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 按序号命名
    existing = list(out_dir.glob("*"))
    idx = len(existing) + 1
    ext = src.suffix or ".png"
    dest = out_dir / f"参考图_{idx:02d}{ext}"

    shutil.copy2(src, dest)
    log(f"已归档截图: {dest}")

    # 同时复制到任务根目录（最新一张作为主图）
    main_img = G_OUTPUTS / task_id / f"客户参考截图{ext}"
    shutil.copy2(src, main_img)
    log(f"已更新主图: {main_img}")

    print(f"[SCREENSHOT] {dest}")
    return dest


def sync_results(task_id: str):
    """从 fleet_exchange/results/ 同步产出到 G 盘 outputs/"""
    out_dir = G_OUTPUTS / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    synced = 0
    # 查找 results 目录中匹配的任务结果
    if FLEET_RESULTS.exists():
        for f in FLEET_RESULTS.iterdir():
            if f.is_file() and task_id in f.name:
                dest = out_dir / "产出方案" / f.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                synced += 1
                log(f"已同步结果: {f.name} -> {dest}")

    # 查找 done 目录中匹配的任务归档
    if FLEET_DONE.exists():
        for f in FLEET_DONE.iterdir():
            if f.is_file() and task_id in f.name:
                dest = out_dir / "任务归档" / f.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest)
                synced += 1

    log(f"同步完成: {task_id}, 共 {synced} 个文件")
    print(f"[SYNC] {synced} files synced")


def deliver_task(task_id: str):
    """聚合所有产出到 E 盘 deliverables/（最终入口）并镜像到 G 盘"""
    src_dir = G_OUTPUTS / task_id
    if not src_dir.exists():
        # 兜底：尝试旧 E 盘 outputs
        src_dir = E_LEGACY_OUTPUTS / task_id
        if not src_dir.exists():
            log(f"ERROR: 输出目录不存在: {src_dir}")
            sys.exit(1)

    e_dest = E_DELIVERABLES / task_id
    g_dest = G_DELIVERABLES / task_id
    e_dest.mkdir(parents=True, exist_ok=True)
    g_dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    for f in src_dir.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src_dir)
            e_d = e_dest / rel
            g_d = g_dest / rel
            e_d.parent.mkdir(parents=True, exist_ok=True)
            g_d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, e_d)
            shutil.copy2(f, g_d)
            copied += 1

    log(f"交付物已聚合: {task_id} -> E 盘: {e_dest} / G 盘: {g_dest} ({copied} 文件)")
    print(f"[DELIVER] E:{e_dest} | G:{g_dest} ({copied} files)")


def main():
    ensure_dirs()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init" and len(sys.argv) >= 3:
        init_task(sys.argv[2])
    elif cmd == "screenshot" and len(sys.argv) >= 4:
        archive_screenshot(sys.argv[2], sys.argv[3])
    elif cmd == "sync" and len(sys.argv) >= 3:
        sync_results(sys.argv[2])
    elif cmd == "deliver" and len(sys.argv) >= 3:
        deliver_task(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
