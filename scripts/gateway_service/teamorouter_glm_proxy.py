#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TeamoRouter GLM 福利版本地代理桥（127.0.0.1:51428）

作用：
1. /v1/models 返回 glm-5.3-flash-free，让 Codex 桌面端下拉框能显示福利版；
2. /v1/chat/completions 透传到 https://teamorouter.cn/v1，密钥走环境变量 TEAMOROUTER_API_KEY；
3. 零明文密钥，仅手动按需启动（禁止开机自启，防静默消耗配额）。
"""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "https://teamorouter.cn"
MODELS_PAYLOAD = {
    "object": "list",
    "data": [
        {"id": "glm-5.3-flash-free", "object": "model", "owned_by": "teamorouter",
         "display_name": "GLM-5.3-Flash 福利版 0.01折"},
        {"id": "glm-5.3-flash", "object": "model", "owned_by": "zhipu"},
    ],
}


class Handler(BaseHTTPRequestHandler):
    def _key(self):
        return os.environ.get("TEAMOROUTER_API_KEY", "")

    def do_GET(self):
        if self.path.split("?")[0] in ("/v1/models", "/models"):
            body = json.dumps(MODELS_PAYLOAD).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path not in ("/v1/chat/completions", "/chat/completions"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        key = self._key()
        if not key:
            self.send_error(500, "TEAMOROUTER_API_KEY 未设置")
            return
        req = urllib.request.Request(
            UPSTREAM + path, data=payload,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                     "X-Teamo-Route-Tag": "play0.019"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read()
                self.send_response(r.status)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    print("TeamoRouter GLM 代理桥就绪: http://127.0.0.1:51428/v1")
    ThreadingHTTPServer(("127.0.0.1", 51428), Handler).serve_forever()
