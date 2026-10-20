#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNB LLM Adapter 自检脚本 v1.0

用途：对适配层做 L4 级实测（不只看 HTTP 码，要验正文内容）。
判据（铁律第18条：跑通必须落在产物内容层）：
  1. /health 返回 status=ok
  2. /v1/models 返回模型清单非空
  3. 非流式请求 → 正文长度 > 0 且含中文
  4. 流式请求 → SSE 事件数 > 1 且聚合正文 > 0
  5. 响应头 X-Adapter-Via 能标明实际通道（cnb / fallback）

用法：
  python selftest.py --port 15741
  退出码：0 全过；1 有失败项（便于流水线判定）
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append((name, detail))
    print(("  [PASS] " if ok else "  [FAIL] ") + name + ("  " + detail if detail else ""), flush=True)
    return ok


def get(url, timeout=15):
    req = urllib.request.Request(url, method="GET")
    with OPENER.open(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


def post(url, payload, timeout=180):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with OPENER.open(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=15741)
    ap.add_argument("--model", default="deepseek-v4-flash")
    args = ap.parse_args()
    base = "http://%s:%d" % (args.host, args.port)

    print("=" * 60, flush=True)
    print("[selftest] 目标 %s  模型 %s" % (base, args.model), flush=True)
    print("=" * 60, flush=True)

    # ---- 1. health ----
    print("\n[1] /health", flush=True)
    try:
        st, hd, body = get(base + "/health")
        j = json.loads(body)
        check("HTTP 200", st == 200, "status=%s" % st)
        check("status=ok", j.get("status") == "ok", str(j.get("status")))
        print("      gateway = %s" % j.get("gateway"), flush=True)
        print("      token   = %s" % j.get("token"), flush=True)
        print("      fallback= %s" % j.get("fallback"), flush=True)
    except Exception as e:
        check("/health 可达", False, "%s: %s" % (type(e).__name__, e))
        return summarize()

    # ---- 2. models ----
    print("\n[2] /v1/models", flush=True)
    try:
        st, hd, body = get(base + "/v1/models")
        j = json.loads(body)
        ids = [m.get("id") for m in j.get("data", [])]
        check("模型清单非空", len(ids) > 0, "count=%d" % len(ids))
        print("      models = %s" % ids, flush=True)
    except Exception as e:
        check("/v1/models 可达", False, "%s: %s" % (type(e).__name__, e))

    # ---- 3. 非流式：必须验正文，不能只看 200 ----
    print("\n[3] 非流式请求（验正文，不只看状态码）", flush=True)
    t0 = time.time()
    try:
        st, hd, body = post(base + "/v1/chat/completions", {
            "model": args.model,
            "messages": [{"role": "user", "content": "用一句话说明多智能体协作评审的价值。"}],
            "stream": False,
        })
        el = time.time() - t0
        via = hd.get("X-Adapter-Via", "(无)")
        j = json.loads(body)
        if "error" in j:
            check("非流式成功", False, "err=%s" % json.dumps(j["error"], ensure_ascii=False)[:200])
        else:
            content = (j["choices"][0]["message"].get("content") or "")
            check("HTTP 200", st == 200, "status=%s via=%s %.1fs" % (st, via, el))
            check("正文非空（L4 内容层）", len(content) > 0,
                  "len=%d" % len(content))
            check("正文含中文", any("\u4e00" <= ch <= "\u9fff" for ch in content),
                  content[:60].replace("\n", " "))
            check("标明实际通道", via in ("cnb", "fallback"), "via=%s" % via)
            print("      正文: %s" % content[:160].replace("\n", " "), flush=True)
    except Exception as e:
        check("非流式请求成功", False, "%s: %s" % (type(e).__name__, e))

    # ---- 4. 流式：验 SSE 事件与聚合正文 ----
    print("\n[4] 流式请求（验 SSE 与聚合正文）", flush=True)
    t0 = time.time()
    try:
        st, hd, body = post(base + "/v1/chat/completions", {
            "model": args.model,
            "messages": [{"role": "user", "content": "用一句话回答：什么是回测？"}],
            "stream": True,
        })
        el = time.time() - t0
        raw = body.decode("utf-8", "replace")
        lines = [l for l in raw.splitlines() if l.startswith("data:")]
        acc = []
        for l in lines:
            c = l[5:].strip()
            if c == "[DONE]" or not c:
                continue
            try:
                o = json.loads(c)
                for ch in o.get("choices", []):
                    d = ch.get("delta") or {}
                    if d.get("content"):
                        acc.append(d["content"])
            except Exception:
                pass
        txt = "".join(acc)
        check("HTTP 200", st == 200, "status=%s %.1fs" % (st, el))
        check("SSE 事件数 > 1", len(lines) > 1, "events=%d" % len(lines))
        check("聚合正文非空", len(txt) > 0, "len=%d" % len(txt))
        print("      正文: %s" % txt[:160].replace("\n", " "), flush=True)
    except Exception as e:
        check("流式请求成功", False, "%s: %s" % (type(e).__name__, e))

    return summarize()


def summarize():
    print("\n" + "=" * 60, flush=True)
    print("[selftest] 通过 %d 项，失败 %d 项" % (len(PASS), len(FAIL)), flush=True)
    if FAIL:
        for n, d in FAIL:
            print("   ❌ %s  %s" % (n, d), flush=True)
        print("[selftest] 结论：FAIL", flush=True)
        return 1
    print("[selftest] 结论：PASS（全部落在内容层）", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
