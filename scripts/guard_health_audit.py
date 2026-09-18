#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
守卫的守卫 · guard_health_audit.py  v1.2
================================================================
v1.2 (2026-09-13) 修复：调度器状态码被特例吞掉 → 审计器自锁假红
  现象：自身结果码 267009 被判「未捕获异常」→ 红 → exit 1 → 下一轮继续判自己红。
  根因：267009 = 0x41301 = SCHED_S_TASK_RUNNING（"任务正在运行"），
        而 v1.1 的自指例外只放行 0/1，**排在语义表之前**，把状态码吞成了脚本失败。
  为什么只有「被调度器拉起」那一次才复现：
    审计器在**运行时**查询 schtasks，此时调度器对正在跑的实例如实回答
    0x41301=RUNNING；等它退出(exit 1)后，记录的结果码才变成 1。
    所以手动跑永远读不到 267009，只在计划任务里幽灵般出现 —— 典型的时序型假故障。
  修法：语义表改为「减刑器」而非「抢答器」——
        · 不放任它抢先返回（否则 HKTunnel 会退化成用弱证据判绿，丢掉端口探针）
        · 而是在证据链判红时兜底降级为黄，并注明「这是调度器状态不是失败」
  教训：**特例分支若排在语义表之前，语义表形同虚设**。
        凡是「状态码 → 结论」的映射，必须置于所有特例之上，或做成全局减刑器。
【为什么要有这个东西】
2026-09-12 实测发现：`Lobster_CatalogGuard_Deepseek` 每 15 分钟崩一次
（StopIteration），已经崩了不知多久，**没有任何人知道**。
原因三层：
  1. 守卫脚本自己抛了未捕获异常；
  2. 崩溃只体现为计划任务 LastResult=1，而**没人看计划任务结果码**；
  3. 被守卫的东西（免费模型目录）因此长期处于裸奔状态。

=> 「守卫自身失效」是**第 5 种假安全形态**：前 4 种是「报成功其实没干」，
   这一种是「根本没人报」。

【核心原则：结果码 ≠ 健康度】
同日反例：`Lobster_HTTP2Socks_7897` 结果码 2147946720（非 0，看着像挂了），
但 7897 端口**实际在 LISTENING** —— 服务好得很。
所以：**凡是能打数据面的，一律以数据面为准；结果码只用于分流。**

数据面证据优先级：
  ① 守卫自落的状态回执  .workbuddy/guard_status/*.json   （最强）
  ② 端口探针 netstat LISTENING                            （次强）
  ③ 计划任务结果码语义映射                                （最弱，仅分流）

用法：
  python guard_health_audit.py              # 全量体检，输出红黄绿报告
  python guard_health_audit.py --json       # 机器可读
  python guard_health_audit.py --prefix Lobster

退出码：0=全绿/无红  1=存在红项  2=审计器本身执行失败

零积分：纯 stdlib + schtasks + netstat。密钥：无。
"""
import json, os, re, subprocess, sys, datetime, socket

PREFIX = "Lobster"

# 审计器自身注册的任务名（v1.1 新增，见 classify() ⓪ 自指例外）
SELF_TASK = "Lobster_GuardHealthAudit"

STATUS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy", "guard_status")

# ---------------------------------------------------------------- 结果码语义
# 计划任务结果码不是「0 成功非 0 失败」，0x4130x 系列是调度器状态而非脚本错误
SCHED_S = {
    0x41300: ("READY",        "OK",   "任务就绪，尚未到触发点"),
    0x41301: ("RUNNING",      "OK",   "任务正在运行中"),
    0x41302: ("DISABLED",     "WARN", "任务被禁用"),
    0x41303: ("NOT_YET_RUN",  "OK",   "注册后还没跑过"),
    0x41304: ("NO_MORE_RUNS", "OK",   "一次性任务已跑完"),
    0x41305: ("NOT_SCHEDULED","WARN", "没有排程"),
}
# 等级词表翻译：语义层写 OK/WARN，报告层只认 GREEN/YELLOW/RED/UNKNOWN/INFO。
#   v1.2 踩坑：两套词表不一致，新任务以 0x41303 走到该分支即抛
#   `KeyError: 'OK'`（rows.sort / 图标查表处），整个审计器崩掉。
SCHED_LEVEL2REPORT = {"OK": "GREEN", "WARN": "YELLOW"}

# 有数据面可打的任务：任务名关键字 -> 需要 LISTENING 的端口
PORT_PROBES = {
    "HTTP2Socks":  [7897],
    "HKTunnel":    [1081],
    "Fleet":       [15721, 15730],
    "CodexProxy":  [15730],
}

# 明确的一次性任务（跑了就完了，结果码无意义）
IGNORE_TASKS = {"Lobster_LaunchObsidianOnce"}

# 非守卫类任务：直接拉 GUI 程序，其退出码由 GUI 自己决定，无健康语义。
# 实测 Lobster_ObsidianLaunch 跑 Obsidian.exe，结果码 0xCFFFFFFF —— 看着像炸了，
# 其实只是 GUI 进程的退出码。若按脚本守卫那套判红，就是典型的「假故障」。
NON_GUARD_TASKS = {
    "Lobster_ObsidianLaunch": "GUI 启动器（Obsidian.exe），退出码无健康语义",
}


def _decode(raw: bytes) -> str:
    for enc in ("cp936", "utf-16-le", "utf-8", "gbk", "latin-1"):
        try:
            s = raw.decode(enc)
            if "任务名" in s or "TaskName" in s or "HostName" in s:
                return s
        except Exception:
            continue
    return raw.decode("cp936", errors="replace")


def run(cmd, timeout=90):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return p.returncode, _decode(p.stdout or b""), _decode(p.stderr or b"")
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", f"{type(e).__name__}: {e}"


def list_tasks():
    """返回 [{name, last_result, last_run, status, action}]"""
    rc, out, err = run(["schtasks", "/query", "/fo", "list", "/v"])
    if rc != 0 and not out:
        raise RuntimeError(f"schtasks 查询失败 rc={rc} err={err[:200]}")
    # 中文 / 英文键名都认；注意「下次运行时间」必须收录，
    # 否则它会被当成上一键的续行，把任务名粘成一坨（v1.0 踩过的坑）
    ZH2EN = {
        "任务名": "name", "TaskName": "name",
        "上次结果": "last_result", "Last Result": "last_result",
        "上次运行时间": "last_run", "Last Run Time": "last_run",
        "下次运行时间": "next_run", "Next Run Time": "next_run",
        "要运行的任务": "action", "Task To Run": "action",
        "计划任务状态": "status", "Status": "status",
        "模式": "mode", "注释": "comment",
    }
    KEY_RE = re.compile(r"^\s*([^:：]{2,24})\s*[:：]\s*(.*)$")

    tasks, cur, key, seen = [], None, None, set()
    for line in out.splitlines():
        if not line.strip():
            continue
        m = KEY_RE.match(line)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            key = ZH2EN.get(k)          # 未收录的键 -> key=None，后续行不再粘连
            if key == "name":
                if cur and cur.get("name"):
                    tasks.append(cur)
                cur = {"name": v, "last_result": "", "last_run": "",
                       "next_run": "", "action": "", "status": "", "mode": ""}
            elif cur is not None and key:
                cur[key] = v
            continue
        # 续行（如超长 action 换行）：仅当上一个是已收录键时才拼接
        if cur is not None and key:
            cur[key] = (cur[key] + " " + line.strip()).strip()
    if cur and cur.get("name"):
        tasks.append(cur)

    # 去重（schtasks 可能对同一任务输出多条）
    out_t = []
    for t in tasks:
        n = t["name"].lstrip("\\")
        if n in seen:
            continue
        seen.add(n)
        out_t.append(t)
    return out_t


def load_status_receipts():
    """读取各守卫自落的状态回执（最强数据面证据）"""
    out = {}
    if not os.path.isdir(STATUS_DIR):
        return out
    for fn in os.listdir(STATUS_DIR):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(STATUS_DIR, fn), encoding="utf-8") as f:
                d = json.load(f)
            out[d.get("guard") or fn[:-5]] = d
        except Exception:
            continue
    return out


def port_listening(port):
    for conn in ("127.0.0.1", "0.0.0.0"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        try:
            if s.connect_ex((conn, port)) == 0:
                return True
        except Exception:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass
    return False


def parse_result(v):
    v = (v or "").strip()
    try:
        return int(v)
    except Exception:
        return None


# 超过此时长没跑过 = 疑似静默停摆（守卫不报错、也不干活）
STALE_HOURS = 72


def hours_since(s):
    """解析 schtasks 的本地化时间串，返回距今年小时数；解析不出或「从未运行」返回 None"""
    s = (s or "").strip()
    if not s or s.upper().startswith("N/A"):
        return None
    s = s.replace("年", "/").replace("月", "/").replace("日", "")
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
        except Exception:
            continue
        # Windows 从不给空值：任务「从未运行过」时，schtasks 输出的是哨兵日期
        #   1999/11/30 0:00:00（不是 N/A）。v1.2 踩坑：当真实日期解析 →
        #   算出「已 234822h 未运行」→ 把刚注册、还没到触发点的健康任务判成静默停摆。
        #   1970 前的哨兵一律视为「从未运行」，不计停摆。
        if dt.year < 2000:
            return None
        return (datetime.datetime.now() - dt).total_seconds() / 3600.0
    return None


def classify(task, receipts):
    """返回 (level, reason, evidence) level ∈ GREEN/YELLOW/RED/UNKNOWN"""
    name = task.get("name", "").lstrip("\\")
    base = name.split("\\")[-1]
    res = parse_result(task.get("last_result"))
    ev = {"task": base, "last_result": task.get("last_result"),
          "last_run": task.get("last_run")}

    # ⓪ 语义预取（v1.2 核心）：调度器状态码 0x4130x 是 Windows 的「状态」，
    #    不是脚本退出码。它绝不能被任何特例分支当成失败证据。
    #    实证：267009 = 0x41301 = SCHED_S_TASK_RUNNING。
    sched = SCHED_S.get(res) if res is not None else None
    sched_ok = bool(sched and sched[1] == "OK")

    def soften(level, reason, e=None):
        """减刑器：证据链判红，但 Windows 明说「这不是失败」→ 降级为黄并留证。
        注意这里**不抢先返回**，以免 HKTunnel 之类退化为弱证据判绿（丢掉端口探针）。"""
        e = e if e is not None else ev
        if level == "RED" and sched_ok:
            e = {**e, "sched_softened": sched[0]}
            return ("YELLOW",
                    f"{reason}；但结果码 {res} = 调度器状态 {sched[0]}（{sched[2]}），"
                    f"不按脚本失败处理", e)
        return (level, reason, e)

    if base in NON_GUARD_TASKS:
        return ("INFO", f"免检：{NON_GUARD_TASKS[base]}（结果码 {res} 不作为故障依据）", ev)

    # ① 自指例外（v1.1，2026-09-12；v1.2 补调度器状态放行）
    #   审计器自身的退出码是「结论」不是「健康度」：0=全绿，1=发现红项，2=自身执行失败。
    #   若把 1 判成自身故障就会自锁：发现红项 → exit 1 → 本次判自身红 → 又 exit 1 → 永久红。
    if base == SELF_TASK:
        if sched_ok:
            return ("GREEN",
                    f"自指项：结果码 {res} = 调度器状态 {sched[0]}（{sched[2]}），非自身故障", ev)
        if res in (0, 1):
            return ("GREEN", f"自指项跳过（退出码 {res} = 全绿/已报告红项，属正常履职）", ev)
        return ("RED", f"审计器上次执行失败（退出码 {res}，未捕获异常）", ev)

    # ② 状态回执（最强）
    #  名称归一化：忽略大小写/下划线/连字符，
    #  否则 "catalog_guard_deepseek" 匹配不上 "Lobster_CatalogGuard_Deepseek"
    norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
    nb = norm(base)
    has_receipt = False
    for gname, d in receipts.items():
        if gname and norm(gname) and norm(gname) in nb:
            has_receipt = True
            ev["receipt"] = d
            age = None
            try:
                age = (datetime.datetime.now()
                       - datetime.datetime.fromisoformat(d["checked_at"])).total_seconds()
            except Exception:
                pass
            if d.get("healthy"):
                return ("GREEN", "守卫状态回执 healthy",
                        {**ev, "receipt_age_sec": int(age) if age else None})
            return soften("RED", f"守卫状态回执 unhealthy: {d.get('detail','')[:120]}")

    # ③ 端口探针
    for kw, ports in PORT_PROBES.items():
        if kw.lower() in base.lower():
            st = {p: port_listening(p) for p in ports}
            ev["ports"] = st
            if all(st.values()):
                return ("GREEN", f"端口 {ports} 全部 LISTENING（结果码 {res} 不代表故障）", ev)
            if any(st.values()):
                return ("YELLOW", f"端口部分在听 {st}", ev)
            return soften("RED", f"端口全部未监听 {st}")

    # ④ 结果码语义
    if res is None:
        return ("UNKNOWN", "结果码无法解析", ev)
    if res == 0:
        if not has_receipt:
            # 结果码 0 只说明「上次没报错」，不说明「真的干了活」。
            # 没有状态回执 = 健康度仍靠猜 → 降级为黄，逼守卫接入 guard_receipt。
            return ("YELLOW",
                    "结果码 0 但无状态回执（弱证据：无法证明守卫真的执行成功，"
                    "建议接入 scripts\\guard_receipt.py）", ev)
        return ("GREEN", "结果码 0", ev)
    if res in SCHED_S:
        code, lvl, desc = SCHED_S[res]
        return (SCHED_LEVEL2REPORT.get(lvl, lvl), f"调度器状态 {code}：{desc}", ev)
    if 0 < res < 256:
        return soften("RED", f"脚本退出码 {res}（非调度器状态，判定为脚本失败）")
    return ("YELLOW", f"未知结果码 {res}（0x{res & 0xFFFFFFFF:X}），需人工确认", ev)


def main():
    args = sys.argv[1:]
    prefix = PREFIX
    if "--prefix" in args:
        i = args.index("--prefix")
        if i + 1 < len(args):
            prefix = args[i + 1]

    receipts = load_status_receipts()
    try:
        tasks = list_tasks()
    except Exception as e:
        print(f"[AUDIT] 审计器执行失败: {e}")
        return 2

    sel = [t for t in tasks
           if prefix.lower() in (t.get("name") or "").lower()
           and t["name"].lstrip("\\").split("\\")[-1] not in IGNORE_TASKS]

    rows = []
    for t in sel:
        lvl, reason, ev = classify(t, receipts)
        # 静默停摆维度：结果码再好看，太久没跑也是死的
        age_h = hours_since(t.get("last_run"))
        ev["stale_hours"] = round(age_h, 1) if age_h is not None else None
        if age_h is not None and age_h > STALE_HOURS:
            if lvl == "GREEN":
                lvl = "YELLOW"
            reason += f"；⚠ 已 {int(age_h)}h 未运行（>{STALE_HOURS}h，疑似静默停摆）"
        rows.append({"level": lvl, "reason": reason, "evidence": ev,
                     "action": t.get("action", "")[:300]})

    # v1.2 兜底：等级词表若再次出现未收录值，降级为 UNKNOWN 而不是让整个审计器崩掉。
    #   一个等级拼写问题不该让所有守卫失去监督。
    VALID = {"RED", "YELLOW", "UNKNOWN", "GREEN", "INFO"}
    for r in rows:
        if r["level"] not in VALID:
            r["reason"] += f"（等级值 '{r['level']}' 未收录，已降级为 UNKNOWN）"
            r["level"] = "UNKNOWN"

    order = {"RED": 0, "YELLOW": 1, "UNKNOWN": 2, "GREEN": 3, "INFO": 4}
    rows.sort(key=lambda r: order.get(r["level"], 2))

    if "--json" in args:
        print(json.dumps({"checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
                          "total": len(rows), "rows": rows},
                         ensure_ascii=False, indent=2))
    else:
        print("=" * 68)
        print(f" 守卫健康审计 · {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f" 扫描范围: 任务名含 '{prefix}'  ·  共 {len(rows)} 项")
        print("=" * 68)
        for r in rows:
            mark = {"GREEN": "[绿]", "YELLOW": "[黄]", "RED": "[红]",
                    "UNKNOWN": "[?]", "INFO": "[略]"}.get(r["level"], "[?]")
            base = r["evidence"]["task"]
            print(f"{mark} {base}")
            print(f"     判定: {r['reason']}")
            if r["evidence"].get("ports"):
                print(f"     端口: {r['evidence']['ports']}")
            if r["evidence"].get("receipt_age_sec") is not None:
                print(f"     回执: {r['evidence']['receipt_age_sec']}s 前")
            if r["level"] == "RED" and r["action"]:
                print(f"     复现: {r['action']}")
            print()
        n_red = sum(1 for r in rows if r["level"] == "RED")
        print("-" * 68)
        print(f" 红 {n_red} / 黄 {sum(1 for r in rows if r['level']=='YELLOW')} "
              f"/ 未知 {sum(1 for r in rows if r['level']=='UNKNOWN')} "
              f"/ 绿 {sum(1 for r in rows if r['level']=='GREEN')} "
              f"/ 免检 {sum(1 for r in rows if r['level']=='INFO')}")
        print("-" * 68)

    # 回执落盘
    try:
        os.makedirs(STATUS_DIR, exist_ok=True)
        p = os.path.join(STATUS_DIR, "_audit_receipt.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
                       "rows": rows}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return 1 if any(r["level"] == "RED" for r in rows) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # v1.1：计划任务跑的时候 stdout 没人看，异常信息必须落盘，否则 exit 2 无从查起
        import traceback
        tb = traceback.format_exc()
        print(f"[AUDIT] 审计器未捕获异常(已兜住): {type(e).__name__}: {e}")
        try:
            os.makedirs(STATUS_DIR, exist_ok=True)
            with open(os.path.join(STATUS_DIR, "audit_crash.log"),
                      "a", encoding="utf-8") as f:
                f.write("\n==== %s ====\n%s" %
                        (datetime.datetime.now().isoformat(timespec="seconds"), tb))
        except Exception:
            pass
        sys.exit(2)
