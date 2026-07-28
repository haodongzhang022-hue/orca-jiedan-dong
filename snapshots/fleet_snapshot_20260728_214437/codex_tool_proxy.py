"""
Codex MCP工具类型转换代理 v5 (完整修复版)
解决 MiMo API 不支持 Responses API 中 custom 工具类型的问题

修复内容：
- 使用流式传输(4096分片)避免大响应截断
- 完善异常捕获，统一返回500错误
- 强制关闭HTTPS连接，杜绝端口泄漏
- 支持环境变量MIMO_API_KEY和命令行--api-key
- 保留从config.toml自动读取API Key能力
"""
import json
import sys
import re
import os
import argparse
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPSConnection
from urllib.parse import urlparse

PORT = 15730
UPSTREAM = "https://token-plan-cn.xiaomimimo.com"

def load_api_key():
    """从config.toml自动读取API Key（向后兼容）"""
    for p in [r"E:\龙虾AI主控中心\Codex\.codex\config.toml",
              os.path.expanduser("~/.codex/config.toml")]:
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        if "OPENAI_API_KEY" in line:
                            m = re.search(r'"([^"]+)"', line)
                            if m:
                                return m.group(1)
            except Exception:
                pass
    return ""

def convert_tools(tools_list):
    """将type:custom工具转为type:function标准格式(Responses API扁平格式)"""
    if not tools_list:
        return tools_list, False
    new_tools = []
    changed = False
    for tool in tools_list:
        if isinstance(tool, dict) and tool.get("type") == "custom":
            changed = True
            func_def = tool.get("custom", {})
            # Responses API扁平格式：直接放在顶层，不嵌套function对象
            new_tool = {
                "type": "function",
                "name": func_def.get("name", "unknown"),
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {"type": "object", "properties": {}})
            }
            new_tools.append(new_tool)
        else:
            new_tools.append(tool)
    return new_tools, changed

class ProxyHandler(BaseHTTPRequestHandler):
    count = 0
    api_key = ""
    upstream = UPSTREAM

    def log_message(self, fmt, *args):
        # 统一日志输出，屏蔽原生冗余访问日志
        sys.stdout.write(f"[代理] {fmt % args}\n")
        sys.stdout.flush()

    def _proxy(self, method):
        # 读取请求体
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        # 尝试转换工具类型
        modified = False
        try:
            data = json.loads(body.decode("utf-8"))
            if "tools" in data and isinstance(data["tools"], list):
                new_tools, changed = convert_tools(data["tools"])
                if changed:
                    data["tools"] = new_tools
                    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                    modified = True
                    ProxyHandler.count += 1
                    self.log_message(f"✓ custom→function 转换 #{ProxyHandler.count}")
        except Exception as e:
            self.log_message(f"工具转换跳过，解析异常: {str(e)}")

        # 解析上游地址
        parsed = urlparse(self.upstream)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = self.path

        self.log_message(f"→ {method} {path} → {host}:{port} ({len(body)}B)")

        # 构建请求头
        req_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
            "Authorization": f"Bearer {self.api_key}",
            "Host": host,
        }
        # 保留原始Accept等头，过滤冲突头
        for k, v in self.headers.items():
            kl = k.lower()
            if kl not in ("host", "content-length", "content-type", "authorization", "connection"):
                req_headers[k] = v

        conn = None
        try:
            # 创建HTTPS连接
            ctx = ssl.create_default_context()
            conn = HTTPSConnection(host, port=port, context=ctx, timeout=120)
            conn.request(method, path, body=body, headers=req_headers)
            resp = conn.getresponse()

            # 回写状态码+响应头给客户端
            self.send_response(resp.status)
            for hk, hv in resp.getheaders():
                lhk = hk.lower()
                # 过滤transfer-encoding避免本地http.server解析冲突
                if lhk not in ("transfer-encoding", "content-length"):
                    self.send_header(hk, hv)
            # 手动设置Content-Length（如果有）
            content_length = resp.getheader("Content-Length")
            if content_length:
                self.send_header("Content-Length", content_length)
            self.end_headers()

            # 流式回传响应体，4096字节分片避免大报文截断
            chunk_size = 4096
            total_bytes = 0
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                self.wfile.write(chunk)
                total_bytes += len(chunk)

            icon = "✓" if modified else "←"
            self.log_message(f"{icon} {resp.status} ({total_bytes}B)")
            return

        except Exception as err:
            err_msg = f"上游API转发失败: {str(err)}"
            self.log_message(f"× {err_msg}")
            err_body = json.dumps({
                "error": {
                    "message": err_msg,
                    "code": "proxy_error",
                    "type": "proxy_error"
                }
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        finally:
            # 强制关闭HTTPS连接，杜绝端口长连接泄漏
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def do_POST(self):
        self._proxy("POST")

    def do_PUT(self):
        self._proxy("PUT")

    def do_GET(self):
        # 健康检查端点
        if self.path == "/health":
            resp = json.dumps({
                "status": "ok",
                "upstream": self.upstream,
                "conversions": ProxyHandler.count,
                "version": "v5"
            }, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self._proxy("GET")

def main():
    parser = argparse.ArgumentParser(description="Codex MCP工具类型转换代理 v5")
    parser.add_argument("--port", type=int, default=PORT, help="监听端口 (默认15730)")
    parser.add_argument("--upstream", default=UPSTREAM, help="上游API地址")
    parser.add_argument("--api-key", type=str, default="", help="MiMo API Key (优先级最高)")
    args = parser.parse_args()

    # API Key优先级：命令行参数 > 环境变量 > config.toml
    api_key = args.api_key or os.getenv("MIMO_API_KEY", "") or load_api_key()
    if not api_key:
        print("[错误] 未找到API Key，请通过以下方式之一提供：")
        print("  1. 命令行参数: --api-key YOUR_KEY")
        print("  2. 环境变量: set MIMO_API_KEY=YOUR_KEY")
        print("  3. 配置文件: E:\\龙虾AI主控中心\\Codex\\.codex\\config.toml")
        sys.exit(1)

    ProxyHandler.upstream = args.upstream.rstrip("/")
    ProxyHandler.api_key = api_key

    server = HTTPServer(("127.0.0.1", args.port), ProxyHandler)
    print(f"[Codex工具代理v5] 启动成功，监听 http://127.0.0.1:{args.port}")
    print(f"[Codex工具代理v5] 上游目标: {ProxyHandler.upstream}")
    print(f"[Codex工具代理v5] API Key: ...{api_key[-8:]}")
    print(f"[Codex工具代理v5] 健康检查: http://127.0.0.1:{args.port}/health")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[已停止] 代理服务正常退出")
        server.shutdown()

if __name__ == "__main__":
    main()
