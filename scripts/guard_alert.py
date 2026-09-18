#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
守卫红项主动告警 · guard_alert.py  v1.0
================================================================
【为什么要有这个脚本】
2026-09-12 建了「守卫的守卫」guard_health_audit.py，但它只会**写报告**。
红项躺在 .workbuddy\\guard_status\\_audit_receipt.json 里，
而没人会定时去翻一个 JSON —— 报告型告警 = 没有告警。

【设计三原则】
1. **不刷屏**：同一红项按指纹去重，冷却期内（默认 12h）不重复推送；
   红项恢复后清除指纹，下次再红可以重新告警（否则复发会静默）。
2. **零积分优先**：默认只写本地告警文件（ALERT.md），**不联网不调模型**；
   企微推送是显式 `--push` 才触发，且走本地 wecom-cli，不消耗积分。
3. **永不拖垮调用方**：任何异常都吞掉，退出码始终 0（告警失败不该让审计变红）。

用法：
  python guard_alert.py                 # 读审计回执 → 红项写 ALERT.md
  python guard_alert.py --push          # 额外推企微（受冷却期约束）
  python guard_alert.py --json          # 机器可读
  python guard_alert.py --cooldown 6    # 改冷却小时数
  python guard_alert.py --dry-run       # 只看会发什么，不写不推

零积分：纯 stdlib + 本地 wecom-cli。密钥：无。
"""
import json
import os
import re
import sys
import time
import hashlib
import datetime
import subprocess

# v1.1 (2026-09-14)：告警器自己也要落回执。
# 讽刺但真实：告警器天天盯别人健康，自己挂了没人知道——审计器只能看到
# 「结果码 0 但无回执 → 判黄」。两行接入，守卫的守卫才没有盲区。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from guard_receipt import write_receipt
except Exception:
    write_receipt = None

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS_DIR = os.path.join(os.path.dirname(HERE), ".workbuddy", "guard_status")
RECEIPT = os.path.join(STATUS_DIR, "_audit_receipt.json")
ALERT_MD = os.path.join(STATUS_DIR, "ALERT.md")
STATE = os.path.join(STATUS_DIR, "_alert_state.json")

DEFAULT_COOLDOWN_H = 12


def _norm_fp(level, task, reason):
    """告警指纹：同一任务同一类原因算一条。
    刻意**剔除**时间/端口等易变字段，否则每次都是新指纹 = 去重失效。"""
    key = "%s|%s|%s" % (level, task, re.sub(r"\d+", "#", reason)[:80])
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    try:
        os.makedirs(STATUS_DIR, exist_ok=True)
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE)
    except Exception:
        pass


def load_reds():
    try:
        with open(RECEIPT, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print("[ALERT] 读不到审计回执: %s" % e)
        return [], None
    rows = [r for r in d.get("rows", []) if r.get("level") == "RED"]
    return rows, d.get("checked_at")


def render(rows, checked_at):
    lines = ["# 守卫告警（红项）", "",
             "> 生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "> 审计时间：%s" % (checked_at or "unknown"),
             "> 共 %d 项红项" % len(rows), ""]
    for r in rows:
        ev = r.get("evidence", {})
        lines.append("## 🔴 %s" % ev.get("task", "?"))
        lines.append("- 判定：%s" % r.get("reason", ""))
        if ev.get("last_run"):
            lines.append("- 上次运行：%s（结果码 %s）" % (ev.get("last_run"), ev.get("last_result")))
        if r.get("action"):
            lines.append("- 复现命令：`%s`" % r["action"][:300])
        lines.append("")
    return "\n".join(lines)


def push_wecom(text, dry=False):
    """本地 wecom-cli 推送。失败不影响主流程。"""
    try:
        r = subprocess.run(["wecom-cli", "message", "send", "--text", text],
                           capture_output=True, text=True, timeout=60,
                           errors="ignore")
        ok = (r.returncode == 0)
        return ok, (r.stdout or r.stderr or "")[:300]
    except FileNotFoundError:
        return False, "wecom-cli 未安装"
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def main():
    args = sys.argv[1:]
    cooldown = DEFAULT_COOLDOWN_H
    if "--cooldown" in args:
        try:
            cooldown = float(args[args.index("--cooldown") + 1])
        except Exception:
            pass
    do_push = "--push" in args
    dry = "--dry-run" in args

    rows, checked_at = load_reds()
    st = load_state()
    now = time.time()

    live_fps = set()
    fresh, muted = [], []
    for r in rows:
        ev = r.get("evidence", {})
        fp = _norm_fp("RED", ev.get("task", "?"), r.get("reason", ""))
        live_fps.add(fp)
        last = st.get(fp, {}).get("last_sent", 0)
        age_h = (now - last) / 3600.0
        if age_h >= cooldown:
            fresh.append((fp, r))
        else:
            muted.append((fp, ev.get("task"), round(cooldown - age_h, 1)))

    # 红项消失 → 清指纹，允许下次复发重新告警（否则复发永远静默）
    recovered = [k for k in st.keys() if k not in live_fps]
    for k in recovered:
        st.pop(k, None)

    result = {"checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
              "red_total": len(rows), "fresh": len(fresh), "muted": len(muted),
              "recovered": len(recovered), "pushed": False, "pushed_to": None}

    if rows and not dry:
        try:
            os.makedirs(STATUS_DIR, exist_ok=True)
            with open(ALERT_MD, "w", encoding="utf-8") as f:
                f.write(render(rows, checked_at))
        except Exception:
            pass
    elif not rows and not dry:
        try:
            if os.path.exists(ALERT_MD):
                os.remove(ALERT_MD)      # 全绿则清空告警文件，避免陈旧红项误导
        except Exception:
            pass

    # 记账必须与「是否已送达」绑定，而不是与「是否推送企微」绑定。
    # v1.0 踩坑：记账写在 do_push 分支里 → 不推送就永不记账 → 冷却期形同虚设，
    # 同一红项每次都被算作「新增待报」，去重完全失效。
    if fresh and not dry:
        for fp, _ in fresh:
            st[fp] = {"last_sent": now,
                      "sent_at": datetime.datetime.now().isoformat(timespec="seconds")}

    if fresh and do_push and not dry:
        titles = ", ".join(r["evidence"].get("task", "?") for _, r in fresh[:5])
        text = ("[龙虾守卫告警] 发现 %d 项红项（新增 %d）：%s\n"
                "详情：%s" % (len(rows), len(fresh), titles, ALERT_MD))
        ok, info = push_wecom(text)
        result["pushed"] = ok
        result["push_info"] = info
    save_state(st)

    # v1.1 自身状态回执：告警器健康 = 它跑完了且知道当前有多少红项
    if write_receipt:
        try:
            write_receipt(
                "guardalert", True,
                "告警器执行完成：红 %d / 新增待报 %d / 冷却静默 %d"
                % (len(rows), len(fresh), len(muted)),
                version="1.1", exit_code=0,
                extra={"red": len(rows), "fresh": len(fresh), "muted": len(muted),
                       "pushed": bool(result.get("pushed"))},
            )
        except Exception:
            pass

    if "--json" in args:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print(" 守卫红项告警 · %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        print(" 红项 %d  ·  新增待报 %d  ·  冷却期内静默 %d  ·  已恢复清账 %d"
              % (len(rows), len(fresh), len(muted), len(recovered)))
        for fp, task, left in muted:
            print("   [静默] %s（%.1fh 后允许再报）" % (task, left))
        for _, r in fresh:
            print("   [待报] %s :: %s" % (r["evidence"].get("task"), r.get("reason", "")[:60]))
        if do_push:
            print(" 推送：%s" % ("成功" if result["pushed"] else "未执行/失败 %s"
                                % result.get("push_info", "")))
        print(" 告警文件：%s" % ALERT_MD)
        print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # 告警自身失败绝不能让上游审计变红
        print("[ALERT] 告警器异常(已忽略): %s: %s" % (type(e).__name__, e))
        sys.exit(0)
