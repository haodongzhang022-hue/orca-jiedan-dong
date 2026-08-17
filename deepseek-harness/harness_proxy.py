#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Harness · 云端免费网关代理（OpenAI 兼容 + 企业微信接单入口）
=========================================================================
职责：
  1. 对外暴露 OpenAI 兼容的 /v1/chat/completions（含流式），模型 = CNB 内置免费 DeepSeek-V4-Flash
  2. 自动处理 CNB 免费网关「仅支持流式」硬约束：非流式请求在代理内强制转流式聚合后返回
  3. 提供 /v1/orders 企业微信群接单入口：派单 → 自动建档任务卡 → 进入订单流水线
  4. /health 健康检查 + /v1/models 模型列表
  5. 密钥零落盘：CNB_TOKEN / ACC_PRODUCT_CONFIG_V2 全部来自环境变量注入

非 Hermes Studio：这是独立自研的 DeepSeek Harness 云端运行时，不走 hermes-web-ui 镜像。

启动:
  CNB_TOKEN=xxx python3 harness_proxy.py --port 8080

客户端指向:
  base_url = http://<host>:8080/v1
  api_key  = 任意占位（代理在容器内自取 CNB_TOKEN 上送网关）
  model    = deepseek-v4-flash
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 配置（全环境变量注入）
# ---------------------------------------------------------------------------

def _resolve_gateway() -> str:
    """解析 CNB 内置 AI 网关 chat/completions 端点。"""
    slug = os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan")
    explicit = os.environ.get("CNB_AI_GATEWAY", "").strip()
    if explicit:
        base = explicit.rstrip("/")
        return base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    raw = os.environ.get("ACC_PRODUCT_CONFIG_V2", "")
    if raw:
        try:
            cfg = json.loads(raw)
            ep = cfg.get("endpoint", "").strip().rstrip("/")
            if ep.endswith("/ai-ide"):
                return ep.replace("/ai-ide", "/ai/chat/completions")
            if ep.endswith("/chat/completions"):
                return ep
            return f"{ep}/chat/completions"
        except Exception:
            pass
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
    "listen_host": os.environ.get("HARNESS_HOST", "0.0.0.0"),
    "listen_port": int(os.environ.get("HARNESS_PORT", "8080")),
    "cnb_gateway": _resolve_gateway(),
    "model": os.environ.get("CNB_MODEL", "deepseek-v4-flash"),
    "cnb_token": _resolve_token(),
}

# 可用模型白名单（免费档）
AVAILABLE_MODELS = {
    "deepseek-v4-flash": "DeepSeek V4 Flash (CNB 免费)",
    "deepseek-r1": "DeepSeek R1 (CNB 免费)",
    "qwen3-235b-a22b": "Qwen3 235B (CNB 免费)",
}

# 订单存储（企业微信接单 → 任务卡落盘）
ORDER_DIR = os.environ.get("HARNESS_ORDER_DIR", "./harness_orders")
os.makedirs(ORDER_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 企业微信接单 → 任务卡建档
# ---------------------------------------------------------------------------

def _sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("_")


def create_order_card(order: Dict[str, Any]) -> Dict[str, Any]:
    """企业微信派单 → 结构化任务卡建档。"""
    order.setdefault("order_id", f"HW{int(time.time())}")
    order.setdefault("created_at", time.strftime("%Y%m%d_%H%M%S"))
    order.setdefault("status", "已接单")
    order.setdefault("deliverables", [])
    order.setdefault("spec", "")

    # 任务卡五段结构
    card = f"""# 任务卡 · {order['order_id']}

## 一、订单信息
- 派单时间：{order.get('created_at')}
- 客户：{order.get('customer', '待确认')}
- 品类：{order.get('category', '待确认')}
- 需求：{order.get('demand', '')}
- 规格：{order.get('spec', '')}
- 群规则：{order.get('group_rule', '待确认')}
- 结算：{order.get('settle', '待确认')}

## 二、交付物清单
{chr(10).join('- ' + d for d in order.get('deliverables', [])) or '- 待确认'}

## 三、执行状态
- 状态：{order.get('status')}

## 四、备注
{order.get('note', '')}
"""
    card_name = f"{order['created_at']}_{_sanitize(str(order.get('customer', '客户')))}_任务卡.md"
    card_path = os.path.join(ORDER_DIR, card_name)
    with open(card_path, "w", encoding="utf-8") as f:
        f.write(card)
    order["card_path"] = card_path
    return order


# ---------------------------------------------------------------------------
# 免费网关调用（强制流式，支持非流式聚合）
# ---------------------------------------------------------------------------

def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CFG['cnb_token']}",
    }


def stream_chat(messages: List[Dict[str, Any]], model: str = None,
                temperature: float = 0.7, max_tokens: int = 4096):
    """以流式方式调用 CNB 免费网关，yield SSE 行（含 content 块）。"""
    model = model or CFG["model"]
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
            if not line:
                continue
            yield line


def non_stream_chat(messages: List[Dict[str, Any]], model: str = None,
                    temperature: float = 0.7, max_tokens: int = 4096) -> Dict[str, Any]:
    """非流式调用：内部强制流式拉全量后聚合为 OpenAI 响应。"""
    model = model or CFG["model"]
    content_parts: List[str] = []
    finish = ""
    for line in stream_chat(messages, model, temperature, max_tokens):
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except Exception:
            continue
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        text = delta.get("content", "")
        if text:
            content_parts.append(text)
        finish = chunk.get("choices", [{}])[0].get("finish_reason") or finish
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "".join(content_parts)},
            "finish_reason": finish or "stop",
        }],
        "usage": {
            "prompt_tokens": sum(len(m.get("content", "")) for m in messages),
            "completion_tokens": len("".join(content_parts)),
            "total_tokens": sum(len(m.get("content", "")) for m in messages) + len("".join(content_parts)),
        },
    }


# ---------------------------------------------------------------------------
# HTTP Handler
# ---------------------------------------------------------------------------

class HarnessHandler(BaseHTTPRequestHandler):

    def _send(self, data, status=200, ctype="application/json"):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8") if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_stream(self, lines):
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

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        return json.loads(raw) if raw else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send({"status": "ok", "model": CFG["model"], "gateway": CFG["cnb_gateway"],
                        "token_prefix": CFG["cnb_token"][:12] if CFG["cnb_token"] else "EMPTY"})
        elif self.path.startswith("/v1/models"):
            self._send({"object": "list", "data": [{"id": k, "object": "model", "owned_by": "cnb"} for k in AVAILABLE_MODELS]})
        elif self.path == "/" or self.path == "/console":
            self._send(open(os.path.join(os.path.dirname(__file__), "web_console.html"), "rb").read(),
                       ctype="text/html; charset=utf-8")
        elif self.path.startswith("/harness"):
            self._handle_harness_get()
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        try:
            if self.path in ("/v1/chat/completions", "/chat/completions"):
                self._handle_chat()
            elif self.path in ("/v1/orders", "/orders"):
                self._handle_order()
            elif self.path == "/v1/orders/list":
                self._handle_order_list()
            elif self.path == "/harness":
                self._handle_harness_post()
            else:
                self._send({"error": f"unknown endpoint {self.path}"}, 404)
        except Exception as e:
            self._send({"error": str(e)}, 500)

    def _handle_chat(self):
        payload = self._read_json()
        model = payload.get("model", CFG["model"])
        if model not in AVAILABLE_MODELS:
            self._send({"error": f"模型 '{model}' 不可用，可选: {list(AVAILABLE_MODELS.keys())}"}, 400)
            return
        messages = payload.get("messages", [])
        if payload.get("stream", False):
            self._send_stream(self._iter_chat(messages, model, payload))
        else:
            result = non_stream_chat(messages, model,
                                     payload.get("temperature", 0.7),
                                     payload.get("max_tokens", 4096))
            self._send(result)

    def _iter_chat(self, messages, model, payload):
        temp = payload.get("temperature", 0.7)
        max_tokens = payload.get("max_tokens", 4096)
        for line in stream_chat(messages, model, temp, max_tokens):
            yield line
        yield "data: [DONE]"

    def _handle_order(self):
        order = self._read_json()
        if not order:
            self._send({"error": "空订单"}, 400)
            return
        saved = create_order_card(order)
        self._send({"ok": True, "order": saved}, 200)

    def _handle_harness(self, task: str, session: str):
        try:
            import harness_agent
        except Exception:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "harness_agent", os.path.join(os.path.dirname(os.path.abspath(__file__)), "harness_agent.py"))
            harness_agent = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(harness_agent)
        bind_port = getattr(self.server, 'server_address', (None, CFG['listen_port']))[1] or CFG['listen_port']
        harness_agent.GATEWAY_BASE = f"http://127.0.0.1:{bind_port}/v1"
        result = harness_agent.run_harness(task, session)
        # 返回纯文本交付结论
        text = (
            "【DeepSeek-Harness 交付结论】\n\n" +
            result["final"] +
            "\n\n【执行计划】\n" +
            "\n".join(f"- [{s.get('skill','')}] {s.get('step',s.get('goal',''))}" for s in result["plan"])
        )
        self._send(text.encode("utf-8"), ctype="text/plain; charset=utf-8")

    def _handle_harness_get(self):
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(self.path).query)
        task = (q.get("task") or ["设计一张企业宣传单"])[0]
        session = (q.get("session") or ["default"])[0]
        self._handle_harness(task, session)

    def _handle_harness_post(self):
        payload = self._read_json()
        task = payload.get("task", "设计一张企业宣传单")
        session = payload.get("session", "default")
        self._handle_harness(task, session)

    def _handle_order_list(self):
        cards = []
        for fn in sorted(os.listdir(ORDER_DIR)):
            if fn.endswith(".md"):
                cards.append(fn)
        self._send({"ok": True, "orders": cards}, 200)

    def log_message(self, fmt, *args):
        pass


# ---------------------------------------------------------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=CFG["listen_port"])
    ap.add_argument("--host", default=CFG["listen_host"])
    args = ap.parse_args()

    if not CFG["cnb_token"]:
        print("[HARNESS][WARN] CNB_TOKEN 未设置，免费网关调用将失败。请在容器环境注入。")
    server = ThreadingHTTPServer((args.host, args.port), HarnessHandler)
    print(f"[DeepSeek-Harness] 云端 Harness 网关已启动: http://{args.host}:{args.port}")
    print(f"[DeepSeek-Harness] 免费模型基座: {CFG['model']}")
    print(f"[DeepSeek-Harness] CNB 免费网关: {CFG['cnb_gateway']}")
    print(f"[DeepSeek-Harness] 端点: /v1/chat/completions(流式) /v1/models /v1/orders(企微接单) /harness(编排) /console")
    server.serve_forever()


if __name__ == "__main__":
    main()
