#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNB LLM Adapter v1.0 — 标准 OpenAI 接口 → CNB 内置免费网关（dsh / ds-bot 专用）

【为什么需要这一层】
CNB 内置免费网关有两个硬约束，dsh 的 llm-pi-ai provider 无法直接适配：
  1) 路径非标准：.../-/ai/chat/completions，不是标准 /v1/chat/completions
  2) 仅支持流式：stream=false 直接返回 400 code 11101
本适配层对外暴露【标准】OpenAI 接口，对内强制流式 + 自动聚合，彻底隔离这两个坑。

【对外接口（容器内 0.0.0.0:15741）】
  GET  /health              → {"status":"ok", ...}
  GET  /v1/models           → OpenAI 格式模型清单
  POST /v1/chat/completions → 支持 stream=true / false 两种

【回落链】
  CNB 免费网关（主） → FALLBACK_BASE（备，如本机 15740 免费池）
  CNB 返回 401/400/5xx/超时 时自动切换，并在响应头 X-Adapter-Via 标注实际通道。

【安全】
  密钥零落盘：CNB_TOKEN / ACC_PRODUCT_CONFIG_V2 全部来自环境变量注入。
  日志只打印脱敏后的前 6 位前缀。

【启动】
  python3 cnb_llm_adapter.py --port 15741
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---------------------------------------------------------------------------
# 配置区（全部来自环境变量，镜像零硬编码密钥）
# ---------------------------------------------------------------------------
DEFAULT_SLUG = os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan")
DEFAULT_MODEL = os.environ.get("CNB_MODEL", "deepseek-v4-flash")
FALLBACK_BASE = os.environ.get("FALLBACK_BASE", "").rstrip("/")
UPSTREAM_TIMEOUT = float(os.environ.get("ADAPTER_TIMEOUT", "180"))

# CNB 网关可用模型白名单（据 cnb_proxy_clouddev.py 实测）
CNB_MODELS = {
    "deepseek-v4-flash": "DeepSeek V4 Flash (CNB Free)",
    "deepseek-r1": "DeepSeek R1 (CNB Free)",
    "qwen3-235b-a22b": "Qwen3 235B (CNB Free)",
}

# 模型名归一：dsh 侧可能写带 -free 后缀的名字，转成 CNB 认的
MODEL_ALIAS = {
    "deepseek-v4-flash-free": "deepseek-v4-flash",
    "deepseek-v4-pro-free": "deepseek-v4-flash",
    "glm-5.3-flash-free": "deepseek-v4-flash",
    "deepseek-v4": "deepseek-v4-flash",
    "deepseek-chat": "deepseek-v4-flash",
    "gpt-4o": "deepseek-v4-flash",
}


def mask(s):
    """脱敏：只留前 6 位"""
    if not s:
        return "(空)"
    return (s[:6] + "***") if len(s) > 6 else "***"


def resolve_gateway():
    """解析 CNB 内置免费网关端点。
    优先 CNB_AI_GATEWAY 显式注入 → 其次 ACC_PRODUCT_CONFIG_V2.endpoint → 最后按 slug 拼。
    """
    explicit = os.environ.get("CNB_AI_GATEWAY", "").strip()
    if explicit:
        base = explicit.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/ai-ide"):
            return base.replace("/ai-ide", "/ai/chat/completions")
        return base + "/chat/completions"

    raw = os.environ.get("ACC_PRODUCT_CONFIG_V2", "")
    if raw:
        try:
            cfg = json.loads(raw)
            ep = (cfg.get("endpoint") or "").strip().rstrip("/")
            if ep:
                if ep.endswith("/ai-ide"):
                    return ep.replace("/ai-ide", "/ai/chat/completions")
                if ep.endswith("/chat/completions"):
                    return ep
                return ep + "/chat/completions"
        except Exception as e:
            print("[adapter] ACC_PRODUCT_CONFIG_V2 解析失败: %s" % e, flush=True)

    return "https://api.cnb.cool/%s/-/ai/chat/completions" % DEFAULT_SLUG


def resolve_token():
    """CNB 鉴权 Token。

    优先级（重要，踩过坑）：
      1) ACC_PRODUCT_CONFIG_V2.authentication.attributes.token
         ← 这是 CNB **AI 网关专用**凭证，容器内自动注入
      2) CNB_TOKEN
         ← 普通流水线令牌，实测直接打 AI 网关会 403
            [NO_RIGHT]OpenAPI only allowed in pipeline
    顺序不能反，否则容器内也会误用普通令牌导致 403。
    """
    try:
        cfg = json.loads(os.environ.get("ACC_PRODUCT_CONFIG_V2", "{}"))
        tok = (cfg.get("authentication", {}).get("attributes", {}).get("token") or "").strip()
        if tok:
            return tok
    except Exception:
        pass
    return os.environ.get("CNB_TOKEN", "").strip()


CNB_GATEWAY = resolve_gateway()
CNB_TOKEN = resolve_token()
START_TS = time.time()


def normalize_model(name):
    n = (name or "").strip()
    n = MODEL_ALIAS.get(n, n)
    if n not in CNB_MODELS:
        # 未知模型统一落到默认，避免 404 model not found
        return DEFAULT_MODEL
    return n


def build_payload(body, force_stream):
    """构造发往 CNB 的请求体：强制 stream，剔掉 CNB 不认的字段。"""
    p = dict(body)
    p["model"] = normalize_model(p.get("model"))
    p["stream"] = bool(force_stream)
    # CNB 网关不接受的标准外字段，剔除避免 400
    for k in ("stream_options", "response_format", "tools", "tool_choice",
              "logprobs", "top_logprobs", "n", "parallel_tool_calls"):
        p.pop(k, None)
    if "max_tokens" not in p or not p.get("max_tokens"):
        # 铁律第38形态：不给 max_tokens 时部分免费池会返回空正文
        p["max_tokens"] = int(os.environ.get("ADAPTER_MAX_TOKENS", "4096"))
    return p


def http_post(url, payload, headers, timeout):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=timeout)


def parse_sse_to_result(raw_bytes, model):
    """把 SSE 流聚合成标准非流式响应。"""
    text = raw_bytes.decode("utf-8", "replace")
    content_parts, reasoning_parts = [], []
    usage, finish = None, None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            obj = json.loads(chunk)
        except Exception:
            continue
        if obj.get("usage"):
            usage = obj["usage"]
        for ch in obj.get("choices", []):
            d = ch.get("delta") or {}
            if d.get("content"):
                content_parts.append(d["content"])
            if d.get("reasoning_content"):
                reasoning_parts.append(d["reasoning_content"])
            if ch.get("finish_reason"):
                finish = ch["finish_reason"]

    content = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    if usage is None:
        # CNB 不回 usage 时给个估算，保证客户端不炸
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": max(1, len(content) // 2),
            "total_tokens": max(1, len(content) // 2),
        }

    msg = {"role": "assistant", "content": content}
    if reasoning:
        msg["reasoning_content"] = reasoning

    return {
        "id": "chatcmpl-cnb-%d" % int(time.time() * 1000),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": msg, "finish_reason": finish or "stop"}],
        "usage": usage,
    }


def sse_to_standard(raw_bytes, model):
    """把 CNB 的 SSE 转成标准 OpenAI SSE（客户端要流式时用）。"""
    text = raw_bytes.decode("utf-8", "replace")
    out = []
    cid = "chatcmpl-cnb-%d" % int(time.time() * 1000)
    created = int(time.time())
    first = {
        "id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
    }
    out.append("data: " + json.dumps(first, ensure_ascii=False) + "\n\n")
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            obj = json.loads(chunk)
        except Exception:
            continue
        for ch in obj.get("choices", []):
            d = ch.get("delta") or {}
            piece = {"index": 0, "delta": {}, "finish_reason": ch.get("finish_reason")}
            if d.get("content"):
                piece["delta"]["content"] = d["content"]
            if d.get("reasoning_content"):
                piece["delta"]["reasoning_content"] = d["reasoning_content"]
            if piece["delta"] or piece["finish_reason"]:
                wrap = {"id": cid, "object": "chat.completion.chunk", "created": created,
                        "model": model, "choices": [piece]}
                out.append("data: " + json.dumps(wrap, ensure_ascii=False) + "\n\n")
    out.append("data: [DONE]\n\n")
    return "".join(out).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # 静默默认访问日志，避免刷屏；关键信息自己打
        pass

    def _send_json(self, code, obj, extra_headers=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, code, body, ctype, extra_headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/health", "/healthz"):
            self._send_json(200, {
                "status": "ok",
                "service": "cnb-llm-adapter",
                "version": "1.0.0",
                "gateway": CNB_GATEWAY,
                "token": mask(CNB_TOKEN),
                "fallback": FALLBACK_BASE or "(未配置)",
                "default_model": DEFAULT_MODEL,
                "uptime_s": round(time.time() - START_TS, 1),
            })
            return
        if path == "/v1/models":
            self._send_json(200, {
                "object": "list",
                "data": [{"id": k, "object": "model", "owned_by": "cnb-free", "description": v}
                         for k, v in CNB_MODELS.items()],
            })
            return
        self._send_json(404, {"error": {"message": "not found: %s" % path, "type": "not_found"}})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/v1/chat/completions", "/chat/completions"):
            self._send_json(404, {"error": {"message": "not found: %s" % path, "type": "not_found"}})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send_json(400, {"error": {"message": "invalid json: %s" % e, "type": "invalid_request"}})
            return

        want_stream = bool(body.get("stream"))
        model = normalize_model(body.get("model"))

        headers = {"Content-Type": "application/json"}
        if CNB_TOKEN:
            headers["Authorization"] = "Bearer " + CNB_TOKEN

        upstream_headers = dict(headers)
        upstream_payload = build_payload(body, force_stream=True)

        via, error_note = "cnb", ""
        raw = b""
        try:
            resp = http_post(CNB_GATEWAY, upstream_payload, upstream_headers, UPSTREAM_TIMEOUT)
            raw = resp.read()
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:300]
            except Exception:
                pass
            error_note = "CNB HTTP %s: %s" % (e.code, detail)
            via = ""
        except Exception as e:
            error_note = "CNB 异常 %s: %s" % (type(e).__name__, e)
            via = ""

        # ---- 回落链 ----
        if not via and FALLBACK_BASE:
            print("[adapter] CNB 失败(%s) → 回落 %s" % (error_note, FALLBACK_BASE), flush=True)
            try:
                # 回落通道一律走非流式：拿完整 JSON 后由本层自行决定怎么吐给客户端。
                # 原因：免费池的 SSE 在本机实测会卡住不结束，非流式稳定且可精确校验正文。
                fb_payload = build_payload(body, force_stream=False)
                fb_headers = {"Content-Type": "application/json",
                              "Authorization": "Bearer " + os.environ.get("FALLBACK_KEY", "fallback")}
                resp = http_post(FALLBACK_BASE + "/chat/completions", fb_payload, fb_headers, UPSTREAM_TIMEOUT)
                raw = resp.read()
                via = "fallback"
                error_note = ""
            except Exception as e:
                error_note += " | fallback 也失败: %s" % e

        if not via:
            self._send_json(502, {"error": {"message": error_note or "upstream unavailable",
                                            "type": "upstream_error"}})
            return

        # 回落通道给的是完整 JSON
        if via == "fallback" and raw.lstrip()[:1] == b"{":
            try:
                obj = json.loads(raw)
                if obj.get("error"):
                    # 上游返回了带 error 的 JSON，不能当成功透传
                    self._send_json(502, {"error": {"message": "fallback upstream error: %s"
                                                    % json.dumps(obj["error"], ensure_ascii=False)[:300],
                                                    "type": "upstream_error"}})
                    return
                obj.setdefault("model", model)
                content = ((obj.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
                if not content:
                    print("[adapter] ⚠️ fallback 正文为空 model=%s raw_bytes=%d" % (model, len(raw)), flush=True)
                if want_stream:
                    # 客户端要流式，把整包拆成 SSE 发出去
                    self._send_bytes(200, self._sse_from_text(content, model), "text/event-stream",
                                     {"X-Adapter-Via": via})
                else:
                    self._send_json(200, obj, {"X-Adapter-Via": via})
                return
            except Exception as e:
                print("[adapter] fallback JSON 解析失败: %s" % e, flush=True)

        # ---- CNB 流式结果 → 按客户端需要输出 ----
        if want_stream:
            self._send_bytes(200, sse_to_standard(raw, model), "text/event-stream",
                             {"X-Adapter-Via": via, "Cache-Control": "no-cache"})
        else:
            result = parse_sse_to_result(raw, model)
            content = (result["choices"][0]["message"].get("content") or "")
            if not content:
                # 铁律第38形态：200 但正文为空必须显式告警，不能静默返回空
                print("[adapter] ⚠️ 聚合后正文为空 model=%s via=%s raw_bytes=%d"
                      % (model, via, len(raw)), flush=True)
            self._send_json(200, result, {"X-Adapter-Via": via})

    def _sse_from_text(self, text, model):
        cid = "chatcmpl-fb-%d" % int(time.time() * 1000)
        created = int(time.time())
        parts = [
            {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
             "choices": [{"index": 0, "delta": {"role": "assistant", "content": text},
                          "finish_reason": None}]},
            {"id": cid, "object": "chat.completion.chunk", "created": created, "model": model,
             "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        ]
        return ("".join("data: " + json.dumps(p, ensure_ascii=False) + "\n\n" for p in parts)
                + "data: [DONE]\n\n").encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=15741)
    args = ap.parse_args()

    print("=" * 62, flush=True)
    print("[adapter] CNB LLM Adapter v1.0 启动", flush=True)
    print("[adapter] 监听        : %s:%d" % (args.host, args.port), flush=True)
    print("[adapter] CNB 网关    : %s" % CNB_GATEWAY, flush=True)
    print("[adapter] CNB Token   : %s" % mask(CNB_TOKEN), flush=True)
    print("[adapter] 回落通道    : %s" % (FALLBACK_BASE or "(未配置)"), flush=True)
    print("[adapter] 默认模型    : %s" % DEFAULT_MODEL, flush=True)
    if not CNB_TOKEN:
        print("[adapter] ⚠️ CNB_TOKEN 未注入，主通道将 401 → 必须有回落通道兜底", flush=True)
    print("=" * 62, flush=True)

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("[adapter] 收到中断，退出", flush=True)
        srv.shutdown()


if __name__ == "__main__":
    main()
