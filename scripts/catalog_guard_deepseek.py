#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Catalog 守卫 · deepseek 免费模型防覆盖  v1.1
================================================================
作用：TeamoRouter Desktop 会周期性覆盖 model-catalog.json，
      把 deepseek-v4-flash-free / deepseek-v4-pro-free 挤掉。
      本守卫每 15 分钟检测一次，缺失自动补回（克隆同族模板条目）。

用法：python catalog_guard_deepseek.py          # 检查并修复
      python catalog_guard_deepseek.py --check  # 只检查不修改

退出码：
  0 = 正常（齐全 / 成功补回）
  2 = catalog 读取失败
  3 = 有缺失但找不到任何可用模板（不会崩，仅报告）
  4 = 写入失败

------------------------------------------------------------------
v1.1 修复（2026-09-12 汤小龙自进化）：
  v1.0 写死 CLONE_FROM="gpt-5.6-luna"，而该 slug 已随上游轮换从
  catalog 消失 → next() 抛 StopIteration → 未捕获异常 → rc=1，
  每 15 分钟崩一次，缺失模型永远补不回来，且**没有任何人收到告警**
  （计划任务结果码没人看）。这是「守卫自身失效静默化」的典型。
  修复：模板候选链（同族精确 → 同前缀族 → 任意 free → 常量 → 任意），
        全程不抛异常，并落结构化状态回执供 meta-guard 采集。
------------------------------------------------------------------
密钥：不涉及。纯本地 JSON 操作。零积分。
"""
import json, os, shutil, sys, datetime

CATALOG = r"C:\Users\Administrator\.codex-orch\backups_state\teamorouter-fast\model-catalog.json"
REQUIRED = ["deepseek-v4-flash-free", "deepseek-v4-pro-free", "glm-5.3-flash-free"]
CLONE_FROM = "gpt-5.6-luna"        # 仅作为候选链中的一档，不再是唯一依赖
CHECK_ONLY = "--check" in sys.argv

STATUS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy", "guard_status")
STATUS_FILE = os.path.join(STATUS_DIR, "catalog_guard_deepseek.json")


def _write_status(ok, code, detail, missing=None, restored=None):
    """落结构化回执，供 guard_health_audit.py 采集（数据面证据，不靠结果码猜）"""
    try:
        os.makedirs(STATUS_DIR, exist_ok=True)
        payload = {
            "guard": "catalog_guard_deepseek",
            "version": "1.1",
            "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "healthy": bool(ok),
            "exit_code": int(code),
            "missing": missing or [],
            "restored": restored or [],
            "detail": detail,
        }
        tmp = STATUS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATUS_FILE)
    except Exception as e:                       # 状态回执失败不影响主流程
        print(f"[GUARD] 状态回执写入失败(忽略): {e}")


def _family_base(slug):
    """deepseek-v4-pro-free -> deepseek-v4-pro"""
    base = slug or ""
    for suf in ("-free",):
        if base.endswith(suf):
            base = base[: -len(suf)]
    return base


def pick_template(models, slug):
    """
    模板候选链：同族精确 → 同前缀族 → 任意 -free → 常量 CLONE_FROM → 任意首个。
    保证在任何情况下都返回模板或 None，**永不抛 StopIteration**。
    """
    base = _family_base(slug)
    fam = (base.split("-")[0] or "").lower()
    by_slug = {m.get("slug"): m for m in models if m.get("slug")}

    chain = []
    if base in by_slug:                                          # 1 同族精确
        chain.append(by_slug[base])
    chain += [m for m in models                                   # 2 同前缀族
              if fam and (m.get("slug") or "").lower().startswith(fam)
              and m.get("slug") != slug]
    chain += [m for m in models                                   # 3 任意 free
              if (m.get("slug") or "").endswith("-free")]
    if CLONE_FROM in by_slug:                                     # 4 常量档
        chain.append(by_slug[CLONE_FROM])
    chain += [m for m in models if m.get("slug")]                 # 5 兜底任意

    for m in chain:
        if isinstance(m, dict) and m.get("slug") and m.get("slug") != slug:
            return m
    return None


def main():
    try:
        with open(CATALOG, encoding="utf-8") as f:
            j = json.load(f)
    except Exception as e:
        print(f"[GUARD] catalog 读取失败: {e}")
        _write_status(False, 2, f"catalog 读取失败: {e}")
        return 2

    models = j.get("models") or []
    slugs = [m.get("slug") for m in models]
    missing = [s for s in REQUIRED if s not in slugs]

    if not missing:
        msg = f"OK 所有必含模型都在 ({datetime.datetime.now():%Y-%m-%d %H:%M:%S})"
        print(f"[GUARD] {msg}")
        _write_status(True, 0, msg)
        return 0

    print(f"[GUARD] 缺失: {missing}")
    if CHECK_ONLY:
        _write_status(False, 1, f"缺失未修复(仅检查): {missing}", missing=missing)
        return 1

    # 逐个缺失项选模板，选不到就跳过而不是崩
    to_add, failed = [], []
    for slug in missing:
        tmpl = pick_template(models, slug)
        if tmpl is None:
            failed.append(slug)
            print(f"[GUARD] 无可用模板，跳过: {slug}")
            continue
        m = json.loads(json.dumps(tmpl))
        m["slug"] = slug
        m["display_name"] = slug
        m["description"] = slug + " routed through TeamoRouter."
        if "default_reasoning_level" in m:
            m["default_reasoning_level"] = "low"
        to_add.append((slug, tmpl.get("slug")))
        models.append(m)

    if not to_add:
        msg = f"有缺失但无任何可用模板，未修改 catalog: {missing}"
        print(f"[GUARD] {msg}")
        _write_status(False, 3, msg, missing=missing)
        return 3

    bak = CATALOG + ".bak.guard_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.copy2(CATALOG, bak)
        j["models"] = models
        with open(CATALOG, "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=2)
    except Exception as e:
        msg = f"写入失败: {e}"
        print(f"[GUARD] {msg}")
        _write_status(False, 4, msg, missing=missing)
        return 4

    restored = [s for s, _ in to_add]
    msg = f"已补回 {restored}（模板来源 {[t for _, t in to_add]}），备份: {bak}"
    if failed:
        msg += f"；无法补回: {failed}"
    print(f"[GUARD] {msg}")
    _write_status(not failed, 0 if not failed else 3, msg,
                  missing=missing, restored=restored)
    return 0 if not failed else 3


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                       # 最后一道防线：守卫绝不裸崩
        print(f"[GUARD] 未捕获异常(已兜住): {type(e).__name__}: {e}")
        _write_status(False, 9, f"未捕获异常: {type(e).__name__}: {e}")
        sys.exit(9)
