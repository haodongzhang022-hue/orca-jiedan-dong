#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codex_catalog_guard.py — Codex model_catalog.json 防生成根防线守护（v1.0 · 2026-08-13）
================================================================================
【问题根因】
Hermes Studio 每次新建群聊会话会重新生成 codex-model-catalog.json，
生成时写入非法档位 "effort": "max"，而 Codex 只认
none/minimal/low/medium/high/xhigh 六档，导致启动即报：
    failed to parse model_catalog_json ... unknown variant `max`
（第三次复发：此前仅事后修复 catalog 文件，未拦截生成源）

【本脚本双层防线】
  第1层 防复发（高频扫描修复）：
    扫描 .hermes-web-ui 下全部 codex-model-catalog.json，
    "effort":"max" -> "effort":"xhigh"，会话生成后 ≤60 秒内自动修正，
    等效拦截写入（在用户 @codex 之前已修复到位）。
  第2层 防覆盖（生成源补丁自愈）：
    核对 Hermes Studio webui/dist/server/index.js 是否被更新还原
    （含 max 非法档位即视为被覆盖），被覆盖则自动重新打补丁，
    打补丁前自动备份，杜绝"升级后复发"。

【用法】
  python codex_catalog_guard.py              # 单次扫描修复 + 补丁自愈（供定时任务/手动）
  python codex_catalog_guard.py --daemon     # 常驻守护模式（每 60 秒巡检一次）
================================================================================
"""
import json
import os
import re
import sys
import time

# ---------- 配置 ----------
HERMES_WEBUI_ROOT = r"C:/Users/Administrator/.hermes-web-ui"
CATALOG_GLOBS = ("codex-model-catalog.json", "codex_model_catalog.json", "*model-catalog.json", "*model_catalog.json")

# Hermes Studio 生成源（每次 Hermes 更新会覆盖，脚本自动重打补丁）
INDEX_JS = r"C:/Users/Administrator/AppData/Local/Programs/Hermes Studio/resources/webui/dist/server/index.js"

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs", "codex_catalog_guard.log")

VALID_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}
BAD_EFFORT = "max"
GOOD_EFFORT = "xhigh"

# 生成源里可能出现的非法档位写法（minified JS 各种形态），统一替换为合法档位
INDEX_PATCHES = [
    (r'"effort"\s*:\s*"max"', '"effort": "%s"' % GOOD_EFFORT),
    (r'effort:"max"', 'effort:"%s"' % GOOD_EFFORT),
    (r'effort:\s*"max"', 'effort:"%s"' % GOOD_EFFORT),
]


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def find_catalogs():
    hits = []
    if not os.path.isdir(HERMES_WEBUI_ROOT):
        return hits
    for root, _dirs, files in os.walk(HERMES_WEBUI_ROOT):
        for fn in files:
            if fn.endswith(CATALOG_GLOBS) and "group-chat" in root:
                hits.append(os.path.join(root, fn))
    return hits


def fix_catalog(path):
    """修复单个 catalog 文件：effort:max -> xhigh。返回 (修复数, 是否改动)。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        log("  !! 读取失败 %s : %s" % (path, e))
        return 0, False
    if '"%s"' % BAD_EFFORT not in raw:
        return 0, False
    # 只替换 effort 字段的 max（避免误伤其他字段）
    new_raw, n = re.subn(r'"effort"\s*:\s*"%s"' % BAD_EFFORT, '"effort": "%s"' % GOOD_EFFORT, raw)
    if n == 0:
        return 0, False
    try:
        json.loads(new_raw)  # 校验仍为合法 JSON，防损坏
    except Exception as e:
        log("  !! 替换后 JSON 校验失败，跳过 %s : %s" % (path, e))
        return 0, False
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_raw)
    return n, True


def scan_fix():
    """第1层：扫描全部 catalog 并修复。"""
    catalogs = find_catalogs()
    if not catalogs:
        log("[scan] 未找到 catalog 文件（%s 下无 group-chat catalog）" % HERMES_WEBUI_ROOT)
        return 0
    total_fixed = 0
    total_files = 0
    for c in catalogs:
        n, changed = fix_catalog(c)
        if changed:
            total_fixed += n
            total_files += 1
            log("[scan] 修复 %s  (%d 处 max->xhigh)" % (c, n))
    log("[scan] 扫描 %d 个 catalog：修复 %d 个文件 / %d 处" % (len(catalogs), total_files, total_fixed))
    return total_fixed


def has_bad_effort(src):
    """精确检测：仅当存在 effort:max 形态的非法档位才算被覆盖（避免裸 "max" 字符串误判）。"""
    for pat, _repl in INDEX_PATCHES:
        if re.search(pat, src):
            return True
    return False


def patch_index_js():
    """第2层：检查生成源 index.js，被覆盖则自动重打补丁（防覆盖）。"""
    if not os.path.isfile(INDEX_JS):
        log("[patch] 生成源不存在：%s" % INDEX_JS)
        return False
    with open(INDEX_JS, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    if not has_bad_effort(src):
        log("[patch] 生成源已带补丁（无 effort:max 残留），无需重打")
        return True
    # 备份一次（幂等：只有真实存在 effort:max 非法档位才备份+重打）
    bak = INDEX_JS + ".bak_guard_auto_%s" % time.strftime("%Y%m%d_%H%M%S")
    with open(bak, "w", encoding="utf-8") as f:
        f.write(src)
    log("[patch] 生成源含非法档位 effort:max，已备份 -> %s" % bak)
    new_src = src
    total = 0
    for pat, repl in INDEX_PATCHES:
        new_src, n = re.subn(pat, repl, new_src)
        total += n
    if total == 0:
        log("[patch] 生成源精确匹配后未替换（形态差异），依赖第1层扫描兜底")
        return False
    with open(INDEX_JS, "w", encoding="utf-8") as f:
        f.write(new_src)
    log("[patch] 已重打生成源补丁：%d 处 max->xhigh（防 Hermes 更新覆盖）" % total)
    return True


def run_once():
    log("==== codex_catalog_guard 巡检开始 ====")
    scan_fix()
    patch_index_js()
    log("==== 巡检结束 ====")


def run_daemon():
    log("[daemon] 常驻守护模式启动，每 60 秒巡检一次")
    while True:
        try:
            run_once()
        except Exception as e:
            log("[daemon] 巡检异常：%s" % e)
        time.sleep(60)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_daemon()
    else:
        run_once()
