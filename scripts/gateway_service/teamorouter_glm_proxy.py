import json
import os
import time
import uuid
import urllib.error
import urllib.request

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TEAMO_BASE = os.environ.get("TEAMOROUTER_BASE", "https://teamorouter.cn/v1")
TEAMO_KEY = os.environ.get("TEAMOROUTER_API_KEY", "")
PORT = int(os.environ.get("GLM_PROXY_PORT", "51428"))
LOG_PATH = os.environ.get("GLM_PROXY_LOG", os.path.join(os.path.dirname(os.path.abspath(__file__)), "teamorouter_glm_proxy.log"))

# GLM models only speak Chat Completions. Everything else is passed through as Responses.
CHAT_MODELS = {"glm-5.2", "glm-5.3", "glm-5.3-flash", "glm-5.3-flash-free"}


def log(entry):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def input_to_messages(inp):
    if isinstance(inp, str):
        return [{"role": "user", "content": inp}]
    messages = []
    for item in inp if isinstance(inp, list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("type") in ("function_call", "function_call_output", "reasoning"):
            continue
        role = item.get("role", "user")
        content = item.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text") or part.get("input_text") or part.get("output_text")
                    if text:
                        parts.append(text)
            text = "".join(parts)
        else:
            text = ""
        if text:
            messages.append({"role": role, "content": text})
    return messages


def call_chat(model, payload):
    body = {
        "model": model,
        "messages": input_to_messages(payload.get("input")),
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        TEAMO_BASE + "/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": "Bearer " + TEAMO_KEY,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_responses(model, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TEAMO_BASE + "/responses",
        data=data,
        method="POST",
        headers={
            "Authorization": "Bearer " + TEAMO_KEY,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat_to_response(model, chat):
    text = ""
    usage = chat.get("usage", {})
    choices = chat.get("choices") or []
    if choices:
        message = choices[0].get("message") or {}
        text = message.get("content") or ""
    return {
        "id": "resp_" + uuid.uuid4().hex,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model,
        "output": [
            {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}
        ],
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self.send_json({"object": "list", "data": [{"id": m, "object": "model"} for m in sorted(CHAT_MODELS)]})
            return
        self.send_json({"error": {"message": "not found"}}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self.send_json({"error": {"message": "bad json: %s" % exc}}, 400)
            return

        model = payload.get("model", "")
        try:
            if model in CHAT_MODELS:
                chat = call_chat(model, payload)
                result = chat_to_response(model, chat)
            else:
                result = call_responses(model, payload)
            log({"model": model, "path": self.path, "status": 200, "ts": int(time.time() * 1000)})
            self.send_json(result)
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", "replace")
            log({"model": model, "path": self.path, "status": exc.code, "error": err, "ts": int(time.time() * 1000)})
            self.send_json({"error": {"message": err, "type": "upstream_error", "code": exc.code}}, exc.code)
        except Exception as exc:
            log({"model": model, "path": self.path, "status": 500, "error": str(exc), "ts": int(time.time() * 1000)})
            self.send_json({"error": {"message": str(exc), "type": "proxy_error", "code": 500}}, 500)


if __name__ == "__main__":
    if not TEAMO_KEY:
        raise SystemExit("TEAMOROUTER_API_KEY is not set")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("teamo-glm-proxy listening on http://127.0.0.1:%d" % PORT, flush=True)
    server.serve_forever()
