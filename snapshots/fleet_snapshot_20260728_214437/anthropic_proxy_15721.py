"""
Anthropic → OpenAI 协议转换代理 (端口 15721)
用途：让 Claude Code 通过 MiMo v2.5 Pro API 运行
后端：https://token-plan-cn.xiaomimimo.com

支持的端点：
  - /v1/messages (Anthropic Messages API)
  - /v1/responses (OpenAI Responses API)
  - /v1/chat/completions (直通)

启动：python anthropic_proxy_15721.py [--port 15721] [--api-key KEY]
"""
import json
import sys
import os
import re
import argparse
import ssl
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPSConnection
from urllib.parse import urlparse
from datetime import datetime

PORT = 15721
UPSTREAM = "token-plan-cn.xiaomimimo.com"
UPSTREAM_PORT = 443

def load_api_key():
    """从 Codex config.toml 读取 API Key"""
    for p in [r"E:\龙虾AI主控中心\Codex\.codex\config.toml",
              os.path.expanduser("~/.codex/config.toml")]:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        m = re.match(r'OPENAI_API_KEY\s*=\s*"([^"]+)"', line.strip())
                        if m:
                            return m.group(1)
            except Exception:
                pass
    return os.environ.get("MIMO_API_KEY", "")

def log(level, msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def anthropic_to_openai(body):
    """Anthropic Messages → OpenAI Chat Completions 转换"""
    messages = []
    system = body.get("system", "")
    if system:
        messages.append({"role": "system", "content": system})

    for msg in body.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        # 处理 content 为数组的情况（Anthropic 格式）
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = "\n".join(text_parts)
        messages.append({"role": role, "content": content})

    openai_body = {
        "model": body.get("model", "mimo-v2.5-pro"),
        "messages": messages,
        "max_tokens": body.get("max_tokens", 4096),
        "stream": body.get("stream", False),
    }
    if "temperature" in body:
        openai_body["temperature"] = body["temperature"]
    if "top_p" in body:
        openai_body["top_p"] = body["top_p"]

    return openai_body

def openai_to_anthropic(openai_resp, model="mimo-v2.5-pro"):
    """OpenAI Chat Completions → Anthropic Messages 转换"""
    if "choices" in openai_resp and len(openai_resp["choices"]) > 0:
        choice = openai_resp["choices"][0]
        content = choice.get("message", {}).get("content", "")
        finish = choice.get("finish_reason", "end_turn")
        stop_reason = "end_turn" if finish == "stop" else ("max_tokens" if finish == "length" else finish)
        return {
            "id": openai_resp.get("id", "msg_0000"),
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": content}],
            "model": model,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": openai_resp.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": openai_resp.get("usage", {}).get("completion_tokens", 0),
            }
        }
    return {"type": "error", "error": {"type": "api_error", "message": "No choices in response"}}

def forward_to_upstream(path, body_bytes, api_key, stream=False):
    """转发请求到 MiMo API"""
    ctx = ssl.create_default_context()
    conn = HTTPSConnection(UPSTREAM, UPSTREAM_PORT, context=ctx, timeout=120)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    try:
        conn.request("POST", path, body=body_bytes, headers=headers)
        resp = conn.getresponse()
        return resp
    except Exception as e:
        log("ERROR", f"Upstream error: {e}")
        return None

class ProxyHandler(BaseHTTPRequestHandler):
    api_key = ""

    def log_message(self, format, *args):
        log("INFO", f"{self.client_address[0]} - {format % args}")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        path = self.path.split("?")[0]
        stream = body.get("stream", False)

        # === /v1/messages (Anthropic 格式) ===
        if path == "/v1/messages":
            log("INFO", f"Anthropic Messages API: model={body.get('model', '?')} stream={stream}")
            openai_body = anthropic_to_openai(body)
            openai_body["model"] = "mimo-v2.5-pro"  # 强制使用 MiMo
            openai_bytes = json.dumps(openai_body).encode("utf-8")

            resp = forward_to_upstream("/v1/chat/completions", openai_bytes, self.api_key, stream)
            if resp is None:
                self.send_error(502, "Upstream unavailable")
                return

            if stream:
                self._handle_stream_response(resp, body.get("model", "mimo-v2.5-pro"))
            else:
                resp_body = resp.read()
                try:
                    openai_resp = json.loads(resp_body)
                    anthropic_resp = openai_to_anthropic(openai_resp, body.get("model", "mimo-v2.5-pro"))
                except Exception as e:
                    log("ERROR", f"Response parse error: {e}")
                    anthropic_resp = {"type": "error", "error": {"type": "api_error", "message": str(e)}}

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                resp_bytes = json.dumps(anthropic_resp).encode("utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
            return

        # === /v1/responses (OpenAI Responses API → Chat Completions) ===
        if path == "/v1/responses":
            log("INFO", f"Responses API: model={body.get('model', '?')} stream={stream}")
            # 转换为 chat/completions
            openai_body = {
                "model": "mimo-v2.5-pro",
                "messages": [],
                "stream": stream,
            }
            # 从 input 提取消息
            inp = body.get("input", "")
            if isinstance(inp, str):
                openai_body["messages"].append({"role": "user", "content": inp})
            elif isinstance(inp, list):
                for item in inp:
                    if isinstance(item, dict):
                        role = item.get("role", "user")
                        content = item.get("content", item.get("text", str(item)))
                        openai_body["messages"].append({"role": role, "content": str(content)})
                    else:
                        openai_body["messages"].append({"role": "user", "content": str(item)})

            if "max_output_tokens" in body:
                openai_body["max_tokens"] = body["max_output_tokens"]

            openai_bytes = json.dumps(openai_body).encode("utf-8")
            resp = forward_to_upstream("/v1/chat/completions", openai_bytes, self.api_key, stream)
            if resp is None:
                self.send_error(502, "Upstream unavailable")
                return

            if stream:
                self._handle_stream_response(resp, "mimo-v2.5-pro")
            else:
                resp_body = resp.read()
                try:
                    openai_resp = json.loads(resp_body)
                    # 转换为 Responses API 格式
                    content = ""
                    if "choices" in openai_resp and len(openai_resp["choices"]) > 0:
                        content = openai_resp["choices"][0].get("message", {}).get("content", "")
                    responses_resp = {
                        "id": openai_resp.get("id", "resp_0000"),
                        "object": "response",
                        "model": "mimo-v2.5-pro",
                        "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": content}]}],
                        "usage": openai_resp.get("usage", {}),
                    }
                except Exception as e:
                    log("ERROR", f"Response parse error: {e}")
                    responses_resp = {"error": {"message": str(e)}}

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                resp_bytes = json.dumps(responses_resp).encode("utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
            return

        # === /v1/chat/completions (直通) ===
        if path == "/v1/chat/completions":
            body["model"] = "mimo-v2.5-pro"
            openai_bytes = json.dumps(body).encode("utf-8")
            resp = forward_to_upstream("/v1/chat/completions", openai_bytes, self.api_key, stream)
            if resp is None:
                self.send_error(502, "Upstream unavailable")
                return

            if stream:
                self._handle_stream_response(resp, "mimo-v2.5-pro")
            else:
                resp_body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
            return

        # === 其他路径 ===
        self.send_error(404, f"Unknown endpoint: {path}")

    def _handle_stream_response(self, resp, model):
        """处理流式响应"""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            buffer = ""
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            self.wfile.write(b"data: [DONE]\n\n")
                            self.wfile.flush()
                            break
                        try:
                            openai_chunk = json.loads(data_str)
                            # 转为 Anthropic 流式格式
                            delta = openai_chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                anthropic_event = {
                                    "type": "content_block_delta",
                                    "index": 0,
                                    "delta": {"type": "text_delta", "text": content}
                                }
                                self.wfile.write(f"data: {json.dumps(anthropic_event)}\n\n".encode("utf-8"))
                                self.wfile.flush()
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            log("ERROR", f"Stream error: {e}")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            body = json.dumps({"status": "ok", "port": PORT, "upstream": UPSTREAM}).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key, anthropic-version")
        self.send_header("Content-Length", "0")
        self.end_headers()

def main():
    global PORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=15721)
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()

    PORT = args.port
    api_key = args.api_key or load_api_key()
    if not api_key:
        log("ERROR", "无 API Key！设置 --api-key 或在 config.toml 中配置 OPENAI_API_KEY")
        sys.exit(1)

    ProxyHandler.api_key = api_key

    log("INFO", "=" * 60)
    log("INFO", "Anthropic → OpenAI 协议转换代理")
    log("INFO", f"监听: http://127.0.0.1:{PORT}")
    log("INFO", f"后端: https://{UPSTREAM}")
    log("INFO", f"端点: /v1/messages → /v1/chat/completions")
    log("INFO", f"API Key: {'*' * 8}...{api_key[-4:]}")
    log("INFO", "=" * 60)

    server = HTTPServer(("127.0.0.1", PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("INFO", "代理已停止")
        server.server_close()

if __name__ == "__main__":
    main()
