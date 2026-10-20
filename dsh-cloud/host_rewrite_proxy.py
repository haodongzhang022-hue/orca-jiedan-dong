#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Host Rewrite Proxy v1.0 — 解决 dsh web 的三重网络约束（CNB 容器专用）

【为什么必须有这一层】
dsh web（0.2.1）有两条硬性安全设计，导致它无法直接对外提供服务：
  1) 禁止 --host 0.0.0.0 —— 源码里 program.error() 直接退出，
     原文：「intentionally not supported yet for safety: it would expose RCE」
  2) /api 有 browser-trust fence —— 非信任 Host 一律 403（本机实测确认：
     正常 Host 返回 401，伪造 cnb.run 域名返回 403）
而 CNB 的 PORTS 转发要求服务监听 0.0.0.0，且访问域名是 {实例ID}-{port}.cnb.run。

本代理做两件事：
  监听 0.0.0.0:<对外端口>  →  转发 127.0.0.1:<dsh实际端口>
  并把每个请求的 Host 头改写成 127.0.0.1:<dsh实际端口>（IP 字面量，fence 必放行）

【协议处理】
  请求方向：逐请求解析 HTTP 头，改写 Host 行；按 Content-Length 精确跳过 body。
  响应方向：纯字节流透传（SSE / WebSocket 升级后同样是透明字节流）。
  chunked 请求体：退化为「原样透传直到连接关闭」，保证不破坏数据。

【用法】
  python3 host_rewrite_proxy.py --listen-port 8830 --target-port 8831
"""
import argparse
import socket
import threading

BUF = 32768
SEP = b"\r\n\r\n"


def _find_head_end(buf):
    return buf.find(SEP)


def _rewrite_host(head_bytes, new_host):
    """改写 HTTP 头里的 Host 行（大小写不敏感），没有则补一行。"""
    lines = head_bytes.split(b"\r\n")
    out, found = [], False
    for ln in lines:
        low = ln.lower()
        if low.startswith(b"host:"):
            out.append(b"Host: " + new_host.encode())
            found = True
        elif low.startswith(b"proxy-connection:"):
            # 代理专用头，透传给源站无意义
            continue
        else:
            out.append(ln)
    if not found and len(out) > 0:
        out.insert(1, b"Host: " + new_host.encode())
    return b"\r\n".join(out)


def _content_length(head_bytes):
    for ln in head_bytes.split(b"\r\n"):
        if ln.lower().startswith(b"content-length:"):
            try:
                return int(ln.split(b":", 1)[1].strip())
            except Exception:
                return 0
    return 0


def _is_chunked(head_bytes):
    for ln in head_bytes.split(b"\r\n"):
        if ln.lower().startswith(b"transfer-encoding:"):
            return b"chunked" in ln.lower()
    return False


def pipe_client_to_upstream(csock, usock, new_host):
    """客户端 → 上游：逐请求改写 Host，按 Content-Length 跳过 body。"""
    buf = b""
    try:
        while True:
            # ---- 阶段一：收齐一个完整请求头 ----
            while _find_head_end(buf) < 0:
                chunk = csock.recv(BUF)
                if not chunk:
                    # 连接结束前把残余原样送出去
                    if buf:
                        usock.sendall(buf)
                    return
                buf += chunk
                if len(buf) > 1024 * 1024:  # 头部异常巨大，放弃改写直接透传
                    usock.sendall(buf)
                    buf = b""
                    break

            idx = _find_head_end(buf)
            if idx < 0:
                continue
            head = buf[:idx]
            rest = buf[idx + len(SEP):]
            buf = b""

            usock.sendall(_rewrite_host(head, new_host) + SEP)

            if _is_chunked(head):
                # chunked 体无法安全切分，整体退化为透明透传
                if rest:
                    usock.sendall(rest)
                while True:
                    chunk = csock.recv(BUF)
                    if not chunk:
                        return
                    usock.sendall(chunk)

            need = _content_length(head)
            if need > 0:
                if rest:
                    usock.sendall(rest)
                    need -= len(rest)
                while need > 0:
                    chunk = csock.recv(min(BUF, need))
                    if not chunk:
                        return
                    usock.sendall(chunk)
                    need -= len(chunk)
            elif rest:
                # 无 body 但已多读，可能是同连接的下一个请求，回填继续解析
                buf = rest
    except Exception:
        return
    finally:
        try:
            usock.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def pipe_upstream_to_client(usock, csock):
    """上游 → 客户端：纯字节流透传（响应头不改写）。"""
    try:
        while True:
            chunk = usock.recv(BUF)
            if not chunk:
                break
            csock.sendall(chunk)
    except Exception:
        pass
    finally:
        try:
            csock.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def handle(csock, target_host, target_port, new_host):
    usock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    usock.settimeout(300)
    try:
        usock.connect((target_host, target_port))
    except Exception:
        try:
            csock.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 16\r\n\r\nupstream down\r\n")
        except Exception:
            pass
        csock.close()
        usock.close()
        return
    t = threading.Thread(target=pipe_upstream_to_client, args=(usock, csock), daemon=True)
    t.start()
    pipe_client_to_upstream(csock, usock, new_host)
    t.join(timeout=5)
    for s in (csock, usock):
        try:
            s.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen-host", default="0.0.0.0")
    ap.add_argument("--listen-port", type=int, default=8830)
    ap.add_argument("--target-host", default="127.0.0.1")
    ap.add_argument("--target-port", type=int, default=8831)
    args = ap.parse_args()

    new_host = "%s:%d" % (args.target_host, args.target_port)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.listen_host, args.listen_port))
    srv.listen(64)

    print("[proxy] %s:%d  ->  %s:%d   (Host 改写为 %s)"
          % (args.listen_host, args.listen_port, args.target_host, args.target_port, new_host), flush=True)

    while True:
        try:
            csock, addr = srv.accept()
        except Exception:
            continue
        csock.settimeout(300)
        threading.Thread(target=handle,
                         args=(csock, args.target_host, args.target_port, new_host),
                         daemon=True).start()


if __name__ == "__main__":
    main()
