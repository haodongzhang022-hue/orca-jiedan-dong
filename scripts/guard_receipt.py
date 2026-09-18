#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_receipt.py v1.0 —— 守卫状态回执「一行接入」模块
================================================================
【为什么要有这个模块】
2026-09-13 审计发现：6 个 Lobster 守卫里只有 1 个（catalog_guard_deepseek）
写了状态回执，其余 5 个只能靠「计划任务结果码」猜健康度。
而结果码经实测分三类：真失败 / 调度器状态(0x4130x) / GUI 进程退出码，
**只有第一类能判红**。用结果码判健康 = 制造假故障。

守卫的守卫（guard_health_audit.py）把「状态回执」列为最强数据面证据，
优先级高于端口探针和结果码。所以要让审计真正有效，必须让**每个守卫都落回执**。

【模块化收益】
原先回执逻辑是 catalog_guard_deepseek 里内联的一段，第二个守卫要用就得复制粘贴。
抽出成本模块后，任何守卫只需两行：
    from guard_receipt import write_receipt
    write_receipt("my_guard", healthy=True, detail="OK", version="1.0")

【回执 Schema】（审计器依赖，勿随意改字段名）
    guard      : str   守卫名（与计划任务名归一化后子串匹配，如 codex_model_guard）
    version    : str   守卫版本
    checked_at : str   ISO8601 本地时间
    healthy    : bool  是否健康
    exit_code  : int   守卫本次退出码
    detail     : str   人话结论（审计器红项会展示这段）
    extra      : dict  可选，任意附加证据

零积分：纯 stdlib，不联网、不调模型。密钥：无。
"""
import json
import os
import datetime

# 回执统一落点：优先「脚本所在目录/../.workbuddy/guard_status」，
# 兜底到接单项目固定路径（供 MCP服务\ 下的守卫使用）。
_FIXED = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\.workbuddy\guard_status"


def status_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [
        os.path.join(os.path.dirname(here), ".workbuddy", "guard_status"),
        _FIXED,
    ]
    for c in cands:
        if os.path.isdir(c):
            return c
    return _FIXED


def write_receipt(guard, healthy, detail="", version="1.0", exit_code=0, extra=None):
    """落一条状态回执。永远不抛异常——守卫本体比回执重要，回执写失败不许拖垮守卫。"""
    try:
        d = status_dir()
        os.makedirs(d, exist_ok=True)
        payload = {
            "guard": guard,
            "version": version,
            "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "healthy": bool(healthy),
            "exit_code": int(exit_code),
            "detail": str(detail)[:500],
        }
        if extra:
            payload["extra"] = extra
        p = os.path.join(d, "%s.json" % guard)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)          # 原子替换：审计器不会读到写了一半的 JSON
        return p
    except Exception:
        return None


if __name__ == "__main__":
    # 自检：写一条 demo 回执，供审计器连通性验证
    p = write_receipt("guard_receipt_selftest", True, "自检通过", version="1.0")
    print("receipt ->", p)
