#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 增强版守护进程（v2.0）

功能：
1. 持续扫描 fleet_exchange/incoming/ 发现新任务
2. 自动初始化任务目录 + 归档截图
3. 调用 pipeline_autopilot 推进流水线
4. 支持批量多订单自动排队处理
5. 看板数据实时刷新

用法：
    python scripts/pipeline_autopilot_daemon.py              # 默认30秒轮询
    python scripts/pipeline_autopilot_daemon.py --interval 15 # 15秒轮询
    python scripts/pipeline_autopilot_daemon.py --once        # 执行一次后退出
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 运行时产物目录（G 盘）
G_DRIVE_ROOT = Path(os.environ.get(
    "G_DRIVE_ROOT",
    "G:/WorkBuddy-Cache/企业微信群定制接单项目"
))
# 兼容镜像路径
G_MIRROR_ROOT = Path("G:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
if not G_DRIVE_ROOT.exists() and G_MIRROR_ROOT.exists():
    G_DRIVE_ROOT = G_MIRROR_ROOT
G_OUTPUTS = G_DRIVE_ROOT / "outputs"
G_LOGS = G_DRIVE_ROOT / "logs"
G_DELIVERABLES = G_DRIVE_ROOT / "deliverables"

PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
SCRIPTS = PROJECT / "scripts"
FLEET_IN = PROJECT / "fleet_exchange" / "incoming"
FLEET_DOING = PROJECT / "fleet_exchange" / "doing"
FLEET_RESULTS = PROJECT / "fleet_exchange" / "results"
OUTPUTS = G_OUTPUTS
LOG_FILE = G_LOGS / "daemon.log"

for d in [G_DRIVE_ROOT, G_OUTPUTS, G_LOGS, G_DELIVERABLES]:
    try:
        os.makedirs(str(d), exist_ok=True)
    except Exception as e:
        print(f"[WARN] 无法创建 G 盘目录 {d}: {e}", file=sys.stderr)

# 已处理的任务文件名缓存（避免重复处理）
PROCESSED_CACHE: set[str] = set()

# Python 路径（优先用系统 Python）
PYTHON_CANDIDATES = [
    Path("C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"),
    Path(sys.executable),
]
PYTHON = None
for p in PYTHON_CANDIDATES:
    if p.exists():
        PYTHON = str(p)
        break
if not PYTHON:
    PYTHON = sys.executable


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(str(LOG_FILE.parent), exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def extract_task_id(text: str) -> str | None:
    """从文本中提取 task_id"""
    for line in text.splitlines():
        if line.startswith("task_id:"):
            return line.split(":", 1)[1].strip()
    return None


def scan_new_tasks() -> list[Path]:
    """扫描 incoming 目录中的新任务"""
    if not FLEET_IN.exists():
        return []

    new_tasks = []
    for f in sorted(FLEET_IN.iterdir(), key=lambda x: x.stat().st_mtime):
        if f.is_file() and f.suffix == ".md" and f.name not in PROCESSED_CACHE:
            new_tasks.append(f)
    return new_tasks


def is_hermes_task(f: Path) -> bool:
    """判断是否是 Hermes 任务"""
    fname = f.name
    if "_Hermes_" in fname:
        return True
    try:
        text = f.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("to:") and "Hermes" in line:
                return True
            if line.startswith("---", 1):  # 第二个 --- 结束 frontmatter
                break
    except Exception:
        pass
    return False


def auto_init_task(task_file: Path):
    """自动初始化任务目录"""
    env = os.environ.copy()
    try:
        result = subprocess.run(
            [PYTHON, str(SCRIPTS / "auto_archive.py"), "init", str(task_file)],
            cwd=str(PROJECT), capture_output=True, text=True, env=env
        )
        if result.returncode == 0:
            log(f"  [ARCHIVE] 初始化完成: {task_file.name}")
        else:
            log(f"  [ARCHIVE] 初始化失败: {result.stderr}")
    except Exception as e:
        log(f"  [ARCHIVE] 异常: {e}")


def run_pipeline():
    """运行一次流水线自动驾驶"""
    env = os.environ.copy()
    try:
        result = subprocess.run(
            [PYTHON, str(SCRIPTS / "pipeline_autopilot.py")],
            cwd=str(PROJECT), capture_output=True, text=True, timeout=120, env=env
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    log(f"  [PIPELINE] {line}")
        else:
            log(f"  [PIPELINE] ERROR: {result.stderr}")
    except subprocess.TimeoutExpired:
        log("  [PIPELINE] 超时(120s)")
    except Exception as e:
        log(f"  [PIPELINE] 异常: {e}")


def generate_dashboard():
    """生成看板数据"""
    try:
        result = subprocess.run(
            [PYTHON, str(SCRIPTS / "pipeline_autopilot.py")],
            cwd=str(PROJECT), capture_output=True, text=True, timeout=60
        )
    except Exception:
        pass


def run_once() -> int:
    """执行一次扫描和处理，返回新处理的任务数"""
    new_tasks = scan_new_tasks()
    if not new_tasks:
        return 0

    count = 0
    for task_file in new_tasks:
        if is_hermes_task(task_file):
            log(f"[NEW] 发现新任务: {task_file.name}")
            PROCESSED_CACHE.add(task_file.name)
            auto_init_task(task_file)
            count += 1
        else:
            # 非 Hermes 任务也标记为已处理（跳过）
            PROCESSED_CACHE.add(task_file.name)

    if count > 0:
        log(f"[BATCH] 本轮处理 {count} 个新任务，推进流水线...")
        run_pipeline()

    return count


def main():
    parser = argparse.ArgumentParser(description="企业微信群接单守护进程")
    parser.add_argument("--interval", type=int, default=30, help="轮询间隔(秒)")
    parser.add_argument("--timeout", type=int, default=0, help="超时退出(秒), 0=永不退出")
    parser.add_argument("--once", action="store_true", help="执行一次后退出")
    args = parser.parse_args()

    log("=" * 50)
    log(f"守护进程启动 (v2.0)")
    log(f"  G_DRIVE_ROOT: {G_DRIVE_ROOT}")
    log(f"  轮询间隔: {args.interval}s")
    log(f"  超时退出: {'永不' if args.timeout == 0 else f'{args.timeout}s'}")
    log(f"  Python: {PYTHON}")
    log("=" * 50)

    # 预扫描：标记已有任务为已处理
    for f in scan_new_tasks():
        PROCESSED_CACHE.add(f.name)
    if PROCESSED_CACHE:
        log(f"[INIT] 已有 {len(PROCESSED_CACHE)} 个任务在队列中，跳过")

    total_processed = 0
    idle_since = time.time()

    while True:
        count = run_once()
        if count > 0:
            total_processed += count
            idle_since = time.time()
            log(f"[STATS] 累计处理: {total_processed} 个任务")
        else:
            elapsed = time.time() - idle_since
            if args.timeout > 0 and elapsed >= args.timeout:
                log(f"[EXIT] 连续 {args.timeout}s 无新任务，累计处理 {total_processed} 个，退出")
                break

        if args.once:
            log(f"[EXIT] 单次模式，处理 {total_processed} 个任务后退出")
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("[EXIT] 用户中断")
    except Exception as e:
        log(f"[FATAL] {e}")
        sys.exit(1)
