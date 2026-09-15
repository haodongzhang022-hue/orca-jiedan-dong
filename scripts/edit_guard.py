#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
edit_guard.py —— 龙虾编辑写竞态守卫 v1.0（零积分 / 纯 stdlib / Windows 优先）

解决什么：
  同一文件「多处修改」时，逐次 read-modify-write 是非原子的。
  并行/连续多个编辑会互相覆盖（静默丢失，工具却报 success）
  或抢锁失败（Windows EBUSY: resource busy or locked）。
  这是「假成功」第 6 形态 —— 不报错、不崩溃，但改动没落盘。

核心思路：
  把 N 处修改收敛成「一次内存替换 + 一次原子落盘 + 一次回读逐项断言」。

用法：
  # 1) 原子应用多处修改（推荐，替代连续多次 Edit）
  python edit_guard.py apply <file> --patch patch.json
  python edit_guard.py apply <file> --old "a" --new "b" [--old2 ...]   # 简易：命令行只能一条，多条请用 patch.json

  # 2) 只回读校验（不写盘），确认改动是否真的在
  python edit_guard.py verify <file> --patch patch.json

  # 3) 查看指纹（sha256/行数/编码/换行）
  python edit_guard.py fingerprint <file>

  # 4) 探测文件是否被占用（能否独占写）
  python edit_guard.py locktest <file>

patch.json 格式：
{
  "edits": [
    {"old": "version: 0.0.0", "new": "version: 1.0.0"},
    {"old": "alpha: AAAA",    "new": "alpha: ALPHA", "count": 1}
  ],
  "assert_old_absent": true     // 可选，默认 true：断言 old 文本已消失
}
  count: 期望替换次数（默认 1）；0 表示「替换所有」。

退出码：
  0 = 全部断言通过
  1 = 有断言未通过（改动没落地或部分丢失）
  2 = 用法/文件错误

作者：汤小龙（AI 分身）· 2026-09-16
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime

VER = "1.0.0"


# ---------- 基础工具 ----------

def _read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def _detect(raw: bytes):
    """检测 BOM / 换行风格，返回 (encoding, newline)"""
    if raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            enc = "gbk"  # Windows 中文环境兜底（bat/cmd 常见）
    nl = "\r\n" if b"\r\n" in raw else "\n"
    return enc, nl


def fingerprint(path):
    raw = _read_bytes(path)
    enc, nl = _detect(raw)
    try:
        text = raw.decode(enc)
    except Exception:
        text = raw.decode(enc, errors="replace")
    return {
        "path": os.path.abspath(path),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "lines": text.count("\n") + (0 if text.endswith("\n") or not text else 1),
        "encoding": enc,
        "newline": "CRLF" if nl == "\r\n" else "LF",
        "mtime": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds"),
    }


def locktest(path, tries=5, wait=0.15):
    """探测文件能否被独占打开（Windows 上被占用会 PermissionError/EBUSY）"""
    for i in range(tries):
        try:
            fh = os.open(path, os.O_RDWR | getattr(os, "O_BINARY", 0))
            os.close(fh)
            return True, i
        except OSError as e:
            if i == tries - 1:
                return False, f"{type(e).__name__}: {e}"
            time.sleep(wait)
    return False, "unknown"


# ---------- 原子写入 ----------

def atomic_write(path, raw: bytes, backup=True):
    """写前备份 + 同目录临时文件 + os.replace 原子替换"""
    bak = None
    if backup and os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = f"{path}.bak_{ts}"
        shutil.copy2(path, bak)

    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".edit_guard_", dir=d)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        for _ in range(5):
            try:
                os.replace(tmp, path)   # Windows: 原子替换
                return True, bak
            except OSError as e:
                if "PermissionError" in str(type(e)) or getattr(e, "winerror", 0) in (5, 13, 32):
                    time.sleep(0.2)
                    continue
                raise
        return False, bak
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ---------- 补丁应用 ----------

def load_patch(patch_path):
    with open(patch_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    edits = data.get("edits") or []
    if not edits:
        raise ValueError("patch.json 里没有 edits")
    for i, e in enumerate(edits):
        if "old" not in e or "new" not in e:
            raise ValueError(f"第 {i} 条 edit 缺 old/new")
    assert_old_absent = data.get("assert_old_absent", True)
    return edits, assert_old_absent


def apply_in_memory(text, edits):
    """在内存中一次性完成全部替换，返回 (new_text, 每条结果)"""
    results = []
    for i, e in enumerate(edits):
        old, new = e["old"], e["new"]
        expect = e.get("count", 1)
        n = text.count(old)
        if expect == 0:                       # 0 = 全部替换
            text = text.replace(old, new)
            actual = n
            ok = True
        else:
            if n != expect:
                ok = False
                actual = 0
            else:
                text = text.replace(old, new, expect)
                actual = expect
                ok = True
        results.append({
            "index": i,
            "old": old[:60],
            "new": new[:60],
            "found": n,
            "expected": expect,
            "replaced": actual if ok else 0,
            "ok": ok,
        })
    return text, results


def verify_on_disk(path, edits, assert_old_absent=True):
    """回读校验：new 必须都在；可选断言 old 已消失"""
    raw = _read_bytes(path)
    enc, _ = _detect(raw)
    text = raw.decode(enc, errors="replace")
    checks = []
    for i, e in enumerate(edits):
        new_present = e["new"] in text
        old_present = e["old"] in text
        ok = new_present and ((not assert_old_absent) or (not old_present))
        checks.append({
            "index": i,
            "new_present": new_present,
            "old_still_present": old_present,
            "ok": ok,
        })
    return checks, text


# ---------- CLI ----------

def cmd_apply(args):
    path = args.file
    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        return 2

    if args.patch:
        edits, assert_old_absent = load_patch(args.patch)
    else:
        if not (args.old and args.new is not None):
            print(json.dumps({"error": "需要 --patch 或同时给 --old/--new"}, ensure_ascii=False))
            return 2
        edits = [{"old": args.old, "new": args.new, "count": args.count}]
        assert_old_absent = True

    before = fingerprint(path)
    ok_lock, lockinfo = locktest(path)
    if not ok_lock and not args.force:
        print(json.dumps({
            "error": "文件被占用（写入会被拒绝或覆盖）",
            "detail": lockinfo,
            "hint": "稍后重试，或加 --force 强制原子替换（os.replace 通常仍可成功）",
        }, ensure_ascii=False, indent=2))
        return 1

    raw0 = _read_bytes(path)
    enc, nl = _detect(raw0)
    text = raw0.decode(enc)

    new_text, results = apply_in_memory(text, edits)

    failed_in_mem = [r for r in results if not r["ok"]]
    if failed_in_mem and not args.partial:
        print(json.dumps({
            "error": "内存替换阶段就有条目未匹配，已放弃写盘（未改动原文件）",
            "failed": failed_in_mem,
            "before": before,
            "hint": "检查 old 文本是否与磁盘完全一致（注意空格/换行/编码）；或用 --partial 允许部分成功",
        }, ensure_ascii=False, indent=2))
        return 1

    # 保持原换行风格与编码
    out = new_text.replace("\r\n", "\n").replace("\n", nl)
    ok_write, bak = atomic_write(path, out.encode(enc), backup=not args.no_backup)
    if not ok_write:
        print(json.dumps({"error": "原子写入失败（os.replace 被拒）", "backup": bak},
                         ensure_ascii=False, indent=2))
        return 1

    checks, _ = verify_on_disk(path, [e for e, r in zip(edits, results) if r["ok"]],
                               assert_old_absent)
    after = fingerprint(path)

    all_ok = all(c["ok"] for c in checks) and len(checks) == len([r for r in results if r["ok"]])
    report = {
        "tool": "edit_guard", "version": VER, "action": "apply",
        "file": os.path.abspath(path),
        "backup": bak,
        "edits_total": len(edits),
        "edits_ok": sum(1 for r in results if r["ok"]),
        "in_memory": results,
        "on_disk_verify": checks,
        "all_assertions_passed": bool(all_ok),
        "sha256_before": before["sha256"], "sha256_after": after["sha256"],
        "changed": before["sha256"] != after["sha256"],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    return 0 if all_ok else 1


def cmd_verify(args):
    path = args.file
    if not os.path.exists(path):
        print(json.dumps({"error": f"文件不存在: {path}"}, ensure_ascii=False))
        return 2
    edits, assert_old_absent = load_patch(args.patch)
    checks, _ = verify_on_disk(path, edits, assert_old_absent)
    all_ok = all(c["ok"] for c in checks)
    report = {
        "tool": "edit_guard", "version": VER, "action": "verify",
        "file": os.path.abspath(path),
        "checks": checks,
        "all_assertions_passed": all_ok,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


def cmd_fingerprint(args):
    print(json.dumps(fingerprint(args.file), ensure_ascii=False, indent=2))
    return 0


def cmd_locktest(args):
    ok, info = locktest(args.file)
    print(json.dumps({"file": args.file, "writable": ok, "detail": info},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="龙虾编辑写竞态守卫 v" + VER)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("apply", help="原子应用多处修改（替代连续多次 Edit）")
    p1.add_argument("file")
    p1.add_argument("--patch", help="patch.json 路径")
    p1.add_argument("--old"); p1.add_argument("--new"); p1.add_argument("--count", type=int, default=1)
    p1.add_argument("--no-backup", action="store_true")
    p1.add_argument("--force", action="store_true", help="文件被占用时仍强制原子替换")
    p1.add_argument("--partial", action="store_true", help="允许部分条目未匹配仍写盘")
    p1.add_argument("--report", help="报告 JSON 输出路径")
    p1.set_defaults(func=cmd_apply)

    p2 = sub.add_parser("verify", help="回读校验改动是否真的落地")
    p2.add_argument("file"); p2.add_argument("--patch", required=True)
    p2.set_defaults(func=cmd_verify)

    p3 = sub.add_parser("fingerprint", help="输出 sha256/行数/编码/换行")
    p3.add_argument("file")
    p3.set_defaults(func=cmd_fingerprint)

    p4 = sub.add_parser("locktest", help="探测文件是否被占用")
    p4.add_argument("file")
    p4.set_defaults(func=cmd_locktest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
