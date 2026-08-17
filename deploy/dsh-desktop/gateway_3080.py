#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本机 3080 本地网关客户端（示例骨架）· 出站模式
=========================================================================
核心结论（来自调研报告）：
  ✗ 不做本地端口反向隧道推送到云端（本机服务无法 "推上云端"，且违反安全红线）
  ✓ 本机 3080 作为「本地网关客户端」，主动出站 HTTPS 调用 CNB 官方 OpenAPI，
    间接使用云端免费 DeepSeek-V4-Flash。
  ✓ WebUI 可视化调试仅放在 Workspace 的代理 URL，不作为正式生产服务。

职责：
  1. 本机/内网工具统一访问 http://127.0.0.1:3080/v1/chat/completions
  2. 本网关在后端转发请求到 CNB 云原生 OpenAPI（出站 HTTPS）
  3. 兼容流式与非流式（CNB 免费网关仅支持流式，非流式本地自动聚合）

密钥零落盘：CNB_TOKEN 由环境变量注入，本文件/镜像不含明文。

启动:
  CNB_TOKEN=xxx python3 gateway_3080.py --port 3080
"""
from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# ---------------------------------------------------------------------------
# 配置（全环境变量注入，零明文）
# ---------------------------------------------------------------------------

def _resolve_gateway() -> str:
    """解析 CNB 官方 OpenAPI 网关（出站 HTTPS 目标）。"""
    explicit = os.environ.get("CNB_AI_GATEWAY", "").strip()
    if explicit:
        base = explicit.rstrip("/")
        return base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    # 默认走当前仓库 CNB 免费网关
    slug = os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan")
    return f"https://api.cnb.cool/{slug}/-/ai/chat/completions"


def _resolve_token() -> str:
    tok = os.environ.get("CNB_TOKEN", "")
    if not tok:
        try:
            cfg = json.loads(os.environ.get("ACC_PRODUCT_CONFIG_V2", "{}"))
            tok = cfg.get("authentication", {}).get("attributes", {}).get("token", "")
        except Exception:
            pass
    return tok


CFG = {
    "listen_host": os.environ.get("GW_HOST", "127.0.0.1"),   # 仅本机/内网，不对外暴露
    "listen_port": int(os.environ.get("GW_PORT", "3080")),
    "cnb_gateway": _resolve_gateway(),
    "model": os.environ.get("CNB_MODEL", "deepseek-v4-flash"),
    "cnb_token": _resolve_token(),
}


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CFG['cnb_token']}",
    }


# ---------------------------------------------------------------------------
# 出站转发：调 CNB OpenAPI（强制流式）
# ---------------------------------------------------------------------------

def stream_forward(messages: list, model: str, temperature: float, max_tokens: int):
    """出站 HTTPS 调用 CNB 网关，以流式 yield SSE 行。"""
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        CFG["cnb_gateway"],
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        for line in resp:
            line = line.decode("utf-8", errors="replace").strip()
            if line:
                yield line


def non_stream_aggregate(messages: list, model: str, temperature: float, max_tokens: int) -> dict:
    """非流式：内部强制流式拉全量后聚合为 OpenAI 完整响应。"""
    parts: list[str] = []
    for line in stream_forward(messages, model, temperature, max_tokens):
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            delta = json.loads(data).get("choices", [{}])[0].get("delta", {})
            if delta.get("content"):
                parts.append(delta["content"])
        except Exception:
            continue
    return {
        "id": f"chatcmpl-{os.getpid()}",
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "".join(parts)}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": sum(len(m.get("content", "")) for m in messages),
                  "completion_tokens": len("".join(parts)),
                  "total_tokens": sum(len(m.get("content", "")) for m in messages) + len("".join(parts))},
    }


# ---------------------------------------------------------------------------
# HTTP Handler（本机网关）
# ---------------------------------------------------------------------------

class GatewayHandler(BaseHTTPRequestHandler):

    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, lines):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        for ln in lines:
            self.wfile.write(ln.encode("utf-8"))
            self.wfile.write(b"\n\n")
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw) if raw else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json({"status": "ok", "mode": "outbound", "model": CFG["model"],
                        "gateway": CFG["cnb_gateway"],
                        "token_prefix": CFG["cnb_token"][:12] if CFG["cnb_token"] else "EMPTY"})
        elif self.path.startswith("/v1/models"):
            self._json({"object": "list", "data": [
                {"id": "deepseek-v4-flash", "object": "model", "owned_by": "cnb"},
                {"id": "z-ai/glm-5.2", "object": "model", "owned_by": "nvidia"},
            ]})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self._json({"error": f"unknown endpoint {self.path}"}, 404)
            return
        payload = self._read_json()
        messages = payload.get("messages", [])
        model = payload.get("model", CFG["model"])
        temp = payload.get("temperature", 0.7)
        max_tokens = payload.get("max_tokens", 4096)
        try:
            if payload.get("stream", False):
                self._sse(stream_forward(messages, model, temp, max_tokens))
            else:
                self._json(non_stream_aggregate(messages, model, temp, max_tokens))
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)

    def log_message(self, fmt, *args):  # 静默日志
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=CFG["listen_port"])
    ap.add_argument("--host", default=CFG["listen_host"])
    args = ap.parse_args()
    if not CFG["cnb_token"]:
        print("[GW3080][WARN] CNB_TOKEN 未设置，出站调用将失败。")
    server = ThreadingHTTPServer((args.host, args.port), GatewayHandler)
    print(f"[GW3080] 本地网关客户端已启动（出站模式）: http://{args.host}:{args.port}")
    print(f"[GW3080] 出站目标: {CFG['cnb_gateway']}")
    print("[GW3080] 端点: /health /v1/models /v1/chat/completions(流式+非流式聚合)")
    server.serve_forever()


if __name__ == "__main__":
    main()
