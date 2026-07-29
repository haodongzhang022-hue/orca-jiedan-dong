#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""msgbus_agent_consumer.py — Agent 消息消费者
轮询指定窗口的收件箱，调用对应 CLI 处理消息，转发到 chain 下一环节。

用法：
    python scripts/msgbus_agent_consumer.py --agent claude --interval 5
    python scripts/msgbus_agent_consumer.py --agent codex --interval 5
    python scripts/msgbus_agent_consumer.py --agent claude --once
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
MSGBUS = PROJECT / "msgbus"
INBOX = MSGBUS / "inbox"
CONTEXT = MSGBUS / "context"
LOG_DIR = Path("G:/龙虾AI主控中心/ORCA数据/企业微信群定制接单项目/logs")

# 工作树目录
WORKTREES = {
    "claude": PROJECT / "worktrees" / "claude",
    "codex": PROJECT / "worktrees" / "codex",
    "hermes": PROJECT / "worktrees" / "hermes",
}

# CLI 命令配置
CLI_CONFIG = {
    "claude": {
        "cmd": ["I:/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe", "-p"],
        "timeout": 120,
    },
    "codex": {
        # 修复(2026-07-28): Codex 0.46 已移除 --quiet/-q，非交互调用须用 exec 子命令；
        # 模型不再强制 o3（不存在于 MiMO 链路），走 ~/.codex/config.toml 默认 aicodeswitch/mimo
        "cmd": ["node", "I:/npm/node_modules/@openai/codex/bin/codex.js", "exec", "--skip-git-repo-check"],
        "timeout": 120,
    },
}

for d in [LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "msgbus_consumer.log"
PROCESSED: set[str] = set()  # 按 msg_id 去重


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


def acquire_single_instance_lock(agent: str) -> bool:
    """单实例锁，防止同一 agent 多个消费者并行重复处理。
    使用 O_EXCL 原子创建消除 TOCTOU 竞态；旧锁 PID 已死则接管。
    """
    lock_file = MSGBUS / f"consumer_{agent}.lock"
    try:
        if lock_file.exists():
            old = lock_file.read_text(encoding="utf-8").strip()
            if old.isdigit() and _pid_alive(int(old)):
                return False
            try:
                lock_file.unlink()
            except Exception:
                pass
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
        finally:
            os.close(fd)
        return True
    except FileExistsError:
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


def call_claude(prompt: str, workdir: Path) -> str:
    """调用 Claude Code CLI 处理消息"""
    cfg = CLI_CONFIG["claude"]
    env = os.environ.copy()
    try:
        # claude -p reads from stdin
        result = subprocess.run(
            cfg["cmd"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=cfg["timeout"],
            cwd=str(workdir),
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[Claude Error] returncode={result.returncode}\nstdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"
    except subprocess.TimeoutExpired:
        return "[Claude Error] 超时(120s)"
    except Exception as e:
        return f"[Claude Error] {e}"


def call_codex(prompt: str, workdir: Path) -> str:
    """调用 Codex CLI 处理消息"""
    cfg = CLI_CONFIG["codex"]
    env = os.environ.copy()
    try:
        result = subprocess.run(
            cfg["cmd"] + [prompt],
            capture_output=True,
            text=True,
            timeout=cfg["timeout"],
            cwd=str(workdir),
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        return output if output else "[Codex] 无输出"
    except subprocess.TimeoutExpired:
        return "[Codex Error] 超时(120s)"
    except Exception as e:
        return f"[Codex Error] {e}"


CLI_CALLERS = {
    "claude": call_claude,
    "codex": call_codex,
}


def forward_msg(msg: dict, dst_window: str) -> Path:
    """转发消息到目标窗口收件箱"""
    forwarded = dict(msg)
    forwarded["prev_dst"] = msg.get("dst", "")
    forwarded["dst"] = dst_window
    forwarded["forwarded_at"] = now_ts()
    forwarded["status"] = "pending"

    dst_dir = INBOX / dst_window
    dst_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{now_ts()}_{forwarded['msg_id'][:8]}_fwd.json"
    fpath = dst_dir / fname
    write_json(fpath, forwarded)
    return fpath


def update_context(agent: str, msg: dict, response: str):
    """更新上下文快照"""
    ctx_file = CONTEXT / f"{agent}_context.json"
    ctx = {}
    if ctx_file.exists():
        ctx = read_json(ctx_file) or {}
    ctx["last_msg"] = msg
    ctx["last_response"] = response[:500]
    ctx["last_update"] = now_ts()
    history = ctx.get("history", [])
    history.append({
        "msg_id": msg.get("msg_id"),
        "src": msg.get("src"),
        "response_preview": response[:200],
        "ts": now_ts(),
    })
    ctx["history"] = history[-10:]
    write_json(ctx_file, ctx)


def process_message(agent: str, fpath: Path, msg: dict) -> bool:
    """处理一条消息"""
    dst = msg.get("dst", "")
    chain = msg.get("task_chain", [])
    payload = msg.get("payload", "")
    status = msg.get("status", "pending")
    msg_id = msg.get("msg_id", "")

    # 按 msg_id 去重
    if msg_id in PROCESSED:
        return False

    if status in ("done", "processing", "forwarded", "delivered"):
        PROCESSED.add(msg_id)
        return False

    # 标记为处理中
    msg["status"] = "processing"
    write_json(fpath, msg)

    log(f"  [PROCESS] {msg_id[:8]} 调用 {agent} CLI 处理...")

    # 调用 CLI
    workdir = WORKTREES.get(agent, PROJECT)
    caller = CLI_CALLERS.get(agent)
    if not caller:
        log(f"  [ERROR] 未知 agent: {agent}")
        PROCESSED.add(fpath.name)
        return False

    response = caller(payload, workdir)
    log(f"  [RESPONSE] {msg_id[:8]} {agent} 回复 {len(response)} 字符")

    # 更新上下文
    update_context(agent, msg, response)

    # 将回复写入当前消息
    msg["response"] = response
    msg["responded_at"] = now_ts()

    # 查找 chain 中的下一个
    # 修复(2026-07-28): 首尾同节点链(如 hermes→claude→codex→hermes)中 chain.index(dst)
    # 永远命中位置0导致无限循环风暴 → 引入 chain_pos 显式游标
    try:
        idx = msg.get("chain_pos")
        if not isinstance(idx, int):
            idx = chain.index(dst)
        if idx < len(chain) - 1:
            next_dst = chain[idx + 1]
            # 把回复作为 payload 转发
            forward_payload = f"[来自 {agent} 的回复]\n\n{response}"
            forward_msg({
                "msg_id": msg_id,
                "ts": now_ts(),
                "src": dst,
                "dst": next_dst,
                "type": "text",
                "payload": forward_payload,
                "task_chain": chain,
                "chain_pos": idx + 1,
                "status": "pending",
                "retries": 0,
                "project": msg.get("project", ""),
            }, next_dst)
            msg["status"] = "forwarded"
            msg["forwarded_to"] = next_dst
            log(f"  [FORWARD] {msg_id[:8]} → {next_dst}")
        else:
            msg["status"] = "done"
            msg["done_at"] = now_ts()
            log(f"  [DONE] {msg_id[:8]} chain 完成")
    except ValueError:
        msg["status"] = "done"
        log(f"  [DONE] {msg_id[:8]} dst 不在 chain 中，标记完成")

    write_json(fpath, msg)
    PROCESSED.add(msg_id)
    return True


def run_once(agent: str) -> int:
    """扫描并处理一次"""
    inbox_dir = INBOX / f"{agent}_cli"
    if not inbox_dir.exists():
        return 0

    count = 0
    for f in sorted(inbox_dir.iterdir(), key=lambda x: x.stat().st_mtime):
        if f.suffix != ".json":
            continue
        msg = read_json(f)
        if not msg:
            continue
        msg_id = msg.get("msg_id", "")
        if msg_id in PROCESSED:
            continue
        if msg.get("status") in ("done", "forwarded", "processing", "delivered"):
            PROCESSED.add(msg_id)
            continue
        try:
            if process_message(agent, f, msg):
                count += 1
        except Exception as e:
            log(f"  [ERROR] {f.name}: {e}")
            PROCESSED.add(msg_id)

    return count


def main():
    parser = argparse.ArgumentParser(description="Agent 消息消费者")
    parser.add_argument("--agent", required=True, choices=["claude", "codex", "hermes"])
    parser.add_argument("--interval", type=int, default=5, help="轮询间隔(秒)")
    parser.add_argument("--once", action="store_true", help="执行一次后退出")
    args = parser.parse_args()

    # 修复(2026-07-28): 强制单实例锁，防止同 agent 多个消费者并行重复处理
    # (此前函数已定义但 main 未调用，导致 3 个 claude + 3 个 codex 消费者并存抢队列)
    if not acquire_single_instance_lock(args.agent):
        log(f"[EXIT] 检测到 {args.agent} 已有消费者实例运行，本进程退出（单实例锁保护）")
        sys.exit(0)

    log("=" * 50)
    log(f"{args.agent} 消费者启动")
    log(f"  收件箱: {INBOX / f'{args.agent}_cli'}")
    log(f"  轮询间隔: {args.interval}s")
    log("=" * 50)

    # 预扫描
    inbox_dir = INBOX / f"{args.agent}_cli"
    if inbox_dir.exists():
        for f in inbox_dir.iterdir():
            if f.suffix == ".json":
                msg = read_json(f)
                if msg and msg.get("status") in ("done", "forwarded", "delivered"):
                    PROCESSED.add(msg.get("msg_id", ""))
    if PROCESSED:
        log(f"[INIT] 已有 {len(PROCESSED)} 条已处理消息，跳过")

    total = 0
    while True:
        count = run_once(args.agent)
        if count > 0:
            total += count
            log(f"[STATS] 累计处理: {total} 条消息")

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
