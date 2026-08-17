#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harness_mcp_loader.py · DeepSeek Harness MCP 统一加载器
=================================================================
「一切皆插件」核心落地：读取 harness_mcp_registry.json，按需 spawn/kill
MCP 子进程（进程级沙箱，替代 Docker-in-Docker），基座 harness_proxy.py /
harness_agent.py 固定不动，能力全部靠本加载器按注册中心热插拔。

双模式 MCP 插件（gateway_3080）支持：
  - 模式一 标准 MCP（stdin/stdout）：loader 拉起子进程，通过 MCP 协议调用
    chat_completions / get_models / health，内部出站转发到 CNB 免费模型。
  - 模式二 HTTP 兼容（--http --port 3080）：loader 拉起 HTTP 网关子进程，
    供表单 base_url=http://127.0.0.1:3080 的老工具调用。

密钥零落盘：仅读环境变量 CNB_TOKEN，注册中心不存明文。
=================================================================
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.environ.get(
    "HARNESS_MCP_REGISTRY",
    os.path.join(BASE_DIR, "config", "harness_mcp_registry.json"),
)


def load_registry() -> dict:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_env(env_map: dict) -> dict:
    """解析 ${env:XXX} 与 ${VAR:-default} 占位符，仅环境变量注入，零明文。"""
    out = {}
    for k, v in (env_map or {}).items():
        if isinstance(v, str):
            if v.startswith("${env:") and v.endswith("}"):
                out[k] = os.environ.get(v[6:-1], "")
            elif "${" in v and ":-" in v:
                # ${VAR:-default}
                inner = v[v.find("${") + 2: v.rfind("}")]
                name, _, default = inner.partition(":-")
                out[k] = os.environ.get(name, default)
            else:
                out[k] = v
        else:
            out[k] = v
    return out


class Gateway3080Client:
    """gateway_3080 双模式 MCP 插件客户端。

    以子进程方式拉起插件，支持两种调用通道：
      - MCP 模式：向子进程 stdin 写 MCP 帧（Content-Length 前缀 JSON-RPC），
        从 stdout 读回结果，调用 chat_completions / get_models / health。
      - HTTP 模式：直接请求 127.0.0.1:{port}/v1 的 OpenAI 兼容接口。
    """

    def __init__(self, service_cfg: dict, registry: dict):
        self.name = "gateway_3080"
        self.cfg = service_cfg
        self.globals = registry.get("globals", {})
        self.mode = os.environ.get("GW_MODE", "mcp")  # mcp | http
        self.port = int(os.environ.get("GW_PORT", self.globals.get("gw_http_port", 3080)))
        self.proc = None
        self.env = _resolve_env(self.cfg.get("env", {}))

    # ---- 启动 ----
    def spawn(self) -> bool:
        if self.proc and self.proc.poll() is None:
            return True
        plugin_path = os.path.join(BASE_DIR, "plugins", "gateway_3080", "gateway_3080.py")
        if not os.path.exists(plugin_path):
            # 回退到 deploy/dsh-desktop/gateway_3080.py
            alt = os.path.join(
                os.path.dirname(BASE_DIR), "deploy", "dsh-desktop", "gateway_3080.py"
            )
            if os.path.exists(alt):
                plugin_path = alt
            else:
                print(f"[mcp-loader] ❌ gateway_3080.py 未找到（{plugin_path} / {alt}）",
                      file=sys.stderr, flush=True)
                return False

        cmd = [sys.executable, plugin_path]
        if self.mode == "http":
            cmd += ["--http", "--port", str(self.port)]

        env = dict(os.environ)
        env.update({k: v for k, v in self.env.items() if v})
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[mcp-loader] ❌ 启动 gateway_3080 失败：{e}", file=sys.stderr, flush=True)
            return False
        print(f"[mcp-loader] ✅ gateway_3080 已启动（mode={self.mode}, pid={self.proc.pid}）",
              file=sys.stderr, flush=True)
        return True

    def kill(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.send_signal(signal.SIGTERM)
                self.proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                self.proc.kill()
        self.proc = None

    # ---- MCP 协议调用 ----
    def _mcp_send(self, obj: dict):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8"))
        self.proc.stdin.write(body)
        self.proc.stdin.flush()

    def _mcp_read(self) -> dict | None:
        header = b""
        while True:
            b = self.proc.stdout.read(1)
            if not b:
                return None
            header += b
            if header.endswith(b"\r\n\r\n") or header.endswith(b"\n\n"):
                break
            if len(header) > 8192:
                return None
        length = 0
        for line in header.decode("utf-8", "ignore").splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                if k.strip().lower() == "content-length":
                    length = int(v.strip())
        raw = self.proc.stdout.read(length)
        return json.loads(raw)

    def mcp_call(self, tool: str, arguments: dict | None = None, timeout: float = 120) -> dict:
        if not self.spawn():
            return {"content": [{"type": "text", "text": "gateway_3080 未启动"}], "isError": True}
        self._mcp_send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-03-26"}})
        self._mcp_read()  # initialize response
        self._mcp_send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": tool, "arguments": arguments or {}}})
        resp = self._mcp_read()
        if resp and "result" in resp:
            return resp["result"]
        return {"content": [{"type": "text", "text": json.dumps(resp, ensure_ascii=False)}],
                "isError": bool(resp and "error" in resp)}

    # ---- 端口就绪等待（看门狗） ----
    def _wait_http_ready(self, timeout: float = 15) -> bool:
        import socket
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc and self.proc.poll() is not None:
                return False
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=1):
                    return True
            except OSError:
                time.sleep(0.5)
        return False

    # ---- HTTP 模式调用 ----
    def http_call(self, tool: str, arguments: dict | None = None, timeout: float = 120) -> dict:
        import urllib.request

        if not self.spawn():
            return {"content": [{"type": "text", "text": "gateway_3080 未启动"}], "isError": True}
        if not self._wait_http_ready():
            return {"content": [{"type": "text", "text": "gateway_3080 HTTP 端口未就绪"}], "isError": True}
        base = f"http://127.0.0.1:{self.port}"
        if tool == "health":
            url = f"{base}/health"
            req = urllib.request.Request(url)
        elif tool == "get_models":
            url = f"{base}/v1/models"
            req = urllib.request.Request(url)
        elif tool == "chat_completions":
            url = f"{base}/v1/chat/completions"
            args = arguments or {}
            body = json.dumps({
                "model": args.get("model", self.env.get("CNB_MODEL", "deepseek-v4-flash")),
                "messages": args.get("messages", []),
                "stream": False,
                "temperature": args.get("temperature", 0.7),
                "max_tokens": args.get("max_tokens", 4096),
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        else:
            return {"content": [{"type": "text", "text": f"未知工具 {tool}"}], "isError": True}
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "") \
                    if tool == "chat_completions" else json.dumps(data, ensure_ascii=False)
                return {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:  # noqa: BLE001
            return {"content": [{"type": "text", "text": f"[GW3080] 调用失败：{e}"}], "isError": True}

    def call(self, tool: str, arguments: dict | None = None, timeout: float = 120) -> dict:
        return self.mcp_call(tool, arguments, timeout) if self.mode == "mcp" \
            else self.http_call(tool, arguments, timeout)


class McpLoader:
    """MCP 统一加载器：按注册中心 spawn/kill 服务，按名称调用工具。"""

    def __init__(self):
        self.registry = load_registry()
        self.services = self.registry.get("services", {})
        self.matrix = {m["service"]: m for m in self.registry.get("spawn_kill_matrix", {}).get("matrix", [])}
        self._procs: dict[str, Gateway3080Client] = {}

    def spawn_service(self, name: str) -> Gateway3080Client | None:
        cfg = self.services.get(name)
        if not cfg or not cfg.get("enabled", False):
            return None
        client = Gateway3080Client(cfg, self.registry)
        if client.spawn():
            self._procs[name] = client
            return client
        return None

    def ensure_gateway(self) -> Gateway3080Client:
        if "gateway_3080_mcp" not in self._procs:
            client = self.spawn_service("gateway_3080_mcp")
            if client is None:
                # 直接手动构造
                cfg = self.services.get("gateway_3080_mcp")
                client = Gateway3080Client(cfg, self.registry)
                client.spawn()
                self._procs["gateway_3080_mcp"] = client
        return self._procs["gateway_3080_mcp"]

    def gateway_call(self, tool: str, arguments: dict | None = None) -> dict:
        gw = self.ensure_gateway()
        return gw.call(tool, arguments)

    def kill_all(self):
        for c in self._procs.values():
            c.kill()
        self._procs.clear()


def main():
    ap = argparse.ArgumentParser(description="DeepSeek Harness MCP 统一加载器")
    ap.add_argument("--call", nargs="+", help="调用 gateway_3080 MCP 工具: <tool> [json_args]")
    ap.add_argument("--tool", default="health", help="要调用的工具（默认 health）")
    ap.add_argument("--args", default="{}", help="工具参数 JSON")
    ap.add_argument("--mode", default="mcp", choices=["mcp", "http"], help="插件模式")
    ap.add_argument("--spawn", action="store_true", help="仅启动 gateway_3080 并退出")
    ap.add_argument("--kill", action="store_true", help="停止已启动的 gateway_3080")
    args = ap.parse_args()

    os.environ.setdefault("GW_MODE", args.mode)
    loader = McpLoader()

    if args.kill:
        loader.kill_all()
        print("[mcp-loader] 已停止全部 MCP 插件")
        return 0

    if args.spawn:
        gw = loader.spawn_service("gateway_3080_mcp")
        print(f"[mcp-loader] gateway_3080 {'已启动' if gw else '启动失败'}（mode={args.mode}）")
        return 0

    if args.call:
        for tool in args.call:
            pass
        tool = args.call[0]
        jargs = args.call[1] if len(args.call) > 1 else args.args
        try:
            arguments = json.loads(jargs)
        except Exception:
            arguments = {}
        result = loader.gateway_call(tool, arguments)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        loader.kill_all()
        return 0

    # 默认：health
    result = loader.gateway_call(args.tool, json.loads(args.args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    loader.kill_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
