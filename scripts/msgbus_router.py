#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""msgbus_router.py — 消息总线路由守护进程
功能：轮询 msgbus/inbox/ 所有窗口，按 task_chain 自动转发消息。
当消息到达 chain 末端时，写入收件箱供 GUI 展示。

用法：
    python scripts/msgbus_router.py              # 默认5秒轮询
    python scripts/msgbus_router.py --interval 3  # 3秒轮询
    python scripts/msgbus_router.py --once        # 执行一次后退出
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
MSGBUS = PROJECT / "msgbus"
INBOX = MSGBUS / "inbox"
CONTEXT = MSGBUS / "context"
LOG_DIR = Path("G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs")

for d in [MSGBUS, INBOX, CONTEXT, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "msgbus_router.log"
PROCESSED: set[str] = set()  # 按 msg_id 去重

# 所有已知窗口
WINDOWS = [
    "hermes_gui", "hermes_cli",
    "codex_gui", "codex_cli",
    "claude_gui", "claude_cli",
]

# 修复(2026-07-28): router 与 consumer 抢跑同一队列是消息风暴根因之一。
# claude_cli / codex_cli 由 msgbus_agent_consumer.py 负责“处理后转发”，router 跳过。
CONSUMER_MANAGED = {"claude_cli", "codex_cli"}

# 修复(2026-07-28): 单实例锁，防止多 router 并行互相转发造成指数复制
LOCK_FILE = MSGBUS / "router.lock"


def _pid_alive(pid: int) -> bool:
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
    except Exception:
        pass
    return False


def acquire_single_instance_lock() -> bool:
    """原子单实例锁：用 O_EXCL 创建锁文件消除 TOCTOU 竞态。
    若锁文件已存在，检测其中 PID 是否存活：存活则退出(返回False)，
    已死则接管(删除旧锁后重新原子创建)。
    """
    try:
        if LOCK_FILE.exists():
            old = LOCK_FILE.read_text(encoding="utf-8").strip()
            if old.isdigit() and _pid_alive(int(old)):
                return False  # 旧实例仍存活，放弃
            # 旧锁对应的进程已死，清理后接管
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
        # 原子创建：O_CREAT | O_EXCL 保证任意时刻仅一个进程成功
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
        finally:
            os.close(fd)
        return True
    except FileExistsError:
        # 极短竞态窗口内另一进程抢先创建，视为已有实例
        return False
    except Exception:
        return True


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_json(path: Path) -> dict | None:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_json(path: Path, data: dict):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H%M%S")


def get_all_messages() -> list[tuple[Path, dict]]:
    """扫描所有窗口收件箱，返回 (文件路径, 消息内容) 列表"""
    results = []
    if not INBOX.exists():
        return results
    for win_dir in INBOX.iterdir():
        if not win_dir.is_dir():
            continue
        # 修复(2026-07-28): consumer 管辖队列由消费者“处理后转发”，router 跳过避免抢跑
        if win_dir.name in CONSUMER_MANAGED:
            continue
        for f in sorted(win_dir.iterdir(), key=lambda x: x.stat().st_mtime):
            if f.suffix == ".json" and f.name not in PROCESSED:
                msg = read_json(f)
                if msg:
                    results.append((f, msg))
    return results


def forward_msg(msg: dict, dst_window: str) -> str:
    """转发消息到目标窗口收件箱"""
    # 创建转发副本
    forwarded = dict(msg)
    forwarded["prev_dst"] = msg.get("dst", "")
    forwarded["dst"] = dst_window
    forwarded["forwarded_at"] = now_ts()
    forwarded["status"] = "pending"

    dst_dir = INBOX / dst_window
    dst_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{now_ts()}_{forwarded['msg_id'][:8]}_fwd.json"
    write_json(dst_dir / fname, forwarded)
    return fname


def update_context(msg: dict):
    """更新上下文快照（供双实例切换使用）"""
    agent = msg.get("dst", "").split("_")[0]  # hermes_gui → hermes
    ctx_file = CONTEXT / f"{agent}_context.json"
    ctx = {}
    if ctx_file.exists():
        ctx = read_json(ctx_file) or {}
    ctx["last_msg"] = msg
    ctx["last_update"] = now_ts()
    # 保留最近10条消息历史
    history = ctx.get("history", [])
    history.append({
        "msg_id": msg.get("msg_id"),
        "src": msg.get("src"),
        "dst": msg.get("dst"),
        "payload": msg.get("payload", "")[:200],
        "ts": msg.get("ts"),
    })
    ctx["history"] = history[-10:]
    write_json(ctx_file, ctx)


def process_message(fpath: Path, msg: dict) -> bool:
    """处理一条消息，返回是否成功"""
    dst = msg.get("dst", "")
    chain = msg.get("task_chain", [])
    status = msg.get("status", "pending")
    msg_id = msg.get("msg_id", "")

    # 修复(2026-07-28): 按 (msg_id, dst, chain_pos) 复合键去重。
    # 之前按裸 msg_id 去重会把同 ID 的 chain 末端消息误判为已处理 → 永远 pending
    dedup_key = f"{msg_id}@{dst}#{msg.get('chain_pos', '')}"
    if dedup_key in PROCESSED:
        return False
    msg_id = dedup_key

    # 已完成/已转发/处理中的消息跳过
    if status in ("done", "forwarded", "processing", "delivered"):
        PROCESSED.add(msg_id)
        return False

    # 检查 dst 是否匹配当前收件箱窗口
    actual_window = fpath.parent.name  # e.g. "hermes_cli"
    if dst != actual_window:
        # dst 和实际窗口不匹配，跳过
        PROCESSED.add(msg_id)
        return False

    # 更新上下文
    update_context(msg)

    if not chain:
        # 无 chain，直接投递到目标窗口（已完成）
        log(f"  [DELIVER] {msg_id[:8]} → {dst}（无chain，直接投递）")
        msg["status"] = "delivered"
        write_json(fpath, msg)
        PROCESSED.add(msg_id)
        return True

    # 有 chain，找到当前在 chain 的哪个位置
    # 修复(2026-07-28): 首尾同节点链中 chain.index(dst) 永远命中位置0造成无限循环风暴
    # → 优先使用 chain_pos 显式游标
    current_dst = dst
    idx = msg.get("chain_pos")
    if not isinstance(idx, int):
        try:
            idx = chain.index(current_dst)
        except ValueError:
            # dst 不在 chain 中，可能是初始投递
            log(f"  [SKIP] {msg_id[:8]} dst={dst} 不在 chain 中")
            PROCESSED.add(msg_id)
            return False

    if idx < len(chain) - 1:
        # 还没到 chain 末端，转发给下一个
        next_dst = chain[idx + 1]
        log(f"  [ROUTE] {msg_id[:8]} {dst} → {next_dst} (chain {idx+1}/{len(chain)})")
        msg["chain_pos"] = idx + 1
        forward_msg(msg, next_dst)
        msg["status"] = "forwarded"
        msg["forwarded_to"] = next_dst
        write_json(fpath, msg)
        PROCESSED.add(msg_id)
        return True
    else:
        # 已到 chain 末端，标记完成
        log(f"  [DONE] {msg_id[:8]} 到达 chain 末端 {dst}，标记完成")
        msg["status"] = "done"
        msg["done_at"] = now_ts()
        write_json(fpath, msg)
        PROCESSED.add(msg_id)
        return True


def run_once() -> int:
    """执行一次扫描和路由，返回处理的消息数"""
    messages = get_all_messages()
    if not messages:
        return 0

    count = 0
    for fpath, msg in messages:
        try:
            if process_message(fpath, msg):
                count += 1
        except Exception as e:
            log(f"  [ERROR] 处理 {fpath.name} 失败: {e}")
            PROCESSED.add(fpath.name)

    return count


def main():
    parser = argparse.ArgumentParser(description="msgbus 消息总线路由器")
    parser.add_argument("--interval", type=int, default=5, help="轮询间隔(秒)")
    parser.add_argument("--once", action="store_true", help="执行一次后退出")
    args = parser.parse_args()

    # 修复(2026-07-28): 单实例保护，多开是消息风暴根因
    if not acquire_single_instance_lock():
        log("[EXIT] 检测到已有 router 实例运行(router.lock PID存活)，本实例退出")
        sys.exit(0)

    log("=" * 50)
    log("msgbus 路由守护进程启动")
    log(f"  轮询间隔: {args.interval}s")
    log(f"  消息目录: {INBOX}")
    log("=" * 50)

    # 预扫描：标记已有消息
    for fpath, msg in get_all_messages():
        if msg.get("status") in ("done", "forwarded", "delivered"):
            PROCESSED.add(msg.get("msg_id", ""))
    if PROCESSED:
        log(f"[INIT] 已有 {len(PROCESSED)} 条已处理消息，跳过")

    total = 0
    while True:
        count = run_once()
        if count > 0:
            total += count
            log(f"[STATS] 累计路由: {total} 条消息")

        if args.once:
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
