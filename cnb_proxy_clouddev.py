"""
CNB CloudDev Proxy v1.0 — 部署在 CNB 云原生开发环境内
利用 CloudDev 自带的 CNB_TOKEN（流水线令牌）透传到 CNB AI 网关，
本地 Hermes Studio 通过 CNB Tunnel 指向本代理，零成本享用云端 DeepSeek V4 Flash。

启动方式:
  python cnb_proxy_clouddev.py --port 8080

Hermes Studio 配置:
  custom_providers:
    - name: cnb-clouddev-proxy
      base_url: https://{clouddev_id}-8080.cnb.run/v1
      api_key: placeholder (CNB_TOKEN 在 CloudDev 侧，本地随便填)
      api_mode: chat_completions
      model: deepseek-v4-flash
"""

import http.server
import json
import os
import sys
import urllib.request
import urllib.error
import argparse

CNB_GATEWAY = "https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions"
CNB_TOKEN = os.getenv("CNB_TOKEN", "")

if not CNB_TOKEN:
    print("[ERROR] CNB_TOKEN 环境变量未设置！请在 CloudDev 环境中运行本脚本。")
    sys.exit(1)

# ------ 可用模型白名单 ------
AVAILABLE_MODELS = {
    "deepseek-v4-flash": "DeepSeek V4 Flash (CNB Free)",
    "deepseek-r1": "DeepSeek R1 (CNB Free)",
    "qwen3-235b-a22b": "Qwen3 235B (CNB Free)",
}

print(f"[CNB Proxy] 启动在端口 {sys.argv[-1] if '--port' in sys.argv else '8080'}")
print(f"[CNB Proxy] CNB Token 前缀: {CNB_TOKEN[:12]}...")
print(f"[CNB Proxy] 网关地址: {CNB_GATEWAY}")
print(f"[CNB Proxy] 可用模型: {list(AVAILABLE_MODELS.keys())}")


class CNBProxyHandler(http.server.BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/v1/models":
            models_list = [
                {"id": k, "object": "model", "owned_by": "cnb"} for k in AVAILABLE_MODELS
            ]
            self._send_json({"object": "list", "data": models_list})
        elif self.path == "/health":
            self._send_json({"status": "ok", "token_prefix": CNB_TOKEN[:12]})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path in ("/v1/chat/completions", "/chat/completions"):
            self._handle_chat()
        else:
            self._send_json({"error": f"unknown endpoint: {self.path}"}, 404)

    def _handle_chat(self):
        try:
            body = self._read_body()
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, 400)
            return

        model = payload.get("model", "deepseek-v4-flash")
        if model not in AVAILABLE_MODELS:
            self._send_json({
                "error": f"模型 '{model}' 不可用，可选: {list(AVAILABLE_MODELS.keys())}"
            }, 400)
            return

        print(f"[CNB Proxy] → {model} ({len(payload.get('messages', []))} msgs)")

        cnb_payload = {
            "model": model,
            "messages": payload.get("messages", []),
            "stream": False,
            "temperature": payload.get("temperature", 0.7),
            "max_tokens": payload.get("max_tokens", 4096),
        }

        req = urllib.request.Request(
            CNB_GATEWAY,
            data=json.dumps(cnb_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CNB_TOKEN}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                print(f"[CNB Proxy] ← {model} OK ({resp.status})")
                self._send_json(result, resp.status)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print(f"[CNB Proxy] ← HTTP {e.code}: {error_body[:200]}")
            self._send_json({
                "error": f"CNB 网关返回 HTTP {e.code}",
                "detail": error_body[:500],
            }, e.code)
        except Exception as e:
            print(f"[CNB Proxy] ← 网络错误: {e}")
            self._send_json({"error": str(e)}, 502)

    def log_message(self, format, *args):
        pass  # 静默日志


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = http.server.HTTPServer((args.host, args.port), CNBProxyHandler)
    print(f"[CNB Proxy] 监听 {args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
