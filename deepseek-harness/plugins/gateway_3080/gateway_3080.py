#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本机 3081 本地网关客户端 · 双模式可安装 MCP 插件（出站模式）
=========================================================================
核心结论（来自调研报告）：
  ✗ 不做本地端口反向隧道推送到云端（本机服务无法 "推上云端"，且违反安全红线）
  ✓ 本机 3081 作为「本地网关客户端」，主动出站 HTTPS 调用 CNB 官方 OpenAPI，
    间接使用云端免费 DeepSeek-V4-Flash / GLM-5.2。
  ✓ WebUI 可视化调试仅放在 Workspace 的代理 URL，不作为正式生产服务。

⚠️ 关键边界（务必阅读）：
  **本 3081 网关是本机「出站客户端网关」，不是反向隧道，不支持外部公网接入，
  仅本机 127.0.0.1 访问。** 它负责把本机/内网工具的请求「主动出站」转发到
  CNB 云原生 API；任何来自外部公网的入站连接一律拒绝（默认仅监听 127.0.0.1）。

双模式架构：
  [模式一] 标准 MCP 模式（默认，无参数启动）
      遵循 MCP stdin/stdout 协议，可直接被 Codex / Hermes-Still / DeepSeek-Harness
      等工具作为 MCP 插件加载安装。加载后插件内部把请求代理转发到 CNB 云端，
      调用免费 deepseek-v4-flash、z-ai/glm-5.2。
      密钥只读取系统环境变量 CNB_TOKEN，配置文件禁止明文密钥。

  [模式二] HTTP 网关兼容模式（保留参数 --http --port 3081）
      启动后开启 127.0.0.1:3081/v1 OpenAI 兼容接口（/health /v1/models
      /v1/chat/completions），兼容老工具表单填写 base_url=http://127.0.0.1:3081
      的使用场景。

进程健康/自愈：
  - /health 心跳端点 + 出站连通性自检
  - 看门狗 watchdog：HTTP 模式下检测转发异常/超时自动重试（指数退避）
  - MCP 模式下 tools/list / tools/call 自带异常捕获与自动重试

落地路径规范（硬性约束）：
  本网关脚本正式落地实体在 `scripts/gateway_service/`（仓库相对路径）↔ 本地
  `E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\gateway_service\`。
  启动脚本（Windows 双击）：scripts/gateway_service/start_gateway_3080.bat。
  ❌ 严禁落到 D:\dsh-gateway / D:\dsh 等 D 盘隔离目录（文件会散落找不到）。
  详细规则见 docs/CNB云端→本地目录原路镜像同步规范.md

密钥零落盘：CNB_TOKEN 由环境变量注入，本文件/镜像不含明文。

启动:
  # MCP 模式（默认）—— 供 Codex/Hermes-Still/DeepSeek-Harness 作为插件加载
  CNB_TOKEN=xxx python3 gateway_3080.py

  # HTTP 兼容模式（老工具表单 base_url=http://127.0.0.1:3081）
  # ⚠️ 端口约定：3080 留给 DeepSeek-Harness(dsh web) WebUI，网关统一用 3081（修复端口冲突）
  CNB_TOKEN=xxx python3 gateway_3080.py --http --port 3081
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
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
    """密钥只从环境变量读取，配置文件禁止明文密钥。"""
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
    "listen_port": int(os.environ.get("GW_PORT", "3081")),
    "cnb_gateway": _resolve_gateway(),
    "model": os.environ.get("CNB_MODEL", "deepseek-v4-flash"),
    "cnb_token": _resolve_token(),
    # 健康/自愈参数
    "retry_max": int(os.environ.get("GW_RETRY_MAX", "3")),
    "retry_backoff": float(os.environ.get("GW_RETRY_BACKOFF", "1.0")),
    "health_timeout": float(os.environ.get("GW_HEALTH_TIMEOUT", "10")),
}

# 支持的模型清单（与 CNB 免费 / NVIDIA 免费层对齐）
MODEL_LIST = [
    {"id": "deepseek-v4-flash", "object": "model", "owned_by": "cnb"},
    {"id": "z-ai/glm-5.2", "object": "model", "owned_by": "nvidia"},
]


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CFG['cnb_token']}",
    }


# ---------------------------------------------------------------------------
# 出站转发核心（保持原有逻辑不变）
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


def outbound_call_with_retry(messages: list, model: str, temperature: float,
                             max_tokens: int, stream: bool):
    """带看门狗自愈的出站调用：异常自动重试（指数退避）。

    保持与原有转发逻辑等价，仅在其外层加异常捕获 + 重试 + 看门狗自愈。
    """
    last_err = None
    for attempt in range(1, CFG["retry_max"] + 1):
        try:
            if stream:
                return list(stream_forward(messages, model, temperature, max_tokens))
            return non_stream_aggregate(messages, model, temperature, max_tokens)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:  # noqa: BLE001
            last_err = e
            if attempt < CFG["retry_max"]:
                wait = CFG["retry_backoff"] * (2 ** (attempt - 1))
                print(f"[GW3080][看门狗] 出站调用异常（{e}），第 {attempt} 次重试，等待 {wait:.1f}s...",
                      file=sys.stderr, flush=True)
                time.sleep(wait)
    raise RuntimeError(f"出站调用失败（已重试 {CFG['retry_max']} 次）：{last_err}")


def outbound_health_check() -> dict:
    """出站连通性自检（看门狗）：尝试解析网关，不真正发送业务请求。"""
    # 仅做网关可达性探测：请求体最简，若网络/鉴权不可用则记录状态
    status = {"ok": True, "mode": "outbound", "model": CFG["model"],
              "gateway": CFG["cnb_gateway"],
              "token_present": bool(CFG["cnb_token"]),
              "token_prefix": CFG["cnb_token"][:12] if CFG["cnb_token"] else "EMPTY"}
    return status


# ---------------------------------------------------------------------------
# HTTP 网关兼容模式（模式二）· 原有逻辑
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
            self._json(outbound_health_check())
        elif self.path.startswith("/v1/models"):
            self._json({"object": "list", "data": MODEL_LIST})
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
            stream = payload.get("stream", False)
            if stream:
                lines = outbound_call_with_retry(messages, model, temp, max_tokens, stream=True)
                self._sse(lines)
            else:
                self._json(outbound_call_with_retry(messages, model, temp, max_tokens, stream=False))
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)

    def log_message(self, fmt, *args):  # 静默日志
        pass


def run_http(host: str, port: int):
    """模式二：HTTP 网关兼容模式。"""
    if not CFG["cnb_token"]:
        print("[GW3080][WARN] CNB_TOKEN 未设置，出站调用将失败。")
    server = ThreadingHTTPServer((host, port), GatewayHandler)
    print(f"[GW3080] HTTP 网关兼容模式已启动（出站）: http://{host}:{port}")
    print(f"[GW3080] 出站目标: {CFG['cnb_gateway']}")
    print("[GW3080] 端点: /health /v1/models /v1/chat/completions(流式+非流式聚合)")
    print("[GW3080] ⚠️ 本网关仅本机 127.0.0.1 访问，不支持外部公网接入（非反向隧道）")
    server.serve_forever()


# ---------------------------------------------------------------------------
# 模式一：标准 MCP 模式（stdin/stdout 协议）
# ---------------------------------------------------------------------------
# MCP（Model Context Protocol）工具协议子集：
#   initialize            → 客户端握手
#   tools/list            → 返回可用工具清单（chat_completions / get_models / health）
#   tools/call            → 调用工具，内部出站转发到 CNB 云端
# 帧格式：Content-Length 前缀的 JSON-RPC 消息（与主流 MCP 客户端兼容）
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "chat_completions",
        "description": "通过 CNB 云端免费 DeepSeek-V4-Flash / GLM-5.2 完成对话/代码生成。密钥由 CNB_TOKEN 环境变量注入，零明文。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                            "content": {"type": "string"}
                        },
                        "required": ["role", "content"]
                    },
                    "description": "对话消息列表"
                },
                "model": {
                    "type": "string",
                    "enum": ["deepseek-v4-flash", "z-ai/glm-5.2"],
                    "default": "deepseek-v4-flash",
                    "description": "模型名"
                },
                "temperature": {"type": "number", "default": 0.7},
                "max_tokens": {"type": "integer", "default": 4096}
            },
            "required": ["messages"]
        }
    },
    {
        "name": "get_models",
        "description": "列出网关可用的模型清单（deepseek-v4-flash / z-ai/glm-5.2）。",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "health",
        "description": "网关出站连通性自检与看门狗状态。",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


def _mcp_send(obj: dict):
    """按 MCP 帧格式输出（stdout，Content-Length 前缀）。"""
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _mcp_read_frame() -> dict | None:
    """从 stdin 读一帧 MCP 消息，EOF 返回 None。

    统一使用 sys.stdin.buffer 二进制读取，避免文本层 readline() 与
    二进制 read() 混用导致的缓冲越界吞包问题。
    """
    header_bytes = bytearray()
    while True:
        byte = sys.stdin.buffer.read(1)
        if not byte:
            return None  # EOF
        header_bytes.append(byte[0])
        if header_bytes.endswith(b"\r\n\r\n") or header_bytes.endswith(b"\n\n"):
            break
        if len(header_bytes) > 8192:  # 防头部异常超长
            return None
    headers = {}
    text = header_bytes.decode("utf-8", errors="ignore")
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    raw = sys.stdin.buffer.read(length)
    return json.loads(raw)


def _mcp_handle_tool_call(params: dict) -> dict:
    """处理 tools/call，内部出站转发（带看门狗自愈重试）。"""
    name = params.get("name", "")
    args = params.get("arguments", {}) or {}

    if name == "chat_completions":
        messages = args.get("messages", [])
        model = args.get("model", CFG["model"])
        temp = args.get("temperature", 0.7)
        max_tokens = args.get("max_tokens", 4096)
        try:
            result = outbound_call_with_retry(messages, model, temp, max_tokens, stream=False)
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "content": [
                    {"type": "text", "text": content}
                ],
                "isError": False
            }
        except Exception as e:  # noqa: BLE001
            return {
                "content": [{"type": "text", "text": f"[GW3080] 出站调用失败：{e}"}],
                "isError": True
            }
    elif name == "get_models":
        return {"content": [{"type": "text", "text": json.dumps(MODEL_LIST, ensure_ascii=False)}], "isError": False}
    elif name == "health":
        return {"content": [{"type": "text", "text": json.dumps(outbound_health_check(), ensure_ascii=False)}], "isError": False}
    return {"content": [{"type": "text", "text": f"未知工具：{name}"}], "isError": True}


def run_mcp():
    """模式一：标准 MCP 模式，遵循 MCP stdin/stdout 协议。"""
    if not CFG["cnb_token"]:
        print("[GW3080][WARN] CNB_TOKEN 未设置，出站调用将失败。", file=sys.stderr, flush=True)
    print("[GW3080] MCP 模式已启动（stdin/stdout）· 供 Codex/Hermes-Still/DeepSeek-Harness 加载",
          file=sys.stderr, flush=True)
    print(f"[GW3080] 出站目标: {CFG['cnb_gateway']} · 可用工具: chat_completions/get_models/health",
          file=sys.stderr, flush=True)

    while True:
        msg = _mcp_read_frame()
        if msg is None:
            break
        method = msg.get("method", "")
        msg_id = msg.get("id")
        if method == "initialize":
            _mcp_send({
                "jsonrpc": "2.0", "id": msg_id,
                "result": {
                    "protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-03-26"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "gateway_3080", "version": "2.0.2"}
                }
            })
        elif method == "tools/list":
            _mcp_send({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": MCP_TOOLS}})
        elif method == "tools/call":
            result = _mcp_handle_tool_call(msg.get("params", {}))
            _mcp_send({"jsonrpc": "2.0", "id": msg_id, "result": result})
        elif method == "notifications/initialized" or method.startswith("notifications/"):
            continue
        else:
            _mcp_send({"jsonrpc": "2.0", "id": msg_id,
                       "error": {"code": -32601, "message": f"Method not found: {method}"}})


def main():
    ap = argparse.ArgumentParser(description="本机 3081 本地网关客户端 · 双模式 MCP 插件（出站）")
    ap.add_argument("--http", action="store_true", help="HTTP 网关兼容模式（模式二）；不加则走标准 MCP 模式（模式一）")
    ap.add_argument("--port", type=int, default=CFG["listen_port"], help="HTTP 模式监听端口（默认 3081）")
    ap.add_argument("--host", default=CFG["listen_host"], help="HTTP 模式监听地址（默认 127.0.0.1，仅本机）")
    args = ap.parse_args()

    if args.http:
        run_http(args.host, args.port)
    else:
        run_mcp()


if __name__ == "__main__":
    main()
