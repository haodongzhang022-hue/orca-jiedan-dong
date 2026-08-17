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
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional

# 双模式 MCP 插件运行时所在目录（与 loader 对齐，读取注册中心 + 探测健康）
HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_REGISTRY = os.environ.get(
    "HARNESS_MCP_REGISTRY",
    os.path.join(HARNESS_DIR, "config", "harness_mcp_registry.json"),
)
GATEWAY_PLUGIN_NAME = "gateway_3080_mcp"
# 双模式插件可用模型清单（与 plugins/gateway_3080/gateway_3080.py 的 MODEL_LIST 对齐）
GATEWAY_MODELS = [
    {"id": "deepseek-v4-flash", "object": "model", "owned_by": "cnb"},
    {"id": "z-ai/glm-5.2", "object": "model", "owned_by": "nvidia"},
]


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
# MCP 插件可视化管理（读取注册中心 + 健康/模式探测 + 启用禁用切换）
# ---------------------------------------------------------------------------

def _read_registry() -> dict:
    """读取 MCP 统一注册中心。"""
    try:
        with open(MCP_REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e), "services": {}}


def _write_registry(data: dict) -> None:
    """写回注册中心（保留原格式，仅更新 services 状态）。"""
    with open(MCP_REGISTRY, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _gateway_mode() -> str:
    """探测 gateway_3080 当前运行模式（环境变量 GW_MODE，默认 mcp）。"""
    return os.environ.get("GW_MODE", "mcp")  # mcp | http


def _http_health(gw_port: int = None) -> bool:
    """HTTP 模式下探测网关健康端点是否可达。"""
    port = gw_port or int(os.environ.get("GW_PORT", "3080"))
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.5):
            return True
    except OSError:
        return False


def _plugin_health(cfg: dict) -> dict:
    """探测单个插件健康状态。仅对 gateway_3080_mcp 做实际探测，其余返回配置态。"""
    if cfg.get("kind") != "mcp_plugin":
        return {"health": "ok", "detail": "配置加载正常"}
    mode = _gateway_mode()
    if mode == "http":
        ok = _http_health(int(cfg.get("env", {}).get("GW_PORT", "") or os.environ.get("GW_PORT", "3080")) \
                          or 3080)
        return {"health": "ok" if ok else "unreachable", "detail": "HTTP 网关可达" if ok else "HTTP 端口未就绪"}
    # MCP 模式：stdin/stdout 进程，无法简单 HTTP 探测；返回按 enabled 态推定
    enabled = cfg.get("enabled", False)
    return {"health": "ok" if enabled else "disabled", "detail": "MCP 模式（stdin/stdout）"}


def _list_plugins() -> list[dict]:
    """读取注册中心 services，返回插件/服务列表（含模式、健康、模型）。"""
    registry = _read_registry()
    services = registry.get("services", {})
    out = []
    for name, cfg in services.items():
        item = {
            "name": name,
            "title": cfg.get("title", name),
            "desc": cfg.get("desc", ""),
            "enabled": bool(cfg.get("enabled", False)),
            "kind": cfg.get("kind", ""),
            "dual_mode": bool(cfg.get("dual_mode", False)),
            "mode": _gateway_mode() if name == GATEWAY_PLUGIN_NAME else None,
        }
        h = _plugin_health(cfg)
        item["health"] = h.get("health")
        item["health_detail"] = h.get("detail")
        if name == GATEWAY_PLUGIN_NAME:
            item["models"] = GATEWAY_MODELS
        out.append(item)
    return out


def _toggle_plugin(name: str, enabled: bool) -> dict:
    """启用/禁用指定插件（写回注册中心）。

    用「目标行文本替换」方式更新，避免整文件重序列化导致的格式漂移
    （数组被拉成多行），从而保持注册中心文件格式与命令行链路完全兼容。
    命令行链路读同一份文件，天然向后兼容。
    """
    registry = _read_registry()
    services = registry.get("services", {})
    if name not in services:
        return {"ok": False, "error": f"插件 {name} 不存在"}

    with open(MCP_REGISTRY, "r", encoding="utf-8") as f:
        text = f.read()

    new_enabled = "true" if enabled else "false"
    # 定位 services.<name> 块，仅替换该块内首个 "enabled": xxx
    key = f'"{name}": {{'
    start = text.find(key)
    if start == -1:
        return {"ok": False, "error": f"插件 {name} 在文件中未找到"}
    brace_open = text.find("{", start + len(key))
    # 找到该 service 块的闭合大括号（粗略：按 } 计数）
    depth = 0
    end = -1
    for i in range(brace_open, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return {"ok": False, "error": f"插件 {name} 块解析失败"}
    block = text[start:end]
    import re as _re
    new_block, n = _re.subn(
        r'("enabled"\s*:\s*)(true|false)',
        lambda m: m.group(1) + new_enabled,
        block,
        count=1,
    )
    if n == 0:
        return {"ok": False, "error": f"插件 {name} 未找到 enabled 字段"}

    new_text = text[:start] + new_block + text[end:]

    # 同步更新 spawn_kill_matrix 中对应服务 spawn_at（兼容紧凑/多行两种格式）
    new_text = _re.sub(
        rf'("service": "{name}",\s*"spawn_at": ")([^"]*)(")',
        lambda m: m.group(1) + ("when_enabled" if enabled else "never") + m.group(3),
        new_text,
        count=1,
    )

    with open(MCP_REGISTRY, "w", encoding="utf-8") as f:
        f.write(new_text)
    return {"ok": True, "name": name, "enabled": enabled}


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
        elif self.path in ("/v1/orders/list", "/orders/list"):
            self._handle_order_list()
        elif self.path == "/plugins" or self.path.startswith("/plugins/"):
            self._handle_plugins_get()
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
            elif self.path.startswith("/plugins/") and self.path.endswith("/toggle"):
                self._handle_plugins_toggle()
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

    # ---- MCP 插件可视化端点 ----
    def _handle_plugins_get(self):
        """GET /plugins（列表） 或 /plugins/<name>（详情）。"""
        if self.path in ("/plugins", "/plugins/"):
            self._send({"ok": True, "registry_version": _read_registry().get("version", ""),
                        "plugins": _list_plugins()}, 200)
            return
        name = self.path[len("/plugins/"):].rstrip("/")
        if not name or "/" in name:
            self._send({"error": "bad path"}, 404)
            return
        found = None
        for p in _list_plugins():
            if p["name"] == name:
                found = p
                break
        if not found:
            self._send({"error": f"插件 {name} 不存在"}, 404)
            return
        self._send({"ok": True, "plugin": found}, 200)

    def _handle_plugins_toggle(self):
        """POST /plugins/<name>/toggle  body={"enabled": true|false}"""
        name = self.path[len("/plugins/"):-len("/toggle")]
        payload = self._read_json()
        enabled = bool(payload.get("enabled", False))
        result = _toggle_plugin(name, enabled)
        self._send(result, 200 if result.get("ok") else 404)

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
    print(f"[DeepSeek-Harness] 端点: /v1/chat/completions(流式) /v1/models /v1/orders(企微接单) /harness(编排) /plugins(MCP插件UI) /console")
    server.serve_forever()


if __name__ == "__main__":
    main()
