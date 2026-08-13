# -*- coding: utf-8 -*-
"""
watch_codex_catalog.py  v1.2  (2026-08-13 加固版)
==================================================
Hermes codex-model-catalog.json 守护脚本（根治 "unknown variant max"）

背景：
  Hermes 每次新建群聊会话都会重新生成 codex-model-catalog.json，自定义
  provider 的模板档位数组含 7 档推理级别（含 "effort": "max"），而 Codex CLI
  只认 6 档（none/minimal/low/medium/high/xhigh），JSON 解析直接失败。

本脚本做三件事（根本防线 = 防生成，非仅事后修复）：
  1. 全量扫描修复：扫描 coding-agent 目录下所有 catalog，把 "max" 换 "xhigh"
  2. 模板源头自愈：若 Hermes 更新把模板（webui/dist/server/index.js）的 max
     档位带回来，自动再次剔除 —— 覆盖"被更新覆盖"场景
  3. 日志落盘：每次运行记录到 logs/catalog_guard.log，便于排查定时任务
     是否真实执行（此前 Python312 路径失效导致任务静默失败的教训）

用法：
  python watch_codex_catalog.py          # 前台常驻（30s 轮询）
  python watch_codex_catalog.py --once   # 只扫描修复一次后退出（配计划任务用）

兼容性：
  - 纯标准库，无第三方依赖
  - 编码统一 UTF-8，适配 Windows 中文路径
"""
import argparse
import json
import os
import re
import sys
import time

CODING_AGENT_DIR = r"C:\Users\Administrator\.hermes-web-ui\coding-agent"
TEMPLATE_FILE = r"C:\Users\Administrator\AppData\Local\Programs\Hermes Studio\resources\webui\dist\server\index.js"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "catalog_guard.log")

MAX_STR = '"effort": "max"'
XHIGH_STR = '"effort": "xhigh"'
# 模板中 max 的两种实际形态（2026-08-13 实测）：
#   对象格式: {effort:"max",description:"Maximum reasoning depth ..."}
#   数组格式: ["default","none","minimal","low","medium","high","xhigh","max"]
TEMPLATE_MAX_OBJ = '{effort:"max",description:"Maximum reasoning depth for the hardest quality-first tasks"}'
TEMPLATE_MAX_OBJ_ALT = '{effort:"max",'
TEMPLATE_ARRAY_MAX = '"xhigh","max"'
TEMPLATE_ARRAY_MAX_REV = '"max","xhigh"'          # 变体：顺序可能颠倒
TEMPLATE_ARRAY_MAX_TAIL = ',"max"]'                # 变体：max 挂在数组尾部

fixed_total = 0


def log(msg):
    """日志落盘（UTF-8），同时 stdout 输出。"""
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        logdir = os.path.dirname(LOG_FILE)
        if logdir and not os.path.isdir(logdir):
            os.makedirs(logdir, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def fix_catalog(path):
    """修复单个 catalog：max -> xhigh。返回 True 表示有改动。"""
    global fixed_total
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False
    if MAX_STR not in content:
        return False
    new_content = content.replace(MAX_STR, XHIGH_STR)
    try:
        json.loads(new_content)
    except json.JSONDecodeError as e:
        log("[SKIP] %s 替换后 JSON 解析失败: %s" % (path, e))
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    fixed_total += 1
    log("[FIXED] %s" % path)
    return True


def scan_and_fix():
    """全量扫描修复。返回本次修复数量。"""
    n = 0
    for root, _dirs, files in os.walk(CODING_AGENT_DIR):
        for name in files:
            if name == "codex-model-catalog.json":
                if fix_catalog(os.path.join(root, name)):
                    n += 1
    return n


def self_heal_template():
    """模板源头自愈：若 Hermes 更新把模板的 max 档带回来，再次剔除（治本）。"""
    if not os.path.exists(TEMPLATE_FILE):
        return False
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return False
    orig = content

    # 1) 对象格式: {effort:"max",...} —— 完整对象或前缀两种写法都剔除
    if TEMPLATE_MAX_OBJ in content:
        content = content.replace("," + TEMPLATE_MAX_OBJ, "")
    if TEMPLATE_MAX_OBJ_ALT in content:
        # 兜底：剔除 {effort:"max", 起始的对象（到下一个 } 结束）
        content = re.sub(r'\{\s*effort\s*:\s*"max"[^}]*\},?', '', content)

    # 2) 数组格式及变体: "xhigh","max" / "max","xhigh" / ,"max"]
    content = content.replace(TEMPLATE_ARRAY_MAX, '"xhigh"')
    content = content.replace(TEMPLATE_ARRAY_MAX_REV, '"xhigh"')
    content = content.replace(TEMPLATE_ARRAY_MAX_TAIL, '"]')

    # 3) 通用兜底：集合/数组里的独立 "max" 元素（紧跟引号逗号分隔）
    content = re.sub(r'"xhigh"\s*,\s*"max"', '"xhigh"', content)
    content = re.sub(r'"max"\s*,\s*"xhigh"', '"xhigh"', content)

    if content == orig:
        return False
    try:
        with open(TEMPLATE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        log("[WARN] 模板自愈失败（权限?）: %s" % e)
        return False
    log("[TEMPLATE] 已剔除模板中的 max 档: %s" % TEMPLATE_FILE)
    return True


def watch_loop(interval=30):
    """常驻监控：轮询扫描（简单可靠，不依赖 watchdog 库）。"""
    log("[WATCH] 守护已启动，每 %ds 扫描一次: %s" % (interval, CODING_AGENT_DIR))
    while True:
        try:
            n = scan_and_fix()
            self_heal_template()
            if n:
                log("[WATCH] 本轮修复 %d 个 catalog（累计 %d）" % (n, fixed_total))
        except Exception as e:
            log("[WATCH] 异常（忽略继续）: %s" % e)
        time.sleep(interval)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="只扫描修复一次后退出")
    ap.add_argument("--interval", type=int, default=30, help="监控间隔秒数（默认 30）")
    args = ap.parse_args()

    n = scan_and_fix()
    t = self_heal_template()
    log("Done: scanned %s, fixed %d catalog(s), template_self_heal=%s (累计 %d)."
        % (CODING_AGENT_DIR, n, t, fixed_total))
    if args.once:
        return
    watch_loop(args.interval)


if __name__ == "__main__":
    main()
