#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude-Code → CNB 内置 DeepSeek-V4-Flash 接口适配层
=====================================================
核心职责：
  1. 拦截 Claude-Code 原生发送给 Anthropic 的 /v1/messages 请求
  2. 改写 ANTHROPIC_BASE_URL 指向 CNB 平台内置 AI 网关（免费配额）
  3. 将 Anthropic Messages 协议转译为 OpenAI Chat Completions 协议
  4. 强制绑定模型 deepseek-v4-flash（CNB 免费基座）
  5. 密钥不落盘：全部从环境变量注入（CNB 流水线环境变量），严禁明文提交 git

设计约束（龙虾五步法 Step3）：
  - 不调用外部付费 API（无 api.deepseek.com / api.anthropic.com 明文）
  - 不触发本地 Ollama 下载模型，全部在 CNB 云端容器内运行
  - 支持额度监控降级：读取环境变量 QUOTA_LIMIT/QUOTA_USED，超限自动降级

环境变量：
  ANTHROPIC_BASE_URL   Claude-Code 客户端侧指向本适配层的地址（默认 http://127.0.0.1:8787）
  CNB_AI_GATEWAY       CNB 内置 AI 网关地址（默认从 ACC_PRODUCT_CONFIG_V2 自动解析，
                       也可显式注入 https://api.cnb.cool/<org>/<repo>/-/ai-ide）
  CNB_MODEL            强制模型名，默认 deepseek-v4-flash
  REASONING_EFFORT     推理强度档位：low / high / max，默认 high
  QUOTA_LIMIT          免费额度上限（条数或核时，用于降级判定）
  QUOTA_USED           当前已用额度（由 quota_monitor.py 写入）
  任意 Key 均不写死在代码中，全部来自流水线 env / imports。
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 配置（全部环境变量注入，杜绝硬编码）
# ---------------------------------------------------------------------------

def _resolve_gateway() -> str:
    """优先使用显式注入的 CNB_AI_GATEWAY，否则从 ACC_PRODUCT_CONFIG_V2 自动解析。
    最终拼接为 CNB 内置 AI 网关的 chat/completions 端点。
    """
    slug = os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan")
    explicit = os.environ.get("CNB_AI_GATEWAY", "").strip()
    if explicit:
        base = explicit.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"
    raw = os.environ.get("ACC_PRODUCT_CONFIG_V2", "")
    if raw:
        try:
            cfg = json.loads(raw)
            ep = cfg.get("endpoint", "").strip().rstrip("/")
            if ep:
                # endpoint 形如 https://api.cnb.cool/<slug>/-/ai-ide → 内置网关端点
                if ep.endswith("/ai-ide"):
                    return ep.replace("/ai-ide", "/ai/chat/completions")
                if ep.endswith("/chat/completions"):
                    return ep
                return f"{ep}/chat/completions"
        except Exception:
            pass
    # 兜底：从仓库 slug 推断
    return f"https://api.cnb.cool/{slug}/-/ai/chat/completions"


CFG = {
    # Claude-Code 客户端请求统一打到本适配层
    "listen_host": os.environ.get("ADAPTER_HOST", "127.0.0.1"),
    "listen_port": int(os.environ.get("ADAPTER_PORT", "8787")),
    # CNB 内置 AI 网关（免费 DeepSeek-V4-Flash）
    "cnb_gateway": _resolve_gateway(),
    # 强制模型：CNB 免费 DeepSeek-V4-Flash
    "model": os.environ.get("CNB_MODEL", "deepseek-v4-flash"),
    # 推理强度档位 low / high / max
    "reasoning_effort": os.environ.get("REASONING_EFFORT", "high"),
    # 从 CNB_TOKEN（流水线注入）或 ACC_PRODUCT_CONFIG_V2 读取内置网关鉴权
    "cnb_token": os.environ.get("CNB_TOKEN", ""),
    # 降级保护阈值
    "quota_limit": float(os.environ.get("QUOTA_LIMIT", "0") or 0),
    "quota_used": float(os.environ.get("QUOTA_USED", "0") or 0),
}

# 若 ACC_PRODUCT_CONFIG_V2 存在且带 token，优先取其 token（适配层鉴权凭据，不落盘）
try:
    raw_cfg = json.loads(os.environ.get("ACC_PRODUCT_CONFIG_V2", "{}"))
    attrs = raw_cfg.get("authentication", {}).get("attributes", {})
    token = attrs.get("token", "")
    if token:
        CFG["cnb_token"] = token
except Exception:
    pass


# ---------------------------------------------------------------------------
# 协议转换：Anthropic Messages → OpenAI Chat Completions
# ---------------------------------------------------------------------------

def anthropic_to_openai(body: Dict[str, Any]) -> Dict[str, Any]:
    """将 Anthropic /v1/messages 请求体转换为 OpenAI /chat/completions 请求体。"""
    sys_parts: List[str] = []
    messages: List[Dict[str, Any]] = []

    for block in body.get("system", []) if isinstance(body.get("system"), list) else [body.get("system")]:
        if isinstance(block, str):
            sys_parts.append(block)
        elif isinstance(block, dict):
            content = block.get("text", "")
            if content:
                sys_parts.append(content)

    for msg in body.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts = []
            for b in content:
                if isinstance(b, dict):
                    if b.get("type") == "text":
                        parts.append(b.get("text", ""))
                    elif b.get("type") == "image":
                        # 图像在纯文本网关中占位提示
                        parts.append("[image]")
                    elif b.get("type") == "tool_result":
                        parts.append(str(b.get("content", "")))
                    elif b.get("type") == "tool_use":
                        parts.append(
                            f"[tool_use:{b.get('name','')}] {json.dumps(b.get('input',{}), ensure_ascii=False)}"
                        )
                else:
                    parts.append(str(b))
            text = "\n".join(p for p in parts if p)
        else:
            text = str(content)
        messages.append({"role": role, "content": text})

    if sys_parts:
        messages.insert(0, {"role": "system", "content": "\n".join(sys_parts)})

    oai_body: Dict[str, Any] = {
        "model": CFG["model"],
        "messages": messages,
        "stream": bool(body.get("stream", False)),
        "max_tokens": body.get("max_tokens", 4096),
    }
    # 推理强度档位（网关若支持则透传，不支持会被忽略）
    if CFG["reasoning_effort"] in ("low", "high", "max"):
        oai_body["reasoning_effort"] = CFG["reasoning_effort"]
        oai_body.setdefault("extra_body", {})["reasoning_effort"] = CFG["reasoning_effort"]
    return oai_body


def openai_chunk_to_anthropic_sse(chunk: Dict[str, Any]) -> str:
    """将 OpenAI 流式 chunk 转成 Anthropic SSE 事件（event: content_block_delta / message_delta）。"""
    out: List[str] = []
    choices = chunk.get("choices", [])
    if not choices:
        return ""
    delta = choices[0].get("delta", {}) or {}
    content = delta.get("content", "")
    reasoning = delta.get("reasoning_content", "")
    finish = choices[0].get("finish_reason")

    if reasoning:
        out.append('event: content_block_delta')
        out.append('data: ' + json.dumps({
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "thinking_delta", "thinking": reasoning},
        }, ensure_ascii=False))
    if content:
        out.append('event: content_block_delta')
        out.append('data: ' + json.dumps({
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": content},
        }, ensure_ascii=False))
    if finish:
        out.append('event: message_delta')
        out.append('data: ' + json.dumps({
            "type": "message_delta",
            "delta": {"stop_reason": finish},
        }, ensure_ascii=False))
    return "\n".join(out) + "\n\n"


def openai_result_to_anthropic(oai: Dict[str, Any]) -> Dict[str, Any]:
    """将 OpenAI 非流式响应转换为 Anthropic Messages 响应。"""
    text = oai.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(text, list):
        text = "".join(x.get("text", "") for x in text if isinstance(x, dict))
    usage = oai.get("usage", {}) or {}
    return {
        "id": oai.get("id", "msg_cnb_adapter"),
        "type": "message",
        "role": "assistant",
        "model": oai.get("model", CFG["model"]),
        "content": [{"type": "text", "text": str(text)}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


# ---------------------------------------------------------------------------
# 额度监控 / 降级保护
# ---------------------------------------------------------------------------

def quota_available() -> Tuple[bool, str]:
    """检查免费额度是否可用；不可用时返回 False + 降级原因。"""
    limit = CFG["quota_limit"]
    used = CFG["quota_used"]
    if limit <= 0:
        return True, "ok"
    if used >= limit:
        return False, f"QUOTA_USED({used}) >= QUOTA_LIMIT({limit})"
    if used / limit >= 0.9:
        return True, f"WARN: quota {used}/{limit} (>=90%)"
    return True, "ok"


# ---------------------------------------------------------------------------
# HTTP Server：Anthropic 兼容端点
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _proxy(self, oai_body: Dict[str, Any], stream: bool):
        """转发到 CNB 内置网关。

        注意：CNB 内置 AI 网关仅支持流式（Non-stream 400）。因此：
        - 客户端流式请求 → 原样流式转发并转译为 Anthropic SSE
        - 客户端非流式请求 → 内部强制 stream=true 拉全量后聚合为 Anthropic 响应
        """
        ok, msg = quota_available()
        if not ok:
            # 超限降级：不调用外部付费 API，直接返回降级说明
            self._send_json(429, {
                "type": "error", "error": {
                    "type": "quota_exceeded", "message": f"CNB免费额度已用尽，触发降级保护：{msg}。请稍后重试或切换底座。"
                }
            })
            return

        # 网关仅支持流式：始终以 stream=true 请求上游
        upstream_body = dict(oai_body)
        upstream_body["stream"] = True

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CFG['cnb_token']}" if CFG["cnb_token"] else "",
        }
        req = urllib.request.Request(
            CFG["cnb_gateway"],
            data=json.dumps(upstream_body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "ignore")[:2000]
            self._send_json(e.code, {"type": "error", "error": {"type": "upstream", "message": err_body}})
            return
        except Exception as e:
            self._send_json(502, {"type": "error", "error": {"type": "upstream", "message": str(e)}})
            return

        if not stream:
            # 非流式：聚合所有 SSE chunk 为单个文本
            texts: List[str] = []
            try:
                for raw_line in resp:
                    line = raw_line.decode("utf-8", "ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except Exception:
                        continue
                    for ch in chunk.get("choices", []):
                        delta = ch.get("delta", {}) or {}
                        c = delta.get("content", "")
                        if c:
                            texts.append(c)
            except Exception as e:
                self._send_json(502, {"type": "error", "error": {"type": "upstream", "message": str(e)}})
                return
            payload = {
                "id": "msg_cnb_adapter",
                "choices": [{"message": {"content": "".join(texts)}}],
                "usage": {},
            }
            self._send_json(200, openai_result_to_anthropic(payload))
            return

        # 流式：逐行转发并转换为 Anthropic SSE
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for raw_line in resp:
                line = raw_line.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    self.wfile.write(b"event: message_stop\ndata: {}\n\n")
                    break
                try:
                    chunk = json.loads(data)
                except Exception:
                    continue
                sse = openai_chunk_to_anthropic_sse(chunk)
                if sse:
                    self.wfile.write(sse.encode("utf-8"))
                    self.wfile.flush()
        except Exception:
            pass

    def do_POST(self):
        path = self.path.split("?")[0]
        if path in ("/v1/messages", "/messages"):
            body = self._read_body()
            stream = bool(body.get("stream", False))
            try:
                oai_body = anthropic_to_openai(body)
            except Exception as e:
                self._send_json(400, {"type": "error", "error": {"type": "invalid_request", "message": str(e)}})
                return
            self._proxy(oai_body, stream)
        elif path in ("/v1/models", "/models"):
            self._send_json(200, {"data": [{"id": CFG["model"], "object": "model"}]})
        else:
            self._send_json(404, {"type": "error", "error": {"type": "not_found", "message": path}})

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/v1/models", "/models"):
            self._send_json(200, {"data": [{"id": CFG["model"], "object": "model"}]})
        elif path in ("/healthz", "/health"):
            self._send_json(200, {"status": "ok", "model": CFG["model"], "gateway": CFG["cnb_gateway"], "quota": f"{CFG['quota_used']}/{CFG['quota_limit']}"})
        else:
            self._send_json(404, {"type": "error", "error": {"type": "not_found", "message": path}})

    def log_message(self, fmt, *args):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{ts}] {fmt % args}\n")


def main():
    host, port = CFG["listen_host"], CFG["listen_port"]
    print(f"[adapter] CNB 内置 DeepSeek-V4-Flash 适配层启动")
    print(f"[adapter] listen   = http://{host}:{port}  (Claude-Code 请设置 ANTHROPIC_BASE_URL=http://{host}:{port})")
    print(f"[adapter] gateway  = {CFG['cnb_gateway']}")
    print(f"[adapter] model    = {CFG['model']} (reasoning_effort={CFG['reasoning_effort']})")
    ok, msg = quota_available()
    print(f"[adapter] quota    = {CFG['quota_used']}/{CFG['quota_limit']} -> {msg}")
    if not ok:
        print("[adapter] ⚠️ 额度已超限，将进入降级保护模式")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
