"""HTTP server 跑 :18765，让浏览器能 fetch 真实 activity_stream.jsonl

汤哥工作台和 activity_view.html 都改走 :18765，跨源 fetch 才有权限。
v2.7: 加 CGI 路由 — /scripts/lib/*.py 用 subprocess 跑 Python 脚本返回 JSON
"""
import http.server, socketserver, os, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # 项目根
PORT = 18765
PYTHON_EXE = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"

# MIME 覆盖 — 修复 .jsonl 下载被 Windows 误识别
MIME_OVERRIDE = {
    '.jsonl': 'application/x-ndjson',   # Windows 友好：浏览器直接渲染
    '.json':  'application/json; charset=utf-8',
    '.svg':   'image/svg+xml',
    '.png':   'image/png',
    '.html':  'text/html; charset=utf-8',
    '.md':    'text/markdown; charset=utf-8',
}

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)
    # 跨源 fetch 必备
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in MIME_OVERRIDE:
            return MIME_OVERRIDE[ext]
        return super().guess_type(path)
    def do_GET(self):
        """拦截 scripts/lib/*.py → 当 CGI 跑"""
        sys.stderr.write(f'[18765 CGI?] path={self.path}\n')
        if self.path.startswith('/scripts/lib/') and self.path.split('?')[0].endswith('.py'):
            self.run_cgi()
            return
        super().do_GET()
    def do_HEAD(self):
        """HEAD 也要走 CGI 路由，否则 HEAD 会被 static file handler 截走"""
        if self.path.startswith('/scripts/lib/') and self.path.split('?')[0].endswith('.py'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        super().do_HEAD()
    def run_cgi(self):
        rel = self.path.lstrip('/').split('?')[0]
        script_full = ROOT / rel
        if not script_full.exists():
            self.send_error(404, 'script not found: ' + rel)
            return
        try:
            env = os.environ.copy()
            env['QUERY_STRING'] = self.path.split('?', 1)[1] if '?' in self.path else ''
            env['PYTHONIOENCODING'] = 'utf-8'
            env['MSYS2_ARG_CONV_EXCL'] = '*'
            # list 形式，避免 cmd/PowerShell 路径 bug
            cmd = [PYTHON_EXE, str(script_full)]
            r = subprocess.run(cmd, capture_output=True, env=env, cwd=str(ROOT), timeout=15)
            out = (r.stdout or b'').decode('utf-8', errors='ignore')
            err = (r.stderr or b'').decode('utf-8', errors='ignore')
            body = out if r.returncode == 0 else (err or 'CGI ERROR')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
        except subprocess.TimeoutExpired:
            self.send_error(504, 'script timeout (15s)')
        except Exception as e:
            self.send_error(500, 'cgi err: ' + str(e))
    def log_message(self, fmt, *args):
        # 简洁输出，不刷屏
        sys.stderr.write('[18765] %s\n' % (fmt % args))

if __name__ == '__main__':
    with socketserver.TCPServer(('127.0.0.1', PORT), CORSHandler) as httpd:
        print(f'🚀 HTTP server UP at http://127.0.0.1:{PORT}/')
        print(f'   Project root: {ROOT}')
        print(f'   Activity stream: http://127.0.0.1:{PORT}/.workbuddy/activity_stream.jsonl')
        print(f'   工作台 v2.7:      http://127.0.0.1:{PORT}/.workbuddy/artifacts/lobster-design-jiedan-station.html')
        print(f'   活动查看器 v3: http://127.0.0.1:{PORT}/scripts/activity_view.html')
        print(f'   5子库调取 CGI: http://127.0.0.1:{PORT}/scripts/lib/recall_from_lib.py?lib=wecom_jd')
        httpd.serve_forever()
